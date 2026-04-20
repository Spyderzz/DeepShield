"""Download the FFHQ 128x128 thumbnail subset from the official Google Drive mirror.

Pulls up to N images (default 10k) into the `real` bucket of the training set.
Falls back to the NVlabs 'ffhq-dataset' helper if available; otherwise expects
user to run the manual download once.

Usage:
    python -m backend.training.datasets.download_ffhq --output ./data/real/ffhq -n 10000
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def try_nvlabs_helper(output: Path, num: int) -> bool:
    """Prefer the official ffhq-dataset downloader if installed."""
    helper = shutil.which("ffhq-dataset")
    if helper is None:
        return False
    cmd = [helper, "--json", "ffhq-dataset-v2.json", "--thumbs", "--num_threads", "4"]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=output, check=False)
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("-n", "--num", type=int, default=10000)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if try_nvlabs_helper(args.output, args.num):
        return

    print("[!] `ffhq-dataset` helper not installed.")
    print("    Install via: pip install ffhq-dataset  (requires gdown)")
    print("    Or download thumbnails128x128.zip manually from:")
    print("      https://github.com/NVlabs/ffhq-dataset")
    print(f"    Extract into: {args.output}")
    sys.exit(1)


if __name__ == "__main__":
    main()
