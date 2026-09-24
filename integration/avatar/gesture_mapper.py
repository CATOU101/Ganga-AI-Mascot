"""Gesture mapping logic for Mascot Avatar animations."""

from __future__ import annotations

import logging
from integration.models.brain_response import GestureType

logger = logging.getLogger("integration.gesture_mapper")

SUPPORTED_GESTURES = {
    # 9 Member 2 Production Actions
    "idle": GestureType.IDLE,
    "chacha_idle": GestureType.IDLE,
    "nod": GestureType.NOD,
    "chacha_nod": GestureType.NOD,
    "point": GestureType.POINT,
    "chacha_point": GestureType.POINT,
    "shrug": GestureType.SHRUG,
    "chacha_shrug": GestureType.SHRUG,
    "thinking": GestureType.THINKING,
    "chacha_thinking": GestureType.THINKING,
    "laughing": GestureType.LAUGHING,
    "chacha_laughing": GestureType.LAUGHING,
    "wave": GestureType.WAVE,
    "waving": GestureType.WAVE,
    "chacha_waving": GestureType.WAVE,
    "thankful": GestureType.THANKFUL,
    "chacha_thankful": GestureType.THANKFUL,
    "shaking_hands": GestureType.SHAKING_HANDS,
    "shakinghands": GestureType.SHAKING_HANDS,
    "chacha_shakinghands": GestureType.SHAKING_HANDS,
    # Semantic aliases
    "greeting": GestureType.WAVE,
    "greet": GestureType.WAVE,
    "hello": GestureType.WAVE,
    "hi": GestureType.WAVE,
    "namaste": GestureType.THANKFUL,
    "thanks": GestureType.THANKFUL,
    "thank_you": GestureType.THANKFUL,
    "agree": GestureType.NOD,
    "yes": GestureType.NOD,
    "doubt": GestureType.SHRUG,
    "uncertain": GestureType.SHRUG,
    "handshake": GestureType.SHAKING_HANDS,
    "shake_hands": GestureType.SHAKING_HANDS,
    # Legacy fallbacks
    "explaining": GestureType.EXPLAINING,
    "hand": GestureType.POINT,
    "gesture": GestureType.POINT,
    "turn": GestureType.IDLE,
}


def map_gesture(raw_gesture: str | GestureType | None, mode: str | None = None) -> GestureType:
    """Map arbitrary gesture string or response mode to supported GestureType with idle fallback."""
    if isinstance(raw_gesture, GestureType):
        val = raw_gesture.value
    elif hasattr(raw_gesture, "value"):
        val = str(getattr(raw_gesture, "value"))
    else:
        val = str(raw_gesture) if raw_gesture is not None else ""

    clean_gesture = val.strip().lower()
    if clean_gesture in SUPPORTED_GESTURES:
        mapped = SUPPORTED_GESTURES[clean_gesture]
        if mapped == GestureType.IDLE:
            if mode == "grounded":
                return GestureType.EXPLAINING
            elif mode in ("insufficient-evidence", "current-info-fallback"):
                return GestureType.THINKING
        return mapped

    if mode == "grounded":
        return GestureType.EXPLAINING
    elif mode in ("insufficient-evidence", "current-info-fallback"):
        return GestureType.THINKING

    if raw_gesture:
        logger.warning(f"[Integration Gesture] Unknown gesture '{raw_gesture}'. Falling back to 'idle'.")
    return GestureType.IDLE

