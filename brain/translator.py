"""Lightweight zero-dependency English <-> Hindi translation module using Python urllib."""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger("brain.translator")


class TranslationError(RuntimeError):
    """Raised when a requested translation cannot be completed."""


def normalize_language(language: str | None, *, default: str) -> str:
    """Normalize and validate the supported English/Hindi language codes."""
    normalized = (language or default).lower().strip()
    if normalized not in {"en", "hi"}:
        raise ValueError(f"Unsupported language code: {language!r}; expected 'en' or 'hi'")
    return normalized


# Pre-defined domain fallback phrases for common GRBMP / RAG messages
DOMAIN_TRANSLATIONS = {
    "en_to_hi": {
        "From the retrieved historical GRBMP material:": "ऐतिहासिक GRBMP सामग्री से प्राप्त जानकारी के अनुसार:",
        "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.": "मेरे ज्ञान आधार में इस प्रश्न का उत्तर देने के लिए पर्याप्त प्रमाण नहीं हैं।",
        "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question.": "वर्तमान प्रोटोटाइप ज्ञान आधार स्थिर/ऐतिहासिक GRBMP सामग्री से बनाया गया है और इस प्रश्न के लिए सत्यापित वर्तमान या रीयल-टाइम जानकारी प्रदान नहीं करता है।",
        "Please ask a question about River Ganga or Namami Gange programs.": "कृपया गंगा नदी या नमामि गंगे कार्यक्रमों के बारे में कोई प्रश्न पूछें।",
        "Please enter a question to ask Chacha Mascot.": "कृपया चाचा शुभंकर से पूछने के लिए कोई प्रश्न दर्ज करें।",
        "Sorry, I'm having trouble connecting right now.": "क्षमा करें, मुझे अभी जुड़ने में परेशानी हो रही है।"
    },
    "hi_to_en": {
        "ऐतिहासिक GRBMP सामग्री से प्राप्त जानकारी के अनुसार:": "From the retrieved historical GRBMP material:",
        "मेरे ज्ञान आधार में इस प्रश्न का उत्तर देने के लिए पर्याप्त प्रमाण नहीं हैं।": "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.",
        "वर्तमान प्रोटोटाइप ज्ञान आधार स्थिर/ऐतिहासिक GRBMP सामग्री से बनाया गया है और इस प्रश्न के लिए सत्यापित वर्तमान या रीयल-टाइम जानकारी प्रदान नहीं करता है।": "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question."
    }
}


def _http_translate(text: str, source_lang: str, target_lang: str) -> str | None:
    """Helper to translate text via Google Translate GTX API using standard urllib."""
    if not text or not text.strip() or source_lang == target_lang:
        return text

    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q="
            + urllib.parse.quote(text)
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data and isinstance(data, list) and len(data) > 0 and data[0]:
                    chunks = [item[0] for item in data[0] if item and isinstance(item, list) and item[0]]
                    res = "".join(chunks).strip()
                    if res:
                        return res
    except Exception as e:
        logger.warning(f"[Translator] HTTP translation failed ({source_lang}->{target_lang}): {e}")

    return None


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text between English and Hindi or raise if translation fails."""
    if not text or not text.strip():
        return text

    src = normalize_language(source_lang, default="en")
    tgt = normalize_language(target_lang, default="en")

    if src == tgt:
        return text

    # Check exact domain phrases first
    domain_map = DOMAIN_TRANSLATIONS.get(f"{src}_to_{tgt}", {})
    if text in domain_map:
        return domain_map[text]

    # Handle historical prefix if present
    prefix_en = "From the retrieved historical GRBMP material: "
    prefix_hi = "ऐतिहासिक GRBMP सामग्री से प्राप्त जानकारी के अनुसार: "

    has_prefix_en = text.startswith(prefix_en)
    has_prefix_hi = text.startswith(prefix_hi)

    core_text = text
    if has_prefix_en:
        core_text = text[len(prefix_en):]
    elif has_prefix_hi:
        core_text = text[len(prefix_hi):]

    translated_core = _http_translate(core_text, src, tgt)
    if not translated_core:
        raise TranslationError(
            f"Translation failed ({src}->{tgt}); returning the untranslated text would be misleading"
        )

    if tgt == "hi":
        prefix = prefix_hi if (has_prefix_en or has_prefix_hi) else ""
        return f"{prefix}{translated_core}"
    else:
        prefix = prefix_en if (has_prefix_en or has_prefix_hi) else ""
        return f"{prefix}{translated_core}"
