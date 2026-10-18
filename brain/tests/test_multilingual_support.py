"""Focused privacy, language, and RAG integration tests; all providers are mocked."""

from types import SimpleNamespace
import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from brain.api import AskRequest, app
from brain.prompts import INSUFFICIENT_EVIDENCE
from brain.rag_pipeline import answer_question
from brain.translator import (
    TranslationConsentRequired,
    TranslationError,
    _external_translate,
    detect_language,
    translate_text,
)


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("What is Ganga?", "en"),
        ("गंगा नदी क्या है?", "hi"),
        ("ಗಂಗಾ ನದಿ ಎಂದರೇನು?", "kn"),
        ("கங்கை நதி என்றால் என்ன?", "ta"),
    ],
)
def test_detection_and_explicit_language_precedence(text, language):
    assert detect_language(text) == language
    assert AskRequest(question=text).get_input_language() == language
    assert AskRequest(question=text, input_language="en").get_input_language() == "en"


def test_detection_failure_uses_safe_default():
    assert detect_language("123 !?") == "en"
    assert detect_language("123 !?", default="hi") == "hi"


def test_translation_is_disabled_by_default_and_does_not_call_network():
    with patch("brain.translator.urllib.request.urlopen") as urlopen:
        with pytest.raises(TranslationConsentRequired):
            translate_text("A question containing private details", "en", "kn")
    urlopen.assert_not_called()


@pytest.mark.parametrize("language", ["hi", "kn", "ta"])
def test_supported_language_translation_uses_mock_provider(language):
    provider = Mock()
    provider.translate.return_value = f"translated-{language}"
    result = translate_text("A mocked sentence", "en", language, allow_external=True, provider=provider)
    assert result == f"translated-{language}"
    provider.translate.assert_called_once_with("A mocked sentence", "en", language)


def test_translation_timeout_and_provider_errors_are_sanitized(caplog):
    secret = "PRIVATE-PROMPT-AND-EXCEPTION"
    with patch("brain.translator.urllib.request.urlopen", side_effect=TimeoutError(secret)):
        with pytest.raises(TranslationError, match="unavailable") as error:
            _external_translate(secret, "en", "hi")
    assert secret not in str(error.value)
    assert secret not in caplog.text

    provider = Mock()
    provider.translate.side_effect = RuntimeError(secret)
    with pytest.raises(TranslationError):
        translate_text("safe test", "en", "ta", allow_external=True, provider=provider)
    assert secret not in caplog.text


def test_same_language_translation_bypasses_provider():
    provider = Mock()
    text = "English text remains unchanged."
    assert translate_text(text, "en", "en", allow_external=True, provider=provider) == text
    provider.translate.assert_not_called()


def test_provider_response_is_mocked_and_parsed():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps([[['ಗಂಗಾ', 'Ganga']]], ensure_ascii=False).encode("utf-8")

    with patch("brain.translator.urllib.request.urlopen", return_value=Response()) as urlopen:
        assert _external_translate("Ganga", "en", "kn") == "ಗಂಗಾ"
    assert urlopen.call_args.kwargs["timeout"] <= 8.0


def test_rag_evidence_rejection_bypasses_generator_and_preserves_schema():
    config = SimpleNamespace(llm_provider="groq", llm_model="model", llm_provider_order=("groq", "openrouter"))
    retriever = Mock()
    retriever.retrieve.return_value = (False, [])
    with patch("brain.rag_pipeline.load_config", return_value=config), \
         patch("brain.rag_pipeline.Retriever", return_value=retriever), \
         patch("brain.rag_pipeline.build_generator") as build:
        response = answer_question("What is Ganga?", input_language="en", output_language="en")
    build.assert_not_called()
    assert response["answer"] == INSUFFICIENT_EVIDENCE
    assert response["citations"] == []
    assert response["mode"] == "insufficient-evidence"


def test_current_information_bypass_does_not_construct_retriever_or_generator():
    config = SimpleNamespace(llm_provider="groq", llm_model="model", llm_provider_order=("groq", "openrouter"))
    with patch("brain.rag_pipeline.load_config", return_value=config), \
         patch("brain.rag_pipeline.asks_for_current_information", return_value=True), \
         patch("brain.rag_pipeline.Retriever") as retriever, \
         patch("brain.rag_pipeline.build_generator") as build:
        response = answer_question("What is happening today?", input_language="en", output_language="en")
    retriever.assert_not_called()
    build.assert_not_called()
    assert response["mode"] == "current-info-fallback"


def test_missing_output_translation_consent_stops_before_generator():
    config = SimpleNamespace(llm_provider="groq", llm_model="model", llm_provider_order=("groq", "openrouter"))
    retriever = Mock()
    retriever.retrieve.return_value = (True, [{"chunk_id": "e1", "text": "Evidence text.", "metadata": {}}])
    with patch("brain.rag_pipeline.load_config", return_value=config), \
         patch("brain.rag_pipeline.Retriever", return_value=retriever), \
         patch("brain.rag_pipeline.build_generator") as build:
        with pytest.raises(TranslationConsentRequired):
            answer_question("What is Ganga?", input_language="en", output_language="ta")
    build.assert_not_called()


def test_eligible_rag_question_keeps_retrieved_citations_and_translates_with_consent():
    hit = {
        "chunk_id": "chunk-1", "text": "Aviral Dhara maintains continuous river flow.",
        "metadata": {"title": "GRBMP", "file_name": "g.pdf", "page_start": 3, "page_end": 4,
                     "section": "Flow", "knowledge_type": "HISTORICAL"},
    }
    config = SimpleNamespace(llm_provider="groq", llm_model="model", llm_provider_order=("groq", "openrouter"))
    retriever = Mock()
    retriever.retrieve.return_value = (True, [hit])
    generator = Mock()
    generator.generate.return_value = {"answer": "Grounded English answer", "citations": [{"source": "GRBMP"}], "mode": "grounded"}
    translated = Mock(return_value="उत्तर")
    with patch("brain.rag_pipeline.load_config", return_value=config), \
         patch("brain.rag_pipeline.Retriever", return_value=retriever), \
         patch("brain.rag_pipeline.build_generator", return_value=generator), \
         patch("brain.rag_pipeline.translate_text", translated):
        response = answer_question(
            "What is Aviral Dhara?", input_language="en", output_language="hi",
            allow_external_translation=True,
        )
    assert response["answer"] == "उत्तर"
    assert response["citations"] == [{"source": "GRBMP"}]
    assert response["retrieved"][0]["chunk_id"] == "chunk-1"
    generator.generate.assert_called_once()
    translated.assert_called_once_with(
        "Grounded English answer", "en", "hi", allow_external=True,
    )


def test_brain_api_explicitly_disables_external_translation_when_requested(monkeypatch):
    client = TestClient(app)
    retriever = Mock()
    monkeypatch.setattr("brain.rag_pipeline.Retriever", retriever)
    response = client.post("/ask", json={
        "question": "ನಮಸ್ಕಾರ ಹೊಸ ಪ್ರಶ್ನೆ", "input_language": "kn", "output_language": "en",
        "translation_consent": False,
    })
    assert response.status_code == 428
    assert "disabled" in response.json()["detail"].lower()
    retriever.assert_not_called()


def test_brain_api_defaults_translation_on_when_field_is_omitted(monkeypatch):
    client = TestClient(app)
    ask = Mock(return_value={"answer": "answer", "mode": "grounded", "citations": []})
    monkeypatch.setattr("brain.api.answer_question", ask)
    for language in ("en", "hi", "kn", "ta"):
        response = client.post("/ask", json={
            "question": "What is Ganga?", "input_language": "en",
            "output_language": language,
        })
        assert response.status_code == 200
        assert response.json()["output_language"] == language
    assert ask.call_count == 4
    assert all(call.kwargs["allow_external_translation"] is True for call in ask.call_args_list)
