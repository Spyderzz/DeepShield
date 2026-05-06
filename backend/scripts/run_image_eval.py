#!/usr/bin/env python3
"""Phase C3/C4 — Image detection eval harness.

Reads MANIFEST.csv, runs classify_image on each fixture present on disk,
and prints a per-family confusion matrix, F1 scores, and per-component
breakdowns so ensemble weights can be tuned.

Usage (from backend/):
    .venv/Scripts/python.exe scripts/run_image_eval.py
    .venv/Scripts/python.exe scripts/run_image_eval.py --manifest tests/eval/MANIFEST.csv
    .venv/Scripts/python.exe scripts/run_image_eval.py --threshold 0.5 --verbose

The script does NOT download images. Populate tests/eval/images/ with the
fixtures listed in MANIFEST.csv before running.

Exit code:
    0 — all per-family accuracy ≥ 70 % and overall accuracy ≥ 75 %
    1 — accuracy thresholds not met (use for CI gating after C4 calibration)
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

# Add backend/ to path so imports resolve when run from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MANIFEST_DEFAULT = Path(__file__).resolve().parent.parent / "tests" / "eval" / "MANIFEST.csv"
IMAGES_DEFAULT = Path(__file__).resolve().parent.parent / "tests" / "eval" / "images"

FAMILIES = ["camera-real", "face-swap", "gan-portrait", "diffusion-portrait", "diffusion-noface"]


def _load_manifest(manifest_path: Path, images_root: Path) -> list[dict]:
    rows = []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            img_path = images_root / Path(row["path"]).name
            rows.append({
                "path": img_path,
                "label": row["label"],
                "family": row["family"],
                "source": row["source"],
                "notes": row.get("notes", ""),
            })
    return rows


def _safe_f1(tp: int, fp: int, fn: int) -> float:
    denom = 2 * tp + fp + fn
    return (2 * tp / denom) if denom > 0 else 0.0


def _run_eval(args) -> int:
    manifest_path = Path(args.manifest)
    images_root = Path(args.images_root)
    threshold = float(args.threshold)

    if not manifest_path.exists():
        print(f"[ERROR] Manifest not found: {manifest_path}")
        return 1

    rows = _load_manifest(manifest_path, images_root)
    present = [r for r in rows if r["path"].exists()]
    missing = [r for r in rows if not r["path"].exists()]

    if not present:
        print(f"[WARN] No eval images found in {images_root}. Populate the directory first.")
        print(f"       Expected paths from MANIFEST.csv:")
        for r in rows[:5]:
            print(f"         {r['path']}")
        return 0

    print(f"\nEval set: {len(present)} images found / {len(rows)} in manifest "
          f"({len(missing)} missing — skipped)")
    if missing and args.verbose:
        for r in missing:
            print(f"  [MISSING] {r['path'].name}")

    # Load models (lazy — only loads what's needed)
    print("\nLoading models...")
    from services.image_service import classify_image
    from services.exif_service import extract_exif
    from utils.scoring import compute_authenticity_score, get_verdict_label
    from PIL import Image

    results = []
    for i, row in enumerate(present):
        try:
            pil = Image.open(row["path"]).convert("RGB")
            raw = row["path"].read_bytes()
            exif_summary = None
            try:
                exif_summary = extract_exif(pil, raw)
            except Exception:
                pass
            clf = classify_image(pil, exif=exif_summary)
            score = compute_authenticity_score(clf.confidence, clf.label)
            predicted_fake = clf.confidence >= threshold
            actual_fake = row["label"] == "fake"
            correct = predicted_fake == actual_fake
            results.append({
                **row,
                "fake_prob": clf.confidence,
                "score": score,
                "method": clf.ensemble_method or "",
                "predicted_fake": predicted_fake,
                "actual_fake": actual_fake,
                "correct": correct,
                "gating": clf.gating_applied or "",
                "components": (clf.evidence_fusion or {}).get("components", {}),
            })
            if args.verbose:
                mark = "✓" if correct else "✗"
                print(f"  [{mark}] {row['path'].name:<35} "
                      f"label={row['label']:<4} "
                      f"prob={clf.confidence:.3f} score={score:3d} "
                      f"family={row['family']}")
        except Exception as e:
            print(f"  [ERR] {row['path'].name}: {e}")

    if not results:
        print("[WARN] No images could be scored.")
        return 0

    print("\n" + "=" * 65)
    print("OVERALL RESULTS")
    print("=" * 65)
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    overall_acc = correct / total * 100

    tp = sum(1 for r in results if r["predicted_fake"] and r["actual_fake"])
    fp = sum(1 for r in results if r["predicted_fake"] and not r["actual_fake"])
    fn = sum(1 for r in results if not r["predicted_fake"] and r["actual_fake"])
    tn = sum(1 for r in results if not r["predicted_fake"] and not r["actual_fake"])
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = _safe_f1(tp, fp, fn)
    fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0.0

    print(f"  Accuracy : {overall_acc:.1f}%  ({correct}/{total})")
    print(f"  Precision: {precision:.3f}")
    print(f"  Recall   : {recall:.3f}")
    print(f"  F1       : {f1:.3f}")
    print(f"  FPR (real→fake): {fpr:.1f}%")

    print("\n" + "-" * 65)
    print("PER-FAMILY RESULTS")
    print("-" * 65)
    family_pass = True
    for family in FAMILIES:
        family_rows = [r for r in results if r["family"] == family]
        if not family_rows:
            continue
        f_correct = sum(1 for r in family_rows if r["correct"])
        f_acc = f_correct / len(family_rows) * 100
        avg_prob = sum(r["fake_prob"] for r in family_rows) / len(family_rows)
        status = "PASS" if f_acc >= 70 else "FAIL"
        if f_acc < 70:
            family_pass = False
        print(f"  {family:<22} acc={f_acc:5.1f}%  avg_fake_prob={avg_prob:.3f}  "
              f"n={len(family_rows):3d}  [{status}]")

    print("\n" + "-" * 65)
    print("COMPONENT SIGNAL BREAKDOWN (mean fake_prob per signal per family)")
    print("-" * 65)
    signal_keys = ["face_stack", "general", "forensics", "exif"]
    header = f"  {'family':<22}" + "".join(f"  {k:<12}" for k in signal_keys)
    print(header)
    for family in FAMILIES:
        family_rows = [r for r in results if r["family"] == family]
        if not family_rows:
            continue
        row_str = f"  {family:<22}"
        for key in signal_keys:
            vals = [r["components"].get(key) for r in family_rows if key in r["components"]]
            mean = sum(vals) / len(vals) if vals else None
            row_str += f"  {mean:.3f}       " if mean is not None else f"  {'n/a':<12}"
        print(row_str)

    print("\n" + "-" * 65)
    print("GATING EVENTS")
    print("-" * 65)
    gated = [r for r in results if r["gating"]]
    print(f"  Total gated: {len(gated)}")
    for r in gated:
        print(f"    {r['path'].name:<35} label={r['label']}  {r['gating']}")

    all_pass = family_pass and overall_acc >= 75.0
    print("\n" + "=" * 65)
    if all_pass:
        print("RESULT: PASS — ready for production")
    else:
        print("RESULT: FAIL — review per-family accuracy and tune weights/thresholds")
        print("  Adjust GENERAL_AI_WEIGHT, DIFFUSION_AI_WEIGHT, FACE_STACK_WEIGHT_FACE,")
        print("  GENERAL_WEIGHT_FACE in .env or config.py, then re-run.")
    print("=" * 65 + "\n")
    return 0 if all_pass else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepShield image detection eval harness")
    parser.add_argument("--manifest", default=str(MANIFEST_DEFAULT),
                        help="Path to MANIFEST.csv")
    parser.add_argument("--images-root", default=str(IMAGES_DEFAULT),
                        help="Directory containing eval images")
    parser.add_argument("--threshold", default=0.5, type=float,
                        help="Fake probability threshold (default: 0.5)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print per-image results")
    args = parser.parse_args()
    sys.exit(_run_eval(args))


if __name__ == "__main__":
    main()
