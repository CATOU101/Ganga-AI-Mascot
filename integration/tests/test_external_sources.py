import io
import json

from integration.external_sources import ExternalSourceService, ExternalSummary
from integration.response_cache import TTLCache, general_response_cache_key
from integration.supplementary_info import append_supplementary_summaries


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.payload


def test_external_summary_lookup_is_bounded_attributed_and_cached():
    calls = []
    now = [0.0]

    def opener(request, timeout):
        calls.append((request.full_url, timeout))
        if "/search/page" in request.full_url:
            return FakeResponse({"pages": [{"title": "Mars"}]})
        return FakeResponse({
            "title": "Mars", "extract": "Mars is the fourth planet from the Sun. It has two moons.",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Mars"}},
            "timestamp": "2026-11-01T00:00:00Z",
        })

    service = ExternalSourceService(opener=opener, clock=lambda: now[0], cache_ttl_seconds=60)
    first = service.search_summaries("What is Mars?", max_sources=20)
    second = service.search_summaries("What is Mars?", max_sources=20)
    assert len(first) == len(second) == 1
    assert first[0].license == "CC BY-SA 4.0 / GFDL"
    assert first[0].page_timestamp == "2026-11-01T00:00:00Z"
    assert second[0].cache_hit is True
    assert len(calls) == 2
    assert all("limit=1" in url or "/page/summary/" in url for url, _ in calls)


def test_current_measurements_are_never_fetched_from_external_summaries():
    service = ExternalSourceService(opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError()))
    assert service.search_summaries("What is the current water quality of Yamuna?") == []
    assert service.is_time_sensitive_or_measurement_query("What is the BOD reading today?") is True
    assert service.is_time_sensitive_or_measurement_query("Explain philosophy on Mars") is False


def test_ganga_overview_format_phrase_resolves_to_the_ganges_article_title():
    service = ExternalSourceService(opener=lambda *_args, **_kwargs: None)
    assert service._article_titles("Tell me about the Ganga in points.", 1) == ["Ganges"]


def test_external_summary_is_separate_and_duplicate_context_is_skipped():
    summary = ExternalSummary(
        title="Mars", extract="Mars has two small natural satellites named Phobos and Deimos.",
        url="https://en.wikipedia.org/wiki/Mars", language="en",
    )
    answer, citations = append_supplementary_summaries("Mars is the fourth planet from the Sun.", [summary])
    assert "### Additional information" in answer
    assert "not verified by the project knowledge base" in answer
    assert citations[0]["url"] == summary.url
    duplicate, duplicate_citations = append_supplementary_summaries(
        summary.extract, [summary]
    )
    assert duplicate == summary.extract
    assert duplicate_citations == []


def test_general_cache_is_keyed_by_language_and_format_and_skips_personal_current_queries():
    english = general_response_cache_key("What is Mars?", "en", "natural")
    assert english != general_response_cache_key("What is Mars?", "hi", "natural")
    assert english != general_response_cache_key("What is Mars?", "en", "comparison")
    assert general_response_cache_key("What is the current weather?", "en", "natural") is None
    assert general_response_cache_key("What should I do?", "en", "natural") is None
    cache = TTLCache[str](ttl_seconds=10, clock=lambda: 1.0)
    cache.set(english, "cached")
    assert cache.get(english) == "cached"
