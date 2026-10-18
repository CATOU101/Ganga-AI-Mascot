"""Language utilities and controlled external translation."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("brain.translator")

SUPPORTED_LANGUAGES = frozenset({"en", "hi", "kn", "ta"})
DEFAULT_TIMEOUT_SECONDS = 8.0


class TranslationError(RuntimeError):
    """Raised when a requested translation cannot be completed safely."""


class TranslationConsentRequired(TranslationError):
    """Raised when external translation is needed but disabled by the caller."""


def normalize_language(language: str | None, *, default: str = "en") -> str:
    normalized = (language or default).lower().strip()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValueError("Unsupported language code; expected en, hi, kn, or ta")
    return normalized


def detect_language(text: str | None, *, default: str = "en") -> str:
    """Detect supported languages by dominant Unicode script; Latin text defaults to English."""
    if not text or not text.strip():
        return normalize_language(default)
    counts = {"hi": 0, "kn": 0, "ta": 0, "en": 0}
    for char in text:
        point = ord(char)
        if 0x0900 <= point <= 0x097F:
            counts["hi"] += 1
        elif 0x0C80 <= point <= 0x0CFF:
            counts["kn"] += 1
        elif 0x0B80 <= point <= 0x0BFF:
            counts["ta"] += 1
        elif char.isascii() and char.isalpha():
            counts["en"] += 1
    language, count = max(counts.items(), key=lambda item: item[1])
    return language if count else normalize_language(default)


_DOMAIN_TRANSLATIONS = {
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
}


def _external_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Call the public Google GTX endpoint with a bounded timeout and no credentials."""
    query = urllib.parse.urlencode({
        "client": "gtx", "sl": source_lang, "tl": target_lang, "dt": "t", "q": text,
    })
    url = f"https://translate.googleapis.com/translate_a/single?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "Ganga-AI-Mascot/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, list) and data and isinstance(data[0], list):
            translated = "".join(
                item[0] for item in data[0]
                if isinstance(item, list) and item and isinstance(item[0], str)
            ).strip()
            if translated:
                return translated
        raise TranslationError("Translation provider returned an unusable response")
    except TranslationError:
        raise
    except urllib.error.HTTPError as http_err:
        logger.warning("External translation failed: http_status_%s", http_err.code)
        raise TranslationError("External translation is unavailable") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        logger.warning("External translation failed: network_or_timeout")
        raise TranslationError("External translation is unavailable") from None
    except (ValueError, TypeError, KeyError):
        logger.warning("External translation failed: malformed_response")
        raise TranslationError("External translation returned an unusable response") from None
    except Exception:
        logger.warning("External translation failed: provider_error")
        raise TranslationError("External translation is unavailable") from None


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
