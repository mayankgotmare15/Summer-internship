"""SQLAlchemy model for idempotency keys."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import GUID, Base, TimestampMixin


class IdempotencyKey(Base, TimestampMixin):
    __tablename__ = "idempotency_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    request_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    response_status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    response_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),
    )
