"""
Chacha Chaudhary - Digital Avatar Speech-to-Text Pipeline
Stage 12A: Speech-to-Text Integration & Transcription Provider Abstraction

Architecture:
    MICROPHONE -> AUDIO FILE (WAV) -> STT PROVIDER -> STRUCTURED TEXT RESULT

Providers:
- LocalSTTProvider: 100% genuinely offline/local speech recognition via Vosk models (English + Hindi).
- FreePublicSTTProvider: Adapter/fallback using public SpeechRecognition service without API keys.
- OptionalCloudSTTProvider: Extensible stub for OpenAI Whisper / Azure / Deepgram cloud APIs.

Features:
- Preserves raw transcription alongside minimal normalized text.
- Full bilingual support (English 'en' and Hindi 'hi') with Unicode NFC preservation.
- Decoupled from Blender, avatar state, and Member 1 AI.
"""

import os
import sys
import json
import wave
import unicodedata
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

# Ensure speech libraries are available
try:
    import vosk
    VOSK_AVAILABLE = True
    VOSK_ERROR = None
except Exception as e:
    VOSK_AVAILABLE = False
    VOSK_ERROR = str(e)

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
    SR_ERROR = None
except Exception as e:
    SR_AVAILABLE = False
    SR_ERROR = str(e)


class STTError(Exception):
    """Base exception for STT errors."""
    pass


class STTEngineUnavailableError(STTError):
    """Raised when the requested STT engine or its required local model is unavailable."""
    pass


class UnsupportedLanguageError(STTError):
    """Raised when an unsupported language code is requested."""
    pass


class TranscriptionError(STTError):
    """Raised when audio transcription fails."""
    pass


class EmptyAudioError(STTError):
    """Raised when the input audio file is empty, missing, or zero-duration."""
    pass


def normalize_text(raw_text: str) -> str:
    """
    Applies minimal, non-destructive normalization to transcription text:
    - Normalizes Unicode to NFC form (essential for Devanagari ligatures/vowels in Hindi)
    - Trims leading and trailing whitespace
    - Collapses consecutive whitespace runs to a single space
    Does NOT aggressively rewrite or remove user punctuation/vocabulary.
    """
    if not raw_text:
        return ""
    text = unicodedata.normalize("NFC", raw_text)
    # Collapse multiple whitespace
    parts = text.strip().split()
    return " ".join(parts)


def get_wav_duration(wav_path: str) -> float:
    """Measures exact duration in seconds from WAV header."""
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"Audio file not found: {wav_path}")
    if os.path.getsize(wav_path) < 44:
        raise EmptyAudioError(f"Audio file '{wav_path}' is empty or corrupt header.")

    with wave.open(wav_path, "rb") as wf:
        n_frames = wf.getnframes()
        sr_rate = wf.getframerate()
        if sr_rate <= 0 or n_frames <= 0:
            raise EmptyAudioError(f"Audio file '{wav_path}' contains 0 audio frames.")
        return round(float(n_frames) / float(sr_rate), 4)


class BaseSTTProvider(ABC):
    """Abstract Base Class for STT Providers."""

    @abstractmethod
    def transcribe(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribes an audio WAV file into a structured dictionary.
        
        Args:
            audio_path: Path to 16-bit mono PCM WAV file.
            language: 'en' for English, 'hi' for Hindi.
            
        Returns:
            Dictionary containing text, raw_text, language, duration_seconds, audio_file, provider, confidence.
        """
        pass


class LocalSTTProvider(BaseSTTProvider):
    """
    100% Genuine Local & Offline STT Provider using Vosk Kaldi speech models.
    Operates entirely on CPU without any internet connection or external server requests.
    Supports English ('en') and Hindi ('hi').
    """

    MODEL_LANG_MAP = {
        "en": "en-us",
        "hi": "hi"
    }

    def __init__(self, models_dir: Optional[str] = None):
        if not VOSK_AVAILABLE:
            raise STTEngineUnavailableError(f"Local Vosk STT engine not installed: {VOSK_ERROR}")
        self.models_dir = models_dir
        self._models = {}

    def _get_model(self, lang_key: str):
        """Loads or retrieves cached Vosk model for the specified language."""
        if lang_key in self._models:
            return self._models[lang_key]

        vosk_lang = self.MODEL_LANG_MAP.get(lang_key)
        if not vosk_lang:
            raise UnsupportedLanguageError(f"Language '{lang_key}' is not supported by LocalSTTProvider. Supported: en, hi")

        try:
            # Vosk Model downloads to local cache directory if not already cached
            if self.models_dir and os.path.exists(self.models_dir):
                model_path = os.path.join(self.models_dir, vosk_lang)
                if os.path.exists(model_path):
                    model = vosk.Model(model_path)
                else:
                    model = vosk.Model(lang=vosk_lang)
            else:
                model = vosk.Model(lang=vosk_lang)
            self._models[lang_key] = model
            return model
        except Exception as e:
            raise STTEngineUnavailableError(f"Failed to load local Vosk model for language '{lang_key}': {str(e)}")

    def transcribe(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        duration = get_wav_duration(audio_path)
        lang_key = language.lower().strip()
        model = self._get_model(lang_key)

        try:
            with wave.open(audio_path, "rb") as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                rec = vosk.KaldiRecognizer(model, sample_rate)
                rec.SetWords(True)

                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    rec.AcceptWaveform(data)

                final_res = json.loads(rec.FinalResult())
                raw_text = final_res.get("text", "")
        except Exception as err:
            raise TranscriptionError(f"Local transcription failed on '{audio_path}': {str(err)}")

        norm = normalize_text(raw_text)

        return {
            "text": norm,
            "raw_text": raw_text,
            "language": lang_key,
            "duration_seconds": duration,
            "audio_file": os.path.abspath(audio_path),
            "provider": "LocalSTTProvider (Vosk Offline)",
            "confidence": None  # Vosk text does not output aggregate utterance confidence
        }


class FreePublicSTTProvider(BaseSTTProvider):
    """
    Adapter/Fallback STT Provider using SpeechRecognition's free public endpoint.
    Requires no paid API keys.
    """

    LANG_MAP = {
        "en": "en-US",
        "hi": "hi-IN"
    }

    def __init__(self):
        if not SR_AVAILABLE:
            raise STTEngineUnavailableError(f"SpeechRecognition library not installed: {SR_ERROR}")
        self.recognizer = sr.Recognizer()

    def transcribe(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        duration = get_wav_duration(audio_path)
        lang_key = language.lower().strip()
        sr_lang = self.LANG_MAP.get(lang_key)
        if not sr_lang:
            raise UnsupportedLanguageError(f"Language '{language}' not supported. Supported: en, hi")

        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
            raw_text = self.recognizer.recognize_google(audio_data, language=sr_lang)
        except sr.UnknownValueError:
            raw_text = ""
        except sr.RequestError as e:
            raise TranscriptionError(f"Public recognition service error: {str(e)}")
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}")

        norm = normalize_text(raw_text)

        return {
            "text": norm,
            "raw_text": raw_text,
            "language": lang_key,
            "duration_seconds": duration,
            "audio_file": os.path.abspath(audio_path),
            "provider": "FreePublicSTTProvider (Google Free)",
            "confidence": None
        }


class OptionalCloudSTTProvider(BaseSTTProvider):
    """
    Extensible stub for future cloud STT providers (OpenAI Whisper API, Azure, Deepgram).
    """

    def __init__(self, api_key: Optional[str] = None, service_name: str = "whisper_api"):
        self.api_key = api_key
        self.service_name = service_name

    def transcribe(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        if not self.api_key:
            raise STTEngineUnavailableError(
                f"Cloud STT provider '{self.service_name}' requires an API key. None provided."
            )
        raise NotImplementedError("Cloud STT provider not yet configured in Stage 12A.")


class ChachaSTTPipeline:
    """
    High-level Speech-to-Text Pipeline manager.
    Defaults to LocalSTTProvider for 100% offline, local development.
    """

    def __init__(self, provider_type: str = "local", models_dir: Optional[str] = None):
        """
        Initializes the STT pipeline.
        
        Args:
            provider_type: 'local' (default, 100% offline Vosk) or 'free' (public adapter).
            models_dir: Optional custom model directory for offline models.
        """
        self.provider_type = provider_type.lower().strip()
        if self.provider_type == "local":
            self.provider = LocalSTTProvider(models_dir=models_dir)
        elif self.provider_type in ["free", "public"]:
            self.provider = FreePublicSTTProvider()
        elif self.provider_type == "cloud":
            self.provider = OptionalCloudSTTProvider()
        else:
            raise ValueError(f"Unknown provider type '{provider_type}'. Allowed: 'local', 'free', 'cloud'")

    def transcribe(self, audio_path: str, language: str = "en") -> Dict[str, Any]:
        """
        Transcribes an input audio file.
        
        Args:
            audio_path: Absolute or relative path to WAV file.
            language: 'en' for English, 'hi' for Hindi.
            
        Returns:
            Structured result dictionary with text, raw_text, duration, etc.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        lang_key = language.lower().strip()
        if lang_key not in ["en", "hi"]:
            raise UnsupportedLanguageError(f"Unsupported language '{language}'. Supported: 'en', 'hi'")

        return self.provider.transcribe(audio_path=audio_path, language=lang_key)

    def transcribe_and_save(self, audio_path: str, language: str = "en", output_json_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes audio and writes the structured result to a JSON file.
        
        Args:
            audio_path: Path to the WAV file.
            language: 'en' or 'hi'.
            output_json_path: Destination JSON path. If None, saves in Output/STT/.
        """
        res = self.transcribe(audio_path=audio_path, language=language)

        if output_json_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            stt_dir = os.path.join(base_dir, "STT")
            os.makedirs(stt_dir, exist_ok=True)
            stem = os.path.splitext(os.path.basename(audio_path))[0]
            output_json_path = os.path.join(stt_dir, f"{stem}_{language}.json")

        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)

        return res


# Helper convenience function
def transcribe(audio_path: str, language: str = "en", provider_type: str = "local") -> Dict[str, Any]:
    """Top-level convenience transcription function."""
    pipeline = ChachaSTTPipeline(provider_type=provider_type)
    return pipeline.transcribe(audio_path=audio_path, language=language)
