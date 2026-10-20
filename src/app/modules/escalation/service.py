"""Escalation service: requester-chosen escalation, guardrails, response handling, and audit trails."""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import structlog
import yaml
from sqlalchemy.orm import Session

from src.app.errors import DomainError, EscalationGuardrailError, NotFoundError
from src.app.modules.directory.service import DirectoryService
from src.app.modules.sla.service import SlaService
from src.core.clock import Clock, ensure_utc
from src.db.models.assignment import Assignment
from src.db.models.audit import AuditLog
from src.db.models.escalation import Escalation
from src.db.models.feedback import Feedback
from src.db.models.sla import EtaChange, SlaClock
from src.db.models.ticket import Ticket
from src.db.models.user import Team, User

logger = structlog.get_logger()


class EscalationService:
    """Manages custom requester escalations, validates guardrails, and processes responses."""

    def __init__(
        self,
        directory_service: DirectoryService | None = None,
        sla_service: SlaService | None = None,
        rules_path: Path = Path("configs/escalation_rules.yaml"),
    ) -> None:
        self.directory = directory_service or DirectoryService()
        self.sla_service = sla_service or SlaService()
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: Path) -> dict[str, Any]:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("requester_escalation", {})
        return {}

    def get_eligibility(
        self, ticket: Ticket, requester_id: uuid.UUID, db: Session, clock: Clock
    ) -> dict[str, Any]:
        """Calculates 24-hour rate limit and cooldown status for ticket escalation."""
        now_dt = ensure_utc(clock.now())
        since_24h = now_dt - timedelta(hours=24)

        all_escalations = (
            db.query(Escalation)
            .filter(
                Escalation.ticket_id == ticket.id,
                Escalation.kind == "requester",
            )
            .order_by(Escalation.created_at.desc())
            .all()
        )
        recent_escalations = [e for e in all_escalations if ensure_utc(e.created_at) >= since_24h]

        used_last_24h = len(recent_escalations)
        max_per_24h = self.rules.get("max_per_24h", 2)
        cooldown_mins = self.rules.get("cooldown_minutes", 60)

        if ticket.status in ["Closed", "Resolved"]:
            return {
                "allowed": False,
                "used_last_24h": used_last_24h,
                "max_per_24h": max_per_24h,
                "next_allowed_at": None,
                "blocked_reason": "ticket_closed",
            }

        if used_last_24h >= max_per_24h:
            return {
                "allowed": False,
                "used_last_24h": used_last_24h,
                "max_per_24h": max_per_24h,
                "next_allowed_at": (
                    ensure_utc(recent_escalations[-1].created_at) + timedelta(hours=24)
                ).isoformat(),
                "blocked_reason": "rate_limit",
            }

        if recent_escalations:
            last_esc = recent_escalations[0]
            cooldown_end = ensure_utc(last_esc.created_at) + timedelta(minutes=cooldown_mins)
            if now_dt < cooldown_end:
                return {
                    "allowed": False,
                    "used_last_24h": used_last_24h,
                    "max_per_24h": max_per_24h,
                    "next_allowed_at": cooldown_end.isoformat(),
                    "blocked_reason": "cooldown",
                }

        return {
            "allowed": True,
            "used_last_24h": used_last_24h,
            "max_per_24h": max_per_24h,
            "next_allowed_at": None,
            "blocked_reason": None,
        }

    def raise_escalation(
        self,
        ticket_id: uuid.UUID,
        raised_by_id: uuid.UUID,
        target_user_id: uuid.UUID,
        reason_code: str,
        note: str,
        db: Session,
        clock: Clock,
    ) -> Escalation:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise NotFoundError("Ticket not found")

        # 1. Check eligibility (Rate limit & cooldown guardrails)
        eligibility = self.get_eligibility(ticket, raised_by_id, db, clock)
        if not eligibility["allowed"]:
            reason = eligibility["blocked_reason"]
            if reason == "rate_limit":
                raise EscalationGuardrailError(
                    "ESCALATION_RATE_LIMIT", "Maximum 2 escalations per 24 hours exceeded"
                )
            if reason == "cooldown":
                raise EscalationGuardrailError(
                    "ESCALATION_COOLDOWN",
                    f"Please wait for cooldown to expire at {eligibility['next_allowed_at']}",
                    details={"next_allowed_at": eligibility["next_allowed_at"]},
                )
            raise EscalationGuardrailError(
                "ESCALATION_NOT_ALLOWED", "Ticket cannot be escalated in its current status"
            )

        # 2. Self and owner guardrails
        if raised_by_id == target_user_id:
            raise EscalationGuardrailError(
                "ESCALATION_TARGET_SELF", "You cannot escalate a ticket to yourself"
            )
        if ticket.assignee_id and ticket.assignee_id == target_user_id:
            raise EscalationGuardrailError(
                "ESCALATION_TARGET_OWNER", "Target user already owns this ticket"
            )

        # 3. Target eligibility and leave check
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise NotFoundError("Target escalation recipient user not found")

        member_info = self.directory.get_member(target_user.email)
        if member_info and not member_info.get("escalation_eligible", True):
            raise EscalationGuardrailError(
                "ESCALATION_TARGET_INELIGIBLE",
                f"{target_user.name} is not marked as escalation-eligible in the directory",
            )

        now_dt = clock.now()
        if member_info:
            on_leave, leave_note, delegate = self.directory.is_on_leave(member_info, now_dt)
            if on_leave:
                raise EscalationGuardrailError(
                    "ESCALATION_TARGET_ON_LEAVE",
                    f"{target_user.name} is on leave ({leave_note}). Recommended delegate: {delegate}",
                    details={"delegate": delegate, "leave_note": leave_note},
                )

        # 4. Calculate response deadline (PRD 4B.6)
        is_critical = ticket.priority == "Critical"
        res_window_mins = (
            30 if is_critical else self.rules.get("response_window_minutes", {}).get("default", 120)
        )
        response_due = self.sla_service.calendar.add_business_seconds(now_dt, res_window_mins * 60)

        # 5. Create Escalation record
        escalation = Escalation(
            ticket_id=ticket.id,
            kind="requester",
            level="E2",
            raised_by=raised_by_id,
            target_user_id=target_user_id,
            reason_code=reason_code,
            note=note,
            status="pending",
            response_due=response_due,
            created_at=now_dt,
        )
        db.add(escalation)

        # Update ticket status
        ticket.is_escalated = True
        ticket.escalation_level = "E2"

        # 6. Wrong team feedback logging (PRD 4B.6)
        if reason_code == "wrong_team":
            fb = Feedback(
                ticket_id=ticket.id,
                kind="wrong_team_escalation",
                predicted_category=ticket.category,
                corrected_category=None,
                actor_id=raised_by_id,
                notes=f"Wrong team escalation: {note}",
                created_at=now_dt,
            )
            db.add(fb)

        # Audit log
        audit = AuditLog(
            ticket_id=ticket.id,
            entity_type="escalation",
            entity_id=str(escalation.id),
            action="escalation_raised",
            actor_id=raised_by_id,
            reason=reason_code,
            after={"target_user": target_user.name, "response_due": response_due.isoformat()},
            created_at=now_dt,
        )
        db.add(audit)
        db.commit()
        db.refresh(escalation)
        return escalation

    def respond(
        self,
        escalation_id: uuid.UUID,
        responder_id: uuid.UUID,
        action: str,  # accept | reassign | decline
        new_eta: datetime | None,
        reassign_to_id: uuid.UUID | None,
        reason_note: str | None,
        db: Session,
        clock: Clock,
    ) -> Escalation:
        esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc:
            raise NotFoundError("Escalation record not found")
        if esc.status != "pending":
            raise DomainError(
                "Escalation already responded", code="ESCALATION_ALREADY_RESPONDED", status_code=409
            )

        ticket = db.query(Ticket).filter(Ticket.id == esc.ticket_id).first()
        now_dt = clock.now()

        esc.responded_at = now_dt
        esc.responder_id = responder_id
        esc.outcome = action
        esc.outcome_note = reason_note
        esc.status = action

        if action == "accept":
            # Target becomes ticket owner
            ticket.assignee_id = esc.target_user_id
            ticket.status = "In progress"
            if new_eta:
                esc.new_eta = new_eta
                # Update SLA clock resolution due
                clock_rec = db.query(SlaClock).filter(SlaClock.ticket_id == ticket.id).first()
                if clock_rec:
                    clock_rec.resolution_due = new_eta
                eta_change = EtaChange(
                    ticket_id=ticket.id,
                    old_resolution_due=clock_rec.resolution_due if clock_rec else now_dt,
                    new_resolution_due=new_eta,
                    reason=f"Accepted escalation by {responder_id}",
                    actor_id=responder_id,
                    created_at=now_dt,
                )
                db.add(eta_change)

            # Record assignment
            fallback_team = db.query(Team).first()
            effective_team_id = ticket.team_id or (fallback_team.id if fallback_team else None)
            asgn = Assignment(
                ticket_id=ticket.id,
                assignee_id=esc.target_user_id,
                team_id=effective_team_id,
                reason="escalation_accept",
                assigned_by=responder_id,
                started_at=now_dt,
                created_at=now_dt,
            )
            db.add(asgn)

        elif action == "reassign":
            if not reassign_to_id:
                raise DomainError("Reassign target user is required", status_code=400)
            ticket.assignee_id = reassign_to_id
            esc.new_assignee_id = reassign_to_id
            if new_eta:
                esc.new_eta = new_eta
                clock_rec = db.query(SlaClock).filter(SlaClock.ticket_id == ticket.id).first()
                if clock_rec:
                    clock_rec.resolution_due = new_eta

            fallback_team = db.query(Team).first()
            effective_team_id = ticket.team_id or (fallback_team.id if fallback_team else None)
            asgn = Assignment(
                ticket_id=ticket.id,
                assignee_id=reassign_to_id,
                team_id=effective_team_id,
                reason="escalation_reassign",
                assigned_by=responder_id,
                started_at=now_dt,
                created_at=now_dt,
            )
            db.add(asgn)

        elif action == "decline":
            # Returns ticket to Team Lead with reason
            team_lead = self.directory.get_team_lead(ticket.category)
            if team_lead:
                lead_user = db.query(User).filter(User.email == team_lead["email"].lower()).first()
                if lead_user:
                    ticket.assigned_agent_id = lead_user.id
            ticket.status = "Assigned"

        # Audit
        audit = AuditLog(
            ticket_id=ticket.id,
            entity_type="escalation",
            entity_id=str(esc.id),
            action=f"escalation_{action}",
            actor_id=responder_id,
            reason=reason_note,
            created_at=now_dt,
        )
        db.add(audit)
        db.commit()
        db.refresh(esc)
        return esc
