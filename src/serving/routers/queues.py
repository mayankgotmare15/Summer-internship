"""
Resolver Team Lead Router.
Provides department backlog visibility, agent assignment, state transitions, and dispute routing.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth.dependencies import AuthenticatedUser, require_role
from src.database.db import get_db
from src.database.models import TicketStatus, UserRole
from src.repositories.ticket_repository import TicketRepository
from src.serving.decision import DEFAULT_ROUTING_MAP

router = APIRouter(prefix="/api/v1/queues", tags=["Resolver Team Lead"])


class AssignRequest(BaseModel):
    assigned_agent: str = Field(..., description="Name or ID of resolver engineer")


class StatusUpdateRequest(BaseModel):
    new_status: TicketStatus = Field(..., description="Target lifecycle state")
    notes: str | None = None


class DisputeRequest(BaseModel):
    reason: str = Field(..., description="Explanation of why ticket was misrouted")


@router.get("/departments")
def list_departments(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(
        require_role([UserRole.RESOLVER_LEAD, UserRole.MANAGER, UserRole.MLOPS_ADMIN])
    ),
) -> list[dict[str, Any]]:
    """Lists resolver departments and their active backlog volume."""
    teams = list(set(DEFAULT_ROUTING_MAP.values()))
    result = []
    for team in sorted(teams):
        backlog = TicketRepository.list_department_queue(db, team_name=team, limit=500)
        result.append(
            {
                "team_name": team,
                "active_tickets": len(backlog),
                "unassigned": sum(1 for t in backlog if not t.assigned_agent),
                "in_progress": sum(1 for t in backlog if t.status == TicketStatus.IN_PROGRESS),
            }
        )
    return result


@router.get("/{team_name}")
def get_department_queue(
    team_name: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.RESOLVER_LEAD, UserRole.MLOPS_ADMIN])),
) -> list[dict[str, Any]]:
    """Returns department backlog for resolver lead."""
    tickets = TicketRepository.list_department_queue(db, team_name=team_name, limit=limit)
    return [
        {
            "id": t.id,
            "text": t.text,
            "category": t.predicted_category,
            "priority": t.predicted_priority,
            "priority_overridden": t.priority_overridden,
            "status": t.status.value,
            "assigned_agent": t.assigned_agent,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tickets
    ]


@router.patch("/{ticket_id}/assign")
def assign_ticket(
    ticket_id: str,
    req: AssignRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.RESOLVER_LEAD, UserRole.MLOPS_ADMIN])),
):
    """Assigns ticket to an engineer; moves status to in_progress."""
    try:
        updated = TicketRepository.assign_agent(
            db=db,
            ticket_id=ticket_id,
            assigned_agent=req.assigned_agent,
            actor_id=user.id,
            actor_role=user.role.value,
        )
        return {
            "status": "success",
            "message": f"Assigned to {req.assigned_agent}",
            "ticket_id": updated.id,
            "assigned_agent": updated.assigned_agent,
            "ticket_status": updated.status.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{ticket_id}/status")
def update_status(
    ticket_id: str,
    req: StatusUpdateRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.RESOLVER_LEAD, UserRole.MLOPS_ADMIN])),
):
    """Updates lifecycle state (e.g. resolved, closed)."""
    try:
        updated = TicketRepository.update_status(
            db=db,
            ticket_id=ticket_id,
            new_status=req.new_status,
            actor_id=user.id,
            actor_role=user.role.value,
            notes=req.notes,
        )
        return {
            "status": "success",
            "ticket_id": updated.id,
            "ticket_status": updated.status.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{ticket_id}/dispute")
def dispute_routing(
    ticket_id: str,
    req: DisputeRequest,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role([UserRole.RESOLVER_LEAD, UserRole.MLOPS_ADMIN])),
):
    """Resolver lead disputes ticket misrouting, returning it to triage."""
    try:
        updated = TicketRepository.dispute_ticket(
            db=db,
            ticket_id=ticket_id,
            actor_id=user.id,
            actor_role=user.role.value,
            dispute_reason=req.reason,
        )
        return {
            "status": "success",
            "message": "Ticket disputed and returned to Human Triage Queue",
            "ticket_id": updated.id,
            "ticket_status": updated.status.value,
            "assigned_team": updated.assigned_team,
            "escalation_level": updated.escalation_level,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
