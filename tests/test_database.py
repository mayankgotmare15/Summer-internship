"""
Unit and integration tests for Database Service, ORM Models, Foreign Keys,
Cascading Deletions, SLA calculations, and Repository Transactions.
"""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.db import SessionLocal, ensure_user_exists, init_db
from src.database.models import FeedbackSubmission, Ticket, TicketEvent, TicketStatus, User, UserRole
from src.repositories.ticket_repository import SLA_DURATIONS, TicketRepository


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


@pytest.fixture
def db_session():
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_ensure_user_exists(db_session: Session):
    # Test creating new user dynamically
    user = ensure_user_exists(
        db_session,
        user_id="test_custom_dev",
        role=UserRole.SPECIALIST_L3,
        name="Custom Developer",
        department="Platform Eng",
    )
    assert user.id == "test_custom_dev"
    assert user.role == UserRole.SPECIALIST_L3
    assert user.department == "Platform Eng"

    # Test retrieval of existing user
    user_again = ensure_user_exists(db_session, user_id="test_custom_dev")
    assert user_again.id == user.id
    assert user_again.name == user.name


def test_create_ticket_and_sla_durations(db_session: Session):
    # Test Critical Ticket SLA (1 hour)
    crit_ticket = TicketRepository.create_ticket(
        db=db_session,
        text="Critical infrastructure failure: all main gateways unresponsive",
        predicted_category="Infrastructure",
        category_confidence=0.98,
        predicted_priority="Critical",
        priority_confidence=0.99,
        priority_overridden=True,
        decision="auto_route",
        assigned_team="Project Engineering & DevOps",
        model_version="1.0.0",
        ticket_id="TKT-UNIT-CRIT-01",
    )
    assert crit_ticket.id == "TKT-UNIT-CRIT-01"
    assert crit_ticket.escalation_level == 3
    assert crit_ticket.status == TicketStatus.ESCALATED_L3
    expected_delta = SLA_DURATIONS["Critical"]
    now = datetime.now(timezone.utc)
    # Validate deadline is within expected range (~1 hour from now)
    diff = crit_ticket.sla_deadline.replace(tzinfo=timezone.utc) - now
    assert timedelta(minutes=55) <= diff <= timedelta(minutes=65)

    # Test Normal Ticket SLA (Medium = 24 hours)
    med_ticket = TicketRepository.create_ticket(
        db=db_session,
        text="Please update my email signature template",
        predicted_category="Internal Project",
        category_confidence=0.88,
        predicted_priority="Medium",
        priority_confidence=0.80,
        priority_overridden=False,
        decision="auto_route",
        assigned_team="Internal Applications",
        model_version="1.0.0",
        ticket_id="TKT-UNIT-MED-02",
    )
    diff_med = med_ticket.sla_deadline.replace(tzinfo=timezone.utc) - now
    assert timedelta(hours=23) <= diff_med <= timedelta(hours=25)


def test_ticket_cascading_deletion(db_session: Session):
    # Create ticket
    tkt = TicketRepository.create_ticket(
        db=db_session,
        text="Temporary ticket for cascade deletion verification",
        predicted_category="Hardware",
        category_confidence=0.92,
        predicted_priority="Low",
        priority_confidence=0.90,
        priority_overridden=False,
        decision="auto_route",
        assigned_team="Desktop Support & Hardware Services",
        model_version="1.0.0",
        ticket_id="TKT-CASCADE-TEST",
    )
    tid = tkt.id

    # Add audit event and feedback submission
    TicketRepository.override_triage(
        db=db_session,
        ticket_id=tid,
        new_category="Access",
        new_team="Identity & Access Management (IAM)",
        new_priority="Medium",
        actor_id="agent_alex",
        actor_role="triager",
        notes="Re-assigned to IAM",
    )

    # Verify event and feedback exist
    events = db_session.query(TicketEvent).filter(TicketEvent.ticket_id == tid).all()
    feedbacks = db_session.query(FeedbackSubmission).filter(FeedbackSubmission.ticket_id == tid).all()
    assert len(events) >= 2
    assert len(feedbacks) >= 1

    # Delete ticket directly and commit
    ticket_to_del = db_session.query(Ticket).filter(Ticket.id == tid).first()
    db_session.delete(ticket_to_del)
    db_session.commit()

    # Assert cascade deletion worked cleanly: no orphaned events or feedbacks
    post_events = db_session.query(TicketEvent).filter(TicketEvent.ticket_id == tid).all()
    post_feedbacks = db_session.query(FeedbackSubmission).filter(FeedbackSubmission.ticket_id == tid).all()
    assert len(post_events) == 0
    assert len(post_feedbacks) == 0


def test_sqlite_foreign_key_enforcement(db_session: Session):
    # Attempting to directly insert TicketEvent with non-existent foreign keys should fail
    bad_event = TicketEvent(
        ticket_id="NON-EXISTENT-TICKET-XYZ",
        actor_id="NON-EXISTENT-USER-999",
        actor_role="unknown",
        action="invalid_action",
    )
    db_session.add(bad_event)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_sla_breach_detection_and_escalation(db_session: Session):
    # Ingest ticket with backdated SLA deadline (past)
    tkt = TicketRepository.create_ticket(
        db=db_session,
        text="Legacy ticket requiring immediate SLA compliance check",
        predicted_category="Access",
        category_confidence=0.91,
        predicted_priority="High",
        priority_confidence=0.85,
        priority_overridden=False,
        decision="auto_route",
        assigned_team="Identity & Access Management (IAM)",
        model_version="1.0.0",
        ticket_id="TKT-SLA-BREACH-SIM",
    )
    # Manually backdate SLA deadline to 2 hours ago
    past_time = datetime.now(timezone.utc) - timedelta(hours=2)
    tkt.sla_deadline = past_time
    tkt.sla_breached = False
    tkt.escalation_level = 2
    tkt.status = TicketStatus.AUTO_ROUTED
    db_session.commit()

    # Run SLA scanner
    result = TicketRepository.check_and_update_sla(db_session)
    assert result["scanned_count"] >= 1
    assert result["new_breaches"] >= 1

    # Verify ticket state is now management_escalated and sla_breached=True
    updated_tkt = TicketRepository.get_ticket(db_session, "TKT-SLA-BREACH-SIM")
    assert updated_tkt.sla_breached is True
    assert updated_tkt.escalation_level == 4
    assert updated_tkt.status == TicketStatus.MANAGEMENT_ESCALATED


def test_analytics_kpi_calculation(db_session: Session):
    analytics = TicketRepository.get_analytics(db_session, N=5000, t=3.0, c=15.0, r=10.0)
    assert analytics["total_tickets"] > 0
    assert 0.0 <= analytics["auto_route_rate"] <= 1.0
    assert 0.0 <= analytics["routed_accuracy"] <= 1.0
    assert "net_hours_saved_monthly" in analytics
    assert "net_cost_saved_usd" in analytics
    assert isinstance(analytics["department_distribution"], dict)
