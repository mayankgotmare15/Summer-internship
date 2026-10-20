"""SQLAlchemy models for tickets and message threads."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base, GUID, TimestampMixin


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), default="portal", nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority_source: Mapped[str] = mapped_column(String(20), default="model", nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    review_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="New", nullable=False, index=True)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("teams.id"), nullable=True, index=True)
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("users.id"), nullable=True, index=True)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalation_level: Mapped[str] = mapped_column(String(10), default="E1", nullable=False)
    first_responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) if 'timezone' in globals() else datetime.utcnow(),
        onupdate=lambda: datetime.now(timezone.utc) if 'timezone' in globals() else datetime.utcnow(),
        nullable=False,
    )


class TicketMessage(Base, TimestampMixin):
    __tablename__ = "ticket_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(20), default="public", nullable=False)  # public | internal | system
    body: Mapped[str] = mapped_column(Text, nullable=False)
