"""Language utilities and controlled external translation."""

from __future__ import annotations

import json
import logging
import html
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Literal

logger = logging.getLogger("brain.translator")

LANGUAGE_NAMES = {
    "en": "English", "hi": "Hindi", "kn": "Kannada", "ta": "Tamil",
    "te": "Telugu", "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati",
    "ml": "Malayalam", "pa": "Punjabi", "ur": "Urdu", "or": "Odia",
    "as": "Assamese",
}
SUPPORTED_LANGUAGES = frozenset(LANGUAGE_NAMES)
LanguageCode = Literal["en", "hi", "kn", "ta", "te", "bn", "mr", "gu", "ml", "pa", "ur", "or", "as"]
SPEECH_LOCALES = {
    "en": "en-IN", "hi": "hi-IN", "kn": "kn-IN", "ta": "ta-IN",
    "te": "te-IN", "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN",
    "ml": "ml-IN", "pa": "pa-IN", "ur": "ur-IN", "or": "or-IN",
    "as": "as-IN",
}
DEFAULT_TIMEOUT_SECONDS = 8.0


class TranslationError(RuntimeError):
    """Raised when a requested translation cannot be completed safely."""


class TranslationConsentRequired(TranslationError):
    """Raised when external translation is needed but disabled by the caller."""


def normalize_language(language: str | None, *, default: str = "en") -> str:
    normalized = (language or default).lower().strip()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValueError("Unsupported language code; expected one of: " + ", ".join(sorted(SUPPORTED_LANGUAGES)))
    return normalized


ROMANIZED_HINDI_CUES = frozenset({
    "kahan", "kaha", "kahaa", "kidhar", "kya", "kaun", "kon", "kaise", "kyun", "kyu",
    "kitna", "kitni", "kitne", "hai", "hain", "ho", "hogi", "hoga", "nadi", "nahin", "nahi",
    "pani", "paani", "safai", "pradushan", "shuru", "hoti", "hota", "hote", "nikalti", "nikalta", "nikalte",
    "aati", "aata", "aate", "batao", "bataiye", "bolo", "karo", "kijiye", "mujhe", "mera", "meri", "mere",
    "aap", "aapka", "aapki", "hum", "hume", "ka", "ki", "ke", "ko", "se", "me", "mein", "par",
})


def detect_language(text: str | None, *, default: str = "en") -> str:
    """Detect supported languages from script plus small disambiguating word cues.

    Hindi/Marathi share Devanagari and Bengali/Assamese share a script, so short
    ambiguous text cannot always be identified perfectly without a language-ID
    model. Their common distinct words and characters are used when present.
    """
    if not text or not text.strip():
        return normalize_language(default)
    counts = {language: 0 for language in SUPPORTED_LANGUAGES}
    for char in text:
        point = ord(char)
        if 0x0900 <= point <= 0x097F:
            counts["hi"] += 1  # Hindi/Marathi share Devanagari.
            counts["mr"] += 1
        elif 0x0C00 <= point <= 0x0C7F:
            counts["te"] += 1
        elif 0x0C80 <= point <= 0x0CFF:
            counts["kn"] += 1
        elif 0x0B80 <= point <= 0x0BFF:
            counts["ta"] += 1
        elif 0x0980 <= point <= 0x09FF:
            counts["bn"] += 1  # Bengali and Assamese share this block.
            counts["as"] += 1
        elif 0x0A80 <= point <= 0x0AFF:
            counts["gu"] += 1
        elif 0x0D00 <= point <= 0x0D7F:
            counts["ml"] += 1
        elif 0x0A00 <= point <= 0x0A7F:
            counts["pa"] += 1
        elif 0x0B00 <= point <= 0x0B7F:
            counts["or"] += 1
        elif 0x0600 <= point <= 0x06FF:
            counts["ur"] += 1
        elif char.isascii() and char.isalpha():
            counts["en"] += 1

    if counts["hi"] or counts["mr"]:
        words = set(re.findall(r"[\u0900-\u097f]+", text.casefold()))
        marathi_cues = {"आहे", "आहेत", "आणि", "मला", "माझे", "माझ्या", "तुम्ही", "मी", "काय", "नाही"}
        hindi_cues = {"है", "हैं", "और", "मुझे", "मेरा", "मेरी", "आप", "मैं", "क्या", "नहीं"}
        if words & marathi_cues and not words & hindi_cues:
            return "mr"
        return "hi"
    if counts["bn"] or counts["as"]:
        if any(char in text for char in "ৰৱ৹৺"):
            return "as"
        return "bn"

    # Check for Romanized Indic / Hinglish phrasing in ASCII questions
    if counts["en"] > 0 and not any(counts[code] > 0 for code in SUPPORTED_LANGUAGES if code != "en"):
        ascii_tokens = set(re.findall(r"[a-zA-Z]+", text.casefold()))
        matched_cues = ascii_tokens & ROMANIZED_HINDI_CUES
        if len(matched_cues) >= 2 or (len(matched_cues) == 1 and any(cue in matched_cues for cue in ("kahan", "kaha", "nikalti", "kitni", "pradushan", "batao", "bataiye"))):
            return "hi"

    language, count = max(counts.items(), key=lambda item: item[1])
    return language if count else normalize_language(default)


_DOMAIN_TRANSLATIONS = {
    ("hi", "en", "अविरल धारा क्या है?"): "What is Aviral Dhara?",
    ("hi", "en", "अविरल धारा क्या है"): "What is Aviral Dhara?",
    ("hi", "en", "अविरल धारा"): "Aviral Dhara",
    ("hi", "en", "निर्मल धारा क्या है?"): "What is Nirmal Dhara?",
    ("hi", "en", "निर्मल धारा"): "Nirmal Dhara",
    ("en", "hi", "From the retrieved historical GRBMP material:"): "ऐतिहासिक GRBMP सामग्री से प्राप्त जानकारी के अनुसार:",
    ("en", "kn", "From the retrieved historical GRBMP material:"): "ಹಿಂಪಡೆಯಲಾದ ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯದ ಪ್ರಕಾರ:",
    ("en", "ta", "From the retrieved historical GRBMP material:"): "மீட்டெடுக்கப்பட்ட வரலாற்று GRBMP தரவுகளின்படி:",
    ("en", "hi", "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably."): "मेरे ज्ञान आधार में इस प्रश्न का उत्तर देने के लिए पर्याप्त प्रमाण नहीं हैं।",
    ("en", "kn", "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably."): "ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ಉತ್ತರಿಸಲು ಪ್ರಸ್ತುತ ಪರಿಶೀಲಿಸಿದ ಜ್ಞಾನದ ಮೂಲದಲ್ಲಿ ಸಾಕಷ್ಟು ಪೂರಕ ಮಾಹಿತಿಯನ್ನು ಕಂಡುಹಿಡಿಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.",
    ("en", "ta", "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably."): "நம்பகமாக பதிலளிக்க சரிபார்க்கப்பட்ட அறிவுத் தளத்தில் போதுமான ஆதாரம் இல்லை.",
    ("en", "hi", "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question."): "वर्तमान प्रोटोटाइप ज्ञान आधार स्थिर/ऐतिहासिक GRBMP सामग्री से बनाया गया है और उस प्रश्न के लिए सत्यापित वर्तमान या रीयल-टाइम जानकारी प्रदान नहीं करता है।",
    ("en", "kn", "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question."): "ಪ್ರಸ್ತುತ ಮಾದರಿ ಜ್ಞಾನಸಂಗ್ರಹವು ಸ್ಥಿರ/ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯವನ್ನು ಆಧರಿಸಿದೆ ಮತ್ತು ಆ ಪ್ರಶ್ನೆಗೆ ಪರಿಶೀಲಿತ ಪ್ರಸ್ತುತ ಅಥವಾ ನೈಜ-ಸಮಯದ ಮಾಹಿತಿಯನ್ನು ಒದಗಿಸುವುದಿಲ್ಲ.",
    ("en", "ta", "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question."): "தற்போதைய முன்மாதிரி அறிவுத் தளம் நிலையான/வரலாற்று GRBMP உள்ளடக்கத்தை அடிப்படையாகக் கொண்டது; அந்தக் கேள்விக்கான சரிபார்க்கப்பட்ட தற்போதைய அல்லது நிகழ்நேரத் தகவலை வழங்காது.",
}
_PREFIXES = {
    "en": "From the retrieved historical GRBMP material: ",
    "hi": "ऐतिहासिक GRBMP सामग्री से प्राप्त जानकारी के अनुसार: ",
    "kn": "ಹಿಂಪಡೆಯಲಾದ ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯದ ಪ್ರಕಾರ: ",
    "ta": "மீட்டெடுக்கப்பட்ட வரலாற்று GRBMP தரவுகளின்படி: ",
    "te": "సేకరించిన చారిత్రక GRBMP సమాచారం ప్రకారం: ",
    "bn": "উদ্ধার করা ঐতিহাসিক GRBMP তথ্য অনুযায়ী: ",
    "mr": "मिळवलेल्या ऐतिहासिक GRBMP माहितीनुसार: ",
    "gu": "મેળવેલી ઐતિહાસિક GRBMP માહિતી અનુસાર: ",
    "ml": "ലഭിച്ച ചരിത്രപരമായ GRBMP വിവരങ്ങൾ പ്രകാരം: ",
    "pa": "ਪ੍ਰਾਪਤ ਇਤਿਹਾਸਕ GRBMP ਜਾਣਕਾਰੀ ਅਨੁਸਾਰ: ",
    "ur": "حاصل شدہ تاریخی GRBMP معلومات کے مطابق: ",
    "or": "ପ୍ରାପ୍ତ ଐତିହାସିକ GRBMP ସୂଚନା ଅନୁଯାୟୀ: ",
    "as": "উদ্ধাৰ কৰা ঐতিহাসিক GRBMP তথ্য অনুসৰি: ",
}


def _external_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Use official Cloud Translation when configured, else legacy public GTX."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    cloud_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "").strip()
    if cloud_key:
        url = "https://translation.googleapis.com/language/translate/v2"
        payload = json.dumps({"q": [text], "source": source_lang, "target": target_lang, "format": "text"}).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json", "User-Agent": "Ganga-AI-Mascot/1.0",
            "X-Goog-Api-Key": cloud_key,
        })
        try:
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS, context=ssl_context) as response:
                data = json.loads(response.read().decode("utf-8"))
            translated = data["data"]["translations"][0]["translatedText"]
            if isinstance(translated, str) and translated.strip():
                return html.unescape(translated).strip()
            raise TranslationError("Translation provider returned an unusable response")
        except TranslationError:
            raise
        except urllib.error.HTTPError as http_err:
            logger.warning("Cloud translation failed: http_status_%s", http_err.code)
            raise TranslationError("External translation is unavailable") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            logger.warning("Cloud translation failed: network_or_timeout")
            raise TranslationError("External translation is unavailable") from None
        except (ValueError, TypeError, KeyError, IndexError):
            logger.warning("Cloud translation failed: malformed_response")
            raise TranslationError("External translation returned an unusable response") from None

    # Compatibility path for existing installations without a Cloud key.
    # Try dict-chrome-ex client first (more resilient against 429), then fall back to gtx.
    for client in ("dict-chrome-ex", "gtx"):
        query = urllib.parse.urlencode({
            "client": client, "sl": source_lang, "tl": target_lang, "dt": "t", "q": text,
        })
        url = f"https://translate.googleapis.com/translate_a/single?{query}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
        )
        try:
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS, context=ssl_context) as response:
                data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and data and isinstance(data[0], list):
                translated = "".join(
                    item[0] for item in data[0]
                    if isinstance(item, list) and item and isinstance(item[0], str)
                ).strip()
                if translated:
                    return translated
        except urllib.error.HTTPError as http_err:
            logger.warning("External translation (%s) failed: http_status_%s", client, http_err.code)
            continue
        except (urllib.error.URLError, TimeoutError, OSError):
            logger.warning("External translation (%s) failed: network_or_timeout", client)
            continue
        except (ValueError, TypeError, KeyError):
            logger.warning("External translation (%s) failed: malformed_response", client)
            continue
        except Exception:
            logger.warning("External translation (%s) failed: provider_error", client)
            continue

    raise TranslationError("External translation is unavailable")


def _http_translate(
    text: str,
    source_lang: str,
    target_lang: str,
    *,
    allow_external: bool = False,
    provider=None,
) -> str | None:
    """Compatibility wrapper; callers must enable external translation."""
    if not allow_external:
        raise TranslationConsentRequired("External translation is disabled for this request")
    if provider is not None:
        try:
            return provider.translate(text, source_lang, target_lang)
        except TranslationError:
            raise
        except Exception:
            logger.warning("External translation failed: provider_error")
            raise TranslationError("External translation is unavailable") from None
    return _external_translate(text, source_lang, target_lang)


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    *,
    allow_external: bool = False,
    provider=None,
) -> str:
    """Translate text, using the external provider only when enabled by the caller.

    Exact domain phrases are translated locally. General translation sends the full
    text to Google Translate GTX only when ``allow_external`` is true. API routes
    allow it by default; direct callers can disable it. No text cache is retained.
    """
    if not text or not text.strip():
        return text
    src = normalize_language(source_lang)
    tgt = normalize_language(target_lang)
    if src == tgt:
        return text
    if (src, tgt, text) in _DOMAIN_TRANSLATIONS:
        return _DOMAIN_TRANSLATIONS[(src, tgt, text)]

    has_prefix = text.startswith(_PREFIXES[src])
    core = text[len(_PREFIXES[src]):] if has_prefix else text
    try:
        translated = _http_translate(
            core, src, tgt, allow_external=allow_external, provider=provider,
        )
    except TranslationError:
        raise
    except Exception:
        logger.warning("External translation failed: provider_error")
        raise TranslationError("External translation is unavailable") from None
    if not isinstance(translated, str) or not translated.strip():
        logger.warning("External translation failed: empty_response")
        raise TranslationError("External translation returned an unusable response")
    prefix = _PREFIXES[tgt] if has_prefix else ""
    return prefix + translated.strip()
