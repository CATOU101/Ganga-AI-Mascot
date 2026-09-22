"""Domain models and data transfer contracts for Integration layer."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ConversationState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


class EmotionType(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    THINKING = "thinking"


class GestureType(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXPLAINING = "explaining"
    WAVE = "wave"


class CitationItem(BaseModel):
    source: str | None = Field(None, description="Document title")
    file_name: str | None = Field(None, description="Source PDF file name")
    page: str | None = Field(None, description="Page number or range")
    section: str | None = Field(None, description="Section title or ID")
    knowledge_type: str | None = Field(None, description="Classification context: HISTORICAL, METHODOLOGICAL, etc.")


class BrainRequest(BaseModel):
    question: str = Field(..., description="Question prompt to Ganga Brain RAG")
    language: str = Field("hi", description="Target language ('hi' | 'en')")
    top_k: int | None = Field(None, description="Retriever candidate override")


class BrainResponse(BaseModel):
    answer: str = Field(..., description="Grounded answer text")
    mode: str = Field("grounded", description="Response mode: 'grounded' | 'insufficient-evidence' | 'current-info-fallback'")
    citations: list[CitationItem] = Field(default_factory=list, description="List of source citations")
    language: str = Field("hi", description="Language code")
    emotion: EmotionType = Field(EmotionType.NEUTRAL, description="Avatar emotion state")
    gesture: GestureType = Field(GestureType.IDLE, description="Avatar gesture animation")


class AvatarPresentation(BaseModel):
    state: ConversationState = Field(ConversationState.IDLE, description="Current conversation state")
    question: str = Field("", description="User question string")
    answer: str = Field("", description="Grounded answer text")
    mode: str = Field("grounded", description="Brain mode")
    citations: list[CitationItem] = Field(default_factory=list, description="Provenance citations")
    language: str = Field("hi", description="Language")
    emotion: EmotionType = Field(EmotionType.NEUTRAL, description="Emotion expression")
    gesture: GestureType = Field(GestureType.IDLE, description="Gesture pose")
    audio_data_base64: str | None = Field(None, description="Synthesized TTS audio payload if available")
    rms_lip_sync: list[float] = Field(default_factory=list, description="Calculated lip-sync RMS frames")
    error_message: str | None = Field(None, description="User-facing error details if failed")
