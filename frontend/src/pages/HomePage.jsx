import { Link } from 'react-router-dom';

const FEATURES = [
  { icon: 'IMG', title: 'Image', desc: 'ViT-based deepfake classification + Grad-CAM heatmaps + 4-signal artifact scan (GAN/JPEG/face-jitter/lighting).' },
  { icon: 'VID', title: 'Video', desc: 'Uniform frame sampling + MediaPipe face-gating + per-frame timeline. No verdict when face content insufficient.' },
  { icon: 'TXT', title: 'Text', desc: 'Fine-tuned BERT fake-news classifier + sensationalism scoring + 15 manipulation patterns + cross-check against trusted sources.' },
  { icon: 'SS',  title: 'Screenshot', desc: 'EasyOCR extraction + layout-anomaly detection + phrase-level suspicious overlays mapped to bounding boxes.' },
];

const STEPS = [
  { n: 1, title: 'Upload', desc: 'Drop an image, video, screenshot, or paste article text.' },
  { n: 2, title: 'Analyze', desc: 'Run through multi-stage AI pipeline with live progress.' },
  { n: 3, title: 'Explain', desc: 'Inspect heatmaps, indicators, and trusted-source evidence.' },
  { n: 4, title: 'Report', desc: 'Download a PDF audit trail or revisit via history.' },
];

export default function HomePage() {
  return (
    <section style={{ display: 'grid', gap: 'var(--space-12)' }}>
      {/* Hero */}
      <div style={{
        display: 'grid',
        gap: 'var(--space-6)',
        padding: 'var(--space-16) var(--space-8)',
        background: 'linear-gradient(135deg, var(--color-primary-50), #FFFFFF 60%)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-sm)',
        textAlign: 'center',
      }}>
        <div style={{
          display: 'inline-block',
          margin: '0 auto',
          padding: '4px 12px',
          background: 'var(--color-primary-100)',
          color: 'var(--color-primary-700)',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-semibold)',
          letterSpacing: '0.05em',
        }}>EXPLAINABLE AI · MULTIMODAL · OPEN-SOURCE</div>
        <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.25rem)', margin: 0, lineHeight: 1.15 }}>
          Detect misinformation with <span style={{ color: 'var(--color-primary-600)' }}>explainable AI</span>
        </h1>
        <p style={{
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--font-size-lg)',
          maxWidth: 700,
          margin: '0 auto',
        }}>
          Upload an image, video, news article, or screenshot. DeepShield returns
          authenticity verdicts backed by transparency signals, heatmaps, and trusted-source evidence.
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/analyze" className="btn-primary" style={{
            display: 'inline-block',
            padding: 'var(--space-3) var(--space-6)',
            background: 'var(--color-primary-500)',
            color: 'white',
            borderRadius: 'var(--radius-md)',
            fontWeight: 'var(--font-weight-semibold)',
            boxShadow: 'var(--shadow-md)',
          }}>Start analysis →</Link>
          <Link to="/about" style={{
            display: 'inline-block',
            padding: 'var(--space-3) var(--space-6)',
            background: 'var(--color-surface)',
            color: 'var(--color-primary-600)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontWeight: 'var(--font-weight-semibold)',
          }}>How it works</Link>
        </div>
      </div>

      {/* Features */}
      <div>
        <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>Four pipelines, one verdict</h2>
        <div className="feature-grid" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 'var(--space-4)',
        }}>
          {FEATURES.map((f) => (
            <div key={f.title} style={{
              background: 'var(--color-surface)',
              padding: 'var(--space-6)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-sm)',
              border: '1px solid var(--color-border)',
            }}>
              <div style={{
                width: 44, height: 44, borderRadius: 'var(--radius-md)',
                background: 'var(--color-primary-50)',
                color: 'var(--color-primary-600)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 'var(--font-weight-bold)',
                marginBottom: 'var(--space-3)',
              }}>{f.icon}</div>
              <h3 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-2)' }}>{f.title}</h3>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', margin: 0 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* How it works */}
      <div>
        <h2 style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>How it works</h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-4)',
        }}>
          {STEPS.map((s) => (
            <div key={s.n} style={{
              padding: 'var(--space-4)',
              textAlign: 'center',
            }}>
              <div style={{
                width: 48, height: 48, margin: '0 auto var(--space-3)',
                borderRadius: 'var(--radius-full)',
                background: 'var(--color-primary-500)',
                color: 'white',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 'var(--font-size-xl)',
                fontWeight: 'var(--font-weight-bold)',
              }}>{s.n}</div>
              <h4 style={{ marginBottom: 'var(--space-1)' }}>{s.title}</h4>
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', margin: 0 }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA strip */}
      <div style={{
        padding: 'var(--space-8)',
        background: 'var(--color-primary-600)',
        color: 'white',
        borderRadius: 'var(--radius-lg)',
        textAlign: 'center',
      }}>
        <h3 style={{ color: 'white', marginBottom: 'var(--space-2)' }}>Ready to verify?</h3>
        <p style={{ opacity: 0.9, marginBottom: 'var(--space-4)' }}>No sign-up required. Login to save history + download PDF reports.</p>
        <Link to="/analyze" style={{
          display: 'inline-block',
          padding: 'var(--space-3) var(--space-6)',
          background: 'white',
          color: 'var(--color-primary-700)',
          borderRadius: 'var(--radius-md)',
          fontWeight: 'var(--font-weight-semibold)',
        }}>Run analysis →</Link>
      </div>
    </section>
  );
}
