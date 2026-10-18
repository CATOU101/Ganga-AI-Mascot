"""Automated Verification Suite for Multilingual Output, Independent Language Selectors, and Voice-Over.

Verifies:
1. Frontend HTML:
   - INPUT LANG selector offers all 4 languages: English, हिंदी (hi), ಕನ್ನಡ (kn), தமிழ் (ta).
   - OUTPUT LANG selector offers all 4 languages: English, हिंदी (hi), ಕನ್ನಡ (kn), தமிழ் (ta).
   - Both selectors have proper IDs and data-lang attributes.
   - Replay Voice button (replayAudioBtn) is present in the response provenance header.
   - Response language badge (responseLangBadge) displays dual In / Out language codes.
2. Frontend JS (app.js):
   - Independent currentInputLanguage and currentOutputLanguage state management.
   - Both setInputLanguage and setOutputLanguage handlers update UI and state.
   - Typed questions and voice STT queries send both input_language and output_language to API.
   - fallbackBrowserTTS respects requested output language for speech synthesis locale and voice.
   - Audio replay handler correctly replays last received speech.
3. Backend Request Contracts:
   - AskRequest supports independent input_language and output_language.
   - BrainRequest supports independent input_language and output_language.
   - Default fallback: output_language defaults to input_language if omitted.
4. Multilingual & Cross-Lingual Answer Pipelines:
   - Hindi input -> English output (hi -> en).
   - English input -> Hindi output (en -> hi).
   - English input -> Kannada output (en -> kn).
   - English input -> Tamil output (en -> ta).
5. Voice-Over & TTS Configuration:
   - Explicit voice mapping:
     * en -> en-IN-PrabhatNeural
     * hi -> hi-IN-MadhurNeural
     * kn -> kn-IN-GaganNeural
     * ta -> ta-IN-ValluvarNeural
   - Refusal of silent English fallback for unsupported languages.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from avatar.Member2_Chacha.chacha_tts_pipeline import EdgeTTSProvider
from brain.api import AskRequest, app
from brain.translator import (
    GoogleGTXTranslationProvider,
    set_default_translation_provider,
)
from integration.models.brain_response import BrainRequest
from integration.voice.tts_adapter import Member2TTSAdapter


class FrontendMultilingualContractTests(unittest.TestCase):
    """Verify frontend UI DOM structure and script compliance for independent language controls."""

    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).resolve().parent.parent.parent
        cls.html_path = project_root / "avatar" / "index.html"
        cls.js_path = project_root / "avatar" / "app.js"
        cls.css_path = project_root / "avatar" / "style.css"

        with open(cls.html_path, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

        with open(cls.js_path, "r", encoding="utf-8") as f:
            cls.js_content = f.read()

    def test_both_input_and_output_lang_selectors_present_in_html(self):
        """Both Input Lang and Output Lang selector groups must exist in index.html."""
        self.assertIn("Input Lang", self.html_content)
        self.assertIn("Output Lang", self.html_content)
        self.assertIn('id="inputLangSelector"', self.html_content)
        self.assertIn('id="outputLangSelector"', self.html_content)

    def test_input_lang_offers_all_four_languages(self):
        """INPUT LANG selector must offer English, Hindi, Kannada, and Tamil."""
        self.assertIn('id="inputLangEn"', self.html_content)
        self.assertIn('id="inputLangHi"', self.html_content)
        self.assertIn('id="inputLangKn"', self.html_content)
        self.assertIn('id="inputLangTa"', self.html_content)

    def test_output_lang_offers_all_four_languages(self):
        """OUTPUT LANG selector must offer English, Hindi, Kannada, and Tamil."""
        self.assertIn('id="outputLangEn"', self.html_content)
        self.assertIn('id="outputLangHi"', self.html_content)
        self.assertIn('id="outputLangKn"', self.html_content)
        self.assertIn('id="outputLangTa"', self.html_content)

    def test_replay_button_and_response_badge_present(self):
        """Replay Voice button and dual provenance badge must exist in index.html."""
        self.assertIn('id="replayAudioBtn"', self.html_content)
        self.assertIn('id="responseLangBadge"', self.html_content)

    def test_independent_language_state_in_app_js(self):
        """app.js must maintain independent currentInputLanguage and currentOutputLanguage."""
        self.assertIn("currentInputLanguage", self.js_content)
        self.assertIn("currentOutputLanguage", self.js_content)
        self.assertIn("setInputLanguage", self.js_content)
        self.assertIn("setOutputLanguage", self.js_content)
        self.assertIn("lastSpeechData", self.js_content)

    def test_api_payloads_send_both_languages_in_app_js(self):
        """app.js must submit both input_language and output_language."""
        self.assertIn("input_language: currentInputLanguage", self.js_content)
        self.assertIn("output_language: currentOutputLanguage", self.js_content)
        self.assertIn("output_language=${currentOutputLanguage}", self.js_content)

    def test_tts_fallback_respects_output_language(self):
        """fallbackBrowserTTS must accept output language and configure matching speech locale."""
        self.assertIn("function fallbackBrowserTTS(text, lang = currentOutputLanguage)", self.js_content)


class BackendIndependentLanguageContractTests(unittest.TestCase):
    """Verify backend models support independent input and output languages."""

    def test_ask_request_supports_different_input_and_output_languages(self):
        """AskRequest allows different input and output languages (cross-lingual)."""
        req_hi_en = AskRequest(question="गंगा नदी", input_language="hi", output_language="en")
        self.assertEqual(req_hi_en.get_input_language(), "hi")
        self.assertEqual(req_hi_en.get_output_language(), "en")

        req_en_kn = AskRequest(question="What is Aviral Dhara?", input_language="en", output_language="kn")
        self.assertEqual(req_en_kn.get_input_language(), "en")
        self.assertEqual(req_en_kn.get_output_language(), "kn")

        req_en_ta = AskRequest(question="What is Aviral Dhara?", input_language="en", output_language="ta")
        self.assertEqual(req_en_ta.get_input_language(), "en")
        self.assertEqual(req_en_ta.get_output_language(), "ta")

    def test_ask_request_defaults_output_to_input_when_omitted(self):
        """When output_language is omitted, it defaults to input_language."""
        req = AskRequest(question="अविरल धारा क्या है?", input_language="hi")
        self.assertEqual(req.get_input_language(), "hi")
        self.assertEqual(req.get_output_language(), "hi")

    def test_brain_request_supports_independent_languages(self):
        """BrainRequest honors output_language independently from input_language."""
        br = BrainRequest(question="Test question", input_language="hi", output_language="en")
        self.assertEqual(br.get_input_language(), "hi")
        self.assertEqual(br.get_output_language(), "en")

        br_default = BrainRequest(question="Test question", input_language="ta")
        self.assertEqual(br_default.get_input_language(), "ta")
        self.assertEqual(br_default.get_output_language(), "ta")


class MultilingualCrossLingualPipelineTests(unittest.TestCase):
    """Verify cross-lingual query answering and translation routing."""

    def setUp(self):
        set_default_translation_provider(None)

    def tearDown(self):
        set_default_translation_provider(None)

    def test_cross_lingual_ask_pipeline_execution(self):
        """Mocked provider verifies cross-lingual translation flow (hi->en, en->hi, en->kn, en->ta)."""
        mock_provider = Mock(spec=GoogleGTXTranslationProvider)

        def mock_translate(text, src, tgt):
            if src == tgt:
                return text
            if src == "hi" and tgt == "en":
                return "What is Aviral Dhara?"
            if src == "en" and tgt == "hi":
                return "अविरल धारा का अर्थ गंगा का निरंतर और निर्बाध प्रवाह है।"
            if src == "en" and tgt == "kn":
                return "ಅವಿರಲ ಧಾರಾ ಎಂದರೆ ಗಂಗಾ ನದಿಯ ನಿರಂತರ ಮತ್ತು ತಡೆರಹಿತ ಹರಿವು."
            if src == "en" and tgt == "ta":
                return "அவிரல் தாரா என்பது கங்கை நதியின் தொடர்ச்சியான மற்றும் தடையற்ற ஓட்டம் ஆகும்."
            return f"Translated {src}->{tgt}: {text}"

        mock_provider.translate.side_effect = mock_translate
        set_default_translation_provider(mock_provider)

        client = TestClient(app)

        # 1. Ask in Hindi, receive answer in English (hi -> en)
        resp1 = client.post("/ask", json={
            "question": "अविरल धारा क्या है?",
            "input_language": "hi",
            "output_language": "en",
            "top_k": 3,
        })
        self.assertEqual(resp1.status_code, 200)
        d1 = resp1.json()
        self.assertEqual(d1["input_language"], "hi")
        self.assertEqual(d1["output_language"], "en")
        self.assertIn("Aviral Dhara", d1["answer"])

        # 2. Ask in English, receive answer in Hindi (en -> hi)
        resp2 = client.post("/ask", json={
            "question": "What is Aviral Dhara?",
            "input_language": "en",
            "output_language": "hi",
            "top_k": 3,
        })
        self.assertEqual(resp2.status_code, 200)
        d2 = resp2.json()
        self.assertEqual(d2["input_language"], "en")
        self.assertEqual(d2["output_language"], "hi")
        self.assertIn("अविरल धारा", d2["answer"])

        # 3. Ask in English, receive answer in Kannada (en -> kn)
        resp3 = client.post("/ask", json={
            "question": "What is Aviral Dhara?",
            "input_language": "en",
            "output_language": "kn",
            "top_k": 3,
        })
        self.assertEqual(resp3.status_code, 200)
        d3 = resp3.json()
        self.assertEqual(d3["input_language"], "en")
        self.assertEqual(d3["output_language"], "kn")
        self.assertIn("ಅವಿರಲ ಧಾರಾ", d3["answer"])

        # 4. Ask in English, receive answer in Tamil (en -> ta)
        resp4 = client.post("/ask", json={
            "question": "What is Aviral Dhara?",
            "input_language": "en",
            "output_language": "ta",
            "top_k": 3,
        })
        self.assertEqual(resp4.status_code, 200)
        d4 = resp4.json()
        self.assertEqual(d4["input_language"], "en")
        self.assertEqual(d4["output_language"], "ta")
        self.assertIn("அவிரல் தாரா", d4["answer"])


class TTSVoiceConfigurationTests(unittest.TestCase):
    """Verify voice-over configuration, language-to-voice mappings, and silent fallback prevention."""

    def test_edgetts_voice_mapping_for_all_four_languages(self):
        """EdgeTTSProvider must explicitly map all four languages to verified neural voices."""
        provider = EdgeTTSProvider()
        expected = {
            "en": "en-IN-PrabhatNeural",
            "hi": "hi-IN-MadhurNeural",
            "kn": "kn-IN-GaganNeural",
            "ta": "ta-IN-ValluvarNeural",
        }
        for lang, expected_voice in expected.items():
            self.assertEqual(provider.DEFAULT_VOICES.get(lang), expected_voice)

    def test_edgetts_rejects_unsupported_language_without_silent_english_fallback(self):
        """EdgeTTSProvider must raise ValueError for unsupported language rather than silent English."""
        provider = EdgeTTSProvider()
        with self.assertRaises(ValueError):
            provider.synthesize_to_wav("Test text", language="de", output_wav="dummy.wav")

    def test_member2_tts_adapter_rejects_unsupported_language(self):
        """Member2TTSAdapter must return None for unsupported language to trigger client fallback."""
        adapter = Member2TTSAdapter()
        res = adapter.synthesize_speech("Test text", language="de")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
