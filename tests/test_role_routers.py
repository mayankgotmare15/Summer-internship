"""
Integration and security tests for role-specific routers, RBAC guards, and state transitions.
"""

from fastapi.testclient import TestClient

from src.database.db import init_db
from src.serving.app import app

client = TestClient(app)


def setup_module():
    init_db()


def test_triage_queue_and_override():
    # 1. Ingest low-confidence ticket that falls to human review
    predict_res = client.post(
        "/predict",
        json={
            "text": "Something is not right with my machine and project repo permissions",
            "ticket_id": "test-triage-01",
        },
    )
    assert predict_res.status_code == 200
    ticket_id = predict_res.json()["ticket_id"]

    # 2. Triager views triage queue
    headers = {"X-User-Role": "triager", "X-User-Id": "agent_alex"}
    queue_res = client.get("/api/v1/triage/queue", headers=headers)
    assert queue_res.status_code == 200
    queue = queue_res.json()
    assert any(t["id"] == ticket_id for t in queue)

    # 3. Triager overrides category to Hardware
    override_res = client.post(
        f"/api/v1/triage/{ticket_id}/override",
        headers=headers,
        json={"category": "Hardware", "notes": "Identified laptop screen failure"},
    )
    assert override_res.status_code == 200
    data = override_res.json()
    assert data["status"] == "success"
    assert data["assigned_team"] == "Desktop Support & Hardware Services"


def test_rbac_least_privilege_enforcement():
    # Triager tries to access administrative threshold tuning -> Expect 403 Forbidden
    triager_headers = {"X-User-Role": "triager", "X-User-Id": "agent_alex"}
    admin_attempt = client.post(
        "/api/v1/admin/threshold",
        headers=triager_headers,
        json={"new_threshold": 0.85},
    )
    assert admin_attempt.status_code == 403
    assert "Access denied" in admin_attempt.json()["detail"]


def test_resolver_lead_workflow():
    # 1. Create ticket routed to Hardware
    predict_res = client.post(
        "/predict",
        json={
            "text": "Laptop display is black and power adapter is broken",
            "ticket_id": "test-hw-02",
        },
    )
    ticket_id = predict_res.json()["ticket_id"]

    lead_headers = {"X-User-Role": "resolver_lead", "X-User-Id": "lead_sarah"}

    # 2. Check department list
    dept_res = client.get("/api/v1/queues/departments", headers=lead_headers)
    assert dept_res.status_code == 200
    assert len(dept_res.json()) > 0

    # 3. Assign ticket to engineer
    assign_res = client.patch(
        f"/api/v1/queues/{ticket_id}/assign",
        headers=lead_headers,
        json={"assigned_agent": "engineer_mike"},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_agent"] == "engineer_mike"

    # 4. Resolve ticket
    status_res = client.patch(
        f"/api/v1/queues/{ticket_id}/status",
        headers=lead_headers,
        json={"new_status": "resolved", "notes": "Replaced motherboard and adapter"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["ticket_status"] == "resolved"


def test_resolver_dispute_workflow():
    # Create ticket
    predict_res = client.post(
        "/predict",
        json={
            "text": "Need admin rights on server",
            "ticket_id": "test-dispute-03",
        },
    )
    ticket_id = predict_res.json()["ticket_id"]

    lead_headers = {"X-User-Role": "resolver_lead", "X-User-Id": "lead_sarah"}
    dispute_res = client.post(
        f"/api/v1/queues/{ticket_id}/dispute",
        headers=lead_headers,
        json={"reason": "This is an IAM security issue, not hardware."},
    )
    assert dispute_res.status_code == 200
    assert dispute_res.json()["status"] == "success"


def test_manager_analytics():
    manager_headers = {"X-User-Role": "manager", "X-User-Id": "mgr_dave"}
    kpi_res = client.get("/api/v1/analytics/kpis", headers=manager_headers)
    assert kpi_res.status_code == 200
    kpis = kpi_res.json()
    assert "auto_route_rate" in kpis
    assert "net_hours_saved_monthly" in kpis
    assert "net_cost_saved_usd" in kpis

    roi_res = client.get("/api/v1/analytics/roi-model", headers=manager_headers)
    assert roi_res.status_code == 200
    assert "volume_curve" in roi_res.json()


def test_admin_threshold_update():
    admin_headers = {"X-User-Role": "mlops_admin", "X-User-Id": "admin_elena"}
    update_res = client.post(
        "/api/v1/admin/threshold",
        headers=admin_headers,
        json={"new_threshold": 0.80},
    )
    assert update_res.status_code == 200
    assert update_res.json()["active_threshold"] == 0.80

    health_res = client.get("/api/v1/admin/model-health", headers=admin_headers)
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "operational"
