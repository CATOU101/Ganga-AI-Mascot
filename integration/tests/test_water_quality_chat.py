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
            ("DO", 8.1, "mg/l"),
            ("BOD", 1.2, "mg/l"),
            ("pH", 7.4, "---"),
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
    assert request.parameter_codes == ("DO", "BOD", "pH")

    service, _ = _service()
    result = service.readings(request)
    assert [station["station"].name for station in result] == [
        station.name for station in STATIONS
    ]
    assert all(len(station["readings"]) == 3 for station in result)


def test_specific_pH_query_returns_only_kanpur_pH():
    request = parse_water_quality_request("What is the pH at Kanpur?")
    assert request.station_names == ("Kanpur",)
    assert request.parameter_codes == ("pH",)
    service, _ = _service()

    readings = service.readings(request)
    assert len(readings) == 1
    assert [item["parameter"] for item in readings[0]["readings"]] == ["pH"]
    answer = format_water_quality_answer(request, readings)
    assert "Kanpur" in answer
    assert "Dissolved oxygen" not in answer
    assert "Biochemical oxygen demand" not in answer


def test_specific_location_without_parameter_returns_three_primary_readings():
    request = parse_water_quality_request("What is the water quality at Haridwar?")
    assert request.station_names == ("Haridwar",)
    assert request.parameter_codes == ("DO", "BOD", "pH")
    service, _ = _service()
    assert len(service.readings(request)[0]["readings"]) == 3


def test_bod_comparison_requests_only_two_locations_and_bod():
    request = parse_water_quality_request("Compare BOD at Haridwar and Kanpur.")
    assert request.station_names == ("Haridwar", "Kanpur")
    assert request.parameter_codes == ("BOD",)
    service, _ = _service()
    readings = service.readings(request)
    assert len(readings) == 2
    assert all([item["parameter"] for item in row["readings"]] == ["BOD"] for row in readings)


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


def test_missing_registry_station_is_reported_without_substituting_station():
    registry = [row for row in _registry() if row["station_no"] != "UK55"]
    request = parse_water_quality_request("What is the water quality at Haridwar?")
    service, _ = _service(registry=registry)
    result = service.readings(request)
    assert result[0]["station"].name == "Haridwar"
    assert result[0]["unavailable"] == "station-unverified"
    answer = format_water_quality_answer(request, result)
    assert "No verified station record" in answer


def test_missing_measurement_is_reported_as_missing_not_zero():
    request = parse_water_quality_request("What is the DO at Farakka?")
    service, _ = _service(snapshot=[])
    result = service.readings(request)
    answer = format_water_quality_answer(request, result)
    assert "no reading is available" in answer
    assert "0 mg/l" not in answer


def test_successful_source_payloads_are_cached_without_showing_cache_age_as_measurement_age():
    request = parse_water_quality_request("What is the DO at Farakka?")
    service, calls = _service()
    first = service.readings(request)
    second = service.readings(request)
    assert first == second
    assert calls == [STATIONS_URL, SNAPSHOT_URL]


def test_stale_measurement_is_labelled_and_source_timestamp_is_used():
    measured_at = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    request = parse_water_quality_request("What is the DO at Farakka?")
    service, _ = _service(snapshot=_snapshot(measured_at))
    result = service.readings(request)
    reading = result[0]["readings"][0]["reading"]
    assert reading["freshness"] == "stale"
    answer = format_water_quality_answer(request, result)
    assert "stale and should not be treated as current" in answer
    assert measured_at[:10] in answer


def test_unknown_measurement_timestamp_is_not_replaced_with_fetch_time():
    rows = _snapshot(timestamp=None)
    rows[0]["timestamp"] = "not-a-timestamp"
    request = parse_water_quality_request("What is the DO at Haridwar?")
    service, _ = _service(snapshot=rows)
    result = service.readings(request)
    answer = format_water_quality_answer(request, result)
    assert "timestamp unknown" in answer
    assert "Freshness cannot be confirmed" in answer


def test_null_measurement_value_is_reported_as_unavailable():
    rows = _snapshot()
    rows[0]["ts_value"] = None
    request = parse_water_quality_request("What is the DO at Haridwar?")
    service, _ = _service(snapshot=rows)
    answer = format_water_quality_answer(request, service.readings(request))
    assert "no reading is available" in answer


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
    assert "Kanpur" in result.answer
    assert "CPCB" in result.answer
    assert not brain.called


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


def test_existing_chat_endpoint_returns_live_data_as_an_ordinary_answer(monkeypatch):
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
    assert "Kanpur" in payload["answer"]
    assert "CPCB" in payload["answer"]
    assert payload["citations"][0]["source"] == "CPCB Real-Time Water Quality Monitoring System"
