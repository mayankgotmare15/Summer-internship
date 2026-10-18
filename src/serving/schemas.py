"""
Pydantic data schemas for FastAPI serving layer with input validation and sanitization.
"""

from typing import Any

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Raw IT support ticket text (max 5,000 characters for DoS protection)",
    )
    ticket_id: str | None = Field(
        default=None, description="Optional unique identifier for tracing ticket lifecycle"
    )


class PredictResponse(BaseModel):
    ticket_id: str | None = None
    category: str
    category_confidence: float = Field(..., ge=0.0, le=1.0)
    priority: str
    priority_confidence: float = Field(..., ge=0.0, le=1.0)
    decision: str = Field(..., description="'auto_route' or 'human_review'")
    routed_team: str
    model_version: str


class BatchPredictRequest(BaseModel):
    tickets: list[PredictRequest] = Field(
        ..., max_length=100, description="Batch of up to 100 tickets"
    )


class BatchPredictResponse(BaseModel):
    predictions: list[PredictResponse]
    total_processed: int


class FeedbackRequest(BaseModel):
    ticket_id: str
    predicted_category: str
    corrected_category: str
    agent_id: str | None = "agent_default"
    notes: str | None = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str


class ModelInfoResponse(BaseModel):
    model_version: str
    threshold: float
    categories: list[str]
    metadata: dict[str, Any]
