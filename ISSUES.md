# DeepShield Known Issues & Bug Tracker

This document tracks reported bugs, accuracy issues, and UI/UX shortcomings to be resolved in future development phases.

## 1. Image Analysis & Deepfake Detection

### 1.1 Model Inaccuracy & Poor Pre-trained Models
- **Issue:** The current ViT deepfake model (`prithivMLmods/Deep-Fake-Detector-v2-Model`) is highly inaccurate, frequently throwing false positives. A real vs. fake image of Barack Obama were both classified as fake, and even original, unedited photos straight from a user's camera phone are flagged as FAKE.
- **Context:** The model's training dataset was likely small or heavily biased toward "fake" if lighting, resolution, or compression artifacts lack studio quality. Current accuracy is unacceptably bad for a production environment.
- **Suggested Fix:** Discard the current model. Research and integrate significantly better state-of-the-art pre-trained models from HuggingFace (e.g., modern ConvNeXt, Swin Transformers, or specialized Deepfake Detection challenges models) that are trained on massive, diverse real-world datasets (like FaceForensics++ or Celeb-DF).

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
