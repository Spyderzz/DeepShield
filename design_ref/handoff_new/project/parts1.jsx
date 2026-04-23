const { useState, useEffect, useRef, useMemo, useCallback } = React;

// ============ NAV ============
function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <header className={`ds-nav ${scrolled ? "scrolled" : ""}`}>
      <div className="ds-nav-inner">
        <a href="#top" className="ds-logo">
          <svg width="22" height="26" viewBox="0 0 22 26" fill="none">
            <path d="M11 1L21 5V12.5C21 18.5 16.5 23.5 11 25C5.5 23.5 1 18.5 1 12.5V5L11 1Z"
              stroke="url(#lg)" strokeWidth="1.5" fill="url(#lgf)"/>
            <path d="M6 11L10 15L16 8" stroke="#6C7DFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <defs>
              <linearGradient id="lg" x1="0" y1="0" x2="22" y2="26">
                <stop stopColor="#7F8FFF"/><stop offset="1" stopColor="#3DDBB3"/>
              </linearGradient>
              <linearGradient id="lgf" x1="0" y1="0" x2="0" y2="26">
                <stop stopColor="rgba(108,125,255,0.15)"/><stop offset="1" stopColor="rgba(61,219,179,0.05)"/>
              </linearGradient>
            </defs>
          </svg>
          <span>DeepShield</span>
        </a>
        <nav className="ds-nav-links">
          <SlideTabs tabs={[
            { label: "Detection", id: "analyze" },
            { label: "Explainability", id: "proof" },
            { label: "Pipeline", id: "pipeline" },
            { label: "Research", id: "compare" },
          ]} />
        </nav>
        <div className="ds-nav-right">
          <button className="btn btn-ghost btn-sm">Sign in</button>
          <button className="btn btn-glass btn-sm btn-shiny" onClick={() => document.getElementById("analyze")?.scrollIntoView({ behavior: "smooth", block: "start" })}>
            Run analysis
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6h8m0 0L6 2m4 4L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
          </button>
        </div>
      </div>
    </header>
  );
}

function SlideTabs({ tabs }) {
  // tabs can be strings or {label, id}
  const items = tabs.map(t => typeof t === "string" ? { label: t, id: null } : t);
  const [active, setActive] = useState(0);
  const [hovered, setHovered] = useState(null);
  const refs = useRef([]);
  const [pill, setPill] = useState({ left: 0, width: 0, opacity: 0 });

  useEffect(() => {
    const idx = hovered ?? active;
    const el = refs.current[idx];
    if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth, opacity: 1 });
  }, [hovered, active]);

  // observe sections to sync active tab with scroll position
  useEffect(() => {
    const ids = items.map(it => it.id).filter(Boolean);
    if (!ids.length) return;
    const sections = ids.map(id => document.getElementById(id)).filter(Boolean);
    if (!sections.length) return;
    const onScroll = () => {
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
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const go = (i) => {
    setActive(i);
    const id = items[i].id;
    if (!id) return;
    const el = document.getElementById(id);
    if (el) {
      const y = el.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: y, behavior: "smooth" });
    }
  };

  return (
    <div className="slide-tabs" onMouseLeave={() => setHovered(null)}>
      <div className="slide-tabs-pill" style={{ left: pill.left, width: pill.width, opacity: pill.opacity }} />
      {items.map((t, i) => (
        <button key={t.label} ref={el => refs.current[i] = el}
          className={`slide-tab ${i === active ? "active" : ""}`}
          onMouseEnter={() => setHovered(i)}
          onClick={() => go(i)}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

// ============ 3D LAYER STACK ============
function LayerStack({ src, playing = true, density = 6 }) {
  const [sweep, setSweep] = useState(0);
  useEffect(() => {
    if (!playing) return;
    let raf; const start = performance.now();
    const tick = (t) => {
      const dur = 2400;
      const p = ((t - start) % dur) / dur;
      setSweep(p);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  const layers = Array.from({ length: density });
  const filters = [
    "none",
    "grayscale(1) contrast(1.3)",
    "hue-rotate(180deg) blur(1.5px) saturate(2)",
    "invert(1) hue-rotate(90deg) saturate(1.6) opacity(0.85)",
    "sepia(0.9) hue-rotate(-30deg) saturate(2)",
    "none",
  ];
  const labels = ["SOURCE", "ARTIFACT", "HEATMAP", "ELA", "FACE MESH", "COMPOSITE"];

  return (
    <div className="stack-scene">
      <div className="stack-ambient" />
      <div className="stack-deck">
        {layers.map((_, i) => {
          const z = (density - 1 - i) * 36;
          const delay = i * 90;
          return (
            <div key={i} className="stack-layer"
              style={{
                transform: `translateZ(${z}px)`,
                animationDelay: `${delay}ms`,
                filter: filters[i % filters.length],
              }}>
              <div className="stack-layer-inner" style={{ backgroundImage: `url(${src})` }} />
              <span className="stack-tag mono">{labels[i % labels.length]} · L{i+1}</span>
              {/* Scanning laser — only on certain layers for visual richness */}
              <div className="stack-laser" style={{ top: `${sweep * 100}%` }} />
            </div>
          );
        })}
        {/* floor grid */}
        <div className="stack-floor" />
      </div>
      {/* Overlaid forensic telemetry */}
      <div className="stack-telemetry">
        <div className="tel-row"><span className="mono">FREQ</span><div className="tel-bar"><i style={{ width: `${30 + sweep*40}%` }}/></div><span className="mono">{(0.72 + sweep*0.2).toFixed(2)}</span></div>
        <div className="tel-row"><span className="mono">ELA</span><div className="tel-bar"><i style={{ width: `${55 + Math.sin(sweep*Math.PI*2)*15}%`, background: "var(--ds-warn)" }}/></div><span className="mono">{(0.41 + Math.abs(Math.sin(sweep*Math.PI))*0.3).toFixed(2)}</span></div>
        <div className="tel-row"><span className="mono">FACE</span><div className="tel-bar"><i style={{ width: `${85 - sweep*20}%`, background: "var(--ds-safe)" }}/></div><span className="mono">{(0.91 - sweep*0.1).toFixed(2)}</span></div>
      </div>
    </div>
  );
}

// ============ HERO ============
function Hero() {
  // Light-mode at rest, transitions to dark as the user scrolls past the hero.
  useEffect(() => {
    const body = document.body;
    body.classList.add("ds-light");
    const onScroll = () => {
      const y = window.scrollY;
      const h = window.innerHeight;
      // 0 → at top (full light), 1 → end of hero (full dark)
      const p = Math.max(0, Math.min(1, y / (h * 0.75)));
      body.style.setProperty("--theme-p", p.toFixed(3));
      if (p > 0.55) body.classList.add("ds-dark-phase"); else body.classList.remove("ds-dark-phase");
      // update three.js dot color when we cross threshold
      if (window.__dotsInstance && window.__dotsInstance.setTheme) {
        const nextTheme = p > 0.55 ? "dark" : "light";
        if (window.__lastTheme !== nextTheme) {
          window.__lastTheme = nextTheme;
          window.__dotsInstance.setTheme(nextTheme);
        }
      }
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => {
      window.removeEventListener("scroll", onScroll);
      body.classList.remove("ds-light");
      body.classList.remove("ds-dark-phase");
      body.style.removeProperty("--theme-p");
    };
  }, []);
  return (
    <section className="ds-hero" id="top">
      <div className="ds-mesh" />
      <div className="ds-grid" />
      <div className="ds-hero-inner">
        <div className="ds-hero-left">
          <span className="label-chip"><span className="dot"/> Forensic AI · v2.0 live</span>
          <h1 className="display ds-hero-title">
            The leading <em className="italic accent">forensic AI</em><br/>
            platform for trust<br/>
            in synthetic media.
          </h1>
          <p className="ds-hero-sub">
            DeepShield inspects every pixel, waveform, and word — returning a calm verdict
            backed by Grad-CAM++, ELA, EXIF and a plain-English explanation.
            For newsrooms, courts, and platforms.
          </p>
          <div className="ds-hero-cta">
            <button className="btn btn-primary btn-lg btn-shiny" onClick={() => document.getElementById("analyze")?.scrollIntoView({ behavior: "smooth" })}>
              Analyze media
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 7h8m0 0L7 3m4 4L7 11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
            </button>
            <button className="btn btn-glass btn-lg">How the pipeline works</button>
          </div>
          <div className="ds-hero-proof">
            <div><span className="mono">92.4%</span><small>FF++ test acc.</small></div>
            <div><span className="mono">&lt; 3%</span><small>real-photo FPR</small></div>
            <div><span className="mono">6</span><small>explainability modes</small></div>
            <div><span className="mono">4</span><small>media modalities</small></div>
          </div>
        </div>
        <div className="ds-hero-right">
          <LayerStack src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=520&q=80&auto=format&fit=crop" />
        </div>
      </div>
    </section>
  );
}

// ============ EDITORIAL STATEMENT ============
function Statement() {
  const [reveal, setReveal] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const onScroll = () => {
      if (!ref.current) return;
      const r = ref.current.getBoundingClientRect();
      const vh = window.innerHeight;
      const p = Math.max(0, Math.min(1, 1 - (r.top / vh)));
      setReveal(p);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  // Progressive reveal — words un-blur as user scrolls
  const blur = Math.max(0, (1 - reveal) * 18);
  const opacity = 0.25 + reveal * 0.75;
  return (
    <section className="ds-statement" id="proof" ref={ref}>
      <div className="ds-statement-peek ds-statement-peek-l" />
      <div className="ds-statement-peek ds-statement-peek-r" />
      <div className="ds-statement-inner">
        <span className="eyebrow">What we do</span>
        <h2 className="display ds-statement-text">
          We <em style={{ filter: `blur(${blur * 0.6}px)`, color: "var(--ds-brand)", fontStyle: "italic" }}>scan</em>{" "}
          every frame,<br/>
          every pixel,{" "}
          <span style={{ filter: `blur(${blur}px)`, opacity }}>every whisper</span>.<br/>
          <span style={{ opacity: 0.55 }}>Forensics for the AI era.</span>
        </h2>
        <ScanOrb reveal={reveal} />
      </div>
    </section>
  );
}

// A single portrait that dissolves into a binary/dot matrix as the user scrolls.
// Real photo → scanning phase → binary-code mosaic → back to composite.
function ScanOrb({ reveal }) {
  const p = Math.min(1, reveal * 1.15);
  // Three phases driven by p:
  //   0.00-0.35  raw photo, subtle scan line
  //   0.35-0.75  dissolve: photo fades while binary cells fade in over the face
  //   0.75-1.00  binary-matrix dominant, photo barely visible
  const photoOpacity = 1 - Math.max(0, (p - 0.15)) * 1.6;
  const binaryOpacity = Math.max(0, (p - 0.25)) * 1.7;
  const glyphScale = 0.6 + p * 0.6;

  // Grid of binary glyphs sampled by p — bottom rows fill first, so it reads
  // like the image "breaks apart" from below.
  const COLS = 18, ROWS = 22;
  const glyphs = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      // each cell reveals at a slightly different progress value
      const noise = Math.sin(r * 1.3 + c * 0.7) * 0.5 + 0.5;
      const threshold = 0.2 + (1 - (r / ROWS)) * 0.5 + noise * 0.2;
      if (p > threshold) {
        glyphs.push({ r, c, char: noise > 0.5 ? "1" : "0", age: Math.min(1, (p - threshold) * 3) });
      }
    }
  }

  // photo URL — a striking editorial portrait
  const SRC = "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=640&h=760&fit=crop&q=80&auto=format";

  return (
    <div className="portrait-dissolve" aria-hidden="true">
      <div className="pd-glow" />
      <div className="pd-frame">
        <img src={SRC} alt="" className="pd-photo" draggable="false" style={{
          opacity: photoOpacity,
          filter: `contrast(${1 + p * 0.2}) saturate(${1 - p * 0.4}) brightness(${0.95 - p * 0.2})`,
        }}/>
        {/* face-mesh hint under the photo while dissolving */}
        <svg className="pd-mesh" viewBox="0 0 100 120" preserveAspectRatio="none" style={{ opacity: Math.max(0, Math.min(1, (p - 0.1) * 2.5)) * (1 - Math.max(0, (p - 0.6) * 2)) }}>
          <g stroke="rgba(61,219,179,0.55)" strokeWidth="0.2" fill="none">
            <polygon points="50,24 38,36 33,55 36,75 44,92 50,98 56,92 64,75 67,55 62,36"/>
            <polyline points="38,36 50,46 62,36"/>
            <polyline points="33,55 42,58 50,60 58,58 67,55"/>
            <polyline points="42,58 50,70 58,58"/>
            <polyline points="36,75 44,72 50,78 56,72 64,75"/>
            <polyline points="50,46 50,60 50,78 50,92"/>
          </g>
          {[[50,24],[38,36],[62,36],[33,55],[67,55],[42,58],[58,58],[50,60],[42,72],[58,72],[36,75],[64,75],[44,92],[56,92],[50,98]].map(([x,y],k)=>(
            <circle key={k} cx={x} cy={y} r="0.6" fill="rgba(61,219,179,0.95)"/>
          ))}
        </svg>
        <div className="pd-binary" style={{ opacity: binaryOpacity }}>
          {glyphs.map((g, i) => (
            <span key={`${g.r}-${g.c}`} className="pd-bit" style={{
              left: `${(g.c / COLS) * 100}%`,
              top: `${(g.r / ROWS) * 100}%`,
              opacity: 0.35 + g.age * 0.65,
              color: g.char === "1" ? "rgba(127,143,255,0.95)" : "rgba(61,219,179,0.85)",
              transform: `translate(-50%, -50%) scale(${glyphScale})`,
              animationDelay: `${(g.r * 0.05 + g.c * 0.03)}s`,
            }}>{g.char}</span>
          ))}
        </div>
        {/* scan line sweeps downward */}
        <div className="pd-scanline" style={{ top: `${(Math.min(p, 0.9) * 110) % 120}%` }} />
        {/* corner brackets */}
        <div className="pd-corner tl" />
        <div className="pd-corner tr" />
        <div className="pd-corner bl" />
        <div className="pd-corner br" />
      </div>
      <div className="pd-meta mono">
        <span>SUBJECT · unverified</span>
        <span>MODEL · ensemble v4.2</span>
        <span>CONFIDENCE · {Math.round(40 + p * 54)}%</span>
      </div>
    </div>
  );
}

// ============ MODALITY CARDS ============
function ModalityCards() {
  const items = [
    { k: "Image", n: "01", desc: "ViT + EfficientNet ensemble with BlazeFace gating. Grad-CAM++, ELA, EXIF, JPEG Q-table, FFT frequency analysis.", sig: ["ensemble", "grad-cam++", "ela", "exif"] },
    { k: "Video", n: "02", desc: "Per-frame classification, optical-flow temporal consistency, blink-rate analysis, lip-sync correlation with audio.", sig: ["temporal", "blink-rate", "lip-sync", "frame-timeline"] },
    { k: "Text", n: "03", desc: "Multilingual XLM-R fake-news classifier, NER-anchored source lookup, truth-override against trusted domains, manipulation indicators.", sig: ["xlm-r", "ner", "truth-override", "sensationalism"] },
    { k: "Screenshot", n: "04", desc: "EasyOCR extraction, credibility pass on extracted claims, layout-anomaly detection, suspicious-phrase bbox overlay.", sig: ["ocr", "layout", "phrase-map", "credibility"] },
  ];
  return (
    <section className="ds-modality" id="pipeline">
      <div className="ds-container">
        <div className="ds-section-head">
          <span className="eyebrow">The pipeline</span>
          <h2 className="display">Four modalities.<br/><em className="italic accent">One verdict.</em></h2>
          <p>Each input routes through its own forensic stack. Outputs converge on a single, calm summary — with every signal exposed for review.</p>
        </div>
        <div className="ds-modality-grid">
          {items.map(it => (
            <article key={it.k} className="mod-card">
              <div className="mod-card-head">
                <span className="mono mod-n">{it.n}</span>
                <span className="mod-kind">{it.k}</span>
              </div>
              <h3 className="display mod-title">{it.k === "Image" ? "Pixel-grade" : it.k === "Video" ? "Frame-by-frame" : it.k === "Text" ? "Narrative-level" : "Layout-aware"} inspection.</h3>
              <p className="mod-desc">{it.desc}</p>
              <ul className="mod-sig">
                {it.sig.map(s => <li key={s} className="mono">{s}</li>)}
              </ul>
              <ModalityVisual kind={it.k} />
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function ModalityVisual({ kind }) {
  if (kind === "Image") return (
    <div className="mv mv-image">
      <div className="mv-frame"/>
      <div className="mv-heat" />
      <div className="mv-box" style={{ left: "22%", top: "30%", width: "32%", height: "36%" }}/>
      <span className="mv-tag mono">0.87 fake</span>
    </div>
  );
  if (kind === "Video") return (
    <div className="mv mv-video">
      {Array.from({length:16}).map((_,i)=>{
        const s = 0.2 + Math.abs(Math.sin(i*0.8)) * 0.8;
        return <span key={i} style={{ height: `${20 + s*70}%`, background: s > 0.6 ? "var(--ds-danger)" : s > 0.4 ? "var(--ds-warn)" : "var(--ds-safe)" }} />;
      })}
    </div>
  );
  if (kind === "Text") return (
    <div className="mv mv-text mono">
      <p><mark className="hl-warn">BREAKING:</mark> sources <mark className="hl-danger">allegedly confirm</mark> that <mark className="hl-safe">Reuters</mark> published…</p>
      <p><mark className="hl-danger">SHOCKING truth</mark> experts refuse to believe.</p>
    </div>
  );
  return (
    <div className="mv mv-shot">
      <div className="mv-shot-head"/>
      <div className="mv-shot-line" style={{width: "82%"}}/>
      <div className="mv-shot-line" style={{width: "64%"}}/>
      <div className="mv-shot-line hl" style={{width: "72%"}}/>
      <div className="mv-shot-line" style={{width: "48%"}}/>
    </div>
  );
}

window.DSParts1 = { Nav, Hero, Statement, ModalityCards, LayerStack };
