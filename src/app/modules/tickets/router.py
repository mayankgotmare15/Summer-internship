"""FastAPI router for tickets, assignments, messages, escalations, and directory."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from src.app.deps import get_clock
from src.app.modules.tickets.controller import TicketController
from src.app.modules.tickets.schemas import (
    EscalateIn,
    EscalationRespondIn,
    MessageIn,
    MessageOut,
    StatusChangeIn,
    TicketCreatedOut,
    TicketCreateIn,
    TicketDetailOut,
)
from src.core.clock import Clock
from src.core.security import decode_access_token
from src.db.models.user import User
from src.db.session import get_db

router = APIRouter(prefix="", tags=["Ticket Lifecycle & Escalation"])
controller = TicketController()


def get_current_user_id(
    authorization: str | None = Header(None), db: Session = Depends(get_db)
) -> uuid.UUID:
    """Helper to extract user ID from auth header, or default to demo user."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            claims = decode_access_token(token)
            return uuid.UUID(claims.get("sub"))
        except Exception:
            pass

    # Default to demo requester for quick tests
    demo_u = db.query(User).filter(User.role == "requester").first()
    return demo_u.id if demo_u else uuid.uuid4()


@router.post(
    "/tickets",
    response_model=TicketCreatedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket, evaluate AI routing, assign engineer, and return SLA promise",
)
def create_ticket(
    payload: TicketCreateIn,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> TicketCreatedOut:
    return controller.create_ticket(payload, "requester@example.com", db, clock)


@router.get(
    "/tickets",
    response_model=list[TicketDetailOut],
    status_code=status.HTTP_200_OK,
    summary="List tickets filtered by view (all, mine, review_queue, my_queue)",
)
def list_tickets(
    view: str = Query("all", description="View filter: all, mine, review_queue, my_queue"),
    db: Session = Depends(get_db),
) -> list[TicketDetailOut]:
    return controller.list_tickets(view, db)


@router.get(
    "/tickets/{identifier}",
    response_model=TicketDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Get full ticket details, assignee, SLA timer, and activity timeline",
)
def get_ticket(
    identifier: str,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> TicketDetailOut:
    return controller.get_ticket(identifier, db, clock)


@router.post(
    "/tickets/{identifier}/status",
    response_model=TicketDetailOut,
    status_code=status.HTTP_200_OK,
    summary="Change ticket status (In progress, Waiting on requester, Resolved)",
)
def change_status(
    identifier: str,
    payload: StatusChangeIn,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> TicketDetailOut:
    return controller.change_status(identifier, payload, user_id, db, clock)


@router.post(
    "/tickets/{identifier}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Post message to ticket discussion thread",
)
def post_message(
    identifier: str,
    payload: MessageIn,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> MessageOut:
    return controller.post_message(identifier, payload, user_id, db, clock)


@router.post(
    "/tickets/{identifier}/escalate",
    status_code=status.HTTP_201_CREATED,
    summary="Requester-chosen escalation with guardrail enforcement",
)
def escalate_ticket(
    identifier: str,
    payload: EscalateIn,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, Any]:
    return controller.escalate_ticket(identifier, payload, user_id, db, clock)


@router.post(
    "/escalations/{escalation_id}/respond",
    status_code=status.HTTP_200_OK,
    summary="Respond to escalation (accept, reassign, decline)",
)
def respond_to_escalation(
    escalation_id: uuid.UUID,
    payload: EscalationRespondIn,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, Any]:
    return controller.respond_to_escalation(escalation_id, payload, user_id, db, clock)


@router.get(
    "/directory/members",
    status_code=status.HTTP_200_OK,
    summary="Search roster directory for assignment and escalation targets",
)
def search_directory(
    q: str = Query("", description="Search term for name, team, skills"),
    team: str | None = Query(None, description="Resolver team filter"),
    clock: Clock = Depends(get_clock),
) -> list[dict[str, Any]]:
    return controller.directory_service.search_members(query=q, for_team=team, at_dt=clock.now())


@router.post(
    "/internal/sla/tick",
    status_code=status.HTTP_200_OK,
    summary="Run SLA scheduler tick to advance ladder and check timeouts",
)
def sla_tick(
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, Any]:
    actions = controller.sla_service.evaluate_ladder(db, clock)
    return {"status": "ok", "actions": actions}
