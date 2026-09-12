"""Chunk approved Knowledge Base sections without losing provenance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    metadata: dict


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_section_text(text: str, target_chars: int, overlap_chars: int, min_chunk_chars: int) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= target_chars:
        return [text]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        separator_len = 2 if current else 0
        if current and current_len + separator_len + len(paragraph) > target_chars:
            chunks.append("\n\n".join(current).strip())
            overlap = chunks[-1][-overlap_chars:].strip() if overlap_chars else ""
            current = [overlap, paragraph] if overlap else [paragraph]
            current_len = sum(len(item) for item in current) + 2 * (len(current) - 1)
        else:
            current.append(paragraph)
            current_len += separator_len + len(paragraph)
    if current:
        chunks.append("\n\n".join(current).strip())

    repaired: list[str] = []
    for chunk in chunks:
        if repaired and len(chunk) < min_chunk_chars:
            repaired[-1] = normalize_text(repaired[-1] + "\n\n" + chunk)
        else:
            repaired.append(chunk)
    return repaired


def chunks_from_sections(sections: Iterable[dict], *, target_chars: int, overlap_chars: int, min_chunk_chars: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section_index, section in enumerate(sections):
        section_id = section["section_id"]
        for chunk_index, text in enumerate(split_section_text(section["text"], target_chars, overlap_chars, min_chunk_chars)):
            metadata = {
                "section_id": section_id,
                "source_id": section.get("source_id") or "",
                "file_name": section.get("file_name") or "",
                "title": section.get("title") or "",
                "section": section.get("section") or "",
                "subsection": section.get("subsection") or "",
                "page_start": int(section.get("page_start") or 0),
                "page_end": int(section.get("page_end") or 0),
                "page": str(section.get("page_start") or ""),
                "section_classification": section.get("section_classification") or "",
                "knowledge_type": section.get("knowledge_type") or "",
                "time_period": section.get("time_period") or "",
                "geographic_scope": section.get("geographic_scope") or "",
                "source_status": section.get("source_status") or "",
                "relevance": section.get("relevance") or "",
            }
            chunks.append(Chunk(chunk_id=f"{section_id}::chunk-{chunk_index + 1:03d}", text=text, metadata=metadata))
    return chunks
