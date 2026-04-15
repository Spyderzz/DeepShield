const MODELS = [
  { name: 'ViT Deepfake Detector', id: 'prithivMLmods/Deep-Fake-Detector-v2-Model', use: 'Image & video frame classification (Realism vs Deepfake).' },
  { name: 'BERT Fake News', id: 'jy46604790/Fake-News-Bert-Detect', use: 'News-text authenticity classifier (LABEL_0=Fake, LABEL_1=Real).' },
  { name: 'EasyOCR', id: 'easyocr (English)', use: 'Screenshot text extraction with bbox coordinates.' },
  { name: 'MediaPipe FaceMesh', id: 'google/mediapipe', use: 'Face detection for video gating and artifact jitter signal.' },
  { name: 'Grad-CAM', id: 'jacobgil/pytorch-grad-cam', use: 'Class-activation heatmaps on ViT attention layers.' },
];

const STACK = [
  'FastAPI + SQLAlchemy + SQLite',
  'PyTorch + HuggingFace Transformers',
  'React 18 + Vite + React Router',
  'JWT auth · bcrypt password hashing',
  'xhtml2pdf + Jinja2 templated reports',
  'NewsData.io trusted-source lookup',
];

const SIGNALS = [
  { title: 'Classifier confidence', desc: 'Primary authenticity signal from fine-tuned ViT/BERT.' },
  { title: 'Grad-CAM heatmap', desc: 'Spatial explanation of model attention on the image.' },
  { title: 'Artifact scan', desc: 'GAN-HF frequency anomaly, JPEG q-table, face jitter, quadrant luminance.' },
  { title: 'Sensationalism score', desc: 'Clickbait regex + ALL CAPS + emotional words + exclamation density.' },
  { title: 'Manipulation patterns', desc: '15 regex probes: unverified claims, emotional manipulation, false authority.' },
  { title: 'Trusted sources', desc: 'News cross-check against weighted domain allowlist (Reuters, AP, BBC…).' },
  { title: 'Contradicting evidence', desc: 'Surface fact-check articles (Snopes, PolitiFact, FullFact…).' },
  { title: 'Layout anomalies', desc: 'OCR bbox height/spacing CV flags font-mismatch or uneven layout.' },
];

const card = {
  background: 'var(--color-surface)',
  padding: 'var(--space-6)',
  borderRadius: 'var(--radius-lg)',
  boxShadow: 'var(--shadow-sm)',
  border: '1px solid var(--color-border)',
};

export default function AboutPage() {
  return (
    <section style={{ display: 'grid', gap: 'var(--space-8)' }}>
      <div>
        <h2>About DeepShield</h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-lg)' }}>
          An explainable AI-based multimodal misinformation detection platform. Built as a college
          minor project — source-available, open-weights, and transparent about limitations.
        </p>
      </div>

      <div style={card}>
        <h3 style={{ marginTop: 0 }}>Methodology</h3>
        <p>
          DeepShield classifies content across four modalities (image, video, text, screenshot) and
          fuses model confidence with deterministic signals — heatmaps, artifact scans, manipulation
          pattern detection, and cross-referencing against trusted news sources. Each verdict carries
          an <b>authenticity score (0–100)</b> and a <b>severity label</b> (Very Likely Real → Likely Fake).
        </p>
        <p>
          The pipeline is intentionally explainable: every component reports its own signal so users
          can inspect <em>why</em> a verdict was issued — not just what.
        </p>
      </div>

      <div>
        <h3>Explainability signals</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 'var(--space-3)',
        }}>
          {SIGNALS.map((s) => (
            <div key={s.title} style={{ ...card, padding: 'var(--space-4)' }}>
              <h4 style={{ fontSize: 'var(--font-size-base)', marginBottom: 'var(--space-1)' }}>{s.title}</h4>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', margin: 0 }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div style={card}>
        <h3 style={{ marginTop: 0 }}>Models</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '2px solid var(--color-border)' }}>
              <th style={{ padding: 'var(--space-2)' }}>Model</th>
              <th style={{ padding: 'var(--space-2)' }}>Identifier</th>
              <th style={{ padding: 'var(--space-2)' }}>Use</th>
            </tr>
          </thead>
          <tbody>
            {MODELS.map((m) => (
              <tr key={m.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: 'var(--space-2)', fontWeight: 'var(--font-weight-semibold)' }}>{m.name}</td>
                <td style={{ padding: 'var(--space-2)', fontFamily: 'monospace', color: 'var(--color-text-secondary)' }}>{m.id}</td>
                <td style={{ padding: 'var(--space-2)', color: 'var(--color-text-secondary)' }}>{m.use}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={card}>
        <h3 style={{ marginTop: 0 }}>Tech stack</h3>
        <ul style={{ margin: 0, paddingLeft: 'var(--space-6)', color: 'var(--color-text-secondary)' }}>
          {STACK.map((s) => <li key={s}>{s}</li>)}
        </ul>
      </div>

      <div style={{ ...card, background: '#FFF8E1', borderColor: '#FFE082', color: '#6D4C00' }}>
        <h3 style={{ marginTop: 0, color: '#6D4C00' }}>Limitations & responsible use</h3>
        <ul style={{ margin: 0, paddingLeft: 'var(--space-6)' }}>
          <li>Classifiers are trained on specific datasets — performance on out-of-distribution content may degrade.</li>
          <li>Video model is face-centric; scenic clips without faces return "Insufficient face content" rather than a verdict.</li>
          <li>OCR quality varies with image clarity, font, and language (English-optimised).</li>
          <li>Trusted-source lookup requires a NewsData.io API key; absent key → empty source panels.</li>
          <li><b>This tool assists verification — it does not replace human judgment.</b> Cross-check with authoritative sources before sharing.</li>
        </ul>
      </div>
    </section>
  );
}
