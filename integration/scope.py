"""Small, explicit routing rules for assistant identity and unsupported topics."""

from __future__ import annotations

import re


IDENTITY_PATTERNS = (
    r"\bwho are you\b", r"\bwhat are you\b", r"\byour name\b",
    r"\bwho is chacha(?: chaudhary)?\b", r"\bwhat is chacha(?: chaudhary)?\b",
    r"\bwhat is your purpose\b", r"\bwhy were you created\b",
    r"\bwhat can you help me with\b", r"\bwhat can you do\b",
    r"\bwhat is your mission\b", r"\byour capabilities\b",
)
WATER_QUALITY_TERMS = (
    "water quality", "water level", "water depth", "ph", "bod", "dissolved oxygen",
    "water reading", "water readings", "water pollution", "monitoring data",
)
OTHER_WATER_BODIES = (
    "yamuna", "brahmaputra", "indus", "godavari", "krishna", "kaveri", "cauvery",
    "narmada", "tapi", "mahanadi", "sabarmati", "chenab", "sutlej", "beas",
    "ghaghara", "gandak", "kosi", "son river", "lake", "reservoir",
)
PROJECT_DOMAIN_TERMS = (
    "sewage treatment", "stp", "wastewater", "waste water", "sewage", "effluent",
    "river pollution", "pollution in rivers", "river conservation", "river basin",
    "ganga action plan", "namami gange", "nmcg", "ngrba", "grbmp",
)


def classify_request(question: str) -> str | None:
    """Return an explicit route label, or None for the existing Ganga RAG path."""
    text = re.sub(r"\s+", " ", (question or "").casefold()).strip()
    if any(re.search(pattern, text) for pattern in IDENTITY_PATTERNS):
        return "identity"

    if any(term in text for term in WATER_QUALITY_TERMS):
        mentions_ganga = any(term in text for term in ("ganga", "ganges", "namami gange", "nmcg"))
        mentions_other = any(term in text for term in OTHER_WATER_BODIES)
        if mentions_other and not mentions_ganga:
            return "unsupported-water-topic"

    mentions_ganga = any(term in text for term in ("ganga", "ganges", "namami gange", "nmcg"))
    if not mentions_ganga and any(re.search(rf"\b{re.escape(river)}\b", text) for river in OTHER_WATER_BODIES):
        return "other-river-context"

    if not any(term in text for term in (
        "ganga", "ganges", "namami", "nmcg", "ngrba", "grbmp", "river basin",
        "aviral dhara", "nirmal dhara", "ganga action plan",
        "cpcb", "water quality", "water level", "water depth", "monitoring",
        "dissolved oxygen", "bod", "ph", "haridwar", "kanpur", "ghazipur",
        "farakka", "nabadwip",
    )) and not any(term in text for term in PROJECT_DOMAIN_TERMS):
        return "general"
    return None


def identity_response(question: str) -> str:
    text = (question or "").casefold()
    if "chacha" in text:
        return (
            "Chacha Chaudhary is the friendly guide persona used in this project. "
            "I’m the AI assistant behind the Ganga AI Mascot experience."
        )
    if any(term in text for term in ("purpose", "created", "mission", "help", "capabilit", "can you do")):
        return (
            "I’m the Ganga AI Mascot, a guide focused on the Ganga, Namami Gange, and river conservation. "
            "I answer domain questions from the project’s verified knowledge base and can present available CPCB monitoring data. "
            "My knowledge-base answers are limited to the evidence and dates in their cited sources."
        )
    return "I’m the Ganga AI Mascot, a conversational guide focused on the Ganga, Namami Gange, and river conservation."


def scope_response(route: str, question: str) -> str:
    if route == "unsupported-water-topic":
        return (
            "The verified knowledge base does not currently contain supported monitoring information for that river or water body. "
            "I focus on the Ganga and the monitoring information available to this project."
        )
    return "I mainly help with the Ganga, Namami Gange, and river conservation. Please ask me about one of those topics."
