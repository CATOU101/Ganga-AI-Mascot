"""Automated Translation Reliability Test Suite.

Verifies:
1. Successful translation.
2. HTTP 429 followed by successful translation.
3. Persistent HTTP 429 exhausting retry limit.
4. Numeric Retry-After header handling.
5. HTTP-date Retry-After header handling.
6. Request timeout followed by recovery.
7. Persistent timeout exhausting retries.
8. Authentication failure (HTTP 401/403) not retried.
9. Other non-retryable HTTP errors (HTTP 400/404) not retried.
10. Retryable server errors (HTTP 5xx).
11. Network connection errors.
12. Malformed JSON / invalid response structure.
13. Empty provider response.
14. Input translation failure explicitly propagated.
15. Output translation failure explicitly propagated.
16. API endpoint propagation of TranslationError to HTTP 503.
17. Bounded total waiting time / no unbounded sleeps.
18. Same-language bypass (0 provider calls).
19. Exact domain-phrase translation without external calls.
20. Historical-prefix preservation and translation.
21. Sanitized logging (no secret API keys leaked in logs).
"""

from __future__ import annotations

import io
import json
import logging
import unittest
import urllib.error
import urllib.response
from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient

from brain.api import app
from brain.rag_pipeline import answer_question
from brain.translator import (
    DOMAIN_TRANSLATIONS,
    PREFIX_MAP,
    GoogleCloudTranslationProvider,
    GoogleGTXTranslationProvider,
    RetryConfig,
    TranslationError,
    _http_translate,
    detect_language,
    get_translation_provider,
    normalize_language,
    parse_retry_after,
    set_default_translation_provider,
    translate_text,
)


class MockHttpResponse:
    def __init__(self, body_bytes: bytes, status: int = 200, headers: dict | None = None):
        self._body = body_bytes
        self.status = status
        self.headers = headers or {}

    def read(self, *args, **kwargs) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def make_mock_http_response(body_bytes: bytes, status: int = 200, headers: dict | None = None):
    return MockHttpResponse(body_bytes, status=status, headers=headers)


class TranslationReliabilityTests(unittest.TestCase):
    def setUp(self):
        set_default_translation_provider(None)

    def tearDown(self):
        set_default_translation_provider(None)

    def test_01_successful_translation_gtx(self):
        """Test standard successful translation via Google GTX."""
        body = json.dumps([[["River Ganga is holy.", "गंगा नदी पवित्र है."]]]).encode("utf-8")
        mock_resp = make_mock_http_response(body, status=200)

        with patch("brain.translator.urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            result = translate_text("गंगा नदी पवित्र है.", "hi", "en")
            self.assertEqual(result, "River Ganga is holy.")
            self.assertEqual(mock_urlopen.call_count, 1)

    def test_02_http_429_followed_by_success(self):
        """HTTP 429 on first attempt, followed by successful response on second attempt."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=2.0,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)

        http_429 = urllib.error.HTTPError(
            "http://gtx", 429, "Too Many Requests", hdrs={"Retry-After": "1.5"}, fp=None
        )
        body = json.dumps([[["Ganga River", "गंगा नदी"]]]).encode("utf-8")
        success_resp = make_mock_http_response(body, status=200)

        with patch("brain.translator.urllib.request.urlopen", side_effect=[http_429, success_resp]) as mock_urlopen:
            res = provider.translate("गंगा नदी", "hi", "en")
            self.assertEqual(res, "Ganga River")
            self.assertEqual(mock_urlopen.call_count, 2)
            self.assertEqual(len(sleep_calls), 1)
            self.assertEqual(sleep_calls[0], 1.5)

    def test_03_persistent_http_429_exhausts_retries(self):
        """Persistent HTTP 429 exhausts retries and raises TranslationError."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=2,
            initial_delay=0.05,
            backoff_factor=2.0,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)

        http_429 = urllib.error.HTTPError(
            "http://gtx", 429, "Too Many Requests", hdrs=None, fp=None
        )

        with patch("brain.translator.urllib.request.urlopen", side_effect=http_429) as mock_urlopen:
            with self.assertLogs("brain.translator", level="WARNING") as captured:
                with self.assertRaises(TranslationError):
                    provider.translate("गंगा नदी", "hi", "en")

            # 1 initial attempt + 2 retries = 3 attempts total
            self.assertEqual(mock_urlopen.call_count, 3)
            self.assertEqual(len(sleep_calls), 2)
            self.assertTrue(any("429" in msg for msg in captured.output))

    def test_04_numeric_retry_after_header_handling(self):
        """Numeric Retry-After header is correctly parsed and capped."""
        self.assertEqual(parse_retry_after("5"), 5.0)
        self.assertEqual(parse_retry_after("12.5"), 12.5)
        self.assertEqual(parse_retry_after("60", max_delay=10.0), 10.0)
        self.assertIsNone(parse_retry_after(None))
        self.assertIsNone(parse_retry_after(""))

    def test_05_http_date_retry_after_handling(self):
        """HTTP-date format in Retry-After header is parsed into future seconds."""
        # Date 10 seconds in the future
        future_dt_str = "Wed, 21 Oct 2099 07:28:00 GMT"
        parsed = parse_retry_after(future_dt_str, max_delay=15.0)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed, 15.0)  # Capped at max_delay

    def test_06_request_timeout_followed_by_recovery(self):
        """Timeout on first request followed by successful retry."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=2,
            initial_delay=0.1,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)

        timeout_err = TimeoutError("Request timed out")
        body = json.dumps([[["Clean Ganga", "स्वच्छ गंगा"]]]).encode("utf-8")
        success_resp = make_mock_http_response(body, status=200)

        with patch("brain.translator.urllib.request.urlopen", side_effect=[timeout_err, success_resp]) as mock_urlopen:
            res = provider.translate("स्वच्छ गंगा", "hi", "en")
            self.assertEqual(res, "Clean Ganga")
            self.assertEqual(mock_urlopen.call_count, 2)
            self.assertEqual(len(sleep_calls), 1)

    def test_07_persistent_timeout_exhausts_retries(self):
        """Persistent timeouts exhaust retries and raise TranslationError."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=2,
            initial_delay=0.05,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)

        with patch("brain.translator.urllib.request.urlopen", side_effect=TimeoutError("Socket timeout")):
            with self.assertRaises(TranslationError) as ctx:
                provider.translate("स्वच्छ गंगा", "hi", "en")
            self.assertIn("network failure", str(ctx.exception).lower())
            self.assertEqual(len(sleep_calls), 2)

    def test_08_authentication_failure_not_retried(self):
        """HTTP 401/403 authentication error fails immediately without retrying."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=3,
            initial_delay=0.1,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleCloudTranslationProvider(
            api_key="mock-key",
            retry_config=retry_cfg,
        )

        http_401 = urllib.error.HTTPError(
            "http://gcp", 401, "Unauthorized", hdrs=None, fp=None
        )

        with patch("brain.translator.urllib.request.urlopen", side_effect=http_401) as mock_urlopen:
            with self.assertRaises(TranslationError) as ctx:
                provider.translate("Ganga", "en", "hi")
            self.assertIn("401", str(ctx.exception))
            # Exactly 1 call: NO retries on auth failure!
            self.assertEqual(mock_urlopen.call_count, 1)
            self.assertEqual(len(sleep_calls), 0)

    def test_09_other_non_retryable_http_errors_not_retried(self):
        """HTTP 400 (Bad Request) fails immediately without retrying."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=3,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)

        http_400 = urllib.error.HTTPError(
            "http://gtx", 400, "Bad Request", hdrs=None, fp=None
        )

        with patch("brain.translator.urllib.request.urlopen", side_effect=http_400) as mock_urlopen:
            with self.assertRaises(TranslationError) as ctx:
                provider.translate("Test", "en", "hi")
            self.assertIn("400", str(ctx.exception))
            self.assertEqual(mock_urlopen.call_count, 1)
            self.assertEqual(len(sleep_calls), 0)

    def test_10_retryable_server_errors_5xx(self):
        """HTTP 503 is retried and succeeds on recovery."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=2,
            initial_delay=0.1,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)

        http_503 = urllib.error.HTTPError(
            "http://gtx", 503, "Service Unavailable", hdrs=None, fp=None
        )
        body = json.dumps([[["Recovered answer", "उत्तर"]]]).encode("utf-8")
        success_resp = make_mock_http_response(body, status=200)

        with patch("brain.translator.urllib.request.urlopen", side_effect=[http_503, success_resp]) as mock_urlopen:
            res = provider.translate("उत्तर", "hi", "en")
            self.assertEqual(res, "Recovered answer")
            self.assertEqual(mock_urlopen.call_count, 2)
            self.assertEqual(len(sleep_calls), 1)

    def test_11_network_connection_errors_retry(self):
        """URLError network connection failure retries and succeeds."""
        sleep_calls = []
        retry_cfg = RetryConfig(
            max_retries=2,
            initial_delay=0.1,
            sleep_fn=lambda s: sleep_calls.append(s),
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)

        net_err = urllib.error.URLError("Connection refused")
        body = json.dumps([[["Success", "सफलता"]]]).encode("utf-8")
        success_resp = make_mock_http_response(body, status=200)

        with patch("brain.translator.urllib.request.urlopen", side_effect=[net_err, success_resp]) as mock_urlopen:
            res = provider.translate("सफलता", "hi", "en")
            self.assertEqual(res, "Success")
            self.assertEqual(mock_urlopen.call_count, 2)
            self.assertEqual(len(sleep_calls), 1)

    def test_12_malformed_json_response(self):
        """Malformed JSON from provider raises TranslationError."""
        provider = GoogleGTXTranslationProvider()
        mock_resp = make_mock_http_response(b"not-json-content", status=200)

        with patch("brain.translator.urllib.request.urlopen", return_value=mock_resp):
            with self.assertRaises(TranslationError) as ctx:
                provider.translate("Hello", "en", "hi")
            self.assertIn("malformed", str(ctx.exception).lower())

    def test_13_empty_provider_response(self):
        """Empty or unexpected response structure raises TranslationError."""
        provider = GoogleGTXTranslationProvider()
        mock_resp = make_mock_http_response(b"[]", status=200)

        with patch("brain.translator.urllib.request.urlopen", return_value=mock_resp):
            with self.assertRaises(TranslationError) as ctx:
                provider.translate("Hello", "en", "hi")
            self.assertIn("unexpected response structure", str(ctx.exception).lower())

    def test_14_input_translation_failure_in_pipeline(self):
        """Input translation failure in answer_question raises TranslationError."""
        with patch("brain.rag_pipeline.translate_text", side_effect=TranslationError("Provider down")):
            with self.assertRaises(TranslationError):
                answer_question("ಗಂಗಾ ನದಿ ಎಂದರೇನು?", input_language="kn", output_language="en")

    def test_15_output_translation_failure_in_pipeline(self):
        """Output translation failure in answer_question raises TranslationError."""
        def fake_translate(text, src, tgt):
            if src == "en" and tgt == "ta":
                raise TranslationError("Tamil output translation failed")
            return text

        with patch("brain.rag_pipeline.translate_text", side_effect=fake_translate):
            with self.assertRaises(TranslationError) as ctx:
                answer_question("What is Aviral Dhara?", input_language="en", output_language="ta")
            self.assertIn("Tamil output translation failed", str(ctx.exception))

    def test_16_propagation_of_translation_error_in_api(self):
        """Brain API POST /ask converts TranslationError into HTTP 503."""
        client = TestClient(app)
        with patch("brain.api.answer_question", side_effect=TranslationError("Translation service unavailable")):
            resp = client.post("/ask", json={"question": "What is Ganga?", "output_language": "hi"})
            self.assertEqual(resp.status_code, 503)
            self.assertIn("Requested answer translation is unavailable", resp.json()["detail"])

    def test_17_no_unbounded_sleeps_and_total_waiting_time_capped(self):
        """Retry loops stop if cumulative delay exceeds max_total_time."""
        # Simulated clock that advances with sleep
        current_clock = [0.0]
        def fake_sleep(s):
            current_clock[0] += s
        def fake_time():
            return current_clock[0]

        retry_cfg = RetryConfig(
            max_retries=10,
            initial_delay=5.0,
            backoff_factor=2.0,
            max_delay=20.0,
            max_total_time=12.0,  # Cap at 12s
            sleep_fn=fake_sleep,
            time_fn=fake_time,
        )
        provider = GoogleGTXTranslationProvider(retry_config=retry_cfg)
        http_429 = urllib.error.HTTPError("http://gtx", 429, "Too Many Requests", hdrs=None, fp=None)

        with patch("brain.translator.urllib.request.urlopen", side_effect=http_429) as mock_urlopen:
            with self.assertRaises(TranslationError) as ctx:
                provider.translate("Test text", "en", "hi")
            self.assertIn("total waiting time exceeded", str(ctx.exception).lower())
            # Should have stopped after ~2 retries due to total time limit
            self.assertLess(mock_urlopen.call_count, 6)

    def test_18_same_language_bypass(self):
        """Same-language requests bypass translation provider completely for all supported languages."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        set_default_translation_provider(mock_provider)

        for lang in ("en", "hi", "kn", "ta"):
            text = f"Sample text in {lang}"
            res = translate_text(text, lang, lang)
            self.assertEqual(res, text)

        # Assert ZERO provider calls were made across all 4 languages
        self.assertEqual(mock_provider.translate.call_count, 0)

    def test_19_exact_domain_phrase_translation(self):
        """Exact GRBMP domain phrases are translated via verified mappings without provider calls."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        set_default_translation_provider(mock_provider)

        # English to Hindi
        res_hi = translate_text(
            "Please ask a question about River Ganga or Namami Gange programs.",
            "en",
            "hi",
        )
        self.assertEqual(res_hi, "कृपया गंगा नदी या नमामि गंगे कार्यक्रमों के बारे में कोई प्रश्न पूछें।")

        # English to Kannada
        res_kn = translate_text(
            "Please ask a question about River Ganga or Namami Gange programs.",
            "en",
            "kn",
        )
        self.assertEqual(res_kn, "ದಯವಿಟ್ಟು ಗಂಗಾ ನದಿ ಅಥವಾ ನಮಾಮಿ ಗಂಗೆ ಕಾರ್ಯಕ್ರಮಗಳ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ.")

        # English to Tamil
        res_ta = translate_text(
            "Please ask a question about River Ganga or Namami Gange programs.",
            "en",
            "ta",
        )
        self.assertEqual(res_ta, "தயவுசெய்து கங்கை நதி அல்லது நமாமி கங்கை திட்டங்கள் குறித்த கேள்வியைக் கேளுங்கள்.")

        # Verify zero external provider calls occurred
        self.assertEqual(mock_provider.translate.call_count, 0)

    def test_20_historical_prefix_handling(self):
        """Historical material prefixes are recognized, stripped, and attached in target language."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        mock_provider.translate.return_value = "ಅಧ್ಯಯನವು ಮಾಲಿನ್ಯವನ್ನು ತೋರಿಸುತ್ತದೆ."
        set_default_translation_provider(mock_provider)

        input_text = "From the retrieved historical GRBMP material: The study shows pollution."
        result = translate_text(input_text, "en", "kn")

        expected_prefix = PREFIX_MAP["kn"]
        self.assertTrue(result.startswith(expected_prefix))
        self.assertIn("ಅಧ್ಯಯನವು ಮಾಲಿನ್ಯವನ್ನು ತೋರಿಸುತ್ತದೆ.", result)
        # Verify provider was passed core text without prefix
        mock_provider.translate.assert_called_once_with("The study shows pollution.", "en", "kn")

    def test_21_credentials_not_exposed_in_logs(self):
        """Secret API keys must NEVER be logged even when HTTP requests fail."""
        secret_key = "super-secret-gcp-key-12345"
        provider = GoogleCloudTranslationProvider(
            api_key=secret_key,
            retry_config=RetryConfig(max_retries=1, initial_delay=0.01),
        )

        http_err = urllib.error.HTTPError(
            f"https://translation.googleapis.com/v2?key={secret_key}",
            403,
            "Forbidden",
            hdrs=None,
            fp=None,
        )

        with patch("brain.translator.urllib.request.urlopen", side_effect=http_err):
            with self.assertLogs("brain.translator", level="WARNING") as captured:
                with self.assertRaises(TranslationError):
                    provider.translate("Ganga", "en", "hi")

            log_output = "\n".join(captured.output)
            self.assertNotIn(secret_key, log_output)
            self.assertIn("403", log_output)


if __name__ == "__main__":
    unittest.main()
