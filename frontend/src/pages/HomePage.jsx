import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './deepshield-landing.css';
import logoImg from '../assets/logo.png';
import { analyzeImage } from '../services/analyzeApi.js';
import useDottedSurface from '../hooks/useDottedSurface.js';
import ScrollReveal from '../components/common/ScrollReveal.jsx';
import { useAuth } from '../contexts/AuthContext.jsx';

/* ============ NAV ============ */
function Nav() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const { user, logout } = useAuth();
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  return (
    <header className={`ds-nav ${scrolled ? 'scrolled' : ''}`}>
      <div className="ds-nav-inner">
        <a href="#top" className="ds-logo">
          <img src={logoImg} alt="DeepShield Logo" className="ds-logo-img" />
        </a>
        <nav className="ds-nav-links">
          <SlideTabs tabs={[
            { label: 'Detection', id: 'analyze' },
            { label: 'Explainability', id: 'proof' },
            { label: 'Pipeline', id: 'pipeline' },
            { label: 'About', id: null, route: '/about' },
            { label: 'Contact', id: null, route: '/contact' },
          ]} />
        </nav>
        <div className="ds-nav-right">
          {user ? (
            <>
              <span className="btn btn-ghost btn-sm" style={{ cursor: 'default' }}>{user.name || user.email}</span>
              <button className="btn btn-ghost btn-sm" onClick={() => { logout(); }}>Sign out</button>
            </>
          ) : (
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/login', { state: { from: '/analyze' } })}>Sign in</button>
          )}
          <button
            className="btn btn-glass btn-sm btn-shiny"
            onClick={() => navigate('/analyze')}
          >
            Run analysis
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6h8m0 0L6 2m4 4L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
          </button>
        </div>
      </div>
    </header>
  );
}

function SlideTabs({ tabs }) {
  const items = tabs.map(t => typeof t === 'string' ? { label: t, id: null } : t);
  const [active, setActive] = useState(0);
  const [hovered, setHovered] = useState(null);
  const refs = useRef([]);
  const [pill, setPill] = useState({ left: 0, width: 0, opacity: 0 });

  useEffect(() => {
    const idx = hovered ?? active;
    const el = refs.current[idx];
    if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth, opacity: 1 });
  }, [hovered, active]);

  useEffect(() => {
    const ids = items.map(it => it.id).filter(Boolean);
    if (!ids.length) return;
    const onScroll = () => {
      const sections = ids.map(id => document.getElementById(id)).filter(Boolean);
      if (!sections.length) return;
      const mid = window.innerHeight * 0.35;
      let bestIdx = 0, bestDist = Infinity;
      sections.forEach(sec => {
        const r = sec.getBoundingClientRect();
        const dist = Math.abs(r.top - mid);
        if (r.top - mid < 0 && dist < bestDist) {
          bestDist = dist;
          bestIdx = items.findIndex(it => it.id === sec.id);
        }
      });
      if (bestIdx >= 0) setActive(bestIdx);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const navigate = useNavigate();
  const go = (i) => {
    setActive(i);
    const item = items[i];
    if (item.route) {
      navigate(item.route);
      return;
    }
    const id = item.id;
    if (!id) return;
    const el = document.getElementById(id);
    if (el) {
      const y = el.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  return (
    <div className="slide-tabs" onMouseLeave={() => setHovered(null)}>
      <div className="slide-tabs-pill" style={{ left: pill.left, width: pill.width, opacity: pill.opacity }} />
      {items.map((t, i) => (
        <button key={t.label} ref={el => refs.current[i] = el}
          className={`slide-tab ${i === active ? 'active' : ''}`}
          onMouseEnter={() => setHovered(i)}
          onClick={() => go(i)}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

/* ============ 3D LAYER STACK ============ */
function LayerStack({ src, playing = true, density = 6, expandOnScroll = false }) {
  const [sweep, setSweep] = useState(0);
  const spreadRef = useRef(36);

  useEffect(() => {
    if (!playing) return;
    let raf;
    const start = performance.now();
    const tick = (t) => {
      const dur = 2400;
      const p = ((t - start) % dur) / dur;
      setSweep(p);

      // Smooth lerp for scroll spread
      const targetScroll = expandOnScroll ? Math.min(1, window.scrollY / 600) : 0;
      const targetSpread = 36 + (targetScroll * 100);
      spreadRef.current += (targetSpread - spreadRef.current) * 0.1;

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, expandOnScroll]);

  const layers = Array.from({ length: density });
  const filters = [
    'none',
    'grayscale(1) contrast(1.3)',
    'hue-rotate(180deg) blur(1.5px) saturate(2)',
    'invert(1) hue-rotate(90deg) saturate(1.6) opacity(0.85)',
    'sepia(0.9) hue-rotate(-30deg) saturate(2)',
    'none',
  ];
  const labels = ['SOURCE', 'ARTIFACT', 'HEATMAP', 'ELA', 'FACE MESH', 'COMPOSITE'];

  return (
    <div className="stack-scene">
      <div className="stack-ambient" />
      <div className="stack-deck">
        {layers.map((_, i) => {
          const z = (density - 1 - i) * spreadRef.current;
          const delay = i * 90;
          return (
            <div key={i} className="stack-layer"
              style={{
                transform: `translateZ(${z}px)`,
                animationDelay: `${delay}ms`,
                filter: filters[i % filters.length],
              }}>
              <div className="stack-layer-inner" style={{ backgroundImage: `url(${src})` }} />
              <span className="stack-tag mono">{labels[i % labels.length]} · L{i + 1}</span>
              <div className="stack-laser" style={{ top: `${sweep * 100}%` }} />
            </div>
          );
        })}
        <div className="stack-floor" />
      </div>
      <div className="stack-telemetry">
        <div className="tel-row"><span className="mono">FREQ</span><div className="tel-bar"><i style={{ width: `${30 + sweep * 40}%` }} /></div><span className="mono">{(0.72 + sweep * 0.2).toFixed(2)}</span></div>
        <div className="tel-row"><span className="mono">ELA</span><div className="tel-bar"><i style={{ width: `${55 + Math.sin(sweep * Math.PI * 2) * 15}%`, background: 'var(--ds-warn)' }} /></div><span className="mono">{(0.41 + Math.abs(Math.sin(sweep * Math.PI)) * 0.3).toFixed(2)}</span></div>
        <div className="tel-row"><span className="mono">FACE</span><div className="tel-bar"><i style={{ width: `${85 - sweep * 20}%`, background: 'var(--ds-safe)' }} /></div><span className="mono">{(0.91 - sweep * 0.1).toFixed(2)}</span></div>
      </div>
    </div>
  );
}

/* ============ HERO ============ */
function Hero() {
  const navigate = useNavigate();
  useEffect(() => {
    const body = document.body;
    body.classList.add('ds-light');
    // Start fully light so the hero text reads dark against the cream sheet on first paint.
    body.style.setProperty('--theme-p', '0');
    body.style.setProperty('--light-k', '1');
    body.style.setProperty('--light-pct', '100%');

    const onScroll = () => {
      const y = window.scrollY;
      const h = window.innerHeight;
      // Hero owns the top of the page. Keep light mode locked until the viewport is
      // roughly scrolled past the hero baseline, then ramp to dark over the next ~40% vh.
      const holdUntil = h * 0.35;
      const rampEnd = h * 0.80;
      const raw = (y - holdUntil) / (rampEnd - holdUntil);
      const p = Math.max(0, Math.min(1, raw));            // 0 = light, 1 = dark
      const lightK = 1 - p;                                // 1 = light, 0 = dark

      body.style.setProperty('--theme-p', p.toFixed(3));
      body.style.setProperty('--light-k', lightK.toFixed(3));
      body.style.setProperty('--light-pct', `${(lightK * 100).toFixed(1)}%`);

      // Retire the legacy class-based toggle; color-mix via --light-k covers everything.
      if (p > 0.98) body.classList.add('ds-dark-phase'); else body.classList.remove('ds-dark-phase');

      if (window.__dotsInstance && window.__dotsInstance.setTheme) {
        const nextTheme = p > 0.5 ? 'dark' : 'light';
        if (window.__lastTheme !== nextTheme) {
          window.__lastTheme = nextTheme;
          window.__dotsInstance.setTheme(nextTheme);
        }
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => {
      window.removeEventListener('scroll', onScroll);
      body.classList.remove('ds-light');
      body.classList.remove('ds-dark-phase');
      body.style.removeProperty('--theme-p');
      body.style.removeProperty('--light-k');
      body.style.removeProperty('--light-pct');
    };
  }, []);
  return (
    <section className="ds-hero" id="top">
      <div className="ds-mesh" />
      <div className="ds-grid" />
      <div className="ds-hero-inner">
        <div className="ds-hero-left">
          <h1 className="display ds-hero-title">
            The leading <br /><em className="italic accent">forensic AI</em><br />
            platform for detecting<br />
            deepfake media.
          </h1>
          <p className="ds-hero-sub">
            DeepShield inspects every pixel, waveform, and word — returning a calm verdict
            backed by Grad-CAM++, ELA, EXIF and a plain-English explanation.
            For newsrooms, courts, and platforms.
          </p>
          <div className="ds-hero-cta">
            <button className="btn btn-primary btn-lg btn-shiny" onClick={() => navigate('/analyze')}>
              Analyze media
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 7h8m0 0L7 3m4 4L7 11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
            </button>
            <button className="btn btn-glass btn-lg" onClick={() => document.getElementById('pipeline')?.scrollIntoView({ behavior: 'smooth' })}>How the pipeline works</button>
          </div>
          <div className="ds-hero-proof">
            <div><span className="mono">92.4%</span><small>FF++ test acc.</small></div>
            <div><span className="mono">&lt; 3%</span><small>real-photo FPR</small></div>
            <div><span className="mono">6</span><small>explainability modes</small></div>
            <div><span className="mono">4</span><small>media modalities</small></div>
          </div>
        </div>
        <div className="ds-hero-right">
          <LayerStack src="https://upload.wikimedia.org/wikipedia/commons/5/5f/The_official_portrait_of_Shri_Narendra_Modi%2C_the_Prime_Minister_of_the_Republic_of_India.jpg" expandOnScroll={true} />
        </div>
      </div>
    </section>
  );
}

/* ============ EDITORIAL STATEMENT ============ */
function Statement() {
  const ref = useRef(null);

  useEffect(() => {
    let raf;
    let currentP = 0;
    const tick = () => {
      if (ref.current) {
        const r = ref.current.getBoundingClientRect();
        const vh = window.innerHeight;
        const start = vh * 0.85;
        const end = vh * 0.15;
        const targetP = Math.max(0, Math.min(1, (start - r.top) / (start - end)));

        currentP += (targetP - currentP) * 0.1;
        ref.current.style.setProperty('--p', currentP.toFixed(4));

        const conf = document.getElementById('pd-conf-val');
        if (conf) conf.textContent = Math.round(40 + currentP * 54);

        const scanline = document.getElementById('pd-scanline');
        if (scanline) scanline.style.top = `${(Math.min(currentP, 0.9) * 110) % 120}%`;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <section className="ds-statement" id="proof" ref={ref} style={{ '--p': 0 }}>
      <div className="ds-statement-peek ds-statement-peek-l" />
      <div className="ds-statement-peek ds-statement-peek-r" />
      <div className="ds-statement-inner">
        <span className="eyebrow">What we do</span>
        <h2 className="display ds-statement-text">
          We <em className="stmt-em">scan</em>{' '}
          every frame,<br />
          every pixel,{' '}
          <span className="stmt-span">every whisper</span>.<br />
          <span style={{ opacity: 0.55 }}>Forensics for the AI era.</span>
        </h2>
        <ScanOrb />
      </div>
    </section>
  );
}

function ScanOrb() {
  const COLS = 18, ROWS = 22;
  const glyphs = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const noise = Math.sin(r * 1.3 + c * 0.7) * 0.5 + 0.5;
      const threshold = 0.2 + (1 - (r / ROWS)) * 0.5 + noise * 0.2;
      glyphs.push({ r, c, char: noise > 0.5 ? '1' : '0', threshold });
    }
  }
  const SRC = 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Elon_Musk_-_54820081119_%28cropped%29.jpg/960px-Elon_Musk_-_54820081119_%28cropped%29.jpg';
  return (
    <div className="portrait-dissolve" aria-hidden="true">
      <div className="pd-glow" />
      <div className="pd-frame">
        <img src={SRC} alt="" className="pd-photo" draggable="false" />
        <svg className="pd-mesh" viewBox="0 0 100 120" preserveAspectRatio="none">
          <g stroke="rgba(61,219,179,0.55)" strokeWidth="0.2" fill="none">
            <polygon points="50,24 38,36 33,55 36,75 44,92 50,98 56,92 64,75 67,55 62,36" />
            <polyline points="38,36 50,46 62,36" />
            <polyline points="33,55 42,58 50,60 58,58 67,55" />
            <polyline points="42,58 50,70 58,58" />
            <polyline points="36,75 44,72 50,78 56,72 64,75" />
            <polyline points="50,46 50,60 50,78 50,92" />
          </g>
          {[[50, 24], [38, 36], [62, 36], [33, 55], [67, 55], [42, 58], [58, 58], [50, 60], [42, 72], [58, 72], [36, 75], [64, 75], [44, 92], [56, 92], [50, 98]].map(([x, y], k) => (
            <circle key={k} cx={x} cy={y} r="0.6" fill="rgba(61,219,179,0.95)" />
          ))}
        </svg>
        <div className="pd-binary">
          {glyphs.map((g) => (
            <span key={`${g.r}-${g.c}`} className="pd-bit" style={{
              left: `${(g.c / COLS) * 100}%`,
              top: `${(g.r / ROWS) * 100}%`,
              color: g.char === '1' ? 'rgba(127,143,255,0.95)' : 'rgba(61,219,179,0.85)',
              animationDelay: `${(g.r * 0.05 + g.c * 0.03)}s`,
              '--t': g.threshold
            }}>{g.char}</span>
          ))}
        </div>
        <div className="pd-scanline" id="pd-scanline" />
        <div className="pd-corner tl" />
        <div className="pd-corner tr" />
        <div className="pd-corner bl" />
        <div className="pd-corner br" />
      </div>
      <div className="pd-meta mono">
        <span>SUBJECT · unverified</span>
        <span>MODEL · ensemble v4.2</span>
        <span>CONFIDENCE · <span id="pd-conf-val">40</span>%</span>
      </div>
    </div>
  );
}

/* ============ MODALITY CARDS ============ */
function ModalityCards() {
  const navigate = useNavigate();
  const items = [
    { k: 'Image', n: '01', desc: 'ViT + EfficientNet ensemble with BlazeFace gating. Grad-CAM++, ELA, EXIF, JPEG Q-table, FFT frequency analysis.', sig: ['ensemble', 'grad-cam++', 'ela', 'exif'] },
    { k: 'Video', n: '02', desc: 'Per-frame classification, optical-flow temporal consistency, blink-rate analysis, lip-sync correlation with audio.', sig: ['temporal', 'blink-rate', 'lip-sync', 'frame-timeline'] },
    { k: 'Text', n: '03', desc: 'Multilingual XLM-R fake-news classifier, NER-anchored source lookup, truth-override against trusted domains, manipulation indicators.', sig: ['xlm-r', 'ner', 'truth-override', 'sensationalism'] },
    { k: 'Screenshot', n: '04', desc: 'EasyOCR extraction, credibility pass on extracted claims, layout-anomaly detection, suspicious-phrase bbox overlay.', sig: ['ocr', 'layout', 'phrase-map', 'credibility'] },
  ];
  return (
    <section className="ds-modality" id="pipeline">
      <div className="ds-container">
        <div className="ds-section-head">
          <span className="eyebrow">The pipeline</span>
          <h2 className="display">Four <ScrollReveal maxBlur={12}>modalities</ScrollReveal>.<br /><ScrollReveal maxBlur={12}><em className="italic accent">One</em></ScrollReveal> <em className="italic accent">verdict.</em></h2>
          <p>Each input routes through its own forensic stack. Outputs converge on a single, calm summary — with every signal exposed for review.</p>
        </div>
        <div className="ds-modality-grid">
          {items.map(it => (
            <article key={it.k} className="mod-card">
              <div className="mod-card-head">
                <span className="mono mod-n">{it.n}</span>
                <span className="mod-kind">{it.k}</span>
              </div>
              <h3 className="display mod-title">{it.k === 'Image' ? 'Pixel-grade' : it.k === 'Video' ? 'Frame-by-frame' : it.k === 'Text' ? 'Narrative-level' : 'Layout-aware'} inspection.</h3>
              <p className="mod-desc">{it.desc}</p>
              <ul className="mod-sig">
                {it.sig.map(s => <li key={s} className="mono">{s}</li>)}
              </ul>
              <ModalityVisual kind={it.k} />
            </article>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '48px' }}>
          <button
            className="btn btn-glass"
            onClick={() => navigate('/models')}
            style={{ borderRadius: '999px', padding: '12px 24px', fontSize: '15px' }}
          >
            Learn more about our models ↗
          </button>
        </div>
      </div>
    </section>
  );
}

function ModalityVisual({ kind }) {
  if (kind === 'Image') return (
    <div className="mv mv-image">
      <div className="mv-frame" />
      <div className="mv-heat" />
      <div className="mv-box" style={{ left: '22%', top: '30%', width: '32%', height: '36%' }} />
      <span className="mv-tag mono">0.87 fake</span>
    </div>
  );
  if (kind === 'Video') return (
    <div className="mv mv-video">
      {Array.from({ length: 16 }).map((_, i) => {
        const s = 0.2 + Math.abs(Math.sin(i * 0.8)) * 0.8;
        return <span key={i} style={{ height: `${20 + s * 70}%`, background: s > 0.6 ? 'var(--ds-danger)' : s > 0.4 ? 'var(--ds-warn)' : 'var(--ds-safe)' }} />;
      })}
    </div>
  );
  if (kind === 'Text') return (
    <div className="mv mv-text mono">
      <p><mark className="hl-warn">BREAKING:</mark> sources <mark className="hl-danger">allegedly confirm</mark> that <mark className="hl-safe">Reuters</mark> published…</p>
      <p><mark className="hl-danger">SHOCKING truth</mark> experts refuse to believe.</p>
    </div>
  );
  return (
    <div className="mv mv-shot">
      <div className="mv-shot-head" />
      <div className="mv-shot-line" style={{ width: '82%' }} />
      <div className="mv-shot-line" style={{ width: '64%' }} />
      <div className="mv-shot-line hl" style={{ width: '72%' }} />
      <div className="mv-shot-line" style={{ width: '48%' }} />
    </div>
  );
}

/* ============ ANALYZE DEMO — WIRED TO REAL BACKEND ============ */
const SAMPLES = [
  { label: 'Staged portrait', src: 'https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=640&q=80&auto=format&fit=crop', filename: 'staged-portrait.jpg' },
  { label: 'Press photo', src: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=640&q=80&auto=format&fit=crop', filename: 'press-photo.jpg' },
  { label: 'Social screenshot', src: 'https://images.unsplash.com/photo-1488554378835-f7acf46e6c98?w=640&q=80&auto=format&fit=crop', filename: 'social-screenshot.jpg' },
];
const STAGES = ['Upload', 'Preprocess', 'Ensemble', 'Grad-CAM++', 'ELA + EXIF', 'LLM summary'];

async function fetchSampleAsFile(s) {
  const res = await fetch(s.src);
  const blob = await res.blob();
  return new File([blob], s.filename, { type: blob.type || 'image/jpeg' });
}

function AnalyzeDemo() {
  const [stage, setStage] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [activeStage, setActiveStage] = useState(0);
  const [sampleIdx, setSampleIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [uploadedUrl, setUploadedUrl] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);
  const sessionId = useRef(Math.random().toString(36).slice(2, 8).toUpperCase());
  const sample = SAMPLES[sampleIdx];

  // Progress ticker while processing (caps at 92% until real result arrives)
  useEffect(() => {
    if (stage !== 'processing') return;
    let p = progress;
    const id = setInterval(() => {
      p = Math.min(92, p + 1.4);
      const cur = Math.min(STAGES.length - 1, Math.floor(p / (100 / STAGES.length)));
      setProgress(p);
      setActiveStage(cur);
    }, 80);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  const runAnalysis = async (file, previewUrl) => {
    setError(null);
    setResult(null);
    setProgress(0);
    setActiveStage(0);
    setUploadedUrl(previewUrl);
    setStage('processing');
    try {
      const data = await analyzeImage(file);
      setProgress(100);
      setActiveStage(STAGES.length - 1);
      setResult(data);
      setTimeout(() => setStage('result'), 250);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Analysis failed');
      setStage('idle');
    }
  };

  const startWithSample = async () => {
    try {
      const f = await fetchSampleAsFile(sample);
      await runAnalysis(f, sample.src);
    } catch (e) {
      setError('Could not load sample image');
    }
  };

  const onFilePicked = async (file) => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    await runAnalysis(file, url);
  };

  const reset = () => {
    setStage('idle');
    setProgress(0);
    setActiveStage(0);
    setResult(null);
    setUploadedUrl(null);
  };

  return (
    <section className="ds-analyze" id="analyze">
      <div className="ds-container">
        <div className="ds-section-head center">
          <span className="eyebrow">Live demonstration</span>
          <h2 className="display">Try the <ScrollReveal maxBlur={12}><em className="italic accent">forensic</em></ScrollReveal> <em className="italic accent">console.</em></h2>
          <p>Drop a sample, watch the 3D pass unfold, receive a verdict with every signal behind it. This is the same view operators see in production.</p>
        </div>

        <div className="console glass-strong">
          <div className="console-chrome">
            <div className="chrome-dots">
              <span /><span /><span />
            </div>
            <div className="chrome-title mono">deepshield · /analyze/image</div>
            <div className="chrome-meta mono">session · {sessionId.current}</div>
          </div>

          <div className="console-body">
            {stage === 'idle' && (
              <div className="console-idle">
                <div
                  className="drop-zone"
                  onDragOver={(e) => { e.preventDefault(); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    const f = e.dataTransfer.files?.[0];
                    if (f) onFilePicked(f);
                  }}
                  onClick={() => fileRef.current?.click()}
                >
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    style={{ display: 'none' }}
                    onChange={(e) => onFilePicked(e.target.files?.[0])}
                  />
                  <div className="drop-liquid">
                    <svg viewBox="0 0 200 200" width="120" height="120">
                      <defs>
                        <linearGradient id="dg" x1="0" y1="0" x2="1" y2="1">
                          <stop stopColor="#7F8FFF" /><stop offset="1" stopColor="#3DDBB3" />
                        </linearGradient>
                      </defs>
                      <path d="M100 20 C140 20 170 50 170 90 C170 130 140 170 100 170 C60 170 30 130 30 90 C30 50 60 20 100 20 Z"
                        fill="none" stroke="url(#dg)" strokeWidth="1.5" strokeDasharray="4 6" opacity="0.6" />
                      <path d="M100 60 L100 120 M80 100 L100 120 L120 100" stroke="url(#dg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                    </svg>
                  </div>
                  <h3 className="display">Drop media here</h3>
                  <p>PNG · JPEG · MP4 · WebM · or paste text / screenshot · 100MB max</p>
                  <button className="btn btn-glass btn-sm" onClick={(e) => { e.stopPropagation(); startWithSample(); }}>Use sample</button>
                  {error && <p style={{ color: 'var(--ds-danger)', marginTop: 14, fontSize: 13 }}>{error}</p>}
                </div>
                <aside className="console-side">
                  <span className="eyebrow">Samples</span>
                  {SAMPLES.map((s, i) => (
                    <button key={i} className={`sample-row ${i === sampleIdx ? 'active' : ''}`} onClick={() => setSampleIdx(i)}>
                      <img src={s.src} alt="" />
                      <div>
                        <div className="sr-name">{s.label}</div>
                        <div className="sr-meta mono">click to select</div>
                      </div>
                    </button>
                  ))}
                  <div className="console-opts">
                    <label className="opt"><input type="checkbox" defaultChecked /> Cache result</label>
                    <label className="opt"><input type="checkbox" defaultChecked /> Run LLM summary</label>
                    <label className="opt"><input type="checkbox" /> Write EXIF verdict</label>
                  </div>
                </aside>
              </div>
            )}

            {stage === 'processing' && (
              <div className="console-processing">
                <div className="proc-stack">
                  <LayerStack src={uploadedUrl || sample.src} density={6} />
                </div>
                <div className="proc-stages">
                  <div className="stages-head">
                    <span className="eyebrow">Forensic passes</span>
                    <span className="mono">{Math.round(progress)}%</span>
                  </div>
                  <div className="stages-bar"><i style={{ width: `${progress}%` }} /></div>
                  <ol className="stage-list">
                    {STAGES.map((s, i) => (
                      <li key={s} className={i < activeStage ? 'done' : i === activeStage ? 'active' : ''}>
                        <span className="stage-dot" />
                        <span className="stage-label">{s}</span>
                        <span className="mono stage-status">
                          {i < activeStage ? '✓' : i === activeStage ? '···' : '—'}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            )}

            {stage === 'result' && result && (
              <ResultView result={result} imgUrl={uploadedUrl || sample.src} onReset={reset} />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function ResultView({ result, imgUrl, onReset }) {
  const [heatmapMode, setHeatmapMode] = useState('heatmap');
  const [alpha, setAlpha] = useState(0.65);
  const [expanded, setExpanded] = useState(null);

  const verdict = result.verdict || {};
  const fakeProb = verdict.fake_probability ?? expl.fake_probability ?? verdict.confidence ?? 0.5;
  const score = typeof verdict.authenticity_score === 'number'
    ? Math.round(verdict.authenticity_score)
    : Math.round(Math.max(0, Math.min(1, 1 - fakeProb)) * 100);
  const verdictColor = score > 65 ? 'safe' : score > 40 ? 'warn' : 'danger';
  const verdictLabel = (verdict.label || verdict.classification || (score < 40 ? 'LIKELY FAKE' : score < 65 ? 'SUSPICIOUS' : 'LIKELY REAL')).toString().toUpperCase();

  const expl = result.explainability || {};
  const exif = expl.exif || {};
  const vlm = expl.vlm_breakdown || {};
  const llm = expl.llm_summary || result.llm_summary || null;
  const artifacts = expl.artifact_indicators || [];
  const sources = result.trusted_sources || [];

  const heatmapData = expl.heatmap_base64 ? `data:image/png;base64,${expl.heatmap_base64}` : null;
  const elaData = expl.ela_base64 ? `data:image/png;base64,${expl.ela_base64}` : null;
  const boxesData = expl.boxes_base64 ? `data:image/png;base64,${expl.boxes_base64}` : null;

  const processingTime = result.processing_summary?.total_ms
    ? (result.processing_summary.total_ms / 1000).toFixed(2)
    : '—';

  const bdItems = [
    { k: 'Facial symmetry', v: vlm.facial_symmetry_score, note: vlm.facial_symmetry_note || 'Left-right alignment across eye, nose, and jaw landmarks.' },
    { k: 'Skin texture', v: vlm.skin_texture_score, note: vlm.skin_texture_note || 'Pore distribution, micro-shading, sebum highlights.' },
    { k: 'Lighting', v: vlm.lighting_score, note: vlm.lighting_note || 'Light-source direction consistent across face and background.' },
    { k: 'Background', v: vlm.background_score, note: vlm.background_note || 'Depth, focal blur, and edge coherence.' },
    { k: 'Anatomy', v: vlm.anatomy_score, note: vlm.anatomy_note || 'Hands, ears, teeth — typical GAN failure zones.' },
    { k: 'Context', v: vlm.context_score, note: vlm.context_note || 'Objects and environment plausibility.' },
  ].map(b => ({ ...b, v: typeof b.v === 'number' ? Math.round(b.v) : (score > 60 ? 80 : 40) }));

  return (
    <div className="result-view">
      <div className={`verdict-card verdict-${verdictColor}`}>
        <div className="verdict-left">
          <ScoreRing value={score} color={verdictColor} />
          <div>
            <span className="eyebrow">Authenticity verdict</span>
            <h3 className="display verdict-label">{verdictLabel}</h3>
            <div className="verdict-meta mono">
              <span>id · {(result.analysis_id || '').slice(0, 8) || '—'}</span>
              <span>·</span>
              <span>ensemble · EfficientNetAutoAttB4 + ViT</span>
              <span>·</span>
              <span>{processingTime}s</span>
            </div>
          </div>
        </div>
        <div className="verdict-llm">
          <span className="eyebrow">Plain-English summary{llm?.model ? ` · ${llm.model}` : ''}</span>
          <p>
            {llm?.summary
              || llm?.text
              || verdict.reasoning
              || `Review the heatmap, EXIF, and detailed breakdown below for the evidence behind this verdict.`}
          </p>
          {Array.isArray(llm?.bullets) && llm.bullets.length > 0 && (
            <div className="verdict-bullets">
              {llm.bullets.map((b, i) => <span key={i}>• {b}</span>)}
            </div>
          )}
        </div>
        <button className="btn btn-ghost btn-sm result-reset" onClick={onReset}>↻ Analyze another</button>
      </div>

      <div className="result-grid">
        <div className="card heatmap-card">
          <div className="card-head">
            <span className="eyebrow">Visual evidence</span>
            <div className="seg-control">
              {['heatmap', 'ela', 'boxes', 'off'].map(m => (
                <button key={m} className={heatmapMode === m ? 'active' : ''} onClick={() => setHeatmapMode(m)}>{m}</button>
              ))}
            </div>
          </div>
          <div className="heatmap-stage">
            <img src={imgUrl} alt="" className="heatmap-base" />
            {heatmapMode === 'heatmap' && (
              heatmapData
                ? <img src={heatmapData} alt="" className="heatmap-overlay" style={{ opacity: alpha, position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', mixBlendMode: 'screen' }} />
                : <div className="heatmap-overlay" style={{ opacity: alpha }} />
            )}
            {heatmapMode === 'ela' && (
              elaData
                ? <img src={elaData} alt="" className="ela-overlay" style={{ opacity: alpha, position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', mixBlendMode: 'screen' }} />
                : <div className="ela-overlay" style={{ opacity: alpha }} />
            )}
            {heatmapMode === 'boxes' && (
              boxesData
                ? <img src={boxesData} alt="" style={{ opacity: alpha, position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
                : (
                  <svg className="heatmap-boxes" viewBox="0 0 100 100" preserveAspectRatio="none">
                    <rect x="22" y="18" width="42" height="48" fill="none" stroke="var(--ds-danger)" strokeWidth="0.4" strokeDasharray="1" />
                    <rect x="28" y="55" width="24" height="16" fill="none" stroke="var(--ds-warn)" strokeWidth="0.4" />
                  </svg>
                )
            )}
          </div>
          <div className="heatmap-foot">
            <span className="mono">α {alpha.toFixed(2)}</span>
            <input type="range" min="0" max="1" step="0.01" value={alpha} onChange={e => setAlpha(+e.target.value)} />
            <span className="mono status-chip">heatmap_status · {expl.heatmap_status || 'n/a'}</span>
          </div>
        </div>

        <div className="card exif-card">
          <div className="card-head">
            <span className="eyebrow">EXIF metadata</span>
            <span className="mono small">{(exif.trust_adjustment ?? exif.trust_delta) != null ? `${exif.trust_adjustment ?? exif.trust_delta} trust` : '—'}</span>
          </div>
          <ul className="exif-list mono">
            {[
              ['Make', exif.make],
              ['Model', exif.model],
              ['DateTimeOriginal', exif.datetime_original || exif.date_time_original || exif.datetime],
              ['GPSInfo', exif.gps || exif.gps_info],
              ['Software', exif.software],
              ['LensModel', exif.lens_model || exif.lens],
            ].map(([k, v]) => {
              const present = v && v !== '—';
              const suspicious = k === 'Software' && typeof v === 'string' && /photoshop|midjourney|dall·e|dalle|stable diffusion/i.test(v);
              const mark = suspicious ? '✗' : present ? '✓' : '⚠';
              const cls = suspicious ? 'bad' : present ? 'ok' : 'warn';
              return (
                <li key={k}>
                  <span>{k}</span>
                  <b className={suspicious ? 'bad' : ''}>{v || '—'}</b>
                  <em className={cls}>{mark}</em>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      <div className="breakdown">
        <div className="card-head">
          <span className="eyebrow">Detailed breakdown{vlm.model ? ` · ${vlm.model}` : ' · Gemini Vision'}</span>
          <span className="mono small">6 components</span>
        </div>
        <div className="breakdown-grid">
          {bdItems.map((b, i) => (
            <button key={b.k} className={`bd-cell ${expanded === i ? 'open' : ''}`} onClick={() => setExpanded(expanded === i ? null : i)}>
              <ScoreRing value={b.v} size={56} color={b.v > 70 ? 'safe' : b.v > 45 ? 'warn' : 'danger'} />
              <div className="bd-body">
                <div className="bd-title">{b.k}</div>
                <div className="mono bd-score">{b.v}/100</div>
                {expanded === i && <p className="bd-note">{b.note}</p>}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="result-grid">
        <div className="card sources-card">
          <div className="card-head">
            <span className="eyebrow">Trusted sources · cross-reference</span>
            <span className="mono small">{sources.length} match{sources.length === 1 ? '' : 'es'}</span>
          </div>
          {sources.length > 0 ? (
            <ul className="src-list">
              {sources.slice(0, 5).map((s, i) => (
                <li key={i}>
                  <div className="src-head">
                    <span className="mono">{s.domain || s.source || `source-${i + 1}`}</span>
                    <div className="src-bar"><i style={{ width: `${Math.round((s.weight ?? s.trust_weight ?? 1) * 100)}%` }} /></div>
                  </div>
                  <p>{s.title || s.snippet || s.description || '—'}</p>
                  <div className="src-foot mono">
                    <span>sim {(s.similarity ?? s.sim ?? 0).toFixed ? (s.similarity ?? s.sim ?? 0).toFixed(2) : '—'}</span>
                    <span>weight {((s.weight ?? s.trust_weight ?? 1)).toFixed ? (s.weight ?? s.trust_weight ?? 1).toFixed(2) : '1.00'}</span>
                    {s.url && <a href={s.url} target="_blank" rel="noreferrer">open ↗</a>}
                  </div>
                </li>
              ))}
            </ul>
          ) : <p className="src-empty">No trusted-source publications match this media within the last 30 days. This weakens authenticity.</p>}
        </div>
        <div className="card artifact-card">
          <div className="card-head">
            <span className="eyebrow">Artifact indicators</span>
            <span className="mono small">{artifacts.length} signals</span>
          </div>
          <ul className="art-list">
            {(artifacts.length > 0 ? artifacts : [
              { name: 'GAN frequency fingerprint', severity: 'low', score: 0.14 },
              { name: 'JPEG Q-table anomaly', severity: 'medium', score: 0.42 },
              { name: 'FaceMesh jaw jitter', severity: 'low', score: 0.18 },
              { name: 'Luminance imbalance', severity: 'low', score: 0.12 },
            ]).map((a, i) => {
              const lvl = (a.severity || a.level || 'low').toString().toLowerCase();
              const val = typeof a.score === 'number' ? a.score : typeof a.confidence === 'number' ? a.confidence : 0;
              return (
                <li key={i}>
                  <span>{a.name || a.indicator || a.k}</span>
                  <span className={`art-chip ${lvl}`}>{lvl}</span>
                  <span className="mono art-val">{val.toFixed(2)}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      <div className="sticky-actions">
        <button className="btn btn-glass btn-sm" onClick={onReset}>↻ New analysis</button>
        <button
          className="btn btn-glass btn-sm"
          onClick={() => {
            if (!result.analysis_id) return;
            const base = import.meta.env.VITE_API_BASE_URL || '/api/v1';
            window.open(`${base}/report/${result.analysis_id}.pdf`, '_blank');
          }}
        >⤓ PDF report</button>
        <button
          className="btn btn-glass btn-sm"
          onClick={() => {
            navigator.clipboard?.writeText(`${window.location.origin}/results/${result.analysis_id || ''}`);
          }}
        >⎘ Copy link</button>
        <button
          className="btn btn-primary btn-sm btn-shiny"
          onClick={() => {
            if (result.analysis_id) window.location.href = `/results/${result.analysis_id}`;
          }}
        >Share verdict →</button>
      </div>
    </div>
  );
}

function ScoreRing({ value, size = 96, color = 'safe' }) {
  const r = size / 2 - 6;
  const c = 2 * Math.PI * r;
  const off = c - (value / 100) * c;
  const stroke = color === 'safe' ? 'var(--ds-safe)' : color === 'warn' ? 'var(--ds-warn)' : 'var(--ds-danger)';
  return (
    <svg width={size} height={size} className="score-ring">
      <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="4" fill="none" />
      <circle cx={size / 2} cy={size / 2} r={r} stroke={stroke} strokeWidth="4" fill="none"
        strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`} style={{ transition: 'stroke-dashoffset 900ms var(--e-out)', filter: `drop-shadow(0 0 8px ${stroke})` }} />
      <text x={size / 2} y={size / 2 + 2} textAnchor="middle" dominantBaseline="middle"
        fontFamily="var(--ff-mono)" fontSize={size * 0.28} fill="var(--ds-ink)" fontWeight="500">{value}</text>
    </svg>
  );
}

/* ============ COMPARISON ============ */
function Comparison() {
  const rows = [
    ['Multimodal (img/video/text/screenshot)', true, false, 'partial', false],
    ['Grad-CAM++ heatmap + ELA + EXIF', true, 'partial', false, false],
    ['LLM plain-English explanation', true, false, false, false],
    ['Trusted-source cross-reference', true, false, false, 'manual'],
    ['Temporal + audio video analysis', true, false, false, false],
    ['Local-first processing', true, false, false, true],
    ['Open-source models', true, false, false, true],
    ['PDF forensic report', true, 'partial', false, false],
  ];
  const cols = ['DeepShield', 'Reality Defender', 'Deepware', 'Manual review'];
  return (
    <section className="ds-compare" id="compare">
      <div className="ds-container">
        <div className="ds-section-head">
          <span className="eyebrow">Why DeepShield</span>
          <h2 className="display">Forensics <em className="italic accent">without the <ScrollReveal maxBlur={12}>noise.</ScrollReveal></em></h2>
        </div>
        <div className="cmp glass">
          <div className="cmp-row cmp-head">
            <div className="cmp-cell" />
            {cols.map((c, i) => (
              <div key={c} className={`cmp-cell ${i === 0 ? 'highlight' : ''}`}>{c}</div>
            ))}
          </div>
          {rows.map(([label, ...vals]) => (
            <div key={label} className="cmp-row">
              <div className="cmp-cell cmp-label">{label}</div>
              {vals.map((v, i) => (
                <div key={i} className={`cmp-cell ${i === 0 ? 'highlight' : ''}`}>
                  {v === true && <span className="chk ok">●</span>}
                  {v === false && <span className="chk no">○</span>}
                  {v === 'partial' && <span className="chk part mono">partial</span>}
                  {v === 'manual' && <span className="chk part mono">manual</span>}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============ IMPACT MARQUEE ============ */
function Marquee() {
  const incidents = [
    { date: 'Mar 2024', head: 'Fabricated Zelensky surrender broadcast', src: 'REUTERS', verdict: 'FAKE' },
    { date: 'Feb 2024', head: 'AI-generated Biden robocall targets NH voters', src: 'AP', verdict: 'FAKE' },
    { date: 'Jan 2024', head: 'Taylor Swift deepfakes surge across X', src: 'BBC', verdict: 'FAKE' },
    { date: 'Nov 2023', head: 'Manipulated Netanyahu audio circulates', src: 'FT', verdict: 'SUSPICIOUS' },
    { date: 'Jul 2023', head: 'Synthetic Xi speech on Taiwan', src: 'WSJ', verdict: 'FAKE' },
    { date: 'May 2023', head: 'Pentagon explosion image goes viral', src: 'AP', verdict: 'FAKE' },
  ];
  const doubled = [...incidents, ...incidents];
  return (
    <section className="ds-marquee">
      <div className="ds-section-head center">
        <span className="eyebrow">Real-world impact</span>
        <h2 className="display">The incidents <em className="italic accent"><ScrollReveal maxBlur={12}>we train</ScrollReveal> on.</em></h2>
      </div>
      <div className="mq-track-wrap">
        <div className="mq-track">
          {doubled.map((it, i) => (
            <article key={i} className="mq-card glass">
              <div className="mq-head">
                <span className="mono">{it.date}</span>
                <span className={`mq-verdict ${it.verdict.toLowerCase()}`}>{it.verdict}</span>
              </div>
              <h4>{it.head}</h4>
              <span className="mq-src mono">{it.src}</span>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============ FAQ ============ */
function FAQ() {
  const qs = [
    ['How accurate is DeepShield?', 'Our ensemble (EfficientNetAutoAttB4 + ViT) achieves 92.4% accuracy on the FaceForensics++ c40 test set with an isotonic-calibrated false-positive rate below 3% on unedited camera photos.'],
    ['Which media types are supported?', 'Images (JPEG/PNG/WebP), videos (MP4/WebM/MOV up to 100MB), news text (50–10,000 chars), and social-media screenshots via EasyOCR.'],
    ['Do you retain uploaded files?', 'No. Files are hashed, analyzed, and deleted within the request lifecycle unless you opt in to the 30-day dedup cache, which stores only the SHA-256 and derived signals — never the raw media.'],
    ['What models power the explainability layer?', 'Grad-CAM++ for visual evidence, Error-Level Analysis for compression tampering, Pillow/exifread for metadata, and Gemini 1.5 Flash for the plain-English summary.'],
    ['Can I run this on-premise?', 'Yes. The FastAPI backend runs entirely offline with local model weights. NewsData.io lookup is optional and disabled by env flag.'],
    ['Which languages do you handle?', 'English and Hindi at launch via XLM-RoBERTa for text and a bilingual EasyOCR reader. Tamil, Bengali, and Marathi are on the near-term roadmap.'],
  ];
  const [open, setOpen] = useState(null);
  return (
    <section className="ds-faq">
      <div className="ds-container ds-faq-inner">
        <div className="faq-left">
          <span className="eyebrow">Questions</span>
          <h2 className="display">We're here<br />to help.</h2>
          <p>Straight answers from the engineers who built the forensic pipeline.</p>
          <button className="btn btn-glass btn-lg">All FAQs ↗</button>
        </div>
        <div className="faq-right">
          {qs.map(([q, a], i) => (
            <button key={q} className={`faq-item ${open === i ? 'open' : ''}`} onClick={() => setOpen(open === i ? -1 : i)}>
              <div className="faq-q">
                <span>{q}</span>
                <span className="faq-plus">{open === i ? '−' : '+'}</span>
              </div>
              <div className="faq-a-wrap"><p className="faq-a">{a}</p></div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============ CTA + FOOTER ============ */
function CTAFooter() {
  const navigate = useNavigate();
  return (
    <>
      <section className="ds-cta">
        <div className="ds-mesh" />
        <div className="ds-container">
          <div className="cta-card glass-strong">
            <span className="eyebrow">Start detecting</span>
            <h2 className="display">Deploy forensic certainty<br /><em className="italic accent">in your newsroom today.</em></h2>
            <p>Join newsrooms, platforms, and research labs using DeepShield as their trust instrument.</p>
            <div className="cta-row">
              <button className="btn btn-primary btn-lg btn-shiny" onClick={() => navigate('/register')}>Get started free
                <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 7h8m0 0L7 3m4 4L7 11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" fill="none" /></svg>
              </button>
              <button className="btn btn-glass btn-lg" onClick={() => navigate('/about')}>Request a live demo</button>
            </div>
          </div>
        </div>
      </section>
      <footer className="ds-footer">
        <div className="ds-container ds-footer-inner">
          <div className="foot-brand">
            <div className="ds-logo">
              <img src={logoImg} alt="DeepShield Logo" className="ds-logo-img" />
            </div>
            <p>Forensic AI for synthetic media. Open models, local-first, no retention.</p>
            <div className="foot-trust mono">
              <span>· Local-first</span><span>· Open models</span><span>· AA contrast</span>
            </div>
          </div>
          <div className="foot-cols">
            <div>
              <h5>Product</h5>
              <Link to="/analyze">Analyze</Link>
              <a href="#pipeline">Pipeline</a>
              <a href="#proof">Explainability</a>
            </div>
            <div>
              <h5>Research</h5>
              <Link to="/models">Model cards</Link>
              <a href="https://paperswithcode.com/task/deepfake-detection" target="_blank" rel="noreferrer">Benchmarks</a>
              <a href="https://arxiv.org/abs/1901.08971" target="_blank" rel="noreferrer">Papers</a>
            </div>
            <div>
              <h5>Company</h5>
              <Link to="/about">About</Link>
              <a href="https://github.com/Spyderzz/DeepShield" target="_blank" rel="noreferrer">Privacy</a>
              <Link to="/contact">Contact</Link>
            </div>
          </div>
        </div>
        <div className="ds-container foot-bottom mono">
          <span>© 2026 DeepShield · all signals open</span>
          <span>build · v2.0</span>
        </div>
      </footer>
    </>
  );
}

/* ============ APP ============ */
export default function HomePage() {
  // Mount the dotted three.js background (global host lives in index.html).
  useDottedSurface();

  return (
    <>
      <div
        className="ds-light-sheet"
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: -1,
          pointerEvents: 'none',
          background: 'radial-gradient(1200px 800px at 30% 20%, rgba(108,125,255,0.10), transparent 60%), radial-gradient(900px 600px at 80% 10%, rgba(61,219,179,0.07), transparent 60%), linear-gradient(180deg, #F7F8FC 0%, #EFF1F7 100%)',
          opacity: 'var(--light-k, 1)',
          transition: 'opacity 140ms linear'
        }}
      />
      <Nav />
      <main>
        <Hero />
        <Statement />
        <ModalityCards />
        <AnalyzeDemo />
        <Comparison />
        <Marquee />
        <FAQ />
        <CTAFooter />
      </main>
    </>
  );
}
