"""Configuration for the first working RAG Brain prototype."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_API_TOP_K = 100
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


@dataclass(frozen=True)
class BrainConfig:
    section_review_path: Path = ROOT / "knowledge_base" / "processed" / "section_review.json"
    processed_documents_dir: Path = ROOT / "knowledge_base" / "processed" / "processed_documents"
    prototype_manifest_path: Path = ROOT / "knowledge_base" / "processed" / "prototype_ingestion_manifest.json"
    prototype_manifest_md_path: Path = ROOT / "knowledge_base" / "processed" / "prototype_ingestion_manifest.md"
    vector_db_path: Path = ROOT / "knowledge_base" / "vector_db"
    sqlite_db_path: Path = ROOT / "knowledge_base" / "vector_db" / "brain_index.sqlite3"
    semantic_vectors_path: Path = ROOT / "knowledge_base" / "vector_db" / "brain_semantic_vectors.npy"
    semantic_vectors_manifest_path: Path = ROOT / "knowledge_base" / "vector_db" / "brain_index_manifest.json"
    collection_name: str = "ganga_brain_prototype"
    embedding_provider: str = os.getenv("GANGA_BRAIN_EMBEDDING_PROVIDER", "semantic")
    embedding_model: str = os.getenv("GANGA_BRAIN_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_dimensions: int = 384
    chunk_target_chars: int = 1400
    chunk_overlap_chars: int = 180
    min_chunk_chars: int = 120
    top_k: int = int(os.getenv("GANGA_BRAIN_TOP_K", "5"))
    candidate_top_k: int = int(os.getenv("GANGA_BRAIN_CANDIDATE_TOP_K", "15"))
    evidence_max_distance: float = float(os.getenv("GANGA_BRAIN_EVIDENCE_MAX_DISTANCE", "1.15"))
    min_keyword_overlap: float = float(os.getenv("GANGA_BRAIN_MIN_KEYWORD_OVERLAP", "0.15"))
    ort_threads: int = int(os.getenv("GANGA_BRAIN_ORT_THREADS", "2"))
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "groq"))
    llm_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "").strip() or DEFAULT_GROQ_MODEL
    )

    def __post_init__(self) -> None:
        if not self.collection_name.strip():
            raise ValueError("collection_name must not be empty")
        if self.embedding_dimensions != 384:
            raise ValueError("The configured MiniLM embedding model requires 384 dimensions")
        if self.top_k < 1 or self.top_k > MAX_API_TOP_K:
            raise ValueError(f"top_k must be between 1 and {MAX_API_TOP_K}")
        if self.candidate_top_k < 1:
            raise ValueError("candidate_top_k must be at least 1")
        if self.candidate_top_k > 1000:
            raise ValueError("candidate_top_k must not exceed 1000")
        if not math.isfinite(self.evidence_max_distance) or not 0 < self.evidence_max_distance <= 2:
            raise ValueError("evidence_max_distance must be finite and between 0 and 2")
        if not 0 <= self.min_keyword_overlap <= 1:
            raise ValueError("min_keyword_overlap must be between 0 and 1")
        if self.ort_threads < 1:
            raise ValueError("ort_threads must be at least 1")
        if self.chunk_target_chars < 1:
            raise ValueError("chunk_target_chars must be at least 1")
        if self.chunk_overlap_chars < 0 or self.chunk_overlap_chars >= self.chunk_target_chars:
            raise ValueError("chunk_overlap_chars must be between 0 and chunk_target_chars - 1")
        if self.min_chunk_chars < 1 or self.min_chunk_chars > self.chunk_target_chars:
            raise ValueError("min_chunk_chars must be between 1 and chunk_target_chars")
        if self.embedding_provider.lower().strip() in {"semantic", "onnx", "default"}:
            if self.embedding_model not in {"all-MiniLM-L6-v2", "onnx-semantic-embedding-v1"}:
                raise ValueError(
                    "The semantic provider supports the existing all-MiniLM-L6-v2 model only"
                )
        elif self.embedding_provider.lower().strip() not in {"local-hash", "hash", "baseline"}:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
        if self.llm_provider.lower().strip() not in {"extractive", "groq"}:
            raise ValueError(f"Unsupported answer generator provider: {self.llm_provider}")
        if not self.llm_model.strip():
            raise ValueError("llm_model must not be empty")


APPROVED_CLASSIFICATIONS = frozenset({"KEEP", "KEEP_HISTORICAL", "KEEP_METHODOLOGICAL"})


def load_config() -> BrainConfig:
    return BrainConfig()
