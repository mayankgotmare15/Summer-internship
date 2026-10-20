"""Database seeding script for teams and demo users from roster.yaml."""

from pathlib import Path
from typing import Any, Dict
import structlog
import yaml
from sqlalchemy.orm import Session
from src.core.security import hash_password
from src.db.models.user import Team, User
from src.db.session import SessionLocal, init_db

logger = structlog.get_logger()

DEFAULT_DEMO_USERS = [
    {
        "email": "requester@example.com",
        "name": "Aarav Patel",
        "role": "requester",
        "department": "Engineering & Product",
    },
    {
        "email": "agent@example.com",
        "name": "Karan Joshi",
        "role": "agent",
        "department": "IT Service Desk (L1)",
    },
    {
        "email": "priya.sharma@example.com",
        "name": "Priya Sharma",
        "role": "engineer",
        "department": "Access and Identity Team",
    },
    {
        "email": "riya.kapoor@example.com",
        "name": "Riya Kapoor",
        "role": "team_lead",
        "department": "Access and Identity Team",
    },
    {
        "email": "rahul.verma@example.com",
        "name": "Rahul Verma",
        "role": "manager",
        "department": "IT Service Delivery",
    },
    {
        "email": "admin@example.com",
        "name": "Siddharth Rao",
        "role": "admin",
        "department": "Platform & MLOps",
    },
]


def seed_teams(db: Session, roster_path: Path = Path("configs/roster.yaml")) -> None:
    if not roster_path.exists():
        logger.warning("Roster file not found, skipping team seeding", path=str(roster_path))
        return

    with open(roster_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    teams_data = data.get("teams", [])
    for t in teams_data:
        code = t.get("code")
        if not code:
            continue
        existing = db.query(Team).filter(Team.code == code).first()
        if not existing:
            team = Team(
                code=code,
                name=t.get("name", code),
                lead_email=t.get("lead_email"),
                manager_email=t.get("manager_email"),
            )
            db.add(team)
    db.commit()


def seed_demo_users(db: Session, roster_path: Path = Path("configs/roster.yaml")) -> None:
    default_pwd = hash_password("demo123")
    # 1. Seed base demo personas
    for u in DEFAULT_DEMO_USERS:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            user = User(
                email=u["email"],
                name=u["name"],
                password_hash=default_pwd,
                role=u["role"],
                department=u["department"],
                is_active=True,
                is_demo=True,
            )
            db.add(user)

    # 2. Seed all members from roster.yaml
    if roster_path.exists():
        with open(roster_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        members_data = data.get("members", [])
        for m in members_data:
            email = m.get("email")
            if not email:
                continue
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                user = User(
                    email=email,
                    name=m.get("name", email.split("@")[0]),
                    password_hash=default_pwd,
                    role=m.get("role", "engineer"),
                    department=f"Team {m.get('team')}",
                    is_active=True,
                    is_demo=True,
                )
                db.add(user)
    db.commit()


def run_seed() -> None:
    """Initializes tables and seeds initial data."""
    init_db()
    with SessionLocal() as db:
        seed_teams(db)
        seed_demo_users(db)
    logger.info("Database initialized and demo seeds loaded successfully")



if __name__ == "__main__":
    run_seed()
