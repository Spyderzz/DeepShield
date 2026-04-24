# Results Page — 6 Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 6 broken areas on the DeepShield results/analyze pages without touching unrelated code.

**Architecture:** All fixes are isolated — 4 are pure frontend field-mapping corrections in `ResultsPage.jsx` and `AnalyzePage.jsx`, 1 is a backend auth-gate removal in `analyze.py`, 1 is a PDF flow fix split between `ResultsPage.jsx` and `reportApi.js`.

**Tech Stack:** React 18 (JSX), FastAPI (Python), Axios, Vite dev server

---

## Root Cause Reference

| # | Symptom | Root cause file : line |
|---|---------|------------------------|
| 1 | LayerStack shows Unsplash stock photo | `AnalyzePage.jsx:258` — hardcoded `SAMPLE_SRC` |
| 2 | Visual evidence card blank | `ResultsPage.jsx:97` — `thumbnail_url` is a bare relative path, no host prepended |
| 3 | Breakdown cards text hidden until click | `ResultsPage.jsx:354` — `{expanded === i && ...}` gate; also VLM keys are flat-style (`vlm.facial_symmetry_score`) but backend sends nested (`vlm.facial_symmetry.score`) plus 4 key-name mismatches |
| 4 | Artifact names blank | `ResultsPage.jsx:428` — reads `a.name \|\| a.indicator \|\| a.k`; backend field is `a.type` |
| 5 | LLM summary shows generic fallback | (a) `ResultsPage.jsx:209` reads `llm?.summary` but field is `paragraph`; (b) `analyze.py:84` returns `None` for unauthenticated users |
| 6 | PDF download → 405 Method Not Allowed | `ResultsPage.jsx:539,147` — calls `GET /api/v1/report/38.pdf`; correct flow is `POST /report/{id}` then `GET /report/{id}/download` |

---

## Task 1 — Stack card: pass uploaded image to LayerStack

**Files:**
- Modify: `frontend/src/pages/AnalyzePage.jsx`

Root cause: Line 258 always passes `SAMPLE_SRC` (Unsplash URL) to `<LayerStack>` regardless of what the user uploaded.

- [ ] **Step 1: Add `previewUrl` state and cleanup**

In `AnalyzePage`, add state for the object URL and revoke it on unmount / new file:

```jsx
// at the top of the AnalyzePage component, after existing useState declarations:
const [previewUrl, setPreviewUrl] = useState(null);
const previewRef = useRef(null);

// add a cleanup effect after the existing useEffects:
useEffect(() => {
  return () => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
  };
}, []);
```

- [ ] **Step 2: Set previewUrl when a file is picked**

Modify `onPickFile`:

```jsx
const onPickFile = (file) => {
  if (!file) return;
  // revoke previous
  if (previewRef.current) URL.revokeObjectURL(previewRef.current);
  if (file instanceof File && file.type.startsWith('image/')) {
    const url = URL.createObjectURL(file);
    previewRef.current = url;
    setPreviewUrl(url);
  } else {
    previewRef.current = null;
    setPreviewUrl(null);
  }
  runAnalysis(file);
};
```

- [ ] **Step 3: Pass previewUrl (with SAMPLE_SRC fallback) to LayerStack**

Find line 258:
```jsx
<LayerStack src={SAMPLE_SRC} density={6} />
```
Replace with:
```jsx
<LayerStack src={previewUrl || SAMPLE_SRC} density={6} />
```

- [ ] **Step 4: Verify**

Upload an image on `http://localhost:5174/analyze`. The stack card should show your image with the colored filter layers applied on top.

---

## Task 2 — Visual evidence: prepend backend host to thumbnail URL

**Files:**
- Modify: `frontend/src/pages/ResultsPage.jsx`

Root cause: `thumbnail_url` from the backend is stored as `"media/thumbs/abc_400.jpg"` (relative path). The browser resolves this relative to the frontend origin (`localhost:5174`), not the backend (`localhost:8000`). The image 404s silently, leaving the heatmap stage blank.

- [ ] **Step 1: Add a helper that resolves media paths**

Add this function near the top of `ResultsPage.jsx`, after the imports:

```jsx
const BACKEND_ORIGIN = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1')
  .replace(/\/api\/v1\/?$/, '');

function resolveMediaUrl(url) {
  if (!url) return null;
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) return url;
  return `${BACKEND_ORIGIN}/${url.replace(/^\/+/, '')}`;
}
```

- [ ] **Step 2: Apply resolver in ResultsView**

Find line 97 in `ResultsView`:
```jsx
const baseImg = result.thumbnail_url || result.media_url || heatmapData;
```
Replace with:
```jsx
const baseImg = resolveMediaUrl(result.thumbnail_url) || resolveMediaUrl(result.media_url) || heatmapData;
```

- [ ] **Step 3: Verify**

On any result page, the Visual Evidence card's background image should now show the analyzed photo instead of a black rectangle. Open DevTools Network tab — the `thumbs/...` request should return 200 from `localhost:8000`.

---

## Task 3 — Breakdown cards: always show notes + fix VLM key mapping

**Files:**
- Modify: `frontend/src/pages/ResultsPage.jsx`

Two bugs here:

**Bug A** — Notes only render when a card is clicked (`expanded === i` gate).

**Bug B** — `BreakdownCard` reads VLM scores with flat keys like `vlm.facial_symmetry_score` and `vlm.facial_symmetry_note`. Backend sends nested objects: `vlm.facial_symmetry = { score: 75, notes: "..." }`. Also 4 key-name mismatches:

| Frontend key | Backend field |
|---|---|
| `lighting` | `lighting_consistency` |
| `background` | `background_coherence` |
| `anatomy` | `anatomy_hands_eyes` |
| `context` | `context_objects` |

And `vlm.model` should be `vlm.model_used`.

- [ ] **Step 1: Fix BreakdownCard key mapping and score accessor**

Find the `base` array definition in `BreakdownCard` (starts ~line 326). Replace the entire `base` array and the `model` eyebrow with:

```jsx
const base = [
  { k: 'Facial symmetry', key: 'facial_symmetry',      defaultNote: 'Left-right alignment across eye, nose, and jaw landmarks.' },
  { k: 'Skin texture',    key: 'skin_texture',          defaultNote: 'Pore distribution, micro-shading, sebum highlights.' },
  { k: 'Lighting',        key: 'lighting_consistency',  defaultNote: 'Light-source direction consistent across face and background.' },
  { k: 'Background',      key: 'background_coherence',  defaultNote: 'Depth, focal blur, and edge coherence.' },
  { k: 'Anatomy',         key: 'anatomy_hands_eyes',    defaultNote: 'Hands, ears, teeth — typical GAN failure zones.' },
  { k: 'Context',         key: 'context_objects',       defaultNote: 'Objects and environment plausibility.' },
].map(b => {
  const component = vlm[b.key];  // { score, notes } or undefined
  return {
    ...b,
    v: typeof component?.score === 'number' ? Math.round(component.score) : (fallbackHigh ? 80 : 40),
    note: component?.notes || b.defaultNote,
  };
});
```

- [ ] **Step 2: Fix eyebrow model label**

In the same `BreakdownCard`, find:
```jsx
<span className="eyebrow">Detailed breakdown{vlm.model ? ` · ${vlm.model}` : ' · Gemini Vision'}</span>
```
Replace with:
```jsx
<span className="eyebrow">Detailed breakdown{vlm.model_used ? ` · ${vlm.model_used}` : ' · Gemini Vision'}</span>
```

- [ ] **Step 3: Always show notes (remove click-to-expand gate)**

Find line ~354:
```jsx
{expanded === i && <p className="bd-note">{b.note}</p>}
```
Replace with:
```jsx
<p className="bd-note">{b.note}</p>
```

Also update the header subtitle from "6 components · click to expand" since expand is now always shown:
```jsx
<span className="mono small">6 components</span>
```

- [ ] **Step 4: Verify**

On any image result, the breakdown section should show all 6 cards with their notes visible without clicking. If VLM data is present in the response (authed users who triggered VLM), the scores should reflect real values instead of the fallback 40/80.

---

## Task 4 — Artifact indicators: fix name field accessor

**Files:**
- Modify: `frontend/src/pages/ResultsPage.jsx`

Root cause: `ArtifactsCard` renders `a.name || a.indicator || a.k` but `ArtifactIndicator` schema fields are `type`, `severity`, `description`, `confidence`. No `name`, `indicator`, or `k` field → blank label.

- [ ] **Step 1: Fix the field accessor in ArtifactsCard**

Find in `ArtifactsCard` (~line 428):
```jsx
<span>{a.name || a.indicator || a.k}</span>
```
Replace with:
```jsx
<span>{a.name || a.type || a.description || a.indicator || '—'}</span>
```

- [ ] **Step 2: Verify**

On an image result, artifact indicator rows should show names like "GAN frequency fingerprint" or whatever `type`/`description` the backend returns. The badge (MEDIUM/LOW) and score were already showing correctly.

---

## Task 5 — LLM summary: fix field name + remove anon gate

**Files:**
- Modify: `frontend/src/pages/ResultsPage.jsx`
- Modify: `backend/api/v1/analyze.py`

Two bugs:

**Bug A** (frontend) — `VerdictCard` reads `llm?.summary || llm?.text` but `LLMExplainabilitySummary` has `paragraph` as the text field.

**Bug B** (backend) — `_compute_llm_summary` immediately returns `None` when `user is None` (anonymous users never get an LLM summary, so the fallback hardcoded text always shows).

- [ ] **Step 1: Fix the field name in VerdictCard**

Find in `VerdictCard` (~line 209):
```jsx
{llm?.summary || llm?.text ||
  'Model confidence is calibrated from the ensemble forward pass. Review the heatmap, EXIF, and detailed breakdown below for the evidence behind this verdict.'}
```
Replace with:
```jsx
{llm?.paragraph ||
  'Model confidence is calibrated from the ensemble forward pass. Review the heatmap, EXIF, and detailed breakdown below for the evidence behind this verdict.'}
```

- [ ] **Step 2: Also fix model label in the eyebrow**

In `VerdictCard` find:
```jsx
<span className="eyebrow">Plain-English summary{llm?.model ? ` · ${llm.model}` : ' · Gemini 1.5'}</span>
```
Replace with:
```jsx
<span className="eyebrow">Plain-English summary{llm?.model_used ? ` · ${llm.model_used}` : ' · Gemini 1.5'}</span>
```

- [ ] **Step 3: Remove the anonymous-user gate in analyze.py**

Open `backend/api/v1/analyze.py`. Find `_compute_llm_summary` (~line 80):

```python
def _compute_llm_summary(resp, *, record_id: int, user, media_kind: str, exclude: dict | None = None):
    """Generate the LLM summary for `resp` — gated on authed users, swallows
    provider errors. Returns the summary or None.
    """
    if user is None:
        return None
```

Remove the auth gate entirely and update the docstring:

```python
def _compute_llm_summary(resp, *, record_id: int, user, media_kind: str, exclude: dict | None = None):
    """Generate the LLM summary for `resp`. Swallows provider errors gracefully."""
    try:
        payload = resp.model_dump(exclude=exclude) if exclude else resp.model_dump()
        return generate_llm_summary(payload=payload, record_id=str(record_id))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"LLM explainer failed for {media_kind}: {e}")
        return None
```

- [ ] **Step 4: Verify**

Submit a new image analysis without being logged in. The "Plain-English Summary" section should now show a real Gemini-generated paragraph explaining why the image is classified as real or fake, referencing specific signals like ELA score or EXIF anomalies.

---

## Task 6 — PDF download: implement two-step generate + download flow

**Files:**
- Modify: `frontend/src/pages/ResultsPage.jsx`

Root cause: Both the header PDF button and the sticky-bar PDF button call:
```js
window.open(`${base}/report/${id}.pdf`, '_blank')
```
This is a `GET` to a `.pdf` URL suffix that doesn't exist. The backend requires:
1. `POST /api/v1/report/{id}` — generates the report, returns `{ report_id, ready: true }`
2. `GET /api/v1/report/{id}/download` — streams the PDF file

`reportApi.js` already has both helpers: `generateReport(id)` and `reportDownloadUrl(id)`.

- [ ] **Step 1: Add a download handler in ResultsView**

Add these imports at the top of `ResultsPage.jsx`:
```jsx
import { generateReport, reportDownloadUrl } from '../services/reportApi.js';
```

Add a handler inside `ResultsView` (before the `return` statement):

```jsx
const [pdfLoading, setPdfLoading] = useState(false);

const handleDownloadPDF = async () => {
  if (pdfLoading) return;
  setPdfLoading(true);
  try {
    await generateReport(id);
    // open the download URL in a new tab — browser will prompt save-as
    window.open(
      `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/report/${id}/download`,
      '_blank'
    );
  } catch (e) {
    alert(e?.userMessage || 'PDF generation failed. Try again.');
  } finally {
    setPdfLoading(false);
  }
};
```

- [ ] **Step 2: Replace both window.open calls with handleDownloadPDF**

There are two PDF buttons. Replace both:

**Header button** (~line 147):
```jsx
<button className="btn btn-glass btn-sm" onClick={() => {
  const base = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  window.open(`${base}/report/${id}.pdf`, '_blank');
}}>⤓ PDF</button>
```
Replace with:
```jsx
<button className="btn btn-glass btn-sm" onClick={handleDownloadPDF} disabled={pdfLoading}>
  {pdfLoading ? '…' : '⤓ PDF'}
</button>
```

**Sticky-bar button** (~line 539):
```jsx
<button className="btn btn-glass btn-sm" onClick={() => {
  const base = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  window.open(`${base}/report/${id}.pdf`, '_blank');
}}>⤓ PDF report</button>
```
Replace with:
```jsx
<button className="btn btn-glass btn-sm" onClick={handleDownloadPDF} disabled={pdfLoading}>
  {pdfLoading ? 'Generating…' : '⤓ PDF report'}
</button>
```

- [ ] **Step 3: Verify**

Click "PDF report" on a result page. Button should briefly show "Generating…", then a new tab should open and the browser should download `deepshield_report_38.pdf`. No 405 error.

---

## Execution Order

Fix in this order — each step is independent and can be verified before moving on:

1. Task 5 backend change first (needs server restart to take effect)
2. Tasks 1–4 and 6 (frontend — hot-reload, no restart needed)
