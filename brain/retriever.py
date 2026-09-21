"""Retriever, hybrid candidate reranking, evidence quality gate, and context assembly."""

from __future__ import annotations

import re

from .config import BrainConfig
from .vector_store import ChromaVectorStore, get_chroma_vector_store


CURRENT_TERMS = (
    "current", "today", "now", "latest", "real-time", "realtime", "present status",
    "water quality", "river discharge", "stp status", "pollution monitoring",
    "programme status", "program status", "infrastructure status", "legal status",
    "regulatory status",
)

STOPWORDS = frozenset({
    "what", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "the", "a", "an", "in", "on", "at", "of", "to", "for", "with",
    "by", "from", "about", "according", "which", "where", "when", "who", "whom",
    "why", "how", "this", "that", "these", "those", "tell", "tells", "say", "says",
    "give", "me", "us", "you", "your", "can", "could", "would", "should", "material",
    "kb", "knowledge", "base", "grbmp",
})

SPECIFIC_TOPIC_TERMS = frozenset({
    "aviral", "dhara", "nirmal", "ngrba", "dolphin", "fish", "hilsa", "agriculture",
    "pesticide", "sanitation", "sewage", "stp", "treatment", "flood", "landslide",
    "disaster", "cremation", "hazard", "swot", "legal", "legislation", "law", "act",
    "ordinance", "judgement", "court", "institution", "governance", "model", "policy",
    "mining", "tannery", "industrial", "effluent", "wetland", "afforestation",
    "tributary", "tributaries", "monitoring", "station", "discharge", "quality",
    "dissolved", "oxygen", "bod", "cod",
})

CORE_OVERVIEW_FILES = (
    "13_GRBMP - MPD.pdf",
    "25_GRBMPInterim_Rep.pdf",
    "27_GRBMP - Extended Summary.pdf",
    "29_2014-06-13_GRBMP_Extended Summary.pdf",
    "Vision Ganga Eng_Compressed.pdf",
    "33_43_001_GEN_DAT_01.pdf",
)

CORE_OVERVIEW_TITLES = (
    "main plan document",
    "interim report",
    "extended summary",
    "vision ganga",
    "river ganga at a glance",
)

OVERVIEW_SECTIONS = (
    "defining river ganga",
    "key features of national river ganga basin",
    "river ganga in basin perspective",
    "vision",
    "chapter i",
    "1. introduction",
)


def is_broad_ganga_query(question: str) -> bool:
    """Detect queries seeking a broad or general overview of the Ganga River."""
    lowered = question.lower()
    has_domain = "ganga" in lowered or "river" in lowered
    if not has_domain:
        return False
    tokens = set(re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", lowered))
    if tokens & SPECIFIC_TOPIC_TERMS:
        return False
    return True


def is_core_overview_hit(hit: dict) -> bool:
    """Identify whether candidate hit comes from core overview material."""
    fn = str(hit.get("metadata", {}).get("file_name", "")).lower()
    title = str(hit.get("metadata", {}).get("title", "")).lower()
    section = str(hit.get("metadata", {}).get("section", "")).lower()

    file_match = any(f.lower() in fn for f in CORE_OVERVIEW_FILES)
    title_match = any(t in title for t in CORE_OVERVIEW_TITLES)
    sec_match = any(s in section for s in OVERVIEW_SECTIONS)

    return (file_match or title_match) or (sec_match and ("main plan" in title or "summary" in title or "glance" in title or "interim" in title))


def asks_for_current_information(question: str) -> bool:
    """Detect queries seeking current or real-time status."""
    lowered = question.lower()
    dynamic_topic = any(term in lowered for term in CURRENT_TERMS[5:])
    freshness = any(term in lowered for term in CURRENT_TERMS[:5])
    return dynamic_topic and freshness


def extract_keywords(question: str) -> list[str]:
    """Extract non-stopword query keywords for lexical grounding check."""
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", question.lower())
    return [token for token in tokens if len(token) >= 3 and token not in STOPWORDS]


def extract_all_query_terms(question: str) -> list[str]:
    """Extract all query words >= 3 chars including domain words for strict entity checks."""
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", question.lower())
    ignore = {"what", "is", "are", "was", "were", "the", "a", "an", "in", "on", "at", "of", "to", "for", "with", "by", "from", "according"}
    return [token for token in tokens if len(token) >= 3 and token not in ignore]


class Retriever:
    def __init__(self, config: BrainConfig, store: ChromaVectorStore | None = None) -> None:
        self.config = config
        self.store = store or get_chroma_vector_store(config)

    def retrieve_candidates(self, question: str, candidate_k: int | None = None) -> list[dict]:
        """Retrieve candidates from Chroma vector store."""
        k = candidate_k or self.config.candidate_top_k
        return self.store.query(question, k)

    def rerank_and_filter(self, question: str, hits: list[dict], top_k: int | None = None) -> tuple[bool, list[dict]]:
        """Rerank candidates using vector similarity and lexical term coverage, then evaluate evidence gate."""
        target_k = top_k or self.config.top_k
        keywords = extract_keywords(question)
        all_terms = extract_all_query_terms(question)

        if not hits or not question.strip():
            return False, []

        # Out-of-domain / Unsupported topic check:
        # Require that at least 60% of query keywords appear somewhere in the candidate pool.
        if keywords:
            pool_terms_found = sum(
                1 for kw in keywords
                if any(kw in (hit["text"] + " " + str(hit["metadata"].get("title", "")) + " " + str(hit["metadata"].get("section", ""))).lower() for hit in hits)
            )
            pool_coverage = pool_terms_found / len(keywords)
            if pool_coverage < 0.60:
                return False, []

        is_broad = is_broad_ganga_query(question)

        scored_hits = []
        for hit in hits:
            content_lower = (hit["text"] + " " + str(hit["metadata"].get("title", "")) + " " + str(hit["metadata"].get("section", ""))).lower()
            if keywords:
                matched_count = sum(1 for kw in keywords if kw in content_lower)
                overlap_ratio = matched_count / len(keywords)
            else:
                matched_count = 0
                overlap_ratio = 1.0

            distance = hit.get("distance", 999.0)
            # Distance threshold depending on embedding type
            is_semantic = getattr(self.store.embedding, "name", "").startswith("onnx")
            max_dist = self.config.evidence_max_distance if is_semantic else 1.35

            if distance > max_dist:
                continue

            # Calculate hybrid score with mild overview preference for broad queries
            base_score = (1.0 / (1.0 + distance)) + (0.5 * overlap_ratio)
            overview_boost = 0.25 if (is_broad and is_core_overview_hit(hit)) else 0.0
            hybrid_score = base_score + overview_boost

            scored_hits.append((hybrid_score, overlap_ratio, hit))

        if not scored_hits:
            return False, []

        # Sort by hybrid score descending
        scored_hits.sort(key=lambda item: item[0], reverse=True)

        # Evidence Gate Check: top result must have sufficient relevance
        top_score, top_overlap, top_hit = scored_hits[0]
        if keywords and top_overlap < self.config.min_keyword_overlap and len(keywords) > 1:
            return False, []

        reranked_hits = [hit for _, _, hit in scored_hits[:target_k]]
        return True, reranked_hits

    def retrieve(self, question: str, top_k: int | None = None) -> tuple[bool, list[dict]]:
        candidates = self.retrieve_candidates(question)
        return self.rerank_and_filter(question, candidates, top_k)


def assemble_context(hits: list[dict], max_chars: int = 6000) -> str:
    """Assemble retrieved hits into context block for answer generation."""
    parts = []
    used = 0
    for index, hit in enumerate(hits, start=1):
        metadata = hit["metadata"]
        header = (
            f"[{index}] Source: {metadata.get('title')}\n"
            f"File: {metadata.get('file_name')}\n"
            f"Page: {metadata.get('page_start')}-{metadata.get('page_end')}\n"
            f"Section: {metadata.get('section')}\n"
            f"Knowledge type: {metadata.get('knowledge_type')}\n"
        )
        body = hit["text"].strip()
        block = f"{header}\n{body}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n---\n\n".join(parts)

