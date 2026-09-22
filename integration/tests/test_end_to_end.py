"""End-to-End integration tests for Ganga AI Mascot system."""

import pytest
from fastapi.testclient import TestClient
from integration.server import app


def test_end_to_end_integration_ask_mock():
    client = TestClient(app)
    
    response = client.post("/api/integration/ask", json={
        "question": "What is Aviral Dhara?",
        "language": "hi"
    })

    assert response.status_code == 200
    data = response.json()

    assert "answer" in data
    assert data["answer"] != ""
    assert data["mode"] in ("grounded", "insufficient-evidence", "current-info-fallback")
    assert "citations" in data
    assert "emotion" in data
    assert "gesture" in data
    assert data["language"] == "hi"


def test_end_to_end_out_of_scope_query():
    client = TestClient(app)
    
    response = client.post("/api/integration/ask", json={
        "question": "What is the population of Mars?",
        "language": "en"
    })

    assert response.status_code == 200
    data = response.json()

    assert data["mode"] in ("insufficient-evidence", "grounded")
    assert data["emotion"] in ("thinking", "neutral")
