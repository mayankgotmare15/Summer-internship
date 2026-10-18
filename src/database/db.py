"""
Database engine configuration, session management, and seed bootstrapping.
"""

import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base, User, UserRole

logger = logging.getLogger(__name__)

DB_PATH = Path("data/ticket_system.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes schema and seeds baseline users."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Ensure any new escalation columns are present if db already existed
    with engine.connect() as conn:
        for col, col_type in [
            ("escalation_level", "INTEGER DEFAULT 1"),
            ("escalation_reason", "TEXT"),
            ("escalated_by", "VARCHAR(64)"),
            ("sla_deadline", "DATETIME"),
            ("sla_breached", "BOOLEAN DEFAULT 0"),
            ("reassignment_count", "INTEGER DEFAULT 0"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE tickets ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception as exc:
                logger.debug("Column '%s' already exists or skipped: %s", col, exc)

        for col, col_type in [
            ("email", "VARCHAR(128)"),
            ("password_hash", "VARCHAR(256)"),
            ("password_salt", "VARCHAR(64)"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("last_login", "DATETIME"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception as exc:
                logger.debug("User column '%s' already exists or skipped: %s", col, exc)
    seed_users()


def get_db():
    """FastAPI dependency for database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_users():
    """Pre-populates baseline enterprise personas with secure credentials."""
    from src.auth.security import hash_password

    default_personas = [
        {
            "id": "usr_triager_alex",
            "name": "Alex Mercer (Service Desk Triager)",
            "role": UserRole.TRIAGER,
            "department": "Service Desk Triage",
            "email": "alex@enterprise.local",
            "password": "ServiceDesk2026!",
        },
        {
            "id": "usr_lead_hardware",
            "name": "Sarah Connor (Desktop & Hardware Lead)",
            "role": UserRole.RESOLVER_LEAD,
            "department": "Desktop Support & Hardware Services",
            "email": "sarah@enterprise.local",
            "password": "HardwareLead2026!",
        },
        {
            "id": "usr_lead_access",
            "name": "Marcus Vance (IAM Security Lead)",
            "role": UserRole.RESOLVER_LEAD,
            "department": "Identity & Access Management (IAM)",
            "email": "marcus@enterprise.local",
            "password": "AccessLead2026!",
        },
        {
            "id": "usr_lead_storage",
            "name": "Elena Fisher (Cloud Storage Lead)",
            "role": UserRole.RESOLVER_LEAD,
            "department": "Cloud & Storage Infrastructure",
            "email": "storage@enterprise.local",
            "password": "StorageLead2026!",
        },
        {
            "id": "usr_l3_specialist",
            "name": "Devon Vance (L3 Senior DevOps & Incident Lead)",
            "role": UserRole.SPECIALIST_L3,
            "department": "Project Engineering & DevOps",
            "email": "devon@enterprise.local",
            "password": "DevOpsHero2026!",
        },
        {
            "id": "usr_manager_dave",
            "name": "David Sterling (IT Operations Delivery Manager)",
            "role": UserRole.MANAGER,
            "department": "IT Service Delivery",
            "email": "david@enterprise.local",
            "password": "Commander2026!",
        },
        {
            "id": "usr_admin_elena",
            "name": "Elena Fisher (MLOps Platform Lead)",
            "role": UserRole.MLOPS_ADMIN,
            "department": "MLOps Platform",
            "email": "elena@enterprise.local",
            "password": "MLOpsMaster2026!",
        },
    ]

    db: Session = SessionLocal()
    try:
        for p in default_personas:
            user = db.query(User).filter(User.id == p["id"]).first()
            pw_hash, pw_salt = hash_password(p["password"])
            if user:
                # Backfill credentials if not set
                if not user.email:
                    user.email = p["email"]
                if not user.password_hash:
                    user.password_hash = pw_hash
                    user.password_salt = pw_salt
                if user.is_active is None:
                    user.is_active = True
            else:
                new_user = User(
                    id=p["id"],
                    name=p["name"],
                    role=p["role"],
                    department=p["department"],
                    email=p["email"],
                    password_hash=pw_hash,
                    password_salt=pw_salt,
                    is_active=True,
                )
                db.add(new_user)
        db.commit()
    finally:
        db.close()
