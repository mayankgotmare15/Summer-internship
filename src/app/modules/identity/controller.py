"""Identity controller for user authentication, token issuance, session management, and devices."""

import uuid
from datetime import timedelta

from sqlalchemy.orm import Session

from src.app.errors import ForbiddenError, NotFoundError, UnauthorizedError
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
from src.core.clock import Clock, ensure_utc
from src.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from src.db.models.device import Device
from src.db.models.password_reset import PasswordReset
from src.db.models.refresh_token import RefreshToken
from src.db.models.user import User


class IdentityController:
    """Handles authentication, refresh token rotation, devices, and profile management."""

    def login(self, payload: LoginIn, db: Session) -> UserOut:
        """Cookie-based login for web clients."""
        user = db.query(User).filter(User.email == payload.email.lower()).first()
        if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password", code="AUTH_INVALID")

        token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "name": user.name,
            }
        )
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
        """Cookie-based demo login for web clients."""
        user = db.query(User).filter(User.role == payload.role, User.is_demo.is_(True)).first()
        if not user or not user.is_active:
            raise NotFoundError(f"Demo user for role '{payload.role}' not found")

        token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "name": user.name,
            }
        )
        return UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
            access_token=token,
        )

    def get_user_by_id(self, user_id: str | uuid.UUID, db: Session) -> UserOut:
        uid = uuid.UUID(str(user_id)) if isinstance(user_id, str) else user_id
        user = db.query(User).filter(User.id == uid).first()
        if not user or not user.is_active:
            raise NotFoundError("User not found")
        return UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
        )

    def issue_tokens(self, payload: TokenIn, db: Session, clock: Clock) -> TokenOut:
        """Issues short-lived JWT access token and rotating refresh token for mobile clients."""
        user = db.query(User).filter(User.email == payload.email.lower()).first()
        if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password", code="AUTH_INVALID")

        now = clock.now()
        access_token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "name": user.name,
            },
            expires_delta=timedelta(minutes=15),
        )
        raw_refresh_token = generate_opaque_token(32)
        token_hash = hash_token(raw_refresh_token)
        family_id = uuid.uuid4()

        refresh_row = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            family_id=family_id,
            token_hash=token_hash,
            device_name=payload.device_name,
            last_used_at=now,
            expires_at=now + timedelta(days=30),
        )
        db.add(refresh_row)
        db.commit()

        me = UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
        )
        return TokenOut(
            access_token=access_token,
            token_type="bearer",
            expires_in=900,
            refresh_token=raw_refresh_token,
            me=me,
        )

    def demo_issue_tokens(self, payload: DemoTokenIn, db: Session, clock: Clock) -> TokenOut:
        """Issues mobile tokens for demo users when DEMO_MODE is active."""
        user = db.query(User).filter(User.role == payload.role, User.is_demo.is_(True)).first()
        if not user or not user.is_active:
            raise NotFoundError(f"Demo user for role '{payload.role}' not found")

        now = clock.now()
        access_token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "name": user.name,
            },
            expires_delta=timedelta(minutes=15),
        )
        raw_refresh_token = generate_opaque_token(32)
        token_hash = hash_token(raw_refresh_token)
        family_id = uuid.uuid4()

        refresh_row = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            family_id=family_id,
            token_hash=token_hash,
            device_name=payload.device_name,
            last_used_at=now,
            expires_at=now + timedelta(days=30),
        )
        db.add(refresh_row)
        db.commit()

        me = UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_demo=user.is_demo,
        )
        return TokenOut(
            access_token=access_token,
            token_type="bearer",
            expires_in=900,
            refresh_token=raw_refresh_token,
            me=me,
        )

    def refresh_tokens(self, payload: RefreshTokenIn, db: Session, clock: Clock) -> TokenRefreshOut:
        """Rotates refresh token and returns a new access token; revokes family upon theft detection."""
        raw_token = payload.refresh_token.strip()
        t_hash = hash_token(raw_token)
        token_record = db.query(RefreshToken).filter(RefreshToken.token_hash == t_hash).first()

        now = clock.now()
        if not token_record:
            raise UnauthorizedError("Invalid refresh token", code="AUTH_INVALID_TOKEN")

        # Reuse of an already-rotated token -> theft detection revoking family
        if token_record.revoked_at is not None:
            db.query(RefreshToken).filter(RefreshToken.family_id == token_record.family_id).update(
                {"revoked_at": now}
            )
            db.commit()
            raise UnauthorizedError(
                "Refresh token has been revoked due to reuse detection",
                code="AUTH_TOKEN_THEFT_DETECTED",
            )

        if ensure_utc(token_record.expires_at) < ensure_utc(now):
            token_record.revoked_at = now
            db.commit()
            raise UnauthorizedError("Refresh token has expired", code="AUTH_TOKEN_EXPIRED")


        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user or not user.is_active:
            token_record.revoked_at = now
            db.commit()
            raise UnauthorizedError("User account not found or inactive", code="AUTH_USER_INACTIVE")

        # Rotate token
        new_raw_refresh = generate_opaque_token(32)
        new_token_hash = hash_token(new_raw_refresh)
        new_token_id = uuid.uuid4()

        token_record.revoked_at = now
        token_record.last_used_at = now
        token_record.replaced_by = new_token_id

        new_record = RefreshToken(
            id=new_token_id,
            user_id=user.id,
            family_id=token_record.family_id,
            token_hash=new_token_hash,
            device_name=token_record.device_name,
            last_used_at=now,
            expires_at=now + timedelta(days=30),
        )
        db.add(new_record)
        db.commit()

        access_token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "name": user.name,
            },
            expires_delta=timedelta(minutes=15),
        )
        return TokenRefreshOut(
            access_token=access_token,
            token_type="bearer",
            expires_in=900,
            refresh_token=new_raw_refresh,
        )

    def logout(
        self,
        payload: LogoutIn | None,
        user_id: uuid.UUID | None,
        db: Session,
        clock: Clock,
    ) -> dict[str, str]:
        """Revokes provided refresh token or current session."""
        now = clock.now()
        if payload and payload.refresh_token:
            t_hash = hash_token(payload.refresh_token.strip())
            token_record = db.query(RefreshToken).filter(RefreshToken.token_hash == t_hash).first()
            if token_record:
                token_record.revoked_at = now
                db.commit()
        return {"status": "logged_out"}

    def list_sessions(self, user_id: uuid.UUID, db: Session, clock: Clock) -> list[SessionOut]:
        """Lists all active signed-in sessions for user."""
        now = clock.now()
        sessions = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .order_by(RefreshToken.created_at.desc())
            .all()
        )
        return [
            SessionOut(
                id=s.id,
                device_name=s.device_name,
                created_at=ensure_utc(s.created_at),
                last_used_at=ensure_utc(s.last_used_at) if s.last_used_at else None,
            )
            for s in sessions
            if ensure_utc(s.expires_at) > ensure_utc(now)
        ]


    def revoke_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID, db: Session, clock: Clock
    ) -> dict[str, str]:
        """Revokes a specific session device."""
        session = (
            db.query(RefreshToken)
            .filter(RefreshToken.id == session_id, RefreshToken.user_id == user_id)
            .first()
        )
        if not session:
            raise NotFoundError("Session not found")
        session.revoked_at = clock.now()
        db.commit()
        return {"status": "revoked"}

    def delete_account(
        self,
        user_id: uuid.UUID,
        payload: AccountDeleteIn | None,
        db: Session,
        clock: Clock,
    ) -> dict[str, str]:
        """Play Policy B8: Requester account deletion with PII anonymization and session purge."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")

        # Staff accounts are managed by directory roster and cannot self-delete
        if user.role != "requester":
            raise ForbiddenError(
                "Staff accounts are managed by the roster directory and cannot be self-deleted.",
                code="ACCOUNT_MANAGED_BY_ROSTER",
            )

        if payload and payload.password and user.password_hash:
            if not verify_password(payload.password, user.password_hash):
                raise UnauthorizedError("Incorrect password", code="AUTH_INVALID")

        now = clock.now()
        # Anonymize requester details
        user.name = "Deleted User"
        user.email = f"deleted_{user.id}@deleted.local"
        user.password_hash = ""
        user.is_active = False

        # Revoke all refresh tokens
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked_at": now})

        # Disable all devices
        db.query(Device).filter(Device.user_id == user.id).update({"disabled_at": now})

        db.commit()
        return {
            "status": "account_deleted",
            "message": "Account has been deactivated and personal data anonymized.",
        }

    def request_password_reset(
        self, payload: PasswordResetRequestIn, db: Session, clock: Clock
    ) -> dict[str, str]:
        """B11: Password reset request, always returns 202 to avoid account enumeration."""
        user = db.query(User).filter(User.email == payload.email.lower()).first()
        if user and user.is_active:
            raw_token = generate_opaque_token(32)
            t_hash = hash_token(raw_token)
            expires_at = clock.now() + timedelta(minutes=30)

            reset_record = PasswordReset(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=t_hash,
                expires_at=expires_at,
            )
            db.add(reset_record)
            db.commit()
            # Outbox / email link: https://<host>/reset?token={raw_token}

        return {
            "status": "accepted",
            "message": "If the email is registered, a password reset link has been sent.",
        }

    def confirm_password_reset(
        self, payload: PasswordResetConfirmIn, db: Session, clock: Clock
    ) -> dict[str, str]:
        """B11: Confirms password reset with opaque token and updates password."""
        now = clock.now()
        t_hash = hash_token(payload.token.strip())
        reset_record = (
            db.query(PasswordReset)
            .filter(PasswordReset.token_hash == t_hash, PasswordReset.used_at.is_(None))
            .first()
        )
        if not reset_record or ensure_utc(reset_record.expires_at) < ensure_utc(now):
            raise UnauthorizedError(
                "Invalid or expired password reset token", code="AUTH_INVALID_TOKEN"
            )


        user = db.query(User).filter(User.id == reset_record.user_id).first()
        if not user or not user.is_active:
            raise NotFoundError("User not found or inactive")

        reset_record.used_at = now
        user.password_hash = hash_password(payload.new_password)

        # Revoke all refresh tokens on password change
        db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update({"revoked_at": now})

        db.commit()
        return {
            "status": "password_reset_successful",
            "message": "Password updated successfully. Please log in with your new password.",
        }

    def upsert_device(
        self, user_id: uuid.UUID, payload: DeviceIn, db: Session, clock: Clock
    ) -> DeviceOut:
        """B2: Registers or updates FCM push notification device token."""
        now = clock.now()
        device = db.query(Device).filter(Device.fcm_token == payload.fcm_token).first()
        if device:
            device.user_id = user_id
            device.platform = payload.platform
            device.app_version = payload.app_version
            device.os_version = payload.os_version
            device.locale = payload.locale
            device.last_seen_at = now
            device.disabled_at = None
        else:
            device = Device(
                id=uuid.uuid4(),
                user_id=user_id,
                platform=payload.platform,
                fcm_token=payload.fcm_token,
                app_version=payload.app_version,
                os_version=payload.os_version,
                locale=payload.locale,
                last_seen_at=now,
            )
            db.add(device)

        db.commit()
        db.refresh(device)
        return DeviceOut(
            id=device.id,
            fcm_token=device.fcm_token,
            platform=device.platform,
            last_seen_at=device.last_seen_at,
        )

    def delete_device(self, device_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> dict[str, str]:
        """B2: Removes push device registration on sign-out."""
        device = (
            db.query(Device).filter(Device.id == device_id, Device.user_id == user_id).first()
        )
        if not device:
            raise NotFoundError("Device registration not found")
        db.delete(device)
        db.commit()
        return {"status": "deleted"}
