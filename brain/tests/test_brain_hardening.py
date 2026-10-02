from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from fastapi.testclient import TestClient

from brain.api import AskRequest, app
from brain.chunking import Chunk
from brain.config import load_config
from brain.embeddings import embedding_provenance
from brain.generator import OpenAIChatGenerator
from brain.translator import TranslationError, normalize_language, translate_text
from brain.vector_store import IndexIntegrityError, _validate_index_files, _write_sqlite_index


def small_index(config, directory: Path) -> tuple[Path, Path, Path]:
    sqlite_path = directory / "brain_index.sqlite3"
    vectors_path = directory / "brain_semantic_vectors.npy"
    manifest_path = directory / "brain_index_manifest.json"
    chunks = [
        Chunk(
            chunk_id="section-1::chunk-001",
            text="A short Ganga fact.",
            metadata={"section_id": "section-1", "page_start": 1, "page_end": 1},
        ),
        Chunk(
            chunk_id="section-2::chunk-001",
            text="Another Ganga fact.",
            metadata={"section_id": "section-2", "page_start": 2, "page_end": 2},
        ),
    ]
    provenance = embedding_provenance(config.embedding_provider, config.embedding_model)
    chunks_hash = _write_sqlite_index(sqlite_path, config, chunks, provenance)
    vectors = np.zeros((2, config.embedding_dimensions), dtype=np.float32)
    vectors[0, 0] = 1.0
    vectors[1, 1] = 1.0
    np.save(vectors_path, vectors, allow_pickle=False)
    manifest = {
        "index_version": "brain-index-v1",
        "collection_name": config.collection_name,
        "sqlite_file": sqlite_path.name,
        "vectors_file": vectors_path.name,
        "total_chunks": 2,
        "dimensions": config.embedding_dimensions,
        "dtype": "float32",
        "chunks_sha256": chunks_hash,
        "vectors_sha256": hashlib.sha256(vectors_path.read_bytes()).hexdigest(),
        "chunk_ids": [chunk.chunk_id for chunk in chunks],
        "embedding": provenance,
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return sqlite_path, vectors_path, manifest_path


class BrainHardeningTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_config_rejects_invalid_runtime_values(self):
        with self.assertRaisesRegex(ValueError, "top_k"):
            replace(self.config, top_k=0)
        with self.assertRaisesRegex(ValueError, "min_keyword_overlap"):
            replace(self.config, min_keyword_overlap=1.1)
        with self.assertRaisesRegex(ValueError, "semantic provider"):
            replace(self.config, embedding_model="different-model")

    def test_api_top_k_is_bounded_and_defaults_to_english(self):
        self.assertEqual(AskRequest(question="What is Ganga?").get_input_language(), "en")
        self.assertEqual(AskRequest(question="What is Ganga?").get_output_language(), "en")
        self.assertEqual(
            AskRequest(question="गंगा क्या है?", input_language="hi").get_output_language(),
            "hi",
        )
        with self.assertRaises(ValueError):
            AskRequest(question="What is Ganga?", top_k=0)
        with self.assertRaises(ValueError):
            AskRequest(question="What is Ganga?", top_k=101)

    def test_language_normalization_rejects_unsupported_codes(self):
        self.assertEqual(normalize_language(" HI ", default="en"), "hi")
        with self.assertRaises(ValueError):
            normalize_language("fr", default="en")

    def test_translation_failure_is_explicit(self):
        with patch("brain.translator._http_translate", return_value=None):
            with self.assertRaises(TranslationError):
                translate_text("A Ganga answer", "en", "hi")

    def test_index_load_validates_chunk_identity_and_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            test_config = replace(
                self.config,
                embedding_provider="local-hash",
                sqlite_db_path=directory / "brain_index.sqlite3",
                semantic_vectors_path=directory / "brain_semantic_vectors.npy",
                semantic_vectors_manifest_path=directory / "brain_index_manifest.json",
            )
            sqlite_path, vectors_path, manifest_path = small_index(test_config, directory)
            chunks, vectors, _ = _validate_index_files(
                test_config, sqlite_path, vectors_path, manifest_path
            )
            self.assertEqual([chunk["chunk_id"] for chunk in chunks], [
                "section-1::chunk-001",
                "section-2::chunk-001",
            ])
            self.assertEqual(vectors.shape, (2, test_config.embedding_dimensions))

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["chunk_ids"][0] = "wrong-chunk-id"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(IndexIntegrityError, "Chunk ID/order mismatch"):
                _validate_index_files(test_config, sqlite_path, vectors_path, manifest_path)

    def test_index_load_is_scoped_to_configured_collection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            test_config = replace(
                self.config,
                embedding_provider="local-hash",
                sqlite_db_path=directory / "brain_index.sqlite3",
                semantic_vectors_path=directory / "brain_semantic_vectors.npy",
                semantic_vectors_manifest_path=directory / "brain_index_manifest.json",
            )
            sqlite_path, vectors_path, manifest_path = small_index(test_config, directory)
            wrong_collection = replace(test_config, collection_name="other-collection")
            with self.assertRaisesRegex(IndexIntegrityError, "does not match configured collection"):
                _validate_index_files(
                    wrong_collection, sqlite_path, vectors_path, manifest_path
                )

    def test_index_validation_ignores_other_collections(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            test_config = replace(
                self.config,
                embedding_provider="local-hash",
                sqlite_db_path=directory / "brain_index.sqlite3",
                semantic_vectors_path=directory / "brain_semantic_vectors.npy",
                semantic_vectors_manifest_path=directory / "brain_index_manifest.json",
            )
            sqlite_path, vectors_path, manifest_path = small_index(test_config, directory)
            with sqlite3.connect(sqlite_path) as connection:
                connection.execute(
                    "INSERT INTO collections VALUES (?, ?, ?, ?, ?, ?)",
                    ("another-collection", "local-hash", "local-hash-embedding-v1", 384, 1, "unused"),
                )
                connection.execute(
                    "INSERT INTO chunks VALUES (?, ?, ?, ?, ?)",
                    ("another-collection", 0, "other::chunk-001", "Other collection", "{}"),
                )
            chunks, _, _ = _validate_index_files(
                test_config, sqlite_path, vectors_path, manifest_path
            )
            self.assertEqual(len(chunks), 2)

    def test_index_validation_checks_vector_dimensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            test_config = replace(
                self.config,
                embedding_provider="local-hash",
                sqlite_db_path=directory / "brain_index.sqlite3",
                semantic_vectors_path=directory / "brain_semantic_vectors.npy",
                semantic_vectors_manifest_path=directory / "brain_index_manifest.json",
            )
            sqlite_path, vectors_path, manifest_path = small_index(test_config, directory)
            np.save(vectors_path, np.zeros((2, 383), dtype=np.float32), allow_pickle=False)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["vectors_sha256"] = hashlib.sha256(vectors_path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(IndexIntegrityError, "Vector shape"):
                _validate_index_files(test_config, sqlite_path, vectors_path, manifest_path)

    def test_openai_generator_uses_bearer_api_key(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "Supported answer."}}]}
        ).encode("utf-8")
        generator = OpenAIChatGenerator.__new__(OpenAIChatGenerator)
        generator.api_key = "test-key"
        generator.model = "test-model"
        hits = [
            {
                "text": "Ganga source evidence is represented here.",
                "metadata": {
                    "title": "Source",
                    "file_name": "source.pdf",
                    "page_start": 1,
                    "page_end": 1,
                    "section": "Section",
                },
            }
        ]
        with patch("brain.generator.urllib.request.urlopen", return_value=response) as urlopen:
            generator.generate("What is Ganga?", hits)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")

    def test_health_reports_readiness_and_ask_defaults_languages(self):
        class ReadyStore:
            config = self.config

            def check_embedding_ready(self):
                return None

            def count(self):
                return 4085

        client = TestClient(app)
        with patch("brain.api.get_vector_store", return_value=ReadyStore()):
            with patch(
                "brain.api.answer_question",
                return_value={"answer": "Answer", "mode": "grounded"},
            ) as answer:
                health = client.get("/health")
                self.assertEqual(health.status_code, 200)
                self.assertTrue(health.json()["brain"]["ready"])
                response = client.post("/ask", json={"question": "What is Ganga?"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(answer.call_args.kwargs["input_language"], "en")
        self.assertEqual(answer.call_args.kwargs["output_language"], "en")

    def test_health_reports_missing_index_as_not_ready(self):
        client = TestClient(app)
        with patch("brain.api.get_vector_store", side_effect=IndexIntegrityError("missing")):
            response = client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["brain"]["ready"])

    def test_api_does_not_return_untranslated_answer_as_success(self):
        client = TestClient(app)
        with patch("brain.api.answer_question", side_effect=TranslationError("translation failed")):
            response = client.post(
                "/ask",
                json={
                    "question": "What is Ganga?",
                    "input_language": "en",
                    "output_language": "hi",
                },
            )
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
