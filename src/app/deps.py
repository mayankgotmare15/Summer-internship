"""Dependency injection providers for FastAPI routes."""

import uuid
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from src.app.errors import UnauthorizedError
from src.app.modules.identity.schemas import UserOut
from src.app.settings import Settings, get_settings
from src.core.clock import Clock, SystemClock
from src.core.security import decode_access_token
from src.db.models.user import User
from src.db.session import get_db

_system_clock = SystemClock()


def get_clock() -> Clock:
    """Provides clock instance (can be overridden in tests via app.dependency_overrides)."""
    return _system_clock


SettingsDep = Annotated[Settings, Depends(get_settings)]
ClockDep = Annotated[Clock, Depends(get_clock)]


def extract_token_from_request(
    request: Request,
    authorization: str | None = None,
) -> str | None:
    """Extracts bearer token from Authorization header or session cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    cookie_token = request.cookies.get("routedesk_token")
    if cookie_token:
        return cookie_token
    header_auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if header_auth and header_auth.startswith("Bearer "):
        return header_auth.split(" ")[1]
    return None


def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> UserOut:
    """Authenticates caller via bearer token or cookie; raises UnauthorizedError if missing or invalid."""
    token = extract_token_from_request(request, authorization)
    if not token:
        raise UnauthorizedError("Missing or invalid authorization token", code="AUTH_REQUIRED")
    try:
        claims = decode_access_token(token)
        user_id_str = claims.get("sub")
        if not user_id_str:
            raise UnauthorizedError("Invalid token claims", code="AUTH_INVALID")
        user = db.query(User).filter(User.id == uuid.UUID(user_id_str)).first()
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive", code="AUTH_USER_NOT_FOUND")
        return UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
        )
    except Exception as exc:
        if isinstance(exc, UnauthorizedError):
            raise exc
        raise UnauthorizedError("Invalid or expired session token", code="AUTH_EXPIRED") from exc


def get_current_user_id(
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    """Extracts user ID from bearer token or cookie, falling back to demo requester for unauthenticated calls."""
    token = extract_token_from_request(request, authorization)
    if token:
        try:
            claims = decode_access_token(token)
            sub = claims.get("sub")
            if sub:
                return uuid.UUID(sub)
        except Exception:
            pass

    demo_u = db.query(User).filter(User.role == "requester").first()
    return demo_u.id if demo_u else uuid.uuid4()
