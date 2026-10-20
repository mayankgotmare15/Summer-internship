"""Unit tests for decision logic, confidence thresholds, and priority override rules."""

from src.ml.decision import DecisionPolicy
from src.ml.priority_rules import PriorityRules


def test_auto_route_above_threshold():
    policy = DecisionPolicy()
    res = policy.evaluate(
        predicted_category="Access",
        confidence=0.85,
        top_categories=[{"category": "Access", "score": 0.85}],
        text="vpn disconnected",
        threshold=0.69,
    )
    assert res.decision == "auto_route"
    assert res.review_reason is None
    assert res.routed_team == "ACCESS"


def test_human_review_below_threshold():
    policy = DecisionPolicy()
    res = policy.evaluate(
        predicted_category="Hardware",
        confidence=0.52,
        top_categories=[{"category": "Hardware", "score": 0.52}],
        text="screen black after reboot",
        threshold=0.69,
    )
    assert res.decision == "human_review"
    assert res.review_reason == "low_confidence"
    assert res.routed_team == "SERVICE_DESK"


def test_miscellaneous_always_human_review():
    policy = DecisionPolicy()
    res = policy.evaluate(
        predicted_category="Miscellaneous",
        confidence=0.95,
        top_categories=[{"category": "Miscellaneous", "score": 0.95}],
        text="random general inquiry",
        threshold=0.69,
    )
    assert res.decision == "human_review"
    assert res.review_reason == "miscellaneous"


def test_multi_issue_triggers_human_review():
    policy = DecisionPolicy()
    res = policy.evaluate(
        predicted_category="Access",
        confidence=0.72,
        top_categories=[
            {"category": "Access", "score": 0.72},
            {"category": "Hardware", "score": 0.35},
        ],
        text="my password reset failed and also my laptop keyboard is not working",
        threshold=0.69,
    )
    assert res.decision == "human_review"
    assert res.review_reason == "multi_issue"


def test_priority_keyword_override_critical():
    rules = PriorityRules()
    res = rules.evaluate(
        base_priority="Medium",
        text="Major production outage on central login server",
        blocking_team=False,
    )
    assert res["priority"] == "Critical"
    assert res["source"] == "rule"


def test_priority_flag_override_high():
    rules = PriorityRules()
    res = rules.evaluate(
        base_priority="Low",
        text="need project repo access",
        blocking_team=True,
    )
    assert res["priority"] == "High"
    assert res["source"] == "rule"


def test_priority_never_downgrades():
    rules = PriorityRules()
    res = rules.evaluate(
        base_priority="Critical",
        text="simple question without keywords",
        blocking_team=False,
    )
    assert res["priority"] == "Critical"
    assert res["source"] == "model"
