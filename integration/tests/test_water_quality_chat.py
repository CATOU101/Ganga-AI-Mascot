from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from integration.config.integration_config import IntegrationConfig
from integration.controller.conversation_controller import ConversationController
from integration.models.brain_response import BrainResponse
from integration.water_quality import (
    CPCBWaterQualityError,
    CPCBWaterQualityService,
    SNAPSHOT_URL,
    STATIONS,
    STATIONS_URL,
    build_water_data_tables,
    format_water_quality_answer,
    is_water_quality_query,
    parse_water_quality_request,
)


def _registry():
    return [
        {
            "station_id": station.station_id,
            "station_no": station.station_no,
            "station_name": f"{station.station_no}_{station.registry_name}, {station.name}",
        }
        for station in STATIONS
    ]


def _snapshot(timestamp=None):
    measured_at = timestamp or datetime.now(timezone.utc).isoformat()
    return [
        {
            "station_id": station.station_id,
            "station_no": station.station_no,
            "station_name": station.name,
            "stationparameter_no": parameter,
            "ts_value": value,
            "ts_unitsymbol": unit,
            "timestamp": measured_at,
        }
        for station in STATIONS
        for parameter, value, unit in (
            ("pH", 7.4, "---"),
            ("BOD", 1.2, "mg/l"),
            ("DO", 8.1, "mg/l"),
            ("S", 12.3, "m"),
            ("Depth", 0.8, "m"),
        )
    ]


def _service(snapshot=None, registry=None):
    payloads = {
        STATIONS_URL: _registry() if registry is None else registry,
        SNAPSHOT_URL: _snapshot() if snapshot is None else snapshot,
    }
    calls = []

    def fetch(url):
        calls.append(url)
        value = payloads[url]
        if isinstance(value, Exception):
            raise value
        return value

    return CPCBWaterQualityService(fetch_json=fetch), calls


def test_general_water_quality_query_requests_five_stations_and_three_parameters():
    query = "What is the current water quality of the Ganga?"
    assert is_water_quality_query(query)
    request = parse_water_quality_request(query)
    assert request.station_names == tuple(station.name for station in STATIONS)
    assert request.parameter_codes == ("pH", "BOD", "DO")

    service, _ = _service()
    result = service.readings(request)
    assert [station["station"].name for station in result] == [
        station.name for station in STATIONS
    ]
    assert all(len(station["readings"]) == 3 for station in result)


def test_water_quality_request_always_returns_exactly_three_quality_parameters():
    request = parse_water_quality_request("What is the pH at Kanpur?")
    assert request.station_names == ("Kanpur",)
    assert request.parameter_codes == ("pH", "BOD", "DO")
    service, _ = _service()

    readings = service.readings(request)
    assert len(readings) == 1
    assert [item["parameter"] for item in readings[0]["readings"]] == ["pH", "BOD", "DO"]
    table = build_water_data_tables(request, readings)[0]
    assert table["columns"] == ["Station", "pH", "BOD", "DO"]
    assert table["rows"][0][0] == "Kanpur (UT58)"


def test_specific_location_without_parameter_returns_three_primary_readings():
    request = parse_water_quality_request("What is the water quality at Haridwar?")
    assert request.station_names == ("Haridwar",)
    assert request.parameter_codes == ("pH", "BOD", "DO")
    service, _ = _service()
    assert len(service.readings(request)[0]["readings"]) == 3


def test_bod_comparison_selects_two_locations_and_keeps_three_quality_columns():
    request = parse_water_quality_request("Compare BOD at Haridwar and Kanpur.")
    assert request.station_names == ("Haridwar", "Kanpur")
    assert request.parameter_codes == ("pH", "BOD", "DO")
    service, _ = _service()
    readings = service.readings(request)
    assert len(readings) == 2
    assert all([item["parameter"] for item in row["readings"]] == ["pH", "BOD", "DO"] for row in readings)


@pytest.mark.parametrize(
    "question",
    [
        "What is the current water level of the Ganga?",
        "Show water depth at Ghazipur.",
        "Compare river stage and depth at Haridwar and Kanpur.",
    ],
)
def test_water_level_and_depth_queries_route_to_cpcb(question):
    assert is_water_quality_query(question)


def test_water_level_only_uses_verified_river_stage_and_depth_codes_and_units():
    request = parse_water_quality_request("What is the current water level and depth at Kanpur?")
    assert request.station_names == ("Kanpur",)
    assert request.include_quality is False
    assert request.include_water_level is True
    assert request.parameter_codes == ("S", "Depth")
    service, _ = _service()
    records = service.readings(request)
    tables = build_water_data_tables(request, records)
    assert len(tables) == 1
    assert tables[0]["columns"] == ["Station", "River stage (m)", "Depth (m)"]
    assert "12.3 m" in tables[0]["rows"][0][1]
    assert "0.8 m" in tables[0]["rows"][0][2]


def test_combined_request_returns_quality_and_level_depth_tables_separately():
    request = parse_water_quality_request(
        "Compare current water quality, water level, and depth at Haridwar and Kanpur."
    )
    assert request.station_names == ("Haridwar", "Kanpur")
    assert request.include_quality and request.include_water_level
    assert request.parameter_codes == ("pH", "BOD", "DO", "S", "Depth")
    service, _ = _service()
    tables = build_water_data_tables(request, service.readings(request))
    assert len(tables) == 2
    assert tables[0]["columns"] == ["Station", "pH", "BOD", "DO"]
    assert tables[1]["columns"] == ["Station", "River stage (m)", "Depth (m)"]
    assert all(len(table["rows"]) == 2 for table in tables)
    assert "Status: Unavailable" in tables[1]["rows"][0][1]
    assert "no exact" in tables[1]["source"]


def test_table_labels_follow_supported_output_language():
    request = parse_water_quality_request("What is the current water level at Haridwar?")
    service, _ = _service()
    table = build_water_data_tables(request, service.readings(request), language="hi")[0]
    assert table["title"] == "जल स्तर और गहराई"
    assert table["columns"] == ["स्टेशन", "नदी का स्तर (m)", "गहराई (m)"]


@pytest.mark.parametrize(
    "question",
    [
        "What does BOD mean?",
        "Explain how Ganga water quality is measured.",
        "Which parameters are tested for Ganga water quality?",
        "How does pollution monitoring work?",
    ],
)
def test_educational_and_methodological_questions_are_not_live_data_queries(question):
    assert not is_water_quality_query(question)


def test_general_water_quality_wording_routes_to_live_data():
    assert is_water_quality_query("Tell me about the Ganga water quality.")


def test_unknown_requested_location_is_not_replaced_with_all_stations():
    request = parse_water_quality_request("What is the pH at Varanasi?")
    assert request.station_names == ()
    assert request.unsupported_location == "Varanasi"
    answer = format_water_quality_answer(request, [])
    assert "can't substitute another location" in answer
    assert build_water_data_tables(request, []) == []


def test_missing_registry_station_is_reported_without_substituting_station():
    registry = [row for row in _registry() if row["station_no"] != "UK55"]
    request = parse_water_quality_request("What is the water quality at Haridwar?")
    service, _ = _service(registry=registry)
    result = service.readings(request)
    assert result[0]["station"].name == "Haridwar"
    assert result[0]["unavailable"] == "station-unverified"
    table = build_water_data_tables(request, result)[0]
    assert all(cell.splitlines()[0] == "N/A" and "Status: Unavailable" in cell for cell in table["rows"][0][1:])


def test_missing_measurement_is_reported_as_missing_not_zero():
    request = parse_water_quality_request("What is the water quality at Farakka?")
    service, _ = _service(snapshot=[])
    result = service.readings(request)
    table = build_water_data_tables(request, result)[0]
    assert all(cell.splitlines()[0] == "N/A" and cell.splitlines()[2] == "Status: Unavailable" for cell in table["rows"][0][1:])
    assert all(len(cell.splitlines()) == 3 for cell in table["rows"][0][1:])
    assert "0 mg/l" not in str(table["rows"])


def test_successful_source_payloads_are_cached_without_showing_cache_age_as_measurement_age():
    request = parse_water_quality_request("What is the DO at Farakka?")
    service, calls = _service()
    first = service.readings(request)
    second = service.readings(request)
    assert first == second
    assert calls == [STATIONS_URL, SNAPSHOT_URL]


def test_stale_measurement_is_labelled_and_source_timestamp_is_used():
    measured_at = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    request = parse_water_quality_request("What is the water quality at Farakka?")
    service, _ = _service(snapshot=_snapshot(measured_at))
    result = service.readings(request)
    reading = result[0]["readings"][0]["reading"]
    assert reading["freshness"] == "stale"
    cell = build_water_data_tables(request, result)[0]["rows"][0][3]
    assert "Stale" in cell
    assert datetime.fromisoformat(measured_at).astimezone(timezone(timedelta(hours=5, minutes=30))).strftime("%d %b %Y") in cell
    assert "Status: Stale reading" in cell


def test_unknown_measurement_timestamp_is_not_replaced_with_fetch_time():
    rows = _snapshot(timestamp=None)
    rows[0]["timestamp"] = "not-a-timestamp"
    request = parse_water_quality_request("What is the water quality at Haridwar?")
    service, _ = _service(snapshot=rows)
    result = service.readings(request)
    cell = build_water_data_tables(request, result)[0]["rows"][0][1]
    assert "Time unavailable" in cell
    assert "Status: Unavailable" in cell


def test_null_measurement_value_is_reported_as_unavailable():
    rows = _snapshot()
    rows[0]["ts_value"] = None
    request = parse_water_quality_request("What is the water quality at Haridwar?")
    service, _ = _service(snapshot=rows)
    table = build_water_data_tables(request, service.readings(request))[0]
    assert table["rows"][0][1].splitlines()[0] == "N/A"
    assert "Status: Unavailable" in table["rows"][0][1]


@pytest.mark.parametrize(
    "parameter,value,expected",
    [
        ("pH", "6.5", "Meets Class B"),
        ("pH", "8.5", "Meets Class B"),
        ("pH", "6.49", "Outside Class B"),
        ("pH", "8.51", "Outside Class B"),
        ("BOD", "3", "Unavailable"),
        ("BOD", "3.01", "Unavailable"),
        ("DO", "5", "Meets Class B"),
        ("DO", "4.99", "Outside Class B"),
    ],
)
def test_class_b_screening_status_at_and_around_thresholds(parameter, value, expected):
    from integration.water_quality import _table_cell

    cell = _table_cell(
        parameter,
        {"value": value, "unit": "---" if parameter == "pH" else "mg/l", "timestamp": "2026-11-08T13:30:00Z", "freshness": "fresh"},
        {"unknown": "Freshness unknown", "fresh": "Fresh", "stale": "Stale"},
    )
    assert cell.splitlines()[0] == (f"{value} (unitless)" if parameter == "pH" else f"{value} mg/l")
    assert f"Status: {expected}" in cell
    assert cell.splitlines()[1] == "08 Nov 2026, 19:00 IST"
    assert len(cell.splitlines()) == 3
    assert all(prefix not in cell for prefix in ("Reading:", "Timestamp:", "Source:", "Threshold/range:"))


def test_localized_cpcb_table_preserves_readings_units_timestamp_and_status_format():
    measured_at = datetime.now(timezone.utc).isoformat()
    expected_timestamp = datetime.fromisoformat(measured_at).astimezone(
        timezone(timedelta(hours=5, minutes=30))
    ).strftime("%d %b %Y, %H:%M IST")
    snapshot = _snapshot(measured_at)
    service, _ = _service(snapshot=snapshot)
    request = parse_water_quality_request("What is water quality at Kanpur?")
    table = build_water_data_tables(request, service.readings(request), "hi")[0]
    assert table["title"] == "जल गुणवत्ता"
    cells = table["rows"][0][1:]
    assert "7.4 (unitless)" in cells[0]
    assert "1.2 mg/l" in cells[1]
    assert "8.1 mg/l" in cells[2]
    assert all(expected_timestamp in cell for cell in cells)
    assert "स्थिति: कक्षा B मानदंड पूरा" in cells[0]
    assert "स्थिति: अनुपलब्ध" in cells[1]  # The CPCB feed does not supply BOD test basis.


def test_status_is_unavailable_for_unknown_units_or_non_numeric_readings():
    from integration.water_quality import _table_cell

    copy = {"unknown": "Freshness unknown", "fresh": "Fresh", "stale": "Stale"}
    for reading in (
        {"value": "5", "unit": "m", "timestamp": None},
        {"value": "sensor-error", "unit": "mg/l", "timestamp": None},
        {"value": "NaN", "unit": "mg/l", "timestamp": None},
    ):
        cell = _table_cell("DO", reading, copy)
        assert "Status: Unavailable" in cell


@pytest.mark.parametrize(
    "value,expected",
    [("3", "Meets Class B"), ("3.01", "Outside Class B")],
)
def test_bod_threshold_applies_only_with_matching_test_basis(value, expected):
    from integration.water_quality import _table_cell

    cell = _table_cell(
        "BOD",
        {
            "value": value,
            "unit": "mg/l",
            "timestamp": "2026-11-08T13:30:00Z",
            "freshness": "fresh",
            "method": "BOD 5-day, 20°C",
        },
        {"unknown": "Freshness unknown", "fresh": "Fresh", "stale": "Stale"},
    )
    assert f"Status: {expected}" in cell


def test_quality_table_cites_class_b_reference_and_limits_the_interpretation():
    request = parse_water_quality_request("What is the water quality at Kanpur?")
    service, _ = _service()
    table = build_water_data_tables(request, service.readings(request))[0]
    assert "Class B is an organized outdoor-bathing screen" in table["source"]
    assert "https://cpcb.nic.in/wqm/Designated_Best_Use_Water_Quality_Criteria.pdf" in table["source"]
    assert "do not determine overall water safety" in table["source"]


def test_upstream_failure_is_not_replaced_with_rag_answer():
    class FailingService:
        def readings(self, request):
            raise CPCBWaterQualityError("upstream timeout")

    class Brain:
        called = False

        def ask(self, *args, **kwargs):
            self.called = True
            return BrainResponse(answer="RAG fallback", input_language="en", output_language="en", language="en")

    brain = Brain()
    controller = ConversationController(
        brain_client=brain,
        config=IntegrationConfig(mock_mode=True),
        water_quality_service=FailingService(),
    )
    result = controller.process_text_question(
        "What is the current water quality of the Ganga?",
        input_language="en",
        output_language="en",
    )
    assert not brain.called
    assert result.mode == "live-water-quality-unavailable"
    assert "couldn't retrieve" in result.answer
    assert result.tables == []


def test_live_question_is_answered_in_conversation_without_calling_brain():
    class Brain:
        called = False

        def ask(self, *args, **kwargs):
            self.called = True
            return BrainResponse(answer="unexpected", input_language="en", output_language="en", language="en")

    brain = Brain()
    service, _ = _service()
    controller = ConversationController(
        brain_client=brain,
        config=IntegrationConfig(mock_mode=True),
        water_quality_service=service,
    )
    result = controller.process_text_question(
        "What is the pH at Kanpur?",
        input_language="en",
        output_language="en",
    )
    assert result.mode == "live-water-quality"
    assert "CPCB" in result.answer
    assert len(result.tables) == 1
    assert result.tables[0].columns == ["Station", "pH", "BOD", "DO"]
    assert result.tables[0].rows[0][0] == "Kanpur (UT58)"
    assert not brain.called


def test_non_english_cpcb_question_is_normalized_before_station_intent_matching(monkeypatch):
    class Brain:
        def ask(self, *args, **kwargs):
            raise AssertionError("CPCB route should handle the translated question")

    service, _ = _service()
    controller = ConversationController(
        brain_client=Brain(), config=IntegrationConfig(mock_mode=True),
        water_quality_service=service,
    )
    translated = []

    def translate(text, source, target, **_kwargs):
        translated.append((text, source, target))
        return "What is the water quality at Kanpur?"

    monkeypatch.setattr("brain.translator.translate_text", translate)
    result = controller.process_text_question(
        "கான்பூரில் நீரின் தரம் என்ன?", input_language="ta", output_language="ta"
    )
    assert result.mode == "live-water-quality"
    assert result.tables[0].rows[0][0] == "Kanpur (UT58)"
    assert translated[0] == ("கான்பூரில் நீரின் தரம் என்ன?", "ta", "en")
    assert translated[1][1:] == ("en", "ta")


def test_level_and_combined_requests_get_appropriate_response_schema():
    service, _ = _service()
    controller = ConversationController(
        brain_client=object(),
        config=IntegrationConfig(mock_mode=True),
        water_quality_service=service,
    )
    level = controller.process_text_question(
        "What is the current water level at all five stations?",
        input_language="en",
        output_language="en",
    )
    assert len(level.tables) == 1
    assert level.tables[0].columns == ["Station", "River stage (m)", "Depth (m)"]
    assert len(level.tables[0].rows) == 5

    combined_controller = ConversationController(
        brain_client=object(),
        config=IntegrationConfig(mock_mode=True),
        water_quality_service=service,
    )
    combined = combined_controller.process_text_question(
        "Compare water quality, level, and depth at Haridwar and Kanpur.",
        input_language="en",
        output_language="en",
    )
    assert len(combined.tables) == 2
    assert len(combined.tables[0].rows) == 2
    assert len(combined.tables[1].rows) == 2


def test_educational_question_continues_through_brain_client():
    class Brain:
        called_with = None

        def ask(self, question, **kwargs):
            self.called_with = question
            return BrainResponse(
                answer="BOD is biochemical oxygen demand.",
                input_language="en",
                output_language="en",
                language="en",
            )

    brain = Brain()
    service, calls = _service()
    controller = ConversationController(
        brain_client=brain,
        config=IntegrationConfig(mock_mode=True),
        water_quality_service=service,
    )
    result = controller.process_text_question(
        "What does BOD mean?",
        input_language="en",
        output_language="en",
    )
    assert result.mode == "grounded"
    assert brain.called_with == "What does BOD mean?"
    assert calls == []


def test_existing_chat_endpoint_returns_structured_live_tables(monkeypatch):
    import integration.server as server

    class Brain:
        def ask(self, *args, **kwargs):
            raise AssertionError("Live water-quality requests must not be sent to Brain.")

    class TextOnlyTTS:
        def synthesize_speech(self, *args, **kwargs):
            return None

    service, _ = _service()
    monkeypatch.setattr(
        server,
        "controller",
        ConversationController(
            brain_client=Brain(),
            config=IntegrationConfig(mock_mode=True),
            water_quality_service=service,
        ),
    )
    monkeypatch.setattr(server, "tts_adapter", TextOnlyTTS())

    response = TestClient(server.app).post(
        "/api/integration/ask",
        json={
            "question": "What is the pH at Kanpur?",
            "input_language": "en",
            "output_language": "en",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "live-water-quality"
    assert "CPCB" in payload["answer"]
    assert payload["citations"][0]["source"] == "CPCB Real-Time Water Quality Monitoring System"
    assert payload["tables"][0]["columns"] == ["Station", "pH", "BOD", "DO"]
    assert len(payload["tables"][0]["rows"]) == 1
