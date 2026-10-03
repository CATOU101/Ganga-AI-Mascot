"""Tests for evidence-gated Groq generation and extractive fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from brain.config import DEFAULT_GROQ_MODEL, BrainConfig
from brain.generator import (
    ExtractiveGenerator,
    GroqGenerator,
    build_generator,
    current_information_response,
    insufficient_evidence_response,
)
from brain.prompts import GROUNDING_SYSTEM_PROMPT, INSUFFICIENT_EVIDENCE
from brain.rag_pipeline import answer_question
from brain.translator import TranslationError, translate_text


HITS = [
    {
        "chunk_id": "chunk-1",
        "text": "Aviral Dhara means maintaining continuous flow in the river in time and space.",
        "metadata": {
            "title": "Ganga River Basin Management Plan",
            "file_name": "grbmp.pdf",
            "page_start": 10,
            "page_end": 11,
            "section": "Mission 1",
            "knowledge_type": "HISTORICAL",
        },
        "distance": 0.3,
    }
]


def fake_chat_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


class GroqGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.client.chat.completions.create.return_value = fake_chat_response(
            "Aviral Dhara means maintaining continuous river flow over time and space."
        )
        self.generator = GroqGenerator(model=DEFAULT_GROQ_MODEL, client=self.client)

    def test_valid_evidence_calls_groq_once_and_preserves_trusted_citations(self):
        result = self.generator.generate(
            "What is Aviral Dhara?",
            HITS,
            True,
            input_language="en",
            output_language="hi",
        )

        self.assertEqual(self.client.chat.completions.create.call_count, 1)
        call = self.client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["model"], DEFAULT_GROQ_MODEL)
        self.assertEqual(call["temperature"], 0)
        self.assertIn(GROUNDING_SYSTEM_PROMPT, call["messages"][0]["content"])
        request_input = json.loads(call["messages"][1]["content"])
        self.assertEqual(request_input["question"], "What is Aviral Dhara?")
        self.assertEqual(request_input["input_language"], "en")
        self.assertEqual(request_input["output_language"], "hi")
        self.assertEqual(request_input["evidence"][0]["chunk_id"], "chunk-1")
        self.assertEqual(request_input["evidence"][0]["metadata"]["file_name"], "grbmp.pdf")
        self.assertEqual(request_input["evidence"][0]["metadata"]["page_start"], 10)
        self.assertEqual(result["answer"], "Aviral Dhara means maintaining continuous river flow over time and space.")
        self.assertEqual(result["mode"], "grounded")
        self.assertEqual(result["citations"][0]["file_name"], "grbmp.pdf")
        self.assertEqual(result["citations"][0]["page"], "10-11")

    def test_insufficient_evidence_does_not_call_groq(self):
        result = self.generator.generate("Mars?", HITS, False)

        self.client.chat.completions.create.assert_not_called()
        self.assertEqual(result["answer"], INSUFFICIENT_EVIDENCE)
        self.assertEqual(result["mode"], "insufficient-evidence")

    def test_groq_failure_uses_extractive_fallback(self):
        self.client.chat.completions.create.side_effect = TimeoutError("request timed out")

        result = self.generator.generate("What is Aviral Dhara?", HITS)
        expected = ExtractiveGenerator().generate("What is Aviral Dhara?", HITS)

        self.assertEqual(self.client.chat.completions.create.call_count, 1)
        self.assertEqual(result, expected)

    def test_empty_groq_output_uses_extractive_fallback(self):
        self.client.chat.completions.create.return_value = fake_chat_response("  ")

        result = self.generator.generate("What is Aviral Dhara?", HITS)

        self.assertEqual(result, ExtractiveGenerator().generate("What is Aviral Dhara?", HITS))

    def test_missing_api_key_uses_fallback_without_creating_client(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
            generator = GroqGenerator(model=DEFAULT_GROQ_MODEL)
            result = generator.generate("What is Aviral Dhara?", HITS)

        self.assertIsNone(generator.client)
        self.assertEqual(result, ExtractiveGenerator().generate("What is Aviral Dhara?", HITS))

    def test_evidence_context_is_bounded(self):
        many_hits = [
            {**HITS[0], "chunk_id": str(index), "text": "x" * 4000}
            for index in range(3)
        ]

        evidence = GroqGenerator._evidence_records(many_hits)

        self.assertEqual(sum(len(record["text"]) for record in evidence), 6000)

    def test_citations_only_include_hits_sent_to_groq(self):
        hits = [
            {**HITS[0], "text": "x" * 6000},
            {
                **HITS[0],
                "chunk_id": "not-sent",
                "text": "A second evidence record omitted by the context budget.",
                "metadata": {**HITS[0]["metadata"], "file_name": "not-sent.pdf"},
            },
        ]

        result = self.generator.generate("question", hits)
        request_input = json.loads(self.client.chat.completions.create.call_args.kwargs["messages"][1]["content"])

        self.assertEqual([item["chunk_id"] for item in request_input["evidence"]], ["chunk-1"])
        self.assertEqual([citation["file_name"] for citation in result["citations"]], ["grbmp.pdf"])

    def test_groq_key_and_model_are_read_from_environment(self):
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "test-key", "GROQ_MODEL": "configured-groq-model", "LLM_PROVIDER": "groq"},
        ):
            config = BrainConfig()
            generator = GroqGenerator()

        self.assertEqual(generator.api_key, "test-key")
        self.assertEqual(generator.model, "configured-groq-model")
        self.assertEqual(config.llm_model, "configured-groq-model")
        self.assertEqual(config.llm_provider, "groq")

    def test_default_model_and_provider(self):
        with patch.dict(os.environ, {}, clear=True):
            config = BrainConfig()
            generator = GroqGenerator()

        self.assertEqual(generator.model, "openai/gpt-oss-120b")
        self.assertEqual(config.llm_model, DEFAULT_GROQ_MODEL)
        self.assertEqual(config.llm_provider, "groq")

    def test_sdk_uses_groq_base_url_and_does_not_retry(self):
        sdk_client = Mock()
        sdk_client.chat.completions.create.return_value = fake_chat_response("Grounded output.")

        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            with patch("openai.OpenAI", return_value=sdk_client) as openai_client:
                generator = GroqGenerator(model=DEFAULT_GROQ_MODEL)
                result = generator.generate("What is Aviral Dhara?", HITS)

        openai_client.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.groq.com/openai/v1",
            timeout=30.0,
            max_retries=0,
        )
        self.assertEqual(sdk_client.chat.completions.create.call_count, 1)
        self.assertEqual(result["answer"], "Grounded output.")

    def test_api_key_is_not_logged_on_failure(self):
        secret = "test-groq-secret"
        self.client.chat.completions.create.side_effect = RuntimeError(secret)

        with self.assertLogs("brain.generator", level="WARNING") as captured:
            self.generator.generate("What is Aviral Dhara?", HITS)

        self.assertNotIn(secret, "\n".join(captured.output))


class PipelineLLMGateTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(llm_provider="groq", llm_model=DEFAULT_GROQ_MODEL)

    def test_approved_evidence_is_sent_to_one_groq_call(self):
        client = Mock()
        client.chat.completions.create.return_value = fake_chat_response("A grounded answer.")
        generator = GroqGenerator(model=DEFAULT_GROQ_MODEL, client=client)
        retriever = Mock()
        retriever.retrieve.return_value = (True, HITS)

        with (
            patch("brain.rag_pipeline.load_config", return_value=self.config),
            patch("brain.rag_pipeline.Retriever", return_value=retriever),
            patch("brain.rag_pipeline.build_generator", return_value=generator) as build,
        ):
            result = answer_question("What is Aviral Dhara?", input_language="en", output_language="en")

        build.assert_called_once_with("groq", DEFAULT_GROQ_MODEL)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        self.assertEqual(result["answer"], "A grounded answer.")

    def test_build_generator_selects_groq(self):
        generator = build_generator("groq", DEFAULT_GROQ_MODEL)
        self.assertIsInstance(generator, GroqGenerator)

    def test_rejected_evidence_never_builds_or_calls_groq(self):
        retriever = Mock()
        retriever.retrieve.return_value = (False, [])

        with (
            patch("brain.rag_pipeline.load_config", return_value=self.config),
            patch("brain.rag_pipeline.Retriever", return_value=retriever),
            patch("brain.rag_pipeline.build_generator") as build,
        ):
            result = answer_question("What is Aviral Dhara?", input_language="en", output_language="en")

        build.assert_not_called()
        self.assertEqual(result["mode"], "insufficient-evidence")
        self.assertEqual(result["answer"], insufficient_evidence_response()["answer"])

    def test_current_information_never_builds_or_calls_groq(self):
        with (
            patch("brain.rag_pipeline.load_config", return_value=self.config),
            patch("brain.rag_pipeline.build_generator") as build,
        ):
            result = answer_question(
                "What is the current water quality of Ganga today?",
                input_language="en",
                output_language="en",
            )

        build.assert_not_called()
        self.assertEqual(result["mode"], "current-info-fallback")
        self.assertEqual(result["answer"], current_information_response()["answer"])


class PipelineLanguageHandlingTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(llm_provider="groq", llm_model=DEFAULT_GROQ_MODEL)

    def test_supported_language_pairs_translate_only_at_required_boundaries(self):
        cases = (
            ("en", "en", "What is the Ganga River?", []),
            (
                "hi",
                "hi",
                "गंगा नदी क्या है?",
                [
                    ("गंगा नदी क्या है?", "hi", "en"),
                    ("A grounded answer.", "en", "hi"),
                ],
            ),
            (
                "hi",
                "en",
                "गंगा नदी क्या है?",
                [("गंगा नदी क्या है?", "hi", "en")],
            ),
            (
                "en",
                "hi",
                "What is the Ganga River?",
                [("A grounded answer.", "en", "hi")],
            ),
        )

        for input_language, output_language, question, expected_translations in cases:
            with self.subTest(input_language=input_language, output_language=output_language):
                retriever = Mock()
                retriever.retrieve.return_value = (True, HITS)
                generator = Mock()
                generator.generate.return_value = {
                    "answer": "A grounded answer.",
                    "citations": [{"file_name": "grbmp.pdf"}],
                    "mode": "grounded",
                }

                def fake_translate(text, source, target):
                    if (source, target) == ("hi", "en"):
                        return "What is the Ganga River?"
                    if (source, target) == ("en", "hi"):
                        return "गंगा नदी का उत्तर।"
                    raise AssertionError(f"Unexpected translation: {source}->{target}")

                with (
                    patch("brain.rag_pipeline.load_config", return_value=self.config),
                    patch("brain.rag_pipeline.Retriever", return_value=retriever),
                    patch("brain.rag_pipeline.build_generator", return_value=generator),
                    patch("brain.rag_pipeline.translate_text", side_effect=fake_translate) as translate,
                ):
                    result = answer_question(
                        question,
                        input_language=input_language,
                        output_language=output_language,
                    )

                self.assertEqual(
                    [(call.args[0], call.args[1], call.args[2]) for call in translate.call_args_list],
                    expected_translations,
                )
                retriever.retrieve.assert_called_once_with("What is the Ganga River?", None)
                generator.generate.assert_called_once()
                self.assertEqual(generator.generate.call_args.args[0], "What is the Ganga River?")
                self.assertEqual(result["mode"], "grounded")
                self.assertEqual(result["citations"], [{"file_name": "grbmp.pdf"}])
                if output_language == "hi":
                    self.assertEqual(result["answer"], "गंगा नदी का उत्तर।")
                else:
                    self.assertEqual(result["answer"], "A grounded answer.")

    def test_hindi_input_translation_failure_stops_before_retrieval_and_groq(self):
        with (
            patch("brain.rag_pipeline.load_config", return_value=self.config),
            patch("brain.rag_pipeline.translate_text", side_effect=TranslationError("HTTP 429")) as translate,
            patch("brain.rag_pipeline.Retriever") as retriever,
            patch("brain.rag_pipeline.build_generator") as build,
        ):
            with self.assertRaises(TranslationError):
                answer_question(
                    "गंगा नदी क्या है?",
                    input_language="hi",
                    output_language="hi",
                )

        translate.assert_called_once_with("गंगा नदी क्या है?", "hi", "en")
        retriever.assert_not_called()
        build.assert_not_called()

    def test_output_translation_failure_occurs_after_generation(self):
        retriever = Mock()
        retriever.retrieve.return_value = (True, HITS)
        generator = Mock()
        generator.generate.return_value = {
            "answer": "A grounded answer.",
            "citations": [{"file_name": "grbmp.pdf"}],
            "mode": "grounded",
        }

        with (
            patch("brain.rag_pipeline.load_config", return_value=self.config),
            patch("brain.rag_pipeline.Retriever", return_value=retriever),
            patch("brain.rag_pipeline.build_generator", return_value=generator),
            patch("brain.rag_pipeline.translate_text", side_effect=TranslationError("HTTP 429")),
        ):
            with self.assertRaises(TranslationError):
                answer_question(
                    "What is the Ganga River?",
                    input_language="en",
                    output_language="hi",
                )

        generator.generate.assert_called_once()

    def test_google_translation_429_is_reported_as_translation_error(self):
        http_429 = urllib.error.HTTPError(
            "https://translate.googleapis.com/translate_a/single",
            429,
            "Too Many Requests",
            hdrs=None,
            fp=None,
        )
        with patch("brain.translator.urllib.request.urlopen", side_effect=http_429):
            with self.assertLogs("brain.translator", level="WARNING") as captured:
                with self.assertRaises(TranslationError):
                    translate_text("गंगा नदी क्या है?", "hi", "en")

        self.assertIn("429", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
