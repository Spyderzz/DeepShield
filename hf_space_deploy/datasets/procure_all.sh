#!/usr/bin/env bash
# Phase 11.1 orchestrator: download + frame-extract + manifest.
# Total disk target: ~120k labeled images. Expect 60-80GB intermediate, ~30GB frames.

set -euo pipefail

ROOT="${ROOT:-./data}"
FFPP="${FFPP:-./ffpp_data}"
mkdir -p "$ROOT/real" "$ROOT/fake" "$FFPP"

# 1. FaceForensics++ (raw, videos) -- requires TOS keypress
python backend/scripts/download_ffpp.py "$FFPP" -d all -c raw -t videos

# 2. Frame extraction: real (original youtube)
python -m backend.training.datasets.extract_frames \
    --input  "$FFPP/original_sequences/youtube/raw/videos" \
    --output "$ROOT/real/ffpp_youtube" --label real --frames 16 --size 224

# 3. Frame extraction: fakes (each manipulation family)
for fam in Deepfakes Face2Face FaceSwap NeuralTextures FaceShifter; do
    python -m backend.training.datasets.extract_frames \
        --input  "$FFPP/manipulated_sequences/$fam/raw/videos" \
        --output "$ROOT/fake/ffpp_${fam,,}" --label fake --frames 16 --size 224
done

# 4. FFHQ thumbnails (real)
python -m backend.training.datasets.download_ffhq --output "$ROOT/real/ffhq" -n 10000

# 6. DFDC preview sample (fake+real) -- needs Kaggle creds
python -m backend.training.datasets.download_dfdc_sample --output "$ROOT/_dfdc_raw"
# NOTE: unzip + sort into $ROOT/fake/dfdc  and  $ROOT/real/dfdc  per DFDC metadata.json

# 7. Build manifest
python -m backend.training.datasets.build_manifest \
    --data "$ROOT" --out "$ROOT/manifest.csv" --seed 42

echo "Phase 11.1 complete. See $ROOT/manifest.csv"
