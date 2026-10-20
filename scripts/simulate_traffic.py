"""Production Traffic Simulator for Drift and Model Decay Drills.

Replays production batches to RouteDesk inference and feedback endpoints:
1. Normal traffic: Samples from baseline test distribution.
2. Shifted-vocabulary drift: Injects emerging tech stack keywords.
3. Held-back category drift: Replays isolated 'Storage' holdout tickets.
4. Agent feedback: Simulates human triage corrections and logs ground truth.
"""

from __future__ import annotations

import argparse
import random
import sys
import uuid
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import pandas as pd

from src.db.models.feedback import Feedback
from src.db.models.prediction import Prediction
from src.db.session import SessionLocal

# Shifted-vocabulary tickets (DevOps, Cloud, Containerization)
SHIFTED_VOCAB_TICKETS = [
    "Kubernetes pod CrashLoopBackOff in production cluster ecom-prod-us-east-1",
    "Terraform state lock acquisition failed on AWS DynamoDB backend",
    "Docker container OOMKilled memory limit exceeded on worker node 4",
    "Istio service mesh sidecar injection failing with admission webhook error",
    "ArgoCD application sync degraded due to GitOps helm values mismatch",
    "Datadog agent tracing disconnected on ingress controller gateway",
    "Kafka consumer lag surging on payment-events topic partition 3",
    "Prometheus scrape target timeout on node-exporter daemonset",
    "AWS IAM role trust relationship invalid for OpenID connect provider",
    "Vault token renewal expired causing microservice database connection pool exhaustion",
    "Helm chart deployment rollout stalled waiting for replica set stabilization",
    "GitHub Actions runner daemon offline in private VPC subnet",
    "Elasticsearch cluster red status unassigned shards due to disk watermark",
    "Cloudflare edge certificate expired on staging internal gateway",
    "OpenTelemetry collector pipeline buffer overflow dropping traces",
]


def load_dataset_samples(path: str | Path, n: int = 100) -> list[dict[str, str]]:
    """Loads text and category samples from parquet dataset."""
    df = pd.read_parquet(path)
    sample_df = df.sample(n=min(n, len(df)), random_state=random.randint(1, 10000))
    return [{"text": row["text"], "expected_category": row.get("category", "")} for _, row in sample_df.iterrows()]


def send_prediction_http(
    base_url: str,
    text: str,
    blocking_team: bool = False,
) -> dict | None:
    """Sends inference request via HTTP client."""
    url = f"{base_url.rstrip('/')}/api/v1/predict"
    try:
        res = httpx.post(url, json={"text": text, "blocking_team": blocking_team}, timeout=10.0)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"HTTP request error: {e}")
    return None


def send_feedback_http(
    base_url: str,
    prediction_id: str,
    predicted_cat: str,
    corrected_cat: str,
) -> bool:
    """Logs agent correction feedback via HTTP client."""
    url = f"{base_url.rstrip('/')}/api/v1/feedback"
    payload = {
        "prediction_id": prediction_id,
        "kind": "agent_correction",
        "predicted_category": predicted_cat,
        "corrected_category": corrected_cat,
        "notes": f"Simulated triage correction: {predicted_cat} -> {corrected_cat}",
    }
    try:
        res = httpx.post(url, json=payload, timeout=10.0)
        return res.status_code in (200, 201)
    except Exception:
        return False


def run_direct_simulation(
    scenario: str,
    count: int = 100,
    with_feedback: bool = False,
) -> int:
    """Simulates production traffic directly against database and inference engine without requiring HTTP server."""
    from src.app.modules.inference.controller import InferenceController
    from src.app.modules.inference.schemas import FeedbackIn, PredictionIn

    ctrl = InferenceController()
    if not ctrl.store.is_ready:
        ctrl.store.load_bundle()

    items: list[dict[str, str]] = []

    if scenario == "normal":
        test_path = Path("data/processed/test.parquet")
        items = load_dataset_samples(test_path, n=count)
    elif scenario == "drift":
        # Combine repeated shifted vocabulary tickets
        expanded = SHIFTED_VOCAB_TICKETS * (count // len(SHIFTED_VOCAB_TICKETS) + 1)
        items = [{"text": t, "expected_category": "Internal Project"} for t in expanded[:count]]
    elif scenario == "holdout":
        holdout_path = Path("data/holdout/storage_holdout.parquet")
        items = load_dataset_samples(holdout_path, n=count)
        for it in items:
            it["expected_category"] = "Storage"
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    print(f"Simulating '{scenario}' traffic: {len(items)} tickets...")
    success_count = 0
    feedback_count = 0

    with SessionLocal() as db:
        for idx, item in enumerate(items, start=1):
            text = item["text"]
            expected = item.get("expected_category")

            try:
                pred = ctrl.predict(
                    PredictionIn(text=text, source=f"sim_{scenario}"),
                    db=db,
                    actor_id=uuid.uuid4(),
                )
                success_count += 1

                # If requested and predicted category disagrees with ground truth, record feedback
                if with_feedback and expected and pred.category != expected:
                    ctrl.record_feedback(
                        FeedbackIn(
                            prediction_id=pred.prediction_id,
                            kind="agent_correction",
                            predicted_category=pred.category,
                            corrected_category=expected,
                            notes=f"Simulated triage correction: {pred.category} -> {expected}",
                        ),
                        db=db,
                    )
                    feedback_count += 1

                if idx % 50 == 0 or idx == len(items):
                    print(f"  Processed {idx}/{len(items)} tickets (Logged {feedback_count} feedback overrides)")
            except Exception as e:
                print(f"  Error processing ticket #{idx}: {e}")

    print(f"Direct simulation complete: {success_count} predictions, {feedback_count} feedback corrections.\n")
    return success_count


def run_http_simulation(
    base_url: str,
    scenario: str,
    count: int = 100,
    with_feedback: bool = False,
) -> int:
    """Simulates production traffic over live HTTP endpoints."""
    items: list[dict[str, str]] = []

    if scenario == "normal":
        test_path = Path("data/processed/test.parquet")
        items = load_dataset_samples(test_path, n=count)
    elif scenario == "drift":
        expanded = SHIFTED_VOCAB_TICKETS * (count // len(SHIFTED_VOCAB_TICKETS) + 1)
        items = [{"text": t, "expected_category": "Internal Project"} for t in expanded[:count]]
    elif scenario == "holdout":
        holdout_path = Path("data/holdout/storage_holdout.parquet")
        items = load_dataset_samples(holdout_path, n=count)
        for it in items:
            it["expected_category"] = "Storage"
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    print(f"Simulating '{scenario}' HTTP traffic to {base_url}: {len(items)} tickets...")
    success_count = 0
    feedback_count = 0

    for idx, item in enumerate(items, start=1):
        text = item["text"]
        expected = item.get("expected_category")

        res = send_prediction_http(base_url, text)
        if res:
            success_count += 1
            pred_id = res.get("prediction_id")
            pred_cat = res.get("category")

            if with_feedback and expected and pred_cat != expected and pred_id:
                fb_ok = send_feedback_http(base_url, pred_id, pred_cat, expected)
                if fb_ok:
                    feedback_count += 1

        if idx % 50 == 0 or idx == len(items):
            print(f"  Processed {idx}/{len(items)} tickets (Logged {feedback_count} feedback overrides)")

    print(f"HTTP simulation complete: {success_count} predictions, {feedback_count} feedback corrections.\n")
    return success_count


def clear_simulation_data() -> None:
    """Utility to clean up prediction logs and feedback in test environments."""
    with SessionLocal() as db:
        num_fb = db.query(Feedback).delete()
        num_pr = db.query(Prediction).delete()
        db.commit()
    print(f"Cleared database logs: {num_pr} predictions, {num_fb} feedback records removed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate production traffic for drift and retraining drills.")
    parser.add_argument(
        "--scenario",
        choices=["normal", "drift", "holdout"],
        default="normal",
        help="Traffic scenario to generate",
    )
    parser.add_argument("--count", type=int, default=150, help="Number of tickets to send")
    parser.add_argument(
        "--with-feedback",
        action="store_true",
        help="Simulate human review corrections for misclassified tickets",
    )
    parser.add_argument("--base-url", default=None, help="HTTP base URL (if None, executes directly via DB engine)")
    parser.add_argument("--clean", action="store_true", help="Clear prediction and feedback tables prior to run")
    args = parser.parse_args()

    if args.clean:
        clear_simulation_data()

    if args.base_url:
        run_http_simulation(
            base_url=args.base_url,
            scenario=args.scenario,
            count=args.count,
            with_feedback=args.with_feedback,
        )
    else:
        run_direct_simulation(
            scenario=args.scenario,
            count=args.count,
            with_feedback=args.with_feedback,
        )


if __name__ == "__main__":
    main()
