"""Main entrypoint for RouteDesk FastAPI backend service."""

from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from src.app.errors import DomainError, ErrorOut
from src.app.lifespan import lifespan
from src.app.settings import get_settings

logger = structlog.get_logger()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise IT Support Ticket Auto-Routing and Priority Classification API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Handles domain exceptions and formats standard ErrorOut response."""
    request_id = request.headers.get("X-Request-ID", "")
    error_payload = ErrorOut(
        code=exc.code,
        message=exc.message,
        field=exc.field,
        details=exc.details,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload.model_dump(),
    )


@app.get("/health", status_code=status.HTTP_200_OK, tags=["System Health"])
async def health_check() -> Dict[str, Any]:
    """Liveness probe: verifies web server process is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/ready", tags=["System Health"])
async def readiness_check() -> JSONResponse:
    """Readiness probe: verifies DB connectivity, migrations, and model availability."""
    db_ok = getattr(app.state, "db_ready", True)
    model_ok = getattr(app.state, "model_ready", False)

    is_ready = db_ok
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if (db_ok and model_ok) else ("degraded" if db_ok else "unhealthy"),
            "checks": {
                "db": "ok" if db_ok else "unreachable",
                "model": "loaded" if model_ok else "not_loaded_fallback_to_human_review",
            },
            "version": settings.app_version,
        },
    )
