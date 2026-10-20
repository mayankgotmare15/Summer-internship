"""SQLAlchemy models for SLA clocks, ladder events, and ETA adjustments."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import GUID, Base, TimestampMixin


class SlaClock(Base, TimestampMixin):
    __tablename__ = "sla_clocks"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    policy_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    calendar: Mapped[str] = mapped_column(
        String(50), default="business", nullable=False
    )  # business | 24x7
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_response_due: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution_due: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state: Mapped[str] = mapped_column(
        String(50), default="running", nullable=False
    )  # running | paused | stopped | pending_approval
    cycle: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    next_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    breached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_response_met: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SlaEvent(Base):
    __tablename__ = "sla_events"
    __table_args__ = (
        UniqueConstraint("ticket_id", "rule_key", "cycle", name="uq_sla_event_ticket_rule_cycle"),
    )

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
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False)
    cycle: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class EtaChange(Base, TimestampMixin):
    __tablename__ = "eta_changes"

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
    old_resolution_due: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    new_resolution_due: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("users.id"), nullable=True
    )
