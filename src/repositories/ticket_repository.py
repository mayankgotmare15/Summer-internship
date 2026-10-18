"""
Repository layer managing ticket persistence, event audit trails, and state transitions.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import FeedbackSubmission, Ticket, TicketEvent, TicketStatus

SLA_DURATIONS = {
    "Critical": timedelta(hours=1),
    "High": timedelta(hours=4),
    "Medium": timedelta(hours=24),
    "Low": timedelta(hours=72),
}


class TicketRepository:
    @staticmethod
    def create_ticket(
        db: Session,
        text: str,
        predicted_category: str,
        category_confidence: float,
        predicted_priority: str,
        priority_confidence: float,
        priority_overridden: bool,
        decision: str,
        assigned_team: str,
        model_version: str,
        ticket_id: str | None = None,
    ) -> Ticket:
        """Persists a new ticket with initial audit event."""
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        tid = ticket_id or f"TKT-{text_hash[:8].upper()}"

        now = datetime.now(timezone.utc)
        sla_deadline = now + SLA_DURATIONS.get(predicted_priority, timedelta(hours=24))

        if priority_overridden and predicted_priority == "Critical":
            escalation_level = 3
            status = TicketStatus.ESCALATED_L3
            assigned_team = "Project Engineering & DevOps"
            escalation_reason = "Automated Emergency Escalation: Critical system override detected"
        elif decision == "auto_route":
            escalation_level = 2
            status = TicketStatus.AUTO_ROUTED
            escalation_reason = None
        else:
            escalation_level = 1
            status = TicketStatus.PENDING_TRIAGE
            escalation_reason = None

        existing = db.query(Ticket).filter(Ticket.id == tid).first()
        if existing:
            existing.text = text
            existing.text_hash = text_hash
            existing.predicted_category = predicted_category
            existing.category_confidence = category_confidence
            existing.predicted_priority = predicted_priority
            existing.priority_confidence = priority_confidence
            existing.priority_overridden = priority_overridden
            existing.decision = decision
            existing.status = status
            existing.assigned_team = assigned_team
            existing.model_version = model_version
            existing.escalation_level = escalation_level
            existing.escalation_reason = escalation_reason
            existing.sla_deadline = sla_deadline
            existing.sla_breached = False
            existing.reassignment_count = 0
            existing.updated_at = now
            db.commit()
            db.refresh(existing)
            return existing

        ticket = Ticket(
            id=tid,
            text=text,
            text_hash=text_hash,
            predicted_category=predicted_category,
            category_confidence=category_confidence,
            predicted_priority=predicted_priority,
            priority_confidence=priority_confidence,
            priority_overridden=priority_overridden,
            decision=decision,
            status=status,
            assigned_team=assigned_team,
            model_version=model_version,
            escalation_level=escalation_level,
            escalation_reason=escalation_reason,
            sla_deadline=sla_deadline,
            sla_breached=False,
            reassignment_count=0,
        )
        db.add(ticket)

        event = TicketEvent(
            ticket_id=tid,
            actor_id="system_ml_classifier",
            actor_role="system",
            action="ticket_ingested",
            previous_state=None,
            new_state=status.value,
            notes=f"Model classified as '{predicted_category}' with confidence {category_confidence:.2f}. Decision: {decision}",
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_ticket(db: Session, ticket_id: str) -> Ticket | None:
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()

    @staticmethod
    def list_triage_queue(db: Session, limit: int = 50) -> list[Ticket]:
        return (
            db.query(Ticket)
            .filter(Ticket.status == TicketStatus.PENDING_TRIAGE)
            .order_by(Ticket.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_department_queue(db: Session, team_name: str, limit: int = 100) -> list[Ticket]:
        return (
            db.query(Ticket)
            .filter(
                Ticket.assigned_team == team_name,
                Ticket.status != TicketStatus.PENDING_TRIAGE,
            )
            .order_by(Ticket.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def override_triage(
        db: Session,
        ticket_id: str,
        new_category: str,
        new_team: str,
        new_priority: str | None,
        actor_id: str,
        actor_role: str,
        notes: str | None = None,
    ) -> Ticket:
        """Triage agent corrects queue assignment and records feedback."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        prev_cat = ticket.predicted_category
        prev_status = ticket.status.value

        ticket.predicted_category = new_category
        ticket.assigned_team = new_team
        if new_priority:
            ticket.predicted_priority = new_priority
        ticket.status = TicketStatus.AUTO_ROUTED
        ticket.decision = "human_overridden"

        # Record Feedback for MLOps Continuous Retraining
        feedback = FeedbackSubmission(
            ticket_id=ticket_id,
            submitted_by=actor_id,
            predicted_category=prev_cat,
            corrected_category=new_category,
            is_override=(prev_cat != new_category),
            notes=notes,
        )
        db.add(feedback)

        # Audit event
        event = TicketEvent(
            ticket_id=ticket_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="triage_override",
            previous_state=prev_status,
            new_state=TicketStatus.AUTO_ROUTED.value,
            notes=f"Overridden from '{prev_cat}' to '{new_category}'. Routed to '{new_team}'. Notes: {notes or 'None'}",
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def approve_triage(
        db: Session,
        ticket_id: str,
        actor_id: str,
        actor_role: str,
    ) -> Ticket:
        """Triage agent approves model's recommended queue."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        prev_status = ticket.status.value
        ticket.status = TicketStatus.AUTO_ROUTED

        event = TicketEvent(
            ticket_id=ticket_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="triage_approved",
            previous_state=prev_status,
            new_state=TicketStatus.AUTO_ROUTED.value,
            notes="Agent confirmed model routing assignment.",
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def update_status(
        db: Session,
        ticket_id: str,
        new_status: TicketStatus,
        actor_id: str,
        actor_role: str,
        notes: str | None = None,
    ) -> Ticket:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        prev_status = ticket.status.value
        ticket.status = new_status

        event = TicketEvent(
            ticket_id=ticket_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="status_updated",
            previous_state=prev_status,
            new_state=new_status.value,
            notes=notes,
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def assign_agent(
        db: Session,
        ticket_id: str,
        assigned_agent: str,
        actor_id: str,
        actor_role: str,
    ) -> Ticket:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        ticket.assigned_agent = assigned_agent
        if ticket.status == TicketStatus.AUTO_ROUTED:
            ticket.status = TicketStatus.IN_PROGRESS

        event = TicketEvent(
            ticket_id=ticket_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="agent_assigned",
            previous_state=ticket.status.value,
            new_state=TicketStatus.IN_PROGRESS.value,
            notes=f"Ticket assigned to engineer '{assigned_agent}'",
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def dispute_ticket(
        db: Session,
        ticket_id: str,
        actor_id: str,
        actor_role: str,
        dispute_reason: str,
    ) -> Ticket:
        """Resolver Lead rejects misrouted ticket. If bounces >= 2, auto-escalates to Manager."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        prev_team = ticket.assigned_team
        ticket.reassignment_count = (ticket.reassignment_count or 0) + 1

        if ticket.reassignment_count >= 2:
            ticket.escalation_level = 4
            ticket.status = TicketStatus.MANAGEMENT_ESCALATED
            ticket.assigned_team = "IT Operations Management / Incident Command"
            ticket.escalation_reason = (
                f"Multi-Bounce Guard ({ticket.reassignment_count} bounces): {dispute_reason}"
            )
            new_target = "IT Operations Management / Incident Command"
            notes = f"Dispute bounce threshold breached. Auto-escalated to Incident Commander by {actor_id}: {dispute_reason}"
        else:
            ticket.status = TicketStatus.PENDING_TRIAGE
            ticket.assigned_team = "Human Triage Queue"
            new_target = "Human Triage Queue"
            notes = f"Disputed by {actor_id}: {dispute_reason} (Bounce count: {ticket.reassignment_count})"

        event = TicketEvent(
            ticket_id=ticket_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action="routing_disputed",
            previous_state=prev_team,
            new_state=new_target,
            notes=notes,
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def escalate_ticket(
        db: Session,
        ticket_id: str,
        target_level: int,
        reason: str,
        actor_id: str,
        actor_role: str,
        target_team: str | None = None,
    ) -> Ticket:
        """Promotes a ticket to Tier 2 (L2), Tier 3 (L3 Specialist), or Tier 4 (Manager)."""
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        prev_status = ticket.status.value
        ticket.escalation_level = target_level
        ticket.escalation_reason = reason
        ticket.escalated_by = actor_id

        if target_level == 2:
            ticket.status = TicketStatus.ESCALATED_L2
            if target_team:
                ticket.assigned_team = target_team
        elif target_level == 3:
            ticket.status = TicketStatus.ESCALATED_L3
            ticket.assigned_team = target_team or "Project Engineering & DevOps"
        elif target_level >= 4:
            ticket.status = TicketStatus.MANAGEMENT_ESCALATED
            ticket.assigned_team = "IT Operations Management / Incident Command"

        event = TicketEvent(
            ticket_id=ticket_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action=f"escalated_to_l{target_level}",
            previous_state=prev_status,
            new_state=ticket.status.value,
            notes=f"Escalated to Tier {target_level} by {actor_id}. Reason: {reason}",
        )
        db.add(event)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def list_escalations(
        db: Session,
        min_level: int = 2,
        limit: int = 100,
    ) -> list[Ticket]:
        """Lists active escalated tickets."""
        return (
            db.query(Ticket)
            .filter(
                Ticket.escalation_level >= min_level,
                Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            )
            .order_by(Ticket.escalation_level.desc(), Ticket.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_l3_queue(db: Session, limit: int = 100) -> list[Ticket]:
        """Lists tickets for Tier 3 Senior DevOps & Incident Lead."""
        return (
            db.query(Ticket)
            .filter(
                (Ticket.escalation_level == 3) | (Ticket.assigned_team == "Project Engineering & DevOps"),
                Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            )
            .order_by(Ticket.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_manager_escalations(db: Session, limit: int = 100) -> list[Ticket]:
        """Lists tickets requiring IT Operations Manager intervention (Level 4, SLA breached, multi-bounce)."""
        return (
            db.query(Ticket)
            .filter(
                (Ticket.escalation_level >= 4)
                | (Ticket.sla_breached.is_(True))
                | (Ticket.reassignment_count >= 2)
                | (Ticket.status == TicketStatus.MANAGEMENT_ESCALATED),
                Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            )
            .order_by(Ticket.sla_breached.desc(), Ticket.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def check_and_update_sla(db: Session) -> dict[str, Any]:
        """Scans active tickets against SLA deadlines and marks breaches/triggers auto-escalation."""
        now = datetime.now(timezone.utc)
        active_tickets = (
            db.query(Ticket)
            .filter(Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]))
            .all()
        )

        breached_count = 0
        auto_escalated_count = 0

        for t in active_tickets:
            if t.sla_deadline:
                deadline = (
                    t.sla_deadline.replace(tzinfo=timezone.utc)
                    if t.sla_deadline.tzinfo is None
                    else t.sla_deadline
                )
                if now > deadline:
                    if not t.sla_breached:
                        t.sla_breached = True
                        breached_count += 1
                        if t.escalation_level < 4:
                            t.escalation_level = 4
                            t.status = TicketStatus.MANAGEMENT_ESCALATED
                            t.escalation_reason = "Automated SLA Breach Escalation"
                            auto_escalated_count += 1
                            event = TicketEvent(
                                ticket_id=t.id,
                                actor_id="system_sla_daemon",
                                actor_role="system",
                                action="sla_breach_escalation",
                                previous_state=t.status.value,
                                new_state=TicketStatus.MANAGEMENT_ESCALATED.value,
                                notes=f"SLA expired at {t.sla_deadline.isoformat()}. Escalated to Incident Command.",
                            )
                            db.add(event)

        if breached_count > 0:
            db.commit()

        return {
            "scanned_count": len(active_tickets),
            "new_breaches": breached_count,
            "auto_escalated": auto_escalated_count,
            "checked_at": now.isoformat(),
        }

    @staticmethod
    def get_analytics(
        db: Session,
        N: int = 5000,
        t: float = 3.0,
        c: float = 15.0,
        r: float = 10.0,
    ) -> dict[str, Any]:
        """Calculates executive ROI & operational KPIs."""
        total = db.query(Ticket).count()
        if total == 0:
            return {
                "total_tickets": 0,
                "auto_route_rate": 0.0,
                "routed_accuracy": 0.90,
                "override_rate": 0.0,
                "pending_triage_count": 0,
                "net_hours_saved_monthly": 0.0,
                "net_cost_saved_usd": 0.0,
                "department_distribution": {},
            }

        auto_routed_count = db.query(Ticket).filter(Ticket.decision == "auto_route").count()
        auto_route_rate = auto_routed_count / total if total > 0 else 0.0

        feedback_total = db.query(FeedbackSubmission).count()
        overrides = (
            db.query(FeedbackSubmission).filter(FeedbackSubmission.is_override.is_(True)).count()
        )
        override_rate = (overrides / feedback_total) if feedback_total > 0 else 0.0

        accuracy = 1.0 - override_rate if feedback_total > 0 else 0.92

        # Net Business Formula: N * a * [ t - (1 - p) * c ]
        net_minutes = N * auto_route_rate * (t - (1.0 - accuracy) * c)
        net_hours = net_minutes / 60.0
        net_cost = net_hours * r

        dept_counts = (
            db.query(Ticket.assigned_team, func.count(Ticket.id))
            .group_by(Ticket.assigned_team)
            .all()
        )

        return {
            "total_tickets": total,
            "auto_route_rate": round(auto_route_rate, 4),
            "routed_accuracy": round(accuracy, 4),
            "override_rate": round(override_rate, 4),
            "pending_triage_count": db.query(Ticket)
            .filter(Ticket.status == TicketStatus.PENDING_TRIAGE)
            .count(),
            "escalations_count": db.query(Ticket)
            .filter(
                Ticket.escalation_level >= 2,
                Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            )
            .count(),
            "l3_count": db.query(Ticket)
            .filter(
                Ticket.escalation_level == 3,
                Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            )
            .count(),
            "manager_escalations_count": db.query(Ticket)
            .filter(
                (Ticket.escalation_level >= 4)
                | (Ticket.status == TicketStatus.MANAGEMENT_ESCALATED)
                | (Ticket.sla_breached.is_(True)),
                Ticket.status.notin_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            )
            .count(),
            "sla_breached_count": db.query(Ticket).filter(Ticket.sla_breached.is_(True)).count(),
            "multi_bounce_count": db.query(Ticket).filter(Ticket.reassignment_count >= 2).count(),
            "net_hours_saved_monthly": round(net_hours, 1),
            "net_cost_saved_usd": round(net_cost, 2),
            "department_distribution": dict(dept_counts),
        }

    @staticmethod
    def list_audit_events(db: Session, limit: int = 50) -> list[TicketEvent]:
        """Retrieves recent audit events for tamper-evident security logging."""
        return (
            db.query(TicketEvent)
            .order_by(TicketEvent.timestamp.desc())
            .limit(limit)
            .all()
        )

