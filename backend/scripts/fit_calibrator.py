"""Isotonic calibration for EfficientNetAutoAttB4 — §7.6 of MERGE_PLAN.

Fits sklearn.isotonic.IsotonicRegression on EfficientNetAutoAttB4's raw sigmoid
outputs and persists the result to backend/models/efficientnet_calibrator.pkl.

Usage:
    .venv/Scripts/python.exe scripts/fit_calibrator.py --real PATH --fake PATH [--val-split 0.2]

Directory layout expected:
    --real path/to/real/faces/      (JPEG/PNG face images, labelled 0)
    --fake path/to/fake/faces/      (JPEG/PNG deepfake images, labelled 1)

FFPP c40 example (from Phase 11.1 Colab download):
    --real training/datasets/ffpp/c40/real/
    --fake training/datasets/ffpp/c40/fake/

The script:
  1. Runs EfficientNet inference on all images (face detection → sigmoid score).
  2. Splits into train/val (stratified, default 80/20).
  3. Fits IsotonicRegression(out_of_bounds='clip') on training split.
  4. Evaluates on val split: accuracy, real→fake FPR, fake→real FNR.
  5. Saves calibrator to backend/models/efficientnet_calibrator.pkl.

Run time: ~5 min on a 50-200 image set on CPU.
"""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
CALIBRATOR_OUT = Path(__file__).resolve().parent.parent / "models" / "efficientnet_calibrator.pkl"


def collect_images(directory: Path) -> list[Path]:
    return sorted(p for p in directory.rglob("*") if p.suffix.lower() in IMAGE_EXTS)


def score_images(det, paths: list[Path]) -> list[float]:
    """Run EfficientNet on each image; return raw sigmoid scores (-1 sentinel for no-face)."""
    from PIL import Image
    scores = []
    for i, p in enumerate(paths):
        try:
            pil = Image.open(p).convert("RGB")
        except Exception as e:
            logger.warning(f"Cannot open {p}: {e}")
            scores.append(-1.0)
            continue
        import numpy as np_inner
        img_np = np_inner.array(pil)
        frame_data = det.face_extractor.process_image(img=img_np)
        faces = frame_data.get("faces", [])
        if not faces:
            scores.append(-1.0)
        else:
            face_t = det._face_tensor(faces[0])
            import torch
            logit = det.raw_logit(face_t)
            from scipy.special import expit
            scores.append(float(expit(logit)))
        if (i + 1) % 10 == 0:
            print(f"  scored {i + 1}/{len(paths)}", end="\r")
    print()
    return scores


def main() -> int:
    parser = argparse.ArgumentParser(description="Fit isotonic calibrator for EfficientNetAutoAttB4")
    parser.add_argument("--real", required=True, type=Path, help="Directory of real face images (label=0)")
    parser.add_argument("--fake", required=True, type=Path, help="Directory of deepfake images (label=1)")
    parser.add_argument("--val-split", type=float, default=0.2, help="Fraction held out for validation (default 0.2)")
    parser.add_argument("--out", type=Path, default=CALIBRATOR_OUT, help="Output pkl path")
    args = parser.parse_args()

    if not args.real.is_dir():
        print(f"ERROR: --real must be a directory: {args.real}")
        return 1
    if not args.fake.is_dir():
        print(f"ERROR: --fake must be a directory: {args.fake}")
        return 1

    real_paths = collect_images(args.real)
    fake_paths = collect_images(args.fake)
    if not real_paths:
        print(f"ERROR: No images found in {args.real}")
        return 1
    if not fake_paths:
        print(f"ERROR: No images found in {args.fake}")
        return 1
    print(f"Found {len(real_paths)} real | {len(fake_paths)} fake images")

    print("Loading EfficientNetDetector (weights cached after first run)…")
    from services.efficientnet_service import EfficientNetDetector
    # Load without applying existing calibrator — we are building a new one.
    det = EfficientNetDetector(calibrator_path=Path("/dev/null"))

    print("Scoring real images…")
    real_scores = score_images(det, real_paths)
    print("Scoring fake images…")
    fake_scores = score_images(det, fake_paths)

    # Build arrays, drop no-face sentinels.
    r_scores = np.array([s for s in real_scores if s >= 0])
    f_scores = np.array([s for s in fake_scores if s >= 0])
    r_labels = np.zeros(len(r_scores))
    f_labels = np.ones(len(f_scores))

    X = np.concatenate([r_scores, f_scores])
    y = np.concatenate([r_labels, f_labels])
    print(f"\nUsable samples: {len(r_scores)} real | {len(f_scores)} fake")
    print(f"No-face dropped: {sum(s < 0 for s in real_scores)} real | {sum(s < 0 for s in fake_scores)} fake")

    if len(X) < 10:
        print("ERROR: Too few usable samples (<10) to fit a calibrator.")
        return 1

    # Stratified train/val split.
    from sklearn.model_selection import train_test_split
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=args.val_split, stratify=y, random_state=42
    )
    print(f"Split: {len(X_tr)} train | {len(X_val)} val")

    print("Fitting IsotonicRegression…")
    from sklearn.isotonic import IsotonicRegression
    cal = IsotonicRegression(out_of_bounds="clip")
    cal.fit(X_tr.reshape(-1, 1), y_tr)

    # Evaluate on val set.
    y_pred_raw = (X_val >= 0.5).astype(int)
    y_pred_cal = (cal.predict(X_val.reshape(-1, 1)) >= 0.5).astype(int)

    def metrics(y_true, y_pred, tag):
        acc = (y_true == y_pred).mean() * 100
        real_mask = y_true == 0
        fpr = (y_pred[real_mask] == 1).mean() * 100 if real_mask.sum() > 0 else 0.0
        fake_mask = y_true == 1
        fnr = (y_pred[fake_mask] == 0).mean() * 100 if fake_mask.sum() > 0 else 0.0
        print(f"  [{tag}]  acc={acc:.1f}%  real→fake FPR={fpr:.1f}%  fake→real FNR={fnr:.1f}%")
        return acc, fpr

    print("\nValidation metrics:")
    acc_raw, fpr_raw = metrics(y_val, y_pred_raw, "raw     ")
    acc_cal, fpr_cal = metrics(y_val, y_pred_cal, "calibrated")

    # Gate G3: ≥88% accuracy, ≤8% FPR.
    g3_pass = acc_cal >= 88.0 and fpr_cal <= 8.0
    print(f"\n  Gate G3: {'PASS ✓' if g3_pass else 'FAIL ✗'} (need acc≥88%, FPR≤8%)")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("wb") as f:
        pickle.dump(cal, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"\nCalibrator saved → {args.out}")
    print("Restart the backend server for the calibrator to take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
