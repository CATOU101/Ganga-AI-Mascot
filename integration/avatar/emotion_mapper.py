"""Emotion mapping logic for Mascot Avatar expressions."""

from __future__ import annotations

import logging
from integration.models.brain_response import EmotionType

logger = logging.getLogger("integration.emotion_mapper")

SUPPORTED_EMOTIONS = {
    "neutral": EmotionType.NEUTRAL,
    "happy": EmotionType.HAPPY,
    "sad": EmotionType.SAD,
    "angry": EmotionType.ANGRY,
    "surprised": EmotionType.SURPRISED,
    "confused": EmotionType.CONFUSED,
    "thinking": EmotionType.THINKING,
    "laughing": EmotionType.LAUGHING,
}


def map_emotion(raw_emotion: str | EmotionType | None, mode: str | None = None) -> EmotionType:
    """Map arbitrary emotion string or response mode to supported EmotionType with neutral fallback."""
    if isinstance(raw_emotion, EmotionType):
        val = raw_emotion.value
    elif hasattr(raw_emotion, "value"):
        val = str(getattr(raw_emotion, "value"))
    else:
        val = str(raw_emotion) if raw_emotion is not None else ""

    clean_emotion = val.strip().lower()
    if clean_emotion in SUPPORTED_EMOTIONS:
        mapped = SUPPORTED_EMOTIONS[clean_emotion]
        if mapped == EmotionType.NEUTRAL and mode in ("insufficient-evidence", "current-info-fallback"):
            return EmotionType.THINKING
        return mapped

    if mode in ("insufficient-evidence", "current-info-fallback"):
        return EmotionType.THINKING

    if raw_emotion:
        logger.warning(f"[Integration Emotion] Unknown emotion '{raw_emotion}'. Falling back to 'happy' or 'neutral'.")
    return EmotionType.HAPPY if mode == "grounded" else EmotionType.NEUTRAL
