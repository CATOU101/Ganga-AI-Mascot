"""End-to-End integration tests for Ganga AI Mascot system."""

import pytest
from fastapi.testclient import TestClient
from integration.server import app


def test_end_to_end_integration_ask_mock():
    client = TestClient(app)
    
    response = client.post("/api/integration/ask", json={
        "question": "What is Aviral Dhara?",
        "input_language": "en",
        "output_language": "hi",
        "top_k": 5
    })

    assert response.status_code == 200
    data = response.json()

    assert "answer" in data
    assert data["answer"] != ""
    assert data["mode"] in ("grounded", "insufficient-evidence", "current-info-fallback")
    assert "citations" in data
    assert "emotion" in data
    assert "gesture" in data
    assert data["input_language"] == "en"
    assert data["output_language"] == "hi"


def test_end_to_end_out_of_scope_query():
    client = TestClient(app)
    
    response = client.post("/api/integration/ask", json={
        "question": "What is the population of Mars?",
        "input_language": "en",
        "output_language": "en",
        "top_k": 5
    })

    assert response.status_code == 200
    data = response.json()

    assert data["mode"] in ("insufficient-evidence", "grounded")
    assert data["input_language"] == "en"
    assert data["output_language"] == "en"


def test_all_four_language_combinations():
    client = TestClient(app)

    # 1. EN -> EN
    r1 = client.post("/api/integration/ask", json={
        "question": "What are the major sources of pollution in the Ganga?",
        "input_language": "en",
        "output_language": "en",
        "top_k": 5
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["input_language"] == "en"
    assert d1["output_language"] == "en"
    assert d1["mode"] == "grounded"
    assert len(d1["citations"]) > 0

    # 2. EN -> HI
    r2 = client.post("/api/integration/ask", json={
        "question": "What are the major sources of pollution in the Ganga?",
        "input_language": "en",
        "output_language": "hi",
        "top_k": 5
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["input_language"] == "en"
    assert d2["output_language"] == "hi"
    assert d2["mode"] == "grounded"
    assert len(d2["citations"]) > 0

    # 3. HI -> HI
    r3 = client.post("/api/integration/ask", json={
        "question": "अविरल धारा क्या है?",
        "input_language": "hi",
        "output_language": "hi",
        "top_k": 5
    })
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["input_language"] == "hi"
    assert d3["output_language"] == "hi"
    assert d3["mode"] == "grounded"
    assert len(d3["citations"]) > 0

    # 4. HI -> EN
    r4 = client.post("/api/integration/ask", json={
        "question": "अविरल धारा क्या है?",
        "input_language": "hi",
        "output_language": "en",
        "top_k": 5
    })
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["input_language"] == "hi"
    assert d4["output_language"] == "en"
    assert d4["mode"] == "grounded"
    assert len(d4["citations"]) > 0


def test_specific_domain_queries():
    client = TestClient(app)

    # STP query
    r_stp = client.post("/api/integration/ask", json={
        "question": "Tell me about Sewage Treatment Plants (STP) capacity.",
        "input_language": "en",
        "output_language": "en",
        "top_k": 5
    })
    assert r_stp.status_code == 200
    assert r_stp.json()["mode"] == "grounded"

    # Broad query
    r_broad = client.post("/api/integration/ask", json={
        "question": "Tell me about Ganga.",
        "input_language": "en",
        "output_language": "hi",
        "top_k": 5
    })
    assert r_broad.status_code == 200
    assert r_broad.json()["mode"] == "grounded"
