"""Phase 1.2 smoke test: download a sample image and run the ViT classifier.

Run from backend/:
    .venv/Scripts/python.exe scripts/test_image_classify.py
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import base64

from models.heatmap_generator import generate_heatmap_base64
from services.artifact_detector import scan_artifacts
from services.image_service import preprocess_and_classify
from utils.scoring import compute_authenticity_score, get_verdict_label

SAMPLE_URL = "https://picsum.photos/seed/deepshield/512/512"


def main() -> int:
    print(f"Fetching sample image: {SAMPLE_URL}")
    req = urllib.request.Request(SAMPLE_URL, headers={"User-Agent": "DeepShield/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    print(f"  got {len(data)} bytes")

    print("Running classifier (first run will download model ~350MB)…")
    pil, result = preprocess_and_classify(data)
    print(f"  image size: {pil.size}")
    print(f"  label: {result.label}")
    print(f"  confidence: {result.confidence:.4f}")
    print(f"  all scores: {result.all_scores}")

    score = compute_authenticity_score(result.confidence, result.label)
    verdict_label, severity = get_verdict_label(score)
    print(f"\n  authenticity_score: {score}")
    print(f"  verdict: {verdict_label} ({severity})")

    print("\nScanning artifact indicators\u2026")
    for ind in scan_artifacts(pil, data):
        print(f"  [{ind.severity.upper():6s}] {ind.type}: {ind.description} (conf {ind.confidence:.2f})")

    print("\nGenerating Grad-CAM heatmap\u2026")
    heatmap_url, heatmap_source = generate_heatmap_base64(pil)
    print(f"  heatmap source: {heatmap_source}")
    if not heatmap_url:
        print("  no heatmap (no face or fallback)")
        return 0
    header, b64 = heatmap_url.split(",", 1)
    out_path = Path(__file__).resolve().parent.parent / "heatmap_smoketest.png"
    out_path.write_bytes(base64.b64decode(b64))
    print(f"  saved: {out_path}")
    print(f"  data URL length: {len(heatmap_url)} chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
