"""Business calendar calculations for business-hours SLA time elapsed and target deadlines."""

import zoneinfo
from datetime import date, datetime, time, timedelta, timezone

import yaml


class BusinessCalendar:
    """Calculates business hours between instants and adds business durations.

    Default: Asia/Kolkata timezone, Monday-Friday 09:00 - 18:00 (9 working hours/day = 32,400s),
    excluding official company holidays.
    """

    def __init__(
        self,
        tz_name: str = "Asia/Kolkata",
        work_days: list[int] | None = None,
        start_time: time = time(9, 0),
        end_time: time = time(18, 0),
        holidays: set[date] | None = None,
    ):
        self.tz = zoneinfo.ZoneInfo(tz_name)
        self.work_days = work_days if work_days is not None else [0, 1, 2, 3, 4]  # Mon-Fri
        self.start_time = start_time
        self.end_time = end_time
        self.holidays = holidays or set()

    @classmethod
    def from_yaml(cls, path: str = "configs/calendar.yaml") -> "BusinessCalendar":
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            tz_name = data.get("timezone", "Asia/Kolkata")
            bh = data.get("business_hours", {})
            work_days = bh.get("work_days", [0, 1, 2, 3, 4])
            start_parts = [int(p) for p in bh.get("start_time", "09:00").split(":")]
            end_parts = [int(p) for p in bh.get("end_time", "18:00").split(":")]
            holidays_raw = data.get("holidays_2026", [])
            holidays = {datetime.strptime(h, "%Y-%m-%d").date() for h in holidays_raw}
            return cls(
                tz_name=tz_name,
                work_days=work_days,
                start_time=time(start_parts[0], start_parts[1]),
                end_time=time(end_parts[0], end_parts[1]),
                holidays=holidays,
            )
        except Exception:
            return cls()

    def _to_local(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(self.tz)

    def is_work_day(self, d: date) -> bool:
        return d.weekday() in self.work_days and d not in self.holidays

    def is_business_hour(self, dt: datetime) -> bool:
        local_dt = self._to_local(dt)
        if not self.is_work_day(local_dt.date()):
            return False
        t = local_dt.time()
        return self.start_time <= t < self.end_time

    def business_seconds(self, start: datetime, end: datetime) -> int:
        """Returns total business seconds elapsed between start and end instants."""
        if end <= start:
            return 0

        start_loc = self._to_local(start)
        end_loc = self._to_local(end)

        total_seconds = 0
        current_day = start_loc.date()
        end_day = end_loc.date()

        while current_day <= end_day:
            if self.is_work_day(current_day):
                work_start = datetime.combine(current_day, self.start_time, tzinfo=self.tz)
                work_end = datetime.combine(current_day, self.end_time, tzinfo=self.tz)

                interval_start = max(start_loc, work_start)
                interval_end = min(end_loc, work_end)

                if interval_end > interval_start:
                    total_seconds += int((interval_end - interval_start).total_seconds())

            current_day += timedelta(days=1)

        return total_seconds

    def add_business_seconds(self, start: datetime, seconds: int) -> datetime:
        """Adds business seconds to start instant, rolling forward over nights, weekends, and holidays."""
        if seconds <= 0:
            return start

        current = self._to_local(start)
        remaining = seconds

        while remaining > 0:
            current_date = current.date()
            if not self.is_work_day(current_date):
                # Roll forward to start of next day
                current = datetime.combine(
                    current_date + timedelta(days=1), self.start_time, tzinfo=self.tz
                )
                continue

            work_start = datetime.combine(current_date, self.start_time, tzinfo=self.tz)
            work_end = datetime.combine(current_date, self.end_time, tzinfo=self.tz)

            if current < work_start:
                current = work_start
            elif current >= work_end:
                current = datetime.combine(
                    current_date + timedelta(days=1), self.start_time, tzinfo=self.tz
                )
                continue

            available_seconds = int((work_end - current).total_seconds())
            if remaining <= available_seconds:
                current += timedelta(seconds=remaining)
                remaining = 0
            else:
                remaining -= available_seconds
                current = datetime.combine(
                    current_date + timedelta(days=1), self.start_time, tzinfo=self.tz
                )

        # Return converted back to UTC
        return current.astimezone(timezone.utc)
