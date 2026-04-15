# DeepShield — API Reference

> **Base URL:** `http://localhost:8000/api/v1`
> **Content Type:** All JSON endpoints accept/return `application/json`. File upload endpoints use `multipart/form-data`.
> **Authentication:** Bearer token via `Authorization: Bearer <token>` header. Required only for `/auth/me`, `/history/*`. Analysis endpoints work both authenticated and unauthenticated — when authenticated, analysis records are linked to your account.

---

## Table of Contents

- [Health](#health)
- [Analyze — Image](#analyze--image)
- [Analyze — Video](#analyze--video)
- [Analyze — Text](#analyze--text)
- [Analyze — Screenshot](#analyze--screenshot)
- [Report — Generate PDF](#report--generate-pdf)
- [Report — Download PDF](#report--download-pdf)
- [Auth — Register](#auth--register)
- [Auth — Login](#auth--login)
- [Auth — Current User](#auth--current-user)
- [History — List](#history--list)
- [History — Detail](#history--detail)
- [History — Delete](#history--delete)
- [Common Response Schemas](#common-response-schemas)
- [Error Responses](#error-responses)

---

## Health

### `GET /health`

Returns server health status.

**Response:**
```json
{ "status": "ok" }
```

---

## Analyze — Image

### `POST /analyze/image`

Analyze an image for deepfake manipulation using ViT classifier, Grad-CAM heatmap, and artifact detection.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `file` | File | Yes | JPEG, PNG, or WebP image (max 20 MB) |

**Response:** `ImageAnalysisResponse`

```json
{
  "analysis_id": "uuid-string",
  "record_id": 1,
  "media_type": "image",
  "timestamp": "2026-04-15T12:00:00+00:00",
  "verdict": {
    "label": "Possibly Manipulated",
    "severity": "warning",
    "authenticity_score": 49,
    "model_confidence": 0.508,
    "model_label": "Deepfake"
  },
  "explainability": {
    "heatmap_base64": "data:image/png;base64,...",
    "artifact_indicators": [
      {
        "type": "gan_artifact",
        "severity": "medium",
        "description": "High-frequency energy ratio indicates possible GAN generation",
        "confidence": 0.67
      }
    ]
  },
  "trusted_sources": [],
  "contradicting_evidence": [],
  "processing_summary": {
    "stages_completed": ["validation", "classification", "artifact_scanning", "heatmap_generation"],
    "total_duration_ms": 4800,
    "model_used": "prithivMLmods/Deep-Fake-Detector-v2-Model"
  },
  "responsible_ai_notice": "AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing."
}
```

**Pipeline stages:** `validation` → `classification` → `artifact_scanning` → `heatmap_generation`

---

## Analyze — Video

### `POST /analyze/video`

Analyze a video by sampling frames, running per-frame ViT classification with face-gating, and aggregating results.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `file` | File | Yes | MP4, AVI, MOV, or WebM video (max 100 MB) |

**Response:** `VideoAnalysisResponse`

```json
{
  "analysis_id": "uuid-string",
  "record_id": 2,
  "media_type": "video",
  "timestamp": "2026-04-15T12:00:00+00:00",
  "verdict": { ... },
  "explainability": {
    "num_frames_sampled": 16,
    "num_face_frames": 12,
    "num_suspicious_frames": 3,
    "mean_suspicious_prob": 0.42,
    "max_suspicious_prob": 0.78,
    "suspicious_ratio": 0.25,
    "insufficient_faces": false,
    "suspicious_timestamps": [2.1, 4.5, 6.8],
    "frames": [
      {
        "index": 0,
        "timestamp_s": 0.0,
        "label": "Realism",
        "confidence": 0.85,
        "suspicious_prob": 0.15,
        "is_suspicious": false,
        "has_face": true,
        "scored": true
      }
    ]
  },
  "processing_summary": { ... },
  "responsible_ai_notice": "..."
}
```

**Face-gating:** If fewer than 3 frames contain a detectable face (`insufficient_faces: true`), verdict defaults to "Insufficient face content" (score 50, severity warning) to avoid false positives on non-face content.

**Pipeline stages:** `validation` → `frame_extraction` → `frame_classification` → `aggregation`

---

## Analyze — Text

### `POST /analyze/text`

Analyze text (news article, social media post) for fake news, sensationalism, and manipulation patterns.

**Request:** `application/json`

```json
{ "text": "Article text to analyze (50 - 10,000 characters)" }
```

**Response:** `TextAnalysisResponse`

```json
{
  "analysis_id": "uuid-string",
  "record_id": 3,
  "media_type": "text",
  "timestamp": "2026-04-15T12:00:00+00:00",
  "verdict": { ... },
  "explainability": {
    "fake_probability": 0.23,
    "top_label": "LABEL_1",
    "all_scores": { "LABEL_0": 0.23, "LABEL_1": 0.77 },
    "keywords": ["climate", "government", "report", "scientists"],
    "sensationalism": {
      "score": 55,
      "level": "Medium",
      "exclamation_count": 3,
      "caps_word_count": 2,
      "clickbait_matches": 1,
      "emotional_word_count": 2,
      "superlative_count": 1
    },
    "manipulation_indicators": [
      {
        "pattern_type": "unverified_claim",
        "matched_text": "Sources say",
        "start_pos": 45,
        "end_pos": 56,
        "severity": "medium",
        "description": "Unverified source attribution without specific citation"
      }
    ]
  },
  "trusted_sources": [
    {
      "source_name": "reuters",
      "title": "Related article headline",
      "url": "https://reuters.com/article/...",
      "published_at": "2026-04-14",
      "relevance_score": 1.0
    }
  ],
  "contradicting_evidence": [],
  "processing_summary": { ... },
  "responsible_ai_notice": "..."
}
```

**Score formula:** `70% classifier × (1 − fake_prob) + 20% (100 − sensationalism) + 10% (100 − manipulation_penalty)`

**Pipeline stages:** `classification` → `sensationalism_analysis` → `manipulation_detection` → `keyword_extraction` → `news_lookup`

---

## Analyze — Screenshot

### `POST /analyze/screenshot`

Analyze a social media screenshot: OCR text extraction, credibility analysis, layout anomaly detection, and suspicious phrase overlay mapping.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `file` | File | Yes | JPEG, PNG, or WebP screenshot (max 20 MB) |

**Response:** `ScreenshotAnalysisResponse`

```json
{
  "analysis_id": "uuid-string",
  "record_id": 4,
  "media_type": "screenshot",
  "timestamp": "2026-04-15T12:00:00+00:00",
  "verdict": { ... },
  "explainability": {
    "extracted_text": "Full OCR text concatenated...",
    "ocr_boxes": [
      {
        "text": "BREAKING NEWS",
        "bbox": [[10, 20], [200, 20], [200, 50], [10, 50]],
        "confidence": 0.95
      }
    ],
    "fake_probability": 0.45,
    "sensationalism": { ... },
    "suspicious_phrases": [
      {
        "text": "Sources say",
        "bbox": [[30, 100], [180, 100], [180, 130], [30, 130]],
        "pattern_type": "unverified_claim",
        "severity": "medium",
        "description": "Unverified source attribution"
      }
    ],
    "layout_anomalies": [
      {
        "type": "font_mismatch",
        "severity": "medium",
        "description": "Text region heights vary significantly (CV=0.45)",
        "confidence": 0.72
      }
    ],
    "keywords": ["breaking", "news", "scandal"]
  },
  "trusted_sources": [ ... ],
  "contradicting_evidence": [ ... ],
  "processing_summary": { ... },
  "responsible_ai_notice": "..."
}
```

**Score formula:** `65% classifier + 20% sensationalism + 10% manipulation + 5% layout`

**Pipeline stages:** `validation` → `ocr` → `classification` → `sensationalism_analysis` → `manipulation_detection` → `phrase_overlay_mapping` → `layout_anomaly_detection` → `keyword_extraction` → `news_lookup`

---

## Report — Generate PDF

### `POST /report/{analysis_id}`

Generate a PDF report for a completed analysis. Idempotent — reuses existing report if already generated.

**Path Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `analysis_id` | int | The `record_id` from an analysis response |

**Response:**
```json
{
  "report_id": 1,
  "analysis_id": 5,
  "ready": true
}
```

---

## Report — Download PDF

### `GET /report/{analysis_id}/download`

Download the generated PDF report.

**Path Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `analysis_id` | int | The `record_id` from an analysis response |

**Response:** `application/pdf` file download (`deepshield_report_{id}.pdf`)

**Errors:**
- `404` — Report not found (generate first)
- `410` — Report expired or deleted

---

## Auth — Register

### `POST /auth/register`

Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure123",
  "name": "Optional Name"
}
```

| Field | Type | Constraints |
|:------|:-----|:------------|
| `email` | string | Valid email (unique) |
| `password` | string | 6–128 characters |
| `name` | string? | Optional, max 255 chars |

**Response (201):** `TokenResponse`
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in_minutes": 1440,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Optional Name",
    "created_at": "2026-04-15T12:00:00"
  }
}
```

**Errors:** `409` — Email already registered

---

## Auth — Login

### `POST /auth/login`

Authenticate and receive a JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure123"
}
```

**Response:** `TokenResponse` (same schema as register)

**Errors:** `401` — Invalid email or password

---

## Auth — Current User

### `GET /auth/me`

Get the currently authenticated user profile. **Requires Bearer token.**

**Response:** `UserOut`
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Optional Name",
  "created_at": "2026-04-15T12:00:00"
}
```

**Errors:** `401` — Missing or invalid token

---

## History — List

### `GET /history`

List past analyses for the authenticated user. **Requires Bearer token.**

**Query Parameters:**

| Parameter | Type | Default | Constraints |
|:----------|:-----|:--------|:------------|
| `limit` | int | 50 | 1–200 |
| `offset` | int | 0 | ≥ 0 |

**Response:**
```json
{
  "items": [
    {
      "id": 10,
      "media_type": "text",
      "verdict": "Very Likely Real",
      "authenticity_score": 88.0,
      "created_at": "2026-04-15T12:30:00"
    }
  ],
  "total": 1
}
```

---

## History — Detail

### `GET /history/{record_id}`

Get full stored analysis result. **Requires Bearer token.**

**Response:** Full analysis response JSON (same as original `/analyze/*` response, excluding heatmap for images)

**Errors:** `404` — Analysis not found or belongs to different user

---

## History — Delete

### `DELETE /history/{record_id}`

Delete an analysis record. **Requires Bearer token.**

**Response:** `204 No Content`

**Errors:** `404` — Analysis not found or belongs to different user

---

## Common Response Schemas

### Verdict

| Field | Type | Description |
|:------|:-----|:------------|
| `label` | string | Human-readable verdict (see trust scale below) |
| `severity` | string | `critical` / `danger` / `warning` / `positive` / `safe` |
| `authenticity_score` | int | 0–100 (higher = more authentic) |
| `model_confidence` | float | 0.0–1.0 raw model confidence |
| `model_label` | string | Raw model output label |

### Trust Scale

| Score Range | Label | Severity |
|:------------|:------|:---------|
| 0–20 | Highly Likely Manipulated | critical |
| 21–40 | Likely Manipulated | danger |
| 41–60 | Possibly Manipulated | warning |
| 61–80 | Very Likely Real | positive |
| 81–100 | Almost Certainly Real | safe |

### ProcessingSummary

| Field | Type | Description |
|:------|:-----|:------------|
| `stages_completed` | string[] | List of pipeline stages executed |
| `total_duration_ms` | int | Total processing time in milliseconds |
| `model_used` | string | HuggingFace model ID used |

---

## Error Responses

All errors follow FastAPI's standard format:

```json
{
  "detail": "Error description string"
}
```

| Status | Meaning |
|:-------|:--------|
| `400` | Bad request (invalid file type, text too short, etc.) |
| `401` | Authentication required or invalid token |
| `404` | Resource not found |
| `409` | Conflict (e.g., duplicate email) |
| `410` | Resource expired (e.g., deleted report) |
| `413` | File too large |
| `500` | Internal server error |
