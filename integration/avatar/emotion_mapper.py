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


def map_emotion(
    raw_emotion: str | EmotionType | None,
    mode: str | None = None,
    text: str | None = None,
) -> EmotionType:
    """Map arbitrary emotion string, response mode, and conversational text to supported EmotionType."""
    if isinstance(raw_emotion, EmotionType):
        val = raw_emotion.value
    elif hasattr(raw_emotion, "value"):
        val = str(getattr(raw_emotion, "value"))
    else:
        val = str(raw_emotion) if raw_emotion is not None else ""

    clean_emotion = val.strip().lower()
    if clean_emotion in SUPPORTED_EMOTIONS and clean_emotion != "neutral":
        return SUPPORTED_EMOTIONS[clean_emotion]

    if mode in ("insufficient-evidence", "current-info-fallback"):
        return EmotionType.THINKING

    if text:
        t_low = text.lower()
        if any(w in t_low for w in ("namaste", "hello", "welcome", "pranam", "greetings", "नमस्ते", "नमस्कार", "प्रणाम", "स्वागत", "बधाई", "congratulations", "shandaar", "delighted", "happy")):
            return EmotionType.HAPPY
        if any(w in t_low for w in ("warning", "alert", "danger", "prohibited", "severely polluted", "chetavni", "savdhaan", "चेतावनी", "सावधान")):
            return EmotionType.SURPRISED
        if any(w in t_low for w in ("sorry", "apologize", "kshama", "maaf", "क्षमा", "माफ़")):
            return EmotionType.CONFUSED

    if clean_emotion == "neutral":
        return EmotionType.NEUTRAL

    if raw_emotion:
        logger.warning(f"[Integration Emotion] Unknown emotion '{raw_emotion}'. Falling back to 'happy' or 'neutral'.")
    return EmotionType.HAPPY if mode == "grounded" else EmotionType.NEUTRAL

