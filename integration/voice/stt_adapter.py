"""Speech-to-Text (STT) interface, offline Vosk engine, and speech recognition adapters."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import wave
from abc import ABC, abstractmethod
from typing import Optional

from brain.translator import SPEECH_LOCALES, SUPPORTED_LANGUAGES

logger = logging.getLogger("integration.stt_adapter")

try:
    import vosk
    VOSK_AVAILABLE = True
except Exception as e:
    vosk = None
    VOSK_AVAILABLE = False
    logger.warning("[Integration STT] Vosk not importable (%s).", type(e).__name__)


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
    SUPPORTED_LANGUAGES = frozenset(MODEL_LANG_MAP)

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
            logger.error("[Integration STT] Error loading Vosk model for %s (%s).", lang_key, type(e).__name__)
            raise

    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "hi") -> str:
        if not audio_bytes or len(audio_bytes) < 44:
            logger.warning("[Integration STT] Received empty or invalid audio bytes.")
            return ""

        lang_key = (language or "hi").lower().strip()
        if lang_key not in self.SUPPORTED_LANGUAGES:
            logger.warning("[Integration STT] Vosk has no configured model for language %s.", lang_key)
            return ""

        try:
            model = self._get_model(lang_key)
        except Exception as err:
            logger.error("[Integration STT] Could not initialize Vosk model (%s).", type(err).__name__)
            raise RuntimeError("Configured Vosk model is unavailable") from None

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
                    logger.error("[Integration STT] Audio conversion failed (return_code=%s).", res.returncode)
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
            logger.info("[Integration STT] Vosk transcription completed for %s.", lang_key)
            return norm_text

        except Exception as e:
            logger.error("[Integration STT] Vosk transcription failed (%s).", type(e).__name__)
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


class AzureSpeechSTTAdapter(STTAdapter):
    """Azure Speech STT for configured Indian locales; requires key and region."""

    SUPPORTED_LANGUAGES = SUPPORTED_LANGUAGES

    def __init__(self, api_key: str | None = None, region: str | None = None):
        self.api_key = api_key or os.getenv("AZURE_SPEECH_KEY", "").strip()
        self.region = region or os.getenv("AZURE_SPEECH_REGION", "").strip()

    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "en") -> str:
        lang = (language or "en").lower().strip()
        if lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError("Unsupported Azure Speech language")
        if not self.api_key or not self.region:
            raise RuntimeError("Azure Speech requires AZURE_SPEECH_KEY and AZURE_SPEECH_REGION")
        if not audio_bytes or len(audio_bytes) < 44:
            return ""
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as exc:
            raise RuntimeError("Install azure-cognitiveservices-speech to enable Azure Speech STT") from exc

        source_path = None
        wav_path = None
        try:
            suffix = ".wav" if audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE" else ".audio"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as source:
                source.write(audio_bytes)
                source_path = source.name
            wav_path = source_path if suffix == ".wav" else source_path + ".wav"
            if shutil.which("ffmpeg"):
                converted_path = source_path + ".pcm.wav"
                result = subprocess.run(
                    ["ffmpeg", "-nostdin", "-y", "-i", source_path, "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", converted_path],
                    capture_output=True, timeout=30,
                )
                if result.returncode != 0 or not os.path.exists(converted_path):
                    raise RuntimeError("Audio conversion failed")
                wav_path = converted_path
            else:
                with wave.open(source_path, "rb") as audio_file:
                    if audio_file.getframerate() != 16000 or audio_file.getnchannels() != 1 or audio_file.getsampwidth() != 2:
                        raise RuntimeError("Install ffmpeg to convert microphone audio to Azure's 16 kHz mono PCM format")

            speech_config = speechsdk.SpeechConfig(subscription=self.api_key, region=self.region)
            speech_config.speech_recognition_language = SPEECH_LOCALES[lang]
            audio_config = speechsdk.audio.AudioConfig(filename=wav_path)
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            result = recognizer.recognize_once_async().get()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return normalize_stt_text(result.text)
            if result.reason == speechsdk.ResultReason.NoMatch:
                return ""
            raise RuntimeError("Azure Speech recognition did not complete")
        except (TimeoutError, OSError):
            logger.warning("Azure Speech STT failed: timeout_or_io")
            raise RuntimeError("Speech recognition is temporarily unavailable") from None
        finally:
            for path in {source_path, wav_path, source_path + ".pcm.wav" if source_path else None}:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass


class UnavailableSTTAdapter(STTAdapter):
    """Explicitly unavailable STT; avoids returning made-up mock transcripts."""

    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "en") -> str:
        raise RuntimeError("No speech recognition provider is configured")


class WebSpeechSTTAdapter(STTAdapter):
    """Adapter signaling Web Speech API integration in browser runtime."""

    def transcribe_audio(self, audio_bytes: bytes | None, language: str = "hi") -> str:
        logger.info(f"[Integration STT] WebSpeechSTTAdapter delegating to client runtime (Lang: {language})")
        return ""


def get_stt_adapter(provider: str = "vosk") -> STTAdapter:
    prov_clean = (provider or "vosk").lower().strip()
    if prov_clean == "auto":
        if os.getenv("AZURE_SPEECH_KEY", "").strip() and os.getenv("AZURE_SPEECH_REGION", "").strip():
            return AzureSpeechSTTAdapter()
        if VOSK_AVAILABLE:
            return VoskSTTAdapter()
        logger.warning("[Integration STT] No configured speech provider is available.")
        return UnavailableSTTAdapter()
    if prov_clean in ("azure", "azure-speech"):
        return AzureSpeechSTTAdapter()
    if prov_clean == "mock":
        return MockSTTAdapter()
    if prov_clean in ("vosk", "local"):
        if VOSK_AVAILABLE:
            return VoskSTTAdapter()
        logger.warning("[Integration STT] Vosk unavailable; no transcription fallback is configured.")
        return UnavailableSTTAdapter()
    return WebSpeechSTTAdapter()
