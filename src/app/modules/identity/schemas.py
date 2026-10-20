"""Schemas for user authentication, mobile tokens, sessions, and device registration."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    email: str = Field(..., description="User email address")
    password: str


class DemoLoginIn(BaseModel):
    role: str = "requester"  # requester | agent | engineer | team_lead | manager | admin


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    department: str | None = None
    is_demo: bool = False
    access_token: str | None = None


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: str
    name: str


class TokenIn(BaseModel):
    email: str = Field(..., description="User email address")
    password: str
    device_name: str | None = Field(None, description="Client device description")


class DemoTokenIn(BaseModel):
    role: str = "requester"
    device_name: str | None = Field(None, description="Client device description")


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds
    refresh_token: str
    me: UserOut


class RefreshTokenIn(BaseModel):
    refresh_token: str


class TokenRefreshOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str | None = None


class SessionOut(BaseModel):
    id: uuid.UUID
    device_name: str | None = None
    created_at: datetime
    last_used_at: datetime | None = None
    is_current: bool = False


class DeviceIn(BaseModel):
    fcm_token: str = Field(..., description="Firebase Cloud Messaging registration token")
    platform: str = Field("android", description="Device platform (android, ios)")
    app_version: str | None = None
    os_version: str | None = None
    locale: str | None = None


class DeviceOut(BaseModel):
    id: uuid.UUID
    fcm_token: str
    platform: str
    last_seen_at: datetime


class PasswordResetRequestIn(BaseModel):
    email: str = Field(..., description="User email for password reset")


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(..., description="Opaque password reset token")
    new_password: str = Field(..., min_length=6, description="New user password")


class AccountDeleteIn(BaseModel):
    password: str | None = Field(None, description="Password confirmation for account deletion")
