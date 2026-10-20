"""Schemas for user authentication and identity."""

import uuid

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
