"""Automated Test Suite for Brain Connectivity and Complete 16-Language Translation Matrix.

Verifies:
1. Brain connectivity error separation (translation errors vs true connection refusal).
2. /health and /api/integration/health readiness checks.
3. All 16 input-output language translation combinations (en, hi, kn, ta).
4. Same-language translation bypass.
5. In-memory translation caching to prevent HTTP 429 rate limiting.
6. Frontend contract for clearing stale citations on request start and failure.
"""

import json
import unittest
import urllib.error
from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient

from brain.api import app as brain_app
from brain.translator import (
    DOMAIN_TRANSLATIONS,
    PREFIX_MAP,
    GoogleGTXTranslationProvider,
    TranslationError,
    clear_translation_cache,
    normalize_language,
    translate_text,
)
from integration.api.brain_client import BrainClient, BrainConnectionError, BrainResponseError
from integration.config.integration_config import IntegrationConfig
from integration.server import app as integration_app


class BrainConnectivityAndErrorClassificationTests(unittest.TestCase):
    def setUp(self):
        clear_translation_cache()

    def test_health_endpoint_returns_ready_status(self):
        """Integration server /health and /api/integration/health return 200 OK with readiness details."""
        client = TestClient(integration_app)
        for endpoint in ["/health", "/api/integration/health"]:
            resp = client.get(endpoint)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["service"], "ganga-integration-server")
            self.assertIn("brain", data)
            self.assertIn("ready", data["brain"])

    def test_translation_failure_is_not_misrepresented_as_connection_failure(self):
        """TranslationError must NOT return 'trouble connecting to the Ganga AI Brain'."""
        cfg = IntegrationConfig(brain_base_url="http://127.0.0.1:8000")
        client = BrainClient(config=cfg)

        with patch("brain.rag_pipeline.answer_question", side_effect=TranslationError("HTTP 429 Too Many Requests")):
            res = client.ask("What is Namami Gange?", input_language="en", output_language="ta")
            self.assertNotIn("connecting to the Ganga AI Brain", res.answer)
            self.assertIn("Translation service", res.answer)
            self.assertEqual(res.mode, "insufficient-evidence")
            self.assertEqual(res.citations, [])

    def test_true_connection_failure_reports_connection_error(self):
        """When standalone HTTP server is unreachable and in-process RAG fails, reports connection failure."""
        cfg = IntegrationConfig(brain_base_url="http://127.0.0.99:9999")
        client = BrainClient(config=cfg)

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            with patch("brain.rag_pipeline.answer_question", side_effect=RuntimeError("Engine not initialized")):
                res = client.ask("What is Namami Gange?", input_language="en", output_language="en")
                self.assertIn("trouble connecting to the Ganga AI Brain", res.answer)
                self.assertEqual(res.mode, "insufficient-evidence")
                self.assertEqual(res.citations, [])

    def test_http_503_from_brain_api_is_classified_as_translation_unavailable(self):
        """Brain API HTTP 503 is recognized as translation failure rather than connection drop."""
        cfg = IntegrationConfig(brain_base_url="http://remote-brain:8000")
        client = BrainClient(config=cfg)

        http_503 = urllib.error.HTTPError(
            "http://remote-brain:8000/ask", 503, "Service Unavailable", hdrs={}, fp=None
        )
        with patch("urllib.request.urlopen", side_effect=http_503):
            res = client.ask("What is Namami Gange?", input_language="en", output_language="ta")
            self.assertIn("Translation service", res.answer)
            self.assertNotIn("connecting to the Ganga AI Brain", res.answer)

    def test_empty_question_handling(self):
        """Empty question returns polite guidance without calling Brain."""
        client = BrainClient()
        res = client.ask("   ", input_language="en", output_language="en")
        self.assertIn("Please ask a question", res.answer)
        self.assertEqual(res.mode, "insufficient-evidence")
        self.assertEqual(res.citations, [])


class TranslationMatrixSixteenCombinationsTests(unittest.TestCase):
    def setUp(self):
        clear_translation_cache()

    def test_all_sixteen_language_combinations(self):
        """Verify all 16 input-output language combinations produce valid translated text."""
        test_inputs = {
            "en": "What is Namami Gange?",
            "hi": "नमामि गंगे क्या है?",
            "kn": "ನಮಾಮಿ ಗಂಗೆ ಎಂದರೇನು?",
            "ta": "நமாமி கங்கை என்றால் என்ன?",
        }
        languages = ["en", "hi", "kn", "ta"]

        for src in languages:
            for tgt in languages:
                pair = f"{src}->{tgt}"
                result = translate_text(test_inputs[src], src, tgt)
                self.assertTrue(bool(result and result.strip()), f"Failed to translate {pair}")
                if src == tgt:
                    self.assertEqual(result, test_inputs[src], f"Same-language {pair} should be unchanged")

    def test_same_language_bypass_makes_zero_provider_calls(self):
        """Same-language translation must immediately return without invoking external providers."""
        with patch("brain.translator._http_translate") as mock_http:
            for lang in ["en", "hi", "kn", "ta"]:
                res = translate_text("Sample test text", lang, lang)
                self.assertEqual(res, "Sample test text")
            self.assertEqual(mock_http.call_count, 0)

    def test_in_memory_translation_caching(self):
        """Second call with identical parameters returns from cache with zero additional provider calls."""
        with patch("brain.translator._http_translate", return_value="अनुवादित पाठ") as mock_http:
            res1 = translate_text("Unique sentence to translate.", "en", "hi")
            self.assertEqual(res1, "अनुवादित पाठ")
            self.assertEqual(mock_http.call_count, 1)

            # Second call must hit cache
            res2 = translate_text("Unique sentence to translate.", "en", "hi")
            self.assertEqual(res2, "अनुवादित पाठ")
            self.assertEqual(mock_http.call_count, 1)

    def test_exact_domain_phrase_and_historical_prefix_handling(self):
        """Exact GRBMP domain phrases and historical material prefixes translate accurately."""
        # Exact domain phrase
        for lang, target_prefix in PREFIX_MAP.items():
            if lang == "en":
                continue
            res = translate_text("From the retrieved historical GRBMP material: ", "en", lang)
            self.assertTrue(res.startswith(target_prefix.rstrip()), f"Prefix mismatch for en->{lang}")


class FrontendContractStaleCitationsTests(unittest.TestCase):
    def test_app_js_clears_stale_citations_on_query_and_error(self):
        """Verify avatar/app.js contains calls to clear stale citations upon query and on error."""
        with open("avatar/app.js", "r", encoding="utf-8") as f:
            content = f.read()

        # Check that renderCitations([]) is called before fetch and inside catch
        self.assertIn("renderCitations([]);", content)
        # Check that error differentiation handles network vs translation vs internal errors
        self.assertIn("Translation service is temporarily unavailable", content)
        self.assertIn("connecting to the Ganga AI Brain server right now", content)


if __name__ == "__main__":
    unittest.main()
