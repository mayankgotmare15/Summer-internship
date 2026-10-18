"""
API tests for FastAPI endpoints using TestClient.
"""

from fastapi.testclient import TestClient
from src.serving.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_model_info_endpoint():
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "threshold" in data
    assert "categories" in data
    assert len(data["categories"]) > 0


def test_predict_endpoint_valid():
    payload = {
        "text": "My laptop monitor won't turn on and screen is completely black.",
        "ticket_id": "test-tkt-101"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == "test-tkt-101"
    assert "category" in data
    assert "category_confidence" in data
    assert "decision" in data
    assert data["decision"] in ["auto_route", "human_review"]
    assert "routed_team" in data


def test_predict_endpoint_empty_text():
    payload = {"text": "   "}
    response = client.post("/predict", json=payload)
    # Pydantic or app validation will reject empty/short text with 400 or 422
    assert response.status_code in [400, 422]


def test_predict_endpoint_oversized_text():
    # 5,001 characters should trigger Pydantic max_length=5000 validation error (DoS protection)
    payload = {"text": "a" * 5001}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_batch_endpoint():
    payload = {
        "tickets": [
            {"text": "Password reset needed for Active Directory account", "ticket_id": "b-1"},
            {"text": "Requesting admin rights to install Docker Desktop", "ticket_id": "b-2"},
        ]
    }
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert len(data["predictions"]) == 2


def test_feedback_endpoint():
    payload = {
        "ticket_id": "test-tkt-101",
        "predicted_category": "Miscellaneous",
        "corrected_category": "Hardware",
        "agent_id": "agent-007",
        "notes": "User clearly specified laptop screen failure."
    }
    response = client.post("/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
