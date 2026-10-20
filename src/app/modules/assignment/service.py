"""Assignment engine implementing PRD Section 4B.2: shifts, leave, skills, workload, and capacity."""

import re
from typing import Any

import structlog
from sqlalchemy.orm import Session

from src.app.modules.directory.service import DirectoryService
from src.core.clock import Clock
from src.db.models.ticket import Ticket
from src.db.models.user import User

logger = structlog.get_logger()

PRIORITY_WEIGHTS = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


class AssignmentService:
    """Selects the named engineer for a ticket using multi-factor constraint optimization."""

    def __init__(self, directory_service: DirectoryService | None = None) -> None:
        self.directory = directory_service or DirectoryService()

    def get_candidate_workload(self, user_id: Any, db: Session) -> tuple[int, int]:
        """Calculates (open_ticket_count, weighted_workload) for an engineer."""
        open_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.assignee_id == user_id,
                Ticket.status.in_(["New", "Assigned", "In progress", "Waiting on requester"]),
            )
            .all()
        )
        count = len(open_tickets)
        weighted = sum(PRIORITY_WEIGHTS.get(t.priority, 2) for t in open_tickets)
        return count, weighted

    def assign_ticket(
        self,
        team_code: str,
        priority: str,
        ticket_text: str,
        db: Session,
        clock: Clock,
    ) -> tuple[User, dict[str, Any]]:
        """Executes Section 4B.2: filters available engineers, matches skills, checks workload, falls back to Lead."""
        now_dt = clock.now()
        text_lower = ticket_text.lower()

        self.directory.get_team(team_code)
        members = self.directory.team_members.get(team_code, [])

        trace: dict[str, Any] = {
            "team_code": team_code,
            "priority": priority,
            "candidates_evaluated": [],
            "fallback_used": False,
        }

        # Step 1: Filter out members on leave
        active_candidates = []
        for m in members:
            on_leave, note, delegate = self.directory.is_on_leave(m, now_dt)
            if on_leave:
                trace["candidates_evaluated"].append(
                    {
                        "email": m["email"],
                        "status": "excluded_on_leave",
                        "note": note,
                        "delegate": delegate,
                    }
                )
                continue

            # Fetch DB user record
            db_user = db.query(User).filter(User.email == m["email"].lower()).first()
            if not db_user:
                continue

            # Step 2: Compute skill overlap
            skills = m.get("skills", [])
            matched_skills = [
                s
                for s in skills
                if re.search(r"\b" + re.escape(s) + r"\b", text_lower)
                or re.search(r"\b" + re.escape(s.replace("_", " ")) + r"\b", text_lower)
            ]

            # Step 3: Compute current open workload
            open_count, weighted_load = self.get_candidate_workload(db_user.id, db)
            capacity = m.get("daily_capacity", 6)

            candidate_info = {
                "user_id": str(db_user.id),
                "name": db_user.name,
                "email": db_user.email,
                "role": m.get("role", "engineer"),
                "matched_skills": matched_skills,
                "skill_score": len(matched_skills),
                "open_count": open_count,
                "weighted_load": weighted_load,
                "capacity": capacity,
                "under_capacity": open_count < capacity,
            }
            trace["candidates_evaluated"].append(candidate_info)
            active_candidates.append((db_user, candidate_info))

        # Filter strictly engineers first (keep Team Lead as fallback)
        engineer_candidates = [
            (u, info) for (u, info) in active_candidates if info["role"] == "engineer"
        ]

        # Prioritize candidates who are under capacity
        eligible = [c for c in engineer_candidates if c[1]["under_capacity"]]
        if not eligible and engineer_candidates:
            # If all are at capacity, take least loaded
            eligible = engineer_candidates

        if eligible:
            # Sort: skill_score desc, weighted_load asc, open_count asc
            eligible.sort(
                key=lambda x: (
                    -x[1]["skill_score"],
                    x[1]["weighted_load"],
                    x[1]["open_count"],
                )
            )
            selected_user, selected_info = eligible[0]
            trace["selected_assignee"] = selected_info
            trace["reason"] = (
                "skill_match_and_capacity"
                if selected_info["skill_score"] > 0
                else "lowest_weighted_workload"
            )
            return selected_user, trace

        # Step 5: Fallback to Team Lead
        trace["fallback_used"] = True
        lead_info = self.directory.get_team_lead(team_code)
        lead_user = None
        if lead_info:
            lead_user = db.query(User).filter(User.email == lead_info["email"].lower()).first()

        if not lead_user:
            # Ultimate fallback to service desk manager
            lead_user = db.query(User).filter(User.email == "rahul.verma@example.com").first()

        trace["selected_assignee"] = {
            "user_id": str(lead_user.id) if lead_user else None,
            "name": lead_user.name if lead_user else "Team Lead",
            "role": "fallback_team_lead",
        }
        trace["reason"] = "fallback_no_available_engineers"
        return lead_user, trace
