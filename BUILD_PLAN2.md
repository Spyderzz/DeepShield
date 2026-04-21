# DeepShield — BUILD PLAN 2 (Hardening, UX Overhaul & Advanced Features)

> **Derived from:** [ISSUES.md](ISSUES.md) (sections 1–6) + end-to-end audit on 2026-04-15
> **Predecessor:** [BUILD_PLAN.md](BUILD_PLAN.md) — Phases 0–10 complete (MVP shipped, manually QA'd)
> **Status:** PLANNING — Phases 11 → 22
> **Authoring date:** 2026-04-15
> **Owner:** Spyderzz

---

## 0. Executive Summary

The MVP works end-to-end across all four media pipelines (image / video / text / screenshot), with auth, history, PDF, and a polished landing page. Manual QA surfaced **25+ defects** spanning model accuracy, explainability depth, UX polish, security hardening, and missing core features (no real video temporal reasoning, no audio detection, no multi-lingual, no rate limiting, broken results page, blind reports endpoint, etc.).

**BUILD PLAN 2 organizes those defects into 12 sequenced phases.** Each phase is independently shippable and minimizes regressions by isolating model swaps from UI work and security work from feature work.

### Top-Priority Themes

| Theme | Phases | Why critical |
|---|---|---|
| **Trust & Accuracy** | 11, 13, 17 | Core promise — currently the ViT image model false-positives even unedited camera photos |
| **Explainability** | 12, 14 | LLM cards + Grad-CAM upgrade + per-component VLM scores fix the "black-box" criticism |
| **Security & Abuse** | 15, 19 | Report endpoints have ZERO auth; no rate limiting; JWT default secret |
| **UX Overhaul** | 16, 18, 20 | Apple-style 3D animation, glassmorphism, sticky FABs, results page repair |
| **Platform Maturity** | 21, 22 | Tests, observability, i18n, dark mode, accessibility, privacy |

---

## 1. Phase Map (Sequencing)

```
Phase 11 → Image Model Replacement (FaceForensics++ fine-tune)
Phase 12 → Explainability v2: LLM Cards + Grad-CAM++ + ELA + EXIF
Phase 13 → Text Pipeline Hardening (NER + Truth-Override + Multi-lingual)
Phase 14 → VLM "Detailed Breakdown" Cards + PDF Re-skin
Phase 15 → Security Hardening (Auth on /report, Rate Limiting, JWT, CORS)
Phase 16 → Results Page Rebuild + History Navigation Fix
Phase 17 → Video Pipeline v2: Temporal Consistency + Audio Detection
Phase 18 → UI Polish v2: Apple 3D Animation, Glassmorphism, Sticky FAB
Phase 19 → Backend Platform: SHA-256 Cache, Job Queue, Object Storage
Phase 20 → Landing Page v2 + Analyze Page Overhaul
Phase 21 → Quality Gates: Tests, CI, Observability, Logging
Phase 22 → Platform Maturity: i18n, Dark Mode, A11y, Privacy
```

Phases 11, 15, and 16 are **blocking** for academic-defense submission. Phases 17, 18, and 21 are the highest user-visible "wow" upgrades.

---

## 2. Phase 11 — Image Model Replacement (Resolves ISSUE 1.1, 6.23)

**Goal:** Replace the over-fitting `prithivMLmods/Deep-Fake-Detector-v2-Model` with a fine-tuned ConvNeXt or Swin-Transformer trained on FaceForensics++ + DFDC + raw camera photos.

### 11.1 Dataset Procurement
- Run `python backend/scripts/download_ffpp.py ./ffpp_data -d all -c raw -t videos` (script is already in repo).
- Augment with: **FFHQ** (real faces), and a sample of **DFDC** (diverse fakes).
- Convert all videos → 16 sampled frames @ 224×224 RGB → ~120k labeled images.

### 11.2 Training Pipeline
- New `backend/training/` module:
  - `dataset.py` — PyTorch `ImageFolder`-style loader, train/val/test 70/15/15.
  - `train_convnext.py` — fine-tune `facebook/convnext-tiny-224` (28M params, fits CPU/single GPU). Loss: BCE + label smoothing 0.1. Optimizer: AdamW lr=1e-4, cosine schedule. 10 epochs.
  - `calibrate.py` — fit isotonic regression on val set → save `calibrator.pkl` (resolves ISSUE 6.23).
  - `eval.py` — confusion matrix, per-source AUC, output `model_card.md`.
- Acceptance gate: **≥ 92% accuracy on held-out FFPP test, ≤ 3% false-positive rate on the camera-photo anchor set.**

### 11.3 Backend Wiring
- New `IMAGE_MODEL_ID="deepshield/convnext-ffpp-v1"` (HF Hub upload OR local path).
- Update `services/image_service.py` → load via `AutoModelForImageClassification`, apply calibrator on output probs.
- Backwards-compat: keep `prithivMLmods/...` path behind `LEGACY_MODEL=true` env flag for A/B comparison in viva.

### 11.4 Smoke + Regression
- Re-run `backend/scripts/test_image_classify.py` against 50 hand-curated images (25 real / 25 fake).
- Update `docs/MODEL_CARDS.md` + `docs/datasets.md` with training run metadata.

**Deliverables:** new HF model checkpoint, calibrator, updated docs, regression report.

---

## 3. Phase 12 — Explainability v2 (Resolves ISSUE 1.2, 1.3, 1.4, 6.15)

### 12.1 Grad-CAM Upgrade + Error Level Analysis (ELA)
- Replace single-layer Grad-CAM with **Grad-CAM++** averaged across last 3 ViT/ConvNeXt blocks (smoother, less square-patch artifacts).
- Add `services/ela_service.py`: re-save image at quality 90, diff against original → per-pixel manipulation map. Blend with Grad-CAM at 60/40 weight.
- Bounding-box mode: extract top-K connected components from the heatmap, render colored boxes (red / yellow / orange) on the original image instead of a colormap splash.
- Frontend `HeatmapOverlay` gets a 3-state toggle: **Heatmap / ELA / Boxes**.
- New `heatmap_status` enum in API (resolves ISSUE 6.15).

### 12.2 EXIF Metadata Extractor
- `services/exif_service.py` using Pillow `_getexif()` + `exifread` fallback.
- Extract: `Make`, `Model`, `DateTimeOriginal`, `GPSInfo`, `Software`, `LensModel`.
- Score boost: presence of valid `Make`+`Model`+`DateTimeOriginal` → −15 to fake_prob; `Software=Adobe Photoshop` → +10 to fake_prob.
- New `exif: ExifSummary` field in `ImageExplainability`.
- Frontend `EXIFCard.jsx`: structured key/value list with green/red trust badges.

### 12.3 LLM Explainability Card
- New `services/llm_explainer.py`:
  - Provider abstraction with concrete `GeminiProvider` (`gemini-1.5-flash`, default) and `OpenAIProvider` (`gpt-4o-mini`).
  - API key from `.env`: `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`.
  - Prompt template feeds the full JSON payload (verdict, scores, indicators, EXIF, sources) → returns short paragraph + 3 bullet "key signals".
  - Cache per `record.id` to avoid re-spending tokens.
- New `llm_summary: { paragraph: str, bullets: list[str], model: str }` in every analysis response (image / video / text / screenshot).
- Frontend `LLMExplainCard.jsx`: rendered as the **first** card in results, sets the narrative tone before raw scores.

**Deliverables:** new heatmap modes, EXIF panel, LLM-generated plain-English explanation displayed in UI + embedded in PDF (Phase 14).

---

## 4. Phase 13 — Text Pipeline Hardening (Resolves ISSUE 2.1, 2.2, 5.3)

### 13.1 NER-Based Keyword Extraction
- Add `spacy==3.7.x` + `en_core_web_sm`.
- Replace `extract_keywords` frequency util with `extract_entities`: prefer `PERSON`, `ORG`, `GPE`, `EVENT`. Fall back to frequency for short text.
- Pass entities (not generic words) to `news_lookup` → fixes irrelevant cached sources.

### 13.2 Truth-Override Rule
- After `search_news_full`, compute cosine similarity (`sentence-transformers/all-MiniLM-L6-v2`) between input text and each trusted-source headline+description.
- If `≥ 1` trusted source has similarity ≥ 0.6 from a `weight ≥ 0.9` domain (Reuters/AP/BBC), apply **`fake_prob *= 0.3`** (cap at 0.15).
- Surface in API: `truth_override: { applied: bool, source_url: str, similarity: float }`.

### 13.3 Multi-Lingual Support (Phase 1 — English + Hindi)
- Swap `jy46604790/Fake-News-Bert-Detect` (English-only) for `xlm-roberta-base` fine-tuned on multilingual fake-news (or `Twitter/twhin-bert-base` as MVP).
- Detect language with `langdetect`; route to appropriate pipeline.
- EasyOCR initialized as `['en','hi']` (extendable). Configurable via `OCR_LANGS` env var.
- Frontend: language badge on results card.

**Deliverables:** more relevant sources, fewer false-positives on real news, baseline Hindi support (extendable to ta/bn/mr in future ticket).

---

## 5. Phase 14 — VLM "Detailed Breakdown" + PDF Re-skin (Resolves ISSUE 1.5, 4.2 polish, 6.24)

### 14.1 VLM Component-Score Card
- New `services/vlm_breakdown.py` calling Gemini 1.5 Pro (or GPT-4o) Vision with a structured-output prompt requesting JSON:
  ```json
  {
    "facial_symmetry": {"score": 0–100, "notes": "..."},
    "skin_texture": {...},
    "lighting_consistency": {...},
    "background_coherence": {...},
    "anatomy_hands_eyes": {...},
    "context_objects": {...}
  }
  ```
- Cached per file SHA (Phase 19) — single VLM call per unique image.
- Frontend new `DetailedBreakdownCards.jsx`: 6 percentage cards in a responsive grid, each clickable to expand notes.

### 14.2 PDF Template v2
- Embed DeepShield SVG logo (base64) at top.
- Render donut chart of authenticity score (matplotlib → PNG → base64).
- Inline 400px-wide thumbnail of analyzed image.
- Inject **LLM paragraph** + **Detailed Breakdown table** + **EXIF table**.
- Replace flex/grid CSS with nested `<table>` (xhtml2pdf-friendly) — also fixes residual rendering glitches behind ISSUE 4.2.
- Acceptance: PDF opens cleanly in Adobe Acrobat, Preview (macOS), and Chrome's built-in viewer.

---

## 6. Phase 15 — Security Hardening (Resolves ISSUE 4.1, 5.4, 6.3, 6.4, 6.6, 6.7, 6.8)

### 15.1 Auth on /report Endpoints
- `POST /report/{id}`, `GET /report/{id}/download`: add `user: User = Depends(get_current_user)`.
- Verify `record.user_id == user.id` OR allow if `record.user_id is None` AND request was made within same session token (resolves ISSUE 6.3).
- `POST /report/cleanup`: admin-only or remove from public router (run only via internal scheduler).
- Frontend: `ReportDownload` checks `isAuthed`; if false, calls `toast.warning('Sign in to download reports')` and redirects.

### 15.2 Rate Limiting (slowapi)
- `pip install slowapi`. Mount `Limiter` keyed by `get_remote_address` for anon and `user.id` when authed.
- Limits:
  - Anonymous: `5/hour` for `/analyze/*`, `2/hour` for `/report/*`.
  - Authenticated: `50/hour` for `/analyze/*`, `20/hour` for `/report/*`.
- Return `429 Too Many Requests` with `Retry-After`. Frontend toast: "Rate limit reached — try again in N minutes."

### 15.3 JWT & Config Hardening
- Refuse to start when `DEBUG=False` and `JWT_SECRET_KEY` is the default. Print `secrets.token_urlsafe(48)` example in error message.
- Restrict CORS `allow_methods` and `allow_headers` to explicit lists. Reject `*` origins when `allow_credentials=True`.
- Add `loguru.add(rotation="10 MB", retention="7 days")` and email scrubber.

**Deliverables:** all `/report` routes auth-guarded, rate limits in place, CI fails if JWT default present in production config.

---

## 7. Phase 16 — Results Page Rebuild + History Navigation (Resolves ISSUE 3.4, 6.1, 6.2, 6.12)

### 16.1 ResultsPage.jsx Implementation
- Fetch `GET /history/{id}` on mount.
- Render the same component stack used in `AnalyzePage` results view (VerdictCard / ScoreMeter / explainability per media type / sources / contradictions / report download).
- Reuse a new `<AnalysisResultView analysis={data}/>` shared component extracted from `AnalyzePage`.
- 404 → friendly empty state with "Back to History" link.

### 16.2 HistoryPage Clickable Rows
- Wrap each row in `<Link to={'/results/' + it.id}>`, keep Delete as `stopPropagation` button.
- Add hover state, focus ring (a11y).

### 16.3 Auth Rehydrate Race
- Add `authReady` boolean to `AuthContext`. Block protected routes with a global splash until `authReady=true`.

### 16.4 Sticky Action Bar (also serves Phase 18 UX overhaul)
- Floating bottom bar with "Analyze Another" + "Generate PDF" + "Share" buttons. Visible only on results pages.

---

## 8. Phase 17 — Video Pipeline v2 (Resolves ISSUE 5.1, 5.2)

### 17.1 Temporal Consistency Module
- New `services/video_temporal.py`:
  - Compute optical flow between consecutive sampled frames (`cv2.calcOpticalFlowFarneback`).
  - Detect anomalies: micro-flicker variance, unnatural blink rate (using FaceMesh eye-aspect-ratio over time), lip-sync mismatch (correlate lip landmark motion with audio energy).
- Output `temporal_score: 0–100` (higher = more natural). Fold into final video score with 30% weight.
- (Optional, gated by GPU): swap to **VideoMAE** (`MCG-NJU/videomae-base-finetuned-kinetics`) fine-tuned on FF++ for true 3D-CNN baseline.

### 17.2 Audio Deepfake Detection
- New `services/audio_service.py`:
  - Extract `.wav` track via `ffmpeg-python` (system ffmpeg already required for OpenCV).
  - Run `microsoft/wavlm-base-plus` or `facebook/wav2vec2-large-960h` embeddings → MLP head trained on ASVspoof 2019 (download script + training in same Phase 11 training/ module).
  - Output `audio_authenticity_score: 0–100`.
- New `audio: AudioExplainability` field in `VideoAnalysisResponse`. Frontend new `AudioCard.jsx` with waveform visualization (`wavesurfer.js`).

### 17.3 Combined Video Verdict
- `final_score = 0.5 * visual_score + 0.3 * temporal_score + 0.2 * audio_score` (when audio present); fall back to 0.7/0.3 when audio missing.

---

## 9. Phase 18 — UI Polish v2 (Resolves ISSUE 3.1, 3.2, 3.5)

### 18.1 Apple-Style 3D Layer Animation
- New `components/common/ProcessingAnimation.jsx` per ISSUE 3.1 spec:
  - 5–7 semi-transparent clones of uploaded image.
  - Parent `transform: rotateX(60deg) rotateZ(-45deg); transform-style: preserve-3d`.
  - `framer-motion` staggered translateZ expansion, spring physics.
  - Per-layer CSS filters: grayscale+contrast (artifact pass), hue-rotate+blur (heatmap), overlay blend (scanning).
  - Scanning laser bar across the top.
- Replaces `LoadingSpinner` for image/video/screenshot uploads.

### 18.2 Glassmorphism + Premium Aesthetics
- Refactor `index.css` tokens: add `--glass-bg: rgba(255,255,255,0.65); --glass-border: rgba(255,255,255,0.3); --glass-blur: 16px;`.
- Wrap primary cards (Verdict, EXIF, LLM summary, Detailed Breakdown) in `.glass-panel` class with `backdrop-filter: blur(16px)`.
- Switch typography to **Inter** (already widely loaded; add `@fontsource/inter`).
- Multi-layered drop shadows (`--shadow-md: 0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.08)`).
- Login/Register: full-page overhaul with mesh-gradient background + glassmorphism form card + lottie illustration.

### 18.3 Analyze Page Core Overhaul
- Centralized hero drag-zone (~600×400) with liquid hover state (svg blob morph on hover, `framer-motion`).
- Segmented controller (iOS-style) for Image / Video / Text / Screenshot — animated pill background.
- Mesh-gradient dark background panel as canvas.

---

## 10. Phase 19 — Backend Platform (Resolves ISSUE 5.5, 6.5, 6.9, 6.10, 6.18, 6.22)

### 19.1 SHA-256 Dedup Cache
- On upload, hash file in 64KB chunks (streaming).
- Query `AnalysisRecord` for `media_hash == sha`. If exists AND `created_at` within `CACHE_TTL_DAYS=30`, return cached payload (mark `cached: true`).
- Add `media_hash: str` column + index to `AnalysisRecord`.

### 19.2 Object Storage
- Stream uploads to `media/{sha[:2]}/{sha}.{ext}` (local disk; S3 abstraction stubbed via `services/storage.py` for later).
- Save thumbnail at `media/thumbs/{sha}_400.jpg` (400px max).
- `AnalysisRecord.media_path` and `AnalysisRecord.thumbnail_url` added to schema and history responses (resolves ISSUE 6.17 once frame thumbnails join the same scheme).

### 19.3 Job Queue (FastAPI BackgroundTasks → Celery later)
- For video + screenshot pipelines (long-running), add `POST /analyze/video` returns `202 Accepted` with `{job_id, status:'queued'}`.
- New `GET /jobs/{id}` returns `{stage, progress, result?}`.
- Frontend `PipelineVisualizer` polls `/jobs/{id}` every 800ms → real backend stages instead of guessed timing.
- Image / text remain synchronous (fast enough).

### 19.4 DB Indices + Postgres Path
- Add Alembic migrations: `ix_record_user_created`, `ix_record_hash`, `ix_report_analysis`.
- Document Postgres connection string in `.env.example`; SQLite remains the default.

### 19.5 Healthcheck Split
- `GET /health/live` → 200 always (process up).
- `GET /health/ready` → 200 only when models loaded + DB reachable.
- Frontend disables Analyze button while `/health/ready` returns 503.

---

## 11. Phase 20 — Landing Page v2 + Engagement (Resolves ISSUE 3.3)

- **Moving Impact Cards:** marquee carousel of 6 real-world deepfake stories (with sources). Use `framer-motion` infinite loop.
- **"Why DeepShield is Better":** 3-column comparison grid vs. competitors (Reality Defender, Deepware, manual checking).
- **FAQ Accordion:** 8 questions covering accuracy, privacy, supported formats, model details.
- **Live counter:** "X analyses run in last 24h" — hits `GET /stats/recent` (new endpoint, Postgres only).
- **Trust badges:** "Local processing", "Open-source models", "Privacy-first" with icons.

---

## 12. Phase 21 — Quality Gates (Resolves ISSUE 6.11, observability gap)

### 21.1 Pytest Suite
- `backend/tests/test_api_image.py` — fixture image, asserts schema + verdict distribution.
- `backend/tests/test_api_text.py` — clickbait + neutral fixtures.
- `backend/tests/test_auth.py` — register/login/me/dup-409.
- `backend/tests/test_report.py` — auth-guarded, content-length > 0, valid PDF magic bytes.
- Target: **70% coverage on `backend/api/` and `backend/services/`.**

### 21.2 Frontend Tests
- Vitest + React Testing Library: `AuthForm`, `UploadZone` (rejects oversize), `VerdictCard` rendering, `HistoryPage` navigation.

### 21.3 GitHub Actions CI
- Workflow: `lint (ruff + eslint) → backend pytest → frontend vitest → frontend build`.
- Block PR merge on red.

### 21.4 Observability
- Add `prometheus_fastapi_instrumentator`. Expose `/metrics`.
- Sentry SDK for both backend (`sentry-sdk[fastapi]`) and frontend (`@sentry/react`). Gated by `SENTRY_DSN` env.
- Structured loguru JSON output in production mode.

---

## 13. Phase 22 — Platform Maturity (Resolves ISSUE 6.13, 6.19, 6.20, 6.21, 6.25)

### 22.1 Internationalization
- Wire `react-i18next` + `i18next-browser-languagedetector`.
- Extract all UI strings to `src/locales/{en,hi}.json`.
- Language switcher in navbar (English / हिन्दी baseline).

### 22.2 Dark Mode
- Add `data-theme="dark"` token set to `index.css` (graphite + indigo palette).
- Toggle in navbar, persisted to `localStorage`. Honors `prefers-color-scheme` initially.

### 22.3 Accessibility Audit
- Run `axe-core` against all routes; target 0 critical violations.
- Add `aria-label` to UploadZone, `role="status" aria-live="polite"` to ToastContainer, `<title>` to ScoreMeter SVG, focus rings to all interactive controls.
- Pair every color cue with text or icon label.

### 22.4 Privacy & Consent
- New `/privacy` page with explicit data-flow diagram and retention policy.
- First-upload modal: "Your media is processed locally. Keywords are sent to NewsData.io for source lookup. [Accept] [Decline]". Persist to `localStorage` + (when authed) backend `User.privacy_consent_at`.

### 22.5 Frontend Sanitization Util
- `src/utils/sanitize-text.js`: strip control chars, normalize unicode, cap at 10k chars. Used by `TextHighlighter` and OCR display.
- ESLint rule: ban `dangerouslySetInnerHTML` outside an explicit allowlist.

---

## 14. Risk Register (BUILD PLAN 2)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| FaceForensics++ download blocked / EULA issues | Medium | High (Phase 11) | Have DFDC fallback dataset ready |
| LLM API costs blow budget | High | Medium (Phase 12, 14) | Default to Gemini Flash (free tier), aggressive cache by SHA, opt-in only |
| Postgres migration introduces regressions | Medium | Medium (Phase 19) | Keep SQLite default; document Postgres as production-only path |
| Apple 3D animation tanks low-end devices | Medium | Low (Phase 18) | Honor `prefers-reduced-motion`; fallback to existing skeleton |
| Multi-lingual model bigger / slower than current BERT | High | Medium (Phase 13) | Quantize to int8 via `optimum`; lazy-load on first non-English request |
| VLM (Phase 14) inflates per-analysis latency by 4–8s | High | Medium | Run VLM in a background job, stream-update UI when ready |

---

## 15. Definition of Done (per phase)

Each phase ships only when:
1. Backend smoke test passes (`pytest -k phase_N`).
2. Frontend builds clean, no console errors on Chrome+Firefox.
3. Manual QA checklist signed off (added to `docs/qa/phase_N.md`).
4. Build log entry appended at top of `BUILD_PLAN2.md` matching `BUILD_PLAN.md` style.
5. ISSUES.md issue lines crossed out / marked `[RESOLVED in Phase N]`.

---

## 16. Indicative Timeline

| Week | Phase(s) | Key milestone |
|---|---|---|
| 1 | 15, 16 | Security hardening + Results page repair (lowest-risk, highest-impact bugs) |
| 2–4 | 11 | Image model retrain (longest pole; runs in background) |
| 3 | 12 | Explainability v2 (LLM, EXIF, ELA) |
| 4 | 13, 14 | Text NER + VLM breakdown + PDF re-skin |
| 5 | 17 | Video temporal + audio |
| 6 | 18, 20 | UI overhaul + landing page v2 |
| 7 | 19 | Cache, storage, jobs, indices |
| 8 | 21, 22 | Tests, CI, i18n, dark mode, a11y, privacy |

Total: ~8 weeks of focused work to graduate from MVP → defensible v1.0.

---

## 17. Progress Tracker

> Update the **Status** column as work proceeds. Use `Pending`, `In Progress`, or `Done`.

### Phase 11 — Image Model Replacement

| Subtask | Status |
|---|---|
| 11.1 Dataset Procurement (FFPP + DFDC) | Done |
| 11.2 Training pipeline (`dataset.py`, `train_convnext.py`, `calibrate.py`, `eval.py`) | Done (trained on Google Colab — ViT fine-tuned on FFPP c40, see `trained_models/Colab_ViT_Training.ipynb`) |
| 11.3 Backend wiring (FFPP ViT checkpoint integrated via `FFPP_MODEL_PATH`, weighted ensemble with EfficientNet + generic ViT — FFPP dominant when face present) | Done |
| 11.4 Smoke + regression (50-image curated set, MODEL_CARDS.md update) | Done |

### Phase 12 — Explainability v2

| Subtask | Status |
|---|---|
| 12.1 Grad-CAM++ upgrade + ELA service + heatmap 3-state toggle | Done |
| 12.2 EXIF extractor (`exif_service.py`, score adjustment, `EXIFCard.jsx`) | Done |
| 12.3 LLM explainability card (`llm_explainer.py`, `LLMExplainCard.jsx`, caching) | Done |

### Phase 13 — Text Pipeline Hardening

| Subtask | Status |
|---|---|
| 13.1 NER-based keyword extraction (spaCy, entity-first lookup) | Done |
| 13.2 Truth-override rule (cosine similarity, trusted-source cap) | Done |
| 13.3 Multi-lingual support (xlm-roberta, langdetect, Hindi OCR) | Done |

### Phase 14 — VLM Detailed Breakdown + PDF Re-skin

| Subtask | Status |
|---|---|
| 14.1 VLM component-score card (`vlm_breakdown.py`, `DetailedBreakdownCards.jsx`) | Done |
| 14.2 PDF template v2 (logo, donut chart, thumbnail, LLM text, nested tables) | Done |

### Phase 15 — Security Hardening

| Subtask | Status |
|---|---|
| 15.1 Auth on `/report` endpoints (ownership check, frontend redirect) | Done |
| 15.2 Rate limiting via slowapi (anon + authed limits, 429 toast) | Done |
| 15.3 JWT & config hardening (refuse default secret, CORS restrict, loguru rotation) | Done |

### Phase 16 — Results Page Rebuild + History Navigation

| Subtask | Status |
|---|---|
| 16.1 `ResultsPage.jsx` implementation (`AnalysisResultView` shared component) | Done |
| 16.2 History page clickable rows (`<Link>`, hover/focus, stopPropagation delete) | Done |
| 16.3 Auth rehydrate race fix (`authReady` boolean in `AuthContext`) | Done |
| 16.4 Sticky action bar ("Analyze Another" / "Generate PDF" / "Share") | Done |

### Phase 17 — Video Pipeline v2

| Subtask | Status |
|---|---|
| 17.1 Temporal consistency module (optical flow, blink rate, lip-sync, `temporal_score`) | Done |
| 17.2 Audio deepfake detection (`audio_service.py`, WavLM/wav2vec2, `AudioCard.jsx`) | Done |
| 17.3 Combined video verdict formula (visual + temporal + audio weights) | Done |

### Phase 18 — UI Polish v2

| Subtask | Status |
|---|---|
| 18.1 Apple-style 3D layer animation (`ProcessingAnimation.jsx`, framer-motion) | Done |
| 18.2 Glassmorphism + premium aesthetics (tokens, `.glass-panel`, Inter font) | Done |
| 18.3 Analyze page core overhaul (hero drag-zone, segmented controller, mesh bg) | Done |

### Phase 19 — Backend Platform

| Subtask | Status |
|---|---|
| 19.1 SHA-256 dedup cache (`media_hash` column, `CACHE_TTL_DAYS`) | Pending |
| 19.2 Object storage (`storage.py`, thumbnail generation, `media_path` in schema) | Pending |
| 19.3 Job queue (`POST /analyze/video` → 202, `GET /jobs/{id}`, frontend polling) | Pending |
| 19.4 DB indices + Alembic migrations + Postgres path docs | Pending |
| 19.5 Healthcheck split (`/health/live`, `/health/ready`, disable Analyze on 503) | Pending |

### Phase 20 — Landing Page v2

| Subtask | Status |
|---|---|
| 20.1 Moving impact cards (marquee carousel, framer-motion infinite loop) | Pending |
| 20.2 "Why DeepShield is Better" comparison grid | Pending |
| 20.3 FAQ accordion (8 questions) | Pending |
| 20.4 Live counter (`GET /stats/recent` endpoint) | Pending |
| 20.5 Trust badges (local processing, open-source, privacy-first) | Pending |

### Phase 21 — Quality Gates

| Subtask | Status |
|---|---|
| 21.1 Pytest suite (image, text, auth, report — 70% coverage target) | Pending |
| 21.2 Frontend tests (Vitest + RTL: AuthForm, UploadZone, VerdictCard, HistoryPage) | Pending |
| 21.3 GitHub Actions CI (lint → pytest → vitest → build) | Pending |
| 21.4 Observability (Prometheus, Sentry, structured loguru JSON) | Pending |

### Phase 22 — Platform Maturity

| Subtask | Status |
|---|---|
| 22.1 Internationalization (react-i18next, en/hi locale files, language switcher) | Pending |
| 22.2 Dark mode (token set, navbar toggle, localStorage + prefers-color-scheme) | Pending |
| 22.3 Accessibility audit (axe-core, aria labels, focus rings, color+text pairs) | Pending |
| 22.4 Privacy & consent page (data-flow diagram, first-upload modal, consent DB field) | Pending |
| 22.5 Frontend sanitization util (`sanitize-text.js`, ESLint `dangerouslySetInnerHTML` ban) | Pending |
