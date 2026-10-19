"""
FastAPI Serving Application for IT Support Ticket Routing & Priority Classifier.
Includes input validation, confidence decision engine, audit logging, and feedback loops.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from src.database.db import SessionLocal, init_db
from src.features.preprocess import clean_text
from src.repositories.ticket_repository import TicketRepository
from src.serving.decision import DecisionEngine
from src.serving.routers import admin, analytics, auth, escalations, queues, triage
from src.serving.schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    FeedbackRequest,
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
)
from contextlib import asynccontextmanager

# Global runtime state
MODEL_ROUTING_PATH = Path("models/routing_model.joblib")
MODEL_PRIORITY_PATH = Path("models/priority_model.joblib")
PREDICTION_LOG_PATH = Path("data/monitoring/prediction_log.jsonl")
FEEDBACK_LOG_PATH = Path("data/monitoring/feedback_log.jsonl")

routing_pipeline: Any | None = None
priority_pipeline: Any | None = None
decision_engine: DecisionEngine = DecisionEngine()
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0-champion")


def load_models():
    """Loads trained artifacts if available."""
    global routing_pipeline, priority_pipeline
    if MODEL_ROUTING_PATH.exists():
        try:
            routing_pipeline = joblib.load(MODEL_ROUTING_PATH)
        except Exception as e:
            print(f"Warning: Failed to load routing model from {MODEL_ROUTING_PATH}: {e}")

    if MODEL_PRIORITY_PATH.exists():
        try:
            priority_pipeline = joblib.load(MODEL_PRIORITY_PATH)
        except Exception as e:
            print(f"Warning: Failed to load priority model from {MODEL_PRIORITY_PATH}: {e}")


# Initialize paths and eager load models on module import
PREDICTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
load_models()


@asynccontextmanager
async def lifespan(app: FastAPI):
    PREDICTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    load_models()
    yield


app = FastAPI(
    title="IT Ticket Auto-Routing & Priority Classifier",
    description="MLOps system for automated ticket queue routing and decision-support priority prediction.",
    version="1.0.0",
    lifespan=lifespan,
)

# Include authentication & persona routers
app.include_router(auth.router)
app.include_router(triage.router)
app.include_router(queues.router)
app.include_router(escalations.router)
app.include_router(analytics.router)
app.include_router(admin.router)

# Mount reports directory for drift HTML reports
from fastapi.staticfiles import StaticFiles
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory="reports", html=True), name="reports")


def log_prediction(
    ticket_id: str | None,
    raw_text: str,
    category: str,
    cat_conf: float,
    priority: str,
    prio_conf: float,
    decision: str,
    routed_team: str,
):
    """
    Structured audit logging. Ticket text is anonymized via SHA-256 hash
    to adhere to SDL privacy principles.
    """
    text_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id or f"tkt-{text_hash[:8]}",
        "text_hash": text_hash,
        "text_length": len(raw_text),
        "predicted_category": category,
        "category_confidence": round(cat_conf, 4),
        "predicted_priority": priority,
        "priority_confidence": round(prio_conf, 4),
        "decision": decision,
        "routed_team": routed_team,
        "model_version": MODEL_VERSION,
    }
    with open(PREDICTION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def predict_single(req: PredictRequest) -> PredictResponse:
    cleaned = clean_text(req.text)
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket text contains no valid tokens after preprocessing.",
        )

    # 1. Routing Prediction
    if routing_pipeline is not None:
        try:
            probs = routing_pipeline.predict_proba([cleaned])[0]
            classes = routing_pipeline.classes_
            max_idx = probs.argmax()
            category = str(classes[max_idx])
            cat_conf = float(probs[max_idx])
        except Exception:
            category = "Miscellaneous"
            cat_conf = 0.50
    else:
        # Fallback heuristic / mock prediction for cold-start before first training run
        category = "Miscellaneous"
        cat_conf = 0.70

    # 2. Priority Prediction
    if priority_pipeline is not None:
        try:
            p_probs = priority_pipeline.predict_proba([cleaned])[0]
            p_classes = priority_pipeline.classes_
            p_max_idx = p_probs.argmax()
            priority = str(p_classes[p_max_idx])
            prio_conf = float(p_probs[p_max_idx])
        except Exception:
            priority = "Medium"
            prio_conf = 0.60
    else:
        priority = "Medium"
        prio_conf = 0.65

    # 3. Priority Keyword Override
    final_priority, overridden = decision_engine.apply_priority_overrides(
        req.text, priority, prio_conf
    )
    if overridden:
        prio_conf = 0.95

    # 4. Routing Decision Engine
    decision, routed_team = decision_engine.evaluate_routing(category, cat_conf)

    # 5. Audit Log (JSONL)
    log_prediction(
        req.ticket_id,
        req.text,
        category,
        cat_conf,
        final_priority,
        prio_conf,
        decision,
        routed_team,
    )

    # 6. Persist to Relational Database
    db = SessionLocal()
    try:
        saved_ticket = TicketRepository.create_ticket(
            db=db,
            text=req.text,
            predicted_category=category,
            category_confidence=cat_conf,
            predicted_priority=final_priority,
            priority_confidence=prio_conf,
            priority_overridden=overridden,
            decision=decision,
            assigned_team=routed_team,
            model_version=MODEL_VERSION,
            ticket_id=req.ticket_id,
        )
        final_ticket_id = saved_ticket.id
    except Exception as e:
        logger.error(f"Failed to persist ticket to database: {e}", exc_info=True)
        db.rollback()
        final_ticket_id = req.ticket_id or "TKT-TEMP"
    finally:
        db.close()

    return PredictResponse(
        ticket_id=final_ticket_id,
        category=category,
        category_confidence=round(cat_conf, 4),
        priority=final_priority,
        priority_confidence=round(prio_conf, 4),
        decision=decision,
        routed_team=routed_team,
        model_version=MODEL_VERSION,
    )


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    ui_path = Path("ui/index.html")
    if ui_path.exists():
        return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>IT Support Ticket Classifier</h1><p>Visit /docs for API documentation.</p>"
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        model_loaded=(routing_pipeline is not None),
        version=MODEL_VERSION,
    )


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info():
    cats = list(decision_engine.routing_map.keys())
    return ModelInfoResponse(
        model_version=MODEL_VERSION,
        threshold=decision_engine.threshold,
        categories=cats,
        metadata={
            "routing_model_loaded": routing_pipeline is not None,
            "priority_model_loaded": priority_pipeline is not None,
            "fallback_queue": decision_engine.fallback_queue,
        },
    )


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    return predict_single(request)


@app.post("/predict/batch", response_model=BatchPredictResponse)
def predict_batch(request: BatchPredictRequest):
    results = [predict_single(ticket) for ticket in request.tickets]
    return BatchPredictResponse(
        predictions=results,
        total_processed=len(results),
    )


@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    """Records human agent corrections to feed into continuous retraining."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": feedback.ticket_id,
        "predicted_category": feedback.predicted_category,
        "corrected_category": feedback.corrected_category,
        "agent_id": feedback.agent_id,
        "notes": feedback.notes,
    }
    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {"status": "success", "message": "Feedback recorded successfully."}
