from unittest.mock import Mock

import pytest

from integration.config.integration_config import IntegrationConfig
from integration.controller.conversation_controller import ConversationController
from integration.models.brain_response import BrainResponse
from integration.scope import classify_request
from integration.external_sources import ExternalSummary


class BrainSpy:
    def __init__(self, response=None):
        self.response = response or BrainResponse(answer="Verified Ganga answer", mode="grounded")
        self.calls = []

    def ask(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


@pytest.mark.parametrize("question", ["Who are you?", "What is your purpose?", "Who is Chacha Chaudhary?"])
def test_identity_routes_before_rag(question):
    brain = BrainSpy()
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question(question, input_language="en", output_language="en")
    assert response.mode == "identity"
    assert response.answer
    assert "Ganga" in response.answer or "Chacha" in response.answer
    assert not brain.calls


@pytest.mark.parametrize("question", [
    "What is Mars?",
    "Tell me about humans.",
    "What are humans?",
    "Explain human evolution.",
    "What is artificial intelligence?",
])
def test_general_questions_use_existing_llm_without_rag(question, monkeypatch):
    brain = BrainSpy()
    generator = Mock()
    generator.generate_general.return_value = {
        "answer": "A concise general knowledge answer.", "citations": [], "mode": "general"
    }
    monkeypatch.setattr("brain.generator.build_generator", lambda *_args: generator)
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question(question, input_language="en", output_language="en")
    assert response.mode == "general"
    assert response.answer.startswith("A concise general knowledge answer.")
    assert "My main purpose is to help you learn about the Ganga" in response.answer
    assert response.citations == []
    generator.generate_general.assert_called_once_with(question)
    assert not brain.calls


def test_general_provider_failure_returns_polite_fallback_without_topic_fact(monkeypatch):
    brain = BrainSpy()
    generator = Mock()
    generator.generate_general.side_effect = RuntimeError("private provider failure details")
    monkeypatch.setattr("brain.generator.build_generator", lambda *_args: generator)
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question("Tell me about humans.", input_language="en", output_language="en")
    assert response.mode == "general-unavailable"
    assert "can’t answer that general-knowledge question right now" in response.answer
    assert "human" not in response.answer.lower()
    assert response.citations == []
    assert not brain.calls


def test_other_river_water_quality_is_not_sent_to_cpcb_or_rag():
    brain = BrainSpy()
    cpcb = Mock()
    controller = ConversationController(
        brain_client=brain, config=IntegrationConfig(mock_mode=True), water_quality_service=cpcb
    )
    response = controller.process_text_question(
        "What is the current water quality of the Yamuna?", input_language="en", output_language="en"
    )
    assert response.mode == "unsupported-water-topic"
    assert "does not currently contain supported monitoring information" in response.answer
    cpcb.readings.assert_not_called()
    assert not brain.calls


def test_supported_ganga_question_continues_to_brain_rag():
    brain = BrainSpy()
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question("What is the Ganga?", input_language="en", output_language="en")
    assert response.mode == "grounded"
    assert len(brain.calls) == 1


@pytest.mark.parametrize("question", [
    "What is the mission of Namami Gange?",
    "What is the importance of the Ganga?",
])
def test_namami_and_ganga_questions_continue_to_rag(question, monkeypatch):
    brain = BrainSpy()
    generator = Mock()
    monkeypatch.setattr("brain.generator.build_generator", lambda *_args: generator)
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question(question, input_language="en", output_language="en")
    assert response.mode == "grounded"
    assert len(brain.calls) == 1
    generator.generate_general.assert_not_called()


def test_multilingual_identity_is_translated_through_existing_pipeline(monkeypatch):
    calls = []

    def translate(text, source, target, **kwargs):
        calls.append((text, source, target, kwargs))
        if target == "en":
            return "Who are you?"
        return "मैं गंगा एआई मार्गदर्शक हूँ।"

    monkeypatch.setattr("brain.translator.translate_text", translate)
    brain = BrainSpy()
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question(
        "ನೀವು ಯಾರು?", input_language="kn", output_language="hi", translation_consent=True
    )
    assert response.mode == "identity"
    assert response.answer == "मैं गंगा एआई मार्गदर्शक हूँ।"
    assert [call[2] for call in calls] == ["en", "hi"]
    assert not brain.calls


def test_romanized_identity_question_is_translated_for_routing(monkeypatch):
    calls = []

    def translate(text, source, target, **_kwargs):
        calls.append((text, source, target))
        return "Who are you?" if target == "en" else "आप गंगा एआई मार्गदर्शक से बात कर रहे हैं।"

    monkeypatch.setattr("brain.translator.translate_text", translate)
    brain = BrainSpy()
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question(
        "Aap kaun hain?", input_language="hi", output_language="hi", translation_consent=True
    )
    assert response.mode == "identity"
    assert response.answer.startswith("आप गंगा")
    assert [call[2] for call in calls] == ["en", "hi"]
    assert not brain.calls


@pytest.mark.parametrize(("route_query", "expected_mode"), [
    ("What is the current water quality of the Yamuna?", "unsupported-water-topic"),
    ("What is Mars?", "general"),
])
def test_multilingual_scope_responses_use_selected_output_language(monkeypatch, route_query, expected_mode):
    translated_outputs = []

    def translate(text, source, target, **_kwargs):
        if target == "en":
            return route_query
        translated_outputs.append(target)
        return f"localized {expected_mode} answer"

    monkeypatch.setattr("brain.translator.translate_text", translate)
    brain = BrainSpy()
    generator = Mock()
    generator.generate_general.return_value = {
        "answer": "A concise answer.", "citations": [], "mode": "general"
    }
    monkeypatch.setattr("brain.generator.build_generator", lambda *_args: generator)
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    response = controller.process_text_question(
        "हिंदी में प्रश्न", input_language="hi", output_language="ta", translation_consent=True
    )
    assert response.mode == expected_mode
    assert response.answer == f"localized {expected_mode} answer"
    assert translated_outputs == ["ta"]
    if expected_mode == "general":
        generator.generate_general.assert_called_once_with(route_query)
    else:
        generator.generate_general.assert_not_called()
    assert not brain.calls


@pytest.mark.parametrize("question,route", [
    ("What is the current water quality of Yamuna?", "unsupported-water-topic"),
    ("What is the mission of Namami Gange?", None),
    ("How does Ganga basin management work?", None),
    ("What is Mars?", "general"),
])
def test_scope_classifier_separates_route_categories(question, route):
    assert classify_request(question) == route


def test_project_domain_queries_without_the_word_ganga_still_route_to_rag():
    assert classify_request("Tell me about Sewage Treatment Plants (STP) capacity.") is None
    assert classify_request("How does river conservation work?") is None


def test_external_river_context_is_attributed_and_does_not_use_rag():
    brain = BrainSpy()
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    controller.external_source_service.search_summaries = Mock(return_value=[ExternalSummary(
        title="Yamuna River", extract="The Yamuna is a major tributary of the Ganges.",
        url="https://en.wikipedia.org/wiki/Yamuna", language="en",
    )])
    response = controller.process_text_question("Tell me about the Yamuna", input_language="en", output_language="en")
    assert response.mode == "external-river-context"
    assert response.citations[0].url == "https://en.wikipedia.org/wiki/Yamuna"
    assert response.citations[0].license == "CC BY-SA 4.0 / GFDL"
    assert not brain.calls


def test_insufficient_broad_ganga_rag_gets_separate_external_background():
    brain = BrainSpy(BrainResponse(
        answer="I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.",
        mode="insufficient-evidence",
    ))
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    summary = ExternalSummary(
        title="Ganges", extract="The Ganges is a transboundary river in South Asia.",
        url="https://en.wikipedia.org/wiki/Ganges", language="en",
    )
    controller.external_source_service.search_summaries = Mock(return_value=[summary])
    response = controller.process_text_question(
        "Tell me about the Ganga in points.", input_language="en", output_language="en"
    )
    assert response.mode == "insufficient-evidence"
    assert "did not provide enough evidence for a grounded answer" in response.answer
    assert "### Additional information" in response.answer
    assert "not verified by the project knowledge base" in response.answer
    assert response.citations[0].source_type == "external"
    assert response.citations[0].url == summary.url
    controller.external_source_service.search_summaries.assert_called_once_with(
        "Tell me about the Ganga.", language="en", max_sources=1
    )
    assert len(brain.calls) == 1


def test_insufficient_specific_pollution_query_does_not_use_ganga_overview_supplement():
    brain = BrainSpy(BrainResponse(answer="No verified evidence.", mode="insufficient-evidence"))
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    controller.external_source_service.search_summaries = Mock(return_value=[])
    response = controller.process_text_question(
        "Tell me about Ganga pollution.", input_language="en", output_language="en"
    )
    assert response.answer == "No verified evidence."
    controller.external_source_service.search_summaries.assert_not_called()


def test_general_response_cache_avoids_second_llm_call(monkeypatch):
    brain = BrainSpy()
    generator = Mock()
    generator.generate_general.return_value = {
        "answer": "Mars is a planet.", "citations": [], "mode": "general"
    }
    monkeypatch.setattr("brain.generator.build_generator", lambda *_args: generator)
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    first = controller.process_text_question("What is Mars?", input_language="en", output_language="en")
    controller.finish_speaking("en", "en")
    second = controller.process_text_question("What is Mars?", input_language="en", output_language="en")
    assert first.answer == second.answer
    generator.generate_general.assert_called_once_with("What is Mars?")


def test_general_external_source_is_optional_and_kept_separate(monkeypatch):
    brain = BrainSpy()
    generator = Mock()
    generator.generate_general.return_value = {
        "answer": "Mars is a planet.", "citations": [], "mode": "general"
    }
    monkeypatch.setattr("brain.generator.build_generator", lambda *_args: generator)
    controller = ConversationController(brain_client=brain, config=IntegrationConfig(mock_mode=True))
    controller.external_source_service.search_summaries = Mock(return_value=[ExternalSummary(
        title="Mars", extract="Mars has two moons named Phobos and Deimos.",
        url="https://en.wikipedia.org/wiki/Mars", language="en",
    )])
    response = controller.process_text_question(
        "What is Mars? Include sources.", input_language="en", output_language="en"
    )
    assert response.answer.startswith("Mars is a planet.")
    assert "### Additional information" in response.answer
    assert response.citations[0].source_type == "external"
