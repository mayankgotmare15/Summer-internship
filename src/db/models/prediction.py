"""SQLAlchemy ORM model for prediction logging."""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base, GUID, TimestampMixin


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, nullable=True, index=True)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    text_preview: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    category_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    probabilities: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    priority_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    priority_source: Mapped[str] = mapped_column(String(20), nullable=False, default="model")
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    review_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    routed_team: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    priority_model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="predict_api")
