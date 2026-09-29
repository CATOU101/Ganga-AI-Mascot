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
