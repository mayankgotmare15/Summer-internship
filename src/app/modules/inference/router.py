"""FastAPI router for model inference, batch prediction, model info, and feedback."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.deps import get_clock
from src.app.modules.inference.controller import InferenceController
from src.app.modules.inference.schemas import (
    BatchPredictionIn,
    BatchPredictionOut,
    FeedbackIn,
    FeedbackOut,
    ModelInfoOut,
    PredictionIn,
    PredictionOut,
)
from src.db.session import get_db

router = APIRouter(prefix="", tags=["ML Inference & Serving"])
controller = InferenceController()


@router.post(
    "/predict",
    response_model=PredictionOut,
    status_code=status.HTTP_200_OK,
    summary="Predict ticket category, priority, and routing decision",
)
def predict_ticket(
    payload: PredictionIn,
    db: Session = Depends(get_db),
) -> PredictionOut:
    """Classifies incoming ticket text and evaluates routing policy and priority rules."""
    return controller.predict(payload, db)


@router.post(
    "/predict/batch",
    response_model=BatchPredictionOut,
    status_code=status.HTTP_200_OK,
    summary="Batch ticket classification (up to 100 tickets)",
)
def predict_batch(
    payload: BatchPredictionIn,
    db: Session = Depends(get_db),
) -> BatchPredictionOut:
    """Classifies multiple ticket texts in a single batch request."""
    return controller.predict_batch(payload, db)


@router.get(
    "/model-info",
    response_model=ModelInfoOut,
    status_code=status.HTTP_200_OK,
    summary="Get active champion model metadata and health status",
)
def get_model_info() -> ModelInfoOut:
    """Returns currently loaded model version, evaluation metrics, threshold, and status."""
    return controller.get_model_info()


@router.post(
    "/feedback",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record agent triage correction or requester feedback",
)
def record_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_db),
) -> FeedbackOut:
    """Logs human corrections and feedback to power model monitoring and automated retraining."""
    return controller.record_feedback(payload, db)


@router.post(
    "/admin/model/reload",
    status_code=status.HTTP_200_OK,
    summary="Hot-reload active champion model bundle from disk",
)
def reload_model() -> Dict[str, Any]:
    """Reloads model bundle from storage and swaps active predictor atomically."""
    ok = controller.store.reload()
    return {
        "status": "reloaded" if ok else "failed",
        "ready": controller.store.is_ready,
        "version": controller.store.get_manifest().get("version"),
    }
