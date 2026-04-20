# Phase 11.1 orchestrator for Windows (PowerShell)
$ErrorActionPreference = "Stop"

$ROOT = if ($env:ROOT) { $env:ROOT } else { ".\data" }
$FFPP = if ($env:FFPP) { $env:FFPP } else { ".\ffpp_data" }

New-Item -ItemType Directory -Force -Path "$ROOT\real" | Out-Null
New-Item -ItemType Directory -Force -Path "$ROOT\fake" | Out-Null
New-Item -ItemType Directory -Force -Path $FFPP | Out-Null

Write-Host "1. FaceForensics++ (highly compressed c40, 10 videos only) -- requires TOS keypress"
python backend\scripts\download_ffpp.py $FFPP -d all -c c40 -t videos -n 10

Write-Host "2. Frame extraction: real (original youtube)"
python -m backend.training.datasets.extract_frames `
    --input "$FFPP\original_sequences\youtube\c40\videos" `
    --output "$ROOT\real\ffpp_youtube" --label real --frames 4 --size 224

Write-Host "3. Frame extraction: fakes (each manipulation family)"
$Families = @("Deepfakes", "Face2Face", "FaceSwap", "NeuralTextures", "FaceShifter")
foreach ($fam in $Families) {
    $famLower = $fam.ToLower()
    python -m backend.training.datasets.extract_frames `
        --input "$FFPP\manipulated_sequences\$fam\c40\videos" `
        --output "$ROOT\fake\ffpp_$famLower" --label fake --frames 4 --size 224
}

Write-Host "4. FFHQ thumbnails (real - limited to 100 items)"
python -m backend.training.datasets.download_ffhq --output "$ROOT\real\ffhq" -n 100


Write-Host "6. DFDC preview sample (fake+real)"
python -m backend.training.datasets.download_dfdc_sample --output "$ROOT\_dfdc_raw"
Write-Host "NOTE: You will need to manually unzip + sort DFDC into $ROOT\fake\dfdc and $ROOT\real\dfdc"

Write-Host "7. Build manifest"
python -m backend.training.datasets.build_manifest `
    --data $ROOT --out "$ROOT\manifest.csv" --seed 42

Write-Host "Phase 11.1 complete. See $ROOT\manifest.csv"
