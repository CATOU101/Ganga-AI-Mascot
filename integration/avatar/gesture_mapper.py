"""Gesture mapping logic for Mascot Avatar animations."""

from __future__ import annotations

import logging
from integration.models.brain_response import GestureType

logger = logging.getLogger("integration.gesture_mapper")

SUPPORTED_GESTURES = {
    "idle": GestureType.IDLE,
    "thinking": GestureType.THINKING,
    "explaining": GestureType.EXPLAINING,
    "wave": GestureType.WAVE,
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
