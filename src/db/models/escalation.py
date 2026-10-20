"""SQLAlchemy models for escalations and ticket approvals."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import GUID, Base, TimestampMixin


class Escalation(Base, TimestampMixin):
    __tablename__ = "escalations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(
        String(20), default="requester", nullable=False
    )  # requester | auto
    level: Mapped[str] = mapped_column(
        String(10), default="E2", nullable=False
    )  # E1 | E2 | E3 | E4
    raised_by: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    reason_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # no_response | wrong_team | business_critical | deadline_at_risk | other
    note: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )  # pending | accepted | reassigned | declined | timed_out | superseded
    response_due: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    responder_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )
    outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    outcome_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )
    new_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending | approved | rejected
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
