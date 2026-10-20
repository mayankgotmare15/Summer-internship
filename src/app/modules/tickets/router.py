"""FastAPI router for tickets, assignments, messages, escalations, directory, and attachments."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.app.deps import get_clock, get_current_user_id
from src.app.modules.tickets.controller import TicketController
from src.app.modules.tickets.schemas import (
    AttachmentOut,
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
from src.db.session import get_db

router = APIRouter(prefix="", tags=["Ticket Lifecycle & Escalation"])
controller = TicketController()


@router.post(
    "/tickets",
    response_model=TicketCreatedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket, evaluate AI routing, assign engineer, and return SLA promise",
)
def create_ticket(
    payload: TicketCreateIn,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> TicketCreatedOut:
    return controller.create_ticket(
        payload, "requester@example.com", db, clock, idempotency_key=idempotency_key
    )


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
    summary="Post message to ticket discussion thread (supports Idempotency-Key)",
)
def post_message(
    identifier: str,
    payload: MessageIn,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> MessageOut:
    return controller.post_message(
        identifier, payload, user_id, db, clock, idempotency_key=idempotency_key
    )


@router.post(
    "/tickets/{identifier}/attachments",
    response_model=AttachmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file attachment (max 10MB, images & PDF)",
)
async def upload_attachment(
    identifier: str,
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> AttachmentOut:
    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "attachment"
    return controller.upload_attachment(
        identifier=identifier,
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
        user_id=user_id,
        db=db,
        clock=clock,
    )


@router.get(
    "/tickets/{identifier}/attachments/{attachment_id}",
    summary="Download or stream ticket file attachment",
)
def get_attachment(
    identifier: str,
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> FileResponse:
    att, path = controller.get_attachment(identifier, attachment_id, db)
    return FileResponse(
        path=path,
        media_type=att.content_type,
        filename=att.filename,
    )


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
