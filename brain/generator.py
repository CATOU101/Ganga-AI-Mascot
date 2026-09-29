"""Modular grounded answer generation and provenance citation assembly."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from abc import ABC, abstractmethod

from .prompts import CURRENT_INFO_MESSAGE, GROUNDING_SYSTEM_PROMPT, INSUFFICIENT_EVIDENCE
from .retriever import extract_keywords


class Generator(ABC):
    @abstractmethod
    def generate(self, question: str, hits: list[dict], is_sufficient: bool = True) -> dict:
        raise NotImplementedError


def citations_from_hits(hits: list[dict]) -> list[dict]:
    """Build unique citation metadata objects from active evidence hits."""
    citations = []
    seen = set()
    for hit in hits:
        md = hit.get("metadata", {})
        key = (md.get("title"), md.get("file_name"), md.get("page_start"), md.get("page_end"), md.get("section"))
        if key in seen:
            continue
        seen.add(key)
        citations.append({
            "source": md.get("title") or "GRBMP Report",
            "file_name": md.get("file_name") or "",
            "page": f"{md.get('page_start')}-{md.get('page_end')}" if md.get("page_start") else str(md.get("page", "")),
            "section": md.get("section") or "",
            "knowledge_type": md.get("knowledge_type") or "",
        })
    return citations


def clean_hit_text(text: str) -> str:
    """Clean raw hit text by stripping OCR artifacts, report codes, page markers, and running headers."""
    text = re.sub(r"\[Page \d+\]", "", text)
    text = re.sub(r"Report\s*Code\s*:\s*[^\n]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{3}_GBP_IIT_[^\n]+", "", text)
    text = re.sub(r"\b(?:\d+\s*)?\|\s*P\s*a\s*g\s*e\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"GRBMP\s*[\u2013\u2014-]\s*[^\n.]+", "", text)
    return text


class ExtractiveGenerator(Generator):
    """Grounded local generator that summarizes by extracting supported sentences."""

    def generate(self, question: str, hits: list[dict], is_sufficient: bool = True) -> dict:
        if not is_sufficient or not hits:
            return {"answer": INSUFFICIENT_EVIDENCE, "citations": [], "mode": "insufficient-evidence"}

        keywords = set(extract_keywords(question))
        sentences: list[str] = []
        contributing_hits: list[dict] = []
        seen_sentences = set()

        for hit in hits:
            text = hit["text"]
            hit_contributed = False
            clean_text = clean_hit_text(text)
            
            for sentence in re.split(r"(?<=[.!?])\s+", clean_text):
                clean = sentence.strip()
                clean = re.sub(r"^\s*\d+(\.\d+)*\s+", "", clean)
                clean = re.sub(r"\s+", " ", clean).strip()
                if len(clean) < 35 or clean in seen_sentences:
                    continue
                
                # Check match against query keywords or general relevance
                clean_lower = clean.lower()
                matches = sum(1 for kw in keywords if kw in clean_lower) if keywords else 1
                
                if matches > 0:
                    sentences.append(clean)
                    seen_sentences.add(clean)
                    hit_contributed = True
                    if len(sentences) >= 4:
                        break
            
            if hit_contributed and hit not in contributing_hits:
                contributing_hits.append(hit)
            if len(sentences) >= 4:
                break

        # Fallback if no matching sentences could be cleanly extracted
        if not sentences:
            # Fallback to top hit text if valid
            if hits:
                top_text = clean_hit_text(hits[0]["text"]).strip()
                first_few = [re.sub(r"^\s*\d+(\.\d+)*\s+", "", s.strip()).strip() for s in re.split(r"(?<=[.!?])\s+", top_text) if len(s.strip()) >= 35][:2]
                if first_few:
                    sentences = first_few
                    contributing_hits = [hits[0]]

        if not sentences or not contributing_hits:
            return {"answer": INSUFFICIENT_EVIDENCE, "citations": [], "mode": "insufficient-evidence"}

        answer = " ".join(sentences[:4])

        # Explicitly distinguish historical information
        if any((hit["metadata"].get("knowledge_type") or "").upper() == "HISTORICAL" for hit in contributing_hits):
            if not answer.startswith("From the retrieved historical"):
                answer = "From the retrieved historical GRBMP material: " + answer

        return {
            "answer": answer,
            "citations": citations_from_hits(contributing_hits),
            "mode": "grounded",
        }



class OpenAIChatGenerator(Generator):
    """Optional OpenAI-compatible generator using environment variables."""

    def __init__(self, model: str | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required when GANGA_BRAIN_LLM_PROVIDER=openai")

    def generate(self, question: str, hits: list[dict], is_sufficient: bool = True) -> dict:
        from .retriever import assemble_context

        if not is_sufficient or not hits:
            return {"answer": INSUFFICIENT_EVIDENCE, "citations": [], "mode": "insufficient-evidence"}

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
                {"role": "user", "content": f"Question:\n{question}\n\nRetrieved context:\n{assemble_context(hits)}"},
            ],
            "temperature": 0,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))

        return {
            "answer": data["choices"][0]["message"]["content"],
            "citations": citations_from_hits(hits),
            "mode": "grounded",
        }


def build_generator(provider: str, model: str) -> Generator:
    prov_clean = (provider or "extractive").lower().strip()
    if prov_clean == "extractive":
        return ExtractiveGenerator()
    if prov_clean == "openai":
        return OpenAIChatGenerator(model)
    raise ValueError(f"Unsupported generator provider: {provider}")


def current_information_response() -> dict:
    return {"answer": CURRENT_INFO_MESSAGE, "citations": [], "mode": "current-info-fallback"}


def insufficient_evidence_response() -> dict:
    return {"answer": INSUFFICIENT_EVIDENCE, "citations": [], "mode": "insufficient-evidence"}
