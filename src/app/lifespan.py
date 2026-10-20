"""Application lifespan events (startup and shutdown management)."""

from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
import structlog
from src.app.settings import get_settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manages application startup and graceful shutdown."""
    settings = get_settings()
    logger.info(
        "Application starting up",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # In Phase 0-3, verify local storage directories exist
    import os
    os.makedirs("./local_db", exist_ok=True)
    os.makedirs(settings.model_dir, exist_ok=True)

    # State flags
    app.state.model_ready = False
    app.state.db_ready = True # In-memory / sqlite ready by default

    yield

    logger.info("Application shutting down")
