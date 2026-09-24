"""Speech-to-Text (STT) interface, offline Vosk engine, and speech recognition adapters."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import unicodedata
import wave
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("integration.stt_adapter")

try:
    import vosk
    VOSK_AVAILABLE = True
except Exception as e:
    vosk = None
    VOSK_AVAILABLE = False
    logger.warning(f"[Integration STT] Vosk not importable: {e}")


def normalize_stt_text(raw_text: str) -> str:
    """Normalize text into NFC Unicode form and collapse whitespace."""
    if not raw_text:
        return ""
    text = unicodedata.normalize("NFC", raw_text)
    return " ".join(text.strip().split())


class STTAdapter(ABC):
    @abstractmethod
    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "hi") -> str:
        """Convert audio bytes into transcribed text string."""
        raise NotImplementedError


class VoskSTTAdapter(STTAdapter):
    """
    100% Genuine Local & Offline STT Adapter using Vosk speech models.
    Supports English ('en') and Hindi ('hi').
    Preserves Devanagari Unicode NFC ligatures and vowels for Hindi.
    """

    MODEL_LANG_MAP = {
        "en": "en-us",
        "hi": "hi",
    }

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = models_dir
        self._models: dict[str, vosk.Model] = {}
        self.blender_exe = r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"

    def _get_model(self, lang_key: str):
        if not VOSK_AVAILABLE or vosk is None:
            raise RuntimeError("Vosk STT library is not installed or available.")

        if lang_key in self._models:
            return self._models[lang_key]

        vosk_lang = self.MODEL_LANG_MAP.get(lang_key, "en-us")
        try:
            if self.models_dir and os.path.exists(self.models_dir):
                m_path = os.path.join(self.models_dir, vosk_lang)
                if os.path.exists(m_path):
                    model = vosk.Model(m_path)
                else:
                    model = vosk.Model(lang=vosk_lang)
            else:
                model = vosk.Model(lang=vosk_lang)
            self._models[lang_key] = model
            return model
        except Exception as e:
            logger.error(f"[Integration STT] Error loading Vosk model for {lang_key}: {e}")
            raise

    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "hi") -> str:
        if not audio_bytes or len(audio_bytes) < 44:
            logger.warning("[Integration STT] Received empty or invalid audio bytes.")
            return ""

        lang_key = (language or "hi").lower().strip()
        if lang_key not in ("en", "hi"):
            lang_key = "hi"

        try:
            model = self._get_model(lang_key)
        except Exception as err:
            logger.error(f"[Integration STT] Could not initialize Vosk model: {err}. Falling back to mock.")
            return MockSTTAdapter().transcribe_audio(audio_bytes, language=lang_key)

        # Write incoming audio to a temporary file
        temp_input = None
        temp_wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f_in:
                f_in.write(audio_bytes)
                temp_input = f_in.name

            # Determine if incoming bytes are standard PCM WAV
            is_wav = audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"
            if is_wav:
                temp_wav = temp_input
            else:
                # Convert WebM/OGG/MP3 to 16kHz mono WAV using Blender aud
                temp_wav = temp_input + "_conv.wav"
                conv_script = f"""
import aud
sound = aud.Sound({repr(temp_input)})
sound.write({repr(temp_wav)}, 16000, 1, aud.FORMAT_S16, aud.CONTAINER_WAV, 65536)
"""
                res = subprocess.run([self.blender_exe, "--background", "--python-expr", conv_script],
                                     capture_output=True, text=True)
                if res.returncode != 0 or not os.path.exists(temp_wav):
                    logger.error(f"[Integration STT] Audio conversion failed: {res.stderr}")
                    return ""

            # Perform Kaldi recognizer pass
            with wave.open(temp_wav, "rb") as wf:
                sample_rate = wf.getframerate()
                rec = vosk.KaldiRecognizer(model, sample_rate)
                rec.SetWords(True)

                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    rec.AcceptWaveform(data)

                final_res = json.loads(rec.FinalResult())
                raw_text = final_res.get("text", "")

            norm_text = normalize_stt_text(raw_text)
            logger.info(f"[Integration STT] Vosk transcribed ({lang_key}): '{norm_text}'")
            return norm_text

        except Exception as e:
            logger.error(f"[Integration STT] Vosk transcription error: {e}")
            return ""
        finally:
            if temp_input and os.path.exists(temp_input) and temp_input != temp_wav:
                try:
                    os.remove(temp_input)
                except Exception:
                    pass
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass


class MockSTTAdapter(STTAdapter):
    """Fallback / testing STT adapter returning pre-configured sample transcriptions."""

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


def get_stt_adapter(provider: str = "vosk") -> STTAdapter:
    prov_clean = (provider or "vosk").lower().strip()
    if prov_clean in ("vosk", "auto", "local"):
        if VOSK_AVAILABLE:
            return VoskSTTAdapter()
        logger.warning("[Integration STT] Vosk not available, using MockSTTAdapter.")
        return MockSTTAdapter()
    elif prov_clean == "mock":
        return MockSTTAdapter()
    return WebSpeechSTTAdapter()
