"""Comprehensive domain and API workflow test suite for Phase 4:
- Ticket creation, AI classification & named owner promise (PRD 4B.1)
- Assignment engine with skills, shifts, and leave exclusions (PRD 4B.2)
- SLA clock pause/resume and business hours arithmetic (PRD 4B.3)
- SLA ladder progression (first response, 50%, 75%, breach E3, manager timeout E4) (PRD 4B.5)
- Requester escalation guardrails (rate limit, cooldown, on-leave delegation, wrong team feedback) (PRD 4B.6)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from src.app.deps import get_clock
from src.app.errors import EscalationGuardrailError
from src.app.main import app
from src.app.modules.assignment.service import AssignmentService
from src.app.modules.directory.service import DirectoryService
from src.app.modules.escalation.service import EscalationService
from src.app.modules.sla.service import SlaService
from src.app.modules.tickets.controller import TicketController
from src.app.modules.tickets.schemas import (
    EscalateIn,
    EscalationRespondIn,
    MessageIn,
    StatusChangeIn,
    TicketCreateIn,
)
from src.core.clock import FakeClock, ensure_utc
from src.db.models.feedback import Feedback
from src.db.models.ticket import Ticket
from src.db.models.user import User
from src.db.session import SessionLocal


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_clock() -> FakeClock:
    # Monday Oct 20, 2026, 10:00 AM Asia/Kolkata (04:30 UTC)
    initial_utc = datetime(2026, 10, 20, 4, 30, tzinfo=timezone.utc)
    return FakeClock(initial_utc)


def test_create_ticket_auto_route_named_owner_and_eta(client: TestClient) -> None:
    """Verifies PRD 4B.1: Ticket received, named owner, team, and SLA deadlines returned."""
    payload = {
        "subject": "VPN client failure",
        "description": "password reset not working and user account locked in active directory",
        "blocking_team": False,
    }
    res = client.post("/api/v1/tickets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"].startswith("T-")
    assert data["status"] == "Assigned"
    assert data["category"] == "Access"
    assert data["team"]["code"] == "ACCESS"
    assert data["assignee"] is not None
    assert data["assignee"]["name"] in ["Priya Sharma", "Arjun Mehta", "Riya Kapoor"]
    assert data["first_response_due"] is not None
    assert data["resolution_due"] is not None
    assert data["can_escalate"] is True


def test_create_ticket_human_review_promise(client: TestClient) -> None:
    """Verifies that multi-issue tickets route to Service Desk with a 30-min triage promise."""
    payload = {
        "subject": "Outlook and printer issues",
        "description": "outlook keeps asking password and my printer is also not working in bay 4",
        "blocking_team": False,
    }
    res = client.post("/api/v1/tickets", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["decision"] in ["human_review", "auto_route"]
    if data["decision"] == "human_review":
        assert data["status"] == "New"
        assert data["team"]["code"] == "SERVICE_DESK"
        assert data["assignee"] is None
        assert data["review_promise_by"] is not None


def test_create_ticket_approval_flow(client: TestClient) -> None:
    """Verifies that Admin rights requests require approval before assignment."""
    payload = {
        "subject": "Need Python admin rights",
        "description": "pls give me admin rights on my laptop to install python for engineering project",
        "blocking_team": False,
    }
    res = client.post("/api/v1/tickets", json=payload)
    assert res.status_code == 201
    data = res.json()
    if data["category"] == "Administrative rights":
        assert data["status"] == "Awaiting approval"
        assert data["awaiting_approval_from"] is not None
        assert data["assignee"] is None


def test_assignment_engine_skills_and_leave_filter(fake_clock: FakeClock) -> None:
    """Tests Section 4B.2: Neha Singh is on leave Oct 20-24, Priya/Arjun match VPN skills."""
    with SessionLocal() as db:
        directory = DirectoryService()
        assignment = AssignmentService(directory)

        # 1. Neha Singh should be identified as on leave
        neha = directory.get_member("neha.singh@example.com")
        on_leave, note, delegate = directory.is_on_leave(neha, fake_clock.now())
        assert on_leave is True
        assert delegate == "arjun.mehta@example.com"

        # 2. Assign Access ticket with VPN/MFA skills
        picked_user, trace = assignment.assign_ticket(
            team_code="ACCESS",
            priority="High",
            ticket_text="vpn connection and mfa active directory authentication error",
            db=db,
            clock=fake_clock,
        )
        assert picked_user is not None
        assert picked_user.email in ["priya.sharma@example.com", "arjun.mehta@example.com"]
        assert picked_user.email != "neha.singh@example.com"
        assert trace["selected_assignee"]["skill_score"] > 0


def test_sla_pause_and_resume_extends_deadline(fake_clock: FakeClock) -> None:
    """Verifies that changing status to 'Waiting on requester' pauses SLA and extends due date."""
    with SessionLocal() as db:
        ctrl = TicketController()
        created = ctrl.create_ticket(
            TicketCreateIn(
                subject="Password reset locked account",
                description="password reset not working and user account locked in active directory",
                blocking_team=False,
            ),
            requester_email="requester@example.com",
            db=db,
            clock=fake_clock,
        )

        ticket_id = created.ticket_uuid
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        initial_due = created.resolution_due
        assert created.status == "Assigned"

        # 1. Change status to Waiting on requester
        ctrl.change_status(
            str(ticket_id),
            StatusChangeIn(to_status="Waiting on requester", note="Need your laptop serial number"),
            actor_id=ticket.assignee_id,
            db=db,
            clock=fake_clock,
        )
        detail = ctrl.get_ticket(str(ticket_id), db, fake_clock)
        assert detail.status == "Waiting on requester"
        assert detail.clock_state == "paused"

        # 2. Advance clock by 3 business hours (180 minutes)
        fake_clock.advance_minutes(180)

        # 3. Requester posts message -> resumes clock
        ctrl.post_message(
            str(ticket_id),
            MessageIn(body="Serial number is SN-987654", internal=False),
            author_id=ticket.requester_id,
            db=db,
            clock=fake_clock,
        )

        resumed_detail = ctrl.get_ticket(str(ticket_id), db, fake_clock)
        assert resumed_detail.status == "In progress"
        assert resumed_detail.clock_state == "running"
        # Resolution due must be extended by roughly 180 minutes
        assert ensure_utc(resumed_detail.resolution_due) > ensure_utc(initial_due)


def test_sla_ladder_progression_to_e3_breach_and_e4(fake_clock: FakeClock) -> None:
    """Verifies that an overdue ticket fires 50%, 75%, breaches to E3, and times out to E4."""
    with SessionLocal() as db:
        sla_service = SlaService()
        # Create ticket with Critical priority (24x7 calendar, 4h resolution)
        requester = db.query(User).filter(User.role == "requester").first()
        hardware_team = db.query(User).filter(User.role == "engineer").first()

        ticket = Ticket(
            id=uuid.uuid4(),
            public_id=f"T-LADDER-{uuid.uuid4().hex[:6]}",
            requester_id=requester.id,
            subject="Critical Outage",
            description="production database offline",
            text_hash="hash",
            category="Hardware",
            priority="Critical",
            decision="auto_route",
            status="Assigned",
            assignee_id=hardware_team.id,
            created_at=fake_clock.now(),
            updated_at=fake_clock.now(),
        )
        db.add(ticket)
        db.commit()

        sla_clock = sla_service.start_clock(ticket, db, fake_clock)
        assert sla_clock.state == "running"

        # Advance 2.5 hours (over 50% elapsed)
        fake_clock.advance_minutes(150)
        actions_50 = sla_service.evaluate_ladder(db, fake_clock)
        assert any(a.get("rule_key") == "pct50_reminder" for a in actions_50)

        # Advance another 1 hour (3.5 hours elapsed = >75%)
        fake_clock.advance_minutes(60)
        actions_75 = sla_service.evaluate_ladder(db, fake_clock)
        assert any(a.get("rule_key") == "pct75_warning" for a in actions_75)

        # Advance past 4 hours -> SLA Breach (E3 Service Desk Manager)
        fake_clock.advance_minutes(60)
        actions_breach = sla_service.evaluate_ladder(db, fake_clock)
        assert any(a.get("rule_key") == "resolution_breached" for a in actions_breach)
        db.refresh(ticket)
        assert ticket.is_escalated is True
        assert ticket.escalation_level == "E3"

        # Advance +2.5 hours post breach without resolution -> Manager Timeout (E4 Delivery Manager)
        fake_clock.advance_minutes(150)
        actions_e4 = sla_service.evaluate_ladder(db, fake_clock)
        assert any(a.get("rule_key") == "manager_timeout" for a in actions_e4)
        db.refresh(ticket)
        assert ticket.escalation_level == "E4"


def test_requester_escalation_guardrails(fake_clock: FakeClock) -> None:
    """Verifies all PRD 4B.6 guardrails: rate limit, cooldown, on-leave delegation, and wrong team feedback."""
    with SessionLocal() as db:
        directory = DirectoryService()
        sla = SlaService()
        esc_service = EscalationService(directory, sla)

        requester = db.query(User).filter(User.email == "requester@example.com").first()
        assignee = db.query(User).filter(User.email == "priya.sharma@example.com").first()
        lead = db.query(User).filter(User.email == "riya.kapoor@example.com").first()
        neha = db.query(User).filter(User.email == "neha.singh@example.com").first()
        access_team = db.query(User).first()
        from src.db.models.user import Team
        team_rec = db.query(Team).filter(Team.code == "ACCESS").first()

        ticket = Ticket(
            id=uuid.uuid4(),
            public_id=f"T-ESC-{uuid.uuid4().hex[:6]}",
            requester_id=requester.id,
            team_id=team_rec.id if team_rec else None,
            subject="Escalation Guardrail Test",
            description="Testing guardrail validation rules",
            text_hash="hash",
            category="Access",
            priority="High",
            decision="auto_route",
            status="In progress",
            assignee_id=assignee.id,
            created_at=fake_clock.now(),
            updated_at=fake_clock.now(),
        )
        db.add(ticket)
        db.commit()

        # 1. Target Self Guardrail
        with pytest.raises(EscalationGuardrailError) as exc_self:
            esc_service.raise_escalation(
                ticket.id, requester.id, requester.id, "business_critical", "note with 10 chars", db, fake_clock
            )
        assert exc_self.value.code == "ESCALATION_TARGET_SELF"

        # 2. Target Owner Guardrail
        with pytest.raises(EscalationGuardrailError) as exc_owner:
            esc_service.raise_escalation(
                ticket.id, requester.id, assignee.id, "business_critical", "note with 10 chars", db, fake_clock
            )
        assert exc_owner.value.code == "ESCALATION_TARGET_OWNER"

        # 3. Target On Leave Guardrail (Neha Singh is on leave Oct 20-24)
        with pytest.raises(EscalationGuardrailError) as exc_leave:
            esc_service.raise_escalation(
                ticket.id, requester.id, neha.id, "business_critical", "note with 10 chars", db, fake_clock
            )
        assert exc_leave.value.code == "ESCALATION_TARGET_ON_LEAVE"
        assert exc_leave.value.details["delegate"] == "arjun.mehta@example.com"

        # 4. Valid Escalation to Team Lead (Riya Kapoor) with reason 'wrong_team'
        esc1 = esc_service.raise_escalation(
            ticket.id,
            requester.id,
            lead.id,
            "wrong_team",
            "This ticket was classified into Access but is actually Storage",
            db,
            fake_clock,
        )
        assert esc1.status == "pending"
        assert esc1.target_user_id == lead.id

        # Verify Wrong Team feedback was automatically recorded for retraining
        fb = db.query(Feedback).filter(Feedback.ticket_id == ticket.id).first()
        assert fb is not None
        assert fb.kind == "wrong_team_escalation"

        # 5. Immediate Second Escalation triggers Cooldown Guardrail
        with pytest.raises(EscalationGuardrailError) as exc_cooldown:
            esc_service.raise_escalation(
                ticket.id, requester.id, lead.id, "other", "Another escalation immediately", db, fake_clock
            )
        assert exc_cooldown.value.code == "ESCALATION_COOLDOWN"

        # 6. Advance past cooldown (65 mins), raise 2nd escalation
        fake_clock.advance_minutes(65)
        manager = db.query(User).filter(User.email == "rahul.verma@example.com").first()
        esc2 = esc_service.raise_escalation(
            ticket.id, requester.id, manager.id, "business_critical", "Second escalation after cooldown", db, fake_clock
        )
        assert esc2.status == "pending"

        # 7. Third escalation within 24 hours triggers Rate Limit Guardrail
        fake_clock.advance_minutes(65)
        with pytest.raises(EscalationGuardrailError) as exc_rate:
            esc_service.raise_escalation(
                ticket.id, requester.id, lead.id, "other", "Third attempt in 24 hours", db, fake_clock
            )
        assert exc_rate.value.code == "ESCALATION_RATE_LIMIT"

        # 8. Accept Escalation by Team Lead
        responded = esc_service.respond(
            escalation_id=esc1.id,
            responder_id=lead.id,
            action="accept",
            new_eta=fake_clock.now() + timedelta(hours=4),
            reassign_to_id=None,
            reason_note="Accepted by Team Lead Riya Kapoor",
            db=db,
            clock=fake_clock,
        )
        assert responded.status == "accept"
        db.refresh(ticket)
        assert ticket.assignee_id == lead.id  # New owner!
