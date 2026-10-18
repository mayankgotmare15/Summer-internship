"""
Triage Agent Router.
Provides human-in-the-loop triage queue review, approval, and queue overrides.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth.dependencies import AuthenticatedUser, require_role
from src.database.db import get_db
from src.database.models import UserRole
from src.repositories.ticket_repository import TicketRepository
from src.serving.decision import DEFAULT_ROUTING_MAP

router = APIRouter(prefix="/api/v1/triage", tags=["Triage Agent"])


class OverrideRequest(BaseModel):
    category: str = Field(..., description="Target category corrected by agent")
    priority: str | None = Field(None, description="Optional priority override")
    notes: str | None = Field(None, description="Reason for override")


@router.get("/queue")
def get_triage_queue(
    limit: int = 50,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.TRIAGER, UserRole.MLOPS_ADMIN])),
) -> list[dict[str, Any]]:
    """Returns all ambiguous or low-confidence tickets awaiting human review."""
    tickets = TicketRepository.list_triage_queue(db, limit=limit)
    return [
        {
            "id": t.id,
            "text": t.text,
            "predicted_category": t.predicted_category,
            "category_confidence": round(t.category_confidence, 4),
            "predicted_priority": t.predicted_priority,
            "priority_confidence": round(t.priority_confidence, 4),
            "priority_overridden": t.priority_overridden,
            "status": t.status.value,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tickets
    ]


@router.post("/{ticket_id}/override")
def override_ticket(
    ticket_id: str,
    req: OverrideRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.TRIAGER, UserRole.MLOPS_ADMIN])),
):
    """Triage agent overrides category; moves ticket to designated resolver queue."""
    target_team = DEFAULT_ROUTING_MAP.get(req.category, "General IT Service Desk")
    try:
        updated = TicketRepository.override_triage(
            db=db,
            ticket_id=ticket_id,
            new_category=req.category,
            new_team=target_team,
            new_priority=req.priority,
            actor_id=user.id,
            actor_role=user.role.value,
            notes=req.notes,
        )
        return {
            "status": "success",
            "message": f"Ticket {ticket_id} re-routed to '{target_team}'",
            "ticket_id": updated.id,
            "assigned_team": updated.assigned_team,
            "ticket_status": updated.status.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{ticket_id}/approve")
def approve_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.TRIAGER, UserRole.MLOPS_ADMIN])),
):
    """Triage agent approves model's recommended queue."""
    try:
        updated = TicketRepository.approve_triage(
            db=db,
            ticket_id=ticket_id,
            actor_id=user.id,
            actor_role=user.role.value,
        )
        return {
            "status": "success",
            "message": f"Ticket {ticket_id} routing confirmed to '{updated.assigned_team}'",
            "ticket_id": updated.id,
            "assigned_team": updated.assigned_team,
            "ticket_status": updated.status.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
