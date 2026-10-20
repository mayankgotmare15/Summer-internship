"""Unit tests for business calendar and business hours calculations."""

from datetime import datetime, time, timezone

from src.core.business_calendar import BusinessCalendar


def test_business_calendar_same_day():
    cal = BusinessCalendar(
        tz_name="UTC",
        work_days=[0, 1, 2, 3, 4],
        start_time=time(9, 0),
        end_time=time(18, 0),
        holidays=set(),
    )
    # Wednesday 10:00 to 14:00 (4 hours = 14400s)
    t1 = datetime(2026, 10, 21, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 21, 14, 0, 0, tzinfo=timezone.utc)
    assert cal.business_seconds(t1, t2) == 14400


def test_business_calendar_overnight():
    cal = BusinessCalendar(
        tz_name="UTC",
        work_days=[0, 1, 2, 3, 4],
        start_time=time(9, 0),
        end_time=time(18, 0),
        holidays=set(),
    )
    # Wednesday 17:00 to Thursday 10:00:
    # Wed: 17:00 to 18:00 = 1 hour (3600s)
    # Thu: 09:00 to 10:00 = 1 hour (3600s)
    # Total = 7200s
    t1 = datetime(2026, 10, 21, 17, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 22, 10, 0, 0, tzinfo=timezone.utc)
    assert cal.business_seconds(t1, t2) == 7200


def test_business_calendar_weekend_skip():
    cal = BusinessCalendar(
        tz_name="UTC",
        work_days=[0, 1, 2, 3, 4],
        start_time=time(9, 0),
        end_time=time(18, 0),
        holidays=set(),
    )
    # Friday 2026-10-23 17:00 to Monday 2026-10-26 10:00:
    # Fri: 1 hour (3600s)
    # Sat, Sun: 0s
    # Mon: 1 hour (3600s)
    # Total = 7200s
    t1 = datetime(2026, 10, 23, 17, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 26, 10, 0, 0, tzinfo=timezone.utc)
    assert cal.business_seconds(t1, t2) == 7200


def test_add_business_seconds():
    cal = BusinessCalendar(
        tz_name="UTC",
        work_days=[0, 1, 2, 3, 4],
        start_time=time(9, 0),
        end_time=time(18, 0),
        holidays=set(),
    )
    # Friday 17:00 + 2 business hours (7200s) -> should be Monday 10:00
    t1 = datetime(2026, 10, 23, 17, 0, 0, tzinfo=timezone.utc)
    res = cal.add_business_seconds(t1, 7200)
    assert res == datetime(2026, 10, 26, 10, 0, 0, tzinfo=timezone.utc)
