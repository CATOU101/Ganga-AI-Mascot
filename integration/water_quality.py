"""CPCB live water-quality lookup for conversational responses."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger("integration.water_quality")

STATIONS_URL = "https://rtwqmsdb1.cpcb.gov.in/data/internet/stations/stations.json"
SNAPSHOT_URL = "https://rtwqmsdb1.cpcb.gov.in/data/internet/layers/10/index.json"
CPCB_SOURCE = "CPCB Real-Time Water Quality Monitoring System"
CPCB_URL = "https://rtwqmsdb1.cpcb.gov.in/#/"
CACHE_TTL_SECONDS = 60
STALE_AFTER_SECONDS = 90 * 60


@dataclass(frozen=True)
class Station:
    name: str
    station_id: str
    station_no: str
    registry_name: str


STATIONS = (
    Station("Haridwar", "11788", "UK55", "Har Ki Pauri"),
    Station("Kanpur", "11791", "UT58", "Luv Kush Barrage"),
    Station("Ghazipur", "11798", "UT66", "Abdul Hameed Setu"),
    Station("Farakka", "11815", "WB86", "Farakka Barrage"),
    Station("Nabadwip", "11816", "WB87", "Nabadwip Bathing Ghat"),
)

STATION_ALIASES = {
    "haridwar": "Haridwar",
    "हरिद्वार": "Haridwar",
    "kanpur": "Kanpur",
    "कानपुर": "Kanpur",
    "ghazipur": "Ghazipur",
    "गाजीपुर": "Ghazipur",
    "farakka": "Farakka",
    "फरक्का": "Farakka",
    "nabadwip": "Nabadwip",
    "nabadvip": "Nabadwip",
    "নবদ্বীপ": "Nabadwip",
    "नवद्वीप": "Nabadwip",
}

PARAMETERS = {
    "DO": ("Dissolved oxygen", ("dissolved oxygen",)),
    "BOD": ("Biochemical oxygen demand", ("biochemical oxygen demand",)),
    "pH": ("pH", ()),
}

PARAMETER_EXPLANATIONS = {
    "DO": "Dissolved oxygen is oxygen present in the water.",
    "BOD": "BOD indicates the oxygen used by microorganisms to break down organic matter.",
    "pH": "pH indicates how acidic or alkaline the water is.",
}


class CPCBWaterQualityError(RuntimeError):
    """Raised when the CPCB registry or snapshot cannot be retrieved or validated."""


@dataclass(frozen=True)
class WaterQualityRequest:
    station_names: tuple[str, ...]
    parameter_codes: tuple[str, ...]
    unsupported_location: str | None = None
    comparison: bool = False


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text, re.IGNORECASE) is not None


def _is_parameter_query(text: str) -> bool:
    lower = text.lower()
    if _contains_phrase(lower, "bod"):
        return True
    do_context = re.search(
        r"\bdo\s+(?:reading|readings|level|levels|value|values|measurement|measurements|at|in|for)\b",
        lower,
    )
    return (
        re.search(r"(?<!\w)DO(?!\w)", text) is not None
        or do_context is not None
        or any(
            _contains_phrase(lower, alias)
            for _, aliases in PARAMETERS.values()
            for alias in aliases
        )
        or _contains_phrase(lower, "ph")
    )


def is_water_quality_query(question: str) -> bool:
    """Recognize live-measurement requests without capturing educational questions."""
    text = question.lower()
    has_quality_phrase = any(
        phrase in text
        for phrase in (
            "water quality",
            "water-quality",
            "जल गुणवत्ता",
            "पानी की गुणवत्ता",
            "गंगा का पानी",
            "गंगा के पानी",
        )
    )
    has_live_intent = any(
        phrase in text
        for phrase in (
            "current",
            "currently",
            "now",
            "today",
            "latest",
            "real-time",
            "realtime",
            "present",
            "reading",
            "readings",
            "measurement",
            "measurements",
            "अभी",
            "आज",
            "वर्तमान",
            "ताज़ा",
            "रीयल-टाइम",
        )
    )
    has_station = any(_contains_phrase(text, alias) for alias in STATION_ALIASES)
    has_ganga_context = any(
        _contains_phrase(text, term)
        for term in ("ganga", "river", "गंगा")
    )
    methodological_question = re.search(
        r"\b(?:how|which|what|explain)\b.*\b(?:measure|measured|measuring|test|tested|testing|"
        r"monitor|monitored|monitoring|assess|assessed|assessment|mean|means|definition)\b",
        text,
    ) is not None
    educational = (
        "what does bod mean",
        "what is bod",
        "what does do mean",
        "what is dissolved oxygen",
        "how is water quality measured",
        "how is the water quality measured",
        "how does water quality get measured",
        "how are water quality parameters measured",
        "which parameters are tested",
        "which parameters are measured",
        "what parameters are tested",
        "how does pollution monitoring work",
        "how is pollution monitored",
        "जल गुणवत्ता कैसे माप",
        "पानी की गुणवत्ता कैसे माप",
    )
    if (
        any(phrase in text for phrase in educational)
        or methodological_question
    ) and not has_live_intent:
        return False

    return (
        has_quality_phrase
        or (has_station and _is_parameter_query(question))
        or (has_live_intent and has_ganga_context and _is_parameter_query(question))
    )


def parse_water_quality_request(question: str) -> WaterQualityRequest:
    """Extract requested stations and parameters; no match means the five-station overview."""
    text = question.lower()
    located_names = []
    for alias, canonical in STATION_ALIASES.items():
        match = re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text, re.IGNORECASE)
        if match:
            located_names.append((match.start(), canonical))
    requested_names = []
    for _, canonical in sorted(located_names):
        if canonical not in requested_names:
            requested_names.append(canonical)
    ordered_stations = tuple(requested_names)

    parameter_codes = []
    if (
        re.search(r"(?<!\w)DO(?!\w)", question) is not None
        or re.search(
            r"\bdo\s+(?:reading|readings|level|levels|value|values|measurement|measurements|at|in|for)\b",
            text,
        )
        or any(_contains_phrase(text, alias) for alias in PARAMETERS["DO"][1])
    ):
        parameter_codes.append("DO")
    if _contains_phrase(text, "bod") or any(
        _contains_phrase(text, alias) for alias in PARAMETERS["BOD"][1]
    ):
        parameter_codes.append("BOD")
    if _contains_phrase(text, "ph"):
        parameter_codes.append("pH")

    requested_parameters = tuple(parameter_codes) or ("DO", "BOD", "pH")
    if ordered_stations:
        station_names = ordered_stations
        unsupported_location = None
    else:
        unsupported_location = _unsupported_location(text)
        station_names = () if unsupported_location else tuple(s.name for s in STATIONS)

    comparison = bool(re.search(r"\b(?:compare|comparison|versus|vs\.?)\b", text))
    return WaterQualityRequest(
        station_names,
        requested_parameters,
        unsupported_location,
        comparison,
    )


def _unsupported_location(text: str) -> str | None:
    match = re.search(r"\b(?:at|in|near|around|of)\s+([a-z][a-z .'-]{1,40})", text)
    if not match:
        hindi_match = re.search(r"(?:में|के पास)\s+([\u0900-\u097f]+)", text)
        if hindi_match and hindi_match.group(1) not in {"गंगा", "नदी", "पानी"}:
            return hindi_match.group(1)
    if not match:
        return None
    candidate = re.split(
        r"\b(?:for|with|and|or|the|water|quality|current|today|now|latest|reading|readings|do|bod|ph|ganga|river)\b",
        match.group(1),
        maxsplit=1,
    )[0].strip(" .'-")
    if not candidate:
        return None
    if any(_contains_phrase(candidate, alias) for alias in STATION_ALIASES):
        return None
    return candidate.title()


def _default_fetch_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "Ganga-AI-Mascot/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status != 200:
                raise CPCBWaterQualityError(f"CPCB returned HTTP {response.status}.")
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise CPCBWaterQualityError(f"Unable to retrieve CPCB data: {error}") from error


class CPCBWaterQualityService:
    def __init__(
        self,
        fetch_json: Callable[[str], Any] = _default_fetch_json,
        *,
        cache_ttl_seconds: int = CACHE_TTL_SECONDS,
        stale_after_seconds: int = STALE_AFTER_SECONDS,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._fetch_json = fetch_json
        self._cache_ttl_seconds = cache_ttl_seconds
        self._stale_after_seconds = stale_after_seconds
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_lock = threading.Lock()

    def _get_json(self, url: str) -> Any:
        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(url)
            if cached and now - cached[0] < self._cache_ttl_seconds:
                return cached[1]

        payload = self._fetch_json(url)
        if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
            raise CPCBWaterQualityError("CPCB returned data in an unexpected format.")
        if payload and url == STATIONS_URL and not any(
            {"station_id", "station_no", "station_name"} <= row.keys() for row in payload
        ):
            raise CPCBWaterQualityError("CPCB station registry is missing required fields.")
        if payload and url == SNAPSHOT_URL and not any(
            {"station_id", "stationparameter_no"} <= row.keys() for row in payload
        ):
            raise CPCBWaterQualityError("CPCB snapshot is missing required station or parameter fields.")

        with self._cache_lock:
            self._cache[url] = (time.monotonic(), payload)
        return payload

    def readings(self, request: WaterQualityRequest) -> list[dict[str, Any]]:
        if request.unsupported_location:
            return []
        try:
            registry = self._get_json(STATIONS_URL)
            snapshot = self._get_json(SNAPSHOT_URL)
        except CPCBWaterQualityError:
            raise
        except Exception as error:
            logger.exception("Unexpected error retrieving CPCB water-quality data")
            raise CPCBWaterQualityError("Unable to retrieve CPCB water-quality data.") from error

        registry_by_id = {str(row.get("station_id")): row for row in registry}
        results = []
        for station_name in request.station_names:
            station = next(s for s in STATIONS if s.name == station_name)
            registry_row = registry_by_id.get(station.station_id)
            verified = (
                registry_row is not None
                and str(registry_row.get("station_no", "")).upper() == station.station_no
                and station.registry_name.lower() in str(registry_row.get("station_name", "")).lower()
            )
            if not verified:
                results.append({"station": station, "unavailable": "station-unverified", "readings": []})
                continue

            station_readings = []
            for code in request.parameter_codes:
                matching = [
                    row
                    for row in snapshot
                    if str(row.get("station_id")) == station.station_id
                    and str(row.get("stationparameter_no", "")).casefold() == code.casefold()
                ]
                reading = self._latest_reading(matching)
                station_readings.append({"parameter": code, "reading": reading})
            results.append({"station": station, "unavailable": None, "readings": station_readings})
        return results

    def _latest_reading(self, records: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not records:
            return None

        def parsed_timestamp(record: dict[str, Any]) -> datetime | None:
            raw_timestamp = record.get("timestamp")
            if not isinstance(raw_timestamp, str) or not raw_timestamp.strip():
                return None
            try:
                parsed = datetime.fromisoformat(raw_timestamp.strip().replace("Z", "+00:00"))
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return None
            return parsed.astimezone(timezone.utc)

        timestamped = [(parsed_timestamp(row), row) for row in records]
        valid = [(stamp, row) for stamp, row in timestamped if stamp is not None]
        selected = max(valid, key=lambda item: item[0])[1] if valid else records[0]
        timestamp = parsed_timestamp(selected)
        raw_value = selected.get("ts_value")
        value = None if raw_value is None or str(raw_value).strip() == "" else str(raw_value)
        now = self._clock().astimezone(timezone.utc)

        if timestamp is None or timestamp > now:
            freshness = "unknown"
        elif (now - timestamp).total_seconds() > self._stale_after_seconds:
            freshness = "stale"
        else:
            freshness = "fresh"

        return {
            "value": value,
            "unit": str(selected.get("ts_unitsymbol") or "").strip(),
            "timestamp": selected.get("timestamp"),
            "freshness": freshness,
        }


def format_water_quality_answer(
    request: WaterQualityRequest,
    records: list[dict[str, Any]],
) -> str:
    if request.unsupported_location:
        return (
            f"I don't have a verified CPCB monitoring-station mapping for {request.unsupported_location}. "
            "I can't substitute another location. The supported locations are Haridwar, Kanpur, "
            "Ghazipur, Farakka, and Nabadwip."
        )

    if not records:
        return "CPCB data could not be retrieved for the requested water-quality locations."

    heading = (
        "CPCB reading comparison at the requested monitoring stations:"
        if request.comparison
        else "Latest available CPCB water-quality readings for the requested monitoring stations:"
    )
    lines = [heading]
    for result in records:
        station: Station = result["station"]
        lines.append(f"\n{station.name} (CPCB station {station.station_no}):")
        if result["unavailable"]:
            lines.append("- No verified station record is currently available in the CPCB registry.")
            continue
        for item in result["readings"]:
            code = item["parameter"]
            description = PARAMETERS[code][0]
            reading = item["reading"]
            if reading is None or reading["value"] is None:
                lines.append(f"- {description} ({code}): no reading is available from this station.")
                continue
            if reading["unit"] == "---":
                unit = " (CPCB unit field: ---)"
            else:
                unit = f" {reading['unit']}" if reading["unit"] else " (unit not supplied)"
            if reading["freshness"] == "unknown":
                timestamp_text = f"timestamp unknown (source value: {reading['timestamp'] or 'not supplied'})"
                freshness_text = "Freshness cannot be confirmed."
            else:
                timestamp = datetime.fromisoformat(reading["timestamp"].replace("Z", "+00:00"))
                timestamp_text = (
                    f"{reading['timestamp']} "
                    f"({timestamp.astimezone(timezone.utc).strftime('%d %b %Y %H:%M UTC')})"
                )
                if reading["freshness"] == "stale":
                    freshness_text = "This measurement is stale and should not be treated as current."
                else:
                    freshness_text = "This measurement is within the 90-minute display freshness window."
            lines.append(
                f"- {description} ({code}): {reading['value']}{unit}; measured {timestamp_text}. "
                f"{freshness_text} {PARAMETER_EXPLANATIONS[code]}"
            )

    lines.append(
        f"\nSource: {CPCB_SOURCE} ({CPCB_URL}). These readings apply to specific monitoring "
        "stations and measurement times, not the entire Ganga. DO, BOD, and pH alone do not "
        "determine whether water is safe to drink."
    )
    return "\n".join(lines)
