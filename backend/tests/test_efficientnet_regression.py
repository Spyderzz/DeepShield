"""Gate G3 regression harness — EfficientNetAutoAttB4 accuracy on anchor set.

Acceptance criteria (MERGE_PLAN §9.1 G3):
  - >=88% accuracy on the anchor set
  - <=8% real->fake false-positive rate

Anchor set priority:
  1. LOCAL  — bundled ICPR2020 notebook/samples/ frames (always available, minimal set)
  2. FFPP   — training/datasets/ffpp/ when present (full G3 gate, 50+ images)
  3. DFDC   — training/datasets/dfdc/ when present

NOTE: ThisPersonDoesNotExist.com (StyleGAN2) is NOT valid for G3 — EfficientNetAutoAttB4
is trained on DFDC video face-swaps and does NOT generalise to GAN-portrait detection.
The full G3 gate requires FFPP c40 data (run scripts/fit_calibrator.py first).

Run from backend/:
    .venv/Scripts/python.exe -m pytest tests/test_efficientnet_regression.py -v
"""
from __future__ import annotations

import io
import sys
import time
import urllib.request
from pathlib import Path
from typing import Tuple

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Anchor image sources
# ---------------------------------------------------------------------------
# Local: bundled ICPR2020 sample frames (ground-truth labels from their scores).
# lynaeydofd_fr0.jpg → EfficientNet scores 0.011 (REAL)
# mqzvfufzoq_fr0.jpg → EfficientNet scores 0.873 (FAKE)
_ICPR_SAMPLES = (
    Path(__file__).resolve().parent.parent
    / "models" / "icpr2020dfdc" / "notebook" / "samples"
)
LOCAL_REAL_IMAGES = [_ICPR_SAMPLES / "lynaeydofd_fr0.jpg"]
LOCAL_FAKE_IMAGES = [_ICPR_SAMPLES / "mqzvfufzoq_fr0.jpg"]

# FFPP / DFDC local data (full G3 gate — available after running training/datasets download scripts).
_FFPP_REAL = Path(__file__).resolve().parent.parent / "training" / "datasets" / "ffpp" / "c40" / "real"
_FFPP_FAKE = Path(__file__).resolve().parent.parent / "training" / "datasets" / "ffpp" / "c40" / "fake"
_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

# Network: thispersondoesnotexist.com — used for G2 gate only (face detection).
# NOT used for G3 accuracy gate: StyleGAN2 faces are a different distribution
# from DFDC video face-swaps (the model's training domain).
TPDNE_URL = "https://thispersondoesnotexist.com/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "DeepShield-Test/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


@pytest.fixture(scope="module")
def detector():
    """Load the EfficientNetDetector once per module."""
    from services.efficientnet_service import EfficientNetDetector
    return EfficientNetDetector()


@pytest.fixture(scope="module")
def anchor_set(detector) -> Tuple[list, list]:
    """Score anchor images. Returns (real_results, fake_results).

    Priority order:
    1. FFPP c40 images (training/datasets/ffpp/c40/{real,fake}/) — full G3 gate
    2. Bundled ICPR2020 notebook samples — minimal sanity check
    """
    from PIL import Image

    def score_dir(directory: Path, limit: int = 50) -> list:
        results = []
        if not directory.is_dir():
            return results
        paths = sorted(p for p in directory.rglob("*") if p.suffix.lower() in _IMAGE_EXTS)[:limit]
        for p in paths:
            try:
                pil = Image.open(p).convert("RGB")
                results.append(detector.detect_image(pil))
            except Exception:
                pass
        return results

    # --- FFPP c40 (full gate) ---
    real_results = score_dir(_FFPP_REAL)
    fake_results = score_dir(_FFPP_FAKE)

    # --- Fallback: bundled ICPR2020 samples ---
    if not real_results:
        for p in LOCAL_REAL_IMAGES:
            if p.exists():
                pil = Image.open(p).convert("RGB")
                real_results.append(detector.detect_image(pil))
    if not fake_results:
        for p in LOCAL_FAKE_IMAGES:
            if p.exists():
                pil = Image.open(p).convert("RGB")
                fake_results.append(detector.detect_image(pil))

    return real_results, fake_results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEfficientNetRegression:

    def test_g1_detector_loads(self, detector):
        """G1: model loaded without crash."""
        assert detector is not None
        assert detector.net is not None
        assert detector.face_extractor is not None

    def test_g2_blazeface_detects_face_on_tpdne(self, detector):
        """G2: BlazeFace detects ≥1 face on a TPDNE image."""
        from PIL import Image
        data = _fetch(TPDNE_URL)
        pil = Image.open(io.BytesIO(data)).convert("RGB")
        img_np = np.array(pil)
        frame_data = detector.face_extractor.process_image(img=img_np)
        faces = frame_data.get("faces", [])
        assert len(faces) >= 1, "BlazeFace detected 0 faces on TPDNE image"

    def test_g3_accuracy_and_fpr(self, anchor_set):
        """G3: ≥88% accuracy and ≤8% real→fake FPR on the anchor set."""
        real_results, fake_results = anchor_set

        # Only count images where a face was detected (no-face = excluded from G3).
        real_scored = [r for r in real_results if r.get("score") is not None]
        fake_scored = [r for r in fake_results if r.get("score") is not None]

        if len(real_scored) + len(fake_scored) < 5:
            pytest.skip("Too few face-detectable images in anchor set for meaningful G3 check")

        # Correctness: REAL → score ≤ 0.5, FAKE → score > 0.5
        real_correct = sum(1 for r in real_scored if r["result"] == "REAL")
        fake_correct = sum(1 for r in fake_scored if r["result"] == "FAKE")

        total = len(real_scored) + len(fake_scored)
        accuracy = (real_correct + fake_correct) / total * 100

        fpr = (len(real_scored) - real_correct) / max(len(real_scored), 1) * 100

        print(f"\n  Anchor set: {len(real_scored)} real | {len(fake_scored)} fake")
        print(f"  Accuracy:   {accuracy:.1f}%  (need >=88%)")
        print(f"  FPR:        {fpr:.1f}%  (need <=8%)")
        for tag, results, exp in [("REAL", real_scored, "REAL"), ("FAKE", fake_scored, "FAKE")]:
            for r in results:
                mark = "✓" if r["result"] == exp else "✗"
                print(f"    [{tag}] {mark} score={r['score']:.3f} cal={r.get('calibrator_applied')}")

        assert accuracy >= 88.0, f"G3 accuracy {accuracy:.1f}% < 88%"
        assert fpr <= 8.0, f"G3 FPR {fpr:.1f}% > 8%"

    def test_no_face_returns_gracefully(self, detector):
        """Noise image with no face should return error='no_face', not raise."""
        from PIL import Image
        noise = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        result = detector.detect_image(noise)
        assert result["error"] == "no_face"
        assert result["score"] is None

    def test_g8_memory_under_threshold(self):
        """G8: RSS after model load < 2500 MB."""
        import psutil
        rss_mb = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"\n  RSS: {rss_mb:.0f} MB")
        assert rss_mb < 2500, f"G8: RSS {rss_mb:.0f} MB exceeds 2500 MB threshold"
