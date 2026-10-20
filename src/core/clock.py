from datetime import datetime, timezone, timedelta
from typing import Optional, Protocol


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensures datetime is timezone-aware in UTC (fixes sqlite naive datetime comparisons)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class Clock(Protocol):
    """Protocol for time abstraction."""
    def now(self) -> datetime:
        ...


class SystemClock:
    """Real system clock providing current UTC datetime."""
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FakeClock:
    """Controllable clock for deterministic testing of SLA ladders and timers."""
    def __init__(self, initial_time: datetime | None = None):
        self._current_time = initial_time or datetime(2026, 10, 20, 9, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._current_time

    def set_time(self, new_time: datetime) -> None:
        if new_time.tzinfo is None:
            new_time = new_time.replace(tzinfo=timezone.utc)
        self._current_time = new_time

    def advance(
        self,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> datetime:
        """Advance fake clock by a specified duration."""
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        self._current_time += delta
        return self._current_time

    def advance_minutes(self, minutes: int) -> datetime:
        return self.advance(minutes=minutes)

    def advance_hours(self, hours: int) -> datetime:
        return self.advance(hours=hours)

    def advance_days(self, days: int) -> datetime:
        return self.advance(days=days)
