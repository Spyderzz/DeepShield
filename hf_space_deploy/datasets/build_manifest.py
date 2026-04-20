"""Build a unified train/val/test manifest (70/15/15) across all dataset buckets.

Expected input layout (produced by the other scripts in this package):

    data_root/
      real/
        ffpp_youtube/*.jpg          # frames from FFPP original_sequences
        ffhq/*.jpg                  # FFHQ thumbnails

      fake/
        ffpp_deepfakes/*.jpg
        ffpp_face2face/*.jpg
        ffpp_faceswap/*.jpg
        ffpp_neuraltextures/*.jpg
        ffpp_faceshifter/*.jpg
        dfdc/*.jpg

The manifest is stratified by (label, source) so FFHQ stays represented
in val/test.

Usage:
    python -m backend.training.datasets.build_manifest \
        --data ./data --out ./data/manifest.csv --seed 42
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png"}


def collect(data_root: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for label in ("real", "fake"):
        label_root = data_root / label
        if not label_root.exists():
            continue
        for source_dir in sorted(p for p in label_root.iterdir() if p.is_dir()):
            for img in source_dir.rglob("*"):
                if img.suffix.lower() in IMG_EXTS and img.is_file():
                    rows.append((str(img.resolve()), label, source_dir.name))
    return rows


def split(rows: list[tuple[str, str, str]], seed: int) -> dict[str, list[tuple[str, str, str]]]:
    buckets: dict[tuple[str, str], list[tuple[str, str, str]]] = defaultdict(list)
    for r in rows:
        buckets[(r[1], r[2])].append(r)

    rng = random.Random(seed)
    out = {"train": [], "val": [], "test": []}
    for key, items in buckets.items():
        rng.shuffle(items)
        n = len(items)
        n_train = int(0.70 * n)
        n_val = int(0.15 * n)
        out["train"].extend(items[:n_train])
        out["val"].extend(items[n_train : n_train + n_val])
        out["test"].extend(items[n_train + n_val :])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rows = collect(args.data)
    if not rows:
        raise SystemExit(f"No images found under {args.data}")

    splits = split(rows, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "source", "split"])
        for name, items in splits.items():
            for path, label, source in items:
                w.writerow([path, label, source, name])

    summary = {k: len(v) for k, v in splits.items()}
    print(f"Manifest: {args.out}")
    print(f"Totals: {summary} (overall {sum(summary.values())})")


if __name__ == "__main__":
    main()
