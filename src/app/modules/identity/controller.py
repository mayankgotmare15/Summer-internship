"""Identity controller for user authentication, demo sessions, and profile retrieval."""

from typing import Optional
from sqlalchemy.orm import Session
from src.app.errors import NotFoundError, UnauthorizedError
from src.app.modules.identity.schemas import DemoLoginIn, LoginIn, UserOut
from src.core.security import create_access_token, verify_password
from src.db.models.user import User


class IdentityController:
    """Handles authentication and session token generation."""

    def login(self, payload: LoginIn, db: Session) -> UserOut:
        user = db.query(User).filter(User.email == payload.email.lower()).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password", code="AUTH_INVALID")

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name,
        })
        return UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
            access_token=token,
        )

    def demo_login(self, payload: DemoLoginIn, db: Session) -> UserOut:
        user = db.query(User).filter(User.role == payload.role, User.is_demo.is_(True)).first()
        if not user:
            raise NotFoundError(f"Demo user for role '{payload.role}' not found")

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name,
        })
        return UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
            access_token=token,
        )

    def get_user_by_id(self, user_id: str, db: Session) -> UserOut:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        return UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
        )
