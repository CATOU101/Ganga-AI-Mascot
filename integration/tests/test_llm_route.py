"""Integration route coverage for the in-process educational RAG path."""

from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient

from integration.config.integration_config import IntegrationConfig


def test_in_process_integration_route_reaches_mocked_llm(monkeypatch):
    import integration.server as server

    hit = {
        "chunk_id": "test-chunk",
        "text": "Aviral Dhara means maintaining continuous flow in the river in time and space.",
        "metadata": {
            "title": "Test source",
            "file_name": "test.pdf",
            "page_start": 1,
            "page_end": 1,
            "section": "Test section",
            "knowledge_type": "STATIC",
        },
        "distance": 0.2,
    }
    llm_generator = Mock()
    llm_generator.generate.return_value = {
        "answer": "Mocked Groq answer.",
        "citations": [{"source": "Test source", "file_name": "test.pdf", "page": "1-1"}],
        "mode": "grounded",
    }
    retriever = Mock()
    retriever.retrieve.return_value = (True, [hit])

    monkeypatch.setattr(
        server.controller.brain_client,
        "config",
        IntegrationConfig(mock_mode=False, brain_base_url="http://127.0.0.1:8000"),
    )
    monkeypatch.setattr(server.controller, "water_quality_service", None)
    synthesize = Mock(return_value=None)
    monkeypatch.setattr(server.tts_adapter, "synthesize_speech", synthesize)
    monkeypatch.setattr("brain.rag_pipeline.load_config", lambda: SimpleNamespace(
        llm_provider="groq", llm_model="openai/gpt-oss-120b"
    ))
    monkeypatch.setattr("brain.rag_pipeline.Retriever", lambda _config: retriever)
    monkeypatch.setattr("brain.rag_pipeline.build_generator", lambda *_args: llm_generator)

    response = TestClient(server.app).post(
        "/api/integration/ask",
        json={"question": "What is Aviral Dhara?", "input_language": "en", "output_language": "en"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Mocked Groq answer."
    assert response.json()["spoken_text"] == "Mocked Groq answer."
    assert synthesize.call_args.args[0] == response.json()["spoken_text"]
    assert llm_generator.generate.call_count == 1
    assert retriever.retrieve.call_count == 1
