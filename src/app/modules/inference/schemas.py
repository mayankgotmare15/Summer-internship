"""Pydantic request and response schemas for model inference and feedback."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class ScoredCategory(BaseModel):
    category: str
    score: float


class TeamRef(BaseModel):
    code: str
    name: str


class PredictionIn(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Free-form IT support ticket text (subject + description)",
    )
    blocking_team: bool = Field(
        default=False,
        description="Flag indicating if the issue is blocking the entire team",
    )
    ticket_id: uuid.UUID | None = Field(
        default=None,
        description="Optional ticket UUID when inference is invoked for an existing ticket",
    )
    source: str = Field(
        default="predict_api",
        description="Source of prediction: predict_api, ticket_create, batch, or console",
    )


class PredictionOut(BaseModel):
    category: str
    category_confidence: float
    top_categories: list[ScoredCategory]
    priority: str
    priority_confidence: float
    priority_source: Literal["model", "rule", "agent"]
    decision: Literal["auto_route", "human_review"]
    review_reason: Literal["low_confidence", "multi_issue", "miscellaneous", "model_unavailable"] | None = None
    routed_team: TeamRef
    threshold: float
    model_version: str
    priority_model_version: str
    prediction_id: uuid.UUID
    latency_ms: int
    top_keywords: list[str] = Field(default_factory=list)


class BatchPredictionIn(BaseModel):
    items: list[PredictionIn] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Batch of ticket requests (up to 100 items)",
    )


class BatchPredictionOut(BaseModel):
    predictions: list[PredictionOut]
    count: int


class ModelInfoOut(BaseModel):
    model_name: str
    version: str
    priority_version: str
    threshold: float
    metrics: dict[str, Any]
    labels: list[str]
    fingerprint: str
    loaded_at: str | None = None
    degraded: bool
    python_version: str
    sklearn_version: str


class FeedbackIn(BaseModel):
    prediction_id: uuid.UUID | None = None
    ticket_id: uuid.UUID | None = None
    kind: Literal[
        "agent_correction",
        "wrong_team_escalation",
        "requester_not_quite",
        "priority_correction",
    ]
    predicted_category: str | None = None
    corrected_category: str | None = None
    predicted_priority: str | None = None
    corrected_priority: str | None = None
    notes: str | None = None


class FeedbackOut(BaseModel):
    id: uuid.UUID
    status: str = "recorded"
    created_at: str
