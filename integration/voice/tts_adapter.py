"""Text-to-Speech (TTS) interface, audio generator, and speech synthesis adapters for Member 2 Chacha."""

from __future__ import annotations

import base64
import logging
import math
import os
import struct
import tempfile
import wave
from abc import ABC, abstractmethod
from typing import NamedTuple

from avatar.Member2_Chacha.chacha_tts_pipeline import EdgeTTSProvider, LocalSapiTTSProvider

logger = logging.getLogger("integration.tts_adapter")


class TTSAudioResult(NamedTuple):
    audio_base64: str
    sample_rate: int
    duration_seconds: float
    pcm_samples: list[float]
    audio_path: str = ""


class TTSAdapter(ABC):
    @abstractmethod
    def synthesize_speech(self, text: str, language: str = "hi") -> TTSAudioResult | None:
        """Synthesize text into speech audio result with PCM samples for lip-sync."""
        raise NotImplementedError


class Member2TTSAdapter(TTSAdapter):
    """
    Production TTS Adapter for Chacha Chaudhary (Member 2).
    - Primary: EdgeTTSProvider (Neural Indian English Prabhat & Hindi Madhur).
    - Fallback: LocalSapiTTSProvider (100% offline Windows SAPI fallback).
    - Uncompressed 16-bit 16kHz Mono PCM WAV output.
    """

    def __init__(self, force_sapi: bool = False):
        self.force_sapi = force_sapi
        self.edge_provider = EdgeTTSProvider()
        self.sapi_provider = LocalSapiTTSProvider()

    def synthesize_speech(self, text: str, language: str = "hi") -> TTSAudioResult | None:
        if not text or not text.strip():
            logger.warning("[Integration TTS] Empty text passed to Member2TTSAdapter.")
            return None

        clean_text = text.strip()
        lang_key = (language or "hi").lower().strip()
        if lang_key not in ("en", "hi"):
            lang_key = "hi"

        temp_wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f_wav:
                temp_wav = f_wav.name

            meta = None
            if not self.force_sapi:
                try:
                    logger.info(f"[Integration TTS] Synthesizing via EdgeTTS neural voice ({lang_key})")
                    meta = self.edge_provider.synthesize_to_wav(
                        text=clean_text, language=lang_key, output_wav=temp_wav
                    )
                except Exception as edge_err:
                    logger.warning(f"[Integration TTS] EdgeTTS failed: {edge_err}. Attempting SAPI fallback.")

            if meta is None:
                logger.info(f"[Integration TTS] Synthesizing via Local SAPI offline fallback ({lang_key})")
                meta = self.sapi_provider.synthesize_to_wav(
                    text=clean_text, language=lang_key, output_wav=temp_wav
                )

            # Read audio bytes and convert to Base64
            with open(temp_wav, "rb") as f:
                wav_bytes = f.read()
            audio_b64 = base64.b64encode(wav_bytes).decode("ascii")

            # Read PCM frames
            pcm_samples: list[float] = []
            sample_rate = 16000
            duration = 1.0
            with wave.open(temp_wav, "rb") as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                sample_width = wf.getsampwidth()
                duration = round(n_frames / float(sample_rate), 4)

                raw_frames = wf.readframes(n_frames)
                if sample_width == 2:
                    count = len(raw_frames) // 2
                    shorts = struct.unpack(f"<{count}h", raw_frames)
                    pcm_samples = [s / 32768.0 for s in shorts]
                elif sample_width == 1:
                    bytes_arr = struct.unpack(f"<{len(raw_frames)}B", raw_frames)
                    pcm_samples = [(b - 128) / 128.0 for b in bytes_arr]

            return TTSAudioResult(
                audio_base64=audio_b64,
                sample_rate=sample_rate,
                duration_seconds=duration,
                pcm_samples=pcm_samples,
                audio_path=temp_wav,
            )

        except Exception as err:
            logger.error(f"[Integration TTS] Member2TTSAdapter failed completely: {err}. Falling back to synthetic.")
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass
            return SyntheticWavTTSAdapter().synthesize_speech(clean_text, language=lang_key)


class SyntheticWavTTSAdapter(TTSAdapter):
    """Generates pure WAV audio tone frames for testing lip-sync and audio playback without cloud TTS keys."""

    def synthesize_speech(self, text: str, language: str = "hi") -> TTSAudioResult | None:
        if not text or not text.strip():
            logger.warning("[Integration TTS] Empty text passed to TTS adapter.")
            return None

        logger.info(f"[Integration TTS] Synthesizing speech with SyntheticWavTTSAdapter: '{text[:30]}...' (Lang: {language})")
        
        sample_rate = 16000
        words = text.split()
        num_words = max(1, len(words))
        duration = min(15.0, max(1.5, num_words * 0.35))
        num_samples = int(sample_rate * duration)

        pcm_samples: list[float] = []
        raw_pcm = bytearray()

        for i in range(num_samples):
            t = i / sample_rate
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
    if prov_clean in ("edge", "member2", "auto", "default"):
        return Member2TTSAdapter()
    elif prov_clean == "sapi":
        return Member2TTSAdapter(force_sapi=True)
    elif prov_clean in ("synthetic", "wav"):
        return SyntheticWavTTSAdapter()
    return WebSpeechTTSAdapter()
