"""Read-only document and section views over the approved Brain index."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from brain.config import APPROVED_CLASSIFICATIONS


CHUNK_NUMBER_RE = re.compile(r"::chunk-(\d+)$")
WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
SEARCH_STOP_WORDS = {"a", "an", "and", "about", "at", "by", "for", "from", "how", "in", "is", "of", "on", "or", "the", "to", "what", "which", "with", "your"}


def _chunk_number(chunk: dict[str, Any], fallback: int) -> tuple[int, int]:
    match = CHUNK_NUMBER_RE.search(str(chunk.get("chunk_id") or ""))
    return (int(match.group(1)), fallback) if match else (fallback, fallback)


def _join_section_chunks(chunks: list[dict[str, Any]], overlap_chars: int) -> str:
    ordered = [item for _, item in sorted(enumerate(chunks), key=lambda pair: _chunk_number(pair[1], pair[0]))]
    text = ""
    for chunk in ordered:
        part = str(chunk.get("text") or "").strip()
        if not part:
            continue
        overlap = text[-overlap_chars:].strip() if text and overlap_chars else ""
        if overlap and part.startswith(overlap):
            part = part[len(overlap):].lstrip()
        if part:
            text = f"{text.rstrip()}\n\n{part}" if text else part
    return text.strip()


def _public_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return only citation and approved-section metadata, never index internals."""
    return {
        "title": str(metadata.get("title") or ""),
        "file_name": str(metadata.get("file_name") or ""),
        "source_id": str(metadata.get("source_id") or "") or None,
        "section": str(metadata.get("section") or ""),
        "subsection": str(metadata.get("subsection") or "") or None,
        "page_start": int(metadata.get("page_start") or 0) or None,
        "page_end": int(metadata.get("page_end") or 0) or None,
        "classification": str(metadata.get("section_classification") or ""),
        "knowledge_type": str(metadata.get("knowledge_type") or ""),
        "time_period": str(metadata.get("time_period") or "") or None,
        "geographic_scope": str(metadata.get("geographic_scope") or "") or None,
        "description": str(metadata.get("relevance") or "") or None,
    }


class ResourceCatalog:
    """Group the approved index by document and original section."""

    def __init__(
        self,
        chunks: list[dict[str, Any]],
        *,
        overlap_chars: int = 180,
        approved_section_ids: set[str] | None = None,
    ) -> None:
        section_chunks: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        section_metadata: dict[tuple[str, str], dict[str, Any]] = {}
        approved_chunk_count = 0
        for chunk in chunks:
            metadata = chunk.get("metadata") or {}
            section_id = str(metadata.get("section_id") or "")
            classification = str(metadata.get("section_classification") or "")
            if classification not in APPROVED_CLASSIFICATIONS:
                continue
            if approved_section_ids is not None and section_id not in approved_section_ids:
                continue
            approved_chunk_count += 1
            file_name = str(metadata.get("file_name") or "")
            if not file_name or not section_id:
                continue
            key = (file_name, section_id)
            section_chunks[key].append(chunk)
            section_metadata.setdefault(key, metadata)

        documents: dict[str, dict[str, Any]] = {}
        for key, items in section_chunks.items():
            metadata = _public_metadata(section_metadata[key])
            if not metadata["title"] or not metadata["section"]:
                continue
            section = {
                **metadata,
                "text": _join_section_chunks(items, overlap_chars),
            }
            document = documents.setdefault(metadata["file_name"], {
                "title": metadata["title"],
                "file_name": metadata["file_name"],
                "source_id": metadata["source_id"],
                "sections": [],
            })
            document["sections"].append(section)

        self.chunks_count = approved_chunk_count
        self.documents = []
        for document in documents.values():
            document["sections"].sort(key=lambda item: (item["page_start"] or 0, item["section"].casefold()))
            sections = document["sections"]
            document["section_count"] = len(sections)
            document["classifications"] = sorted({item["classification"] for item in sections if item["classification"]})
            document["knowledge_types"] = sorted({item["knowledge_type"] for item in sections if item["knowledge_type"]})
            document["time_periods"] = sorted({item["time_period"] for item in sections if item["time_period"]})
            document["geographic_scopes"] = sorted({item["geographic_scope"] for item in sections if item["geographic_scope"]})
            descriptions = [item["description"] for item in sections if item["description"]]
            document["description"] = descriptions[0] if descriptions else None
            self.documents.append(document)
        self.documents.sort(key=lambda item: (item["title"].casefold(), item["file_name"].casefold()))
        self.sections = [section for document in self.documents for section in document["sections"]]

    def document_list(self) -> dict[str, Any]:
        public_documents = []
        for item in self.documents:
            public_documents.append({key: value for key, value in item.items() if key != "sections"})
        return {
            "counts": {
                "documents": len(self.documents),
                "approved_sections": len(self.sections),
                "indexed_chunks": self.chunks_count,
            },
            "documents": public_documents,
        }

    def get_document(self, file_name: str) -> dict[str, Any] | None:
        return next((item for item in self.documents if item["file_name"] == file_name), None)

    @staticmethod
    def _excerpt(text: str, query_terms: list[str], limit: int = 760) -> str:
        if len(text) <= limit:
            return text
        lowered = text.casefold()
        positions = [lowered.find(term) for term in query_terms if lowered.find(term) >= 0]
        start = max(0, min(positions) - 160) if positions else 0
        end = min(len(text), start + limit)
        if start:
            paragraph_start = text.rfind("\n\n", 0, start)
            if paragraph_start >= start - 220:
                start = paragraph_start + 2
        if end < len(text):
            boundary = text.rfind(". ", start + limit // 2, end)
            if boundary > start:
                end = boundary + 1
        prefix = "…" if start else ""
        suffix = "…" if end < len(text) else ""
        return prefix + text[start:end].strip() + suffix

    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        normalized = " ".join((query or "").split()).casefold()
        terms = [term for term in dict.fromkeys(WORD_RE.findall(normalized)) if term not in SEARCH_STOP_WORDS]
        if not terms:
            return []
        scored = []
        for section in self.sections:
            searchable = f"{section['title']} {section['file_name']} {section['section']} {section['subsection'] or ''} {section['text']}".casefold()
            matched = sum(term in searchable for term in terms)
            if not matched:
                continue
            title_text = section["title"].casefold()
            section_text = f"{section['section']} {section['subsection'] or ''}".casefold()
            metadata = {key: value for key, value in section.items() if key != "text"}
            score = matched + 3 * sum(term in title_text for term in terms) + 4 * sum(term in section_text for term in terms)
            scored.append((score, metadata, section["text"]))
        scored.sort(key=lambda item: (-item[0], item[1]["title"].casefold(), item[1]["page_start"] or 0))
        return [
            {**metadata, "excerpt": self._excerpt(text, terms)}
            for _, metadata, text in scored[:max(1, min(limit, 50))]
        ]
