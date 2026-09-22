"""Unit tests for Integration Brain HTTP Client."""

import pytest
from integration.api.brain_client import BrainClient
from integration.config.integration_config import IntegrationConfig
from integration.models.brain_response import EmotionType, GestureType


def test_brain_client_mock_mode():
    config = IntegrationConfig(mock_mode=True)
    client = BrainClient(config)

    res = client.ask("What is Aviral Dhara?", language="en")
    assert res.answer != ""
    assert res.mode == "grounded"
    assert len(res.citations) > 0
    assert res.emotion in (EmotionType.NEUTRAL, EmotionType.HAPPY, EmotionType.SAD, EmotionType.THINKING)
    assert res.gesture in (GestureType.EXPLAINING, GestureType.WAVE, GestureType.THINKING)


def test_brain_client_empty_question():
    client = BrainClient(IntegrationConfig(mock_mode=True))
    res = client.ask("   ", language="hi")
    assert res.mode == "insufficient-evidence"
    assert "Please ask a question" in res.answer


def test_brain_client_connection_failure(monkeypatch):
    # Invalid port to trigger connection error and mock in-process failure
    config = IntegrationConfig(brain_base_url="http://127.0.0.1:59999", brain_timeout_seconds=1.0, mock_mode=False)
    client = BrainClient(config)

    import brain.rag_pipeline
    monkeypatch.setattr(brain.rag_pipeline, "answer_question", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("In-process failure")))

    res = client.ask("What is pollution in Ganga?", language="en")
    assert res.mode == "insufficient-evidence"
    assert "trouble connecting" in res.answer or "issue" in res.answer


def test_brain_client_parse_response_validation():
    client = BrainClient()
    raw_bytes = b'{"answer": "Ganga pollution test", "mode": "grounded", "citations": [{"source": "GRBMP Title"}], "emotion": "happy", "gesture": "wave"}'
    
    parsed = client._parse_response(raw_bytes, request_language="hi")
    assert parsed.answer == "Ganga pollution test"
    assert parsed.mode == "grounded"
    assert len(parsed.citations) == 1
    assert parsed.citations[0].source == "GRBMP Title"
    assert parsed.emotion == EmotionType.HAPPY
    assert parsed.gesture == GestureType.WAVE
