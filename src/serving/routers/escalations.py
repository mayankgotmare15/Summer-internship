"""
Escalation and SLA Management Router.
Provides tiered escalation workflows (L1 -> L2 -> L3 -> Manager),
SLA countdown monitoring, bounce dispute resolution, and incident command oversight.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth.dependencies import AuthenticatedUser, require_role
from src.database.db import get_db
from src.database.models import UserRole
from src.repositories.ticket_repository import TicketRepository

router = APIRouter(prefix="/api/v1/escalations", tags=["Escalation & SLA Management"])


class EscalateRequest(BaseModel):
    target_level: int = Field(..., ge=2, le=4, description="Target escalation level (2=L2, 3=L3, 4=Manager)")
    reason: str = Field(..., min_length=3, description="Operational justification for ticket escalation")
    target_team: str | None = Field(None, description="Optional target department team")


def serialize_ticket(t: Any) -> dict[str, Any]:
    return {
        "id": t.id,
        "text": t.text,
        "category": t.predicted_category,
        "priority": t.predicted_priority,
        "priority_overridden": t.priority_overridden,
        "status": t.status.value,
        "assigned_team": t.assigned_team,
        "assigned_agent": t.assigned_agent,
        "escalation_level": t.escalation_level,
        "escalation_reason": t.escalation_reason,
        "escalated_by": t.escalated_by,
        "sla_deadline": t.sla_deadline.isoformat() if t.sla_deadline else None,
        "sla_breached": t.sla_breached,
        "reassignment_count": t.reassignment_count,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.post("/{ticket_id}/escalate")
def escalate_ticket(
    ticket_id: str,
    req: EscalateRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(
        require_role([
            UserRole.TRIAGER,
            UserRole.RESOLVER_LEAD,
            UserRole.SPECIALIST_L3,
            UserRole.MANAGER,
            UserRole.MLOPS_ADMIN,
        ])
    ),
):
    """
    Escalates a ticket to higher competency or managerial tier.
    - L1/L2 can escalate to L2 or L3.
    - L3 can escalate to Manager/Incident Commander (Level 4).
    """
    try:
        updated = TicketRepository.escalate_ticket(
            db=db,
            ticket_id=ticket_id,
            target_level=req.target_level,
            reason=req.reason,
            actor_id=user.id,
            actor_role=user.role.value,
            target_team=req.target_team,
        )
        return {
            "status": "success",
            "message": f"Ticket {ticket_id} escalated to Tier {req.target_level}",
            "ticket": serialize_ticket(updated),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.get("/active")
def get_active_escalations(
    min_level: int = 2,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(
        require_role([
            UserRole.TRIAGER,
            UserRole.RESOLVER_LEAD,
            UserRole.SPECIALIST_L3,
            UserRole.MANAGER,
            UserRole.MLOPS_ADMIN,
        ])
    ),
) -> list[dict[str, Any]]:
    """Returns all active escalated tickets."""
    tickets = TicketRepository.list_escalations(db, min_level=min_level, limit=limit)
    return [serialize_ticket(t) for t in tickets]


@router.get("/l3-backlog")
def get_l3_specialist_backlog(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(
        require_role([UserRole.SPECIALIST_L3, UserRole.MANAGER, UserRole.MLOPS_ADMIN])
    ),
) -> list[dict[str, Any]]:
    """Returns Tier 3 DevOps & Senior Specialist incident backlog."""
    tickets = TicketRepository.list_l3_queue(db, limit=limit)
    return [serialize_ticket(t) for t in tickets]


@router.get("/manager-oversight")
def get_manager_escalation_oversight(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(
        require_role([UserRole.MANAGER, UserRole.MLOPS_ADMIN])
    ),
) -> list[dict[str, Any]]:
    """Returns critical tickets requiring Incident Commander attention (Level 4, SLA breached, multi-bounce)."""
    tickets = TicketRepository.list_manager_escalations(db, limit=limit)
    return [serialize_ticket(t) for t in tickets]


@router.post("/check-sla")
def check_sla_breaches(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(
        require_role([
            UserRole.TRIAGER,
            UserRole.RESOLVER_LEAD,
            UserRole.SPECIALIST_L3,
            UserRole.MANAGER,
            UserRole.MLOPS_ADMIN,
        ])
    ),
) -> dict[str, Any]:
    """Sweeps active tickets against SLA timers and automatically promotes breached tickets."""
    return TicketRepository.check_and_update_sla(db)
