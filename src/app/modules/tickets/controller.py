"""Ticket controller handling creation, assignment, lifecycle state transitions, messages, and escalation."""

import hashlib
import io
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

import structlog
from PIL import Image
from sqlalchemy.orm import Session

from src.app.errors import BadRequestError, NotFoundError
from src.app.modules.assignment.service import AssignmentService
from src.app.modules.directory.service import DirectoryService
from src.app.modules.escalation.service import EscalationService
from src.app.modules.inference.controller import TEAM_NAMES, InferenceController
from src.app.modules.inference.schemas import PredictionIn
from src.app.modules.sla.service import SlaService
from src.app.modules.tickets.schemas import (
    AttachmentOut,
    EscalateIn,
    EscalationRespondIn,
    MemberRef,
    MessageIn,
    MessageOut,
    StatusChangeIn,
    TeamRef,
    TicketCreatedOut,
    TicketCreateIn,
    TicketDetailOut,
)
from src.app.settings import get_settings
from src.core.clock import Clock, ensure_utc
from src.core.ids import generate_public_id
from src.db.models.assignment import Assignment
from src.db.models.attachment import Attachment
from src.db.models.escalation import Approval
from src.db.models.idempotency import IdempotencyKey
from src.db.models.notification import Notification
from src.db.models.sla import SlaClock
from src.db.models.ticket import Ticket, TicketMessage
from src.db.models.user import Team, User

logger = structlog.get_logger()

# Categories that mandate an approval stage before assignment (PRD 4A.2 & 4B.4)
APPROVAL_CATEGORIES = {"Administrative rights", "Purchase"}


def strip_exif(content_type: str, file_bytes: bytes) -> bytes:
    """Strips GPS and camera metadata from image files."""
    ct = content_type.lower()
    if ct in ["image/jpeg", "image/png", "image/webp"]:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            out_buf = io.BytesIO()
            fmt = "JPEG" if "jpeg" in ct else ("PNG" if "png" in ct else "WEBP")
            if fmt == "JPEG" and image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.save(out_buf, format=fmt)
            return out_buf.getvalue()
        except Exception as exc:
            logger.warning("Failed to strip EXIF from image", error=str(exc))
            return file_bytes
    return file_bytes



class TicketController:
    """Orchestrates ticket creation, automated routing, assignment, and escalation workflows."""

    def __init__(self) -> None:
        self.inference_controller = InferenceController()
        self.directory_service = DirectoryService()
        self.assignment_service = AssignmentService(self.directory_service)
        self.sla_service = SlaService()
        self.escalation_service = EscalationService(self.directory_service, self.sla_service)

    def _resolve_team_record(self, team_code: str, db: Session) -> Team:
        team = db.query(Team).filter(Team.code == team_code).first()
        if not team:
            team = Team(code=team_code, name=TEAM_NAMES.get(team_code, team_code))
            db.add(team)
            db.commit()
            db.refresh(team)
        return team

    def create_ticket(
        self,
        payload: TicketCreateIn,
        requester_email: str,
        db: Session,
        clock: Clock,
        idempotency_key: str | None = None,
    ) -> TicketCreatedOut:
        # 1. Resolve requester
        requester = db.query(User).filter(User.email == requester_email.lower()).first()
        if not requester:
            requester = db.query(User).filter(User.role == "requester").first()
            if not requester:
                requester = User(
                    email=requester_email,
                    name=requester_email.split("@")[0],
                    password_hash="mock",
                    role="requester",
                )
                db.add(requester)
                db.commit()
                db.refresh(requester)

        req_hash = hashlib.sha256(
            f"{payload.subject}:{payload.description}:{payload.channel}:{payload.blocking_team}".encode()
        ).hexdigest()

        if idempotency_key and requester:
            existing_key = (
                db.query(IdempotencyKey)
                .filter(
                    IdempotencyKey.user_id == requester.id,
                    IdempotencyKey.key == idempotency_key,
                )
                .first()
            )
            if existing_key:
                return TicketCreatedOut(**json.loads(existing_key.response_body))

        full_text = f"{payload.subject}\n{payload.description}"
        text_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
        public_id = generate_public_id(db=db)

        # 2. Run inference & decision logic
        pred_res = self.inference_controller.predict(
            PredictionIn(
                text=full_text, blocking_team=payload.blocking_team, source="ticket_create"
            ),
            db=db,
            actor_id=requester.id,
        )


        team_code = pred_res.routed_team.code
        team_record = self._resolve_team_record(team_code, db)

        now_dt = clock.now()
        ticket_id = uuid.uuid4()

        assigned_user: User | None = None
        first_resp_due: datetime | None = None
        resol_due: datetime | None = None
        review_promise: datetime | None = None
        awaiting_approval: MemberRef | None = None

        # 3. Decision branches
        if pred_res.decision == "auto_route":
            if pred_res.category in APPROVAL_CATEGORIES:
                # Requires approval step first
                ticket_status = "Awaiting approval"
                # Assign approver: line manager or security lead
                approver = db.query(User).filter(User.email == "rahul.verma@example.com").first()
                if approver:
                    approval = Approval(
                        ticket_id=ticket_id,
                        approver_id=approver.id,
                        status="pending",
                        due_at=self.sla_service.calendar.add_business_seconds(now_dt, 8 * 3600),
                    )
                    db.add(approval)
                    awaiting_approval = MemberRef(
                        id=approver.id, name=approver.name, email=approver.email, role=approver.role
                    )
            else:
                # Direct assignment
                ticket_status = "Assigned"
                assigned_user, rule_trace = self.assignment_service.assign_ticket(
                    team_code=team_code,
                    priority=pred_res.priority,
                    ticket_text=full_text,
                    db=db,
                    clock=clock,
                )
                # Start SLA Clock
                mock_ticket = Ticket(id=ticket_id, priority=pred_res.priority)
                sla_clock = self.sla_service.start_clock(mock_ticket, db, clock)
                first_resp_due = sla_clock.first_response_due
                resol_due = sla_clock.resolution_due

                # Record Assignment
                asgn = Assignment(
                    ticket_id=ticket_id,
                    assignee_id=assigned_user.id,
                    team_id=team_record.id,
                    reason="auto",
                    rule_trace=rule_trace,
                    started_at=now_dt,
                )
                db.add(asgn)
        else:
            # Human Review Queue (L1 Triage)
            ticket_status = "New"
            team_record = self._resolve_team_record("SERVICE_DESK", db)
            review_promise = now_dt + timedelta(minutes=30)

        # 4. Save Ticket Entity
        ticket = Ticket(
            id=ticket_id,
            public_id=public_id,
            requester_id=requester.id,
            subject=payload.subject,
            description=payload.description,
            text_hash=text_hash,
            channel=payload.channel,
            category=pred_res.category,
            priority=pred_res.priority,
            priority_source=pred_res.priority_source,
            decision=pred_res.decision,
            review_reason=pred_res.review_reason,
            status=ticket_status,
            team_id=team_record.id,
            assignee_id=assigned_user.id if assigned_user else None,
            created_at=now_dt,
            updated_at=now_dt,
        )
        db.add(ticket)

        # 5. Save initial message
        msg = TicketMessage(
            ticket_id=ticket.id,
            author_id=requester.id,
            kind="public",
            body=payload.description,
            created_at=now_dt,
        )
        db.add(msg)

        # 6. Notifications (In-app + email dispatch)
        if assigned_user:
            notif = Notification(
                user_id=assigned_user.id,
                ticket_id=ticket.id,
                event_type="ticket_assigned",
                title=f"New Ticket {public_id} Assigned ({pred_res.priority})",
                body=f"Assigned {payload.subject}. First response by {first_resp_due.strftime('%I:%M %p') if first_resp_due else 'SLA'}.",
                link=f"/tickets/{public_id}",
            )
            db.add(notif)

        db.commit()
        db.refresh(ticket)

        assignee_ref = None
        if assigned_user:
            assignee_ref = MemberRef(
                id=assigned_user.id,
                name=assigned_user.name,
                email=assigned_user.email,
                role=assigned_user.role,
            )

        team_ref = TeamRef(
            code=team_record.code,
            name=TEAM_NAMES.get(team_record.code, team_record.name),
        )

        result = TicketCreatedOut(
            id=public_id,
            ticket_uuid=ticket.id,
            status=ticket.status,
            category=ticket.category,
            priority=ticket.priority,
            decision=pred_res.decision,
            assignee=assignee_ref,
            team=team_ref,
            first_response_due=first_resp_due,
            resolution_due=resol_due,
            awaiting_approval_from=awaiting_approval,
            review_promise_by=review_promise,
            can_escalate=ticket_status in ["Assigned", "In progress"],
        )

        if idempotency_key and requester:
            ik = IdempotencyKey(
                user_id=requester.id,
                key=idempotency_key,
                request_hash=req_hash,
                response_status=201,
                response_body=result.model_dump_json(),
            )
            db.add(ik)
            db.commit()

        return result


    def get_ticket(self, identifier: str, db: Session, clock: Clock) -> TicketDetailOut:
        """Finds ticket by public_id (e.g. T-1042) or UUID."""
        ticket = None
        try:
            val_uuid = uuid.UUID(identifier)
            ticket = db.query(Ticket).filter(Ticket.id == val_uuid).first()
        except ValueError:
            ticket = db.query(Ticket).filter(Ticket.public_id == identifier.upper()).first()

        if not ticket:
            raise NotFoundError(f"Ticket '{identifier}' not found")

        # Resolve relations
        team_rec = db.query(Team).filter(Team.id == ticket.team_id).first()
        team_ref = TeamRef(
            code=team_rec.code if team_rec else "SERVICE_DESK",
            name=TEAM_NAMES.get(team_rec.code if team_rec else "SERVICE_DESK", "Service Desk"),
        )

        assignee_ref = None
        if ticket.assignee_id:
            assignee = db.query(User).filter(User.id == ticket.assignee_id).first()
            if assignee:
                assignee_ref = MemberRef(
                    id=assignee.id, name=assignee.name, email=assignee.email, role=assignee.role
                )

        sla_clock = db.query(SlaClock).filter(SlaClock.ticket_id == ticket.id).first()

        # Messages
        raw_msgs = (
            db.query(TicketMessage)
            .filter(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.created_at.asc())
            .all()
        )
        messages_out = []
        for m in raw_msgs:
            author_name = "System"
            if m.author_id:
                u = db.query(User).filter(User.id == m.author_id).first()
                if u:
                    author_name = u.name
            messages_out.append(
                MessageOut(
                    id=m.id,
                    author_name=author_name,
                    kind=m.kind,
                    body=m.body,
                    created_at=m.created_at,
                )
            )

        # Attachments
        raw_atts = (
            db.query(Attachment)
            .filter(Attachment.ticket_id == ticket.id)
            .order_by(Attachment.created_at.asc())
            .all()
        )
        attachments_out = [
            AttachmentOut(
                id=a.id,
                ticket_id=a.ticket_id,
                uploader_id=a.uploader_id,
                filename=a.filename,
                content_type=a.content_type,
                size_bytes=a.size_bytes,
                created_at=ensure_utc(a.created_at),
            )
            for a in raw_atts
        ]

        eligibility = self.escalation_service.get_eligibility(
            ticket, ticket.requester_id, db, clock
        )

        return TicketDetailOut(
            id=ticket.public_id,
            ticket_uuid=ticket.id,
            subject=ticket.subject,
            description=ticket.description,
            category=ticket.category,
            priority=ticket.priority,
            priority_source=ticket.priority_source,
            status=ticket.status,
            decision=ticket.decision,
            review_reason=ticket.review_reason,
            team=team_ref,
            assignee=assignee_ref,
            is_escalated=ticket.is_escalated,
            escalation_level=ticket.escalation_level,
            first_response_due=ensure_utc(sla_clock.first_response_due) if sla_clock else None,
            resolution_due=ensure_utc(sla_clock.resolution_due) if sla_clock else None,
            first_responded_at=ensure_utc(ticket.first_responded_at),
            clock_state=sla_clock.state if sla_clock else None,
            messages=messages_out,
            attachments=attachments_out,
            can_escalate=eligibility["allowed"],
            escalation_eligibility=eligibility,
            created_at=ensure_utc(ticket.created_at),
        )


    def list_tickets(
        self,
        view: str,
        db: Session,
        user_email: str | None = None,
        limit: int = 50,
    ) -> list[TicketDetailOut]:
        q = db.query(Ticket)
        if view == "review_queue":
            q = q.filter(Ticket.status == "New", Ticket.decision == "human_review")
        elif view == "mine" and user_email:
            u = db.query(User).filter(User.email == user_email.lower()).first()
            if u:
                q = q.filter(Ticket.requester_id == u.id)
        elif view == "my_queue" and user_email:
            u = db.query(User).filter(User.email == user_email.lower()).first()
            if u:
                q = q.filter(Ticket.assignee_id == u.id)

        tickets = q.order_by(Ticket.created_at.desc()).limit(limit).all()
        from src.core.clock import SystemClock

        sys_clock = SystemClock()

        return [self.get_ticket(str(t.id), db, sys_clock) for t in tickets]

    def change_status(
        self,
        identifier: str,
        payload: StatusChangeIn,
        actor_id: uuid.UUID | None,
        db: Session,
        clock: Clock,
    ) -> TicketDetailOut:
        ticket = (
            db.query(Ticket)
            .filter((Ticket.public_id == identifier.upper()) | (Ticket.id == identifier))
            .first()
        )
        if not ticket:
            raise NotFoundError("Ticket not found")

        old_status = ticket.status
        ticket.status = payload.to_status
        ticket.version += 1

        now_dt = clock.now()

        # Handle SLA clock pause / resume / stop
        if payload.to_status == "Waiting on requester":
            self.sla_service.pause_clock(ticket, db, clock)
        elif old_status == "Waiting on requester" and payload.to_status == "In progress":
            self.sla_service.resume_clock(ticket, db, clock)
        elif payload.to_status in ["Resolved", "Closed"]:
            self.sla_service.stop_clock(ticket, db, clock)
            ticket.resolved_at = now_dt
            if payload.to_status == "Closed":
                ticket.closed_at = now_dt

        # If engineer responds for the first time
        if (
            not ticket.first_responded_at
            and old_status == "Assigned"
            and payload.to_status == "In progress"
        ):
            self.sla_service.record_first_response(ticket, db, clock)

        if payload.note:
            msg = TicketMessage(
                ticket_id=ticket.id,
                author_id=actor_id,
                kind="public",
                body=f"Status changed to {payload.to_status}: {payload.note}",
                created_at=now_dt,
            )
            db.add(msg)

        db.commit()
        return self.get_ticket(str(ticket.id), db, clock)

    def post_message(
        self,
        identifier: str,
        payload: MessageIn,
        author_id: uuid.UUID | None,
        db: Session,
        clock: Clock,
        idempotency_key: str | None = None,
    ) -> MessageOut:
        ticket = (
            db.query(Ticket)
            .filter((Ticket.public_id == identifier.upper()) | (Ticket.id == identifier))
            .first()
        )
        if not ticket:
            raise NotFoundError("Ticket not found")

        req_hash = hashlib.sha256(
            f"{identifier}:{payload.body}:{payload.internal}".encode()
        ).hexdigest()

        if idempotency_key and author_id:
            existing_key = (
                db.query(IdempotencyKey)
                .filter(
                    IdempotencyKey.user_id == author_id,
                    IdempotencyKey.key == idempotency_key,
                )
                .first()
            )
            if existing_key:
                return MessageOut(**json.loads(existing_key.response_body))

        now_dt = clock.now()
        msg = TicketMessage(
            ticket_id=ticket.id,
            author_id=author_id,
            kind="internal" if payload.internal else "public",
            body=payload.body,
            created_at=now_dt,
        )
        db.add(msg)

        # If requester replies while clock was paused, resume clock!
        if ticket.status == "Waiting on requester" and author_id == ticket.requester_id:
            ticket.status = "In progress"
            self.sla_service.resume_clock(ticket, db, clock)

        db.commit()
        db.refresh(msg)

        author_name = "User"
        if author_id:
            u = db.query(User).filter(User.id == author_id).first()
            if u:
                author_name = u.name

        result = MessageOut(
            id=msg.id,
            author_name=author_name,
            kind=msg.kind,
            body=msg.body,
            created_at=msg.created_at,
        )

        if idempotency_key and author_id:
            ik = IdempotencyKey(
                user_id=author_id,
                key=idempotency_key,
                request_hash=req_hash,
                response_status=201,
                response_body=result.model_dump_json(),
            )
            db.add(ik)
            db.commit()

        return result


    def escalate_ticket(
        self,
        identifier: str,
        payload: EscalateIn,
        requester_id: uuid.UUID,
        db: Session,
        clock: Clock,
    ) -> dict[str, Any]:
        ticket = (
            db.query(Ticket)
            .filter((Ticket.public_id == identifier.upper()) | (Ticket.id == identifier))
            .first()
        )
        if not ticket:
            raise NotFoundError("Ticket not found")

        esc = self.escalation_service.raise_escalation(
            ticket_id=ticket.id,
            raised_by_id=requester_id,
            target_user_id=payload.target_user_id,
            reason_code=payload.reason_code,
            note=payload.note,
            db=db,
            clock=clock,
        )
        return {
            "escalation_id": esc.id,
            "status": esc.status,
            "response_due": esc.response_due.isoformat(),
            "level": esc.level,
        }

    def respond_to_escalation(
        self,
        escalation_id: uuid.UUID,
        payload: EscalationRespondIn,
        responder_id: uuid.UUID,
        db: Session,
        clock: Clock,
    ) -> dict[str, Any]:
        esc = self.escalation_service.respond(
            escalation_id=escalation_id,
            responder_id=responder_id,
            action=payload.action,
            new_eta=payload.new_eta,
            reassign_to_id=payload.reassign_to_id,
            reason_note=payload.reason_note,
            db=db,
            clock=clock,
        )
        return {
            "escalation_id": esc.id,
            "outcome": esc.outcome,
            "status": esc.status,
            "new_eta": esc.new_eta.isoformat() if esc.new_eta else None,
        }

    def upload_attachment(
        self,
        identifier: str,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        user_id: uuid.UUID,
        db: Session,
        clock: Clock,
    ) -> AttachmentOut:
        """B6: Validates, strips EXIF, stores file to disk, and records ticket attachment."""
        ticket = (
            db.query(Ticket)
            .filter((Ticket.public_id == identifier.upper()) | (Ticket.id == identifier))
            .first()
        )
        if not ticket:
            raise NotFoundError("Ticket not found")

        allowed_types = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
        if content_type.lower() not in allowed_types:
            raise BadRequestError(
                f"Unsupported file type '{content_type}'. Allowed types: JPEG, PNG, WebP, PDF.",
                code="UNSUPPORTED_MEDIA_TYPE",
            )

        max_bytes = 10 * 1024 * 1024  # 10 MB
        if len(file_bytes) > max_bytes:
            raise BadRequestError(
                "File size exceeds maximum allowed limit of 10 MB.",
                code="ATTACHMENT_TOO_LARGE",
            )

        count = db.query(Attachment).filter(Attachment.ticket_id == ticket.id).count()
        if count >= 5:
            raise BadRequestError(
                "Maximum limit of 5 attachments per ticket reached.",
                code="MAX_ATTACHMENTS_EXCEEDED",
            )

        clean_bytes = strip_exif(content_type, file_bytes)

        settings = get_settings()
        upload_dir = os.path.join(settings.upload_dir, str(ticket.id))
        os.makedirs(upload_dir, exist_ok=True)

        att_id = uuid.uuid4()
        safe_name = os.path.basename(filename).replace(" ", "_")
        storage_path = os.path.join(upload_dir, f"{att_id}_{safe_name}")

        with open(storage_path, "wb") as f:
            f.write(clean_bytes)

        now_dt = clock.now()
        attachment = Attachment(
            id=att_id,
            ticket_id=ticket.id,
            uploader_id=user_id,
            filename=safe_name,
            content_type=content_type,
            size_bytes=len(clean_bytes),
            storage_path=storage_path,
            created_at=now_dt,
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)

        return AttachmentOut(
            id=attachment.id,
            ticket_id=attachment.ticket_id,
            uploader_id=attachment.uploader_id,
            filename=attachment.filename,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            created_at=ensure_utc(attachment.created_at),
        )

    def get_attachment(
        self,
        identifier: str,
        attachment_id: uuid.UUID,
        db: Session,
    ) -> tuple[Attachment, str]:
        """Retrieves attachment record and verified storage path on disk."""
        ticket = (
            db.query(Ticket)
            .filter((Ticket.public_id == identifier.upper()) | (Ticket.id == identifier))
            .first()
        )
        if not ticket:
            raise NotFoundError("Ticket not found")

        attachment = (
            db.query(Attachment)
            .filter(Attachment.id == attachment_id, Attachment.ticket_id == ticket.id)
            .first()
        )
        if not attachment:
            raise NotFoundError("Attachment not found")

        if not os.path.exists(attachment.storage_path):
            raise NotFoundError("Attachment file not found on storage disk")

        return attachment, attachment.storage_path

