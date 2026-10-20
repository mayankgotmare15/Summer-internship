"""Database declarative base and portable column types for SQLite & PostgreSQL."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.

    Stores as CHAR(36) in SQLite and handles native UUID conversions transparently.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        try:
            return str(uuid.UUID(str(value)))
        except (ValueError, AttributeError):
            return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            return value


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy entities."""

    pass


class TimestampMixin:
    """Mixin adding UTC created_at timestamp to models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
