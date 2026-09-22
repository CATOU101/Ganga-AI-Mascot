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


def map_gesture(raw_gesture: str | None, mode: str | None = None) -> GestureType:
    """Map arbitrary gesture string or response mode to supported GestureType with idle fallback."""
    if not raw_gesture:
        if mode == "grounded":
            return GestureType.EXPLAINING
        elif mode == "insufficient-evidence":
            return GestureType.THINKING
        return GestureType.IDLE

    clean_gesture = str(raw_gesture).strip().lower()
    if clean_gesture in SUPPORTED_GESTURES:
        return SUPPORTED_GESTURES[clean_gesture]

    logger.warning(f"[Integration Gesture] Unknown gesture '{raw_gesture}'. Falling back to 'idle'.")
    return GestureType.IDLE
