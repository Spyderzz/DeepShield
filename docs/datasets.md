# DeepShield — Training Datasets (Phase 11.1)

> **Scope:** Dataset procurement for the ConvNeXt-tiny image detector that replaces `prithivMLmods/Deep-Fake-Detector-v2-Model`.
> **Target:** ~120k labeled 224×224 RGB frames, roughly balanced real/fake.
> **Acceptance gate (Phase 11.2):** ≥92% accuracy on held-out FFPP test.

---

## 1. Buckets

| Bucket | Label | Source | Role | Count target |
|---|---|---|---|---|
| FFPP — `original_sequences/youtube` | real | FaceForensics++ raw videos → 16 frames/video | Primary real | ~16k |
| FFPP — `Deepfakes` / `Face2Face` / `FaceSwap` / `NeuralTextures` / `FaceShifter` | fake | FFPP raw manipulated videos → 16 frames/video | Primary fake | ~80k |
| FFHQ thumbnails (128×128 upsampled) | real | NVlabs FFHQ | Diversity: real unmanipulated faces | ~10k |

| DFDC preview | real + fake | Kaggle `deepfake-detection-challenge` | Out-of-distribution diversity | ~10–15k |

Totals roughly 118–125k images, stratified 70/15/15 train/val/test per `(label, source)` pair so every bucket is represented in val and test.

---

## 2. Scripts

All live under [backend/training/datasets/](../backend/training/datasets/):

| Script | Purpose |
|---|---|
| [download_ffpp.py](../backend/scripts/download_ffpp.py) | Official FFPP downloader (TOS gated). |
| [extract_frames.py](../backend/training/datasets/extract_frames.py) | Sample N frames per video at 224×224 JPEG q=95. |
| [download_ffhq.py](../backend/training/datasets/download_ffhq.py) | FFHQ thumbnail subset via NVlabs helper. |

| [download_dfdc_sample.py](../backend/training/datasets/download_dfdc_sample.py) | Kaggle-CLI wrapper for DFDC preview. |
| [build_manifest.py](../backend/training/datasets/build_manifest.py) | Unified CSV manifest with stratified 70/15/15 split. |
| [procure_all.sh](../backend/training/datasets/procure_all.sh) | End-to-end orchestrator for all of the above. |

---

## 3. One-shot procurement

```bash
# (~/.kaggle/kaggle.json must exist for DFDC)
bash backend/training/datasets/procure_all.sh
```

Output: `./data/manifest.csv` with columns `path, label, source, split`.

---

## 4. Why this mix

- **FFPP** is the academic gold standard but visually narrow (YouTube faces only) — a model trained solely on FFPP overfits to the YouTube distribution and false-positives on phone photos.
- **FFHQ** contributes high-resolution real faces outside the YouTube domain.
- **DFDC preview** contributes the generator diversity FFPP lacks (different face-swap codebases, compression artifacts).

---

## 5. License & EULA notes

- **FaceForensics++**: research-only EULA; the `download_ffpp.py` script asks for TOS acknowledgement on stdin. Do not redistribute the raw videos.
- **FFHQ**: CC-BY-NC-SA-4.0; derived frames carry the same license.
- **DFDC preview**: Facebook/Kaggle research terms; login-gated.

Redistribution of the built manifest is fine as long as it contains **paths** only — no pixel data.

---

## 6. Provenance audit

`build_manifest.py` records `source` per row, so Phase 11.2's `eval.py` can produce per-source AUC (surfaces any single-bucket collapse) and `calibrate.py` can stratify the isotonic fit.
