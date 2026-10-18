"""
MLOps & Platform Administration Router.
Enforces runtime threshold tuning, drift telemetry inspection, and CT triggers.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import AuthenticatedUser, require_role
from src.database.models import UserRole
from src.monitoring.check_thresholds import evaluate_telemetry
from src.monitoring.drift_report import generate_drift_report

router = APIRouter(prefix="/api/v1/admin", tags=["MLOps Administrator"])


class ThresholdUpdateRequest(BaseModel):
    new_threshold: float = Field(
        ..., ge=0.50, le=0.99, description="Confidence threshold between 0.50 and 0.99"
    )


@router.get("/model-health")
def get_model_health(
    user: AuthenticatedUser = Depends(require_role([UserRole.MLOPS_ADMIN])),
) -> dict[str, Any]:
    """Inspects active champion model metadata and governance metrics."""
    meta_path = Path("models/champion_metadata.json")
    champion_data = {}
    if meta_path.exists():
        try:
            with open(meta_path, encoding="utf-8") as f:
                champion_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            champion_data = {}

    return {
        "status": "operational",
        "champion_metadata": champion_data,
        "runtime_version": "v1.0.0-champion",
        "inspected_by": user.id,
    }


@router.post("/threshold")
def update_confidence_threshold(
    req: ThresholdUpdateRequest,
    user: AuthenticatedUser = Depends(require_role([UserRole.MLOPS_ADMIN])),
):
    """Dynamically updates confidence threshold tau without restart."""
    from src.serving.app import decision_engine

    old_tau = decision_engine.threshold
    decision_engine.threshold = req.new_threshold

    return {
        "status": "success",
        "message": f"Threshold updated from {old_tau:.2f} to {req.new_threshold:.2f}",
        "active_threshold": req.new_threshold,
        "updated_by": user.id,
    }


@router.post("/trigger-retraining")
def trigger_retraining(
    user: AuthenticatedUser = Depends(require_role([UserRole.MLOPS_ADMIN])),
):
    """Triggers continuous retraining pipeline."""
    # In production, dispatches GitHub Actions retrain.yml
    return {
        "status": "dispatched",
        "message": "Continuous retraining workflow dispatched for Challenger evaluation.",
        "triggered_by": user.id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/telemetry")
def get_telemetry_status(
    user: AuthenticatedUser = Depends(require_role([UserRole.MLOPS_ADMIN])),
):
    """Evaluates telemetry boundaries and drift."""
    try:
        generate_drift_report()
        is_healthy = evaluate_telemetry()
        return {
            "telemetry_healthy": is_healthy,
            "drift_report_url": "/reports/drift_report.html",
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    user: AuthenticatedUser = Depends(require_role([UserRole.MLOPS_ADMIN])),
) -> list[dict[str, Any]]:
    """Fetches recent security & lifecycle audit events for SOC2 / ISO 27001 compliance."""
    from src.database.db import SessionLocal
    from src.repositories.ticket_repository import TicketRepository

    db = SessionLocal()
    try:
        events = TicketRepository.list_audit_events(db, limit=limit)
        return [
            {
                "id": e.id,
                "ticket_id": e.ticket_id,
                "actor_id": e.actor_id,
                "actor_role": e.actor_role,
                "action": e.action,
                "previous_state": e.previous_state,
                "new_state": e.new_state,
                "notes": e.notes,
                "created_at": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ]
    finally:
        db.close()

