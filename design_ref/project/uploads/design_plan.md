# DeepShield — Frontend Design Plan

> **Purpose:** Full UI/UX redesign spec. Feed to `frontend-design` + `ui-ux-pro-max` skills.
> **Scope:** Phases 16, 18, 20, 22 of [BUILD_PLAN2.md](BUILD_PLAN2.md) + all result cards added in Phase 12–14.
> **Inspiration:** [DeepTrace](https://github.com/DevyanshBhattacharya/DeepTrace) (dashboard-first, trust-focused SaaS).
> **Authoring date:** 2026-04-20
> **Owner:** Spyderzz

---

## 0. Design Thesis

DeepShield is a **trust instrument**. Every surface must read as: *calm, forensic, evidence-rich*. Not playful. Not alarmist. The aesthetic should resemble a cross between **Linear** (precision), **Vercel dashboards** (density + clarity), **Stripe** (data trust), and **Apple iOS 17 glass** (depth + premium feel). DeepTrace supplies the mental model: landing → dashboard → result.

**Three non-negotiables:**
1. **Evidence first.** LLM paragraph + verdict visible above the fold on results.
2. **Motion with purpose.** 3D processing animation is signature — everything else is subtle.
3. **Accessibility is a feature.** AA contrast, reduced-motion, keyboard-first.

---

## 1. Design Tokens

### 1.1 Color System (dual-theme)

**Light (default)** — forensic lab aesthetic, cool neutrals.

| Token | Value | Use |
|---|---|---|
| `--bg-canvas` | `#F7F8FB` | Page background |
| `--bg-surface` | `#FFFFFF` | Card background |
| `--bg-elevated` | `#FFFFFF` | Modal, popover |
| `--bg-muted` | `#F1F3F8` | Sunken panels, inputs |
| `--border-subtle` | `#E6E8EF` | Card divider |
| `--border-strong` | `#C9CED9` | Focus ring base |
| `--text-primary` | `#0B0F1A` | Headings |
| `--text-secondary` | `#4A5268` | Body |
| `--text-tertiary` | `#8892A6` | Captions |
| `--brand-500` | `#3D5AFE` | Primary action (deep indigo) |
| `--brand-600` | `#2E3FD1` | Hover |
| `--brand-50` | `#EEF1FF` | Brand wash |
| `--accent-teal` | `#00BFA5` | Safe / real |
| `--accent-amber` | `#FFB300` | Suspicious |
| `--accent-crimson` | `#E53935` | Fake / danger |
| `--glass-bg` | `rgba(255,255,255,0.65)` | `.glass-panel` |
| `--glass-border` | `rgba(255,255,255,0.45)` | Glass edge |
| `--glass-blur` | `18px` | backdrop-filter |

**Dark** — graphite + indigo, emits premium product feel.

| Token | Value |
|---|---|
| `--bg-canvas` | `#0A0D14` |
| `--bg-surface` | `#11151F` |
| `--bg-elevated` | `#161B28` |
| `--bg-muted` | `#1B2030` |
| `--border-subtle` | `#242A3A` |
| `--text-primary` | `#F5F7FA` |
| `--text-secondary` | `#A8B2C7` |
| `--brand-500` | `#6C7DFF` |
| `--glass-bg` | `rgba(22,27,40,0.55)` |

Mesh-gradient backdrop for hero + auth: radial blobs `brand-500 → accent-teal → transparent` at 20% opacity, animated via 40s CSS keyframe.

### 1.2 Typography

- **Display / Headings:** `Inter Display` (fallback `Inter`) — weights 600, 700.
- **Body:** `Inter` — 400, 500.
- **Mono (scores, hashes, EXIF):** `JetBrains Mono` — 500.

Scale (rem): 0.75 / 0.875 / 1 / 1.125 / 1.25 / 1.5 / 1.875 / 2.5 / 3.25 / 4.5. Line-height 1.5 body, 1.15 display. Tracking `-0.02em` on display.

### 1.3 Radius & Elevation

- Radius: `sm 6 / md 10 / lg 14 / xl 20 / 2xl 28 / full`.
- Shadows — multi-layer, soft:
  - `--shadow-1`: `0 1px 2px rgba(10,15,30,0.04), 0 2px 6px rgba(10,15,30,0.04)`
  - `--shadow-2`: `0 2px 4px rgba(10,15,30,0.05), 0 12px 28px rgba(10,15,30,0.08)`
  - `--shadow-glow-brand`: `0 0 0 1px rgba(61,90,254,0.25), 0 8px 24px rgba(61,90,254,0.25)`

### 1.4 Motion

- Easing: `--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)`, `--ease-spring` via `framer-motion` (`stiffness 220, damping 26`).
- Durations: `fast 140ms`, `base 240ms`, `slow 420ms`, `hero 900ms`.
- Honor `prefers-reduced-motion`: disable all non-essential transitions, keep opacity only.

---

## 2. Component Library (atomic → molecular)

Reusable primitives. Build under `frontend/src/components/ui/`.

| Primitive | Notes |
|---|---|
| `Button` | variants: `primary`, `secondary`, `ghost`, `danger`, `glass`. sizes: sm/md/lg. Loading state with spinner. |
| `Card` | `default` / `glass` / `elevated`. Slots: header, body, footer. |
| `Input`, `Textarea`, `Select` | floating-label variant + inline validation. |
| `Badge` | semantic: safe/warning/danger/info/neutral. With optional dot + icon. |
| `Tabs` | iOS-style segmented pill (animated `layoutId` background). |
| `Toggle` | 3-state variant for Heatmap / ELA / Boxes. |
| `Tooltip` | radix-style, 180ms fade+translate. |
| `Dialog`, `Drawer` | focus-trap, esc-close, scroll-lock. |
| `Progress`, `ProgressRing` | ring used in ScoreMeter + donut PDF chart. |
| `Skeleton` | shimmer, respects reduced motion. |
| `Toast` | stacked top-right, auto-dismiss, aria-live. |
| `DropZone` | drag-over liquid SVG morph, keyboard accessible. |
| `EmptyState` | illustration + CTA. |

All primitives accept `className` and forward ref. Icon set: **Lucide** (consistent stroke).

---

## 3. Layout System

- **Shell:** persistent `Navbar` (h 64) + optional `Sidebar` (240) on authed pages + `Footer`.
- **Navbar** (glass, sticky): logo · segmented nav (Analyze / History / About) · right cluster (language picker · theme toggle · auth avatar menu).
- **Content container:** max-width `1240px`, padding `x-6 y-10`.
- **Grid:** 12-col, 24px gutter desktop, 16px tablet, single-col mobile.
- **Breakpoints:** `sm 640 · md 768 · lg 1024 · xl 1280 · 2xl 1536`.

---

## 4. Page Specs

### 4.1 Landing / HomePage (Phase 20)

**Above-the-fold hero**
- Left 60%: headline "Detect deepfakes before they detect you." + subline + dual CTA (`Analyze now` → /analyze, `How it works` → scroll).
- Right 40%: live **3D layer animation** preview — stack of translucent face frames with scanning laser, looping. Same component as processing state, in demo mode.
- Background: dark mesh-gradient canvas with faint grid, parallax on scroll.

**Section 2 — Moving Impact Cards** (marquee)
- Infinite `framer-motion` loop, 6 real-world deepfake incidents. Each card: headline, date, source logo, verdict badge. Hover pauses row.

**Section 3 — Pipeline explainer**
- 4 vertical cards (Image · Video · Text · Screenshot). Each has micro-lottie + 3-bullet explainer + "Run sample" link.

**Section 4 — "Why DeepShield"** comparison grid
- 3 columns (DeepShield / Reality Defender / Manual). Green check / red cross matrix. DeepShield column highlighted with glow border.

**Section 5 — Trust strip**
- Live counter (X analyses / 24h) · Badges (Local-first · Open models · No media retention) · Trusted-source logos (Reuters, AP, BBC as partners in lookup).

**Section 6 — FAQ accordion** (8 Q).

**Section 7 — CTA band + Footer**.

### 4.2 AnalyzePage (Phase 18.3 overhaul)

- **Hero drop-zone:** centered, 640×420, glass panel over mesh-gradient. Liquid SVG blob morphs on drag-over (brand → teal). Accepts drop, paste, click.
- **Media type switcher:** iOS segmented control (Image · Video · Text · Screenshot) just under drop-zone; animated pill, keyboard-arrow-nav.
- **Options row:** checkbox `Cache result`, URL input (for image URL), language picker (OCR langs).
- **Processing state:** drop-zone is replaced in-place by `ProcessingAnimation` (see §5.1) + `PipelineVisualizer` stepper (stages from `/jobs/{id}`: Upload → Preprocess → Model → Heatmap → LLM → Done).
- **Result view:** see §4.3.

### 4.3 Results view (`AnalysisResultView` — shared Phase 16.1)

Rendered both inline on Analyze and on dedicated `/results/:id`.

Order of cards (top → bottom):

1. **VerdictCard** — big glass card. Left: large verdict label (REAL / SUSPICIOUS / FAKE) with traffic-light icon; ScoreMeter ring (0–100). Right: LLM paragraph (2–3 lines). Below: 3 key-signal bullets from LLM.
2. **MediaPreviewCard** — thumbnail + filename + SHA-8 + `cached` badge if applicable. For video: frame timeline with `FrameTimeline`. For text: reformatted text block with highlights.
3. **DetailedBreakdownCards** (Phase 14.1) — 6-up responsive grid (facial_symmetry, skin_texture, lighting, background, anatomy, context). Each card: percentage ring + label + expand-on-click notes drawer.
4. **HeatmapOverlay** (Phase 12.1) — 3-state toggle pill (Heatmap / ELA / Boxes) top-right. Image underneath with overlay at 65% alpha. Slider controls alpha. Status chip reflects `heatmap_status`.
5. **EXIFCard** (Phase 12.2) — two-column key/value list. Green ✓ on trusted fields, red ⚠ on "Software: Photoshop". Footer shows score adjustment.
6. **IndicatorCards** — chips for each `ArtifactIndicator`.
7. **SourcePanel + ContradictionPanel** — for text. Each source row: favicon, domain, trust weight bar, similarity %, headline, "Open" link.
8. **Audio Card** (Phase 17.2) — waveform via `wavesurfer.js`, authenticity ring, WavLM model tag.
9. **Temporal Consistency card** (video) — mini line chart of per-frame temporal score.
10. **ReportDownload** — PDF button (disabled with tooltip if unauthed).

**Sticky action bar** (Phase 16.4) bottom: `Analyze another` · `Generate PDF` · `Share` · `Copy link`. Glass pill, 72px tall, slides up after results load.

### 4.4 ResultsPage `/results/:id` (Phase 16.1)

- On mount: `GET /history/{id}`. Loading → full-page skeleton mirroring result card stack. 404 → illustrated empty state with "Back to History".
- Renders `<AnalysisResultView/>`.

### 4.5 HistoryPage (Phase 16.2)

- Top bar: search input · filter chips (All · Image · Video · Text · Screenshot · Real · Fake) · date-range picker.
- Data grid: dense table on desktop (`Thumb · Type · Verdict · Score · Date · Actions`), card grid on mobile. Each row = `<Link to=/results/:id>`, Delete is trailing icon button with `stopPropagation`, confirm dialog.
- Empty state: "No analyses yet" + CTA.
- Pagination: infinite scroll (IntersectionObserver).

### 4.6 Login / Register (Phase 18.2)

- Split layout: left 50% mesh-gradient canvas with animated brand mark + rotating testimonials/quotes; right 50% glass form card centered.
- Form: floating-label inputs, inline validation, password strength meter, `show/hide` eye toggle. Submit = loading state on button.
- Social auth placeholder row (future).

### 4.7 About + Privacy + FAQ (Phase 22.4)

- Long-form, 720px reading column. Hero headline + TOC sticky sidebar. Data-flow SVG diagram inline. `/privacy` + consent modal on first upload.

### 4.8 NotFoundPage

- Glitched "404" with subtle face-warp shader illustration. Back-home CTA.

---

## 5. Signature Interactions

### 5.1 Processing Animation (Phase 18.1)

File: `components/common/ProcessingAnimation.jsx`.

- Parent: `perspective: 1400px; transform-style: preserve-3d; transform: rotateX(58deg) rotateZ(-42deg)`.
- 6 translucent clones of uploaded image, stacked with `translateZ` gap `28px`.
- `framer-motion` staggered entrance (`delay 80ms * i`, spring).
- Per-layer filters: L1 grayscale+contrast (artifact pass), L2 hue-rotate 180 + blur(2px) (heatmap pass), L3 invert + overlay blend (ELA pass), L4 red channel isolate (face mesh), L5 identity, L6 ghost outline.
- Horizontal scanning laser (2px, `brand-500 → transparent`) sweeping top-to-bottom, 2.4s loop.
- Ambient brand-color glow behind stack, pulsing 3s.
- Reduced-motion fallback: static stack, no sweep.

### 5.2 Verdict Reveal

- ScoreMeter ring counts up 0 → score over 900ms `ease-out-expo`.
- Verdict label fades in + slides 12px up after ring completes.
- LLM paragraph streams in word-by-word (60ms) if backend streams; otherwise fade.

### 5.3 Segmented Controller

- Underlying animated pill uses `layoutId="seg-pill"` so switching glides between tabs.

### 5.4 Drop-zone liquid morph

- Idle: rounded rect. Drag-over: SVG `<path>` animates between 4 pre-authored blob paths via `framer-motion`. Brand gradient stroke, glow increases.

### 5.5 Card hover

- `translateY(-2px)` + shadow step from `--shadow-1` → `--shadow-2`, 180ms.

---

## 6. Accessibility (Phase 22.3)

- Contrast: AA minimum, AAA for body. Audit with `axe-core` on every route.
- Focus rings: 2px `brand-500` with 2px offset, never removed.
- Keyboard: full tab traversal; `/` focuses search; `Esc` closes dialogs; arrow keys in segmented control.
- Screen reader: `aria-live="polite"` on toasts and stage stepper; `role="img"` + description on ScoreMeter SVG; `<title>` on all SVGs.
- Never color-only: pair verdict color with icon + text (✓ Real / ! Suspicious / ✗ Fake).
- Reduced motion: global query disables transform/parallax; keep opacity fades.

---

## 7. Internationalization (Phase 22.1)

- `react-i18next` + detector. Namespaces: `common`, `landing`, `analyze`, `results`, `auth`, `history`.
- Locales shipped: `en`, `hi`. Placeholders wired for `ta`, `bn`, `mr`.
- RTL support deferred (document token-ready).
- Language picker in navbar + auth persistence.

---

## 8. State & Data Conventions

- **React Query** (migrate from ad-hoc fetch) for all API calls: cache keys `['analysis', id]`, `['history']`, `['me']`. Background refetch off.
- **AuthContext** gains `authReady` (Phase 16.3). Protected routes render global splash until ready.
- **Toast** stays context-based; upgrade to stacking.
- **Theme**: `data-theme` on `<html>`, persisted `localStorage.theme`, defaults to `prefers-color-scheme`.

---

## 9. Assets

- Logo SVG: shield + scan-line mark. Monochrome + gradient variants. Used in navbar, PDF, favicon, OG.
- Lottie: 4 pipeline micro-loops (image / video / text / screenshot) — ≤10KB each.
- Illustrations: empty-state, 404, auth hero — line-art style, brand palette only.
- OG image: 1200×630, gradient mesh + tagline.

---

## 10. File/Folder Plan

```
frontend/src/
├── components/
│   ├── ui/                     # primitives (§2)
│   ├── layout/                 # Navbar, Sidebar, Footer, Shell
│   ├── common/                 # ProcessingAnimation, PipelineVisualizer, StickyActionBar
│   ├── results/                # existing + DetailedBreakdownCards, AudioCard, TemporalCard, AnalysisResultView
│   ├── upload/                 # DropZone (liquid), MediaTypeSwitcher, OptionsRow
│   ├── landing/                # Hero, ImpactMarquee, PipelineGrid, Comparison, TrustStrip, FAQ
│   └── auth/                   # AuthForm v2, MeshBackdrop
├── pages/                      # (unchanged names, internals rebuilt)
├── hooks/                      # useAnalysis, useJob, useTheme, useI18n
├── lib/
│   ├── queryClient.js          # React Query
│   ├── motion.js               # shared variants, easings
│   └── tokens.css              # CSS vars (light+dark)
├── locales/{en,hi}/*.json
└── utils/sanitize-text.js
```

---

## 11. Phase-to-Screen Mapping

| BUILD_PLAN2 phase | Frontend deliverable in this plan |
|---|---|
| 12.1 Grad-CAM/ELA | HeatmapOverlay 3-state toggle (§4.3 #4) |
| 12.2 EXIF | EXIFCard (§4.3 #5) |
| 12.3 LLM | LLMExplainCard folded into VerdictCard (§4.3 #1) |
| 13.3 Multi-lingual | LanguageBadge + navbar picker (§7) |
| 14.1 VLM | DetailedBreakdownCards (§4.3 #3) |
| 14.2 PDF v2 | Re-skin via shared tokens + logo (§9) |
| 16.1 ResultsPage | §4.4 + AnalysisResultView |
| 16.2 History rows | §4.5 |
| 16.3 Auth race | §8 `authReady` splash |
| 16.4 Sticky bar | §4.3 bottom bar |
| 17.2 Audio | AudioCard (§4.3 #8) |
| 17.x Temporal | TemporalCard (§4.3 #9) |
| 18.1 3D anim | §5.1 |
| 18.2 Glass | §1.1 glass tokens, `.glass-panel` |
| 18.3 Analyze overhaul | §4.2 |
| 19.3 Job queue | PipelineVisualizer polls `/jobs/{id}` (§4.2) |
| 20 Landing v2 | §4.1 |
| 22.1 i18n | §7 |
| 22.2 Dark mode | §1.1 dual theme + §8 toggle |
| 22.3 A11y | §6 |
| 22.4 Privacy | §4.7 consent modal |
| 22.5 Sanitization | `utils/sanitize-text.js` |

---

## 12. Inspiration Distillation (DeepTrace)

Takeaways applied:
- **Landing → Dashboard → Results** three-stage flow → mirrored in §4.1/4.2/4.4.
- **Dashboard-first** for authed users → History becomes the landing after login.
- **Trust visual language** (shield motif, blockchain/hash chips) → reuse SHA-8 badge on every analysis.
- **Workflow diagrams** surfaced in product → our PipelineVisualizer promotes stage visibility.

Divergences:
- We reject blockchain framing — DeepShield emphasizes **local-first + open models**.
- We lean heavier on **glassmorphism + 3D motion** to differentiate.
- LLM plain-English paragraph is our unique trust primitive; DeepTrace lacks it.

---

## 13. Acceptance Checklist per Screen

- [ ] Hits AA contrast in both themes (axe 0 critical).
- [ ] Tab order linear and visible.
- [ ] Reduced-motion variant ships.
- [ ] Empty + loading + error states drawn.
- [ ] Mobile 375w layout verified.
- [ ] Lighthouse a11y ≥ 95, perf ≥ 85.
- [ ] i18n: no hard-coded strings; pseudo-locale renders without overflow.

---

## 14. Rollout Order (frontend-only)

1. **Tokens + primitives** (§1, §2) — unblock everything else.
2. **Shell** (Navbar, Footer, theme, authReady splash).
3. **AnalysisResultView** extraction + ResultsPage + HistoryPage rows (Phase 16 blocker).
4. **HeatmapOverlay toggle + EXIFCard + LLMExplainCard + LanguageBadge** (already partially done per BUILD_PLAN2 tracker — re-skin with new tokens).
5. **AnalyzePage overhaul + ProcessingAnimation + PipelineVisualizer polling**.
6. **DetailedBreakdownCards + AudioCard + TemporalCard**.
7. **Landing v2** (Hero + marquee + comparison + FAQ).
8. **Auth pages re-skin**.
9. **Dark mode + i18n + a11y polish + privacy consent**.
10. **Vitest + RTL tests alongside each milestone**.

---

End.
