"""SLA management: target calculations, clock pause/resume, and automatic escalation ladder."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog
import yaml
from sqlalchemy.orm import Session
from src.core.business_calendar import BusinessCalendar
from src.core.clock import Clock, ensure_utc
from src.db.models.assignment import Assignment
from src.db.models.notification import Notification
from src.db.models.sla import EtaChange, SlaClock, SlaEvent
from src.db.models.ticket import Ticket
from src.db.models.user import User

logger = structlog.get_logger()


class SlaService:
    """Calculates SLA deadlines, evaluates escalation ladder, and manages clock state."""

    def __init__(
        self,
        sla_path: Path = Path("configs/sla.yaml"),
        rules_path: Path = Path("configs/escalation_rules.yaml"),
    ) -> None:
        self.sla_cfg = self._load_yaml(sla_path)
        self.rules_cfg = self._load_yaml(rules_path)
        self.calendar = BusinessCalendar.from_yaml()

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def calculate_deadlines(
        self,
        priority: str,
        start_time: datetime,
    ) -> tuple[datetime, datetime, str]:
        """Returns (first_response_due, resolution_due, calendar_type)."""
        prio_info = self.sla_cfg.get("priorities", {}).get(priority, {
            "first_response_minutes": 240,
            "resolution_minutes": 1440,
            "calendar": "business",
        })

        cal_type = prio_info.get("calendar", "business")
        fr_mins = prio_info.get("first_response_minutes", 240)
        res_mins = prio_info.get("resolution_minutes", 1440)

        if cal_type == "24x7":
            fr_due = start_time + timedelta(minutes=fr_mins)
            res_due = start_time + timedelta(minutes=res_mins)
        else:
            fr_due = self.calendar.add_business_seconds(start_time, fr_mins * 60)
            res_due = self.calendar.add_business_seconds(start_time, res_mins * 60)

        return fr_due, res_due, cal_type

    def start_clock(self, ticket: Ticket, db: Session, clock: Clock) -> SlaClock:
        now_dt = clock.now()
        fr_due, res_due, cal_type = self.calculate_deadlines(ticket.priority, now_dt)

        clock_record = SlaClock(
            ticket_id=ticket.id,
            policy_version="v1.1",
            priority=ticket.priority,
            calendar=cal_type,
            started_at=now_dt,
            first_response_due=fr_due,
            resolution_due=res_due,
            state="running",
            cycle=1,
            next_check_at=fr_due,
        )
        db.merge(clock_record)
        db.commit()
        return clock_record

    def pause_clock(self, ticket: Ticket, db: Session, clock: Clock) -> Optional[SlaClock]:
        clock_rec = db.query(SlaClock).filter(SlaClock.ticket_id == ticket.id).first()
        if not clock_rec or clock_rec.state != "running":
            return clock_rec

        clock_rec.state = "paused"
        clock_rec.paused_at = clock.now()
        db.commit()
        return clock_rec

    def resume_clock(self, ticket: Ticket, db: Session, clock: Clock) -> Optional[SlaClock]:
        clock_rec = db.query(SlaClock).filter(SlaClock.ticket_id == ticket.id).first()
        if not clock_rec or clock_rec.state != "paused" or not clock_rec.paused_at:
            return clock_rec

        now_dt = ensure_utc(clock.now())
        paused_at = ensure_utc(clock_rec.paused_at)
        paused_duration = int((now_dt - paused_at).total_seconds())

        res_due = ensure_utc(clock_rec.resolution_due)
        # Extend due date by paused duration
        if clock_rec.calendar == "24x7":
            new_res_due = res_due + timedelta(seconds=paused_duration)
        else:
            new_res_due = self.calendar.add_business_seconds(res_due, paused_duration)

        old_res_due = clock_rec.resolution_due
        clock_rec.resolution_due = new_res_due
        clock_rec.paused_seconds += paused_duration
        clock_rec.paused_at = None
        clock_rec.state = "running"

        # Record ETA change
        eta_change = EtaChange(
            ticket_id=ticket.id,
            old_resolution_due=old_res_due,
            new_resolution_due=new_res_due,
            reason="Clock resumed from requester wait",
        )
        db.add(eta_change)
        db.commit()
        return clock_rec

    def record_first_response(self, ticket: Ticket, db: Session, clock: Clock) -> None:
        clock_rec = db.query(SlaClock).filter(SlaClock.ticket_id == ticket.id).first()
        if clock_rec:
            clock_rec.first_response_met = True
            ticket.first_responded_at = clock.now()
            db.commit()

    def evaluate_ladder(self, db: Session, clock: Clock) -> List[Dict[str, Any]]:
        """Idempotent ladder evaluator. Scans active clocks and fires scheduled ladder steps."""
        now_dt = ensure_utc(clock.now())
        active_clocks = db.query(SlaClock).filter(SlaClock.state == "running").all()
        actions_taken = []

        for c in active_clocks:
            ticket = db.query(Ticket).filter(Ticket.id == c.ticket_id).first()
            if not ticket or ticket.status in ["Resolved", "Closed"]:
                c.state = "stopped"
                db.commit()
                continue

            fr_due = ensure_utc(c.first_response_due)
            res_due = ensure_utc(c.resolution_due)
            started_at = ensure_utc(c.started_at)
            breached_at = ensure_utc(c.breached_at)

            # 1. First Response Miss Check
            if not c.first_response_met and fr_due and now_dt > fr_due:
                existing_event = (
                    db.query(SlaEvent)
                    .filter(
                        SlaEvent.ticket_id == c.ticket_id,
                        SlaEvent.rule_key == "first_response_miss",
                        SlaEvent.cycle == c.cycle,
                    )
                    .first()
                )
                if not existing_event:
                    evt = SlaEvent(
                        ticket_id=c.ticket_id,
                        rule_key="first_response_miss",
                        cycle=c.cycle,
                        detail={"due": fr_due.isoformat(), "fired_at": now_dt.isoformat()},
                    )
                    db.add(evt)
                    # Reassign ticket or notify team lead
                    ticket.is_escalated = True
                    ticket.escalation_level = "E2"
                    actions_taken.append({
                        "ticket_id": str(ticket.id),
                        "public_id": ticket.public_id,
                        "action": "first_response_miss",
                    })

            # Calculate resolution progress ratio
            if c.calendar == "24x7":
                total_duration = (res_due - started_at).total_seconds()
                elapsed = (now_dt - started_at).total_seconds() - c.paused_seconds
            else:
                total_duration = self.calendar.business_seconds(started_at, res_due)
                elapsed = self.calendar.business_seconds(started_at, now_dt) - c.paused_seconds

            ratio = elapsed / total_duration if total_duration > 0 else 1.0

            # 2. 50% Reminder
            if ratio >= 0.50:
                self._fire_step_once(
                    c, "pct50_reminder", {"ratio": round(ratio, 2)}, db, actions_taken, ticket
                )

            # 3. 75% Warning
            if ratio >= 0.75:
                self._fire_step_once(
                    c, "pct75_warning", {"ratio": round(ratio, 2)}, db, actions_taken, ticket
                )

            # 4. 100% Breach
            if res_due and now_dt >= res_due:
                if not c.breached_at:
                    c.breached_at = now_dt
                    breached_at = now_dt
                self._fire_step_once(
                    c,
                    "resolution_breached",
                    {"breached_at": now_dt.isoformat()},
                    db,
                    actions_taken,
                    ticket,
                    escalate_level="E3",
                )

            # 5. Manager Timeout (2 hours after breach without resolution)
            if breached_at and now_dt >= (breached_at + timedelta(hours=2)):
                self._fire_step_once(
                    c,
                    "manager_timeout",
                    {"breached_at": breached_at.isoformat()},
                    db,
                    actions_taken,
                    ticket,
                    escalate_level="E4",
                )

        db.commit()
        return actions_taken

    def _fire_step_once(
        self,
        c: SlaClock,
        rule_key: str,
        detail: Dict[str, Any],
        db: Session,
        actions_list: List[Dict[str, Any]],
        ticket: Ticket,
        escalate_level: Optional[str] = None,
    ) -> None:
        existing = (
            db.query(SlaEvent)
            .filter(
                SlaEvent.ticket_id == c.ticket_id,
                SlaEvent.rule_key == rule_key,
                SlaEvent.cycle == c.cycle,
            )
            .first()
        )
        if not existing:
            evt = SlaEvent(
                ticket_id=c.ticket_id,
                rule_key=rule_key,
                cycle=c.cycle,
                detail=detail,
            )
            db.add(evt)
            if escalate_level:
                ticket.is_escalated = True
                ticket.escalation_level = escalate_level

            actions_list.append({
                "ticket_id": str(ticket.id),
                "public_id": ticket.public_id,
                "rule_key": rule_key,
                "escalate_level": escalate_level,
            })
