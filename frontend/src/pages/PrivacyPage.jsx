import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { SharedNav, SharedFooter } from '../components/layout/SharedNav.jsx';
import useDottedSurface from '../hooks/useDottedSurface.js';
import './deepshield-landing.css';
import './deepshield-pages.css';

const DATA_FLOW = [
  {
    step: '01',
    title: 'Upload',
    desc: 'Your file is sent over TLS-encrypted HTTPS directly to our backend. It is never stored on a CDN or third-party service.',
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
  {
    step: '02',
    title: 'Analysis',
    desc: 'Forensic processing runs entirely on our server — no data is forwarded to external AI APIs except optional Gemini summarisation, which receives only a short text excerpt.',
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    step: '03',
    title: 'Retention',
    desc: 'Uploaded files are deleted from disk within 5 minutes of analysis. Only the result record (scores, metadata, no raw pixels) is stored in our database.',
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6M14 11v6" />
      </svg>
    ),
  },
  {
    step: '04',
    title: 'Deletion',
    desc: 'Any authenticated user can delete their full history from the History page. The database record and all derived artefacts are hard-deleted immediately.',
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
        <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
      </svg>
    ),
  },
];

const FAQ = [
  {
    q: 'Do you train on my uploads?',
    a: 'No. Your files are never used for model training, fine-tuning, or any learning process. They are processed and discarded.',
  },
  {
    q: 'Who can see my analysis results?',
    a: 'Only you. Results are tied to your account and are not shared. Unauthenticated analyses are ephemeral — they exist only for the duration of the browser session.',
  },
  {
    q: 'Does DeepShield use Gemini / third-party AI?',
    a: 'Optionally. The LLM explainability summary may use Gemini Flash. We send only a short text description of the forensic scores — never your raw file or its pixels.',
  },
  {
    q: 'What data do you collect at registration?',
    a: 'Email address and a bcrypt-hashed password. That\'s it. No phone numbers, no payment info, no tracking pixels.',
  },
  {
    q: 'Is my data shared with third parties?',
    a: 'No. We do not sell, rent, or share personal data. Infrastructure providers (hosting) may have access to encrypted traffic logs per their standard policies.',
  },
  {
    q: 'What cookies do you use?',
    a: 'A single session JWT stored in localStorage — no tracking cookies, no analytics cookies, no third-party cookies.',
  },
];

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`faq-item ${open ? 'open' : ''}`} style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '16px', marginBottom: '16px' }}>
      <button
        className="faq-q"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', padding: '0', background: 'transparent', border: 'none', color: 'var(--ds-ink)', fontSize: '1rem', fontWeight: '500', textAlign: 'left', cursor: 'pointer', transition: 'color 150ms' }}
      >
        <span>{q}</span>
        <svg className="faq-chevron" viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true" style={{ flexShrink: 0, color: 'var(--ds-muted)', transition: 'transform 200ms', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}>
          <path d="M5 8l5 5 5-5" />
        </svg>
      </button>
      {open && (
        <div className="faq-a" role="region" style={{ paddingTop: '12px' }}>
          <p style={{ fontSize: '14.5px', lineHeight: '1.7', color: 'var(--ds-ink-2)', margin: '0' }}>{a}</p>
        </div>
      )}
    </div>
  );
}

export default function PrivacyPage() {
  useDottedSurface();
  const navigate = useNavigate();

  return (
    <>
      <SharedNav current="privacy" />
      <section className="page-shell about-shell">
        <div className="page-head">
          <div className="crumbs">
            <a onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Home</a>
            <span className="sep">/</span>
            <span>Privacy</span>
          </div>
          <span className="eyebrow">Transparency</span>
          <h1 className="display" style={{ maxWidth: 900 }}>Privacy &amp; Data <span className="accent">Policy</span></h1>
          <p className="sub" style={{ maxWidth: 640 }}>
            DeepShield is built on a simple principle: <strong>your media is yours.</strong> We process what you upload, return a verdict, and discard the file. Nothing is retained, sold, or shared.
          </p>
        </div>

        <div className="about-wrap">
          {/* Data Flow */}
          <div className="about-manifesto">
            <span className="eyebrow">How your data flows</span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '28px', marginTop: '32px' }}>
              {DATA_FLOW.map(({ step, title, desc, icon }) => (
                <div key={step} style={{ display: 'flex', flexDirection: 'column', gap: '12px', padding: '24px', borderRadius: '16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', transition: 'all 200ms' }} className="flow-card">
                  <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(108,125,255,0.1)', border: '1px solid rgba(108,125,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6c7dff', flexShrink: 0, fontSize: '20px' }} aria-hidden="true">
                    {icon}
                  </div>
                  <div>
                    <p style={{ fontSize: '11px', color: 'var(--ds-muted)', margin: 0, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.08em' }} className="mono">{step}</p>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: '600', color: 'var(--ds-ink)', margin: '0 0 8px 0' }}>{title}</h3>
                    <p style={{ fontSize: '14px', lineHeight: '1.65', color: 'var(--ds-ink-2)', margin: 0 }}>{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Security Commitments */}
          <div className="about-metrics" style={{ marginTop: '80px' }}>
            <span className="eyebrow">Our commitments</span>
            <div className="privacy-commitments" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginTop: '32px' }}>
              <div className="privacy-commitment-card" style={{ padding: '28px 24px', borderTop: '1px solid var(--ds-border)', borderBottom: '1px solid var(--ds-border)', minHeight: '180px' }}>
                <p className="mono" style={{ margin: '0 0 14px', fontSize: '11px', color: 'var(--ds-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>01</p>
                <h3 className="display" style={{ margin: '0 0 10px', fontSize: 'clamp(26px, 3vw, 34px)', lineHeight: '1.05' }}>No file retention</h3>
                <p style={{ color: 'var(--ds-ink-2)', margin: 0, lineHeight: '1.65' }}>Files are deleted within 5 minutes of analysis.</p>
              </div>
              <div className="privacy-commitment-card" style={{ padding: '28px 24px', borderTop: '1px solid var(--ds-border)', borderBottom: '1px solid var(--ds-border)', minHeight: '180px' }}>
                <p className="mono" style={{ margin: '0 0 14px', fontSize: '11px', color: 'var(--ds-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>02</p>
                <h3 className="display" style={{ margin: '0 0 10px', fontSize: 'clamp(26px, 3vw, 34px)', lineHeight: '1.05' }}>No training on uploads</h3>
                <p style={{ color: 'var(--ds-ink-2)', margin: 0, lineHeight: '1.65' }}>Uploads are never used for ML training or fine-tuning.</p>
              </div>
              <div className="privacy-commitment-card" style={{ padding: '28px 24px', borderTop: '1px solid var(--ds-border)', borderBottom: '1px solid var(--ds-border)', minHeight: '180px' }}>
                <p className="mono" style={{ margin: '0 0 14px', fontSize: '11px', color: 'var(--ds-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>03</p>
                <h3 className="display" style={{ margin: '0 0 10px', fontSize: 'clamp(26px, 3vw, 34px)', lineHeight: '1.05' }}>No tracking cookies</h3>
                <p style={{ color: 'var(--ds-ink-2)', margin: 0, lineHeight: '1.65' }}>We keep to a single session JWT and avoid analytics cookies.</p>
              </div>
              <div className="privacy-commitment-card" style={{ padding: '28px 24px', borderTop: '1px solid var(--ds-border)', borderBottom: '1px solid var(--ds-border)', minHeight: '180px' }}>
                <p className="mono" style={{ margin: '0 0 14px', fontSize: '11px', color: 'var(--ds-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>04</p>
                <h3 className="display" style={{ margin: '0 0 10px', fontSize: 'clamp(26px, 3vw, 34px)', lineHeight: '1.05' }}>Open-source models</h3>
                <p style={{ color: 'var(--ds-ink-2)', margin: 0, lineHeight: '1.65' }}>Processing remains auditable, transparent, and reviewable.</p>
              </div>
            </div>
          </div>

          {/* FAQ */}
          <div className="about-partners" style={{ marginTop: '80px' }}>
            <span className="eyebrow">Common questions</span>
            <h2 className="display" style={{ marginTop: '12px', marginBottom: '48px' }}>FAQ</h2>
            <div style={{ maxWidth: '700px' }}>
              {FAQ.map((item) => (
                <FaqItem key={item.q} {...item} />
              ))}
            </div>
          </div>

          {/* CTA */}
          <div className="about-cta" style={{ marginTop: '80px', paddingTop: '80px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
            <h2 className="display italic" style={{ marginBottom: '12px' }}>Questions or requests?</h2>
            <p style={{ color: 'var(--ds-ink-2)', marginBottom: '28px', fontSize: '16px' }}>To request data deletion or ask about our privacy practices, reach out via the contact page.</p>
            <Link to="/contact" className="btn btn-glass" style={{ textDecoration: 'none', display: 'inline-flex', gap: '8px', alignItems: 'center' }}>
              Contact us
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path d="M2 6.5h9m0 0L7 2.5m4 4L7 10.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </Link>
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}
