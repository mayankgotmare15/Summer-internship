"""Pydantic schemas for ticket creation, status queries, messages, and escalation."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class MemberRef(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str


class TeamRef(BaseModel):
    code: str
    name: str


class TicketCreateIn(BaseModel):
    subject: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    blocking_team: bool = Field(default=False)
    channel: Literal["portal", "chat", "email_sim"] = "portal"


class TicketCreatedOut(BaseModel):
    id: str  # e.g. "T-1042"
    ticket_uuid: uuid.UUID
    status: str
    category: str
    priority: str
    decision: Literal["auto_route", "human_review"]
    assignee: Optional[MemberRef] = None
    team: TeamRef
    first_response_due: Optional[datetime] = None
    resolution_due: Optional[datetime] = None
    awaiting_approval_from: Optional[MemberRef] = None
    review_promise_by: Optional[datetime] = None
    can_escalate: bool = True


class MessageOut(BaseModel):
    id: uuid.UUID
    author_name: Optional[str]
    kind: str
    body: str
    created_at: datetime


class TicketDetailOut(BaseModel):
    id: str  # public_id
    ticket_uuid: uuid.UUID
    subject: str
    description: str
    category: str
    priority: str
    priority_source: str
    status: str
    decision: str
    review_reason: Optional[str] = None
    team: TeamRef
    assignee: Optional[MemberRef] = None
    is_escalated: bool
    escalation_level: str
    first_response_due: Optional[datetime] = None
    resolution_due: Optional[datetime] = None
    first_responded_at: Optional[datetime] = None
    clock_state: Optional[str] = None
    messages: List[MessageOut] = Field(default_factory=list)
    can_escalate: bool = True
    escalation_eligibility: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class StatusChangeIn(BaseModel):
    to_status: Literal["In progress", "Waiting on requester", "Resolved", "Closed", "Assigned"]
    note: Optional[str] = None
    new_eta: Optional[datetime] = None


class MessageIn(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)
    internal: bool = False


class EscalateIn(BaseModel):
    target_user_id: uuid.UUID
    reason_code: Literal["no_response", "wrong_team", "business_critical", "deadline_at_risk", "other"]
    note: str = Field(..., min_length=10, max_length=500)


class EscalationRespondIn(BaseModel):
    action: Literal["accept", "reassign", "decline"]
    new_eta: Optional[datetime] = None
    reassign_to_id: Optional[uuid.UUID] = None
    reason_note: Optional[str] = None
