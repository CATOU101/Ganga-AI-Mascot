"""Mocked adapter contract tests for all configured speech locales.

No live speech service is contacted. These tests verify locale routing and safe
failure behavior; they do not claim speech accuracy for real recordings.
"""

import io
import sys
import types
import wave

import pytest

from brain.translator import SPEECH_LOCALES, SUPPORTED_LANGUAGES
from integration.voice.stt_adapter import AzureSpeechSTTAdapter, get_stt_adapter
from integration.voice.tts_adapter import AzureSpeechTTSProvider, SyntheticWavTTSAdapter


def _silent_wav():
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\0\0" * 160)
    return output.getvalue()


@pytest.mark.parametrize("language", sorted(SUPPORTED_LANGUAGES))
def test_azure_stt_routes_each_supported_language_to_configured_locale(monkeypatch, language):
    state = {}

    class SpeechConfig:
        def __init__(self, subscription, region):
            state["credentials"] = (subscription, region)

    class AudioConfig:
        def __init__(self, filename):
            state["filename"] = filename

    class Recognizer:
        def __init__(self, speech_config, audio_config):
            state["locale"] = speech_config.speech_recognition_language

        def recognize_once_async(self):
            return types.SimpleNamespace(get=lambda: types.SimpleNamespace(
                reason="recognized", text="  नमूना   transcript  "))

    speechsdk = types.ModuleType("azure.cognitiveservices.speech")
    speechsdk.SpeechConfig = SpeechConfig
    speechsdk.SpeechRecognizer = Recognizer
    speechsdk.ResultReason = types.SimpleNamespace(RecognizedSpeech="recognized", NoMatch="nomatch")
    speechsdk.audio = types.SimpleNamespace(AudioConfig=AudioConfig)
    azure = types.ModuleType("azure")
    azure.__path__ = []
    cognitiveservices = types.ModuleType("azure.cognitiveservices")
    cognitiveservices.__path__ = []
    azure.cognitiveservices = cognitiveservices
    cognitiveservices.speech = speechsdk
    monkeypatch.setitem(sys.modules, "azure", azure)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices", cognitiveservices)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices.speech", speechsdk)
    monkeypatch.setattr("integration.voice.stt_adapter.shutil.which", lambda _name: None)

    transcript = AzureSpeechSTTAdapter("test-key", "test-region").transcribe_audio(
        _silent_wav(), language=language
    )
    assert state["locale"] == SPEECH_LOCALES[language]
    assert state["credentials"] == ("test-key", "test-region")
    assert transcript == "नमूना transcript"


def test_stt_auto_prefers_azure_only_when_both_credentials_exist(monkeypatch):
    monkeypatch.setenv("AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "test-region")
    assert isinstance(get_stt_adapter("auto"), AzureSpeechSTTAdapter)
    monkeypatch.delenv("AZURE_SPEECH_KEY")
    monkeypatch.delenv("AZURE_SPEECH_REGION")
    assert get_stt_adapter("auto").__class__.__name__ in {
        "VoskSTTAdapter", "UnavailableSTTAdapter"
    }


@pytest.mark.parametrize("language", sorted(SUPPORTED_LANGUAGES))
def test_tts_voice_configuration_and_audio_pipeline_cover_all_codes(language):
    assert set(AzureSpeechTTSProvider.VOICES) == SUPPORTED_LANGUAGES
    result = SyntheticWavTTSAdapter().synthesize_speech("test", language)
    assert result is not None
    assert result.audio_base64.startswith("UklGR")


@pytest.mark.parametrize("language", sorted(SUPPORTED_LANGUAGES))
def test_azure_tts_uses_language_specific_voice_and_writes_audio(monkeypatch, tmp_path, language):
    state = {}

    class SpeechConfig:
        def __init__(self, subscription, region):
            pass

        def set_speech_synthesis_output_format(self, output_format):
            state["format"] = output_format

    class AudioOutputConfig:
        def __init__(self, filename):
            state["filename"] = filename

    class Synthesizer:
        def __init__(self, speech_config, audio_config):
            state["voice"] = speech_config.speech_synthesis_voice_name

        def speak_text_async(self, text):
            with wave.open(state["filename"], "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(b"\0\0" * 100)
            return types.SimpleNamespace(get=lambda: types.SimpleNamespace(reason="completed"))

    speechsdk = types.ModuleType("azure.cognitiveservices.speech")
    speechsdk.SpeechConfig = SpeechConfig
    speechsdk.SpeechSynthesizer = Synthesizer
    speechsdk.SpeechSynthesisOutputFormat = types.SimpleNamespace(Riff16Khz16BitMonoPcm="riff")
    speechsdk.ResultReason = types.SimpleNamespace(SynthesizingAudioCompleted="completed")
    speechsdk.audio = types.SimpleNamespace(AudioOutputConfig=AudioOutputConfig)
    azure = types.ModuleType("azure")
    azure.__path__ = []
    cognitiveservices = types.ModuleType("azure.cognitiveservices")
    cognitiveservices.__path__ = []
    azure.cognitiveservices = cognitiveservices
    cognitiveservices.speech = speechsdk
    monkeypatch.setitem(sys.modules, "azure", azure)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices", cognitiveservices)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices.speech", speechsdk)

    metadata = AzureSpeechTTSProvider("test-key", "test-region").synthesize_to_wav(
        "sample", language, str(tmp_path / f"{language}.wav")
    )
    assert state["voice"] == AzureSpeechTTSProvider.VOICES[language]
    assert state["format"] == "riff"
    assert metadata["provider"] == "AzureSpeech"
