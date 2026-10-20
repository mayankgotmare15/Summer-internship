"""FastAPI router for user authentication, mobile tokens, sessions, password reset, and devices."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from src.app.deps import get_clock, get_current_user, get_current_user_id
from src.app.modules.identity.controller import IdentityController
from src.app.modules.identity.schemas import (
    AccountDeleteIn,
    DemoLoginIn,
    DemoTokenIn,
    DeviceIn,
    DeviceOut,
    LoginIn,
    LogoutIn,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
    RefreshTokenIn,
    SessionOut,
    TokenIn,
    TokenOut,
    TokenRefreshOut,
    UserOut,
)
from src.core.clock import Clock
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Identity & Authentication"])
devices_router = APIRouter(prefix="/devices", tags=["Device Registry"])
controller = IdentityController()


# --- Cookie / Web Authentication ---

@router.post("/login", response_model=UserOut, summary="Web session login via httpOnly cookie")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> UserOut:
    user_out = controller.login(payload, db)
    if user_out.access_token:
        response.set_cookie(
            key="routedesk_token",
            value=user_out.access_token,
            httponly=True,
            samesite="lax",
        )
    return user_out


@router.post("/demo-login", response_model=UserOut, summary="Web demo login via httpOnly cookie")
def demo_login(payload: DemoLoginIn, response: Response, db: Session = Depends(get_db)) -> UserOut:
    user_out = controller.demo_login(payload, db)
    if user_out.access_token:
        response.set_cookie(
            key="routedesk_token",
            value=user_out.access_token,
            httponly=True,
            samesite="lax",
        )
    return user_out


@router.post("/logout", status_code=status.HTTP_200_OK, summary="Revoke session cookie and refresh token")
def logout(
    response: Response,
    payload: LogoutIn | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, str]:
    response.delete_cookie("routedesk_token")
    return controller.logout(payload, user_id, db, clock)


@router.get("/me", response_model=UserOut, summary="Get profile of currently authenticated user")
def get_me(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    return current_user


# --- Mobile Bearer Token Authentication (B1) ---

@router.post("/token", response_model=TokenOut, summary="Issue access and rotating refresh token for mobile")
def issue_token(
    payload: TokenIn,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> TokenOut:
    return controller.issue_tokens(payload, db, clock)


@router.post("/demo-token", response_model=TokenOut, summary="Issue demo access and refresh token for mobile")
def demo_issue_token(
    payload: DemoTokenIn,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> TokenOut:
    return controller.demo_issue_tokens(payload, db, clock)


@router.post("/refresh", response_model=TokenRefreshOut, summary="Rotate refresh token and issue new access token")
def refresh_token(
    payload: RefreshTokenIn,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> TokenRefreshOut:
    return controller.refresh_tokens(payload, db, clock)


@router.get("/sessions", response_model=list[SessionOut], summary="List active signed-in sessions for user")
def list_sessions(
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> list[SessionOut]:
    return controller.list_sessions(current_user.id, db, clock)


@router.delete("/sessions/{session_id}", summary="Revoke a signed-in session device")
def revoke_session(
    session_id: uuid.UUID,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, str]:
    return controller.revoke_session(session_id, current_user.id, db, clock)


@router.delete("/me", summary="Play Store Policy B8: Delete requester account and anonymize personal data")
def delete_account(
    payload: AccountDeleteIn | None = None,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, str]:
    return controller.delete_account(current_user.id, payload, db, clock)


# --- Password Reset (B11) ---

@router.post(
    "/password-reset/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset token link",
)
def request_password_reset(
    payload: PasswordResetRequestIn,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, str]:
    return controller.request_password_reset(payload, db, clock)


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset with opaque token",
)
def confirm_password_reset(
    payload: PasswordResetConfirmIn,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> dict[str, str]:
    return controller.confirm_password_reset(payload, db, clock)


# --- Device Registry (B2) ---

@devices_router.post("", response_model=DeviceOut, status_code=status.HTTP_200_OK, summary="Register or update FCM device")
def register_device(
    payload: DeviceIn,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
) -> DeviceOut:

    return controller.upsert_device(current_user.id, payload, db, clock)


@devices_router.delete("/{device_id}", summary="Unregister FCM device on sign-out")
def delete_device(
    device_id: uuid.UUID,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return controller.delete_device(device_id, current_user.id, db)
