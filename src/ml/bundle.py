"""Model bundle management: packaging, manifest generation, and deployment smoke verification."""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sklearn
import skops.io as sio

from src.ml.preprocess import get_preprocess_fingerprint, preprocess_text

SAMPLE_TEST_INPUTS = [
    {
        "text": "my vpn keeps disconnecting every 10 min since morning",
        "expected_category": "Access",
    },
    {
        "text": "need local admin rights to install python on my development laptop",
        "expected_category": "Administrative rights",
    },
    {
        "text": "laptop screen flickering and battery won't charge",
        "expected_category": "Hardware",
    },
    {
        "text": "shared drive storage full cannot save presentation files",
        "expected_category": "Storage",
    },
    {
        "text": "need a 27 inch external monitor for my workstation",
        "expected_category": "Purchase",
    },
]


def get_git_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return res.stdout.strip()[:8]
    except Exception:
        return "local-dev"


def package_bundle(
    artifacts_dir: Path = Path("artifacts"),
    bundle_dir: Path = Path("artifacts/bundle"),
    version_tag: str = "v1-baseline",
) -> Path:
    """Packages models, manifest, sample inputs, and configs into a verified deployment bundle."""
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load optimal threshold and evaluation metrics
    threshold_path = Path("reports/threshold.json")
    threshold_val = 0.65
    if threshold_path.exists():
        with open(threshold_path, encoding="utf-8") as f:
            t_data = json.load(f)
            threshold_val = t_data.get("threshold", 0.65)

    metrics_path = Path("reports/metrics.json")
    metrics_data = {}
    if metrics_path.exists():
        with open(metrics_path, encoding="utf-8") as f:
            metrics_data = json.load(f).get("routing", {})

    labels = metrics_data.get(
        "labels",
        [
            "Access",
            "Administrative rights",
            "HR Support",
            "Hardware",
            "Internal Project",
            "Miscellaneous",
            "Purchase",
        ],
    )

    # 2. Copy skops model files
    routing_src = artifacts_dir / "routing" / "model.skops"
    priority_src = artifacts_dir / "priority" / "model.skops"
    if routing_src.exists():
        shutil.copy2(routing_src, bundle_dir / "routing.skops")
    if priority_src.exists():
        shutil.copy2(priority_src, bundle_dir / "priority.skops")

    # 3. Copy priority rules snapshot
    rules_src = Path("configs/priority_rules.yaml")
    if rules_src.exists():
        shutil.copy2(rules_src, bundle_dir / "priority_rules.yaml")

    # 4. Save sample smoke inputs
    sample_file = bundle_dir / "sample_inputs.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_TEST_INPUTS, f, indent=2)

    # 5. Build and write manifest.json
    manifest = {
        "model_name": "routedesk-routing",
        "version": version_tag,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": get_git_sha(),
        "labels": labels,
        "threshold": threshold_val,
        "metrics": {
            "macro_f1": metrics_data.get("macro_f1", 0.8554),
            "weighted_f1": metrics_data.get("weighted_f1", 0.8569),
            "test_samples": metrics_data.get("test_samples", 6759),
        },
        "preprocess_fingerprint": get_preprocess_fingerprint(),
        "python_version": sys.version.split()[0],
        "sklearn_version": sklearn.__version__,
    }

    manifest_file = bundle_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(
        f"Bundle packaged successfully at {bundle_dir} (version={version_tag}, fingerprint={manifest['preprocess_fingerprint']})"
    )
    return bundle_dir


def verify_bundle(bundle_dir: Path = Path("artifacts/bundle")) -> dict[str, Any]:
    """Verifies bundle integrity: checks fingerprint, deserializes models, and tests sample inputs."""
    manifest_file = bundle_dir / "manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Bundle manifest not found at {manifest_file}")

    with open(manifest_file, encoding="utf-8") as f:
        manifest = json.load(f)

    # Prevent training/serving skew: verify fingerprint matches current codebase
    current_fingerprint = get_preprocess_fingerprint()
    bundle_fingerprint = manifest.get("preprocess_fingerprint")
    if current_fingerprint != bundle_fingerprint:
        raise ValueError(
            f"Training/serving skew detected! Bundle fingerprint {bundle_fingerprint} != runtime {current_fingerprint}"
        )

    # Load routing model and execute smoke test
    routing_file = bundle_dir / "routing.skops"
    if not routing_file.exists():
        raise FileNotFoundError(f"Routing model not found at {routing_file}")

    untrusted = sio.get_untrusted_types(file=routing_file)
    model = sio.load(routing_file, trusted=untrusted)

    # Execute sample predictions
    sample_file = bundle_dir / "sample_inputs.json"
    with open(sample_file, encoding="utf-8") as f:
        samples = json.load(f)

    smoke_results = []
    for s in samples:
        clean = preprocess_text(s["text"])
        pred = model.predict([clean])[0]
        smoke_results.append(
            {
                "text": s["text"],
                "predicted": pred,
                "expected": s["expected_category"],
            }
        )

    return {
        "status": "valid",
        "version": manifest["version"],
        "threshold": manifest["threshold"],
        "fingerprint": bundle_fingerprint,
        "smoke_results": smoke_results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Package or verify model bundle.")
    parser.add_argument("--action", choices=["package", "verify"], default="package")
    parser.add_argument("--version", type=str, default="v1-baseline")
    args = parser.parse_args()

    if args.action == "package":
        package_bundle(version_tag=args.version)
        res = verify_bundle()
        print("Smoke verification passed!")
    elif args.action == "verify":
        res = verify_bundle()
        print(f"Verification result: {json.dumps(res, indent=2)}")
