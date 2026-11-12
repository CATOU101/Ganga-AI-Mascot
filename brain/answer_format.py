"""Deterministic detection of user-requested answer shape and detail."""

from __future__ import annotations

import re
from dataclasses import dataclass


NUMBER_WORDS = {
    "one": 1, "a": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


@dataclass(frozen=True)
class AnswerFormat:
    style: str = "natural"
    detail: str = "normal"
    points: int | None = None
    word_count: int | None = None
    examples: bool = False
    summary: bool = False
    tone: str | None = None

    @property
    def cache_key(self) -> str:
        return f"{self.style}|{self.detail}|{self.points}|{self.word_count}|{self.examples}|{self.summary}|{self.tone}"

    def instructions(self) -> str:
        directions = []
        if self.style == "comparison_table":
            directions.append("Use a compact comparison table with one row per supported comparison criterion.")
        elif self.style == "pros_cons":
            directions.append("Organize the supported advantages and disadvantages under separate headings or columns.")
        elif self.style == "steps":
            directions.append("Present the explanation as logically ordered numbered steps.")
        elif self.style == "bullets":
            directions.append("Use a concise bullet list.")
        elif self.style == "numbered":
            directions.append("Use a concise numbered list.")
        elif self.style == "paragraphs":
            directions.append("Use short paragraphs and no list unless needed for accuracy.")

        if self.points is not None:
            directions.append(
                f"The user requested {self.points} points. Include no more than {self.points}; "
                "if the available evidence supports fewer, give only supported points and say so."
            )
        if self.detail == "brief":
            directions.append("Keep the explanation brief and omit unnecessary background.")
        elif self.detail == "detailed":
            directions.append("Give a detailed but focused explanation, limited to supported facts.")
        elif self.detail == "complex":
            directions.append("Explain the reasoning in depth while staying focused and evidence-based.")
        if self.examples:
            directions.append("Include a short example when it can be given accurately.")
        if self.summary:
            directions.append("End with a one-sentence summary.")
        if self.word_count:
            directions.append(f"Aim for about {self.word_count} words; do not cut off a sentence or citations to meet the target.")
        if self.tone:
            directions.append(f"Use a {self.tone} tone.")
        return " ".join(directions)


def _parse_count(text: str) -> int | None:
    match = re.search(
        r"\b(?:in|give|list|explain|name|provide)?\s*(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:distinct\s+)?(?:points|reasons|causes|steps|examples|ways|items|differences)\b",
        text,
    )
    if not match:
        return None
    token = match.group(1)
    return int(token) if token.isdigit() else NUMBER_WORDS[token]


def strip_answer_formatting_instructions(question: str) -> str:
    """Remove output-shape phrases before retrieval without changing the user prompt."""
    text = re.sub(r"\s+", " ", question or "").strip()
    ending_match = re.search(r"([.?!]+)\s*$", text)
    ending = ending_match.group(1) if ending_match else ""
    if ending_match:
        text = text[:ending_match.start()].rstrip()
    count = r"(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)"
    patterns = (
        rf"\b(?:in|as)\s+(?:{count}\s+)?(?:bullet\s+)?(?:points?|bullets?|a\s+list)\b",
        r"\b(?:in|as)\s+(?:bullet|numbered)\s+(?:points?|list)\b",
        rf"\b(?:{count})\s+(?:distinct\s+)?(?:points|reasons|causes|steps|examples|ways|items|differences)\b",
        r"\b(?:bullet|numbered)\s+(?:points?|list)\b",
    )
    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip(" ,;:") + ending


def detect_answer_format(question: str) -> AnswerFormat:
    text = re.sub(r"\s+", " ", (question or "").casefold()).strip()
    points = _parse_count(text)
    word_match = re.search(r"\b(?:about|around|approximately|exactly|in)\s+(\d{2,4})\s+words?\b", text)
    word_count = int(word_match.group(1)) if word_match else None

    if re.search(r"\b(advantages?\s+and\s+disadvantages?|pros\s+and\s+cons|benefits?\s+and\s+drawbacks?)\b", text):
        style = "pros_cons"
    elif re.search(r"\b(compare|comparison|contrast|versus|vs\.?)\b", text):
        style = "comparison_table"
    elif re.search(r"\bstep[ -]by[ -]step|\bsteps?\s+to\b", text):
        style = "steps"
    elif re.search(r"\b(bullet|bullets|bullet points|in points|as points|in bullets)\b", text):
        style = "bullets"
    elif points is not None:
        style = "numbered"
    elif re.search(r"\b(numbered list|numbered points)\b", text):
        style = "numbered"
    elif re.search(r"\b(paragraph|paragraphs|prose)\b", text):
        style = "paragraphs"
    else:
        style = "natural"

    if re.search(r"\b(briefly|brief|short|in short|concise|quick summary)\b", text):
        detail = "brief"
    elif re.search(r"\b(in detail|detailed|thorough|comprehensive)\b", text):
        detail = "detailed"
    elif (points or 0) >= 8 or re.search(r"\b(step by step|in depth|deep dive)\b", text):
        detail = "complex"
    else:
        detail = "normal"

    tone = next((tone for tone in ("simple", "friendly", "formal", "academic") if re.search(rf"\b{tone}\b", text)), None)
    return AnswerFormat(
        style=style,
        detail=detail,
        points=points,
        word_count=word_count,
        examples=bool(re.search(r"\b(with|include|give)\s+examples?\b|\bfor example\b", text)),
        summary=bool(re.search(r"\b(summarize|summary|key takeaways)\b", text)),
        tone=tone,
    )
