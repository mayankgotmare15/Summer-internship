"""
Integration tests for the IT Escalation Management System.
Tests tiered escalation (L1 -> L2 -> L3 -> Manager), SLA calculation,
multi-bounce dispute auto-escalation, and RBAC guards.
"""

from fastapi.testclient import TestClient

from src.database.db import init_db
from src.serving.app import app

client = TestClient(app)


def setup_module():
    init_db()


def test_initial_sla_and_emergency_escalation():
    # 1. Normal ticket gets SLA deadline and Level 2 if confident or Level 1 if low-conf
    res1 = client.post(
        "/predict",
        json={"text": "Please reset my domain password", "ticket_id": "test-sla-01"},
    )
    assert res1.status_code == 200

    # 2. Critical outage keyword triggers Emergency Escalation to Tier 3 directly
    res_crit = client.post(
        "/predict",
        json={
            "text": "CRITICAL OUTAGE: production database server down, all users blocked",
            "ticket_id": "test-emerg-01",
        },
    )
    assert res_crit.status_code == 200
    assert res_crit.json()["priority"] == "Critical"

    # Verify L3 backlog has this emergency ticket
    l3_headers = {"X-User-Role": "specialist_l3", "X-User-Id": "devon_vance"}
    l3_res = client.get("/api/v1/escalations/l3-backlog", headers=l3_headers)
    assert l3_res.status_code == 200
    l3_tickets = l3_res.json()
    assert any(t["id"] == "test-emerg-01" for t in l3_tickets)
    emerg_tkt = next(t for t in l3_tickets if t["id"] == "test-emerg-01")
    assert emerg_tkt["escalation_level"] == 3


def test_manual_hierarchical_escalation():
    # Ingest standard ticket
    res = client.post(
        "/predict",
        json={
            "text": "Laptop keyboard has water damage and keys are sticking",
            "ticket_id": "test-esc-02",
        },
    )
    assert res.status_code == 200

    # L2 Resolver escalates to L3 with reason
    lead_headers = {"X-User-Role": "resolver_lead", "X-User-Id": "lead_sarah"}
    esc_res = client.post(
        "/api/v1/escalations/test-esc-02/escalate",
        headers=lead_headers,
        json={
            "target_level": 3,
            "reason": "Motherboard short circuit requires senior hardware lab diagnostic",
        },
    )
    assert esc_res.status_code == 200
    data = esc_res.json()
    assert data["status"] == "success"
    assert data["ticket"]["escalation_level"] == 3
    assert "Motherboard short circuit" in data["ticket"]["escalation_reason"]


def test_multi_bounce_dispute_auto_escalation():
    # Ingest ticket
    res = client.post(
        "/predict",
        json={
            "text": "Cannot access internal gitlab server over VPN connection",
            "ticket_id": "test-bounce-03",
        },
    )
    assert res.status_code == 200

    lead_headers = {"X-User-Role": "resolver_lead", "X-User-Id": "lead_sarah"}

    # 1st Dispute: Bounces back to triage queue
    disp1 = client.post(
        "/api/v1/queues/test-bounce-03/dispute",
        headers=lead_headers,
        json={"reason": "Not a hardware issue, VPN belongs to IAM or DevOps"},
    )
    assert disp1.status_code == 200
    assert disp1.json()["ticket_status"] == "pending_triage"

    # 2nd Dispute: Bounces again -> Triggers multi-bounce guard and auto-escalates to Manager!
    disp2 = client.post(
        "/api/v1/queues/test-bounce-03/dispute",
        headers=lead_headers,
        json={"reason": "IAM verified credentials valid, server routing failure"},
    )
    assert disp2.status_code == 200
    data = disp2.json()
    assert data["ticket_status"] == "management_escalated"
    assert "IT Operations Management" in data["assigned_team"]

    # Verify it appears in Manager Oversight queue
    mgr_headers = {"X-User-Role": "manager", "X-User-Id": "manager_dave"}
    oversight_res = client.get("/api/v1/escalations/manager-oversight", headers=mgr_headers)
    assert oversight_res.status_code == 200
    mgr_tickets = oversight_res.json()
    assert any(t["id"] == "test-bounce-03" for t in mgr_tickets)


def test_sla_check_endpoint():
    mgr_headers = {"X-User-Role": "manager", "X-User-Id": "manager_dave"}
    sla_res = client.post("/api/v1/escalations/check-sla", headers=mgr_headers)
    assert sla_res.status_code == 200
    data = sla_res.json()
    assert "scanned_count" in data
    assert "checked_at" in data
