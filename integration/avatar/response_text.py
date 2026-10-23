"""Presentation-safe deterministic conversion from display copy to narration."""

from __future__ import annotations

import re


def spoken_response(text: str) -> str:
    """Remove common markdown artifacts while retaining the answer's wording."""
    value = text or ""
    value = re.sub(r"```(?:\w+)?\s*([\s\S]*?)```", r"\1", value)
    value = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"^\s{0,3}#{1,6}\s*", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*[-*+]\s+", "", value, flags=re.MULTILINE)
    value = re.sub(r"^\s*\d+[.)]\s+", "", value, flags=re.MULTILINE)
    value = re.sub(r"(?<!\w)[*_~`]{1,3}([^*_~`]+)[*_~`]{1,3}(?!\w)", r"\1", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([,.!?;:])", r"\1", value)
    value = re.sub(r"([.!?])(?:\s*\1)+", r"\1", value)
    return value.strip()
