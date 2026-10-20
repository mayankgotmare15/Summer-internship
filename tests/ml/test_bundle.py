"""Tests for model bundle verification, manifest schema, and training-serving skew detection."""

import json
from pathlib import Path

from src.ml.bundle import verify_bundle


def test_bundle_manifest_structure():
    manifest_path = Path("artifacts/bundle/manifest.json")
    assert manifest_path.exists(), "Manifest file missing in artifacts/bundle"

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["model_name"] == "routedesk-routing"
    assert "version" in manifest
    assert "threshold" in manifest
    assert isinstance(manifest["threshold"], float)
    assert "preprocess_fingerprint" in manifest
    assert len(manifest["preprocess_fingerprint"]) == 16
    assert "labels" in manifest
    assert len(manifest["labels"]) >= 7


def test_bundle_smoke_inputs_pass():
    res = verify_bundle(Path("artifacts/bundle"))
    assert res["status"] == "valid"
    assert len(res["smoke_results"]) == 5
    for s in res["smoke_results"]:
        assert s["predicted"] in [
            "Access",
            "Administrative rights",
            "HR Support",
            "Hardware",
            "Internal Project",
            "Miscellaneous",
            "Purchase",
            "Storage",
        ]
