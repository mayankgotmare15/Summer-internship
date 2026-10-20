"""Database repository for predictions and feedback queries."""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from src.db.models.feedback import Feedback
from src.db.models.prediction import Prediction


class InferenceRepository:
    """Repository managing persistence for model predictions and feedback records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save_prediction(self, prediction: Prediction) -> Prediction:
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        return prediction

    def get_prediction_by_id(self, prediction_id: uuid.UUID) -> Optional[Prediction]:
        return self.db.query(Prediction).filter(Prediction.id == prediction_id).first()

    def save_feedback(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_recent_predictions(self, limit: int = 50) -> List[Prediction]:
        return (
            self.db.query(Prediction)
            .order_by(Prediction.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_unexported_feedback(self, limit: int = 100) -> List[Feedback]:
        return (
            self.db.query(Feedback)
            .filter(Feedback.exported_at.is_(None))
            .order_by(Feedback.created_at.asc())
            .limit(limit)
            .all()
        )
