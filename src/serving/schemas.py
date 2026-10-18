"""
Pydantic data schemas for FastAPI serving layer with input validation and sanitization.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="Raw IT support ticket text (max 5,000 characters for DoS protection)"
    )
    ticket_id: Optional[str] = Field(
        default=None,
        description="Optional unique identifier for tracing ticket lifecycle"
    )


class PredictResponse(BaseModel):
    ticket_id: Optional[str] = None
    category: str
    category_confidence: float = Field(..., ge=0.0, le=1.0)
    priority: str
    priority_confidence: float = Field(..., ge=0.0, le=1.0)
    decision: str = Field(..., description="'auto_route' or 'human_review'")
    routed_team: str
    model_version: str


class BatchPredictRequest(BaseModel):
    tickets: List[PredictRequest] = Field(
        ...,
        max_length=100,
        description="Batch of up to 100 tickets"
    )


class BatchPredictResponse(BaseModel):
    predictions: List[PredictResponse]
    total_processed: int


class FeedbackRequest(BaseModel):
    ticket_id: str
    predicted_category: str
    corrected_category: str
    agent_id: Optional[str] = "agent_default"
    notes: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str


class ModelInfoResponse(BaseModel):
    model_version: str
    threshold: float
    categories: List[str]
    metadata: Dict[str, Any]
