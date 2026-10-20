"""SQLAlchemy ORM model for prediction feedback and triage corrections."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import GUID, Base, TimestampMixin


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True, index=True)
    prediction_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("predictions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kind: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # agent_correction | wrong_team_escalation | requester_not_quite | priority_correction
    predicted_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    corrected_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    predicted_priority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    corrected_priority: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
