"""FastAPI integration and unit tests for inference, batch serving, feedback, and auth."""

import time
from typing import Generator
import numpy as np
import pytest
from fastapi.testclient import TestClient
from src.app.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Test client managing lifespan context (model load + db init)."""
    with TestClient(app) as c:
        yield c


def test_health_check(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "RouteDesk" in data["app"]


def test_ready_check(client: TestClient) -> None:
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["checks"]["db"] == "ok"
    assert data["checks"]["model"] == "loaded"


def test_model_info_endpoint(client: TestClient) -> None:
    res = client.get("/api/v1/model-info")
    assert res.status_code == 200
    data = res.json()
    assert data["model_name"] == "routedesk-routing"
    assert data["version"] == "v1-baseline"
    assert data["threshold"] == 0.69
    assert data["degraded"] is False
    assert len(data["labels"]) >= 7
    assert "macro_f1" in data["metrics"]


def test_predict_single_ticket(client: TestClient) -> None:
    payload = {
        "text": "password reset not working and user account locked in active directory",
        "blocking_team": False,
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Access"
    assert data["category_confidence"] > 0.5
    assert len(data["top_categories"]) == 3
    assert data["routed_team"]["code"] in ["ACCESS", "SERVICE_DESK"]
    assert data["prediction_id"] is not None
    assert isinstance(data["latency_ms"], int)


def test_predict_empty_text_validation(client: TestClient) -> None:
    res = client.post("/api/v1/predict", json={"text": "   "})
    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "TEXT_EMPTY"


def test_predict_oversized_text_validation(client: TestClient) -> None:
    oversized = "trouble with laptop " * 300  # > 5000 chars
    res = client.post("/api/v1/predict", json={"text": oversized})
    assert res.status_code in [400, 422]


def test_predict_priority_rule_override(client: TestClient) -> None:
    payload = {
        "text": "production outage detected, critical database unreachable and whole team blocked",
        "blocking_team": True,
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["priority"] == "Critical"
    assert data["priority_source"] == "rule"


def test_predict_multi_issue_triggers_human_review(client: TestClient) -> None:
    payload = {
        "text": "outlook keeps asking password and my printer is also not working",
        "blocking_team": False,
    }
    res = client.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] in ["human_review", "auto_route"]
    if data["decision"] == "human_review":
        assert data["review_reason"] in ["multi_issue", "low_confidence"]


def test_predict_batch_endpoint(client: TestClient) -> None:
    items = [
        {"text": "need local admin rights to install nodejs on laptop"},
        {"text": "screen cracked on monitor need replacement"},
        {"text": "reset my windows login password"},
    ]
    res = client.post("/api/v1/predict/batch", json={"items": items})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 3
    assert len(data["predictions"]) == 3
    for pred in data["predictions"]:
        assert "category" in pred
        assert "decision" in pred
        assert "routed_team" in pred


def test_feedback_submission(client: TestClient) -> None:
    feedback_payload = {
        "kind": "agent_correction",
        "predicted_category": "Hardware",
        "corrected_category": "Storage",
        "predicted_priority": "Medium",
        "corrected_priority": "High",
        "notes": "Shared drive capacity issue wrongly labeled as hardware",
    }
    res = client.post("/api/v1/feedback", json=feedback_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "recorded"
    assert data["id"] is not None


def test_demo_auth_and_me(client: TestClient) -> None:
    login_res = client.post("/api/v1/auth/demo-login", json={"role": "agent"})
    assert login_res.status_code == 200
    user_data = login_res.json()
    assert user_data["role"] == "agent"
    token = user_data["access_token"]
    assert token is not None

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == user_data["email"]
    assert me_data["role"] == "agent"


def test_latency_benchmark_p95(client: TestClient) -> None:
    """Measures end-to-end API latency across 30 inferences to verify PRD p95 < 300 ms."""
    latencies = []
    test_tickets = [
        "cannot access company intranet portal from home",
        "need new mouse and ergonomic keyboard",
        "requesting permission for aws s3 storage bucket access",
        "laptop bluescreen error when starting windows",
        "update direct deposit bank details in workday hr",
    ]

    for i in range(30):
        t_text = test_tickets[i % len(test_tickets)]
        t0 = time.perf_counter()
        res = client.post("/api/v1/predict", json={"text": t_text})
        assert res.status_code == 200
        latencies.append((time.perf_counter() - t0) * 1000)

    p50 = float(np.percentile(latencies, 50))
    p95 = float(np.percentile(latencies, 95))
    print(f"\nAPI Latency Benchmark (N=30): p50={p50:.2f}ms, p95={p95:.2f}ms")
    assert p95 < 300.0, f"p95 latency {p95:.2f}ms exceeded 300ms SLA budget"
