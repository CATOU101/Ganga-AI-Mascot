"""Unit tests for emotion and gesture mappers."""

import pytest
from integration.avatar.emotion_mapper import map_emotion
from integration.avatar.gesture_mapper import map_gesture
from integration.models.brain_response import EmotionType, GestureType


def test_emotion_mapper():
    assert map_emotion("happy") == EmotionType.HAPPY
    assert map_emotion("thinking") == EmotionType.THINKING
    assert map_emotion("sad") == EmotionType.SAD
    assert map_emotion("neutral") == EmotionType.NEUTRAL
    assert map_emotion("INVALID_EMOTION") == EmotionType.NEUTRAL
    assert map_emotion(None, mode="insufficient-evidence") == EmotionType.THINKING


def test_gesture_mapper():
    assert map_gesture("wave") == GestureType.WAVE
    assert map_gesture("thinking") == GestureType.THINKING
    assert map_gesture("explaining") == GestureType.EXPLAINING
    assert map_gesture("idle") == GestureType.IDLE
    assert map_gesture("UNKNOWN_ANIMATION") == GestureType.IDLE
    assert map_gesture(None, mode="grounded") == GestureType.EXPLAINING
