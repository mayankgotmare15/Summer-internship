"""
Unit tests for decision logic, confidence thresholds, and priority overrides.
"""

from src.serving.decision import DecisionEngine


def test_decision_auto_route_above_threshold():
    engine = DecisionEngine(default_threshold=0.75)
    decision, team = engine.evaluate_routing("Hardware", 0.88)
    assert decision == "auto_route"
    assert team == "Desktop Support & Hardware Services"


def test_decision_human_review_below_threshold():
    engine = DecisionEngine(default_threshold=0.75)
    decision, team = engine.evaluate_routing("Access", 0.62)
    assert decision == "human_review"
    assert team == "Human Triage Queue"


def test_decision_exact_threshold():
    engine = DecisionEngine(default_threshold=0.75)
    decision, team = engine.evaluate_routing("Storage", 0.75)
    assert decision == "auto_route"
    assert team == "Cloud & Storage Infrastructure"


def test_priority_override_critical_keyword():
    engine = DecisionEngine()
    final_prio, overridden = engine.apply_priority_overrides(
        "Production server outage affecting all clients",
        predicted_priority="Low",
        priority_confidence=0.9
    )
    assert final_prio == "Critical"
    assert overridden is True


def test_priority_no_override():
    engine = DecisionEngine()
    final_prio, overridden = engine.apply_priority_overrides(
        "Please install python on my mac",
        predicted_priority="Medium",
        priority_confidence=0.8
    )
    assert final_prio == "Medium"
    assert overridden is False
