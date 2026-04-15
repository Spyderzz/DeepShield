# DeepShield — Model Cards

> Academic documentation of all AI/ML models used in DeepShield.
> Follows [Google Model Card guidelines](https://modelcards.withgoogle.com/about).

---

## Table of Contents

1. [ViT Deepfake Image Classifier](#1-vit-deepfake-image-classifier)
2. [BERT Fake News Text Classifier](#2-bert-fake-news-text-classifier)
3. [EasyOCR Text Extraction Engine](#3-easyocr-text-extraction-engine)
4. [MediaPipe FaceMesh](#4-mediapipe-facemesh)
5. [Grad-CAM Explainability](#5-grad-cam-explainability)
6. [Deterministic Signal Extractors](#6-deterministic-signal-extractors)
7. [Composite Scoring Formula](#7-composite-scoring-formula)
8. [Known Limitations](#8-known-limitations)

---

## 1. ViT Deepfake Image Classifier

| Property | Value |
|:---------|:------|
| **Model ID** | [`prithivMLmods/Deep-Fake-Detector-v2-Model`](https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model) |
| **Architecture** | Vision Transformer (ViT) — `vit-base-patch16-224` |
| **Parameters** | ~86M |
| **Input** | 224×224 RGB image (auto-resized from any dimension) |
| **Output** | Binary classification: `{0: "Realism", 1: "Deepfake"}` with confidence |
| **Training Data** | Face-centric deepfake datasets (GAN-generated face swaps) |
| **Used In** | Image analysis pipeline, Video per-frame analysis |
| **Inference Device** | CPU (configurable to CUDA via `DEVICE` env var) |
| **Typical Latency** | ~2-4s per image on CPU |

### Usage in DeepShield

```python
# Image pipeline: classify_image() in services/image_service.py
from transformers import AutoModelForImageClassification, AutoImageProcessor
model = AutoModelForImageClassification.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")
processor = AutoImageProcessor.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")

# Video pipeline: analyze_video() in services/video_service.py
# Reuses the same model via ModelLoader singleton, applies per-frame with face-gating
```

### Strengths
- Good accuracy on face-centric deepfakes (GAN-generated face swaps)
- Interpretable via Grad-CAM heatmaps showing attention regions
- Lightweight enough for CPU inference

### Limitations
- **Face-centric bias:** Trained primarily on face manipulation data; tends to over-predict "Deepfake" on non-face imagery (landscapes, objects, text)
- **GAN-trained:** May underperform on diffusion-model-generated images (Stable Diffusion, DALL-E) which exhibit different artifact patterns
- **Resolution sensitivity:** All images are resized to 224×224, losing fine-grained details

### Mitigation in DeepShield
- **Face-gating (video):** Only frames with MediaPipe-detected faces contribute to the verdict. Below 3 face frames → "Insufficient face content" instead of a potentially incorrect classification
- **Artifact detection:** Supplementary deterministic signals (FFT spectral analysis, JPEG Q-table, facial boundary jitter) provide explainability beyond the neural classifier

---

## 2. BERT Fake News Text Classifier

| Property | Value |
|:---------|:------|
| **Model ID** | [`jy46604790/Fake-News-Bert-Detect`](https://huggingface.co/jy46604790/Fake-News-Bert-Detect) |
| **Architecture** | BERT-base uncased, fine-tuned for sequence classification |
| **Parameters** | ~110M |
| **Input** | Tokenized text (max 512 tokens, truncated) |
| **Output** | Binary classification: `{LABEL_0: "Fake", LABEL_1: "Real"}` with confidence |
| **Training Data** | Fake news datasets (English language) |
| **Used In** | Text analysis pipeline, Screenshot OCR text credibility check |
| **Typical Latency** | ~1-2s per text on CPU |

### Usage in DeepShield

```python
# Text pipeline: classify_text() in services/text_service.py
from transformers import pipeline
pipe = pipeline("text-classification", model="jy46604790/Fake-News-Bert-Detect", top_k=None)
# Returns all label scores; fake_prob extracted from LABEL_0
```

### Supplementary Analyses (non-neural)
The BERT classifier provides the core credibility signal. DeepShield augments it with:

1. **Sensationalism scoring** — Regex-based detection of clickbait patterns, emotional language, ALL CAPS, exclamation marks, superlatives → 0-100 score
2. **Manipulation indicator detection** — 15 regex patterns across 3 categories:
   - `unverified_claim` (5 patterns): "sources say", "allegedly", "reports suggest", etc.
   - `emotional_manipulation` (5 patterns): "shocking truth", "wake up", "they don't want you to know", etc.
   - `false_authority` (5 patterns): "experts confirm", "studies show", "everyone knows", etc.

### Note on Model Selection
The original BUILD_PLAN specified `GonzaloA/fake-news-detection-small`, but this model returned 404 on the HuggingFace Hub at build time. `jy46604790/Fake-News-Bert-Detect` was selected as a replacement with the same architecture and task (binary fake/real classification).

---

## 3. EasyOCR Text Extraction Engine

| Property | Value |
|:---------|:------|
| **Library** | [`EasyOCR`](https://github.com/JaidedAI/EasyOCR) v1.7.2 |
| **Architecture** | CRAFT text detector + CRNN text recognizer |
| **Languages** | English (`en`) |
| **Input** | PIL Image (any size) |
| **Output** | List of `(bounding_box, text, confidence)` tuples |
| **Used In** | Screenshot analysis pipeline |
| **Typical Latency** | ~5-15s depending on text density |

### Usage in DeepShield

```python
# Screenshot pipeline: run_ocr() in services/screenshot_service.py
import easyocr
reader = easyocr.Reader(["en"], gpu=False, verbose=False)
results = reader.readtext(numpy_array, detail=1)
```

### Notes
- `verbose=False` is required on Windows to prevent `UnicodeEncodeError` with cp1252 console encoding
- Low-confidence detections (< 0.3) are filtered out
- Bounding boxes are used for suspicious phrase overlay mapping on the original screenshot

---

## 4. MediaPipe FaceMesh

| Property | Value |
|:---------|:------|
| **Library** | [`MediaPipe`](https://github.com/google/mediapipe) v0.10.14 |
| **Model** | FaceMesh (468 3D landmarks) |
| **Used In** | Video face-gating, Artifact detection (facial boundary jitter) |
| **Configuration** | `static_image_mode=True`, `max_num_faces=5`, `min_detection_confidence=0.5` |

### Purpose in DeepShield

1. **Video pipeline face-gating:** Determines which sampled frames contain faces. Only face-containing frames contribute to the deepfake probability aggregation.
2. **Artifact detection (jaw-contour jitter):** Extracts 17 jaw-contour landmarks (indices 10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400), computes inter-landmark distances, and flags high variance (CV > 0.15) as potential deepfake boundary artifacts.

---

## 5. Grad-CAM Explainability

| Property | Value |
|:---------|:------|
| **Library** | [`pytorch-grad-cam`](https://github.com/jacobgil/pytorch-grad-cam) v1.5.4 |
| **Method** | GradCAM++ on ViT attention layers |
| **Target Layer** | `model.vit.encoder.layer[-1].layernorm_before` |
| **Reshape Transform** | Drop CLS token, reshape 196 patch tokens → 14×14 spatial grid |
| **Output** | Base64-encoded PNG heatmap overlaid on original image |

### How It Works

1. Forward pass through ViT classifier
2. Compute gradients of the predicted class w.r.t. the target layer
3. Weight activation maps by gradient importance
4. Reshape from 196 tokens to 14×14 grid
5. Upsample to 224×224 and apply JET colormap
6. Alpha-blend heatmap over original image (α=0.4)
7. Encode as `data:image/png;base64,...`

### Interpretation
- **Red/hot regions** = Areas the model focused on most for its classification decision
- **Blue/cool regions** = Areas with low model attention
- For deepfake-classified images, red regions typically correspond to manipulated facial boundaries, inconsistent lighting, or GAN artifacts

---

## 6. Deterministic Signal Extractors

These are non-neural, algorithmic detectors that provide interpretable evidence signals:

| Signal | Method | Threshold | Severity Mapping |
|:-------|:-------|:----------|:-----------------|
| **GAN HF Artifact** | FFT power spectrum, high-frequency energy ratio | ratio > 0.15 | Low: 0.15-0.25, Medium: 0.25-0.40, High: > 0.40 |
| **JPEG Compression Anomaly** | PIL `img.quantization` Q-table inspection | deviation from standard tables | Low-Medium based on deviation |
| **Facial Boundary Jitter** | MediaPipe jaw-contour landmark CV | CV > 0.15 | Medium-High based on CV |
| **Lighting Inconsistency** | Per-quadrant luminance mean + std analysis | inter-quadrant variance | Medium-High based on imbalance |
| **Layout Anomaly (Screenshot)** | OCR bbox height/alignment/spacing CV | CV thresholds per type | Low-Medium |

---

## 7. Composite Scoring Formula

DeepShield combines multiple signals into a single **authenticity score** (0-100, higher = more authentic):

### Image Pipeline
```
score = authenticity_score(model_confidence, model_label)
       where authenticity_score maps (1 - fake_prob) × 100 through the trust scale
```

### Video Pipeline
```
score = (1 − mean_suspicious_prob) × 100
       where mean_suspicious_prob is averaged only over face-containing frames
       If insufficient_faces: score = 50 (neutral)
```

### Text Pipeline
```
score = 0.70 × (1 − fake_prob) × 100
      + 0.20 × (100 − sensationalism_score)
      + 0.10 × (100 − manipulation_penalty)
      where manipulation_penalty = min(num_indicators × 5, 30)
```

### Screenshot Pipeline
```
score = 0.65 × (1 − fake_prob) × 100
      + 0.20 × (100 − sensationalism_score)
      + 0.10 × (100 − manipulation_penalty)
      + 0.05 × (100 − layout_penalty)
      where layout_penalty = min(num_anomalies × 5, 15)
      If no text extracted: score = 50 (neutral)
```

---

## 8. Known Limitations

| Limitation | Impact | Mitigation |
|:-----------|:-------|:-----------|
| ViT trained on GAN fakes only | May miss diffusion-model deepfakes | Supplementary artifact signals provide partial coverage |
| BERT limited to English | Non-English text gets inaccurate classification | EasyOCR supports Hindi; BERT model could be swapped |
| Single-model pipeline | No ensemble voting | Artifact indicators provide multi-signal evidence |
| CPU-only default | Slower inference (2-4s/image, 5-15s/screenshot) | GPU configurable via `DEVICE=cuda` |
| 512-token BERT limit | Long articles truncated | First 2000 chars sent; keywords extracted from full text |
| No temporal audio analysis | Video audio track not analyzed | Face-gating on visual frames only |

---

## Citations

```bibtex
@misc{deepfakedetectorv2,
    title={Deep-Fake-Detector-v2-Model},
    author={prithivMLmods},
    year={2024},
    howpublished={\url{https://huggingface.co/prithivMLmods/Deep-Fake-Detector-v2-Model}}
}

@misc{fakenewsbertdetect,
    title={Fake-News-Bert-Detect},
    author={jy46604790},
    year={2024},
    howpublished={\url{https://huggingface.co/jy46604790/Fake-News-Bert-Detect}}
}

@inproceedings{selvaraju2017gradcam,
    title={Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization},
    author={Selvaraju, Ramprasaath R. and Cogswell, Michael and Das, Abhishek and
            Vedantam, Ramakrishna and Parikh, Devi and Batra, Dhruv},
    booktitle={IEEE International Conference on Computer Vision (ICCV)},
    year={2017}
}

@inproceedings{jaided2020easyocr,
    title={EasyOCR},
    author={JaidedAI},
    year={2020},
    howpublished={\url{https://github.com/JaidedAI/EasyOCR}}
}

@misc{mediapipe2019,
    title={MediaPipe: A Framework for Building Perception Pipelines},
    author={Google},
    year={2019},
    howpublished={\url{https://mediapipe.dev}}
}

@misc{dosovitskiy2020vit,
    title={An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale},
    author={Dosovitskiy, Alexey and Beyer, Lucas and Kolesnikov, Alexander and
            Weissenborn, Dirk and Zhai, Xiaohua and Unterthiner, Thomas and
            Dehghani, Mostafa and Minderer, Matthias and Heigold, Georg and
            Gelly, Sylvain and Uszkoreit, Jakob and Houlsby, Neil},
    year={2020},
    eprint={2010.11929},
    archivePrefix={arXiv}
}

@article{devlin2018bert,
    title={BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding},
    author={Devlin, Jacob and Chang, Ming-Wei and Lee, Kenton and Toutanova, Kristina},
    journal={arXiv preprint arXiv:1810.04805},
    year={2018}
}
```
