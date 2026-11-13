"""CPCB live water-quality lookup for conversational responses."""

from __future__ import annotations

import json
import logging
import math
import re
import ssl
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

logger = logging.getLogger("integration.water_quality")

STATIONS_URL = "https://rtwqmsdb1.cpcb.gov.in/data/internet/stations/stations.json"
SNAPSHOT_URL = "https://rtwqmsdb1.cpcb.gov.in/data/internet/layers/10/index.json"
CPCB_SOURCE = "CPCB Real-Time Water Quality Monitoring System"
CPCB_URL = "https://rtwqmsdb1.cpcb.gov.in/#/"
CPCB_BATHING_CRITERIA_URL = "https://cpcb.nic.in/wqm/Designated_Best_Use_Water_Quality_Criteria.pdf"
CWC_FLOOD_PORTAL_URL = "https://ffs.india-water.gov.in/"
CWC_THRESHOLDS_REFERENCE_URL = "https://cwc.gov.in/sites/default/files/sopapril2025.pdf"
CPCB_CLASS_B_CRITERIA = {
    "pH": "6.5–8.5",
    "BOD": "≤3 mg/L (5-day, 20°C; Class B organized outdoor bathing)",
    "DO": "≥5 mg/L (Class B organized outdoor bathing)",
}
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
    "pH": ("pH", ()),
    "BOD": ("Biochemical oxygen demand", ("biochemical oxygen demand",)),
    "DO": ("Dissolved oxygen", ("dissolved oxygen",)),
    # Verified live layer-10 fields: S / River Stage / m and Depth / Depth / m.
    "S": ("River stage", ("river stage", "water level", "river level")),
    "Depth": ("Depth", ("water depth", "river depth")),
}

QUALITY_PARAMETER_CODES = ("pH", "BOD", "DO")
LEVEL_PARAMETER_CODES = ("S", "Depth")

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
    include_quality: bool = True
    include_water_level: bool = False


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
        re.search(r"(?<!\w)DO(?!\w)", text, re.IGNORECASE) is not None
        or do_context is not None
        or any(
            _contains_phrase(lower, alias)
            for _, aliases in PARAMETERS.values()
            for alias in aliases
        )
        or _contains_phrase(lower, "ph")
    )


def _has_water_level_intent(text: str) -> bool:
    lower = text.casefold()
    return any(
        _contains_phrase(lower, phrase)
        for phrase in (
            "water level", "river stage", "river level", "water depth", "river depth", "how deep",
            "जल स्तर", "पानी का स्तर", "नदी का स्तर", "जल की गहराई", "पानी की गहराई",
        )
    ) or bool(re.search(r"(?<!\w)depth(?!\w)", lower))
def is_water_quality_query(question: str) -> bool:
    """Recognize CPCB live water-quality, river-stage, or depth requests."""
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

    has_level_intent = _has_water_level_intent(question)
    asks_definition = re.search(
        r"\b(?:what does .+ mean|what is (?:a |the )?(?:water level|river stage|water depth|depth)|"
        r"define .*(?:water level|river stage|water depth|depth))\b",
        text,
    ) is not None
    if has_level_intent and asks_definition and not (has_live_intent or has_station or has_ganga_context):
        return False
    if has_level_intent:
        return True

    return (
        has_quality_phrase
        or (has_station and _is_parameter_query(question))
        or (has_live_intent and has_ganga_context and _is_parameter_query(question))
    )


def parse_water_quality_request(question: str) -> WaterQualityRequest:
    """Classify requested tables and locations; absent a location, use all five stations."""
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

    include_water_level = _has_water_level_intent(question)
    mentions_quality_parameter = (
        re.search(r"(?<!\w)DO(?!\w)", question) is not None
        or _contains_phrase(text, "bod")
        or _contains_phrase(text, "ph")
        or any(
            _contains_phrase(text, alias)
            for code in QUALITY_PARAMETER_CODES
            for alias in PARAMETERS[code][1]
        )
    )
    has_quality_phrase = any(
        phrase in text
        for phrase in (
            "water quality", "water-quality", "जल गुणवत्ता", "पानी की गुणवत्ता", "गंगा का पानी", "गंगा के पानी"
        )
    )
    include_quality = has_quality_phrase or mentions_quality_parameter or not include_water_level
    requested_parameters = (
        (QUALITY_PARAMETER_CODES if include_quality else ())
        + (LEVEL_PARAMETER_CODES if include_water_level else ())
    )
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
        include_quality,
        include_water_level,
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
    if re.match(r"^(?:all|each|every)\s+(?:(?:five|5)\s+)?(?:configured\s+)?(?:stations?|locations?)\b", candidate):
        return None
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
    ssl_context = None
    if url.startswith("https://"):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    try:
        kwargs = {"timeout": 10}
        if ssl_context is not None:
            kwargs["context"] = ssl_context
        with urllib.request.urlopen(request, **kwargs) as response:
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
            "method": next((
                selected.get(key) for key in (
                    "bod_method", "test_method", "measurement_method", "analysis_method", "method"
                ) if selected.get(key) not in (None, "")
            ), None),
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
        return "CPCB data could not be retrieved for the requested locations."

    if request.include_quality and request.include_water_level:
        content = "Separate water-quality and water-level/depth tables are shown below."
    elif request.include_water_level:
        content = "The CPCB river-stage and water-depth readings are shown in the table below."
    else:
        content = "The CPCB pH, BOD, and DO readings are shown in the table below."
    if request.comparison:
        content = "Comparison: " + content[0].lower() + content[1:]
    disclaimer = (
        " CPCB Class B is a bathing-use benchmark; pH, BOD, and DO alone do not establish overall water safety or suitability."
        if request.include_quality else ""
    )
    return (
        f"{content} Source: {CPCB_SOURCE} ({CPCB_URL}). Measurements apply to their named "
        f"stations and timestamps, not the whole Ganga.{disclaimer}"
    )


def _localized_table_copy(language: str) -> dict[str, str]:
    translations = {
        "en": {"quality": "Water quality", "level": "Water level and depth", "station": "Station", "stage": "River stage (m)", "depth": "Depth (m)", "fresh": "Fresh", "stale": "Stale", "unknown": "Freshness unknown", "unavailable": "Unavailable", "stale_reading": "Stale reading", "meets": "Meets Class B", "outside": "Outside Class B"},
        "hi": {"quality": "जल गुणवत्ता", "level": "जल स्तर और गहराई", "station": "स्टेशन", "stage": "नदी का स्तर (m)", "depth": "गहराई (m)", "fresh": "ताज़ा", "stale": "पुराना", "unknown": "ताज़गी अज्ञात", "unavailable": "अनुपलब्ध", "stale_reading": "पुरानी रीडिंग", "meets": "कक्षा B मानदंड पूरा", "outside": "कक्षा B मानदंड से बाहर"},
        "kn": {"quality": "ನೀರಿನ ಗುಣಮಟ್ಟ", "level": "ನೀರಿನ ಮಟ್ಟ ಮತ್ತು ಆಳ", "station": "ಕೇಂದ್ರ", "stage": "ನದಿಯ ಮಟ್ಟ (m)", "depth": "ಆಳ (m)", "fresh": "ತಾಜಾ", "stale": "ಹಳೆಯದು", "unknown": "ತಾಜಾತನ ತಿಳಿದಿಲ್ಲ", "unavailable": "ಲಭ್ಯವಿಲ್ಲ", "stale_reading": "ಹಳೆಯ ಓದು", "meets": "Class B ಮಾನದಂಡ ಪೂರೈಸುತ್ತದೆ", "outside": "Class B ಮಾನದಂಡದ ಹೊರಗೆ"},
        "ta": {"quality": "நீரின் தரம்", "level": "நீர்மட்டம் மற்றும் ஆழம்", "station": "நிலையம்", "stage": "ஆற்றின் நீர்மட்டம் (m)", "depth": "ஆழம் (m)", "fresh": "புதியது", "stale": "பழையது", "unknown": "புதுமை தெரியவில்லை", "unavailable": "கிடைக்கவில்லை", "stale_reading": "பழைய அளவீடு", "meets": "Class B அளவுகோலைப் பூர்த்தி செய்கிறது", "outside": "Class B அளவுகோலுக்கு வெளியே"},
        "te": {"quality": "నీటి నాణ్యత", "level": "నీటి మట్టం మరియు లోతు", "station": "కేంద్రం", "stage": "నది మట్టం (m)", "depth": "లోతు (m)", "fresh": "తాజా", "stale": "పాతది", "unknown": "తాజాదనం తెలియదు", "unavailable": "అందుబాటులో లేదు", "stale_reading": "పాత కొలత", "meets": "Class B ప్రమాణాన్ని చేరింది", "outside": "Class B ప్రమాణం వెలుపల"},
        "bn": {"quality": "জলের গুণমান", "level": "জলের স্তর ও গভীরতা", "station": "কেন্দ্র", "stage": "নদীর স্তর (m)", "depth": "গভীরতা (m)", "fresh": "সাম্প্রতিক", "stale": "পুরনো", "unknown": "সময় অজানা", "unavailable": "অনুপলব্ধ", "stale_reading": "পুরনো পাঠ", "meets": "Class B মানদণ্ড পূরণ", "outside": "Class B মানদণ্ডের বাইরে"},
        "mr": {"quality": "पाण्याची गुणवत्ता", "level": "पाण्याची पातळी आणि खोली", "station": "केंद्र", "stage": "नदीची पातळी (m)", "depth": "खोली (m)", "fresh": "ताजे", "stale": "जुने", "unknown": "वेळ अज्ञात", "unavailable": "उपलब्ध नाही", "stale_reading": "जुने मापन", "meets": "Class B निकष पूर्ण", "outside": "Class B निकषाबाहेर"},
        "gu": {"quality": "પાણીની ગુણવત્તા", "level": "પાણીનું સ્તર અને ઊંડાઈ", "station": "કેન્દ્ર", "stage": "નદીનું સ્તર (m)", "depth": "ઊંડાઈ (m)", "fresh": "તાજું", "stale": "જૂનું", "unknown": "સમય અજ્ઞાત", "unavailable": "ઉપલબ્ધ નથી", "stale_reading": "જૂનું માપન", "meets": "Class B માપદંડ પૂર્ણ", "outside": "Class B માપદંડ બહાર"},
        "ml": {"quality": "ജലഗുണനിലവാരം", "level": "ജലനിരപ്പും ആഴവും", "station": "കേന്ദ്രം", "stage": "നദിനിരപ്പ് (m)", "depth": "ആഴം (m)", "fresh": "പുതിയത്", "stale": "പഴയത്", "unknown": "സമയം അറിയില്ല", "unavailable": "ലഭ്യമല്ല", "stale_reading": "പഴയ അളവ്", "meets": "Class B മാനദണ്ഡം പാലിക്കുന്നു", "outside": "Class B മാനദണ്ഡത്തിന് പുറത്ത്"},
        "pa": {"quality": "ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ", "level": "ਪਾਣੀ ਦਾ ਪੱਧਰ ਅਤੇ ਡੂੰਘਾਈ", "station": "ਕੇਂਦਰ", "stage": "ਦਰਿਆ ਦਾ ਪੱਧਰ (m)", "depth": "ਡੂੰਘਾਈ (m)", "fresh": "ਤਾਜ਼ਾ", "stale": "ਪੁਰਾਣਾ", "unknown": "ਸਮਾਂ ਅਣਜਾਣ", "unavailable": "ਉਪਲਬਧ ਨਹੀਂ", "stale_reading": "ਪੁਰਾਣੀ ਰੀਡਿੰਗ", "meets": "Class B ਮਾਪਦੰਡ ਪੂਰਾ", "outside": "Class B ਮਾਪਦੰਡ ਤੋਂ ਬਾਹਰ"},
        "ur": {"quality": "پانی کا معیار", "level": "پانی کی سطح اور گہرائی", "station": "مرکز", "stage": "دریا کی سطح (m)", "depth": "گہرائی (m)", "fresh": "تازہ", "stale": "پرانا", "unknown": "وقت نامعلوم", "unavailable": "دستیاب نہیں", "stale_reading": "پرانی پیمائش", "meets": "Class B معیار پر پورا", "outside": "Class B معیار سے باہر"},
        "or": {"quality": "ଜଳର ଗୁଣବତ୍ତା", "level": "ଜଳସ୍ତର ଓ ଗଭୀରତା", "station": "କେନ୍ଦ୍ର", "stage": "ନଦୀ ସ୍ତର (m)", "depth": "ଗଭୀରତା (m)", "fresh": "ନୂତନ", "stale": "ପୁରୁଣା", "unknown": "ସମୟ ଅଜଣା", "unavailable": "ଉପଲବ୍ଧ ନାହିଁ", "stale_reading": "ପୁରୁଣା ମାପ", "meets": "Class B ମାନଦଣ୍ଡ ପୂରଣ", "outside": "Class B ମାନଦଣ୍ଡ ବାହାରେ"},
        "as": {"quality": "পানীৰ গুণাগুণ", "level": "পানীৰ স্তৰ আৰু গভীৰতা", "station": "কেন্দ্ৰ", "stage": "নদীৰ স্তৰ (m)", "depth": "গভীৰতা (m)", "fresh": "শেহতীয়া", "stale": "পুৰণি", "unknown": "সময় অজ্ঞাত", "unavailable": "উপলব্ধ নহয়", "stale_reading": "পুৰণি পাঠ", "meets": "Class B মানদণ্ড পূৰণ", "outside": "Class B মানদণ্ডৰ বাহিৰত"},
    }
    copy = translations.get(language, translations["en"]).copy()
    copy["status_prefix"] = _STATUS_PREFIX.get(language, "Status")
    return copy


_STATUS_PREFIX = {
    "en": "Status", "hi": "स्थिति", "kn": "ಸ್ಥಿತಿ", "ta": "நிலை",
    "te": "స్థితి", "bn": "অবস্থা", "mr": "स्थिती", "gu": "સ્થિતિ",
    "ml": "നില", "pa": "ਸਥਿਤੀ", "ur": "حالت", "or": "ସ୍ଥିତି", "as": "অৱস্থা",
}


def _reading_status(code: str, reading: dict[str, Any] | None) -> str:
    """Return a compact screening label; the table note carries benchmark details."""
    if reading is None or reading.get("value") is None:
        return "Unavailable"
    if reading.get("freshness") == "stale":
        return "Stale reading"
    if reading.get("freshness") != "fresh":
        return "Unavailable"
    if code not in CPCB_CLASS_B_CRITERIA:
        return "Unavailable"
    if code == "BOD":
        method = str(reading.get("method") or "").casefold()
        has_5_day_basis = bool(re.search(r"\b5\s*(?:-| )?days?\b|\b5d\b", method))
        has_20_c_basis = bool(re.search(r"\b20\s*(?:°\s*)?c\b|\b20\s*degrees?\s*c\b", method))
        if not (has_5_day_basis and has_20_c_basis):
            return "Unavailable"
    unit = str(reading.get("unit", "")).strip().casefold()
    if code == "pH":
        valid_unit = unit in {"", "---", "ph"}
    else:
        valid_unit = unit in {"mg/l", "mg/litre", "mg/liter", "mg l-1", "mg·l⁻¹"}
    try:
        value = float(str(reading["value"]).strip())
    except (KeyError, TypeError, ValueError):
        return "Unavailable"
    if not valid_unit or not math.isfinite(value):
        return "Unavailable"
    meets_criterion = (
        6.5 <= value <= 8.5 if code == "pH"
        else value <= 3.0 if code == "BOD"
        else value >= 5.0
    )
    return "Meets Class B" if meets_criterion else "Outside Class B"


def _table_cell(code: str, reading: dict[str, Any] | None, copy: dict[str, str]) -> str:
    if reading is None or reading.get("value") is None:
        value = "N/A"
    else:
        unit = reading.get("unit", "")
        if unit == "---":
            value = f"{reading['value']} (unitless)"
        elif unit:
            value = f"{reading['value']} {unit}"
        else:
            value = f"{reading['value']} (unit unavailable)"
    raw_timestamp = reading.get("timestamp") if reading else None
    timestamp_text = "Time unavailable"
    if isinstance(raw_timestamp, str) and raw_timestamp.strip():
        try:
            parsed = datetime.fromisoformat(raw_timestamp.strip().replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                timestamp_text = parsed.astimezone(timezone.utc).astimezone(
                    timezone(timedelta(hours=5, minutes=30))
                ).strftime("%d %b %Y, %H:%M IST")
        except ValueError:
            pass
    status = _reading_status(code, reading)
    status_key = {"Unavailable": "unavailable", "Stale reading": "stale_reading", "Meets Class B": "meets", "Outside Class B": "outside"}.get(status)
    if status_key:
        status = copy.get(status_key, status)
    return f"{value}\n{timestamp_text}\n{copy.get('status_prefix', 'Status')}: {status}"


def build_water_data_tables(
    request: WaterQualityRequest,
    records: list[dict[str, Any]],
    language: str = "en",
) -> list[dict[str, Any]]:
    """Build separate in-chat table payloads from verified CPCB station readings."""
    if request.unsupported_location or not records:
        return []
    copy = _localized_table_copy(language)
    by_station = {}
    for result in records:
        by_station[result["station"].name] = (
            {item["parameter"]: item["reading"] for item in result.get("readings", [])}
            if not result.get("unavailable") else {}
        )

    tables = []
    for include, code_set, title_key in (
        (request.include_quality, QUALITY_PARAMETER_CODES, "quality"),
        (request.include_water_level, LEVEL_PARAMETER_CODES, "level"),
    ):
        if not include:
            continue
        if title_key == "quality":
            columns = [copy["station"], "pH", "BOD", "DO"]
        else:
            columns = [copy["station"], copy["stage"], copy["depth"]]
        rows = []
        for result in records:
            station = result["station"]
            station_readings = by_station.get(station.name, {})
            rows.append([
                f"{station.name} ({station.station_no})",
                *[_table_cell(code, station_readings.get(code), copy) for code in code_set],
            ])
        tables.append({
            "title": copy[title_key],
            "columns": columns,
            "rows": rows,
            "source": (
                f"{CPCB_SOURCE} ({CPCB_URL}). Class B is an organized outdoor-bathing screen: "
                f"pH 6.5–8.5; DO ≥5 mg/L; BOD ≤3 mg/L (5-day, 20°C) ({CPCB_BATHING_CRITERIA_URL}). "
                "These three parameters do not determine overall water safety or suitability. "
                "BOD status is unavailable when its test method is unknown."
                if title_key == "quality" else
                f"{CPCB_SOURCE} ({CPCB_URL}). CWC warning/danger status is unavailable: no exact "
                f"gauge match and current thresholds are verified ({CWC_FLOOD_PORTAL_URL}; "
                f"station-specific reference: {CWC_THRESHOLDS_REFERENCE_URL}). CPCB Depth is a "
                "separate measured field, not derived from river stage; no depth threshold is available."
            ),
        })
    return tables
