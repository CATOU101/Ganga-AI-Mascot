"""Multilingual Translation and End-to-End RAG Verification Suite.

Verifies:
1. Six primary translation directions:
   - English -> Hindi (en -> hi)
   - Hindi -> English (hi -> en)
   - English -> Kannada (en -> kn)
   - Kannada -> English (kn -> en)
   - English -> Tamil (en -> ta)
   - Tamil -> English (ta -> en)
2. Same-language bypass for en, hi, kn, ta.
3. Language normalization and unsupported code rejection.
4. Deterministic Unicode script language detection for hi, kn, ta, en.
5. Explicit user language selection precedence over detection.
6. End-to-end integration across Hindi, Kannada, and Tamil:
   - Input question in Indic script.
   - Recognition/preservation of input language.
   - Translation of Indic query to English working language.
   - Retrieval and answer generation through RAG pipeline.
   - Output translation of English answer to target language.
   - Verification of response structure and language metadata.
7. Simulated input translation failure handling.
8. Simulated output translation failure handling.
9. Prevention of false-success / untranslated response returns.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, Mock, patch

from fastapi.testclient import TestClient

from brain.api import AskRequest, app
from brain.rag_pipeline import answer_question
from brain.translator import (
    DOMAIN_TRANSLATIONS,
    PREFIX_MAP,
    GoogleGTXTranslationProvider,
    TranslationError,
    detect_language,
    normalize_language,
    set_default_translation_provider,
    translate_text,
)


class MultilingualDirectionsTests(unittest.TestCase):
    def setUp(self):
        set_default_translation_provider(None)

    def tearDown(self):
        set_default_translation_provider(None)

    def test_all_six_translation_directions(self):
        """Verify all 6 bidirectional translation directions using mocked provider."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)

        # Dictionary of test phrases and translations
        translations_dict = {
            ("en", "hi"): ("What is Aviral Dhara?", "अविरल धारा क्या है?"),
            ("hi", "en"): ("अविरल धारा क्या है?", "What is Aviral Dhara?"),
            ("en", "kn"): ("What is Aviral Dhara?", "ಅವಿರಲ ಧಾರಾ ಎಂದರೇನು?"),
            ("kn", "en"): ("ಅವಿರಲ ಧಾರಾ ಎಂದರೇನು?", "What is Aviral Dhara?"),
            ("en", "ta"): ("What is Aviral Dhara?", "அவிரல் தாரா என்றால் என்ன?"),
            ("ta", "en"): ("அவிரல் தாரா என்றால் என்ன?", "What is Aviral Dhara?"),
        }

        def fake_translate(text, src, tgt):
            return translations_dict.get((src, tgt), (None, f"Mocked {tgt}"))[1]

        mock_provider.translate.side_effect = fake_translate
        set_default_translation_provider(mock_provider)

        for (src, tgt), (input_text, expected_output) in translations_dict.items():
            with self.subTest(direction=f"{src}->{tgt}"):
                result = translate_text(input_text, src, tgt)
                self.assertEqual(result, expected_output)

    def test_same_language_bypass_all_supported_languages(self):
        """Same-language requests bypass translation provider completely."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        set_default_translation_provider(mock_provider)

        test_cases = [
            ("en", "River Ganga flows into the Bay of Bengal."),
            ("hi", "गंगा नदी बंगाल की खाड़ी में गिरती है।"),
            ("kn", "ಗಂಗಾ ನದಿಯು ಬಂಗಾಳ ಕೊಲ್ಲಿಗೆ ಹರಿಯುತ್ತದೆ."),
            ("ta", "கங்கை நதி வங்காள விரிகுಡாவில் கலக்கிறது."),
        ]
        for lang, phrase in test_cases:
            with self.subTest(lang=lang):
                res = translate_text(phrase, lang, lang)
                self.assertEqual(res, phrase)

        self.assertEqual(mock_provider.translate.call_count, 0)

    def test_language_normalization_and_validation(self):
        """Verify normalization and rejection of invalid codes."""
        self.assertEqual(normalize_language("EN"), "en")
        self.assertEqual(normalize_language(" hi "), "hi")
        self.assertEqual(normalize_language("KN"), "kn")
        self.assertEqual(normalize_language(" ta "), "ta")
        self.assertEqual(normalize_language(None, default="en"), "en")

        with self.assertRaises(ValueError):
            normalize_language("fr")
        with self.assertRaises(ValueError):
            normalize_language("es")
        with self.assertRaises(ValueError):
            normalize_language("de")

    def test_automatic_language_detection(self):
        """Verify deterministic Unicode script language detection."""
        self.assertEqual(detect_language("What are the major pollution sources?"), "en")
        self.assertEqual(detect_language("गंगा नदी की मुख्य प्रदूषण समस्याएं क्या हैं?"), "hi")
        self.assertEqual(detect_language("ಗಂಗಾ ನದಿಯ ಮಾಲಿನ್ಯದ ಮುಖ್ಯ ಮೂಲಗಳು ಯಾವುವು?"), "kn")
        self.assertEqual(detect_language("கங்கை நதியின் முக்கிய மாசு ஆதாரங்கள் யாவை?"), "ta")
        self.assertEqual(detect_language(""), "en")
        self.assertEqual(detect_language("   "), "en")

    def test_explicit_selection_precedence_over_detection(self):
        """Explicit user selection must NOT be overridden by auto-detection."""
        # User explicitly selects English even though query text contains Hindi
        req = AskRequest(question="गंगा नदी", input_language="en", output_language="en")
        self.assertEqual(req.get_input_language(), "en")
        self.assertEqual(req.get_output_language(), "en")

        # User asks without specifying input_language -> auto-detect activates
        req_auto_hi = AskRequest(question="गंगा नदी क्या है?")
        self.assertEqual(req_auto_hi.get_input_language(), "hi")
        self.assertEqual(req_auto_hi.get_output_language(), "hi")

        req_auto_kn = AskRequest(question="ಗಂಗಾ ನದಿ ಯಾವುದು?")
        self.assertEqual(req_auto_kn.get_input_language(), "kn")
        self.assertEqual(req_auto_kn.get_output_language(), "kn")

        req_auto_ta = AskRequest(question="கங்கை நதி எங்கே உள்ளது?")
        self.assertEqual(req_auto_ta.get_input_language(), "ta")
        self.assertEqual(req_auto_ta.get_output_language(), "ta")


class MultilingualEndToEndIntegrationTests(unittest.TestCase):
    def setUp(self):
        set_default_translation_provider(None)

    def tearDown(self):
        set_default_translation_provider(None)

    def test_hindi_end_to_end_pipeline(self):
        """E2E Hindi query -> input translation -> RAG retrieval -> generator -> output translation."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        mock_provider.translate.side_effect = lambda text, src, tgt: (
            "What is the mission of Namami Gange?" if src == "hi" and tgt == "en"
            else ("नमामि गंगे का उद्देश्य गंगा का कायाकल्प है।" if src == "en" and tgt == "hi" else text)
        )
        set_default_translation_provider(mock_provider)

        client = TestClient(app)
        response = client.post("/ask", json={
            "question": "नमामि गंगे का मिशन क्या है?",
            "input_language": "hi",
            "output_language": "hi",
            "top_k": 3,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["input_language"], "hi")
        self.assertEqual(data["output_language"], "hi")
        self.assertIn("नमामि गंगे", data["answer"])
        self.assertIn(data["mode"], ("grounded", "insufficient-evidence", "current-info-fallback"))

    def test_kannada_end_to_end_pipeline(self):
        """E2E Kannada query -> input translation -> RAG retrieval -> generator -> output translation."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        mock_provider.translate.side_effect = lambda text, src, tgt: (
            "What is the mission of Namami Gange?" if src == "kn" and tgt == "en"
            else ("ನಮಾಮಿ ಗಂಗೆಯ ಮಿಷನ್ ಗಂಗಾ ನದಿಯನ್ನು ಪುನರುಜ್ಜೀವನಗೊಳಿಸುವುದಾಗಿದೆ." if src == "en" and tgt == "kn" else text)
        )
        set_default_translation_provider(mock_provider)

        client = TestClient(app)
        response = client.post("/ask", json={
            "question": "ನಮಾಮಿ ಗಂಗೆಯ ಧ್ಯೇಯವೇನು?",
            "input_language": "kn",
            "output_language": "kn",
            "top_k": 3,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["input_language"], "kn")
        self.assertEqual(data["output_language"], "kn")
        self.assertIn("ನಮಾಮಿ ಗಂಗೆಯ", data["answer"])

    def test_tamil_end_to_end_pipeline(self):
        """E2E Tamil query -> input translation -> RAG retrieval -> generator -> output translation."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        mock_provider.translate.side_effect = lambda text, src, tgt: (
            "What is the mission of Namami Gange?" if src == "ta" and tgt == "en"
            else ("நமாமி கங்கையின் நோக்கம் கங்கை நதியை புத்துயிர் பெறுவதாகும்." if src == "en" and tgt == "ta" else text)
        )
        set_default_translation_provider(mock_provider)

        client = TestClient(app)
        response = client.post("/ask", json={
            "question": "நமாமி கங்கையின் நோக்கம் என்ன?",
            "input_language": "ta",
            "output_language": "ta",
            "top_k": 3,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["input_language"], "ta")
        self.assertEqual(data["output_language"], "ta")
        self.assertIn("நமாமி கங்கையின்", data["answer"])

    def test_kannada_input_translation_failure_produces_explicit_503(self):
        """Simulate Kannada input translation failure; assert explicit 503 error."""
        def fail_kn_to_en(text, src, tgt):
            if src == "kn" and tgt == "en":
                raise TranslationError("Kannada translation service connection failed")
            return text

        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        mock_provider.translate.side_effect = fail_kn_to_en
        set_default_translation_provider(mock_provider)

        client = TestClient(app)
        response = client.post("/ask", json={
            "question": "ಗಂಗಾ ನದಿ ಮಾಲಿನ್ಯಕ್ಕೆ ಕಾರಣವೇನು?",
            "input_language": "kn",
            "output_language": "kn",
        })
        self.assertEqual(response.status_code, 503)
        self.assertIn("Requested answer translation is unavailable", response.json()["detail"])

    def test_tamil_output_translation_failure_produces_explicit_503(self):
        """Simulate Tamil output translation failure; assert explicit 503 error."""
        def fail_en_to_ta(text, src, tgt):
            if src == "ta" and tgt == "en":
                return "What are the pollution sources in Ganga?"
            if src == "en" and tgt == "ta":
                raise TranslationError("Tamil provider quota exhausted")
            return text

        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        mock_provider.translate.side_effect = fail_en_to_ta
        set_default_translation_provider(mock_provider)

        client = TestClient(app)
        response = client.post("/ask", json={
            "question": "கங்கை நதியின் முக்கிய மாசு ஆதாரங்கள் யாவை?",
            "input_language": "ta",
        })
        self.assertEqual(response.status_code, 503)
        self.assertIn("Requested answer translation is unavailable", response.json()["detail"])

    def test_no_false_successful_translation_returned(self):
        """Never silently return untranslated English when Indic output translation fails."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)
        mock_provider.translate.side_effect = TranslationError("Network drop")
        set_default_translation_provider(mock_provider)

        # Directly invoking translate_text must raise TranslationError, never return input unchanged
        with self.assertRaises(TranslationError):
            translate_text("A detailed answer about River Ganga basin.", "en", "kn")

        with self.assertRaises(TranslationError):
            translate_text("A detailed answer about River Ganga basin.", "en", "ta")


if __name__ == "__main__":
    unittest.main()
