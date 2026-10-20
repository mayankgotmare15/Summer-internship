"""Application lifespan events (startup and shutdown management)."""

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
import structlog
from src.app.settings import get_settings
from src.db.seed import run_seed
from src.db.session import init_db
from src.ml.store import ModelStore

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

    # 1. Ensure storage directories exist
    os.makedirs("./local_db", exist_ok=True)
    os.makedirs(settings.model_dir, exist_ok=True)

    # 2. Initialize DB & seed demo data
    try:
        run_seed()
        app.state.db_ready = True
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        app.state.db_ready = False

    # 3. Load active champion model bundle
    try:
        store = ModelStore.get_instance()
        loaded = store.load_bundle()
        app.state.model_ready = loaded
        app.state.model_store = store
        if not loaded:
            logger.warning("Application started in DEGRADED MODE: active model bundle not loaded")
    except Exception as e:
        logger.error("Error during model bundle loading", error=str(e))
        app.state.model_ready = False

    yield

    logger.info("Application shutting down")
