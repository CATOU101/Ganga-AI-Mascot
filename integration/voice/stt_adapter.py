"""Speech-to-Text (STT) interface and adapters."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("integration.stt_adapter")


class STTAdapter(ABC):
    @abstractmethod
    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "hi") -> str:
        """Convert audio bytes into transcribed text string."""
        raise NotImplementedError


class MockSTTAdapter(STTAdapter):
    """Fallback / testing STT adapter returning pre-configured or sample transcriptions."""

    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "hi") -> str:
        logger.info(f"[Integration STT] Transcribing audio with MockSTTAdapter (Language: {language})")
        if not audio_bytes or len(audio_bytes) == 0:
            logger.warning("[Integration STT] Received empty audio bytes.")
            return ""
        
        if language == "hi":
            return "अविरल धारा क्या है?"
        return "What is Aviral Dhara?"


class WebSpeechSTTAdapter(STTAdapter):
    """Adapter signaling Web Speech API integration in browser runtime."""

    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "hi") -> str:
        logger.info(f"[Integration STT] WebSpeechSTTAdapter delegating to client runtime (Lang: {language})")
        return ""


def get_stt_adapter(provider: str = "auto") -> STTAdapter:
    prov_clean = (provider or "auto").lower().strip()
    if prov_clean == "mock":
        return MockSTTAdapter()
    return WebSpeechSTTAdapter()
