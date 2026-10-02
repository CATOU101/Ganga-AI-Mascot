"""SQLite metadata and NumPy vector storage for Ganga Brain."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .chunking import Chunk, chunks_from_sections
from .config import BrainConfig, load_config
from .embeddings import embedding_provenance, get_embedding_function
from .ingest import write_manifest


class IndexIntegrityError(RuntimeError):
    """Raised when the persisted Brain index is missing or inconsistent."""


_STORE_CACHE: dict[str, SQLiteVectorStore] = {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _chunk_data_hash(records: Sequence[dict[str, Any]]) -> str:
    canonical = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _chunk_records(chunks: Sequence[Chunk]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "metadata": chunk.metadata,
        }
        for chunk in chunks
    ]


def _write_sqlite_index(
    path: Path,
    config: BrainConfig,
    chunks: Sequence[Chunk],
    provenance: dict[str, str],
) -> str:
    records = _chunk_records(chunks)
    chunk_hash = _chunk_data_hash(records)
    ids = [chunk.chunk_id for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise IndexIntegrityError("Cannot build index: chunk IDs are not unique")

    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE collections (
                name TEXT PRIMARY KEY,
                embedding_provider TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                embedding_dimensions INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                chunks_sha256 TEXT NOT NULL
            );
            CREATE TABLE chunks (
                collection_name TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                chunk_id TEXT NOT NULL,
                text TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                PRIMARY KEY (collection_name, chunk_id),
                UNIQUE (collection_name, ordinal),
                FOREIGN KEY (collection_name) REFERENCES collections(name)
            );
            CREATE INDEX chunks_collection_order
                ON chunks(collection_name, ordinal);
            """
        )
        connection.execute(
            """
            INSERT INTO collections
                (name, embedding_provider, embedding_model, embedding_dimensions,
                 chunk_count, chunks_sha256)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                config.collection_name,
                provenance["provider"],
                provenance["model"],
                config.embedding_dimensions,
                len(chunks),
                chunk_hash,
            ),
        )
        connection.executemany(
            """
            INSERT INTO chunks
                (collection_name, ordinal, chunk_id, text, metadata_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    config.collection_name,
                    ordinal,
                    chunk.chunk_id,
                    chunk.text,
                    json.dumps(chunk.metadata, ensure_ascii=False, sort_keys=True),
                )
                for ordinal, chunk in enumerate(chunks)
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return chunk_hash


def _expected_model(config: BrainConfig) -> dict[str, str]:
    return embedding_provenance(config.embedding_provider, config.embedding_model)


def _validate_index_files(
    config: BrainConfig,
    sqlite_path: Path,
    vectors_path: Path,
    manifest_path: Path,
) -> tuple[list[dict[str, Any]], np.ndarray, dict[str, Any]]:
    for path in (sqlite_path, vectors_path, manifest_path):
        if not path.is_file():
            raise IndexIntegrityError(f"Brain index resource is missing: {path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IndexIntegrityError(f"Cannot read Brain index manifest {manifest_path}: {exc}") from exc

    if not isinstance(manifest, dict):
        raise IndexIntegrityError("Brain index manifest must contain a JSON object")
    if manifest.get("index_version") != "brain-index-v1":
        raise IndexIntegrityError("Unsupported or missing Brain index manifest version")
    if manifest.get("collection_name") != config.collection_name:
        raise IndexIntegrityError(
            f"Index collection {manifest.get('collection_name')!r} does not match "
            f"configured collection {config.collection_name!r}"
        )
    expected_model = _expected_model(config)
    stored_model = manifest.get("embedding")
    if not isinstance(stored_model, dict):
        raise IndexIntegrityError("Index manifest is missing embedding provenance")
    for key in ("provider", "model", "model_archive_sha256"):
        if stored_model.get(key) != expected_model.get(key):
            raise IndexIntegrityError(
                f"Index embedding {key} {stored_model.get(key)!r} does not match "
                f"configured embedding {expected_model.get(key)!r}"
            )

    if manifest.get("dimensions") != config.embedding_dimensions:
        raise IndexIntegrityError(
            f"Index dimensions {manifest.get('dimensions')!r} do not match "
            f"configured dimensions {config.embedding_dimensions}"
        )
    if manifest.get("dtype") != "float32":
        raise IndexIntegrityError(f"Unsupported vector dtype: {manifest.get('dtype')!r}")
    if manifest.get("sqlite_file") != sqlite_path.name or manifest.get("vectors_file") != vectors_path.name:
        raise IndexIntegrityError("Index manifest file names do not match configured index paths")

    try:
        connection = sqlite3.connect(sqlite_path)
        try:
            collection = connection.execute(
                """
                SELECT embedding_provider, embedding_model, embedding_dimensions,
                       chunk_count, chunks_sha256
                FROM collections WHERE name = ?
                """,
                (config.collection_name,),
            ).fetchone()
            if collection is None:
                raise IndexIntegrityError(
                    f"Configured collection {config.collection_name!r} is absent from the SQLite index"
                )
            rows = connection.execute(
                """
                SELECT ordinal, chunk_id, text, metadata_json
                FROM chunks WHERE collection_name = ? ORDER BY ordinal
                """,
                (config.collection_name,),
            ).fetchall()
            collection_count = connection.execute(
                "SELECT COUNT(*) FROM collections WHERE name = ?",
                (config.collection_name,),
            ).fetchone()[0]
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise IndexIntegrityError(f"Cannot read SQLite index {sqlite_path}: {exc}") from exc

    provider, model, dimensions, declared_count, declared_hash = collection
    if provider != expected_model["provider"] or model != expected_model["model"]:
        raise IndexIntegrityError("SQLite collection embedding identity does not match configuration")
    if dimensions != config.embedding_dimensions:
        raise IndexIntegrityError(
            f"SQLite collection dimensions {dimensions} do not match configured dimensions "
            f"{config.embedding_dimensions}"
        )
    if collection_count != 1:
        raise IndexIntegrityError(
            f"Expected one configured collection row, found {collection_count}"
        )

    expected_count = manifest.get("total_chunks")
    if not isinstance(expected_count, int) or expected_count < 1:
        raise IndexIntegrityError("Index manifest has an invalid total_chunks value")
    if declared_count != expected_count or len(rows) != expected_count:
        raise IndexIntegrityError(
            f"Chunk count mismatch: manifest={expected_count}, "
            f"SQLite collection={declared_count}, rows={len(rows)}"
        )

    chunk_ids = manifest.get("chunk_ids")
    if not isinstance(chunk_ids, list) or len(chunk_ids) != expected_count:
        raise IndexIntegrityError("Index manifest chunk_ids are missing or have the wrong length")
    if any(not isinstance(chunk_id, str) or not chunk_id for chunk_id in chunk_ids):
        raise IndexIntegrityError("Index manifest contains an invalid chunk ID")
    if len(set(chunk_ids)) != expected_count:
        raise IndexIntegrityError("Index manifest chunk IDs are not unique")

    records: list[dict[str, Any]] = []
    loaded_chunks: list[dict[str, Any]] = []
    for expected_ordinal, row in enumerate(rows):
        ordinal, chunk_id, text, metadata_json = row
        if ordinal != expected_ordinal:
            raise IndexIntegrityError(
                f"SQLite chunk ordinals are not contiguous at row {expected_ordinal}"
            )
        if chunk_id != chunk_ids[expected_ordinal]:
            raise IndexIntegrityError(
                f"Chunk ID/order mismatch at row {expected_ordinal}: "
                f"SQLite={chunk_id!r}, manifest={chunk_ids[expected_ordinal]!r}"
            )
        if not isinstance(text, str) or not isinstance(metadata_json, str):
            raise IndexIntegrityError(f"SQLite text or metadata is invalid for chunk {chunk_id!r}")
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError as exc:
            raise IndexIntegrityError(f"Invalid metadata JSON for chunk {chunk_id!r}") from exc
        if not isinstance(metadata, dict):
            raise IndexIntegrityError(f"Metadata for chunk {chunk_id!r} must be a JSON object")
        records.append({"chunk_id": chunk_id, "text": text, "metadata": metadata})
        loaded_chunks.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "metadata": metadata,
            }
        )

    chunk_hash = _chunk_data_hash(records)
    if chunk_hash != declared_hash or chunk_hash != manifest.get("chunks_sha256"):
        raise IndexIntegrityError("SQLite chunk contents do not match the index manifest checksum")
    if _sha256_file(vectors_path) != manifest.get("vectors_sha256"):
        raise IndexIntegrityError("NumPy vector file checksum does not match the index manifest")

    try:
        vectors = np.load(vectors_path, mmap_mode="r", allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise IndexIntegrityError(f"Cannot load NumPy vectors {vectors_path}: {exc}") from exc
    expected_shape = (expected_count, config.embedding_dimensions)
    if vectors.shape != expected_shape:
        raise IndexIntegrityError(
            f"Vector shape {vectors.shape} does not match expected {expected_shape}"
        )
    if vectors.dtype != np.float32:
        raise IndexIntegrityError(f"Vector dtype {vectors.dtype} does not match float32")
    if not np.isfinite(vectors).all():
        raise IndexIntegrityError("Vector matrix contains non-finite values")

    return loaded_chunks, vectors, manifest


class SQLiteVectorStore:
    """Collection-scoped SQLite metadata and NumPy vector store."""

    def __init__(self, config: BrainConfig, embedding=None) -> None:
        self.config = config
        self.embedding = embedding or get_embedding_function(
            config.embedding_provider,
            config.embedding_dimensions,
            config.ort_threads,
            config.embedding_model,
        )
        self.chunks, self.vectors, self.manifest = _validate_index_files(
            config,
            config.sqlite_db_path,
            config.semantic_vectors_path,
            config.semantic_vectors_manifest_path,
        )
        self._embedding_ready = False

    def check_embedding_ready(self) -> None:
        if self._embedding_ready:
            return
        vector = np.asarray(self.embedding.embed_query("Ganga Brain readiness check"), dtype=np.float32)
        if vector.shape != (self.config.embedding_dimensions,) or not np.isfinite(vector).all():
            raise IndexIntegrityError(
                f"Query embedding has invalid shape or values: {vector.shape}"
            )
        self._embedding_ready = True

    def query(self, query_text: str, top_k: int) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if not self.chunks:
            raise IndexIntegrityError("Configured Brain collection contains no chunks")

        query_vector = np.asarray(self.embedding.embed_query(query_text), dtype=np.float32)
        if query_vector.shape != (self.config.embedding_dimensions,):
            raise IndexIntegrityError(
                f"Query embedding shape {query_vector.shape} does not match "
                f"({self.config.embedding_dimensions},)"
            )
        if not np.isfinite(query_vector).all():
            raise IndexIntegrityError("Query embedding contains non-finite values")

        distances = np.linalg.norm(self.vectors - query_vector, axis=1)
        k = min(top_k, len(distances))
        indices = np.argpartition(distances, k - 1)[:k]
        indices = indices[np.argsort(distances[indices])]
        return [
            {
                "chunk_id": self.chunks[index]["chunk_id"],
                "text": self.chunks[index]["text"],
                "metadata": self.chunks[index]["metadata"],
                "distance": float(distances[index]),
            }
            for index in indices
        ]

    def count(self) -> int:
        return len(self.chunks)


def get_vector_store(config: BrainConfig) -> SQLiteVectorStore:
    """Return a process-level store keyed by the active files and collection."""
    cache_key = ":".join(
        (
            str(config.sqlite_db_path.resolve()),
            str(config.semantic_vectors_path.resolve()),
            str(config.semantic_vectors_manifest_path.resolve()),
            config.collection_name,
            config.embedding_provider,
            config.embedding_model,
            str(config.embedding_dimensions),
            str(config.ort_threads),
        )
    )
    if cache_key not in _STORE_CACHE:
        _STORE_CACHE[cache_key] = SQLiteVectorStore(config)
    return _STORE_CACHE[cache_key]


def build_index(config: BrainConfig, batch_size: int = 100) -> dict[str, Any]:
    """Build a complete index from reviewed sections without touching legacy artifacts."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    config.vector_db_path.mkdir(parents=True, exist_ok=True)

    ingestion_manifest = write_manifest(config)
    chunks = chunks_from_sections(
        ingestion_manifest["sections"],
        target_chars=config.chunk_target_chars,
        overlap_chars=config.chunk_overlap_chars,
        min_chunk_chars=config.min_chunk_chars,
    )
    if not chunks:
        raise IndexIntegrityError("No approved chunks were produced from the reviewed knowledge base")

    provenance = _expected_model(config)
    embedding = get_embedding_function(
        config.embedding_provider,
        config.embedding_dimensions,
        config.ort_threads,
        config.embedding_model,
    )
    with tempfile.TemporaryDirectory(
        prefix=".brain-index-build-",
        dir=config.vector_db_path,
    ) as staging_dir:
        staging = Path(staging_dir)
        staging_sqlite = staging / config.sqlite_db_path.name
        staging_vectors = staging / config.semantic_vectors_path.name
        staging_manifest = staging / config.semantic_vectors_manifest_path.name
        chunks_hash = _write_sqlite_index(staging_sqlite, config, chunks, provenance)

        batches: list[list[float]] = []
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            batches.extend(embedding.embed_documents([chunk.text for chunk in batch]))
        vectors = np.asarray(batches, dtype=np.float32)
        expected_shape = (len(chunks), config.embedding_dimensions)
        if vectors.shape != expected_shape:
            raise IndexIntegrityError(
                f"Generated vector shape {vectors.shape} does not match expected {expected_shape}"
            )
        if not np.isfinite(vectors).all():
            raise IndexIntegrityError("Generated vector matrix contains non-finite values")
        np.save(staging_vectors, vectors, allow_pickle=False)

        manifest = {
            "index_version": "brain-index-v1",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "collection_name": config.collection_name,
            "sqlite_file": config.sqlite_db_path.name,
            "vectors_file": config.semantic_vectors_path.name,
            "total_chunks": len(chunks),
            "dimensions": config.embedding_dimensions,
            "dtype": "float32",
            "chunks_sha256": chunks_hash,
            "vectors_sha256": _sha256_file(staging_vectors),
            "chunk_ids": [chunk.chunk_id for chunk in chunks],
            "embedding": provenance,
            "chunking": {
                "target_chars": config.chunk_target_chars,
                "overlap_chars": config.chunk_overlap_chars,
                "min_chunk_chars": config.min_chunk_chars,
            },
        }
        staging_manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        _validate_index_files(
            config,
            staging_sqlite,
            staging_vectors,
            staging_manifest,
        )

        os.replace(staging_sqlite, config.sqlite_db_path)
        os.replace(staging_vectors, config.semantic_vectors_path)
        os.replace(staging_manifest, config.semantic_vectors_manifest_path)

    _STORE_CACHE.clear()
    _validate_index_files(
        config,
        config.sqlite_db_path,
        config.semantic_vectors_path,
        config.semantic_vectors_manifest_path,
    )
    return {
        "collection_name": config.collection_name,
        "total_chunks": len(chunks),
        "dimensions": config.embedding_dimensions,
        "sqlite_file": str(config.sqlite_db_path),
        "vectors_file": str(config.semantic_vectors_path),
        "manifest_file": str(config.semantic_vectors_manifest_path),
        "embedding": provenance,
    }


def generate_semantic_vectors(config: BrainConfig, batch_size: int = 100) -> dict[str, Any]:
    """Backward-compatible entry point that now builds the full reviewed-data index."""
    return build_index(config, batch_size=batch_size)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Brain SQLite/NumPy index from reviewed data.")
    parser.add_argument("--generate-vectors", action="store_true", help="Build the complete SQLite and NumPy index.")
    parser.add_argument("--batch-size", type=int, default=100, help="Embedding batch size.")
    args = parser.parse_args()

    if not args.generate_vectors:
        parser.error("Use --generate-vectors")
    print(json.dumps(build_index(load_config(), args.batch_size), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
