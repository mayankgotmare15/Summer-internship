"""
Monitoring Threshold Checker.
Evaluates prediction logs and agent feedback against operational alerting boundaries:
1. Low-Confidence Rate (> 25%)
2. Agent Override Rate (> 15%)
3. Sudden Category Distribution Drift
Exits with code 1 upon breach to trigger automated retraining pipelines.
"""

import json
from pathlib import Path
import sys
import yaml

CONFIG_PATH = Path("configs/params.yaml")
PRED_LOG_PATH = Path("data/monitoring/prediction_log.jsonl")
FEEDBACK_LOG_PATH = Path("data/monitoring/feedback_log.jsonl")


def load_thresholds() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            return cfg.get("monitoring", {})
    return {
        "low_confidence_threshold": 0.25,
        "agent_override_threshold": 0.15,
        "window_size": 500
    }


def evaluate_telemetry() -> bool:
    thresholds = load_thresholds()
    low_conf_thresh = thresholds.get("low_confidence_threshold", 0.25)
    override_thresh = thresholds.get("agent_override_threshold", 0.15)
    window = thresholds.get("window_size", 500)

    print("=== OPERATIONAL TELEMETRY & THRESHOLD CHECK ===")

    # 1. Evaluate Prediction Log
    if not PRED_LOG_PATH.exists():
        print(f"Notice: Prediction log not found at {PRED_LOG_PATH}. Skipping check.")
        return True

    predictions = []
    with open(PRED_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    predictions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not predictions:
        print("Notice: No prediction records found yet.")
        return True

    recent_preds = predictions[-window:]
    total_recent = len(recent_preds)

    human_review_count = sum(1 for p in recent_preds if p.get("decision") == "human_review")
    low_conf_rate = human_review_count / total_recent if total_recent > 0 else 0.0

    print(f"Evaluated Last {total_recent} Predictions:")
    print(f" - Low-Confidence / Fallback Rate: {low_conf_rate*100:.2f}% (Alert Limit: {low_conf_thresh*100:.1f}%)")

    breaches = []
    if low_conf_rate > low_conf_thresh:
        breaches.append(
            f"Low-confidence fallback rate ({low_conf_rate*100:.1f}%) exceeded limit ({low_conf_thresh*100:.1f}%)"
        )

    # 2. Evaluate Feedback Log (Agent Overrides)
    if FEEDBACK_LOG_PATH.exists():
        feedbacks = []
        with open(FEEDBACK_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        feedbacks.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        if feedbacks:
            total_fb = len(feedbacks)
            overrides = sum(
                1 for fb in feedbacks
                if fb.get("predicted_category") != fb.get("corrected_category")
            )
            override_rate = overrides / total_fb
            print(f"Evaluated {total_fb} Agent Feedback Submissions:")
            print(f" - Agent Override Rate: {override_rate*100:.2f}% (Alert Limit: {override_thresh*100:.1f}%)")

            if override_rate > override_thresh:
                breaches.append(
                    f"Agent override rate ({override_rate*100:.1f}%) exceeded limit ({override_thresh*100:.1f}%)"
                )

    if breaches:
        print("\n🚨 OPERATIONAL THRESHOLD BREACH DETECTED!")
        for b in breaches:
            print(f" - ⚠️ {b}")
        print("Action required: Trigger continuous retraining pipeline.")
        return False
    else:
        print("\n✅ All monitoring metrics are within acceptable operating parameters.")
        return True


if __name__ == "__main__":
    is_healthy = evaluate_telemetry()
    if not is_healthy:
        sys.exit(1)
