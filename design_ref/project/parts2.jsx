const { useState: uS, useEffect: uE, useRef: uR, useMemo: uM, useCallback: uCB } = React;

// ============ ANALYZE — interactive demo ============
function AnalyzeDemo() {
  const [stage, setStage] = uS("idle"); // idle | dragging | processing | result
  const [progress, setProgress] = uS(0);
  const [activeStage, setActiveStage] = uS(0);
  const [sampleIdx, setSampleIdx] = uS(0);
  const samples = [
    { label: "Staged portrait", src: "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=640&q=80&auto=format&fit=crop", fakeProb: 0.87, verdict: "LIKELY FAKE" },
    { label: "Press photo", src: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=640&q=80&auto=format&fit=crop", fakeProb: 0.12, verdict: "LIKELY REAL" },
    { label: "Social screenshot", src: "https://images.unsplash.com/photo-1488554378835-f7acf46e6c98?w=640&q=80&auto=format&fit=crop", fakeProb: 0.58, verdict: "SUSPICIOUS" },
  ];
  const stages = ["Upload", "Preprocess", "Ensemble", "Grad-CAM++", "ELA + EXIF", "LLM summary"];

  uE(() => {
    if (stage !== "processing") return;
    let p = 0, cur = 0;
    const id = setInterval(() => {
      p += 2.2;
      cur = Math.min(stages.length - 1, Math.floor(p / (100 / stages.length)));
      setProgress(p);
      setActiveStage(cur);
      if (p >= 100) {
        clearInterval(id);
        setTimeout(() => setStage("result"), 300);
      }
    }, 70);
    return () => clearInterval(id);
  }, [stage]);

  const start = () => { setProgress(0); setActiveStage(0); setStage("processing"); };
  const reset = () => { setStage("idle"); setProgress(0); setActiveStage(0); };

  const sample = samples[sampleIdx];

  return (
    <section className="ds-analyze" id="analyze">
      <div className="ds-container">
        <div className="ds-section-head center">
          <span className="eyebrow">Live demonstration</span>
          <h2 className="display">Try the <em className="italic accent">forensic console.</em></h2>
          <p>Drop a sample, watch the 3D pass unfold, receive a verdict with every signal behind it. This is the same view operators see in production.</p>
        </div>

        <div className="console glass-strong">
          {/* Console chrome */}
          <div className="console-chrome">
            <div className="chrome-dots">
              <span/><span/><span/>
            </div>
            <div className="chrome-title mono">deepshield · /analyze/image</div>
            <div className="chrome-meta mono">session · {Math.random().toString(36).slice(2,8).toUpperCase()}</div>
          </div>

          <div className="console-body">
            {stage === "idle" && (
              <div className="console-idle">
                <div className="drop-zone"
                  onDragOver={(e) => { e.preventDefault(); setStage("dragging"); }}
                  onClick={start}>
                  <div className="drop-liquid">
                    <svg viewBox="0 0 200 200" width="120" height="120">
                      <defs>
                        <linearGradient id="dg" x1="0" y1="0" x2="1" y2="1">
                          <stop stopColor="#7F8FFF"/><stop offset="1" stopColor="#3DDBB3"/>
                        </linearGradient>
                      </defs>
                      <path d="M100 20 C140 20 170 50 170 90 C170 130 140 170 100 170 C60 170 30 130 30 90 C30 50 60 20 100 20 Z"
                        fill="none" stroke="url(#dg)" strokeWidth="1.5" strokeDasharray="4 6" opacity="0.6"/>
                      <path d="M100 60 L100 120 M80 100 L100 120 L120 100" stroke="url(#dg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                    </svg>
                  </div>
                  <h3 className="display">Drop media here</h3>
                  <p>PNG · JPEG · MP4 · WebM · or paste text / screenshot · 100MB max</p>
                  <button className="btn btn-glass btn-sm" onClick={(e)=>{e.stopPropagation(); start();}}>Use sample</button>
                </div>
                <aside className="console-side">
                  <span className="eyebrow">Samples</span>
                  {samples.map((s,i)=>(
                    <button key={i} className={`sample-row ${i===sampleIdx?"active":""}`} onClick={()=>setSampleIdx(i)}>
                      <img src={s.src} alt="" />
                      <div>
                        <div className="sr-name">{s.label}</div>
                        <div className="sr-meta mono">fake_p {s.fakeProb.toFixed(2)}</div>
                      </div>
                    </button>
                  ))}
                  <div className="console-opts">
                    <label className="opt"><input type="checkbox" defaultChecked/> Cache result</label>
                    <label className="opt"><input type="checkbox" defaultChecked/> Run LLM summary</label>
                    <label className="opt"><input type="checkbox"/> Write EXIF verdict</label>
                  </div>
                </aside>
              </div>
            )}

            {stage === "processing" && (
              <div className="console-processing">
                <div className="proc-stack">
                  <window.DSParts1.LayerStack src={sample.src} density={6} />
                </div>
                <div className="proc-stages">
                  <div className="stages-head">
                    <span className="eyebrow">Forensic passes</span>
                    <span className="mono">{Math.round(progress)}%</span>
                  </div>
                  <div className="stages-bar"><i style={{ width: `${progress}%` }}/></div>
                  <ol className="stage-list">
                    {stages.map((s, i) => (
                      <li key={s} className={i < activeStage ? "done" : i === activeStage ? "active" : ""}>
                        <span className="stage-dot"/>
                        <span className="stage-label">{s}</span>
                        <span className="mono stage-status">
                          {i < activeStage ? "✓" : i === activeStage ? "···" : "—"}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            )}

            {stage === "result" && <ResultView sample={sample} onReset={reset} />}
          </div>
        </div>
      </div>
    </section>
  );
}

// ============ RESULT VIEW ============
function ResultView({ sample, onReset }) {
  const [heatmapMode, setHeatmapMode] = uS("heatmap"); // heatmap | ela | boxes | off
  const [alpha, setAlpha] = uS(0.65);
  const [expanded, setExpanded] = uS(null);
  const score = Math.round((1 - sample.fakeProb) * 100);
  const verdictColor = score > 65 ? "safe" : score > 40 ? "warn" : "danger";

  return (
    <div className="result-view">
      {/* Verdict banner */}
      <div className={`verdict-card verdict-${verdictColor}`}>
        <div className="verdict-left">
          <ScoreRing value={score} color={verdictColor} />
          <div>
            <span className="eyebrow">Authenticity verdict</span>
            <h3 className="display verdict-label">{sample.verdict}</h3>
            <div className="verdict-meta mono">
              <span>sha · {Math.random().toString(36).slice(2, 10)}</span>
              <span>·</span>
              <span>ensemble · EfficientNetAutoAttB4 + ViT</span>
              <span>·</span>
              <span>{(2.1 + Math.random()).toFixed(2)}s</span>
            </div>
          </div>
        </div>
        <div className="verdict-llm">
          <span className="eyebrow">Plain-English summary · Gemini 1.5</span>
          <p>
            The subject's {score < 50 ? "jawline asymmetry and over-smoothed skin texture strongly suggest GAN synthesis" : score < 70 ? "compression profile and lighting are inconsistent with a native camera capture, but no single signal is conclusive" : "EXIF signature, skin micro-texture and frequency fingerprint are consistent with an in-camera photograph"}. EXIF reports {score > 70 ? "a Canon EOS R5 with valid GPS" : "Software=Adobe Photoshop 24.1 — weakens trust"}. Cross-reference against trusted sources found {score > 70 ? "3 matching" : "0 matching"} publications.
          </p>
          <div className="verdict-bullets">
            <span>• Facial symmetry {score > 60 ? "natural" : "uneven"}</span>
            <span>• Skin texture {score > 60 ? "micro-pore consistent" : "over-smoothed"}</span>
            <span>• Frequency fingerprint {score > 60 ? "matches sensor" : "GAN-like HF"}</span>
          </div>
        </div>
        <button className="btn btn-ghost btn-sm result-reset" onClick={onReset}>↻ Analyze another</button>
      </div>

      {/* Heatmap + breakdown */}
      <div className="result-grid">
        <div className="card heatmap-card">
          <div className="card-head">
            <span className="eyebrow">Visual evidence</span>
            <div className="seg-control">
              {["heatmap","ela","boxes","off"].map(m=>(
                <button key={m} className={heatmapMode===m?"active":""} onClick={()=>setHeatmapMode(m)}>{m}</button>
              ))}
            </div>
          </div>
          <div className="heatmap-stage">
            <img src={sample.src} alt="" className="heatmap-base"/>
            {heatmapMode === "heatmap" && <div className="heatmap-overlay" style={{ opacity: alpha }} />}
            {heatmapMode === "ela" && <div className="ela-overlay" style={{ opacity: alpha }} />}
            {heatmapMode === "boxes" && (
              <svg className="heatmap-boxes" viewBox="0 0 100 100" preserveAspectRatio="none">
                <rect x="22" y="18" width="42" height="48" fill="none" stroke="var(--ds-danger)" strokeWidth="0.4" strokeDasharray="1"/>
                <rect x="28" y="55" width="24" height="16" fill="none" stroke="var(--ds-warn)" strokeWidth="0.4"/>
                <text x="23" y="16" fill="var(--ds-danger)" fontSize="2.2" className="mono">face · 0.91</text>
                <text x="29" y="54" fill="var(--ds-warn)" fontSize="2" className="mono">mouth · 0.62</text>
              </svg>
            )}
          </div>
          <div className="heatmap-foot">
            <span className="mono">α {alpha.toFixed(2)}</span>
            <input type="range" min="0" max="1" step="0.01" value={alpha} onChange={e=>setAlpha(+e.target.value)} />
            <span className="mono status-chip">heatmap_status · ready</span>
          </div>
        </div>

        <div className="card exif-card">
          <div className="card-head">
            <span className="eyebrow">EXIF metadata</span>
            <span className="mono small">6 fields · {score > 70 ? "+3 trust" : "−12 trust"}</span>
          </div>
          <ul className="exif-list mono">
            <li><span>Make</span><b>{score > 70 ? "Canon" : "—"}</b><em className={score>70?"ok":"warn"}>{score>70?"✓":"⚠"}</em></li>
            <li><span>Model</span><b>{score > 70 ? "EOS R5" : "—"}</b><em className={score>70?"ok":"warn"}>{score>70?"✓":"⚠"}</em></li>
            <li><span>DateTimeOriginal</span><b>{score > 70 ? "2026:03:14 09:22:01" : "—"}</b><em className={score>70?"ok":"warn"}>{score>70?"✓":"⚠"}</em></li>
            <li><span>GPSInfo</span><b>{score > 70 ? "37.78°N 122.41°W" : "stripped"}</b><em className={score>70?"ok":"warn"}>{score>70?"✓":"⚠"}</em></li>
            <li><span>Software</span><b className={score<70?"bad":""}>{score<70?"Adobe Photoshop 24.1":"Canon Firmware 1.7.0"}</b><em className={score<70?"bad":"ok"}>{score<70?"✗":"✓"}</em></li>
            <li><span>LensModel</span><b>{score > 70 ? "RF 50mm F1.2 L" : "—"}</b><em className={score>70?"ok":"warn"}>{score>70?"✓":"⚠"}</em></li>
          </ul>
        </div>
      </div>

      {/* Detailed breakdown — 6 VLM cards */}
      <div className="breakdown">
        <div className="card-head">
          <span className="eyebrow">Detailed breakdown · Gemini Vision</span>
          <span className="mono small">6 components</span>
        </div>
        <div className="breakdown-grid">
          {[
            { k: "Facial symmetry", v: score > 60 ? 88 : 42, note: "Left-right alignment across eye, nose, and jaw landmarks." },
            { k: "Skin texture", v: score > 60 ? 91 : 37, note: "Pore distribution, micro-shading, sebum highlights." },
            { k: "Lighting", v: score > 60 ? 84 : 51, note: "Light-source direction consistent across face and background." },
            { k: "Background", v: score > 60 ? 77 : 63, note: "Depth, focal blur, and edge coherence." },
            { k: "Anatomy", v: score > 60 ? 94 : 29, note: "Hands, ears, teeth — typical GAN failure zones." },
            { k: "Context", v: score > 60 ? 82 : 48, note: "Objects and environment plausibility." },
          ].map((b,i)=>(
            <button key={b.k} className={`bd-cell ${expanded===i?"open":""}`} onClick={()=>setExpanded(expanded===i?null:i)}>
              <ScoreRing value={b.v} size={56} color={b.v>70?"safe":b.v>45?"warn":"danger"} />
              <div className="bd-body">
                <div className="bd-title">{b.k}</div>
                <div className="mono bd-score">{b.v}/100</div>
                {expanded===i && <p className="bd-note">{b.note}</p>}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Sources */}
      <div className="result-grid">
        <div className="card sources-card">
          <div className="card-head">
            <span className="eyebrow">Trusted sources · cross-reference</span>
            <span className="mono small">{score>70?"3 matches":"0 matches"}</span>
          </div>
          {score > 70 ? (
            <ul className="src-list">
              {[
                { dom: "reuters.com", w: 1.0, sim: 0.87, title: "Original press release photographed on stage, March 14." },
                { dom: "apnews.com", w: 1.0, sim: 0.82, title: "AP confirms image authenticity via direct pool access." },
                { dom: "bbc.com", w: 0.95, sim: 0.74, title: "BBC republishes under fair use; no manipulation reported." },
              ].map(s=>(
                <li key={s.dom}>
                  <div className="src-head"><span className="mono">{s.dom}</span><div className="src-bar"><i style={{width: `${s.w*100}%`}}/></div></div>
                  <p>{s.title}</p>
                  <div className="src-foot mono"><span>sim {s.sim}</span><span>weight {s.w.toFixed(2)}</span><a>open ↗</a></div>
                </li>
              ))}
            </ul>
          ) : <p className="src-empty">No trusted-source publications match this media within the last 30 days. This weakens authenticity.</p>}
        </div>
        <div className="card artifact-card">
          <div className="card-head">
            <span className="eyebrow">Artifact indicators</span>
            <span className="mono small">4 signals</span>
          </div>
          <ul className="art-list">
            {[
              { k: "GAN frequency fingerprint", lvl: score<60?"high":"low", val: score<60?0.78:0.14 },
              { k: "JPEG Q-table anomaly", lvl: "medium", val: 0.42 },
              { k: "FaceMesh jaw jitter", lvl: score<60?"medium":"low", val: score<60?0.55:0.18 },
              { k: "Luminance imbalance", lvl: "low", val: 0.12 },
            ].map(a=>(
              <li key={a.k}>
                <span>{a.k}</span>
                <span className={`art-chip ${a.lvl}`}>{a.lvl}</span>
                <span className="mono art-val">{a.val.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Sticky action bar */}
      <div className="sticky-actions">
        <button className="btn btn-glass btn-sm" onClick={onReset}>↻ New analysis</button>
        <button className="btn btn-glass btn-sm">⤓ PDF report</button>
        <button className="btn btn-glass btn-sm">⎘ Copy link</button>
        <button className="btn btn-primary btn-sm btn-shiny">Share verdict →</button>
      </div>
    </div>
  );
}

function ScoreRing({ value, size = 96, color = "safe" }) {
  const r = size/2 - 6;
  const c = 2 * Math.PI * r;
  const off = c - (value/100) * c;
  const stroke = color === "safe" ? "var(--ds-safe)" : color === "warn" ? "var(--ds-warn)" : "var(--ds-danger)";
  return (
    <svg width={size} height={size} className="score-ring">
      <circle cx={size/2} cy={size/2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="4" fill="none"/>
      <circle cx={size/2} cy={size/2} r={r} stroke={stroke} strokeWidth="4" fill="none"
        strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`} style={{ transition: "stroke-dashoffset 900ms var(--e-out)", filter: `drop-shadow(0 0 8px ${stroke})` }}/>
      <text x={size/2} y={size/2+2} textAnchor="middle" dominantBaseline="middle"
        fontFamily="var(--ff-mono)" fontSize={size*0.28} fill="var(--ds-ink)" fontWeight="500">{value}</text>
    </svg>
  );
}

window.DSParts2 = { AnalyzeDemo };
