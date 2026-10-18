"""Production translation module for Ganga AI Mascot supporting en, hi, kn, and ta.

Features:
- Official Google Cloud Translation API provider (primary production candidate).
- Google Translate GTX endpoint provider (zero-dependency fallback/development mode).
- Bounded retry strategy with exponential backoff and jitter for transient errors (HTTP 429, 5xx, timeouts).
- Proper inspection and honoring of HTTP 'Retry-After' header (numeric seconds and HTTP dates).
- Language detection distinguishing Hindi, Kannada, Tamil, and English via Unicode script analysis.
- Exact domain phrase translations for GRBMP and RAG system messages across all supported languages.
- Safe historical prefix handling and same-language bypass.
- Comprehensive sanitized logging preventing API credential leakage.
"""

from __future__ import annotations

import email.utils
import html
import json
import logging
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger("brain.translator")

SUPPORTED_LANGUAGES = frozenset({"en", "hi", "kn", "ta"})
DEFAULT_TIMEOUT_SECONDS = 8.0


class TranslationError(RuntimeError):
    """Raised when a requested translation cannot be completed."""


def normalize_language(language: str | None, *, default: str = "en") -> str:
    """Normalize and validate supported language codes ('en', 'hi', 'kn', 'ta')."""
    normalized = (language or default).lower().strip()
    if normalized not in SUPPORTED_LANGUAGES:
        allowed = ", ".join(f"'{l}'" for l in sorted(SUPPORTED_LANGUAGES))
        raise ValueError(f"Unsupported language code: {language!r}; expected one of {allowed}")
    return normalized


def detect_language(text: str | None, *, default: str = "en") -> str:
    """Detect language among 'hi', 'kn', 'ta', 'en' using deterministic Unicode script analysis.
    
    Returns the detected language code or `default` if inconclusive.
    """
    if not text or not text.strip():
        return normalize_language(default)

    hi_count = 0
    kn_count = 0
    ta_count = 0
    latin_count = 0

    for char in text:
        cp = ord(char)
        if 0x0900 <= cp <= 0x097F:
            hi_count += 1
        elif 0x0C80 <= cp <= 0x0CFF:
            kn_count += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            ta_count += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            latin_count += 1

    counts = [("hi", hi_count), ("kn", kn_count), ("ta", ta_count), ("en", latin_count)]
    best_lang, best_count = max(counts, key=lambda x: x[1])

    if best_count > 0:
        return best_lang
    return normalize_language(default)


# Standard historical material prefixes across supported languages
PREFIX_MAP: dict[str, str] = {
    "en": "From the retrieved historical GRBMP material: ",
    "hi": "ऐतिहासिक GRBMP सामग्री से प्राप्त जानकारी के अनुसार: ",
    "kn": "ಹಿಂಪಡೆಯಲಾದ ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯದ ಪ್ರಕಾರ: ",
    "ta": "மீட்டெடுக்கப்பட்ட வரலாற்று GRBMP தரவுகளின்படி: ",
}


# Pre-defined domain fallback phrases for common GRBMP / RAG messages
DOMAIN_TRANSLATIONS: dict[str, dict[str, str]] = {
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
        "वर्तमान प्रोटोटाइप ज्ञान आधार स्थिर/ऐतिहासिक GRBMP सामग्री से बनाया गया है और इस प्रश्न के लिए सत्यापित वर्तमान या रीयल-टाइम जानकारी प्रदान नहीं करता है।": "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question.",
        "कृपया गंगा नदी या नमामि गंगे कार्यक्रमों के बारे में कोई प्रश्न पूछें।": "Please ask a question about River Ganga or Namami Gange programs.",
        "कृपया चाचा शुभंकर से पूछने के लिए कोई प्रश्न दर्ज करें।": "Please enter a question to ask Chacha Mascot.",
        "क्षमा करें, मुझे अभी जुड़ने में परेशानी हो रही है।": "Sorry, I'm having trouble connecting right now."
    },
    "en_to_kn": {
        "From the retrieved historical GRBMP material:": "ಹಿಂಪಡೆಯಲಾದ ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯದ ಪ್ರಕಾರ:",
        "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.": "ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ಉತ್ತರಿಸಲು ಪ್ರಸ್ತುತ ಪರಿಶೀಲಿಸಿದ ಜ್ಞಾನದ ಮೂಲದಲ್ಲಿ ಸಾಕಷ್ಟು ಪೂರಕ ಮಾಹಿತಿಯನ್ನು ಕಂಡುಹಿಡಿಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.",
        "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question.": "ಪ್ರಸ್ತುತ ಮಾದರಿ ಜ್ಞಾನದ ಮೂಲವನ್ನು ಸ್ಥಿರ/ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯದಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ ಮತ್ತು ಆ ಪ್ರಶ್ನೆಗೆ ಪರಿಶೀಲಿಸಿದ ಪ್ರಸ್ತುತ ಅಥವಾ ನೈಜ-ಸಮಯದ ಮಾಹಿತಿಯನ್ನು ಒದಗಿಸುವುದಿಲ್ಲ.",
        "Please ask a question about River Ganga or Namami Gange programs.": "ದಯವಿಟ್ಟು ಗಂಗಾ ನದಿ ಅಥವಾ ನಮಾಮಿ ಗಂಗೆ ಕಾರ್ಯಕ್ರಮಗಳ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ.",
        "Please enter a question to ask Chacha Mascot.": "ದಯವಿಟ್ಟು ಚಾಚಾ ಮ್ಯಾಸ್ಕಾಟ್ ಬಳಿ ಕೇಳಲು ಪ್ರಶ್ನೆಯನ್ನು ನಮೂದಿಸಿ.",
        "Sorry, I'm having trouble connecting right now.": "ಕ್ಷಮಿಸಿ, ಸಂಪರ್ಕ ಸಾಧಿಸಲು ನನಗೆ ತೊಂದರೆಯಾಗುತ್ತಿದೆ."
    },
    "kn_to_en": {
        "ಹಿಂಪಡೆಯಲಾದ ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯದ ಪ್ರಕಾರ:": "From the retrieved historical GRBMP material:",
        "ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ಉತ್ತರಿಸಲು ಪ್ರಸ್ತುತ ಪರಿಶೀಲಿಸಿದ ಜ್ಞಾನದ ಮೂಲದಲ್ಲಿ ಸಾಕಷ್ಟು ಪೂರಕ ಮಾಹಿತಿಯನ್ನು ಕಂಡುಹಿಡಿಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ.": "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.",
        "ಪ್ರಸ್ತುತ ಮಾದರಿ ಜ್ಞಾನದ ಮೂಲವನ್ನು ಸ್ಥಿರ/ಐತಿಹಾಸಿಕ GRBMP ವಿಷಯದಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ ಮತ್ತು ಆ ಪ್ರಶ್ನೆಗೆ ಪರಿಶೀಲಿಸಿದ ಪ್ರಸ್ತುತ ಅಥವಾ ನೈಜ-ಸಮಯದ ಮಾಹಿತಿಯನ್ನು ಒದಗಿಸುವುದಿಲ್ಲ.": "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question.",
        "ದಯವಿಟ್ಟು ಗಂಗಾ ನದಿ ಅಥವಾ ನಮಾಮಿ ಗಂಗೆ ಕಾರ್ಯಕ್ರಮಗಳ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ.": "Please ask a question about River Ganga or Namami Gange programs.",
        "ದಯವಿಟ್ಟು ಚಾಚಾ ಮ್ಯಾಸ್ಕಾಟ್ ಬಳಿ ಕೇಳಲು ಪ್ರಶ್ನೆಯನ್ನು ನಮೂದಿಸಿ.": "Please enter a question to ask Chacha Mascot.",
        "ಕ್ಷಮಿಸಿ, ಸಂಪರ್ಕ ಸಾಧಿಸಲು ನನಗೆ ತೊಂದರೆಯಾಗುತ್ತಿದೆ.": "Sorry, I'm having trouble connecting right now."
    },
    "en_to_ta": {
        "From the retrieved historical GRBMP material:": "மீட்டெடுக்கப்பட்ட வரலாற்று GRBMP தரவுகளின்படி:",
        "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.": "நம்பகமான பதிலை அளிக்க தற்போதைய சரிபார்க்கப்பட்ட அறிவுத் தளத்தில் போதுமான ஆதாரத் தகவலைக் கண்டுபிடிக்க முடியவில்லை.",
        "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question.": "தற்போதைய மாதிரி அறிவுத் தளம் நிலையான/வரலாற்று GRBMP பொருட்களிலிருந்து உருவாக்கப்பட்டுள்ளது மற்றும் அந்தக் கேள்விக்கு சரிபார்க்கப்பட்ட தற்போதைய அல்லது நிகழ்நேர தகவலை வழங்காது.",
        "Please ask a question about River Ganga or Namami Gange programs.": "தயவுசெய்து கங்கை நதி அல்லது நமாமி கங்கை திட்டங்கள் குறித்த கேள்வியைக் கேளுங்கள்.",
        "Please enter a question to ask Chacha Mascot.": "சாச்சா சின்னத்திடம் கேட்க ஒரு கேள்வியை உள்ளிடவும்.",
        "Sorry, I'm having trouble connecting right now.": "மன்னிக்கவும், இப்போது இணைப்பதில் சிக்கல் ஏற்பட்டுள்ளது."
    },
    "ta_to_en": {
        "மீட்டெடுக்கப்பட்ட வரலாற்று GRBMP தரவுகளின்படி:": "From the retrieved historical GRBMP material:",
        "நம்பகமான பதிலை அளிக்க தற்போதைய சரிபார்க்கப்பட்ட அறிவுத் தளத்தில் போதுமான ஆதாரத் தகவலைக் கண்டுபிடிக்க முடியவில்லை.": "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.",
        "தற்போதைய மாதிரி அறிவுத் தளம் நிலையான/வரலாற்று GRBMP பொருட்களிலிருந்து உருவாக்கப்பட்டுள்ளது மற்றும் அந்தக் கேள்விக்கு சரிபார்க்கப்பட்ட தற்போதைய அல்லது நிகழ்நேர தகவலை வழங்காது.": "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question.",
        "தயவுசெய்து கங்கை நதி அல்லது நமாமி கங்கை திட்டங்கள் குறித்த கேள்வியைக் கேளுங்கள்.": "Please ask a question about River Ganga or Namami Gange programs.",
        "சாச்சா சின்னத்திடம் கேட்க ஒரு கேள்வியை உள்ளிடவும்.": "Please enter a question to ask Chacha Mascot.",
        "மன்னிக்கவும், இப்போது இணைப்பதில் சிக்கல் ஏற்பட்டுள்ளது.": "Sorry, I'm having trouble connecting right now."
    }
}


def parse_retry_after(header_value: str | None, max_delay: float = 30.0) -> float | None:
    """Parse HTTP Retry-After header into seconds. Supports integer seconds and HTTP dates."""
    if not header_value or not str(header_value).strip():
        return None
    val = str(header_value).strip()
    try:
        seconds = float(val)
        if seconds >= 0:
            return min(seconds, max_delay)
    except ValueError:
        pass

    try:
        parsed_dt = email.utils.parsedate_to_datetime(val)
        if parsed_dt:
            diff = (parsed_dt - datetime.now(timezone.utc)).total_seconds()
            if diff > 0:
                return min(diff, max_delay)
            return 0.0
    except Exception:
        pass

    return None


class RetryConfig:
    """Configuration for bounded retry policy."""
    def __init__(
        self,
        max_retries: int | None = None,
        initial_delay: float | None = None,
        max_delay: float | None = None,
        backoff_factor: float = 2.0,
        max_total_time: float = 20.0,
        sleep_fn: Callable[[float], None] = time.sleep,
        time_fn: Callable[[], float] = time.time,
    ) -> None:
        self.max_retries = max_retries if max_retries is not None else int(os.getenv("TRANSLATION_MAX_RETRIES", "3"))
        self.initial_delay = initial_delay if initial_delay is not None else float(os.getenv("TRANSLATION_INITIAL_DELAY", "0.2"))
        self.max_delay = max_delay if max_delay is not None else float(os.getenv("TRANSLATION_MAX_DELAY", "8.0"))
        self.backoff_factor = backoff_factor
        self.max_total_time = max_total_time
        self.sleep_fn = sleep_fn
        self.time_fn = time_fn


_TRANSLATION_CACHE: dict[tuple[str, str, str], str] = {}


def clear_translation_cache() -> None:
    """Clear in-memory translation cache (useful for testing)."""
    _TRANSLATION_CACHE.clear()


class TranslationProvider(ABC):
    """Abstract Base Class for translation providers."""

    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source_lang to target_lang.
        
        Raises TranslationError if translation cannot be completed.
        """
        raise NotImplementedError


class GoogleGTXTranslationProvider(TranslationProvider):
    """Translation provider using Google Translate and fallback endpoints with bounded retries."""

    ENDPOINTS = [
        "https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={q}",
        "https://translate.google.com/translate_a/single?client=at&sl={sl}&tl={tl}&dt=t&q={q}",
        "https://api.mymemory.translated.net/get?q={q}&langpair={sl}|{tl}",
    ]

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text or not text.strip() or source_lang == target_lang:
            return text

        start_time = self.retry_config.time_fn()
        current_delay = self.retry_config.initial_delay
        attempts = 0
        max_attempts = 1 + self.retry_config.max_retries

        encoded_text = urllib.parse.quote(text)

        while attempts < max_attempts:
            # Rotate endpoints on successive attempts if rate-limited
            endpoint_idx = (attempts) % len(self.ENDPOINTS)
            endpoint_template = self.ENDPOINTS[endpoint_idx]
            url = endpoint_template.format(sl=source_lang, tl=target_lang, q=encoded_text)

            user_agent = self.USER_AGENTS[attempts % len(self.USER_AGENTS)]
            req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
            attempts += 1

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    status = getattr(resp, "status", 200)
                    if status == 200:
                        raw_body = resp.read().decode("utf-8")
                        try:
                            data = json.loads(raw_body)
                        except json.JSONDecodeError as jde:
                            logger.warning(f"[Translator] Malformed JSON from translation provider: {jde}")
                            raise TranslationError(f"Malformed translation response from provider: {jde}") from jde

                        # 1. Google Translate response structure: [[["translated", "source", ...]]]
                        if data and isinstance(data, list) and len(data) > 0 and data[0]:
                            chunks = [item[0] for item in data[0] if item and isinstance(item, list) and item[0]]
                            result = "".join(chunks).strip()
                            if result:
                                return result
                            raise TranslationError("Empty translation received from Google GTX")

                        # 2. MyMemory response structure: {"responseData": {"translatedText": "..."}}
                        if isinstance(data, dict) and "responseData" in data:
                            resp_data = data.get("responseData") or {}
                            translated = resp_data.get("translatedText")
                            if translated and translated.strip():
                                return translated.strip()

                        raise TranslationError("Unexpected response structure from translation provider")
                    else:
                        raise urllib.error.HTTPError(url, status, f"HTTP {status}", resp.headers, None)

            except urllib.error.HTTPError as http_err:
                code = http_err.code
                headers = http_err.headers or {}
                # Crucial for test assertions and diagnostic monitoring: log warning with status code
                logger.warning(
                    f"[Translator] HTTP translation failed ({source_lang}->{target_lang}): "
                    f"HTTP {code} {http_err.reason}"
                )

                # Non-retryable HTTP errors
                if code in (400, 401, 403, 404):
                    raise TranslationError(
                        f"Non-retryable HTTP error from translation provider: HTTP {code} ({source_lang}->{target_lang})"
                    ) from http_err

                # Retryable HTTP errors: 429 and 5xx
                if code == 429 or (500 <= code < 600):
                    if attempts >= max_attempts:
                        raise TranslationError(
                            f"HTTP translation failed after {attempts} attempts ({source_lang}->{target_lang}): HTTP {code}"
                        ) from http_err

                    retry_after_hdr = headers.get("Retry-After") or headers.get("retry-after")
                    retry_after_sec = parse_retry_after(retry_after_hdr, self.retry_config.max_delay)

                    delay = retry_after_sec if retry_after_sec is not None else current_delay
                    # Add jitter if delay was not explicitly dictated by Retry-After
                    if retry_after_sec is None:
                        delay = min(delay + random.uniform(0, 0.25 * max(delay, 0.05)), self.retry_config.max_delay)
                        current_delay = min(current_delay * self.retry_config.backoff_factor, self.retry_config.max_delay)

                    elapsed = self.retry_config.time_fn() - start_time
                    if elapsed + delay > self.retry_config.max_total_time:
                        raise TranslationError(
                            f"Translation retry total waiting time exceeded for ({source_lang}->{target_lang})"
                        ) from http_err

                    self.retry_config.sleep_fn(delay)
                    continue

                raise TranslationError(f"HTTP error during translation ({source_lang}->{target_lang}): {http_err}") from http_err

            except (urllib.error.URLError, TimeoutError, OSError) as net_err:
                logger.warning(
                    f"[Translator] Network/timeout error during translation ({source_lang}->{target_lang}): {net_err}"
                )
                if attempts >= max_attempts:
                    raise TranslationError(
                        f"Translation network failure after {attempts} attempts ({source_lang}->{target_lang}): {net_err}"
                    ) from net_err

                delay = min(current_delay + random.uniform(0, 0.25 * max(current_delay, 0.05)), self.retry_config.max_delay)
                current_delay = min(current_delay * self.retry_config.backoff_factor, self.retry_config.max_delay)

                elapsed = self.retry_config.time_fn() - start_time
                if elapsed + delay > self.retry_config.max_total_time:
                    raise TranslationError(
                        f"Translation timeout retry total time exceeded for ({source_lang}->{target_lang})"
                    ) from net_err

                self.retry_config.sleep_fn(delay)
                continue

            except TranslationError:
                raise
            except Exception as exc:
                logger.warning(f"[Translator] Unexpected error ({source_lang}->{target_lang}): {exc}")
                raise TranslationError(f"Unexpected translation error: {exc}") from exc

        raise TranslationError(f"Translation failed ({source_lang}->{target_lang}) after {attempts} attempts")


class GoogleCloudTranslationProvider(TranslationProvider):
    """Official Google Cloud Translation API (v2 Basic) with authenticated requests and retry handling."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self.api_key = (api_key or os.getenv("GOOGLE_TRANSLATE_API_KEY") or os.getenv("TRANSLATION_API_KEY") or "").strip()
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text or not text.strip() or source_lang == target_lang:
            return text

        if not self.api_key:
            raise TranslationError(
                "Google Cloud Translation API key not configured. Set GOOGLE_TRANSLATE_API_KEY in environment."
            )

        start_time = self.retry_config.time_fn()
        current_delay = self.retry_config.initial_delay
        attempts = 0
        max_attempts = 1 + self.retry_config.max_retries

        # Build payload according to official Google Cloud Translation API v2
        endpoint = f"https://translation.googleapis.com/language/translate/v2?key={urllib.parse.quote(self.api_key)}"
        payload = {
            "q": [text],
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Ganga-AI-Mascot-Translator/1.0",
        }
        req = urllib.request.Request(endpoint, data=body_bytes, headers=headers, method="POST")

        while attempts < max_attempts:
            attempts += 1
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    status = getattr(resp, "status", 200)
                    if status == 200:
                        raw_body = resp.read().decode("utf-8")
                        try:
                            data = json.loads(raw_body)
                        except json.JSONDecodeError as jde:
                            logger.warning(f"[Translator] Malformed JSON from Google Cloud Translation API: {jde}")
                            raise TranslationError(f"Malformed response from Google Cloud Translation API: {jde}") from jde

                        translations = data.get("data", {}).get("translations", [])
                        if translations and isinstance(translations, list) and translations[0]:
                            translated_text = translations[0].get("translatedText", "")
                            # Decode HTML entities if returned by Google Translate
                            decoded = html.unescape(translated_text).strip()
                            if decoded:
                                return decoded
                            raise TranslationError("Empty translation received from Google Cloud Translation API")
                        raise TranslationError("Unexpected response structure from Google Cloud Translation API")
                    else:
                        raise urllib.error.HTTPError(endpoint, status, f"HTTP {status}", resp.headers, None)

            except urllib.error.HTTPError as http_err:
                code = http_err.code
                headers = http_err.headers or {}
                # Sanitize error message to ensure API key is never logged
                logger.warning(
                    f"[Translator] Google Cloud Translation request failed ({source_lang}->{target_lang}): "
                    f"HTTP {code} {http_err.reason}"
                )

                if code in (400, 401, 403, 404):
                    raise TranslationError(
                        f"Non-retryable error from Google Cloud Translation API: HTTP {code}"
                    ) from http_err

                if code == 429 or (500 <= code < 600):
                    if attempts >= max_attempts:
                        raise TranslationError(
                            f"Google Cloud Translation failed after {attempts} attempts ({source_lang}->{target_lang}): HTTP {code}"
                        ) from http_err

                    retry_after_hdr = headers.get("Retry-After") or headers.get("retry-after")
                    retry_after_sec = parse_retry_after(retry_after_hdr, self.retry_config.max_delay)

                    delay = retry_after_sec if retry_after_sec is not None else current_delay
                    if retry_after_sec is None:
                        delay = min(delay + random.uniform(0, 0.25 * max(delay, 0.05)), self.retry_config.max_delay)
                        current_delay = min(current_delay * self.retry_config.backoff_factor, self.retry_config.max_delay)

                    elapsed = self.retry_config.time_fn() - start_time
                    if elapsed + delay > self.retry_config.max_total_time:
                        raise TranslationError(
                            f"Translation retry total waiting time exceeded for ({source_lang}->{target_lang})"
                        ) from http_err

                    self.retry_config.sleep_fn(delay)
                    continue

                raise TranslationError(f"HTTP error from Google Cloud Translation: {http_err}") from http_err

            except (urllib.error.URLError, TimeoutError, OSError) as net_err:
                logger.warning(
                    f"[Translator] Network error communicating with Google Cloud Translation ({source_lang}->{target_lang}): {net_err}"
                )
                if attempts >= max_attempts:
                    raise TranslationError(
                        f"Google Cloud Translation network failure after {attempts} attempts ({source_lang}->{target_lang}): {net_err}"
                    ) from net_err

                delay = min(current_delay + random.uniform(0, 0.25 * max(current_delay, 0.05)), self.retry_config.max_delay)
                current_delay = min(current_delay * self.retry_config.backoff_factor, self.retry_config.max_delay)

                elapsed = self.retry_config.time_fn() - start_time
                if elapsed + delay > self.retry_config.max_total_time:
                    raise TranslationError(
                        f"Google Cloud Translation timeout retry time exceeded for ({source_lang}->{target_lang})"
                    ) from net_err

                self.retry_config.sleep_fn(delay)
                continue

            except TranslationError:
                raise
            except Exception as exc:
                logger.warning(f"[Translator] Unexpected Google Cloud Translation failure: {exc}")
                raise TranslationError(f"Unexpected Google Cloud Translation failure: {exc}") from exc

        raise TranslationError(f"Translation failed ({source_lang}->{target_lang}) after {attempts} attempts")


_default_provider: TranslationProvider | None = None


def get_translation_provider(name: str | None = None) -> TranslationProvider:
    """Factory to retrieve or initialize the configured TranslationProvider."""
    global _default_provider
    provider_name = (name or os.getenv("TRANSLATION_PROVIDER", "")).strip().lower()

    if provider_name in ("google_cloud", "google", "gcp"):
        return GoogleCloudTranslationProvider()
    if provider_name in ("gtx", "google_gtx", "free"):
        return GoogleGTXTranslationProvider()

    if _default_provider is not None and not name:
        return _default_provider

    # Auto-detect: if Google Cloud credentials exist, use GoogleCloudTranslationProvider
    api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY") or os.getenv("TRANSLATION_API_KEY")
    if api_key:
        return GoogleCloudTranslationProvider(api_key=api_key)

    # Otherwise default to GoogleGTXTranslationProvider
    return GoogleGTXTranslationProvider()


def set_default_translation_provider(provider: TranslationProvider | None) -> None:
    """Override or inject the default translation provider (useful for tests)."""
    global _default_provider
    _default_provider = provider


def _http_translate(
    text: str,
    source_lang: str,
    target_lang: str,
    *,
    provider: TranslationProvider | None = None,
) -> str | None:
    """Backwards-compatible helper to translate text via the configured translation provider."""
    if not text or not text.strip() or source_lang == target_lang:
        return text

    active_provider = provider or get_translation_provider()
    try:
        return active_provider.translate(text, source_lang, target_lang)
    except Exception as exc:
        logger.warning(f"[Translator] HTTP translation failed ({source_lang}->{target_lang}): {exc}")
        return None


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    *,
    provider: TranslationProvider | None = None,
) -> str:
    """Translate text between supported languages ('en', 'hi', 'kn', 'ta') or raise TranslationError."""
    if not text or not text.strip():
        return text

    src = normalize_language(source_lang, default="en")
    tgt = normalize_language(target_lang, default="en")

    if src == tgt:
        return text

    cache_key = (src, tgt, text.strip())
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    # Check exact domain phrases directly first
    direct_key = f"{src}_to_{tgt}"
    domain_map = DOMAIN_TRANSLATIONS.get(direct_key, {})
    if text in domain_map:
        res = domain_map[text]
        _TRANSLATION_CACHE[cache_key] = res
        return res

    # Check cross-Indic phrase via English pivot if available
    if src != "en" and tgt != "en":
        to_en = DOMAIN_TRANSLATIONS.get(f"{src}_to_en", {})
        if text in to_en:
            en_pivot = to_en[text]
            from_en = DOMAIN_TRANSLATIONS.get(f"en_to_{tgt}", {})
            if en_pivot in from_en:
                res = from_en[en_pivot]
                _TRANSLATION_CACHE[cache_key] = res
                return res

    # Check historical material prefix
    has_prefix = False
    core_text = text
    for lang_code, pfx in PREFIX_MAP.items():
        if text.startswith(pfx):
            has_prefix = True
            core_text = text[len(pfx):]
            break
        # Also check without trailing space
        pfx_trimmed = pfx.rstrip()
        if text.startswith(pfx_trimmed):
            has_prefix = True
            core_text = text[len(pfx_trimmed):].lstrip()
            break

    # If the text was exclusively the prefix itself, return the target prefix directly
    if has_prefix and not core_text.strip():
        target_prefix = PREFIX_MAP.get(tgt, PREFIX_MAP["en"])
        _TRANSLATION_CACHE[cache_key] = target_prefix
        return target_prefix

    # Check if core_text matches domain translations
    translated_core = None
    if direct_key in DOMAIN_TRANSLATIONS and core_text in DOMAIN_TRANSLATIONS[direct_key]:
        translated_core = DOMAIN_TRANSLATIONS[direct_key][core_text]
    elif src != "en" and tgt != "en":
        to_en = DOMAIN_TRANSLATIONS.get(f"{src}_to_en", {})
        if core_text in to_en:
            en_pivot = to_en[core_text]
            from_en = DOMAIN_TRANSLATIONS.get(f"en_to_{tgt}", {})
            if en_pivot in from_en:
                translated_core = from_en[en_pivot]

    if translated_core is None:
        active_provider = provider or get_translation_provider()
        # Direct call to provider or _http_translate so mock hooks work seamlessly
        try:
            # If _http_translate is patched in tests, allow its return value to be honored
            translated_core = _http_translate(core_text, src, tgt, provider=active_provider)
        except TranslationError:
            raise
        except Exception as err:
            raise TranslationError(
                f"Translation failed ({src}->{tgt}); returning the untranslated text would be misleading: {err}"
            ) from err

    if not translated_core:
        raise TranslationError(
            f"Translation failed ({src}->{tgt}); returning the untranslated text would be misleading"
        )

    if has_prefix:
        target_prefix = PREFIX_MAP.get(tgt, PREFIX_MAP["en"])
        final_res = f"{target_prefix}{translated_core}"
    else:
        final_res = translated_core

    _TRANSLATION_CACHE[cache_key] = final_res
    return final_res
