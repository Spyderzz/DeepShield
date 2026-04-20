# DeepShield — MERGE PLAN: Integrating DeepShield1 into DeepShield

> **Date:** 2026-04-20 · **Last updated:** 2026-04-21
> **Owner:** Spyderzz
> **Source repo:** [DeepShield1](https://github.com/Spyderzz/DeepShield1)
> **Target repo:** `minor2/` (DeepShield — FastAPI + React)
> **Constraint:** No local large-model training — reuse DeepShield1 pretrained weights directly.
> **Environment:** Windows 11, no WSL, no local GPU, ~50GB free disk.

> **Implementation status (2026-04-21):** P0 + P1 + P2 complete. P3 script written, not yet run. G1/G2/G8 gates passed. G3/G4/G5/G6/G7 pending data or manual verification. See §8 Execution Priority and §9.1 Gates for per-item status.

---

## 0. Reconciliation with BUILD_PLAN2 Phase 11

This merge **supersedes [BUILD_PLAN2 §2 Phase 11 — Image Model Replacement](BUILD_PLAN2.md)**. Rationale:

- Phase 11 planned a local ConvNeXt / Swin fine-tune on FF++ + DFDC. That requires training compute the environment does not have (no local GPU, Colab was only reached for dataset prep).
- EfficientNetAutoAttB4 (DFDC-trained, ICPR 2020 paper-validated) is a **drop-in, training-free** replacement that hits the same accuracy target Phase 11 aimed for (~92% on FF++ test).
- Phase 11.1 dataset procurement work (FFPP c40) is **not wasted** — it becomes the regression/benchmark set for Phase 11.4 (smoke test) and for the isotonic calibrator in §7.6 below.

**Action:** Mark [BUILD_PLAN2.md](BUILD_PLAN2.md) Phase 11.2 / 11.3 as `Superseded by MERGE_PLAN` once §4 Step 4 of this doc completes. Retain 11.4 (regression harness) and add a new 11.5 "Calibrator fit on EfficientNet logits" (see §7.6).

---

## 1. Feature Mapping

### 1.1 Your System (DeepShield)

| # | Feature | Status |
|---|---------|--------|
| 1 | Image deepfake detection (ViT `prithivMLmods/Deep-Fake-Detector-v2-Model`) | ✅ Done |
| 2 | Video deepfake detection (per-frame ViT + face gating via MediaPipe) | ✅ Done |
| 3 | Text fake-news detection (BERT `jy46604790/Fake-News-Bert-Detect`) | ✅ Done |
| 4 | Screenshot OCR + credibility (EasyOCR + BERT reuse) | ✅ Done |
| 5 | Grad-CAM / Grad-CAM++ heatmaps | ✅ Done |
| 6 | ELA (Error Level Analysis) | ✅ Done |
| 7 | EXIF metadata extraction + trust scoring | ✅ Done |
| 8 | LLM explainability (Gemini/OpenAI) | ✅ Done |
| 9 | VLM detailed breakdown (6-component scores) | ✅ Done |
| 10 | Trusted source lookup (NewsData.io) | ✅ Done |
| 11 | Contradiction detection (fact-check routing) | ✅ Done |
| 12 | Sensationalism + manipulation indicator detection | ✅ Done |
| 13 | PDF report generation (xhtml2pdf + Jinja2) | ✅ Done |
| 14 | Auth (JWT + bcrypt) + history + per-user records | ✅ Done |
| 15 | Pipeline visualizer (animated stage stepper) | ✅ Done |
| 16 | Artifact detection (FFT, JPEG Q-table, FaceMesh jitter, luminance) | ✅ Done |
| 17 | NER keyword extraction (spaCy) | ✅ Done |
| 18 | Multi-lingual support (langdetect + Hindi OCR) | ✅ Done |

### 1.2 DeepShield1 (DeepTrace fork)

| # | Feature | Status |
|---|---------|--------|
| A | Video deepfake detection (EfficientNetAutoAttB4, DFDC-trained) | ✅ |
| B | Image deepfake detection (same EfficientNetAutoAttB4 via `/predict`) | ✅ |
| C | BlazeFace face extraction (dedicated face detector) | ✅ |
| D | ICPR2020-DFDC ensemble pipeline (`polimi-ispl/icpr2020dfdc`) | ✅ |
| E | Multiple model architectures (ConvLSTM, LRCN, SwinEfficient, VisionTransformer, EnsembleLearning) | ✅ Notebooks |
| F | Blockchain verification (Hardhat + NeoX smart contracts) | ✅ |
| G | Google OAuth (Passport.js + MongoDB sessions) | ✅ |
| H | ExifTool metadata embedding (write verdict into video metadata) | ✅ |
| I | Augmentation techniques notebook | ✅ |
| J | React frontend with TailwindCSS | ✅ |

### 1.3 Overlap Analysis

| Feature | Your System | DeepShield1 | Winner |
|---------|-------------|-------------|--------|
| Image detection model | ViT (HF, high false-positive) | EfficientNetAutoAttB4 (DFDC-trained, research-grade) | **DeepShield1** |
| Video detection model | Per-frame ViT (no temporal) | EfficientNetAutoAttB4 + BlazeFace (face-focused) | **DeepShield1** |
| Face detection | MediaPipe FaceMesh | BlazeFace | **Merge both** |
| Text analysis | Full pipeline (BERT + NER + sources) | None | **Your system** |
| Screenshot analysis | OCR + credibility + layout | None | **Your system** |
| Explainability | Grad-CAM++ / ELA / EXIF / LLM / VLM | None | **Your system** |
| Auth system | JWT + bcrypt (Python) | Google OAuth (Node.js) | **Your system** |
| Backend framework | FastAPI (Python, async) | Express.js + Flask (split) | **Your system** |
| Frontend | React + vanilla CSS + Framer Motion | React + TailwindCSS | **Your system** |
| PDF reports | xhtml2pdf + Jinja2 | None | **Your system** |
| Blockchain | None | Hardhat + NeoX | **Ignore** (not needed) |
| Metadata embedding | EXIF read-only | ExifTool write | **Nice-to-have from DS1** |

### 1.4 Missing in Your System (to adopt from DeepShield1)

1. **EfficientNetAutoAttB4 model** — research-grade, DFDC-trained, significantly better than current ViT
2. **BlazeFace face detector** — faster, purpose-built for face extraction vs MediaPipe
3. **ICPR2020 ensemble pipeline** — multiple model weight aggregation framework
4. **ExifTool metadata write** — embed verdict into analyzed files

### 1.5 Features to Preserve (your system is better)

- All 4 media pipelines (image/video/text/screenshot)
- Full explainability stack (Grad-CAM++, ELA, EXIF, LLM, VLM)
- FastAPI architecture (async, Pydantic, typed)
- Auth + history + PDF reports
- Trusted source verification
- Frontend component library

---

## 2. Architecture Comparison

### 2.1 Backend

| Aspect | Your System | DeepShield1 |
|--------|-------------|-------------|
| API framework | FastAPI (Python) | Express.js (Node) + Flask (Python ML) |
| ML runtime | In-process (same FastAPI server) | Separate Flask server on port 8080 |
| Database | SQLite via SQLAlchemy | MongoDB Atlas |
| Auth | JWT (stateless) | Passport.js + session cookies |
| File handling | Temp upload → process → delete | Save to disk, manual cleanup |

### 2.2 ML Pipeline

| Aspect | Your System | DeepShield1 |
|--------|-------------|-------------|
| Image model | `prithivMLmods/Deep-Fake-Detector-v2-Model` (ViT, HF) | `EfficientNetAutoAttB4` (DFDC weights, `torch.utils.model_zoo`) |
| Face detection | MediaPipe FaceMesh (468 landmarks) | BlazeFace (bounding-box, lightweight) |
| Preprocessing | HF `AutoImageProcessor` (224x224) | Custom `isplutils.get_transformer` (scale policy, 224x224) |
| Video processing | OpenCV uniform frame sampling (16 frames) | `VideoReader` class + `FaceExtractor` (100 frames) |
| Output | Softmax probabilities via HF pipeline | Raw logits → `scipy.special.expit` (sigmoid) |
| Model source | HuggingFace Hub auto-download | `torch.utils.model_zoo.load_url` (direct weight URL) |

### 2.3 Data Flow Comparison

**Your system:**
```
Upload → FastAPI → validate → PIL open → HF processor → ViT forward → softmax
       → Grad-CAM → artifact scan → compose result → DB persist → JSON response
```

**DeepShield1:**
```
Upload → Flask → save temp → BlazeFace face extract → isplutils transform
       → EfficientNet forward → sigmoid(logits) → JSON {score, result}
```

### 2.4 API Structure

| Your System | DeepShield1 |
|-------------|-------------|
| `POST /api/v1/analyze/image` | `POST /predict` (Flask :8080) |
| `POST /api/v1/analyze/video` | `POST /upload-video` (Flask :8080) |
| `POST /api/v1/analyze/text` | — |
| `POST /api/v1/analyze/screenshot` | — |
| `POST /api/v1/report/{id}` | — |
| `POST /api/v1/auth/register` | `GET /auth/google` (Express :5000) |
| `GET /api/v1/history` | — |

---

## 3. Model Integration Strategy

### 3.1 Models Available in DeepShield1

| Model | Architecture | Training Data | Weights Source | Size |
|-------|-------------|---------------|----------------|------|
| **EfficientNetAutoAttB4** | EfficientNet-B4 + Auto-Attention | DFDC | `weights.weight_url['EfficientNetAutoAttB4_DFDC']` | ~75MB |
| **EfficientNetB4** | EfficientNet-B4 | DFDC/FFPP | Same weight registry | ~70MB |
| **EfficientNetB4ST** | EfficientNet-B4 (style transfer) | DFDC/FFPP | Same weight registry | ~70MB |
| **Xception** | Xception | DFDC/FFPP | Same weight registry | ~80MB |
| **BlazeFace** | Lightweight face detector | — | `blazeface.pth` + `anchors.npy` | ~500KB |

### 3.2 How Each Model Works

**EfficientNetAutoAttB4 (primary target for integration):**
- Input: 224x224 face crop (RGB), normalized via model-specific normalizer
- BlazeFace detects face bounding boxes → crop → scale to 224x224
- Forward pass outputs raw logits (single value)
- `sigmoid(logit)` → probability (>0.5 = FAKE, ≤0.5 = REAL)
- For video: extract N frames → extract faces → batch inference → `sigmoid(mean(logits))`

**BlazeFace:**
- Lightweight SSD-based face detector
- Requires `blazeface.pth` (weights) + `anchors.npy` (anchor boxes)
- Returns bounding boxes + confidence for each detected face
- Used as preprocessing step before the classifier

### 3.3 How to Reuse Without Retraining

1. **Clone the ICPR2020 repo** into `backend/models/icpr2020dfdc/`:
   ```bash
   cd backend/models
   git clone https://github.com/polimi-ispl/icpr2020dfdc
   ```

2. **Weights auto-download** — `torch.utils.model_zoo.load_url()` downloads from the URL defined in `architectures/weights.py`. No manual download needed. Cached in `~/.cache/torch/`.

3. **BlazeFace weights** — copy `blazeface.pth` and `anchors.npy` from the cloned repo's `blazeface/` directory.

4. **No retraining required** — these are fully pretrained on DFDC. Just load and run inference.

### 3.4 Steps to Plug Into Your System

**Step 1: Create adapter service** `backend/services/efficientnet_service.py`:

```python
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import torch
from loguru import logger
from PIL import Image
from scipy.special import expit
from torch.utils.model_zoo import load_url

# Resolve paths OS-agnostically (Windows-safe — use pathlib, not string concat).
ICPR_PATH = (Path(__file__).resolve().parent.parent / "models" / "icpr2020dfdc").resolve()
_NOTEBOOK_DIR = str(ICPR_PATH / "notebook")
if _NOTEBOOK_DIR not in sys.path:
    sys.path.insert(0, _NOTEBOOK_DIR)

# ICPR2020 imports are only valid after sys.path is patched above.
from blazeface import BlazeFace, FaceExtractor  # noqa: E402
from architectures import fornet, weights  # noqa: E402
from isplutils import utils as ispl_utils  # noqa: E402


class EfficientNetDetector:
    def __init__(
        self,
        model_name: str = "EfficientNetAutoAttB4",
        train_db: str = "DFDC",
        device: str = "cpu",
    ) -> None:
        self.device = torch.device(device)
        self.model_name = model_name
        self.train_db = train_db

        weight_key = f"{model_name}_{train_db}"
        if weight_key not in weights.weight_url:
            raise KeyError(f"Unknown model/DB combination: {weight_key}")
        model_url = weights.weight_url[weight_key]

        self.net = getattr(fornet, model_name)().eval().to(self.device)
        # check_hash=False — some weight files on the ISPL mirror have stale hashes; verify via size instead.
        state = load_url(model_url, map_location=self.device, check_hash=False)
        self.net.load_state_dict(state)

        self.transf = ispl_utils.get_transformer(
            "scale", 224, self.net.get_normalizer(), train=False
        )

        blazeface_dir = ICPR_PATH / "blazeface"
        weights_path = blazeface_dir / "blazeface.pth"
        anchors_path = blazeface_dir / "anchors.npy"
        if not weights_path.exists() or not anchors_path.exists():
            raise FileNotFoundError(
                f"BlazeFace assets missing. Expected {weights_path} and {anchors_path}. "
                "Clone icpr2020dfdc into backend/models/ and ensure the blazeface/ subdir is complete."
            )

        self.facedet = BlazeFace().to(self.device)
        self.facedet.load_weights(str(weights_path))
        self.facedet.load_anchors(str(anchors_path))
        self.face_extractor = FaceExtractor(facedet=self.facedet)
        logger.info(f"EfficientNetDetector ready: {model_name} / {train_db} on {self.device}")

    @staticmethod
    def _to_tensor(transformed: "np.ndarray | dict | torch.Tensor") -> torch.Tensor:
        # `get_transformer` returns an albumentations Compose in recent ICPR2020 revisions,
        # but older forks return torchvision transforms. Normalize both into a tensor.
        if isinstance(transformed, dict):
            return transformed["image"]
        if isinstance(transformed, torch.Tensor):
            return transformed
        raise TypeError(f"Unsupported transformer output type: {type(transformed)}")

    def detect_image(self, pil_image: Image.Image) -> dict:
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        img_array = np.array(pil_image)
        face_data = self.face_extractor.process_image(img=img_array)
        faces = face_data.get("faces", [])
        if not faces:
            return {"error": "no_face", "score": None, "result": None}

        face_t = self._to_tensor(self.transf(image=faces[0]))
        with torch.no_grad():
            logit = self.net(face_t.unsqueeze(0).to(self.device))
            score = float(torch.sigmoid(logit).item())
        return {
            "score": score,
            "result": "FAKE" if score > 0.5 else "REAL",
            "model": f"{self.model_name}_{self.train_db}",
            "error": None,
        }

    def detect_video_frames(self, frames: list[np.ndarray]) -> dict:
        face_tensors: list[torch.Tensor] = []
        for frame in frames:
            face_data = self.face_extractor.process_image(img=frame)
            faces = face_data.get("faces", [])
            if faces:
                face_tensors.append(self._to_tensor(self.transf(image=faces[0])))

        if not face_tensors:
            return {"error": "no_faces", "mean_score": None, "per_frame": []}

        batch = torch.stack(face_tensors).to(self.device)
        with torch.no_grad():
            logits = self.net(batch).cpu().numpy().flatten()
        per_frame = expit(logits).tolist()
        mean_score = float(expit(np.mean(logits)))
        return {
            "mean_score": mean_score,
            "per_frame": per_frame,
            "model": f"{self.model_name}_{self.train_db}",
            "error": None,
        }
```

**Notes on the adapter:**
- `check_hash=False` — the published weights on ISPL's mirror occasionally have stale sha256 hashes baked into the URL; verify integrity by logging the tensor count after load instead.
- `_to_tensor()` guards against both albumentations-dict and torchvision-tensor outputs since ICPR2020 forks diverge here.
- All paths use `pathlib.Path` — Windows-safe, no `sys.path.append('..')` leaks.
- The BlazeFace asset check fails loudly at construction instead of at first inference.

**Step 2: Wire into model_loader.py** — add `load_efficientnet()` method to singleton.

**Step 3: Update image_service.py** — call EfficientNet alongside ViT, use ensemble average or pick EfficientNet as primary.

### 3.5 Grad-CAM++ Compatibility Break (NEW — resolves a Phase 12 regression)

[Phase 12.1](BUILD_PLAN2.md) wired Grad-CAM++ to the ViT's last 3 transformer blocks. EfficientNetAutoAttB4 has a different architecture — Grad-CAM target layers must change, or heatmaps will break.

**Target layers for EfficientNet-B4 (AutoAttB4 wraps the same backbone):**

| Purpose | Layer path in `fornet.EfficientNetAutoAttB4` |
|---------|----------------------------------------------|
| Primary CAM target | `.efficientnet._blocks[-1]` (last MBConv block before head) |
| Attention heatmap (unique to AutoAttB4) | `.efficientnet._blocks[-1]` feature × `.attconv` output |
| Fallback | `.efficientnet._conv_head` |

**Action items:**
- Extend `services/gradcam_service.py` (currently ViT-only) with `model_family: Literal["vit", "efficientnet"]` dispatch.
- For `efficientnet`, use `pytorch-grad-cam` library's `GradCAMPlusPlus` with `target_layers=[model.efficientnet._blocks[-1]]`.
- AutoAttB4's built-in attention map is cheaper and more semantically grounded than Grad-CAM for this family — prefer it as primary, Grad-CAM as fallback.
- Return `heatmap_source: "attention" | "gradcam++" | "fallback"` in API response for UI to display correctly alongside the 3-state toggle from Phase 12.1.

---

## 4. Merge Strategy (Step-by-Step)

### Step 1: Clone ICPR2020 Dependency

```bash
cd backend/models
git clone https://github.com/polimi-ispl/icpr2020dfdc
```

- **Files needed:** `blazeface/`, `architectures/`, `isplutils/`, `notebook/` directories
- **Add to `.gitignore`:** `backend/models/icpr2020dfdc/` (large repo, reference only)

### Step 2: Install Additional Python Dependencies

Add to `backend/requirements.txt`:
```
albumentations>=1.3.0,<1.5       # ICPR2020 uses A.Compose; pin to avoid 1.5+ API break
pytorch-grad-cam>=1.5.0          # For EfficientNet heatmaps (see §3.5)
```
(`scipy`, `torch 2.4.1+cpu`, `numpy`, `Pillow` already present.)

**Do NOT add `efficientnet-pytorch`.** ICPR2020's `architectures/fornet.py` vendors its own EfficientNet implementation via `torch.hub`-loaded `facebookresearch/semi-supervised-ImageNet1K-models`. The standalone `efficientnet-pytorch` package (last released 2020) is abandoned and breaks against torch ≥ 2.0.

### Step 3: Create Adapter Service

- **New file:** `backend/services/efficientnet_service.py` (code in §3.4 above)
- **Pattern:** Adapter wrapping DeepShield1's inference logic into your service interface
- **No changes** to existing `image_service.py` or `video_service.py` yet

### Step 4: Update Model Loader

- **Modify:** `backend/models/model_loader.py`
- Add `_efficientnet_detector = None` and `load_efficientnet()` method
- Lazy initialization, same singleton pattern as existing models
- Add `EFFICIENTNET_MODEL` and `EFFICIENTNET_TRAIN_DB` to `config.py`

### Step 5: Create Ensemble Scoring in Image Pipeline

- **Modify:** `backend/services/image_service.py`
- Add `ENSEMBLE_MODE` env flag (default `true`)
- When ensemble enabled: run both ViT + EfficientNet, average scores
- When disabled: use EfficientNet only (better accuracy)
- Expose `models_used: list[str]` in API response

### Step 6: Upgrade Video Pipeline

- **Modify:** `backend/services/video_service.py`
- Replace per-frame ViT classification with EfficientNet's `detect_video_frames()`
- Keep MediaPipe face gating as fallback when BlazeFace finds no faces
- Use BlazeFace as primary face detector (faster, purpose-built)

### Step 7: Add ExifTool Write Capability (Optional)

- **New file:** `backend/services/metadata_writer.py`
- Wrap ExifTool CLI for writing verdict into analyzed file metadata
- Gate behind `EXIFTOOL_PATH` env var (skip if not installed)
- Call after analysis completes, before temp file cleanup

### Modules Summary

| Action | File | Source |
|--------|------|--------|
| **Copy** | `icpr2020dfdc/` repo | DeepShield1 dependency |
| **Create** | `services/efficientnet_service.py` | New adapter |
| **Create** | `services/metadata_writer.py` | Inspired by DS1 |
| **Modify** | `models/model_loader.py` | Add EfficientNet loader |
| **Modify** | `services/image_service.py` | Ensemble scoring |
| **Modify** | `services/video_service.py` | Replace ViT with EfficientNet |
| **Modify** | `config.py` | New env vars |
| **Modify** | `requirements.txt` | New deps |
| **Ignore** | `Backend/server.js` | Node.js, not needed |
| **Ignore** | `Smart Contracts/` | Blockchain, not needed |
| **Ignore** | `src/` (DS1 frontend) | Your frontend is superior |
| **Ignore** | `Backend/Models/user.js` | MongoDB schema, not needed |

---

## 5. Compatibility Adjustments

### 5.1 Dependency Alignment

```diff
# backend/requirements.txt additions
+ efficientnet-pytorch==0.7.1
+ albumentations>=1.3.0
# scipy already present
# torch already present
# numpy already present
# Pillow already present
```

### 5.2 Environment Setup

Add to `.env.example`:
```env
# EfficientNet Model (from DeepShield1)
EFFICIENTNET_MODEL=EfficientNetAutoAttB4
EFFICIENTNET_TRAIN_DB=DFDC
ENSEMBLE_MODE=true

# ExifTool (optional)
EXIFTOOL_PATH=
```

### 5.3 Model Loading Fixes

- DeepShield1 uses `sys.path.append('..')` — replace with explicit `pathlib.Path` injection in adapter (see §3.4).
- BlazeFace expects relative paths to `blazeface.pth` — use absolute paths via `Path(__file__).resolve()` chain.
- `torch.utils.model_zoo.load_url` caches to `~/.cache/torch/checkpoints/` (Windows: `%USERPROFILE%\.cache\torch\checkpoints\`). First run downloads ~75MB.
- **Windows-specific:** set `TORCH_HOME=D:\torch_cache` (or similar) if C: is tight — weights + HF cache + EasyOCR models already consume ~3–4GB on this machine.
- `check_hash=True` can fail against the ISPL weight mirror; use `check_hash=False` and log tensor shapes post-load as sanity check.

### 5.4 Path Corrections

| DeepShield1 Path | Your System Path |
|------------------|------------------|
| `models/icpr2020dfdc/notebook/` | `backend/models/icpr2020dfdc/notebook/` |
| `../blazeface/blazeface.pth` | `backend/models/icpr2020dfdc/blazeface/blazeface.pth` |
| `../blazeface/anchors.npy` | `backend/models/icpr2020dfdc/blazeface/anchors.npy` |

### 5.5 Config Translation

| DeepShield1 | Your System |
|-------------|-------------|
| `net_model = 'EfficientNetAutoAttB4'` | `settings.EFFICIENTNET_MODEL` |
| `train_db = 'DFDC'` | `settings.EFFICIENTNET_TRAIN_DB` |
| `device = torch.device('cpu')` | `settings.DEVICE` (already exists) |
| `face_size = 224` | Hardcoded in adapter (model-specific) |
| `frames_per_video = 100` | `settings.VIDEO_SAMPLE_FRAMES` (add) |

---

## 6. Risks and Conflict Points

### 6.1 Architectural Mismatches

| Risk | Severity | Mitigation |
|------|----------|------------|
| DeepShield1 uses Flask, you use FastAPI | Low | Adapter pattern — no Flask needed |
| ICPR2020 repo expects specific directory structure | Medium | Use `sys.path.insert` with absolute paths |
| BlazeFace vs MediaPipe face detection differences | Medium | Keep both — BlazeFace primary, MediaPipe fallback |

### 6.2 Naming Conflicts

| Conflict | Resolution |
|----------|------------|
| Both systems have `models/` directory | DS1 repo goes into `backend/models/icpr2020dfdc/` (subdirectory) |
| Both have `app.py` | DS1's `app.py` is not used — adapter replaces it |
| Both have `requirements.txt` | Merge deps into your existing file |

### 6.3 Runtime Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| EfficientNet + ViT both in memory (~150MB+ each) | High RAM | Lazy load; only load EfficientNet when `ENSEMBLE_MODE=true` |
| `torch.utils.model_zoo.load_url` first-run download | Startup delay | Document in SETUP_GUIDE; weights cache persists |
| BlazeFace weight files missing | Crash on load | Check file existence at startup, fallback to MediaPipe |
| ICPR2020 repo API changes | Breaking | Pin to specific commit hash |

### 6.4 Dependency Conflicts

| Package | Your Version | DS1 Needs | Resolution |
|---------|-------------|-----------|------------|
| `torch` | 2.4.1+cpu | Any recent | ✅ Compatible |
| `numpy` | Latest | Any | ✅ Compatible |
| `scipy` | Latest | For `expit` | ✅ Already installed |
| `albumentations` | Not installed | Required by ICPR2020 | Install `>=1.3.0,<1.5` |
| `pytorch-grad-cam` | Not installed | Required for EfficientNet heatmap | Install `>=1.5.0` |
| `efficientnet-pytorch` | — | NOT needed (vendored) | **Skip** (see §5.1) |

### 6.5 License & Commit Pinning (NEW — academic submission risk)

- **ICPR2020 repo license:** `CC BY-NC-SA 4.0` — research and non-commercial use only. For a university minor-project viva this is fine; for any future commercial fork, EfficientNetAutoAttB4 must be swapped for a permissively-licensed alternative (e.g., retrain on same data, or use `selimsef/dfdc_deepfake_challenge` MIT weights).
- **Pin the ICPR2020 commit.** As of 2026-04-20 the repo main branch is stable, but the notebook/ module has shifted imports twice in 2024. Add to README / setup:
  ```bash
  cd backend/models
  git clone https://github.com/polimi-ispl/icpr2020dfdc
  cd icpr2020dfdc
  git checkout a93233c   # 2024-02 known-good
  ```
- Document the pinned commit in `docs/MODEL_CARDS.md` alongside the weight SHA.

### 6.6 Memory Footprint (NEW — Windows/CPU reality check)

Running all current models + EfficientNetAutoAttB4 concurrently:

| Component | RAM (approx) |
|-----------|-------------:|
| ViT image model (HF) | 340 MB |
| EfficientNetAutoAttB4 | 280 MB |
| BlazeFace | 2 MB |
| BERT fake-news | 440 MB |
| EasyOCR (en + hi) | 650 MB |
| spaCy + sentence-transformers | 280 MB |
| MediaPipe FaceMesh | 40 MB |
| FastAPI baseline + request buffers | 200 MB |
| **Total steady state** | **~2.2 GB** |

Mitigations:
- Lazy-load EfficientNet only when `ENSEMBLE_MODE=true` OR primary-mode flag set.
- Consider `torch.inference_mode()` context over `torch.no_grad()` — fewer allocations on 2.4+.
- Add `/admin/unload-models` endpoint for development (idle GC).

---

## 7. Optimization Suggestions

### 7.1 Modularization

Create `backend/services/detectors/` package:
```
detectors/
├── __init__.py
├── base.py              # ABC: detect_image(), detect_video()
├── vit_detector.py      # Current ViT logic
├── efficientnet_detector.py  # New adapter
└── ensemble.py          # Weighted combination strategy
```

### 7.2 Inference Optimization

- **ONNX export:** Convert EfficientNetAutoAttB4 to ONNX for 2-3x CPU speedup
- **Quantization:** Apply `torch.quantization.quantize_dynamic` for CPU
- **Batch face processing:** For video, batch all face crops into single forward pass

### 7.3 GPU/CPU Fallback

```python
DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
```
Already in DS1's `image-app.py` — adopt this pattern in `config.py`.

### 7.4 Caching Strategy

- Hash uploaded file (SHA-256) before processing — already planned in Phase 19
- Cache EfficientNet results alongside ViT results per hash
- For ensemble: cache individual model scores, recompute ensemble on-the-fly

### 7.5 API Standardization

Add `models_used` field to all analysis responses:
```json
{
  "verdict": "Likely Fake",
  "score": 23,
  "models_used": ["EfficientNetAutoAttB4_DFDC", "ViT_Deep-Fake-Detector-v2"],
  "ensemble_method": "weighted_average"
}
```

### 7.6 Calibrator on EfficientNet Logits (carries over from Phase 11)

DFDC-trained models are notoriously over-confident on in-the-wild real photos (the camera-anchor false-positive issue that motivated Phase 11 in the first place is NOT automatically solved by swapping the backbone).

- Reuse Phase 11.1 downloaded FFPP c40 + the curated 50-image real-camera anchor set.
- Fit `sklearn.isotonic.IsotonicRegression` against EfficientNetAutoAttB4's raw sigmoid outputs on a held-out val split.
- Persist as `backend/models/efficientnet_calibrator.pkl`.
- Apply inside `EfficientNetDetector.detect_image()` before returning `score`.
- **This is a one-off CPU job (~5 min on the anchor set), not training — fits the "no local training" constraint.**

---

## 8. Final Recommended Hybrid Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 CLIENT (React + Vite SPA)                    │
│  Your existing frontend — NO changes from DeepShield1        │
└────────────────────────┬────────────────────────────────────┘
                         │ REST / JSON
┌────────────────────────┼────────────────────────────────────┐
│                 FastAPI Backend (your system)                 │
│                                                              │
│  ┌──────────────── Service Layer ─────────────────────────┐  │
│  │ image_service  ──→ EnsembleScorer                      │  │
│  │ video_service  ──→ EfficientNet + MediaPipe fallback   │  │
│  │ text_service   (unchanged)                             │  │
│  │ screenshot_service (unchanged)                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────── Detector Layer ────────────────────────┐  │
│  │ detectors/                                              │  │
│  │ ├── base.py         # ABC                               │  │
│  │ ├── vit_detector.py # Existing ViT (HuggingFace)       │  │
│  │ ├── efficientnet_detector.py # NEW from DeepShield1    │  │
│  │ └── ensemble.py     # Weighted avg / voting             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────── Explainability (unchanged) ────────────────────┐  │
│  │ Grad-CAM++ │ ELA │ EXIF │ LLM │ VLM │ Artifacts       │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────── Face Detection (merged) ───────────────────────┐  │
│  │ BlazeFace (primary) + MediaPipe (fallback)             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────── Data Layer (unchanged) ────────────────────────┐  │
│  │ SQLite │ Temp Files │ PDF Cache │ HF Model Cache       │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

External Dependencies (from DeepShield1):
  backend/models/icpr2020dfdc/   ← git clone (pinned commit)
    ├── blazeface/               ← Face detector weights
    ├── architectures/           ← EfficientNet model defs
    └── isplutils/               ← Preprocessing transforms
```

### Key Decisions

1. **EfficientNetAutoAttB4 becomes PRIMARY** — DFDC-trained, ICPR 2020 validated
2. **ViT kept as SECONDARY** — ensemble diversity, A/B comparison for viva
3. **BlazeFace replaces MediaPipe** for deepfake face detection (MediaPipe retained for artifact detection)
4. **Blockchain from DS1: IGNORED** — not relevant
5. **Node.js backend from DS1: IGNORED** — everything runs through FastAPI
6. **DS1 frontend: IGNORED** — your React frontend is far more complete

### Execution Priority

| Priority | Task | Effort |
|----------|------|--------|
| P0 | Clone ICPR2020 (pin commit `a93233c`) + install deps | 30 min |
| P0 | Create `efficientnet_service.py` adapter (§3.4) | 2 hours |
| P0 | Wire into `model_loader.py` (lazy singleton) | 1 hour |
| P0 | Smoke test: 5 real + 5 fake images, verify no crash, log scores | 30 min |
| P1 | Extend `gradcam_service.py` for EfficientNet (§3.5) | 2 hours |
| P1 | Update `image_service.py` with ensemble + `models_used` field | 2 hours |
| P1 | Update `video_service.py` with EfficientNet + BlazeFace | 2 hours |
| P1 | Fit isotonic calibrator (§7.6) on FFPP c40 val split | 1 hour |
| P2 | Regression harness on 50-image anchor set (§9 acceptance) | 1 hour |
| P2 | Add `metadata_writer.py` (ExifTool) | 1 hour |
| P2 | Update config + env + docs + MODEL_CARDS.md | 1 hour |
| P3 | ONNX export for production speed | 2 hours |

**Total estimated effort: ~16 hours of focused work.**

---

## 9. Acceptance Criteria & Rollback (NEW)

### 9.1 Go/No-Go Gates

Before declaring the merge complete, all of the following must be true:

| # | Gate | How to verify |
|---|------|---------------|
| G1 | EfficientNetAutoAttB4 loads on cold start without crash | `backend/scripts/test_efficientnet_load.py` — new smoke script |
| G2 | BlazeFace detects ≥1 face on 90% of the 50-image anchor set | Regression log output |
| G3 | On the 50-image anchor set: **≥ 88% accuracy, ≤ 8% real→fake FPR** (calibrator applied) | `pytest backend/tests/test_efficientnet_regression.py` |
| G4 | Grad-CAM / attention heatmap renders for EfficientNet path (no blank PNG) | Manual eye-check on 5 sample images |
| G5 | Video pipeline end-to-end: 30s test clip finishes in < 90s on CPU | Smoke run |
| G6 | Existing ViT-only path still works when `ENSEMBLE_MODE=false` and legacy flag set | Regression |
| G7 | PDF report renders with `models_used` field populated | Visual check |
| G8 | Memory footprint at steady state ≤ 2.5 GB under ensemble load | `psutil` log in smoke script |

### 9.2 Rollback Plan

If any of G3 / G4 / G5 fail, revert in this order — each step is independently reversible:

1. Flip `ENSEMBLE_MODE=false` in `.env` → image/video services fall back to ViT-only, no code change.
2. Comment out `loader.load_efficientnet()` call in `model_loader.py` → weights never load, zero RAM impact.
3. Revert commits in reverse order: `git revert <merge-commit-range>`. Adapter file can remain (dead code) — it has no import-time side effects since `sys.path` injection is inside the class module.
4. Delete `backend/models/icpr2020dfdc/` if disk pressure warrants. Weights cache survives at `~/.cache/torch/` and will be re-used on next attempt.

### 9.3 Telemetry to Add During Merge

Log these fields on every analysis to enable A/B evaluation during viva:

- `model_primary` — which model's score was used for the final verdict
- `model_scores` — dict of all model raw scores before ensemble
- `face_detector_used` — `"blazeface"` or `"mediapipe_fallback"`
- `calibrator_applied` — bool
- `heatmap_source` — `"attention" | "gradcam++" | "fallback" | "none"`

These go into `AnalysisRecord.debug_metadata` (new JSON column — piggyback on Phase 19.4 Alembic migration).

---

End of MERGE_PLAN.
