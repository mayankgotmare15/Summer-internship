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

from sqlalchemy import event

DB_PATH = Path("data/ticket_system.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
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


def ensure_user_exists(
    db: Session,
    user_id: str,
    role: str | UserRole = UserRole.SYSTEM,
    name: str | None = None,
    department: str | None = None,
) -> User:
    """Guarantees a User entity exists to enforce foreign key integrity."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user

    if isinstance(role, str):
        try:
            role_enum = UserRole(role.lower())
        except ValueError:
            role_enum = UserRole.SYSTEM
    else:
        role_enum = role

    user = User(
        id=user_id,
        name=name or user_id.replace("_", " ").title(),
        role=role_enum,
        department=department or "Enterprise Operations",
        email=f"{user_id}@enterprise.local",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def seed_users():
    """Pre-populates baseline enterprise personas, system agents, and test aliases."""
    from src.auth.security import hash_password

    default_personas = [
        # Demo Web UI Accounts
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
        # Automated System Principals
        {
            "id": "system_ml_classifier",
            "name": "ML Classifier System Agent",
            "role": UserRole.SYSTEM,
            "department": "MLOps Platform",
            "email": "ml-classifier@enterprise.local",
            "password": "SystemAgent2026!",
        },
        {
            "id": "system_sla_daemon",
            "name": "SLA Monitor Daemon",
            "role": UserRole.SYSTEM,
            "department": "IT Operations",
            "email": "sla-daemon@enterprise.local",
            "password": "SystemAgent2026!",
        },
        # Integration Test & Legacy Aliases
        {
            "id": "agent_alex",
            "name": "Alex Mercer (Triage)",
            "role": UserRole.TRIAGER,
            "department": "Service Desk Triage",
            "email": "alex.triager@enterprise.local",
            "password": "ServiceDesk2026!",
        },
        {
            "id": "lead_sarah",
            "name": "Sarah Connor (Lead)",
            "role": UserRole.RESOLVER_LEAD,
            "department": "Desktop Support & Hardware Services",
            "email": "sarah.lead@enterprise.local",
            "password": "HardwareLead2026!",
        },
        {
            "id": "devon_vance",
            "name": "Devon Vance (L3)",
            "role": UserRole.SPECIALIST_L3,
            "department": "Project Engineering & DevOps",
            "email": "devon.l3@enterprise.local",
            "password": "DevOpsHero2026!",
        },
        {
            "id": "manager_dave",
            "name": "David Sterling (Manager)",
            "role": UserRole.MANAGER,
            "department": "IT Service Delivery",
            "email": "manager.dave@enterprise.local",
            "password": "Commander2026!",
        },
        {
            "id": "mgr_dave",
            "name": "David Sterling (Mgr Alias)",
            "role": UserRole.MANAGER,
            "department": "IT Service Delivery",
            "email": "mgr.dave@enterprise.local",
            "password": "Commander2026!",
        },
        {
            "id": "admin_elena",
            "name": "Elena Fisher (Admin)",
            "role": UserRole.MLOPS_ADMIN,
            "department": "MLOps Platform",
            "email": "admin.elena@enterprise.local",
            "password": "MLOpsMaster2026!",
        },
        {
            "id": "engineer_mike",
            "name": "Mike Zhang (Resolver)",
            "role": UserRole.RESOLVER_LEAD,
            "department": "Desktop Support & Hardware Services",
            "email": "engineer.mike@enterprise.local",
            "password": "HardwareLead2026!",
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
                if hasattr(p["role"], "value"):
                    user.role = p["role"]
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
