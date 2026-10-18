"""
Authentication and Role-Based Access Control (RBAC) dependencies.
"""

from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from src.auth.security import decode_access_token
from src.database.models import UserRole


class AuthenticatedUser(BaseModel):
    id: str
    role: UserRole
    department: str
    name: str = "Enterprise User"


ROLE_DEFAULT_DEPARTMENTS = {
    UserRole.TRIAGER: "Service Desk Triage",
    UserRole.RESOLVER_LEAD: "Desktop Support & Hardware Services",
    UserRole.SPECIALIST_L3: "Project Engineering & DevOps",
    UserRole.MANAGER: "IT Service Delivery",
    UserRole.MLOPS_ADMIN: "MLOps Platform",
}

ROLE_DEFAULT_NAMES = {
    UserRole.TRIAGER: "Alex Mercer",
    UserRole.RESOLVER_LEAD: "Sarah Connor",
    UserRole.SPECIALIST_L3: "Devon Vance",
    UserRole.MANAGER: "David Sterling",
    UserRole.MLOPS_ADMIN: "Elena Fisher",
}


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default="triager"),
    x_user_id: str | None = Header(default=None),
) -> AuthenticatedUser:
    """
    Extracts authenticated user from Bearer token or legacy headers.
    Defaults to 'triager' role for seamless local testing if no auth header given.
    """
    # 1. Bearer Token Authentication (Preferred)
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token. Please re-login.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            role = UserRole(payload.get("role", "triager"))
        except ValueError:
            role = UserRole.TRIAGER

        return AuthenticatedUser(
            id=payload.get("sub", "usr_unknown"),
            role=role,
            department=payload.get("department", ROLE_DEFAULT_DEPARTMENTS.get(role, "General")),
            name=payload.get("name", ROLE_DEFAULT_NAMES.get(role, "Enterprise User")),
        )

    # 2. Legacy / Local Header Fallback (For automated test suites and backward compatibility)
    role_str = (x_user_role or "triager").lower().strip()
    try:
        user_role = UserRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid X-User-Role header: '{role_str}'. Valid roles: {[r.value for r in UserRole]}",
        ) from None

    user_id = x_user_id or f"usr_{user_role.value}"
    department = ROLE_DEFAULT_DEPARTMENTS.get(user_role, "General")
    name = ROLE_DEFAULT_NAMES.get(user_role, "Enterprise User")

    return AuthenticatedUser(
        id=user_id,
        role=user_role,
        department=department,
        name=name,
    )


def require_role(allowed_roles: list[UserRole]):
    """
    Factory creating FastAPI dependency that enforces RBAC.
    Rejects unauthorized roles with 403 Forbidden.
    """

    def dependency(
        authorization: str | None = Header(default=None),
        x_user_role: str | None = Header(default="triager"),
        x_user_id: str | None = Header(default=None),
    ) -> AuthenticatedUser:
        user = get_current_user(authorization, x_user_role, x_user_id)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{user.role.value}' does not have required permissions. Allowed roles: {[r.value for r in allowed_roles]}",
            )
        return user

    return dependency
