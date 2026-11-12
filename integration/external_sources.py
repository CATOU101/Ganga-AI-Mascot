"""Small, optional Wikimedia summary lookup with attribution and bounded caching.

This adapter is intended for stable background facts only. It must not be used
for current readings, water quality, water levels, or flood status.
"""

from __future__ import annotations

import html
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from brain.answer_format import strip_answer_formatting_instructions

logger = logging.getLogger("integration.external_sources")

WIKIPEDIA_LANGUAGES = frozenset({
    "en", "hi", "kn", "ta", "te", "bn", "mr", "gu", "ml", "pa", "ur", "or", "as",
})
WIKIPEDIA_LICENSE = "CC BY-SA 4.0 / GFDL"
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60
DEFAULT_MAX_SUMMARY_CHARS = 700
MAX_SOURCES_PER_REQUEST = 2
REQUEST_TIMEOUT_SECONDS = 4.0
CURRENT_OR_MEASUREMENT_TERMS = (
    "current", "today", "latest", "right now", "real-time", "realtime", "present status",
    "water quality", "water level", "water depth", "dissolved oxygen",
    "flood warning", "danger level", "station reading", "monitoring data",
)
MEASUREMENT_PARAMETER_RE = re.compile(r"\b(?:pH|BOD)\b", re.IGNORECASE)
QUESTION_PREFIXES = (
    "tell me about ", "explain ", "what is ", "what are ", "who is ", "who are ",
    "describe ", "give me information about ", "compare ", "comparison of ",
)
RIVER_TITLES = {
    "ganga": "Ganges", "ganges": "Ganges", "yamuna": "Yamuna River",
    "brahmaputra": "Brahmaputra River", "indus": "Indus River",
    "godavari": "Godavari River", "krishna": "Krishna River",
    "kaveri": "Kaveri River", "cauvery": "Kaveri River",
    "narmada": "Narmada River", "mahanadi": "Mahanadi River",
}


@dataclass(frozen=True)
class ExternalSummary:
    title: str
    extract: str
    url: str
    language: str
    license: str = WIKIPEDIA_LICENSE
    retrieved_at: str = ""
    page_timestamp: str | None = None
    cache_hit: bool = False


class ExternalSourceService:
    """Fetch at most two short article summaries, cache them, and return attribution."""

    def __init__(
        self,
        *,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        max_summary_chars: int = DEFAULT_MAX_SUMMARY_CHARS,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        opener=None,
        clock=time.monotonic,
    ) -> None:
        self.cache_ttl_seconds = max(1, cache_ttl_seconds)
        self.max_summary_chars = max(100, min(max_summary_chars, 1000))
        self.timeout_seconds = timeout_seconds
        self._opener = opener or urllib.request.urlopen
        self._clock = clock
        self._cache: dict[tuple[str, str], tuple[float, ExternalSummary]] = {}
        self._query_cache: dict[tuple[str, str, int], tuple[float, list[ExternalSummary]]] = {}
        self._lock = threading.Lock()

    def search_summaries(
        self,
        query: str,
        *,
        language: str = "en",
        max_sources: int = 1,
    ) -> list[ExternalSummary]:
        lang = language if language in WIKIPEDIA_LANGUAGES else "en"
        normalized = re.sub(r"\s+", " ", (query or "").casefold()).strip()
        if not normalized or self.is_time_sensitive_or_measurement_query(normalized):
            return []
        limit = max(1, min(int(max_sources), MAX_SOURCES_PER_REQUEST))
        query_key = (lang, normalized, limit)
        now = self._clock()
        with self._lock:
            cached_query = self._query_cache.get(query_key)
            if cached_query:
                created, cached_summaries = cached_query
                if now - created < self.cache_ttl_seconds:
                    return [ExternalSummary(
                        title=item.title,
                        extract=item.extract,
                        url=item.url,
                        language=item.language,
                        license=item.license,
                        retrieved_at=item.retrieved_at,
                        page_timestamp=item.page_timestamp,
                        cache_hit=True,
                    ) for item in cached_summaries]
                del self._query_cache[query_key]
        titles = self._article_titles(query, limit)
        summaries = []
        for title in titles[:limit]:
            summary = self._cached_summary(title, lang)
            if summary is None:
                summary = self._fetch_summary(title, lang)
                if summary:
                    with self._lock:
                        self._cache[(lang, title.casefold())] = (self._clock(), summary)
            if summary:
                summaries.append(summary)
        result = summaries[:limit]
        if result:
            with self._lock:
                self._query_cache[query_key] = (self._clock(), result)
        return result

    @staticmethod
    def is_time_sensitive_or_measurement_query(query: str) -> bool:
        text = re.sub(r"\s+", " ", (query or "").casefold()).strip()
        if any(term in text for term in CURRENT_OR_MEASUREMENT_TERMS) or MEASUREMENT_PARAMETER_RE.search(text):
            return True
        return bool(re.search(r"\b(last|past|next)\s+\d+\s+(days?|weeks?|months?|years?)\b", text))

    def _article_titles(self, question: str, limit: int) -> list[str]:
        text = re.sub(
            r"\s+", " ", strip_answer_formatting_instructions(question).casefold()
        ).strip().rstrip("?.! ")
        if re.search(r"\b(compare|comparison|contrast|versus|vs\.?)\b", text):
            matched = []
            for alias, title in RIVER_TITLES.items():
                if re.search(rf"\b{re.escape(alias)}\b", text) and title not in matched:
                    matched.append(title)
            if len(matched) >= 2:
                return matched[:limit]

        for prefix in QUESTION_PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        text = re.sub(r"^(?:the|a|an)\s+", "", text)
        text = re.sub(r"\b(please|briefly|in detail|step by step|with examples)\b", " ", text)
        text = re.sub(r"\b(with|include|provide|show|give)\s+(?:me\s+)?(?:sources?|citations?|references?|additional context)\b", " ", text)
        text = re.sub(r"\s+", " ", text).strip(" .?!")
        if not text:
            return []
        for alias, title in RIVER_TITLES.items():
            if re.search(rf"\b{re.escape(alias)}\b", text):
                return [title]
        return [text[:120]]

    def _cached_summary(self, title: str, language: str) -> ExternalSummary | None:
        key = (language, title.casefold())
        now = self._clock()
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            created, summary = entry
            if now - created >= self.cache_ttl_seconds:
                del self._cache[key]
                return None
            return ExternalSummary(
                title=summary.title,
                extract=summary.extract,
                url=summary.url,
                language=summary.language,
                license=summary.license,
                retrieved_at=summary.retrieved_at,
                page_timestamp=summary.page_timestamp,
                cache_hit=True,
            )

    def _request_json(self, url: str, language: str) -> dict | None:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Ganga-AI-Mascot/1.0 (https://github.com/CATOU101/Ganga-AI-Mascot)",
                "Api-User-Agent": "Ganga-AI-Mascot/1.0 (https://github.com/CATOU101/Ganga-AI-Mascot)",
            },
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read(256_000)
            payload = json.loads(raw.decode("utf-8"))
            return payload if isinstance(payload, dict) else None
        except urllib.error.HTTPError as error:
            if error.code == 429:
                logger.info("Wikimedia summary lookup throttled; skipping external source.")
            else:
                logger.info("Wikimedia summary lookup unavailable: http_%s.", error.code)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError):
            logger.info("Wikimedia summary lookup unavailable.")
        return None

    def _fetch_summary(self, query_or_title: str, language: str) -> ExternalSummary | None:
        base = f"https://{language}.wikipedia.org"
        search_url = f"{base}/w/rest.php/v1/search/page?{urllib.parse.urlencode({'q': query_or_title, 'limit': 1})}"
        search = self._request_json(search_url, language)
        pages = search.get("pages") if search else None
        if not isinstance(pages, list) or not pages or not isinstance(pages[0], dict):
            return None
        title = pages[0].get("title") or pages[0].get("key")
        if not isinstance(title, str) or not title.strip():
            return None

        summary_url = f"{base}/api/rest_v1/page/summary/{urllib.parse.quote(title, safe='')}"
        payload = self._request_json(summary_url, language)
        if not payload:
            return None
        extract = self._clean_extract(payload.get("extract", ""), self.max_summary_chars)
        page_url = payload.get("content_urls", {}).get("desktop", {}).get("page")
        if not extract or not self._valid_wikipedia_url(page_url):
            return None
        page_title = str(payload.get("title") or title).strip()
        return ExternalSummary(
            title=page_title,
            extract=extract,
            url=page_url,
            language=language,
            retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            page_timestamp=payload.get("timestamp") if isinstance(payload.get("timestamp"), str) else None,
        )

    @staticmethod
    def _valid_wikipedia_url(value: object) -> bool:
        if not isinstance(value, str):
            return False
        parsed = urllib.parse.urlparse(value)
        return parsed.scheme == "https" and parsed.hostname is not None and parsed.hostname.endswith(".wikipedia.org")

    @staticmethod
    def _clean_extract(value: object, limit: int) -> str:
        if not isinstance(value, str):
            return ""
        clean = html.unescape(re.sub(r"<[^>]+>", " ", value))
        clean = re.sub(r"\[[0-9]+\]", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean) <= limit:
            return clean
        boundary = clean.rfind(". ", 0, limit + 1)
        if boundary >= int(limit * 0.55):
            return clean[:boundary + 1]
        cut = clean.rfind(" ", 0, limit)
        return clean[:cut if cut > 0 else limit].rstrip(" ,;:") + "…"
