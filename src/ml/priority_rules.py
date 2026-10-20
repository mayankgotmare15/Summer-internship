"""Priority rules engine: keyword and flag overrides that can elevate priority (PRD Section 9.2)."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

PRIORITY_RANKS = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4,
}

REVERSE_RANKS = {v: k for k, v in PRIORITY_RANKS.items()}


class PriorityRules:
    def __init__(self, rules_path: Path = Path("configs/priority_rules.yaml")):
        self.critical_keywords: List[str] = [
            "outage", "server down", "production down", "data breach",
            "ransomware", "security incident", "all users blocked", "company wide"
        ]
        self.high_keywords: List[str] = [
            "blocked", "cannot work", "urgent", "vip", "deadline today",
            "client demo", "whole team"
        ]
        self._load_rules(rules_path)

    def _load_rules(self, rules_path: Path) -> None:
        if rules_path.exists():
            try:
                with open(rules_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                kw = cfg.get("keyword_rules", {})
                if "Critical" in kw:
                    self.critical_keywords = kw["Critical"]
                if "High" in kw:
                    self.high_keywords = kw["High"]
            except Exception:
                pass

    def evaluate(
        self,
        base_priority: str,
        text: str,
        blocking_team: bool = False,
    ) -> Dict[str, str]:
        """Evaluates priority rules. Can only raise priority, never lower it."""
        text_lower = text.lower()
        current_rank = PRIORITY_RANKS.get(base_priority, 2) # Default Medium
        raised_rank = current_rank
        source = "model"

        # Check Critical triggers
        for kw in self.critical_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                raised_rank = max(raised_rank, PRIORITY_RANKS["Critical"])
                source = "rule"
                break

        # Check High triggers
        if raised_rank < PRIORITY_RANKS["Critical"]:
            if blocking_team:
                raised_rank = max(raised_rank, PRIORITY_RANKS["High"])
                source = "rule"
            else:
                for kw in self.high_keywords:
                    if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                        raised_rank = max(raised_rank, PRIORITY_RANKS["High"])
                        source = "rule"
                        break

        final_priority = REVERSE_RANKS.get(raised_rank, base_priority)
        return {
            "priority": final_priority,
            "source": source if final_priority != base_priority else "model",
        }

    def apply(
        self,
        model_priority: str,
        text: str,
        flags: Optional[Dict[str, Any]] = None,
    ) -> Any:
        from collections import namedtuple
        flags = flags or {}
        blocking = flags.get("blocking_team", False)
        res = self.evaluate(model_priority, text, blocking_team=blocking)
        Result = namedtuple("PriorityRuleResult", ["priority", "source"])
        return Result(priority=res["priority"], source=res["source"])

