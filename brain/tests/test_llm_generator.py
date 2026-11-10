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
    OpenRouterGenerator,
    ProviderChainGenerator,
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


def fake_chat_response(text: str, finish_reason: str = "stop") -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason=finish_reason)]
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

    def test_length_finish_gets_one_bounded_continuation_and_merges_overlap(self):
        partial = (
            "The Ganga rises at Gaumukh and flows toward the Bay of Bengal. "
            "Its course receives many tributaries. The Ganga"
        )
        continuation = "The Ganga joins several major tributaries before reaching the delta."
        self.client.chat.completions.create.side_effect = [
            fake_chat_response(partial, "length"),
            fake_chat_response(continuation, "stop"),
        ]

        result = self.generator.generate("Describe the Ganga.", HITS)

        self.assertEqual(self.client.chat.completions.create.call_count, 2)
        first_call = self.client.chat.completions.create.call_args_list[0].kwargs
        second_call = self.client.chat.completions.create.call_args_list[1].kwargs
        self.assertEqual(first_call["max_completion_tokens"], 700)
        self.assertEqual(second_call["max_completion_tokens"], 700)
        self.assertNotIn("max_tokens", first_call)
        self.assertTrue(result["answer"].endswith("before reaching the delta."))
        self.assertEqual(result["answer"].count("The Ganga joins"), 1)
        self.assertEqual(result["citations"][0]["file_name"], "grbmp.pdf")

    def test_still_truncated_continuation_uses_extractive_fallback(self):
        self.client.chat.completions.create.side_effect = [
            fake_chat_response("A partial answer about the Ganga", "length"),
            fake_chat_response("continues without a sentence ending", "length"),
        ]

        result = self.generator.generate("Describe the Ganga.", HITS)

        self.assertEqual(self.client.chat.completions.create.call_count, 2)
        self.assertEqual(result, ExtractiveGenerator().generate("Describe the Ganga.", HITS))
        self.assertNotIn("A partial answer", result["answer"])

    def test_non_stop_finish_reason_uses_extractive_fallback(self):
        self.client.chat.completions.create.return_value = fake_chat_response(
            "A clipped answer.", "content_filter"
        )

        result = self.generator.generate("Describe the Ganga.", HITS)

        self.assertEqual(result, ExtractiveGenerator().generate("Describe the Ganga.", HITS))

    def test_stop_finish_without_sentence_boundary_is_not_presented(self):
        self.client.chat.completions.create.return_value = fake_chat_response(
            "The Ganga is a major river that flows through several regions"
        )

        result = self.generator.generate("Describe the Ganga.", HITS)

        self.assertNotIn("The Ganga is a major river", result["answer"])
        self.assertEqual(result["answer"], ExtractiveGenerator().generate("Describe the Ganga.", HITS)["answer"])

    def test_incomplete_extractive_fallback_returns_explicit_safe_response(self):
        from brain.generator import INCOMPLETE_GENERATION_MESSAGE

        incomplete_hits = [{**HITS[0], "text": "A long source fragment that has no terminal punctuation"}]
        self.client.chat.completions.create.side_effect = TimeoutError("provider unavailable")

        result = self.generator.generate("What is described?", incomplete_hits)

        self.assertEqual(result["answer"], INCOMPLETE_GENERATION_MESSAGE)
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["mode"], "insufficient-evidence")

    def test_insufficient_evidence_does_not_call_groq(self):
        result = self.generator.generate("Mars?", HITS, False)

        self.client.chat.completions.create.assert_not_called()
        self.assertEqual(result["answer"], INSUFFICIENT_EVIDENCE)
        self.assertEqual(result["mode"], "insufficient-evidence")

    def test_groq_failure_uses_extractive_fallback(self):
        self.client.chat.completions.create.side_effect = TimeoutError("request timed out")

        with self.assertLogs("brain.generator", level="WARNING") as captured:
            result = self.generator.generate("What is Aviral Dhara?", HITS)
        expected = ExtractiveGenerator().generate("What is Aviral Dhara?", HITS)

        self.assertEqual(self.client.chat.completions.create.call_count, 1)
        self.assertEqual(result, expected)
        self.assertIn("groq failed: timeout", "\n".join(captured.output))

    def test_empty_groq_output_uses_extractive_fallback(self):
        self.client.chat.completions.create.return_value = fake_chat_response("  ")

        result = self.generator.generate("What is Aviral Dhara?", HITS)

        self.assertEqual(result, ExtractiveGenerator().generate("What is Aviral Dhara?", HITS))

    def test_hosted_answer_cleanup_removes_exact_repeat_and_extra_spacing(self):
        self.client.chat.completions.create.return_value = fake_chat_response(
            "  Aviral Dhara supports river flow.  Aviral Dhara supports river flow.\n\n It also considers time and space.  "
        )

        result = self.generator.generate("What is Aviral Dhara?", HITS)

        self.assertEqual(result["answer"], "Aviral Dhara supports river flow. It also considers time and space.")
        self.assertEqual(result["citations"][0]["file_name"], "grbmp.pdf")

    def test_missing_api_key_uses_fallback_without_creating_client(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
            generator = GroqGenerator(model=DEFAULT_GROQ_MODEL)
            with self.assertLogs("brain.generator", level="WARNING") as captured:
                result = generator.generate("What is Aviral Dhara?", HITS)

        self.assertIsNone(generator.client)
        self.assertEqual(result, ExtractiveGenerator().generate("What is Aviral Dhara?", HITS))
        self.assertIn("missing_credentials", "\n".join(captured.output))

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
                with self.assertLogs("brain.generator", level="INFO") as captured:
                    result = generator.generate("What is Aviral Dhara?", HITS)

        openai_client.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.groq.com/openai/v1",
            timeout=30.0,
            max_retries=0,
        )
        self.assertEqual(sdk_client.chat.completions.create.call_count, 1)
        self.assertEqual(result["answer"], "Grounded output.")
        self.assertIn("LLM provider groq succeeded", "\n".join(captured.output))

    def test_api_key_is_not_logged_on_failure(self):
        secret = "test-groq-secret"
        self.client.chat.completions.create.side_effect = RuntimeError(secret)

        with self.assertLogs("brain.generator", level="WARNING") as captured:
            self.generator.generate("What is Aviral Dhara?", HITS)

        self.assertNotIn(secret, "\n".join(captured.output))


class ProviderChainTests(unittest.TestCase):
    def test_groq_success_does_not_call_openrouter(self):
        groq_client = Mock()
        groq_client.chat.completions.create.return_value = fake_chat_response("Groq answer.")
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake-groq", "OPENROUTER_API_KEY": "fake-or"}):
            generator = ProviderChainGenerator([
                ("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")
            ])
            with patch("brain.generator._hosted_generator", return_value=GroqGenerator(client=groq_client)) as factory:
                result = generator.generate("What is Aviral Dhara?", HITS)

        self.assertEqual(result["answer"], "Groq answer.")
        factory.assert_called_once_with("groq", DEFAULT_GROQ_MODEL)

    def test_groq_failure_then_openrouter_success_passes_equivalent_context(self):
        groq_client, openrouter_client = Mock(), Mock()
        groq_client.chat.completions.create.side_effect = TimeoutError("private prompt and evidence")
        openrouter_client.chat.completions.create.return_value = fake_chat_response("OpenRouter answer.")
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake-groq", "OPENROUTER_API_KEY": "fake-or"}):
            chain = ProviderChainGenerator([
                ("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")
            ])
            with patch("brain.generator._hosted_generator", side_effect=[
                GroqGenerator(DEFAULT_GROQ_MODEL, groq_client, propagate_failures=True),
                OpenRouterGenerator("nvidia/nemotron-3.5-super-vl:free", openrouter_client, propagate_failures=True),
            ]):
                result = chain.generate("Private prompt", HITS)

        self.assertEqual(result["answer"], "OpenRouter answer.")
        groq_call = groq_client.chat.completions.create.call_args.kwargs
        router_call = openrouter_client.chat.completions.create.call_args.kwargs
        self.assertEqual(groq_call["messages"], router_call["messages"])
        self.assertEqual(groq_call["temperature"], router_call["temperature"])
        self.assertEqual(groq_call["max_completion_tokens"], router_call["max_completion_tokens"])
        self.assertNotIn("reasoning", groq_call)
        self.assertEqual(router_call["extra_body"]["reasoning"], {"enabled": False})
        self.assertEqual(result["citations"], ExtractiveGenerator().generate("q", HITS)["citations"])
        self.assertEqual(result["mode"], "grounded")

    def test_incomplete_groq_continuation_falls_through_to_openrouter(self):
        groq_client, openrouter_client = Mock(), Mock()
        groq_client.chat.completions.create.side_effect = [
            fake_chat_response("The Ganga is a major river. It flows through", "length"),
            fake_chat_response("several regions", "length"),
        ]
        openrouter_client.chat.completions.create.return_value = fake_chat_response(
            "Aviral Dhara means maintaining continuous river flow over time and space."
        )
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake-groq", "OPENROUTER_API_KEY": "fake-or"}):
            chain = ProviderChainGenerator([
                ("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")
            ])
            with patch("brain.generator._hosted_generator", side_effect=[
                GroqGenerator(DEFAULT_GROQ_MODEL, groq_client, propagate_failures=True),
                OpenRouterGenerator("nvidia/nemotron-3.5-super-vl:free", openrouter_client, propagate_failures=True),
            ]):
                result = chain.generate("What is Aviral Dhara?", HITS)

        self.assertEqual(groq_client.chat.completions.create.call_count, 2)
        openrouter_client.chat.completions.create.assert_called_once()
        self.assertEqual(result["answer"], "Aviral Dhara means maintaining continuous river flow over time and space.")
        self.assertEqual(result["citations"][0]["file_name"], "grbmp.pdf")

    def test_missing_groq_key_skips_to_openrouter(self):
        client = Mock()
        client.chat.completions.create.return_value = fake_chat_response("Router answer.")
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": "fake-or"}):
            chain = ProviderChainGenerator([
                ("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")
            ])
            with patch("brain.generator._hosted_generator", side_effect=[
                GroqGenerator(DEFAULT_GROQ_MODEL, propagate_failures=True),
                OpenRouterGenerator("nvidia/nemotron-3.5-super-vl:free", client, propagate_failures=True),
            ]) as factory:
                result = chain.generate("question", HITS)

        self.assertEqual(result["answer"], "Router answer.")
        self.assertEqual(factory.call_count, 2)
        client.chat.completions.create.assert_called_once()

    def test_both_provider_failures_return_extractive_schema_and_citations(self):
        clients = [Mock(), Mock()]
        for client in clients:
            client.chat.completions.create.side_effect = RuntimeError("secret prompt/evidence")
        with patch.dict(os.environ, {"GROQ_API_KEY": "fake-groq", "OPENROUTER_API_KEY": "fake-or"}):
            chain = ProviderChainGenerator([
                ("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")
            ])
            with patch("brain.generator._hosted_generator", side_effect=[
                GroqGenerator(DEFAULT_GROQ_MODEL, clients[0], propagate_failures=True),
                OpenRouterGenerator("nvidia/nemotron-3.5-super-vl:free", clients[1], propagate_failures=True),
            ]):
                result = chain.generate("secret prompt", HITS)

        expected = ExtractiveGenerator().generate("secret prompt", HITS)
        self.assertEqual(result, expected)
        self.assertEqual(set(result), {"answer", "citations", "mode"})

    def test_neither_key_constructs_sdk_client(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "", "OPENROUTER_API_KEY": ""}):
            chain = ProviderChainGenerator([
                ("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")
            ])
            with patch("openai.OpenAI") as sdk:
                result = chain.generate("question", HITS)

        sdk.assert_not_called()
        self.assertEqual(result, ExtractiveGenerator().generate("question", HITS))

    def test_openrouter_first_ordering(self):
        router = Mock()
        router.chat.completions.create.return_value = fake_chat_response("Router primary.")
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-or", "GROQ_API_KEY": "fake-groq"}):
            chain = ProviderChainGenerator([
                ("openrouter", "nvidia/nemotron-3.5-super-vl:free"), ("groq", DEFAULT_GROQ_MODEL)
            ])
            with patch("brain.generator._hosted_generator", return_value=OpenRouterGenerator(
                "nvidia/nemotron-3.5-super-vl:free", router
            )) as factory:
                result = chain.generate("question", HITS)

        self.assertEqual(result["answer"], "Router primary.")
        factory.assert_called_once_with("openrouter", "nvidia/nemotron-3.5-super-vl:free")

    def test_extractive_mode_never_constructs_hosted_providers(self):
        with patch("brain.generator._hosted_generator") as factory:
            result = build_generator("extractive", DEFAULT_GROQ_MODEL).generate("question", HITS)
        factory.assert_not_called()
        self.assertEqual(result, ExtractiveGenerator().generate("question", HITS))

    def test_openrouter_sdk_configuration_and_disabled_reasoning(self):
        client = Mock()
        client.chat.completions.create.return_value = fake_chat_response("OpenRouter answer.")
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "fake-openrouter"}):
            with patch("openai.OpenAI", return_value=client) as sdk:
                generator = OpenRouterGenerator()
                generator.generate("question", HITS)

        sdk.assert_called_once_with(
            api_key="fake-openrouter",
            base_url="https://openrouter.ai/api/v1",
            timeout=30.0,
            max_retries=0,
        )
        call = client.chat.completions.create.call_args.kwargs
        self.assertEqual(call["model"], "nvidia/nemotron-3.5-super-vl:free")
        self.assertEqual(call["extra_body"]["reasoning"], {"enabled": False})

    def test_safe_fallback_logs_exclude_keys_prompts_evidence_and_exception_text(self):
        client = Mock()
        secret_values = ["fake-groq-secret", "prompt-private", "evidence-private", "exception-private"]
        client.chat.completions.create.side_effect = RuntimeError(secret_values[-1])
        with patch.dict(os.environ, {"GROQ_API_KEY": secret_values[0]}):
            chain = ProviderChainGenerator([("groq", DEFAULT_GROQ_MODEL)])
            with patch("brain.generator._hosted_generator", return_value=GroqGenerator(
                DEFAULT_GROQ_MODEL, client, propagate_failures=True
            )):
                with self.assertLogs("brain.generator", level="WARNING") as logs:
                    chain.generate(secret_values[1], [{**HITS[0], "text": secret_values[2]}])

        rendered = "\n".join(logs.output)
        for secret in secret_values:
            self.assertNotIn(secret, rendered)

    def test_provider_errors_all_fall_through_to_next_adapter(self):
        from openai import (
            APIConnectionError,
            AuthenticationError,
            BadRequestError,
            InternalServerError,
            RateLimitError,
        )

        failures = [
            (AuthenticationError("do not log", response=Mock(), body=None), "authentication_or_permission_error"),
            (BadRequestError("do not log", response=Mock(), body=None), "invalid_request_or_model"),
            (fake_chat_response(""), "malformed_response"),
            (RuntimeError("do not log"), "unexpected_provider_error"),
            (TimeoutError("do not log"), "timeout"),
            (APIConnectionError(request=Mock()), "connection_error"),
            (RateLimitError("do not log", response=Mock(), body=None), "rate_limited"),
            (InternalServerError("do not log", response=Mock(), body=None), "provider_server_error"),
        ]
        for failed, expected_category in failures:
            with self.subTest(failure=type(failed).__name__):
                first, second = Mock(), Mock()
                first.chat.completions.create.side_effect = failed if isinstance(failed, Exception) else None
                if not isinstance(failed, Exception):
                    first.chat.completions.create.return_value = failed
                second.chat.completions.create.return_value = fake_chat_response("Second provider succeeded.")
                with patch.dict(os.environ, {"GROQ_API_KEY": "fake-groq", "OPENROUTER_API_KEY": "fake-or"}):
                    chain = ProviderChainGenerator([
                        ("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")
                    ])
                    with patch("brain.generator._hosted_generator", side_effect=[
                        GroqGenerator(DEFAULT_GROQ_MODEL, first, propagate_failures=True),
                        OpenRouterGenerator("nvidia/nemotron-3.5-super-vl:free", second, propagate_failures=True),
                    ]):
                        with self.assertLogs("brain.generator", level="WARNING") as logs:
                            result = chain.generate("question", HITS)
                self.assertEqual(result["answer"], "Second provider succeeded.")
                first.chat.completions.create.assert_called_once()
                second.chat.completions.create.assert_called_once()
                log_text = "\n".join(logs.output)
                self.assertIn("LLM provider groq failed:", log_text)
                self.assertNotIn("do not log", log_text)
                self.assertIn(expected_category, log_text)

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
        self.assertIsInstance(generator, ProviderChainGenerator)
        self.assertEqual(generator.providers, [("groq", DEFAULT_GROQ_MODEL), ("openrouter", "nvidia/nemotron-3.5-super-vl:free")])

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

                def fake_translate(text, source, target, *, allow_external=False):
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
                        allow_external_translation=True,
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

        translate.assert_called_once_with("गंगा नदी क्या है?", "hi", "en", allow_external=False)
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
                    allow_external_translation=True,
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
                    translate_text("गंगा नदी क्या है?", "hi", "en", allow_external=True)

        self.assertIn("429", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
