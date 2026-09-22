"""Text-to-Speech (TTS) interface, audio generator, and speech synthesis adapters."""

from __future__ import annotations

import base64
import logging
import math
import struct
from abc import ABC, abstractmethod
from typing import NamedTuple

logger = logging.getLogger("integration.tts_adapter")


class TTSAudioResult(NamedTuple):
    audio_base64: str
    sample_rate: int
    duration_seconds: float
    pcm_samples: list[float]


class TTSAdapter(ABC):
    @abstractmethod
    def synthesize_speech(self, text: str, language: str = "hi") -> TTSAudioResult | None:
        """Synthesize text into speech audio result with PCM samples for lip-sync."""
        raise NotImplementedError


class SyntheticWavTTSAdapter(TTSAdapter):
    """Generates pure WAV audio tone frames for testing lip-sync and audio playback without cloud TTS keys."""

    def synthesize_speech(self, text: str, language: str = "hi") -> TTSAudioResult | None:
        if not text or not text.strip():
            logger.warning("[Integration TTS] Empty text passed to TTS adapter.")
            return None

        logger.info(f"[Integration TTS] Synthesizing speech for text: '{text[:30]}...' (Lang: {language})")
        
        sample_rate = 16000
        words = text.split()
        num_words = max(1, len(words))
        duration = min(15.0, max(1.5, num_words * 0.35))
        num_samples = int(sample_rate * duration)

        pcm_samples: list[float] = []
        raw_pcm = bytearray()

        for i in range(num_samples):
            t = i / sample_rate
            # Modulate amplitude according to simulated syllables/words
            modulation = 0.5 * (1.0 + math.sin(2 * math.pi * 3.5 * t)) * (0.8 + 0.2 * math.sin(2 * math.pi * 0.5 * t))
            freq = 220.0 + 40.0 * math.sin(2 * math.pi * 1.5 * t)
            sample_val = modulation * math.sin(2 * math.pi * freq * t)
            pcm_samples.append(sample_val)

            int_val = int(sample_val * 32767.0)
            int_val = max(-32768, min(32767, int_val))
            raw_pcm.extend(struct.pack("<h", int_val))

        wav_bytes = self._create_wav_header(sample_rate, 1, 16, len(raw_pcm)) + raw_pcm
        audio_b64 = base64.b64encode(wav_bytes).decode("ascii")

        return TTSAudioResult(
            audio_base64=audio_b64,
            sample_rate=sample_rate,
            duration_seconds=duration,
            pcm_samples=pcm_samples
        )

    def _create_wav_header(self, sample_rate: int, num_channels: int, bits_per_sample: int, data_size: int) -> bytes:
        header = bytearray()
        header.extend(b"RIFF")
        header.extend(struct.pack("<I", 36 + data_size))
        header.extend(b"WAVEfmt ")
        header.extend(struct.pack("<I", 16))
        header.extend(struct.pack("<H", 1))  # PCM
        header.extend(struct.pack("<H", num_channels))
        header.extend(struct.pack("<I", sample_rate))
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        header.extend(struct.pack("<I", byte_rate))
        block_align = num_channels * bits_per_sample // 8
        header.extend(struct.pack("<H", block_align))
        header.extend(struct.pack("<H", bits_per_sample))
        header.extend(b"data")
        header.extend(struct.pack("<I", data_size))
        return bytes(header)


class WebSpeechTTSAdapter(TTSAdapter):
    """Client-side WebSpeech API proxy that returns null audio bytes while triggering browser synthesis."""

    def synthesize_speech(self, text: str, language: str = "hi") -> TTSAudioResult | None:
        logger.info(f"[Integration TTS] WebSpeechTTSAdapter delegating text to browser SpeechSynthesis (Lang: {language})")
        return None


def get_tts_adapter(provider: str = "auto") -> TTSAdapter:
    prov_clean = (provider or "auto").lower().strip()
    if prov_clean in ("synthetic", "wav"):
        return SyntheticWavTTSAdapter()
    return WebSpeechTTSAdapter()
