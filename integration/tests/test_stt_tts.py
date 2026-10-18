"""Unit tests for STT, TTS, and Lip-Sync modules."""

import pytest
from integration.avatar.lipsync import LipSyncAnalyzer
from integration.voice.stt_adapter import MockSTTAdapter
from integration.voice.tts_adapter import SyntheticWavTTSAdapter


def test_mock_stt_adapter():
    adapter = MockSTTAdapter()
    
    hi_text = adapter.transcribe_audio(b"fake_audio_bytes", language="hi")
    assert hi_text == "अविरल धारा क्या है?"

    en_text = adapter.transcribe_audio(b"fake_audio_bytes", language="en")
    assert en_text == "What is Aviral Dhara?"

    empty_text = adapter.transcribe_audio(b"", language="en")
    assert empty_text == ""


def test_synthetic_tts_and_lipsync():
    tts = SyntheticWavTTSAdapter()
    result = tts.synthesize_speech("What is Aviral Dhara?", language="en")

    assert result is not None
    assert result.audio_base64 != ""
    assert result.duration_seconds > 0.0
    assert len(result.pcm_samples) > 0

    analyzer = LipSyncAnalyzer(frame_size=512)
    rms_frames = analyzer.compute_rms_frames(result.pcm_samples)

    assert len(rms_frames) > 0
    # Values should be normalized between 0.0 and 1.0
    assert all(0.0 <= val <= 1.0 for val in rms_frames)


def test_member2_tts_all_four_languages_voice_selection():
    from avatar.Member2_Chacha.chacha_tts_pipeline import EdgeTTSProvider
    provider = EdgeTTSProvider()
    assert provider.DEFAULT_VOICES["en"] == "en-IN-PrabhatNeural"
    assert provider.DEFAULT_VOICES["hi"] == "hi-IN-MadhurNeural"
    assert provider.DEFAULT_VOICES["kn"] == "kn-IN-GaganNeural"
    assert provider.DEFAULT_VOICES["ta"] == "ta-IN-ValluvarNeural"


def test_member2_tts_unsupported_language_refuses_silent_english_fallback():
    from avatar.Member2_Chacha.chacha_tts_pipeline import EdgeTTSProvider
    from integration.voice.tts_adapter import Member2TTSAdapter

    provider = EdgeTTSProvider()
    with pytest.raises(ValueError) as exc:
        provider.synthesize_to_wav("Bonjour", language="fr", output_wav="test.wav")
    assert "Unsupported language code" in str(exc.value)

    adapter = Member2TTSAdapter()
    res = adapter.synthesize_speech("Bonjour", language="fr")
    # Must refuse silent fallback and return None for client/browser fallback
    assert res is None


def test_live_or_mocked_tts_audio_synthesis_all_four_languages():
    from integration.voice.tts_adapter import Member2TTSAdapter
    adapter = Member2TTSAdapter()

    # Test synthesizing all 4 languages produces valid PCM samples and Base64 WAV
    test_phrases = {
        "en": "Namaste, I am Chacha Chaudhary.",
        "hi": "नमस्ते, मैं चाचा चौधरी हूँ।",
        "kn": "ನಮಸ್ಕಾರ, ನಾನು ಚಾಚಾ ಚೌಧರಿ.",
        "ta": "வணக்கம், நான் சாச்சா சவுத்ரி.",
    }

    for lang, text in test_phrases.items():
        res = adapter.synthesize_speech(text, language=lang)
        assert res is not None, f"TTS synthesis failed for {lang}"
        assert res.duration_seconds > 0.0
        assert len(res.pcm_samples) > 0
        assert len(res.audio_base64) > 0
        assert res.sample_rate == 16000
