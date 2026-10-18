"""In-process language route tests with mocked Brain and speech providers."""

from unittest.mock import Mock

from fastapi.testclient import TestClient

from integration.config.integration_config import IntegrationConfig
from integration.server import app


def test_in_process_route_reaches_mocked_generator_and_preserves_response(monkeypatch):
    import integration.server as server

    monkeypatch.setattr(
        server.controller.brain_client,
        "config",
        IntegrationConfig(brain_base_url="http://127.0.0.1:8000", mock_mode=False),
    )
    hit = {
        "chunk_id": "route-hit", "text": "Aviral Dhara maintains continuous river flow.",
        "metadata": {"title": "GRBMP", "file_name": "grbmp.pdf", "page_start": 3,
                     "page_end": 4, "section": "Flow", "knowledge_type": "HISTORICAL"},
    }
    retriever = Mock()
    retriever.retrieve.return_value = (True, [hit])
    generator = Mock()
    generator.generate.return_value = {
        "answer": "Grounded answer", "citations": [{"source": "GRBMP", "file_name": "grbmp.pdf"}],
        "mode": "grounded",
    }
    monkeypatch.setattr("brain.rag_pipeline.Retriever", lambda _cfg: retriever)
    monkeypatch.setattr("brain.rag_pipeline.build_generator", lambda *_args: generator)
    monkeypatch.setattr(server.tts_adapter, "synthesize_speech", lambda *_args, **_kwargs: None)

    response = TestClient(app).post("/api/integration/ask", json={
        "question": "What is Aviral Dhara?", "input_language": "en", "output_language": "en",
    })

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Grounded answer"
    assert data["citations"][0]["file_name"] == "grbmp.pdf"
    assert data["input_language"] == "en"
    assert data["output_language"] == "en"
    generator.generate.assert_called_once()


def test_integration_route_allows_translation_when_field_is_omitted(monkeypatch):
    import integration.server as server

    monkeypatch.setattr(
        server.controller.brain_client,
        "config",
        IntegrationConfig(brain_base_url="http://127.0.0.1:8000", mock_mode=False),
    )
    answer = Mock(return_value={"answer": "Ganga River answer", "mode": "grounded", "citations": []})
    monkeypatch.setattr("brain.rag_pipeline.answer_question", answer)
    monkeypatch.setattr(server.tts_adapter, "synthesize_speech", lambda *_args, **_kwargs: None)

    response = TestClient(app).post("/api/integration/ask", json={
        "question": "ಗಂಗಾ ನದಿ ಎಂದರೇನು?", "input_language": "kn", "output_language": "en",
    })

    assert response.status_code == 200
    assert response.json()["answer"] == "Ganga River answer"
    answer.assert_called_once()
    assert answer.call_args.kwargs["allow_external_translation"] is True


def test_ui_keeps_quiz_and_has_no_translation_consent_control():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    html = (root / "avatar" / "index.html").read_text(encoding="utf-8-sig")
    app_js = (root / "avatar" / "app.js").read_text(encoding="utf-8-sig")
    assert 'id="quizNavButton"' in html
    assert 'src="quiz-data.js"' in html
    assert 'src="quiz.js"' in html
    assert "createQuizController" in app_js
    assert "translation-consent" not in html
    assert "translationConsent" not in html
    assert "Google Translate" not in html
    assert "translationConsent" not in app_js
    assert "translation_consent" not in app_js


def test_speech_language_support_is_configured_but_limited_by_provider():
    from integration.voice.stt_adapter import VoskSTTAdapter
    from avatar.Member2_Chacha.chacha_tts_pipeline import EdgeTTSProvider, LocalSapiTTSProvider

    assert VoskSTTAdapter.SUPPORTED_LANGUAGES == {"en", "hi"}
    adapter = VoskSTTAdapter()
    assert adapter.transcribe_audio(b"RIFF" + b"0" * 48, language="kn") == ""
    assert set(EdgeTTSProvider.DEFAULT_VOICES) == {"en", "hi", "kn", "ta"}
    try:
        LocalSapiTTSProvider().synthesize_to_wav("text", "ta", output_wav="unused.wav")
    except RuntimeError as exc:
        assert "configured" in str(exc)
    else:
        raise AssertionError("SAPI must not silently use an English voice for Tamil")
