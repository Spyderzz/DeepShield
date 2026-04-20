"""Download a sample of the DFDC (Deepfake Detection Challenge) Preview dataset.

The full DFDC is ~470GB; the *preview* release (~5GB, Kaggle) is enough for
diversity augmentation alongside FFPP.

Requires the Kaggle CLI (`pip install kaggle`) and ~/.kaggle/kaggle.json.

Usage:
    python -m backend.training.datasets.download_dfdc_sample --output ./data/dfdc_preview
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument(
        "--competition",
        default="deepfake-detection-challenge",
        help="Kaggle competition slug (default: deepfake-detection-challenge preview).",
    )
    args = ap.parse_args()

    kaggle = shutil.which("kaggle")
    if kaggle is None:
        print("Kaggle CLI not found. Install with: pip install kaggle", file=sys.stderr)
        print("Then place kaggle.json in ~/.kaggle/ (chmod 600).", file=sys.stderr)
        sys.exit(2)

    args.output.mkdir(parents=True, exist_ok=True)
    cmd = [kaggle, "competitions", "download", "-c", args.competition, "-p", str(args.output)]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Downloaded to {args.output}. Unzip with: unzip *.zip")


if __name__ == "__main__":
    main()
