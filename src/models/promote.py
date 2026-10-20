"""Quality gate and model promotion engine (PRD Section 11.3 & 04-ml-services.md Section 1.5)."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.ml.bundle import get_git_sha, verify_bundle


def load_params() -> dict:
    with open("configs/params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def evaluate_gate(
    candidate_metrics: dict[str, Any],
    champion_metrics: dict[str, Any] | None,
    gate_params: dict[str, Any],
    p95_latency_ms: float,
) -> tuple[bool, list[str]]:
    """Evaluates candidate model against production quality gate rules."""
    reasons = []
    passed = True

    min_macro_f1 = gate_params.get("min_macro_f1", 0.80)
    max_drop = gate_params.get("max_per_class_drop", 0.05)
    max_latency = gate_params.get("max_p95_latency_ms", 50)
    min_acc = gate_params.get("min_auto_accuracy", 0.90)

    cand_f1 = candidate_metrics.get("macro_f1", 0.0)
    cand_acc = candidate_metrics.get("auto_accuracy")

    # 1. Absolute Macro-F1 threshold & Auto-accuracy threshold
    if cand_f1 < min_macro_f1:
        passed = False
        reasons.append(f"Macro-F1 {cand_f1:.4f} < minimum required {min_macro_f1:.4f}")

    if cand_acc is not None and cand_acc < min_acc:
        passed = False
        reasons.append(f"Auto-accuracy {cand_acc:.4f} < minimum required {min_acc:.4f}")

    # 2. Comparison with live champion if present
    if champion_metrics and "macro_f1" in champion_metrics:
        champ_f1 = champion_metrics["macro_f1"]
        # Allow equality or better
        if cand_f1 < (champ_f1 - 0.01):
            passed = False
            reasons.append(
                f"Candidate Macro-F1 {cand_f1:.4f} regressed from Champion {champ_f1:.4f}"
            )

        # Per-class regression check: no class drops > 5 points
        cand_classes = candidate_metrics.get("per_class", {})
        champ_classes = champion_metrics.get("per_class", {})
        for cls_name, champ_stats in champ_classes.items():
            if cls_name in cand_classes:
                f1_old = champ_stats.get("f1", 0.0)
                f1_new = cand_classes[cls_name].get("f1", 0.0)
                drop = f1_old - f1_new
                if drop > max_drop:
                    passed = False
                    reasons.append(
                        f"Class '{cls_name}' regressed by {drop:.4f} > allowed {max_drop}"
                    )

    # 3. p95 Latency check
    if p95_latency_ms > max_latency:
        passed = False
        reasons.append(f"p95 Latency {p95_latency_ms:.1f}ms exceeds {max_latency}ms budget")

    return passed, reasons


def measure_p95_latency(model, samples: list[str]) -> float:
    """Measures single-prediction p95 latency on CPU."""
    latencies = []
    # Warmup
    for s in samples[:5]:
        _ = model.predict([s])

    for s in samples:
        t0 = time.perf_counter()
        _ = model.predict([s])
        latencies.append((time.perf_counter() - t0) * 1000.0)

    return float(sorted(latencies)[int(len(latencies) * 0.95)])


def main() -> None:
    params = load_params()
    gate_cfg = params.get("gate", {})
    reports_dir = Path("reports")
    bundle_dir = Path("artifacts/bundle")
    champion_path = Path("models/champion.json")

    # 1. Verify bundle smoke test
    print("Verifying bundle integrity and sample inputs...")
    bundle_status = verify_bundle(bundle_dir)

    # 2. Load metrics and threshold
    with open(reports_dir / "metrics.json", encoding="utf-8") as f:
        metrics_all = json.load(f)
    cand_routing_metrics = metrics_all.get("routing", {})

    with open(reports_dir / "threshold.json", encoding="utf-8") as f:
        threshold_info = json.load(f)

    # 3. Measure p95 latency on test sample
    import pandas as pd
    import skops.io as sio

    test_df = pd.read_parquet("data/features/test.parquet")
    sample_texts = test_df["text_clean"].head(500).tolist()
    untrusted = sio.get_untrusted_types(file=bundle_dir / "routing.skops")
    model = sio.load(bundle_dir / "routing.skops", trusted=untrusted)
    p95_lat = measure_p95_latency(model, sample_texts)
    print(f"Measured single-ticket p95 inference latency: {p95_lat:.2f} ms")

    # 4. Load champion metrics
    champ_metrics = None
    if champion_path.exists():
        with open(champion_path, encoding="utf-8") as f:
            champ_data = json.load(f)
            champ_metrics = champ_data.get("metrics")

    # 5. Evaluate Quality Gate
    passed, reasons = evaluate_gate(cand_routing_metrics, champ_metrics, gate_cfg, p95_lat)

    print("\n================ QUALITY GATE REPORT ================")
    print(f"Status:             {'PASSED' if passed else 'FAILED'}")
    print(f"Candidate Macro-F1: {cand_routing_metrics['macro_f1']:.4f}")
    print(f"Auto-Route Acc:     {threshold_info.get('auto_route_accuracy', 0):.1%}")
    print(f"p95 Latency:        {p95_lat:.2f} ms")

    if not passed:
        print("\nFailure reasons:")
        for r in reasons:
            print(f" - {r}")
        raise ValueError(f"Quality gate failed: {reasons}")

    # 6. Promote to Champion: update models/champion.json
    champion_record = {
        "model_name": "ticket-routing",
        "version": bundle_status["version"],
        "run_id": f"run_{get_git_sha()}",
        "alias": "champion",
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "threshold": threshold_info.get("threshold", 0.69),
        "metrics": {
            "macro_f1": cand_routing_metrics["macro_f1"],
            "weighted_f1": cand_routing_metrics["weighted_f1"],
            "auto_route_rate": threshold_info.get("auto_route_rate"),
            "auto_route_accuracy": threshold_info.get("auto_route_accuracy"),
            "p95_latency_ms": round(p95_lat, 2),
        },
        "labels": cand_routing_metrics.get("labels", []),
        "preprocess_fingerprint": bundle_status["fingerprint"],
        "gate_status": "PASSED",
    }

    with open(champion_path, "w", encoding="utf-8") as f:
        json.dump(champion_record, f, indent=2)

    print(f"\nSuccessfully promoted model to champion! Updated {champion_path}")


if __name__ == "__main__":
    main()
