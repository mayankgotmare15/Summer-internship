"""
Decision engine for ticket classification, routing assignment, and priority elevation rules.
"""

import os

import yaml

DEFAULT_ROUTING_MAP = {
    "Access": "Identity & Access Management (IAM)",
    "Administrative rights": "Endpoint Operations & Security",
    "HR Support": "People Operations & HR Systems",
    "Hardware": "Desktop Support & Hardware Services",
    "Internal Project": "Project Engineering & DevOps",
    "Miscellaneous": "General IT Service Desk",
    "Purchase": "IT Procurement & Asset Management",
    "Storage": "Cloud & Storage Infrastructure",
}

CRITICAL_OVERRIDE_KEYWORDS = [
    "outage",
    "system down",
    "production down",
    "security breach",
    "ransomware",
    "all users blocked",
    "emergency",
    "data loss",
]

HIGH_OVERRIDE_KEYWORDS = [
    "urgent",
    "blocked",
    "cannot work",
    "director",
    "executive",
    "deadline today",
]


class DecisionEngine:
    def __init__(
        self,
        routing_config_path: str | None = "configs/routing_map.yaml",
        default_threshold: float = 0.75,
    ):
        self.threshold = float(os.getenv("CONFIDENCE_THRESHOLD", default_threshold))
        self.routing_map = DEFAULT_ROUTING_MAP.copy()
        self.fallback_queue = "Human Triage Queue"

        if routing_config_path and os.path.exists(routing_config_path):
            try:
                with open(routing_config_path, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    if cfg and "routing_map" in cfg:
                        self.routing_map.update(cfg["routing_map"])
                    if cfg and "fallback_queue" in cfg:
                        self.fallback_queue = cfg["fallback_queue"]
            except (yaml.YAMLError, OSError):
                # Fallback to default routing map if config file cannot be read
                pass

    def evaluate_routing(
        self, predicted_category: str, category_confidence: float
    ) -> tuple[str, str]:
        """
        Determines routing decision and assigned team based on model confidence threshold.
        Returns (decision, routed_team).
        """
        if category_confidence >= self.threshold:
            decision = "auto_route"
            routed_team = self.routing_map.get(predicted_category, self.fallback_queue)
        else:
            decision = "human_review"
            routed_team = self.fallback_queue

        return decision, routed_team

    def apply_priority_overrides(
        self, raw_text: str, predicted_priority: str, priority_confidence: float
    ) -> tuple[str, bool]:
        """
        Checks for high-severity enterprise keywords to elevate priority safely.
        Returns (final_priority, was_overridden).
        """
        lower = raw_text.lower()
        for kw in CRITICAL_OVERRIDE_KEYWORDS:
            if kw in lower:
                return "Critical", True

        for kw in HIGH_OVERRIDE_KEYWORDS:
            if kw in lower and predicted_priority in ["Low", "Medium"]:
                return "High", True

        return predicted_priority, False
