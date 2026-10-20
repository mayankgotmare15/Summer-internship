"""Directory and roster service: team lookups, member availability, skills, and delegation."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()


class DirectoryService:
    """Manages resolver teams and staff roster loaded from configs/roster.yaml."""

    def __init__(self, roster_path: Path = Path("configs/roster.yaml")) -> None:
        self.roster_path = roster_path
        self.teams: dict[str, dict[str, Any]] = {}
        self.members: dict[str, dict[str, Any]] = {}  # keyed by email (lower)
        self.team_members: dict[str, list[dict[str, Any]]] = {}  # keyed by team code
        self.load()

    def load(self) -> None:
        if not self.roster_path.exists():
            logger.warning("Roster file not found", path=str(self.roster_path))
            return

        with open(self.roster_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for t in data.get("teams", []):
            code = t.get("code")
            if code:
                self.teams[code] = t
                self.team_members[code] = []

        for m in data.get("members", []):
            email = m.get("email", "").lower()
            if email:
                self.members[email] = m
                team_code = m.get("team")
                if team_code in self.team_members:
                    self.team_members[team_code].append(m)

    def get_team(self, team_code: str) -> dict[str, Any] | None:
        return self.teams.get(team_code)

    def get_team_lead(self, team_code: str) -> dict[str, Any] | None:
        t = self.get_team(team_code)
        if not t:
            return None
        lead_email = t.get("lead_email", "").lower()
        return self.members.get(lead_email)

    def get_member(self, email: str) -> dict[str, Any] | None:
        return self.members.get(email.lower())

    def is_on_leave(
        self, member: dict[str, Any], at_dt: datetime
    ) -> tuple[bool, str | None, str | None]:
        """Checks if member is on leave at given datetime. Returns (on_leave, note, delegate_email)."""
        check_date = at_dt.strftime("%Y-%m-%d")
        for leave_period in member.get("leave", []):
            start = leave_period.get("start_date")
            end = leave_period.get("end_date")
            if start and end and start <= check_date <= end:
                return True, leave_period.get("note", "On Leave"), member.get("delegate_email")
        return False, None, None

    def search_members(
        self,
        query: str = "",
        for_team: str | None = None,
        at_dt: datetime | None = None,
    ) -> list[dict[str, Any]]:
        now_dt = at_dt or datetime.now(timezone.utc)
        q = query.lower().strip()

        results = []
        for email, m in self.members.items():
            name = m.get("name", "")
            team = m.get("team", "")
            role = m.get("role", "")
            skills = " ".join(m.get("skills", []))

            if q and not (
                q in name.lower() or q in email or q in team.lower() or q in skills.lower()
            ):
                continue

            on_leave, note, delegate = self.is_on_leave(m, now_dt)

            # Team match priority score
            priority_rank = 3
            if for_team and team == for_team:
                if role == "team_lead":
                    priority_rank = 1
                else:
                    priority_rank = 2
            elif role == "sd_manager" or role == "delivery_manager":
                priority_rank = 1

            results.append(
                {
                    "email": email,
                    "name": name,
                    "team": team,
                    "role": role,
                    "skills": m.get("skills", []),
                    "escalation_eligible": m.get("escalation_eligible", True),
                    "on_leave": on_leave,
                    "leave_note": note,
                    "delegate_email": delegate,
                    "daily_capacity": m.get("daily_capacity", 6),
                    "_rank": priority_rank,
                }
            )

        # Sort: priority_rank asc, then name asc
        results.sort(key=lambda x: (x["_rank"], x["name"]))
        return results
