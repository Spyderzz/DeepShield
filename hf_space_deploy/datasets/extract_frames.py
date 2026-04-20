"""Convert FFPP / DFDC videos -> 16 sampled frames at 224x224 RGB.

Usage:
    python -m backend.training.datasets.extract_frames \
        --input ./ffpp_data/original_sequences/youtube/raw/videos \
        --output ./ffpp_data/frames/real \
        --label real --frames 16 --size 224
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm


def sample_frame_indices(total: int, n: int) -> list[int]:
    if total <= 0:
        return []
    if total <= n:
        return list(range(total))
    step = total / float(n)
    return [min(total - 1, int(step * i + step / 2)) for i in range(n)]


def extract_from_video(path: Path, out_dir: Path, n: int, size: int) -> int:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return 0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = set(sample_frame_indices(total, n))
    out_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if i in indices:
            frame = cv2.resize(frame, (size, size), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(out_dir / f"{path.stem}_f{i:06d}.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved += 1
        i += 1
    cap.release()
    return saved


def main() -> None:
    ap = argparse.ArgumentParser(description="Sample N frames per video and resize.")
    ap.add_argument("--input", required=True, type=Path, help="Directory of .mp4 videos (recursive).")
    ap.add_argument("--output", required=True, type=Path, help="Directory to write .jpg frames.")
    ap.add_argument("--label", required=True, choices=["real", "fake"], help="Label tag for manifest.")
    ap.add_argument("--frames", type=int, default=16)
    ap.add_argument("--size", type=int, default=224)
    ap.add_argument("--manifest", type=Path, default=None, help="Optional CSV manifest append path.")
    args = ap.parse_args()

    videos = [p for p in args.input.rglob("*.mp4")]
    if not videos:
        print(f"No .mp4 found under {args.input}")
        return

    rows: list[tuple[str, str, str]] = []
    total_frames = 0
    for vid in tqdm(videos, desc=f"extract[{args.label}]"):
        rel_out = args.output / vid.stem
        saved = extract_from_video(vid, rel_out, args.frames, args.size)
        total_frames += saved
        if args.manifest is not None:
            for jpg in rel_out.glob("*.jpg"):
                rows.append((str(jpg), args.label, vid.stem))

    if args.manifest is not None and rows:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        new_file = not args.manifest.exists()
        with args.manifest.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["path", "label", "source_video"])
            w.writerows(rows)

    print(f"Done. Videos: {len(videos)}, frames written: {total_frames}")


if __name__ == "__main__":
    main()
