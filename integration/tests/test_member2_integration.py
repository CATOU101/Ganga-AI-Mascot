"""Comprehensive Integration Test Suite for Member 2 Digital Avatar + Voice System."""

from __future__ import annotations

import io
import os
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from integration.avatar.emotion_mapper import map_emotion
from integration.avatar.gesture_mapper import map_gesture
from integration.avatar.lipsync import RhubarbLipSyncAnalyzer, LipSyncAnalyzer
from integration.avatar.mascot_presenter import MascotPresenter
from integration.models.brain_response import (
    AvatarPresentation,
    BrainResponse,
    CitationItem,
    ConversationState,
    EmotionType,
    GestureType,
)
from integration.server import app
from integration.voice.stt_adapter import VoskSTTAdapter, MockSTTAdapter, get_stt_adapter
from integration.voice.tts_adapter import (
    Member2TTSAdapter,
    SyntheticWavTTSAdapter,
    TTSAudioResult,
    get_tts_adapter,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
MEMBER2_DIR = ROOT_DIR / "avatar" / "Member2_Chacha"


def test_member2_glb_asset_exists():
    glb_path = MEMBER2_DIR / "Chacha_Master.glb"
    assert glb_path.exists(), f"Chacha_Master.glb not found at {glb_path}"
    file_size_mb = glb_path.stat().st_size / (1024 * 1024)
    assert file_size_mb > 50.0, f"GLB file size too small: {file_size_mb:.2f} MB"


def test_member2_glb_validation_report():
    report_path = MEMBER2_DIR / "MEMBER2_GLB_VALIDATION.md"
    assert report_path.exists(), f"Validation report missing at {report_path}"
    content = report_path.read_text(encoding="utf-8")
    assert "57" in content, "Armature 57 bones must be documented"
    assert "Chacha_Idle" in content, "Chacha_Idle clip must be documented"
    assert "Chacha_ShakingHands" in content, "Chacha_ShakingHands clip must be documented"
    assert "Viseme_A" in content, "Visemes must be documented"
    assert "Emotion_Happy" in content, "Facial emotions must be documented"
    assert "60,000" in content, "60,000 vertices documentation required"


def test_member2_emotion_mapper_expanded():
    assert map_emotion("happy") == EmotionType.HAPPY
    assert map_emotion("sad") == EmotionType.SAD
    assert map_emotion("angry") == EmotionType.ANGRY
    assert map_emotion("surprised") == EmotionType.SURPRISED
    assert map_emotion("confused") == EmotionType.CONFUSED
    assert map_emotion("thinking") == EmotionType.THINKING
    assert map_emotion("laughing") == EmotionType.LAUGHING
    assert map_emotion("neutral") == EmotionType.NEUTRAL
    assert map_emotion("invalid_xyz") == EmotionType.NEUTRAL


def test_member2_gesture_mapper_all_9_actions():
    assert map_gesture("idle") == GestureType.IDLE
    assert map_gesture("nod") == GestureType.NOD
    assert map_gesture("point") == GestureType.POINT
    assert map_gesture("shrug") == GestureType.SHRUG
    assert map_gesture("thinking") == GestureType.THINKING
    assert map_gesture("laughing") == GestureType.LAUGHING
    assert map_gesture("wave") == GestureType.WAVE
    assert map_gesture("thankful") == GestureType.THANKFUL
    assert map_gesture("shaking_hands") == GestureType.SHAKING_HANDS


def test_member2_gesture_mapper_aliases():
    assert map_gesture("namaste") == GestureType.THANKFUL
    assert map_gesture("thanks") == GestureType.THANKFUL
    assert map_gesture("greet") == GestureType.WAVE
    assert map_gesture("hello") == GestureType.WAVE
    assert map_gesture("agree") == GestureType.NOD
    assert map_gesture("doubt") == GestureType.SHRUG
    assert map_gesture("handshake") == GestureType.SHAKING_HANDS
    assert map_gesture("chacha_idle") == GestureType.IDLE
    assert map_gesture("chacha_waving") == GestureType.WAVE


def test_member2_vosk_stt_adapter():
    adapter = get_stt_adapter("vosk")
    assert isinstance(adapter, (VoskSTTAdapter, MockSTTAdapter))

    # Empty audio handling
    res_empty = adapter.transcribe_audio(b"", language="hi")
    assert res_empty == ""


def test_member2_tts_adapter_synthetic_fallback():
    tts = SyntheticWavTTSAdapter()
    res = tts.synthesize_speech("Chacha Chaudhary welcomes you to Namami Gange.", language="en")
    assert res is not None
    assert len(res.audio_base64) > 100
    assert res.sample_rate == 16000
    assert res.duration_seconds > 0.5
    assert len(res.pcm_samples) > 0


def test_member2_rhubarb_lipsync_analyzer():
    analyzer = RhubarbLipSyncAnalyzer()
    assert len(analyzer.allowed_visemes) >= 16
    assert "Viseme_Silence" in analyzer.allowed_visemes
    assert "Viseme_A" in analyzer.allowed_visemes
    assert "Viseme_MBP" in analyzer.allowed_visemes

    # Fallback generation test
    fb = analyzer._build_fallback_timeline(1.0)
    assert fb["duration_seconds"] == 1.0
    assert len(fb["visemes"]) > 0
    assert all("viseme" in v for v in fb["visemes"])


def test_member2_mascot_presenter_full_payload():
    presenter = MascotPresenter()
    brain_resp = BrainResponse(
        answer="Ganga is India's sacred river.",
        mode="grounded",
        citations=[CitationItem(source="GRBMP 2020")],
        language="en",
        emotion="happy",
        gesture="point",
    )
    tts = SyntheticWavTTSAdapter()
    tts_result = tts.synthesize_speech(brain_resp.answer, language="en")

    pres = presenter.create_presentation(
        brain_response=brain_resp,
        conversation_state=ConversationState.SPEAKING,
        tts_result=tts_result,
    )

    assert pres.state == ConversationState.SPEAKING
    assert pres.answer == brain_resp.answer
    assert pres.text == brain_resp.answer
    assert pres.emotion == EmotionType.HAPPY
    assert pres.gesture == GestureType.POINT
    assert pres.audio_data_base64 is not None
    assert pres.audio_format == "wav"
    assert len(pres.rms_lip_sync) > 0


def test_member2_api_ask_mock_endpoint():
    client = TestClient(app)
    response = client.post(
        "/api/integration/ask",
        json={"question": "What is the mission of Namami Gange?", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "emotion" in data
    assert "gesture" in data
    assert data["language"] == "en"


def test_member2_api_stt_endpoint():
    client = TestClient(app)
    # Send a small fake audio file to test multipart endpoint handling
    fake_wav = b"RIFF" + b"\x00" * 36 + b"WAVEfmt " + b"\x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data" + b"\x00" * 100
    response = client.post(
        "/api/integration/stt",
        files={"file": ("test.wav", fake_wav, "audio/wav")},
        data={"language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_zero_git_deletions():
    res = subprocess.run(
        ["git", "diff", "--name-status"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    lines = res.stdout.strip().splitlines()
    deleted = [l for l in lines if l.startswith("D\t")]
    assert len(deleted) == 0, f"Strict non-destructive rule violated! Deleted files: {deleted}"
