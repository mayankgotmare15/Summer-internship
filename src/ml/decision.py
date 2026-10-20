"""Routing decision logic applying confidence thresholds, multi-issue detection, and team mapping."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RE_CONJUNCTION = re.compile(
    r"\b(and also|and my|and our|plus|along with|as well as)\b", re.IGNORECASE
)


@dataclass
class DecisionResult:
    decision: str  # "auto_route" | "human_review"
    review_reason: str | None  # "low_confidence" | "multi_issue" | "miscellaneous" | "model_unavailable"
    routed_team: str  # team code, e.g. "ACCESS", "SERVICE_DESK"
    threshold: float


class DecisionPolicy:
    def __init__(self, routing_map_path: Path = Path("configs/routing_map.yaml")):
        self.routing_map: dict[str, str] = {}
        self._load_routing_map(routing_map_path)

    def _load_routing_map(self, path: Path) -> None:
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                cats = data.get("categories", {})
                for cat_name, info in cats.items():
                    self.routing_map[cat_name] = info.get("team_code", "SERVICE_DESK")
            except Exception:
                pass

    def evaluate(
        self,
        predicted_category: str,
        confidence: float,
        top_categories: list[dict[str, Any]],
        text: str,
        threshold: float = 0.69,
        model_available: bool = True,
    ) -> DecisionResult:
        """Applies confidence threshold, multi-issue detection, and Miscellaneous category rule."""
        if not model_available:
            return DecisionResult(
                decision="human_review",
                review_reason="model_unavailable",
                routed_team="SERVICE_DESK",
                threshold=threshold,
            )

        if predicted_category == "Miscellaneous":
            return DecisionResult(
                decision="human_review",
                review_reason="miscellaneous",
                routed_team="SERVICE_DESK",
                threshold=threshold,
            )

        if confidence < threshold:
            return DecisionResult(
                decision="human_review",
                review_reason="low_confidence",
                routed_team="SERVICE_DESK",
                threshold=threshold,
            )

        # Multi-issue check: secondary category >= 0.30 and presence of conjunction
        if len(top_categories) > 1:
            second_cat = top_categories[1]
            if second_cat.get("score", 0.0) >= 0.30 and RE_CONJUNCTION.search(text):
                return DecisionResult(
                    decision="human_review",
                    review_reason="multi_issue",
                    routed_team="SERVICE_DESK",
                    threshold=threshold,
                )

        # Confident single-issue ticket
        target_team = self.routing_map.get(predicted_category, "SERVICE_DESK")
        return DecisionResult(
            decision="auto_route",
            review_reason=None,
            routed_team=target_team,
            threshold=threshold,
        )
