"""
Relational Database Models for Role-Based IT Ticket Management.
Supports full ticket lifecycle, audit event log, agent feedback, and RBAC users.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserRole(str, enum.Enum):
    TRIAGER = "triager"
    RESOLVER_LEAD = "resolver_lead"
    SPECIALIST_L3 = "specialist_l3"
    MANAGER = "manager"
    MLOPS_ADMIN = "mlops_admin"


class TicketStatus(str, enum.Enum):
    PENDING_TRIAGE = "pending_triage"
    AUTO_ROUTED = "auto_routed"
    IN_PROGRESS = "in_progress"
    ESCALATED_L2 = "escalated_l2"
    ESCALATED_L3 = "escalated_l3"
    MANAGEMENT_ESCALATED = "management_escalated"
    RESOLVED = "resolved"
    REASSIGNED = "reassigned"
    CLOSED = "closed"


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    department = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=True)
    password_salt = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    events = relationship("TicketEvent", back_populates="actor")
    feedbacks = relationship("FeedbackSubmission", back_populates="user")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(64), primary_key=True)
    text = Column(Text, nullable=False)
    text_hash = Column(String(64), nullable=False, index=True)
    predicted_category = Column(String(64), nullable=False)
    category_confidence = Column(Float, nullable=False)
    predicted_priority = Column(String(32), nullable=False)
    priority_confidence = Column(Float, nullable=False)
    priority_overridden = Column(Boolean, default=False)
    decision = Column(String(32), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.PENDING_TRIAGE, index=True)
    assigned_team = Column(String(128), nullable=False, index=True)
    assigned_agent = Column(String(64), nullable=True)
    model_version = Column(String(64), nullable=False)
    escalation_level = Column(Integer, default=1, index=True)
    escalation_reason = Column(Text, nullable=True)
    escalated_by = Column(String(64), nullable=True)
    sla_deadline = Column(DateTime, nullable=True, index=True)
    sla_breached = Column(Boolean, default=False, index=True)
    reassignment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    events = relationship("TicketEvent", back_populates="ticket", cascade="all, delete-orphan")
    feedbacks = relationship(
        "FeedbackSubmission", back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(64), ForeignKey("tickets.id"), nullable=False, index=True)
    actor_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    actor_role = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False)
    previous_state = Column(String(64), nullable=True)
    new_state = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ticket = relationship("Ticket", back_populates="events")
    actor = relationship("User", back_populates="events")


class FeedbackSubmission(Base):
    __tablename__ = "feedback_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(64), ForeignKey("tickets.id"), nullable=False, index=True)
    submitted_by = Column(String(64), ForeignKey("users.id"), nullable=False)
    predicted_category = Column(String(64), nullable=False)
    corrected_category = Column(String(64), nullable=False)
    is_override = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ticket = relationship("Ticket", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")
