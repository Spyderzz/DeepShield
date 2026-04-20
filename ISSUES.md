# DeepShield Known Issues & Bug Tracker

This document tracks reported bugs, accuracy issues, and UI/UX shortcomings to be resolved in future development phases.

## 1. Image Analysis & Deepfake Detection

### 1.1 Model Inaccuracy & Poor Pre-trained Models
- **Issue:** The current ViT deepfake model (`prithivMLmods/Deep-Fake-Detector-v2-Model`) is highly inaccurate, frequently throwing false positives. A real vs. fake image of Barack Obama were both classified as fake, and even original, unedited photos straight from a user's camera phone are flagged as FAKE.
- **Context:** The model's training dataset was likely small or heavily biased toward "fake" if lighting, resolution, or compression artifacts lack studio quality. Current accuracy is unacceptably bad for a production environment.
- **Suggested Fix:** Discard the current model. We have officially procured the **FaceForensics++ dataset downloader script** (Saved to: `backend/scripts/download_ffpp.py`). 
  - Execute this script (e.g., `python download_ffpp.py ./ffpp_data -d all -c raw -t videos`) to pull the massive, diverse real-world datasets (Deepfakes, Face2Face, FaceSwap, etc.).
  - Use this data to fine-tune a superior state-of-the-art HuggingFace model (e.g., ConvNeXt or Swin Transformer) to permanently fix the false-positive detection flaws.

### 1.2 Unintuitive Visuals & Heatmap (Grad-CAM)
- **Issue:** The heatmap overlay generated on images is obscure and not easily understandable by a non-technical human.
- **Context:** The current Grad-CAM implementation pulls activations from the final ViT layer and overlays a standard JET colormap, which often highlights background elements or square patches instead of specific facial artifacts.
- **Suggested Fix:** Implement a clearer, visual deepfake artifact locator. Combine the heatmap with a technique like Error Level Analysis (ELA) to highlight manipulated pixels directly. Alternatively, use strict red/yellow bounding boxes around identified facial artifacts (like jawline clipping) to show users *exactly* where the manipulation is, rather than a generic heatmap splash.

### 1.3 Missing Human-Readable Explainability (LLM Integration)
- **Issue:** There is no textual explanation explaining *why* an image was classified as real or fake in plain English.
- **Context:** The Image Explainability currently only surfaces the raw heatmap base64 and deterministic artifacts (FFT/JPEG in JSON), but leaves the user guessing how to interpret them.
- **Suggested Fix:** Add an LLM Explainability Card to the UI. Integrate an LLM API (Gemini or OpenAI—the user will provide the key in `.env`). Feed the backend's JSON analysis payload (scores, artifact flags, metadata) directly to the LLM via prompt engineering, and have it return a short, friendly, synthesized paragraph explaining exactly why the media is real or fake to display on the frontend.

### 1.4 Missing Image Metadata (EXIF) Checking
- **Issue:** The system completely ignores the file's inherent metadata (EXIF data) which could serve as a massive confidence booster for "Real" images taken natively on smartphones or digital cameras.
- **Context:** Currently, files are stripped of metadata when loaded as base PIL images or processed via the ViT algorithm, discarding valuable camera signatures, GPS, and timestamp data.
- **Suggested Fix:** Use libraries like `exifread` or `Pillow`'s `_getexif()` to extract metadata before the image is modified. Factor EXIF data into the master authenticity score (e.g., presence of valid `Make`, `Model`, and `DateTimeOriginal` heavily penalizes the "Fake" probability).

### 1.5 Granular 'Detailed Breakdown' Metric Cards & PDF Integration
- **Issue:** The current reporting relies on an abstract global score and backend JSON variables, lacking the deeply granular, component-specific breakdowns seen in top-tier detection sites (like deepfakedetection.io).
- **Context:** User testing with competitor platforms shows that users expect detailed, categorized analysis cards. For example: "Skin Texture Analysis (35%)", "Lighting & Shadow Consistency (25%)", "Background Coherence (15%)", or "Natural Eye Reflections". Some of these require Vision-Language Models (VLMs) recognizing specific imagery (like a flag pin on a lapel).
- **Suggested Fix:** Utilize a Vision-Language Model API (like Gemini 1.5 Pro) to analyze the image and return a structured JSON breakdown of specific categories (Facial Symmetry, Skin Texture, Lighting, Background, Hands/Anatomy). 
  - Render these as distinct percentage-based metric cards in the UI under a "Detailed Breakdown" section.
  - Dynamically inject these precise component breakdowns, along with the high-level LLM Analysis Summary paragraph, directly into the `xhtml2pdf` Jinja2 template so the downloadable PDF reads exactly like the web UI's detailed report.

---

## 2. Text Analysis & News Lookup

### 2.1 Irrelevant Cached Sources
- **Issue:** Even when text is correctly classified as Real, the "credible sources" pulled by the NewsData.io API are sometimes irrelevant to the actual provided text.
- **Context:** The keywords are currently extracted using a basic word-frequency utility (`extract_keywords` in `text_service.py`), which might grab generic words (e.g., "said", "today", "people") instead of context-heavy named entities (e.g., "Barack Obama", "White House"). This causes the News API search to yield generic articles.
- **Suggested Fix:** Implement Named Entity Recognition (NER) (e.g., via `spacy` or a lightweight transformer) to extract proper nouns for the NewsData API query instead of frequency-based keywords.

### 2.2 Verifiable Truth Shown as "Fake" (False Positives)
- **Issue:** Real news with verifiable sources is sometimes incorrectly flagged as "FAKE".
- **Context:** The `fake_prob` mapping from `LABEL_0` (fixed in Phase 10) correctly links the model's output, meaning the underlying HuggingFace BERT model itself (`jy46604790/Fake-News-Bert-Detect`) is hallucinating false positives. Furthermore, the presence of verifiable sources from the News API does not currently *override* or reduce the model's fake score.
- **Suggested Fix:** Implement a "Truth Override" rule: if the News API returns articles from trusted domains (e.g., `reuters.com`) with a high similarity to the input text, it should dramatically slash the `fake_prob` score regardless of the BERT model's raw output.

---

## 3. UI / UX Design

### 3.1 Missing 3D "Apple-Style" Layer Animations
- **Issue:** The image processing animation is missing the requested premium, "Apple-style" fluid motion during analysis. The client explicitly requested a 3D isometric layer stack animation (reference: https://cdn.swipefile.com/2019/09/apple-presentation-photo-layers.png).
- **Context:** The processing state is currently just a basic skeletal spinner, violating the core directive to make the UX feel like an advanced next-gen application.
- **Suggested Fix:** Build a custom React `ProcessingAnimation` component using `framer-motion`. Detailed implementation requirements:
  - **The Setup:** Instead of one image, dynamically render 5–7 identical semi-transparent copies of the user's uploaded image.
  - **The Isometric Perspective:** Apply a parent wrapper style of `transform: rotateX(60deg) rotateZ(-45deg); transform-style: preserve-3d;` to tilt everything into an isometric view.
  - **The Staggered Expansion:** Using Framer Motion, translate each cloned layer upwards along the Z-axis (e.g., `translateZ(40px)`, `translateZ(80px)`) over a 1.5-second easing curve.
  - **The Visual Filters:** Apply different CSS filters to each floating layer to depict the ML pipeline "scanning" them:
    - Layer 1 (Bottom): Base original image.
    - Layer 2: `filter: grayscale(100%) contrast(150%)` (representing structural/artifact analysis).
    - Layer 3: `filter: hue-rotate(90deg) blur(2px)` (representing heatmap extraction).
    - Layer 4: `mix-blend-mode: overlay` with a scanning glow bar.
  - **The Polish:** Include a scanning laser beam moving across the top layer, and use spring physics (not linear) so the layers bounce softly into their expanded isometric stack while the backend API processes the result.

### 3.2 Basic / Unprofessional Aesthetics
- **Issue:** The UI (especially the Auth pages) feels too generic, heavily "AI-generated", and lacks a liquid-smooth, professional polish.
- **Context:** Standard CSS/Tailwind utilities were used without a cohesive, state-of-the-art design language. The Login/Register pages are incredibly basic.
- **Suggested Fix:** Refactor the UI layout referencing top-tier Dribbble/Figma designs (e.g., https://refero.design). Add subtle backdrop-blur (glassmorphism), refined typography (e.g., SF Pro or Inter), soft multi-layered drop shadows, and micro-interactions on hover/click to make the interface feel premium and unified. The Login/Register screens should undergo a massive visual overhaul with modern themed graphics.

### 3.3 Missing Trust Signals & Engagement Content (Landing Page)
- **Issue:** The current landing page lacks credibility, social proof, and engaging storytelling to convince users that the tool is legitimate and superior to competitors.
- **Context:** The HomePage currently acts mostly as a functional dashboard entry point rather than a polished SaaS marketing page.
- **Suggested Fix:** Enhance the Landing Page with the following components:
  1. **Moving Impact Cards:** Implement a smooth animated marquee or interactive carousel showing real-world deepfake impact stories (e.g., identity theft, financial fraud, political manipulation) to establish urgency.
  2. **"Why DeepShield is Better" Section:** A comparison grid/feature highlight explicitly showing the system's competitive edge (e.g., Multi-modal support, Local EXIF processing, Open-Source API integrations).
  3. **FAQ Section:** An accordion-style Frequently Asked Questions section covering privacy (data retention), accuracy rates, and accepted file formats.

### 3.4 Poor Results Navigation & Workflow UX
- **Issue:** After an analysis is complete, the "Analyze Another Image/Article" button is buried at the very bottom of the results page, requiring excessive scrolling.
- **Context:** The long vertical dump of results cards forces the user to manually scroll back simply to upload another file, breaking the workflow loop.
- **Suggested Fix:** Implement modern UX placement for continuous workflow:
  1. **Sticky Action Bar:** Instead of pushing buttons to the bottom, lock the primary actions ("Analyze Another", "Generate PDF") to a sticky floating bar (FAB) at the bottom or top of the viewport.
  2. **Tabbed Navigation:** Condense the long vertical scroll by putting advanced details (like Sensationalism or Fact Check) into navigable tabs.
  3. **Contextual Upload Zone:** Place a small mini-uploader to the side or top of the results page so the next image can be dragged-and-dropped instantly without needing a button click to go backwards.

### 3.5 Analyze Page Core UI Overhaul
- **Issue:** The main Analyze Page heavily lacks professional-grade layout formatting; it relies on very basic generic boxes which degrades the feeling of being a state-of-the-art AI tool.
- **Context:** Currently, the upload forms, toggles, and processing states are functionally stacked but not structurally unified or stylized.
- **Suggested Fix:** Radically elevate the Analyze Page's aesthetic. Incorporate modern drag-and-drop dashboard patterns:
  1. A centralized, massive, and animated dashed drag-and-drop zone with liquid-physics hover states.
  2. Implement segmented controllers (like Apple's iOS toggles) for switching between Image/Video/Text/Screenshot rather than basic buttons or tabs.
  3. Wrap the primary forms in unified glassmorphism panels (blurred translucent cards) floating over a stylized dark, gradient-mesh background.

---

## 4. PDF Generation & Authentication Bugs

### 4.1 Missing Auth Guard on PDF Downloads
- **Issue:** The PDF report can currently be downloaded even if the user is not logged in.
- **Context:** In `AnalyzePage.jsx` or backend `report.py`, the download endpoint `GET /report/{id}/download` likely lacks a dependency on `get_current_user`, or the frontend allows the flow to proceed without verifying local auth state.
- **Suggested Fix:** (1) Add frontend routing guards so clicking "Download Report" throws a toast and redirects unauthenticated users to `/login`. (2) Add `user: User = Depends(get_current_user)` to the backend `/report/*` routes to secure them.

### 4.2 Corrupted / Empty PDF Output
- **Issue:** The downloaded PDF report is completely empty and Adobe Acrobat cannot open it (error).
- **Context:** The transition from WeasyPrint to `xhtml2pdf` likely broke formatting. If `pisa.CreatePDF()` receives bad HTML rendering (e.g., broken asset paths, unsupported CSS properties like flexbox), it outputs a corrupted 0-byte or invalid chunk instead of a valid `%PDF` binary.
- **Suggested Fix:** Debug backend `report_service.py`. Capture `pisa.CreatePDF` error logs (`pisa.err`), replace modern CSS (`flex`, `grid`) in the Jinja2 template with legacy nested `<table>` structures (which `xhtml2pdf` requires), or switch back to an active PDF engine like Playwright/Puppeteer or `pdfkit`. 

---

## 5. Advanced Technical Deficits & Missing Architectures

### 5.1 No Audio/Voice Deepfake Detection
- **Issue:** The system entirely ignores the audio track of uploaded video files, presenting a massive vulnerability.
- **Context:** Modern deepfakes often combine real video footage with AI-cloned voice audio (e.g., ElevenLabs). The current Video pipeline only samples visual frames via MediaPipe/ViT.
- **Suggested Fix:** Build out an Audio Pipeline. Extract the `.wav` audio track using `ffmpeg-python` and pass it through a dedicated audio deepfake model (e.g., Wav2Vec2 or Whisper for acoustic artifact variance) to score voice authenticity.

### 5.2 Video Pipeline Lacks Temporal Consistency
- **Issue:** Video deepfake detection is inherently flawed because it treats the video as isolated, static images.
- **Context:** The pipeline extracts `n=16` frames and classifies each via the ViT image model. It misses motion-based anomalies like micro-flickering, unnatural eye-blinking rates, or lip-sync mismatch.
- **Suggested Fix:** Implement a sequence-based architecture. Instead of (or alongside) isolated frame analysis, feed the feature embeddings into an LSTM/GRU, or use a 3D-CNN (like I3D) that evaluates behavior and motion over time.

### 5.3 Missing Multi-Lingual Support (Crucial for India)
- **Issue:** Fake news/Deepfakes heavily propagate in regional languages, but the platform is hardcoded strictly for English.
- **Context:** `EasyOCR` is initialized with `['en']`, and `Fake-News-Bert-Detect` is an English-only NLP model. Hindi, Tamil, or Bengali screenshots/text will fail entirely.
- **Suggested Fix:** 
  1. Add regional language codes to EasyOCR initialization (e.g., `['en', 'hi', 'mr', 'ta']`).
  2. Swap the English BERT model for a robust Multi-lingual Transformer (e.g., `xlm-roberta-base` fine-tuned for fake news).

### 5.4 No Abuse Protection / Rate Limiting (DDoS Vulnerability)
- **Issue:** The API endpoints allow unrestricted, massive file uploads continuously.
- **Context:** Video processing is extremely CPU-heavy. A malicious user could crash the backend instantly by sending concurrent 100MB video payloads.
- **Suggested Fix:** Implement rate limiting using `slowapi` on FastAPI. Restrict unauthenticated users to 5 requests/hour, and authenticated users to 50 requests/hour to prevent server exhaustion.

### 5.5 Missing Global Media Caching (Performance)
- **Issue:** Viral fakes (e.g., a trending manipulated political image) will be uploaded thousands of times, forcing the server to recalculate the exact same ViT inference and News API lookup repeatedly.
- **Context:** The system recalculates every file from scratch regardless of previous scans.
- **Suggested Fix:** Implement SHA-256 file hashing upon upload. Before processing, check the DB for an existing `AnalysisRecord` with that exact hash. If found, return the cached Explainability object instantly (sub-10ms response time vs. 4-second CPU load).

---

## 6. Newly Discovered Issues (End-to-End Audit, 2026-04-15)

### 6.1 ResultsPage is a Placeholder Stub
- **Issue:** [frontend/src/pages/ResultsPage.jsx](frontend/src/pages/ResultsPage.jsx) only renders `<h2>Results</h2>` plus the URL `id`. No history item is actually viewable in detail after the analysis is dismissed.
- **Context:** The route `/results/:id` is registered in `App.jsx`, but no fetch is performed against `GET /history/{id}` and no result components are mounted.
- **Suggested Fix:** Implement full results rendering: fetch the stored payload via `getHistoryItem(id)`, then render the same VerdictCard / ScoreMeter / explainability stack used in `AnalyzePage`. Make HistoryPage rows clickable links that route to `/results/:id`.

### 6.2 History Rows Are Not Clickable / No "View" Action
- **Issue:** [frontend/src/pages/HistoryPage.jsx](frontend/src/pages/HistoryPage.jsx) renders rows with only a Delete button — there is no way to re-open a past analysis.
- **Context:** Combined with 6.1, all stored history is effectively write-only from the UI's perspective; the user can see scores but never re-examine the heatmap, sources, or indicators.
- **Suggested Fix:** Wrap each row in a `<Link to={'/results/' + it.id}>` (or add an explicit "View" button) and pair with a working ResultsPage.

### 6.3 PDF Report Endpoints Have Zero Authorization
- **Issue:** [backend/api/v1/report.py](backend/api/v1/report.py) uses neither `get_current_user` nor `optional_current_user`. Any anonymous request (or any logged-in user with another user's analysis ID) can trigger PDF generation and download.
- **Context:** This is the backend-side root cause behind ISSUE 4.1. Reports also have no `user_id` ownership check against the underlying `AnalysisRecord`.
- **Suggested Fix:** Add `user: User = Depends(get_current_user)` to `POST /report/{id}`, `GET /report/{id}/download`, and `POST /report/cleanup`. Verify `record.user_id == user.id` before serving.

### 6.4 Missing Backend Rate Limiting / Abuse Protection
- **Issue:** `main.py` registers no rate-limit middleware. Combined with 6.3, anonymous users can trigger expensive ViT + Grad-CAM + EasyOCR + Jinja2/PDF pipelines unrestricted (matches ISSUE 5.4 but adds the PDF + report-cleanup endpoints to the attack surface).
- **Suggested Fix:** Add `slowapi` middleware with per-IP and per-user buckets. Restrict report generation more aggressively (e.g., 10/hour) since it disk-writes.

### 6.5 SQLite + No DB Indices for History/Reports
- **Issue:** `deepshield.db` is committed/used as production storage, yet there are no explicit DB indices on `AnalysisRecord.user_id`, `AnalysisRecord.created_at`, or `Report.analysis_id`.
- **Context:** History queries `WHERE user_id=? ORDER BY created_at DESC LIMIT 50` will table-scan as records grow. SQLite is also single-writer — concurrent video uploads will serialize.
- **Suggested Fix:** Add explicit `Index('ix_record_user_created', user_id, created_at.desc())` and `Index('ix_report_analysis', analysis_id)`. Plan a Postgres migration path for production.

### 6.6 JWT Secret Defaults to "change-me-in-production"
- **Issue:** [backend/config.py:36](backend/config.py#L36) hard-defaults `JWT_SECRET_KEY="change-me-in-production"`. If `.env` is missing, all production tokens become trivially forgeable.
- **Suggested Fix:** Refuse to start when `DEBUG=False` and `JWT_SECRET_KEY` is the default; require minimum 32 random chars. Add `secrets.token_urlsafe(48)` snippet to setup docs.

### 6.7 Permissive CORS, allow_credentials=True, allow_methods=*
- **Issue:** `main.py` sets `allow_credentials=True` together with `allow_methods=["*"]`/`allow_headers=["*"]`. Combined with the static origin list this works today, but it's a footgun the moment someone adds a wildcard.
- **Suggested Fix:** Restrict methods to `["GET","POST","DELETE","OPTIONS"]` and headers to the actual list (`Authorization`, `Content-Type`). Reject wildcard origins at config-load when credentials are on.

### 6.8 Unrestricted Logger PII Leakage
- **Issue:** `auth.py` and `analyze.py` log full email/user_id and analysis verdicts via `loguru` with no scrubbing. `text_service.classify_text` logs partial content via classifier label. Logs are unrotated.
- **Suggested Fix:** Configure `loguru.add(rotation="10 MB", retention="7 days", compression="zip")`. Scrub email→`u***@d***` in info logs. Move sensitive details to DEBUG.

### 6.9 No Background Task Queue — Long Requests Block Workers
- **Issue:** Video analysis (16 frames × ViT + FaceMesh) and PDF generation run synchronously inside the request handler. A single uvicorn worker is fully blocked for 5–30 seconds; the frontend has only a passive spinner with no real progress.
- **Suggested Fix:** Move heavy pipelines to `BackgroundTasks` or Celery/Redis with a job-id polling endpoint (`GET /analyze/{job_id}/status`). Frontend `PipelineVisualizer` would then show real backend stage progress instead of guessed timing.

### 6.10 No Persistent Object Storage for Uploaded Media
- **Issue:** Uploads are read into memory or written to a tempfile and immediately deleted. The original media is never retained, which prevents (a) re-running newer models on past uploads, (b) showing the original image alongside historical results, and (c) admin audit.
- **Suggested Fix:** Stream uploads to local `media/{sha256[:2]}/{sha256}.{ext}` (or S3-compatible). Store the hash on `AnalysisRecord`. Combined with ISSUE 5.5 this also unlocks the dedup cache.

### 6.11 No Test Suite — `backend/tests/` Is Empty
- **Issue:** [backend/tests/](backend/tests/) contains only `__init__.py`. All "smoke tests" live in ad-hoc scripts in `backend/scripts/`. No CI gates regressions.
- **Suggested Fix:** Add `pytest` + `httpx.AsyncClient` integration tests for each endpoint with fixture media files. Wire a GitHub Actions workflow to run lint + tests on every push.

### 6.12 Frontend Has No Loading-Skeleton on Initial Auth Rehydrate
- **Issue:** `AuthContext.fetchMe` runs on mount; until it resolves, `isAuthed` is `false` and protected pages (HistoryPage) bounce the user to `/login` even when they have a valid token. Race-condition logout on every refresh.
- **Suggested Fix:** Track `authReady` boolean; render a global splash/skeleton until `fetchMe` settles, then evaluate guards.

### 6.13 No Frontend Input Sanitization for Text Analysis Display
- **Issue:** `TextHighlighter` and the OCR `extracted_text` panel render user/extracted strings that originate from arbitrary screenshots. While React escapes by default, any future `dangerouslySetInnerHTML` or copy-paste link rewrites could open XSS.
- **Suggested Fix:** Add a `sanitize-text.js` util (strip control chars, normalize unicode, cap length) before any formatted rendering, and add an ESLint rule banning `dangerouslySetInnerHTML` outside an allowlist.

### 6.14 NewsData.io Failure Modes Silently Return Empty Arrays
- **Issue:** `news_lookup.search_news_full` swallows HTTP / timeout / quota errors and returns empty `trusted_sources`/`contradicting_evidence`. The UI then implies "no corroborating sources" (suggesting it's fake) when the real cause is API outage / missing key.
- **Suggested Fix:** Surface `news_status` field (`ok` / `no_key` / `quota_exceeded` / `network_error`) in the response. Frontend should render an explicit "Source verification unavailable" badge instead of pretending zero results.

### 6.15 Heatmap Generation Failures Silently Drop the Heatmap
- **Issue:** [backend/api/v1/analyze.py:81](backend/api/v1/analyze.py#L81) catches all heatmap exceptions and returns `heatmap_base64=""`. Frontend `HeatmapOverlay` then renders blank/broken.
- **Suggested Fix:** Add a `heatmap_status` enum (`ok`/`failed`/`skipped_no_face`); render a friendly "Heatmap unavailable for this image" panel instead of an empty `<img>`.

### 6.16 Score Weighting & Trust Scale Are Not User-Configurable / Not Documented in UI
- **Issue:** The 70/20/10 (text) and 65/20/10/5 (screenshot) weighted formulas are hardcoded magic numbers in `analyze.py`. The user has no way to inspect them, and they are absent from AboutPage.
- **Suggested Fix:** Move weights to `config.py`, expose them via `GET /config/scoring`, and render a "Scoring methodology" panel on the explainability card.

### 6.17 Video Pipeline: No Frame Thumbnails Persisted
- **Issue:** `FrameTimeline` shows colored bars but no actual thumbnails of the suspicious frames. Users can't visually verify which frame the model flagged.
- **Suggested Fix:** Save each sampled frame as `media/frames/{record_id}/{idx}.jpg` and return URLs in `frames[*].thumbnail_url`. Display thumbnail on hover.

### 6.18 No Healthcheck / Readiness Distinction
- **Issue:** `/health` returns OK even before models have finished preloading; frontend can fire requests that hang for 30+ seconds during cold start.
- **Suggested Fix:** Split `/health/live` (process up) and `/health/ready` (models loaded). Frontend gates the Analyze button on readiness.

### 6.19 No Dark Mode / Theme Toggle
- **Issue:** Only a single light-only theme is shipped. Users on OLED / dark-environment expect a toggle on a "premium" product.
- **Suggested Fix:** Add `data-theme="dark"` token set to `index.css`, persist via `localStorage`, and add a navbar toggle.

### 6.20 Accessibility: Missing aria-* and Keyboard Navigation
- **Issue:** Custom upload zone, score arc, segmented switcher, and toasts have no `role`/`aria-live` annotations; the score arc SVG has no `<title>`. Color-only verdict signaling fails WCAG AA.
- **Suggested Fix:** Audit with `axe-core`. Add `aria-label` to upload zone, `role="status" aria-live="polite"` to toasts, `<title>` to SVGs, and pair every color cue with an icon or text label.

### 6.21 No Internationalization Scaffolding
- **Issue:** All UI strings are hardcoded English literals scattered across components. Even if backend gains multi-lingual support (ISSUE 5.3), the frontend can't follow.
- **Suggested Fix:** Wire `react-i18next` with `en.json` as baseline; extract strings into namespaced keys. Lays groundwork for Hindi/Tamil/Bengali pages.

### 6.22 Hardcoded Image Model in Settings (No Environment Override Tested)
- **Issue:** Despite being in `Settings`, swapping `IMAGE_MODEL_ID` requires re-fetching weights and there is no model-switching test or fallback path. If HuggingFace 404s the model, the entire backend crashes at startup with `PRELOAD_MODELS=true`.
- **Suggested Fix:** Wrap `model_loader` in try/except → log error and lazy-load on demand; add `/health/ready` to surface model load failures.

### 6.23 No Per-Pipeline Confidence Calibration
- **Issue:** Image, video, text, and screenshot scores all use the same `TRUST_SCALE` thresholds (70/40 cutoffs), but each model has wildly different calibration (BERT fake-news is over-confident; ViT deepfake is under-confident on real photos per ISSUE 1.1).
- **Suggested Fix:** Calibrate each pipeline separately with isotonic regression on a held-out validation set; expose per-pipeline thresholds in config.

### 6.24 Pisa/xhtml2pdf Has No Logo, Branding, or Charts in PDF
- **Issue:** Even when the PDF generates correctly (ISSUE 4.2 fixed), the output is plain HTML with no DeepShield logo, no chart of the score arc, no thumbnail of the analyzed image — looks like a debug dump, not a report.
- **Suggested Fix:** Embed a base64 SVG logo header, render a static-PNG donut chart of the score (matplotlib → base64), and inline the analyzed image (resized to ~400px) at the top of the PDF.

### 6.25 No Privacy Policy / Data Retention Disclosure
- **Issue:** Users upload photos/screenshots that may contain faces, IDs, or chat content. There is no privacy page, no opt-in disclosure that media is sent to HuggingFace-hosted models (locally cached after first run, but the implication is unclear), and no mention of NewsData.io leak.
- **Suggested Fix:** Add `/privacy` route with explicit data-flow diagram: "Your media never leaves this server. Models run locally. Text keywords are sent to NewsData.io for source lookup." Persist the user's consent on first upload.
