# DeepShield — Frontend Redesign Tracker

> **Source:** Dark editorial redesign bundle from Claude Design (`/tmp/design/out/deepshield/`, copied into `design_ref/`). Design plan at `design_plan.md`. Original prompt: forensic/premium, dark-first, graphite + indigo + teal, Instrument Serif + Geist + JetBrains Mono, 3D layer-stack signature animation.
> **Approach:** Port the 2 polished pages (Landing, Analyze) 1:1 into React. Extend the 5 rough pages (Results, History, Login/Register, About, 404) using the same tokens + component vocabulary. Wire every interaction to the real backend via `analyzeApi`, `AuthContext`.

---

## Design Tokens (committed)

| Token | Value |
|---|---|
| `--ds-bg` | `#0A0D14` |
| `--ds-bg-2` | `#0F1320` |
| `--ds-ink` | `#E8ECF5` |
| `--ds-ink-2` | `#B3BACB` |
| `--ds-muted` | `#7A8299` |
| `--ds-brand` | `#6C7DFF` (indigo) |
| `--ds-brand-2` | `#3DDBB3` (teal) |
| `--ds-safe` | `#3DDBB3` |
| `--ds-warn` | `#FFB347` |
| `--ds-danger` | `#FF5E7A` |
| `--ds-surface` | `rgba(255,255,255,0.04)` |
| `--ds-border` | `rgba(255,255,255,0.08)` |
| `--ff-display` | `"Instrument Serif", serif` |
| `--ff-sans` | `"Geist", system-ui` |
| `--ff-mono` | `"JetBrains Mono", ui-monospace` |

Backward-compat: old `--color-*` vars kept as aliases so any un-rewritten component won't crash.

---

## Shared Components (committed)

- `components/layout/Navbar.jsx` — dark glass sticky nav, slide-tab indicator, logo shield SVG, sign-in + run-analysis right-cluster. `useAuth` wired.
- `components/layout/Footer.jsx` — 3-col link grid, brand trust chips, build version footer.

---

## Page Status

| Page | Design Source | Port Status | Backend Wired | Notes |
|---|---|---|---|---|
| HomePage (`/`) | `DeepShield.html` + `parts1-3.jsx` | ☐ | n/a | Hero + 3D LayerStack + Statement + ModalityCards + AnalyzeDemo + Comparison + Marquee + FAQ + CTA. LayerStack is reused on Analyze. |
| AnalyzePage (`/analyze`) | `analyze-app.jsx` | ☐ | ☐ | 4-mode segmented (image/video/text/screenshot). Real upload → calls `analyzeImage/Video/Text/Screenshot` / `submitVideoJob` + `pollVideoJob`. Navigate to `/results/:id` on done. |
| ResultsPage (`/results/:id`) | `results-app.jsx` (rough) | ☐ | ☐ | Verdict card, heatmap toggle, EXIF, 6-up breakdown, sources, artifacts, sticky action bar. GET `/history/{id}`. |
| HistoryPage (`/history`) | `history-app.jsx` (rough) | ☐ | ☐ | Stats + search + filter chips + grid/table. GET `/history`. DELETE per-row. |
| LoginPage + RegisterPage | `auth-app.jsx` (rough) | ☐ | ☐ | Split shell, tabs, quote column. Wire to `AuthContext.login/register`. |
| AboutPage (`/about`) | `about-app.jsx` (rough) | ☐ | n/a | Manifesto, metrics, team, partners, CTA. Static. |
| NotFoundPage (`*`) | `parts3.jsx` glitch block (rough) | ☐ | n/a | Glitch 404, scan-line bg, terminal readout. |

---

## Backend wiring assumptions (flag when unknown)

- **`/history` list endpoint**: assumed to return `[{id, kind, verdict, score, thumb, created_at, sha8}]`. Verify in `backend/api/v1/`.
- **`/history/{id}` detail**: assumed to return the full `AnalysisResponse` schema used by `/analyze/*`.
- **`DELETE /history/{id}`**: assumed. Will fall back to hiding locally if 404.
- **Job polling**: `/analyze/video/async` + `/jobs/{id}` already exist in `analyzeApi.js`. Use same pattern for image if latency needs SSE; otherwise sync.
- **Auth**: assume `AuthContext.login({email,password})` + `.register({email,password,name})` return `{user,token}`. TBD.

Unresolved questions to ask user:
1. Does `/history` GET exist? If not, skip fetch and show empty state w/ TODO.
2. Register fields: email + password + display-name only? Or more?

---

## Work Log

- **2026-04-22 init**: bundle extracted, foundation scaffolded. Landing + Analyze port in progress.
