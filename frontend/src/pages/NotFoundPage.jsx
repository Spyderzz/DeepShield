import { useNavigate } from 'react-router-dom';
import { SharedNav, SharedFooter } from '../components/layout/SharedNav.jsx';
import useDottedSurface from '../hooks/useDottedSurface.js';
import './deepshield-landing.css';
import './deepshield-pages.css';

export default function NotFoundPage() {
  useDottedSurface();
  const navigate = useNavigate();
  const path = typeof window !== 'undefined' ? window.location.pathname : '/unknown';
  return (
    <>
      <SharedNav />
      <section className="nf-shell">
        <div className="nf-bg">
          <div className="nf-noise"/>
          {Array.from({ length: 40 }).map((_, i) => (
            <span key={i} className="nf-scan" style={{ top: `${(i / 40) * 100}%`, animationDelay: `${i * 0.05}s` }}/>
          ))}
        </div>
        <div className="nf-inner">
          <div className="nf-glitch">
            <span className="eyebrow">error 404</span>
            <h1 className="display nf-num">
              <span style={{ color: 'var(--ds-brand)' }}>4</span>
              <span className="italic">0</span>
              <span style={{ color: 'var(--ds-brand-2)' }}>4</span>
            </h1>
            <h2 className="display italic">Signal lost.</h2>
            <p className="nf-sub">The page you were looking for couldn't be verified — no source match, no cached hash, no temporal trail. It may have moved, or it may never have existed.</p>
            <div className="nf-console mono">
              <div className="nf-line">&gt; resolve <b>{path}</b></div>
              <div className="nf-line">&gt; lookup cache <span style={{ color: 'var(--ds-danger)' }}>MISS</span></div>
              <div className="nf-line">&gt; cross-reference trusted sources <span style={{ color: 'var(--ds-danger)' }}>0 matches</span></div>
              <div className="nf-line">&gt; fallback: return verdict <span style={{ color: 'var(--ds-warn)' }}>404 NOT_FOUND</span></div>
            </div>
            <div className="nf-cta">
              <a onClick={() => navigate('/')} className="btn btn-primary btn-lg btn-shiny" style={{ textDecoration: 'none', cursor: 'pointer' }}>← Back to home</a>
              <a onClick={() => navigate('/analyze')} className="btn btn-glass btn-lg" style={{ textDecoration: 'none', cursor: 'pointer' }}>Analyze media →</a>
            </div>
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}
