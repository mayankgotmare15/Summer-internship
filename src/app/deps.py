"""Dependency injection providers for FastAPI routes."""

from typing import Annotated
from fastapi import Depends
from src.app.settings import Settings, get_settings
from src.core.clock import Clock, SystemClock

_system_clock = SystemClock()


def get_clock() -> Clock:
    """Provides clock instance (can be overridden in tests via app.dependency_overrides)."""
    return _system_clock


SettingsDep = Annotated[Settings, Depends(get_settings)]
ClockDep = Annotated[Clock, Depends(get_clock)]
