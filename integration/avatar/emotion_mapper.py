"""Emotion mapping logic for Mascot Avatar expressions."""

from __future__ import annotations

import logging
from integration.models.brain_response import EmotionType

logger = logging.getLogger("integration.emotion_mapper")

SUPPORTED_EMOTIONS = {
    "neutral": EmotionType.NEUTRAL,
    "happy": EmotionType.HAPPY,
    "sad": EmotionType.SAD,
    "thinking": EmotionType.THINKING,
}


def map_emotion(raw_emotion: str | None, mode: str | None = None) -> EmotionType:
    """Map arbitrary emotion string or response mode to supported EmotionType with neutral fallback."""
    if not raw_emotion:
        if mode == "insufficient-evidence":
            return EmotionType.THINKING
        return EmotionType.NEUTRAL

    clean_emotion = str(raw_emotion).strip().lower()
    if clean_emotion in SUPPORTED_EMOTIONS:
        return SUPPORTED_EMOTIONS[clean_emotion]

    logger.warning(f"[Integration Emotion] Unknown emotion '{raw_emotion}'. Falling back to 'neutral'.")
    return EmotionType.NEUTRAL
