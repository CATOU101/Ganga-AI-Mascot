"""SQLite + NumPy vector storage and retrieval backend for Ganga Brain.

This module provides a standalone, crash-proof vector retrieval layer that loads
metadata from knowledge_base/vector_db/chroma.sqlite3 and computes vector distances
using NumPy. It completely bypasses chromadb and native C/Rust binding crashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from .chunking import Chunk
from .config import BrainConfig, load_config
from .embeddings import get_embedding_function


_STORE_CACHE: dict[str, SQLiteVectorStore] = {}


class SQLiteVectorStore:
    """Standalone vector store backed by SQLite metadata and portable NumPy vector files."""

    def __init__(self, config: BrainConfig, embedding=None) -> None:
        self.config = config
        self.embedding = embedding or get_embedding_function(
            config.embedding_provider,
            config.embedding_dimensions,
            config.ort_threads,
        )
        self.chunks: list[dict[str, Any]] = []
        self.vectors: np.ndarray | None = None

        self._load_sqlite_data()
        self._load_vectors()

    def _load_sqlite_data(self) -> None:
        """Load text chunks and citation metadata from SQLite database."""
        if not self.config.sqlite_db_path.exists():
            return

        conn = sqlite3.connect(str(self.config.sqlite_db_path), check_same_thread=False)
        cursor = conn.cursor()

        # Query all embedding items ordered by SQLite id
        cursor.execute("SELECT id, embedding_id FROM embeddings ORDER BY id ASC;")
        embedding_rows = cursor.fetchall()

        if not embedding_rows:
            conn.close()
            return

        # Query all metadata key-values
        cursor.execute(
            """
            SELECT id, key, string_value, int_value, float_value
            FROM embedding_metadata
            ORDER BY id ASC;
            """
        )

        metadata_by_id: dict[int, dict[str, Any]] = {}
        for em_id, key, str_val, int_val, float_val in cursor.fetchall():
            if em_id not in metadata_by_id:
                metadata_by_id[em_id] = {}
            val = str_val if str_val is not None else (int_val if int_val is not None else float_val)
            metadata_by_id[em_id][key] = val

        conn.close()

        chunks = []
        for em_id, chunk_id in embedding_rows:
            meta = metadata_by_id.get(em_id, {})
            text = meta.pop("chroma:document", "")
            
            # Format clean citation metadata dictionary
            metadata_dict = {
                "section_id": meta.get("section_id", ""),
                "source_id": meta.get("source_id", ""),
                "file_name": meta.get("file_name", ""),
                "title": meta.get("title", ""),
                "section": meta.get("section", ""),
                "subsection": meta.get("subsection", ""),
                "page_start": int(meta.get("page_start") or 0),
                "page_end": int(meta.get("page_end") or 0),
                "page": str(meta.get("page", meta.get("page_start", ""))),
                "section_classification": meta.get("section_classification", ""),
                "knowledge_type": meta.get("knowledge_type", ""),
                "time_period": meta.get("time_period", ""),
                "geographic_scope": meta.get("geographic_scope", ""),
                "source_status": meta.get("source_status", ""),
                "relevance": meta.get("relevance", ""),
            }
            chunks.append({
                "id": em_id,
                "chunk_id": chunk_id,
                "text": text,
                "metadata": metadata_dict,
            })

        self.chunks = chunks

    def _load_vectors(self) -> None:
        """Load vector matrix into NumPy array."""
        provider = (self.config.embedding_provider or "semantic").lower().strip()

        if provider in ("semantic", "onnx", "default"):
            if self.config.semantic_vectors_path.exists():
                arr = np.load(str(self.config.semantic_vectors_path))
                if arr.dtype != np.float32:
                    arr = arr.astype(np.float32)
                self.vectors = arr
            else:
                self.vectors = None
        elif provider in ("local-hash", "hash", "baseline"):
            if self.chunks:
                texts = [c["text"] for c in self.chunks]
                vecs = self.embedding.embed_documents(texts)
                self.vectors = np.array(vecs, dtype=np.float32)

    def query(self, query_text: str, top_k: int) -> list[dict]:
        """Perform NumPy vector distance query and return top-k hits."""
        if not self.chunks or self.vectors is None:
            return []

        # Generate query vector (384 float32)
        q_vec = self.embedding.embed_query(query_text)
        q = np.array(q_vec, dtype=np.float32)

        # Compute Euclidean L2 distance to preserve Chroma distance semantics
        diffs = self.vectors - q
        distances = np.linalg.norm(diffs, axis=1)

        # Find top_k smallest distance indices
        k = min(top_k, len(distances))
        top_indices = np.argpartition(distances, k - 1)[:k]
        top_indices = top_indices[np.argsort(distances[top_indices])]

        hits = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            hits.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "distance": float(distances[idx]),
            })
        return hits

    def count(self) -> int:
        return len(self.chunks)


def get_chroma_vector_store(config: BrainConfig) -> SQLiteVectorStore:
    """Retrieve process-level singleton SQLiteVectorStore."""
    resolved_path = str(config.sqlite_db_path.resolve())
    cache_key = f"{resolved_path}:{config.embedding_provider}:{config.ort_threads}"
    if cache_key not in _STORE_CACHE:
        _STORE_CACHE[cache_key] = SQLiteVectorStore(config)
    return _STORE_CACHE[cache_key]


# Alias for backward compatibility
ChromaVectorStore = SQLiteVectorStore


def generate_semantic_vectors(config: BrainConfig, batch_size: int = 100) -> dict:
    """Explicit CLI command to generate semantic_vectors.npy from SQLite text chunks."""
    store = SQLiteVectorStore(config)
    if not store.chunks:
        raise RuntimeError("No SQLite chunks found in knowledge_base/vector_db/chroma.sqlite3")

    total = len(store.chunks)
    chunk_ids = [c["chunk_id"] for c in store.chunks]
    texts = [c["text"] for c in store.chunks]

    emb_fn = get_embedding_function("semantic", config.embedding_dimensions, config.ort_threads)
    all_vectors: list[list[float]] = []

    print(f"Generating vectors for {total} chunks in batches of {batch_size} (threads: {config.ort_threads})...")
    for start in range(0, total, batch_size):
        batch_texts = texts[start : start + batch_size]
        vecs = emb_fn.embed_documents(batch_texts)
        all_vectors.extend(vecs)
        print(f"Embedded batch {len(all_vectors)}/{total}")

    arr = np.array(all_vectors, dtype=np.float32)

    # Verification checks
    if arr.shape != (total, config.embedding_dimensions):
        raise ValueError(f"Invalid array shape {arr.shape}, expected ({total}, {config.embedding_dimensions})")
    if arr.dtype != np.float32:
        raise ValueError(f"Invalid array dtype {arr.dtype}, expected float32")

    # Atomic write to temporary file then atomic rename
    out_path = config.semantic_vectors_path
    tmp_path = out_path.with_suffix(".tmp.npy")

    np.save(str(tmp_path), arr)
    os.replace(str(tmp_path), str(out_path))

    # Compute SHA256 checksum
    sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()

    # Save manifest mapping file
    manifest_data = {
        "version": "semantic-vectors-v1",
        "created_at_utc": str(Path(out_path).stat().st_mtime),
        "total_vectors": total,
        "dimensions": config.embedding_dimensions,
        "dtype": "float32",
        "sha256": sha256,
        "chunk_ids": chunk_ids,
    }

    config.semantic_vectors_manifest_path.write_text(
        json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Successfully generated {out_path} ({arr.shape}, {out_path.stat().st_size} bytes)")
    return {
        "total_vectors": total,
        "dimensions": config.embedding_dimensions,
        "file": str(out_path),
        "manifest": str(config.semantic_vectors_manifest_path),
        "sha256": sha256,
    }


def main():
    parser = argparse.ArgumentParser(description="SQLite Vector Store Manager")
    parser.add_argument("--generate-vectors", action="store_true", help="Generate semantic_vectors.npy from SQLite text chunks.")
    args = parser.parse_args()

    if args.generate_vectors:
        res = generate_semantic_vectors(load_config())
        print(json.dumps(res, indent=2))
    else:
        parser.error("Use --generate-vectors")


if __name__ == "__main__":
    main()
