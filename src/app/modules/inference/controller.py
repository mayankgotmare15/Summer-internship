"""Inference use cases: ticket prediction, decision evaluation, priority rules, and feedback logging."""

import hashlib
import uuid
from typing import Any, Dict, List, Optional
import structlog
from sqlalchemy.orm import Session
from src.app.errors import DomainError, ModelUnavailableError
from src.app.modules.inference.repository import InferenceRepository
from src.app.modules.inference.schemas import (
    BatchPredictionIn,
    BatchPredictionOut,
    FeedbackIn,
    FeedbackOut,
    ModelInfoOut,
    PredictionIn,
    PredictionOut,
    ScoredCategory,
    TeamRef,
)
from src.db.models.feedback import Feedback
from src.db.models.prediction import Prediction
from src.ml.decision import DecisionPolicy
from src.ml.priority_rules import PriorityRules
from src.ml.store import ModelStore

logger = structlog.get_logger()

# Team name mapping
TEAM_NAMES: Dict[str, str] = {
    "ACCESS": "Access and Identity Team",
    "HARDWARE": "Desktop and Hardware Support",
    "STORAGE": "Storage and Infrastructure Team",
    "HR": "HR Systems Support",
    "PROCUREMENT": "Procurement and Asset Team",
    "PROJECTS": "Project and Application Support",
    "SERVICE_DESK": "Service Desk Triage",
}


class InferenceController:
    """Orchestrates model inference, routing policy, priority overrides, and database logging."""

    def __init__(self) -> None:
        self.store = ModelStore.get_instance()
        self.decision_policy = DecisionPolicy()
        self.priority_rules = PriorityRules()

    def predict(
        self,
        payload: PredictionIn,
        db: Session,
        actor_id: Optional[uuid.UUID] = None,
    ) -> PredictionOut:
        # Validate text constraints
        raw_text = payload.text.strip()
        if not raw_text:
            raise DomainError(
                code="TEXT_EMPTY",
                message="Ticket text cannot be empty or solely whitespace",
                status_code=400,
                field="text",
            )
        if len(payload.text) > 5000:
            raise DomainError(
                code="TEXT_TOO_LONG",
                message="Ticket text exceeds the maximum 5,000 character limit",
                status_code=400,
                field="text",
                details={"length": len(payload.text), "max": 5000},
            )

        if not self.store.is_ready:
            raise ModelUnavailableError("Inference model is currently unavailable or degraded")

        predictor = self.store.get_predictor()
        manifest = self.store.get_manifest()
        threshold = float(manifest.get("threshold", 0.69))

        # 1. Scikit-learn dual prediction
        raw_pred = predictor.predict(payload.text)

        # 2. Decision policy (threshold, multi-issue, miscellaneous)
        decision_result = self.decision_policy.evaluate(
            predicted_category=raw_pred.category,
            confidence=raw_pred.category_confidence,
            top_categories=raw_pred.top_categories,
            text=payload.text,
            threshold=threshold,
            model_available=True,
        )

        # 3. Priority rules override (outage, whole team blocked, etc.)
        rule_flags = {"blocking_team": payload.blocking_team}
        prio_result = self.priority_rules.apply(
            model_priority=raw_pred.priority,
            text=payload.text,
            flags=rule_flags,
        )

        # 4. Resolve routed team reference
        routed_team_code = decision_result.routed_team
        routed_team_name = TEAM_NAMES.get(routed_team_code, "Service Desk Triage")
        team_ref = TeamRef(code=routed_team_code, name=routed_team_name)

        # 5. Format top categories
        top_cats = [
            ScoredCategory(category=item["category"], score=round(float(item["score"]), 4))
            for item in raw_pred.top_categories
        ]

        text_hash = hashlib.sha256(payload.text.encode("utf-8")).hexdigest()
        text_preview = payload.text[:200].replace("\n", " ").strip()
        prediction_id = uuid.uuid4()

        # 6. Persist to predictions table
        repo = InferenceRepository(db)
        prediction_entity = Prediction(
            id=prediction_id,
            ticket_id=payload.ticket_id,
            text_hash=text_hash,
            text_preview=text_preview,
            category=raw_pred.category,
            category_confidence=round(float(raw_pred.category_confidence), 4),
            probabilities={k: round(float(v), 4) for k, v in raw_pred.probabilities.items()},
            priority=prio_result.priority,
            priority_confidence=round(float(raw_pred.priority_confidence), 4),
            priority_source=prio_result.source,
            decision=decision_result.decision,
            review_reason=decision_result.review_reason,
            routed_team=routed_team_code,
            threshold=threshold,
            model_version=raw_pred.model_version,
            priority_model_version=raw_pred.priority_model_version,
            latency_ms=raw_pred.latency_ms,
            source=payload.source,
        )
        try:
            repo.save_prediction(prediction_entity)
        except Exception as e:
            logger.error("Failed to log prediction to database", error=str(e))

        return PredictionOut(
            category=raw_pred.category,
            category_confidence=round(float(raw_pred.category_confidence), 4),
            top_categories=top_cats,
            priority=prio_result.priority,
            priority_confidence=round(float(raw_pred.priority_confidence), 4),
            priority_source=prio_result.source,
            decision=decision_result.decision,
            review_reason=decision_result.review_reason,
            routed_team=team_ref,
            threshold=threshold,
            model_version=raw_pred.model_version,
            priority_model_version=raw_pred.priority_model_version,
            prediction_id=prediction_id,
            latency_ms=raw_pred.latency_ms,
            top_keywords=raw_pred.top_keywords,
        )

    def predict_batch(self, payload: BatchPredictionIn, db: Session) -> BatchPredictionOut:
        results: List[PredictionOut] = []
        for item in payload.items:
            res = self.predict(item, db)
            results.append(res)
        return BatchPredictionOut(predictions=results, count=len(results))

    def get_model_info(self) -> ModelInfoOut:
        manifest = self.store.get_manifest()
        is_ready = self.store.is_ready

        return ModelInfoOut(
            model_name=manifest.get("model_name", "routedesk-routing"),
            version=manifest.get("version", "v1-baseline"),
            priority_version=manifest.get("priority_version", "v1-priority"),
            threshold=float(manifest.get("threshold", 0.69)),
            metrics=manifest.get("metrics", {}),
            labels=manifest.get("labels", []),
            fingerprint=manifest.get("preprocess_fingerprint", ""),
            loaded_at=self.store._loaded_at,
            degraded=not is_ready,
            python_version=manifest.get("python_version", ""),
            sklearn_version=manifest.get("sklearn_version", ""),
        )

    def record_feedback(
        self,
        payload: FeedbackIn,
        db: Session,
        actor_id: Optional[uuid.UUID] = None,
    ) -> FeedbackOut:
        repo = InferenceRepository(db)
        feedback_id = uuid.uuid4()
        feedback_entity = Feedback(
            id=feedback_id,
            ticket_id=payload.ticket_id,
            prediction_id=payload.prediction_id,
            kind=payload.kind,
            predicted_category=payload.predicted_category,
            corrected_category=payload.corrected_category,
            predicted_priority=payload.predicted_priority,
            corrected_priority=payload.corrected_priority,
            actor_id=actor_id,
            notes=payload.notes,
        )
        saved = repo.save_feedback(feedback_entity)
        from datetime import timezone
        return FeedbackOut(
            id=saved.id,
            status="recorded",
            created_at=saved.created_at.astimezone(timezone.utc).isoformat(),
        )
