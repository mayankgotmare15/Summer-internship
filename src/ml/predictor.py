"""Predictor runtime engine: text preprocessing, dual inference, and feature explainability."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
from src.ml.preprocess import preprocess_text


@dataclass
class RawPrediction:
    category: str
    category_confidence: float
    top_categories: List[Dict[str, Any]]
    probabilities: Dict[str, float]
    priority: str
    priority_confidence: float
    priority_probabilities: Dict[str, float]
    model_version: str
    priority_model_version: str
    latency_ms: int
    top_keywords: List[str] = field(default_factory=list)


class Predictor:
    """Predictor wrapping the scikit-learn pipelines for routing and priority."""

    def __init__(
        self,
        routing_pipeline: Any,
        priority_pipeline: Any,
        manifest: Dict[str, Any],
    ) -> None:
        self.routing_pipeline = routing_pipeline
        self.priority_pipeline = priority_pipeline
        self.manifest = manifest
        self.routing_version = manifest.get("version", "v1-baseline")
        self.priority_version = manifest.get("priority_version", "v1-priority")

    def explain(self, clean_text: str, predicted_category: str, top_n: int = 5) -> List[str]:
        """Extracts top explanatory features for the predicted class using TF-IDF weights and coefficients."""
        try:
            tfidf = self.routing_pipeline.named_steps.get("tfidf")
            clf = self.routing_pipeline.named_steps.get("clf")
            if not tfidf or not clf or not hasattr(clf, "coef_"):
                return []

            vec = tfidf.transform([clean_text])
            if vec.nnz == 0:
                return []

            classes = list(clf.classes_)
            if predicted_category not in classes:
                return []
            class_idx = classes.index(predicted_category)

            coef = clf.coef_[class_idx]
            # Multiply sparse row by class coefficients
            feature_impacts = vec.multiply(coef).tocsr()
            indices = feature_impacts.indices
            data = feature_impacts.data

            if len(data) == 0:
                return []

            sorted_order = np.argsort(-data)
            top_k = sorted_order[:top_n]
            feature_names = tfidf.get_feature_names_out()
            keywords = []
            for idx_pos in top_k:
                if data[idx_pos] > 0:
                    keywords.append(str(feature_names[indices[idx_pos]]))
            return keywords
        except Exception:
            return []

    def predict(self, raw_text: str) -> RawPrediction:
        """Executes inference for both routing and priority on the normalized text."""
        t0 = time.perf_counter()

        # 1. Shared text preprocessing (PRD FR-03)
        clean_text = preprocess_text(raw_text)
        if not clean_text:
            clean_text = "ticket"

        # 2. Routing prediction & probability distribution
        routing_probs = self.routing_pipeline.predict_proba([clean_text])[0]
        routing_classes = list(self.routing_pipeline.classes_)

        cat_prob_map = {
            cls_name: float(routing_probs[idx])
            for idx, cls_name in enumerate(routing_classes)
        }
        # Sort classes descending by probability
        sorted_cats = sorted(
            [{"category": cls_name, "score": cat_prob_map[cls_name]} for cls_name in routing_classes],
            key=lambda x: x["score"],
            reverse=True,
        )

        top_category = sorted_cats[0]["category"]
        category_confidence = sorted_cats[0]["score"]

        # 3. Priority prediction & probability distribution
        try:
            priority_probs = self.priority_pipeline.predict_proba([clean_text])[0]
            priority_classes = list(self.priority_pipeline.classes_)
            prio_prob_map = {
                prio_name: float(priority_probs[idx])
                for idx, prio_name in enumerate(priority_classes)
            }
            top_prio_idx = int(np.argmax(priority_probs))
            top_priority = priority_classes[top_prio_idx]
            priority_confidence = float(priority_probs[top_prio_idx])
        except Exception:
            prio_prob_map = {"Low": 0.25, "Medium": 0.50, "High": 0.20, "Critical": 0.05}
            top_priority = "Medium"
            priority_confidence = 0.50

        # 4. Explainability keywords
        top_keywords = self.explain(clean_text, top_category, top_n=5)

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        return RawPrediction(
            category=top_category,
            category_confidence=category_confidence,
            top_categories=sorted_cats[:3],
            probabilities=cat_prob_map,
            priority=top_priority,
            priority_confidence=priority_confidence,
            priority_probabilities=prio_prob_map,
            model_version=self.routing_version,
            priority_model_version=self.priority_version,
            latency_ms=elapsed_ms,
            top_keywords=top_keywords,
        )
