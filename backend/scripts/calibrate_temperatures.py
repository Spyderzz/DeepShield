#!/usr/bin/env python3
"""Phase C4 — Grid-search temperature scalars for AI-image detector heads.

Reads MANIFEST.csv, sweeps GENERAL_MODEL_TEMPERATURE and
DIFFUSION_MODEL_TEMPERATURE over a grid, and reports the combination that
maximises F1 on the eval set. Write the winning values to .env or config.py.

Usage (from backend/):
    .venv/Scripts/python.exe scripts/calibrate_temperatures.py
    .venv/Scripts/python.exe scripts/calibrate_temperatures.py --steps 10

Requires eval images to be present in tests/eval/images/.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MANIFEST = Path(__file__).resolve().parent.parent / "tests" / "eval" / "MANIFEST.csv"
IMAGES_ROOT = Path(__file__).resolve().parent.parent / "tests" / "eval" / "images"


def _load_manifest():
    rows = []
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            p = IMAGES_ROOT / Path(row["path"]).name
            if p.exists():
                rows.append({"path": p, "label": row["label"], "family": row["family"]})
    return rows


def _score_all(rows, t_gen: float, t_diff: float) -> list[dict]:
    import os
    os.environ["GENERAL_MODEL_TEMPERATURE"] = str(t_gen)
    os.environ["DIFFUSION_MODEL_TEMPERATURE"] = str(t_diff)

    # Force reload of settings (they're read at import time via pydantic-settings)
    import importlib
    import config as cfg_mod
    importlib.reload(cfg_mod)

    from services import general_image_service as gis
    importlib.reload(gis)
    from services import image_service as ims
    importlib.reload(ims)

    from PIL import Image

    results = []
    for row in rows:
        try:
            pil = Image.open(row["path"]).convert("RGB")
            clf = ims.classify_image(pil)
            results.append({
                "label": row["label"],
                "fake_prob": clf.confidence,
                "predicted_fake": clf.confidence >= 0.5,
                "actual_fake": row["label"] == "fake",
            })
        except Exception:
            pass
    return results


def _f1(results) -> float:
    tp = sum(1 for r in results if r["predicted_fake"] and r["actual_fake"])
    fp = sum(1 for r in results if r["predicted_fake"] and not r["actual_fake"])
    fn = sum(1 for r in results if not r["predicted_fake"] and r["actual_fake"])
    denom = 2 * tp + fp + fn
    return (2 * tp / denom) if denom > 0 else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=6,
                        help="Grid steps per axis (default: 6 → 36 combinations)")
    args = parser.parse_args()

    rows = _load_manifest()
    if not rows:
        print(f"[WARN] No eval images found in {IMAGES_ROOT}. Populate first.")
        return

    print(f"Calibrating on {len(rows)} images with {args.steps}x{args.steps} grid…\n")

    import numpy as np
    temps = list(np.linspace(0.5, 2.0, args.steps))

    best_f1, best_tg, best_td = 0.0, 1.0, 1.0
    print(f"  {'t_gen':>6}  {'t_diff':>6}  {'F1':>6}")
    print("  " + "-" * 24)
    for tg in temps:
        for td in temps:
            results = _score_all(rows, tg, td)
            f1 = _f1(results)
            if f1 > best_f1:
                best_f1, best_tg, best_td = f1, tg, td
            print(f"  {tg:6.2f}  {td:6.2f}  {f1:6.3f}")

    print(f"\nBest: GENERAL_MODEL_TEMPERATURE={best_tg:.2f}  "
          f"DIFFUSION_MODEL_TEMPERATURE={best_td:.2f}  F1={best_f1:.3f}")
    print("\nAdd these to backend/.env:\n"
          f"  GENERAL_MODEL_TEMPERATURE={best_tg:.2f}\n"
          f"  DIFFUSION_MODEL_TEMPERATURE={best_td:.2f}")


if __name__ == "__main__":
    main()
