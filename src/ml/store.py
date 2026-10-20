"""ModelStore: bundle loading, fingerprint verification, warmup, and atomic hot-reloading."""

import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional
import skops.io as sio
import structlog
from src.app.errors import ModelUnavailableError
from src.app.settings import get_settings
from src.ml.predictor import Predictor
from src.ml.preprocess import get_preprocess_fingerprint

logger = structlog.get_logger()


class ModelStore:
    """Manages loaded ML models in memory with thread-safe hot reload and skew checking."""

    _instance: Optional["ModelStore"] = None
    _lock = Lock()

    def __init__(self, bundle_dir: Optional[Path] = None) -> None:
        self.settings = get_settings()
        self.bundle_dir = bundle_dir or Path(self.settings.model_dir)
        self._predictor: Optional[Predictor] = None
        self._manifest: Dict[str, Any] = {}
        self._ready: bool = False
        self._loaded_at: Optional[str] = None
        self._mutex = Lock()

    @classmethod
    def get_instance(cls, bundle_dir: Optional[Path] = None) -> "ModelStore":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(bundle_dir)
            return cls._instance

    @property
    def is_ready(self) -> bool:
        return self._ready and self._predictor is not None

    def get_manifest(self) -> Dict[str, Any]:
        return self._manifest

    def get_predictor(self) -> Predictor:
        if not self.is_ready or self._predictor is None:
            raise ModelUnavailableError("Active model is not loaded or is currently in degraded mode")
        return self._predictor

    def load_bundle(self, bundle_dir: Optional[Path] = None) -> bool:
        """Loads and verifies model bundle from disk."""
        target_dir = bundle_dir or self.bundle_dir
        logger.info("Attempting to load model bundle", bundle_dir=str(target_dir))

        if not target_dir.exists():
            logger.warning("Model bundle directory not found", bundle_dir=str(target_dir))
            self._ready = False
            return False

        manifest_path = target_dir / "manifest.json"
        if not manifest_path.exists():
            logger.warning("Bundle manifest.json missing", path=str(manifest_path))
            self._ready = False
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Prevent training/serving skew (PRD FR-03 & 04-ml-services.md 1.3)
            current_fp = get_preprocess_fingerprint()
            bundle_fp = manifest.get("preprocess_fingerprint")
            if current_fp != bundle_fp:
                logger.error(
                    "Training/serving skew detected! Fingerprints mismatch",
                    runtime_fingerprint=current_fp,
                    bundle_fingerprint=bundle_fp,
                )
                self._ready = False
                return False

            routing_file = target_dir / "routing.skops"
            if not routing_file.exists():
                logger.error("Routing model file missing", path=str(routing_file))
                self._ready = False
                return False

            untrusted_routing = sio.get_untrusted_types(file=routing_file)
            routing_pipeline = sio.load(routing_file, trusted=untrusted_routing)

            # Load priority model if available
            priority_file = target_dir / "priority.skops"
            priority_pipeline = None
            if priority_file.exists():
                untrusted_priority = sio.get_untrusted_types(file=priority_file)
                priority_pipeline = sio.load(priority_file, trusted=untrusted_priority)

            new_predictor = Predictor(
                routing_pipeline=routing_pipeline,
                priority_pipeline=priority_pipeline,
                manifest=manifest,
            )

            # Warmup: run a sample prediction to initialize text tokenizers & caches
            from datetime import datetime, timezone
            _ = new_predictor.predict("warmup test ticket for vpn connection failure")

            with self._mutex:
                self._predictor = new_predictor
                self._manifest = manifest
                self._ready = True
                self._loaded_at = datetime.now(timezone.utc).isoformat()

            logger.info(
                "Model bundle successfully loaded and verified",
                version=manifest.get("version"),
                fingerprint=bundle_fp,
                threshold=manifest.get("threshold"),
            )
            return True

        except Exception as e:
            logger.error("Failed to load model bundle", error=str(e), exc_info=True)
            self._ready = False
            return False

    def reload(self) -> bool:
        """Atomic hot-reload invoked by admin endpoint."""
        logger.info("Hot-reloading model bundle from disk")
        return self.load_bundle()
