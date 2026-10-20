"""Unit tests for time abstraction protocol and FakeClock."""

from datetime import datetime, timedelta, timezone

from src.core.clock import FakeClock, SystemClock


def test_system_clock_returns_utc_datetime():
    clock = SystemClock()
    t = clock.now()
    assert isinstance(t, datetime)
    assert t.tzinfo is not None
    assert t.tzinfo == timezone.utc


def test_fake_clock_initial_time():
    init_dt = datetime(2026, 10, 20, 9, 30, 0, tzinfo=timezone.utc)
    clock = FakeClock(init_dt)
    assert clock.now() == init_dt


def test_fake_clock_advance_minutes():
    init_dt = datetime(2026, 10, 20, 9, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(init_dt)
    advanced = clock.advance(minutes=45)
    assert advanced == datetime(2026, 10, 20, 9, 45, 0, tzinfo=timezone.utc)
    assert clock.now() == advanced


def test_fake_clock_advance_hours_and_days():
    init_dt = datetime(2026, 10, 20, 9, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(init_dt)
    advanced = clock.advance(days=1, hours=2)
    assert advanced == init_dt + timedelta(days=1, hours=2)
    assert clock.now() == advanced
