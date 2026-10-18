"""
Authentication and User Lifecycle Router.
Provides Signup, Login, Profile retrieval, and 1-Click Demo Persona Access.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.auth.dependencies import AuthenticatedUser, get_current_user
from src.auth.security import create_access_token, hash_password, verify_password
from src.database.db import get_db
from src.database.models import User, UserRole

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & User Management"])


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128, description="User's full name")
    email: str = Field(..., description="Corporate email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    role: UserRole = Field(..., description="Assigned organizational role")
    department: str = Field(..., min_length=2, max_length=128, description="Department name")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered corporate email")
    password: str = Field(..., description="User password")


class QuickLoginRequest(BaseModel):
    role: UserRole = Field(..., description="Role to quickly authenticate as")


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str | None = None
    role: str
    department: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


class DemoUserResponse(BaseModel):
    id: str
    name: str
    role: str
    department: str
    email: str
    demo_password: str
    badge: str


DEMO_PERSONAS = [
    {
        "id": "usr_triager_alex",
        "name": "Alex Mercer",
        "role": "triager",
        "department": "Service Desk Triage",
        "email": "alex@enterprise.local",
        "demo_password": "ServiceDesk2026!",
        "badge": "Tier 1: Service Desk Triager",
    },
    {
        "id": "usr_lead_hardware",
        "name": "Sarah Connor",
        "role": "resolver_lead",
        "department": "Desktop Support & Hardware Services",
        "email": "sarah@enterprise.local",
        "demo_password": "HardwareLead2026!",
        "badge": "Tier 2: Resolver Team Lead",
    },
    {
        "id": "usr_l3_specialist",
        "name": "Devon Vance",
        "role": "specialist_l3",
        "department": "Project Engineering & DevOps",
        "email": "devon@enterprise.local",
        "demo_password": "DevOpsHero2026!",
        "badge": "Tier 3: Senior DevOps & Incident Lead",
    },
    {
        "id": "usr_manager_dave",
        "name": "David Sterling",
        "role": "manager",
        "department": "IT Service Delivery",
        "email": "david@enterprise.local",
        "demo_password": "Commander2026!",
        "badge": "Tier 4: Operations Manager & Commander",
    },
    {
        "id": "usr_admin_elena",
        "name": "Elena Fisher",
        "role": "mlops_admin",
        "department": "MLOps Platform",
        "email": "elena@enterprise.local",
        "demo_password": "MLOpsMaster2026!",
        "badge": "MLOps Platform Engineer",
    },
]


@router.get("/demo-users", response_model=list[DemoUserResponse])
def get_demo_users():
    """Returns available pre-seeded demo accounts for one-click testing."""
    return DEMO_PERSONAS


@router.post("/signup", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    """Registers a new corporate user with role-based dashboard assignment."""
    email_clean = req.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An account with email '{email_clean}' is already registered.",
        )

    pw_hash, pw_salt = hash_password(req.password)
    user_id = f"usr_{req.role.value}_{uuid.uuid4().hex[:8]}"

    new_user = User(
        id=user_id,
        name=req.name.strip(),
        role=req.role,
        department=req.department.strip(),
        email=email_clean,
        password_hash=pw_hash,
        password_salt=pw_salt,
        is_active=True,
        last_login=datetime.now(timezone.utc),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        user_id=new_user.id,
        role=new_user.role.value,
        department=new_user.department,
        name=new_user.name,
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=new_user.id,
            name=new_user.name,
            email=new_user.email,
            role=new_user.role.value,
            department=new_user.department,
        ),
    )


@router.post("/login", response_model=AuthTokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials and returns a Bearer access token."""
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not user.password_hash or not user.password_salt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(req.password, user.password_hash, user.password_salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        department=user.department,
        name=user.name,
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            department=user.department,
        ),
    )


@router.post("/quick-login", response_model=AuthTokenResponse)
def quick_demo_login(req: QuickLoginRequest, db: Session = Depends(get_db)):
    """1-Click login to switch between pre-seeded demo roles instantly."""
    user = db.query(User).filter(User.role == req.role).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No pre-seeded user found for role '{req.role.value}'",
        )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        department=user.department,
        name=user.name,
    )

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            department=user.department,
        ),
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the authenticated profile of the active session."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if user:
        return UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value,
            department=user.department,
        )
    return UserProfileResponse(
        id=current_user.id,
        name=current_user.name,
        email=None,
        role=current_user.role.value,
        department=current_user.department,
    )
