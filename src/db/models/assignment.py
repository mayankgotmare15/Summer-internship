"""SQLAlchemy model for ticket assignment history and rule trace."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import GUID, Base, TimestampMixin


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

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
    assignee_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("teams.id"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # auto | agent_triage | lead_reassign | first_response_miss | escalation_accept | escalation_reassign | escalation_decline | fallback_lead
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id"),
        nullable=True,
    )
    rule_trace: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
