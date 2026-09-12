"""Configuration for the first working RAG Brain prototype."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class BrainConfig:
    section_review_path: Path = ROOT / "knowledge_base" / "processed" / "section_review.json"
    processed_documents_dir: Path = ROOT / "knowledge_base" / "processed" / "processed_documents"
    prototype_manifest_path: Path = ROOT / "knowledge_base" / "processed" / "prototype_ingestion_manifest.json"
    prototype_manifest_md_path: Path = ROOT / "knowledge_base" / "processed" / "prototype_ingestion_manifest.md"
    vector_db_path: Path = ROOT / "knowledge_base" / "vector_db"
    sqlite_db_path: Path = ROOT / "knowledge_base" / "vector_db" / "chroma.sqlite3"
    semantic_vectors_path: Path = ROOT / "knowledge_base" / "vector_db" / "semantic_vectors.npy"
    semantic_vectors_manifest_path: Path = ROOT / "knowledge_base" / "vector_db" / "semantic_vectors_manifest.json"
    collection_name: str = "ganga_brain_prototype"
    embedding_provider: str = os.getenv("GANGA_BRAIN_EMBEDDING_PROVIDER", "semantic")
    embedding_model: str = os.getenv("GANGA_BRAIN_EMBEDDING_MODEL", "onnx-semantic-embedding-v1")
    embedding_dimensions: int = 384
    chunk_target_chars: int = 1400
    chunk_overlap_chars: int = 180
    min_chunk_chars: int = 120
    top_k: int = int(os.getenv("GANGA_BRAIN_TOP_K", "5"))
    candidate_top_k: int = int(os.getenv("GANGA_BRAIN_CANDIDATE_TOP_K", "15"))
    evidence_max_distance: float = float(os.getenv("GANGA_BRAIN_EVIDENCE_MAX_DISTANCE", "1.15"))
    min_keyword_overlap: float = float(os.getenv("GANGA_BRAIN_MIN_KEYWORD_OVERLAP", "0.15"))
    ort_threads: int = int(os.getenv("GANGA_BRAIN_ORT_THREADS", "2"))
    llm_provider: str = os.getenv("GANGA_BRAIN_LLM_PROVIDER", "extractive")
    llm_model: str = os.getenv("GANGA_BRAIN_LLM_MODEL", "grounded-extractive-v1")


APPROVED_CLASSIFICATIONS = frozenset({"KEEP", "KEEP_HISTORICAL", "KEEP_METHODOLOGICAL"})


def load_config() -> BrainConfig:
    return BrainConfig()
