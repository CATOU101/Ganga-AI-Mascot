"""Configuration management for Ganga AI Mascot Integration layer."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationConfig:
    brain_base_url: str = os.getenv("BRAIN_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    brain_timeout_seconds: float = float(os.getenv("BRAIN_TIMEOUT_SECONDS", "30.0"))
    mock_mode: bool = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "hi")
    stt_provider: str = os.getenv("STT_PROVIDER", "auto")
    tts_provider: str = os.getenv("TTS_PROVIDER", "auto")
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "8080"))


def load_integration_config() -> IntegrationConfig:
    return IntegrationConfig()
