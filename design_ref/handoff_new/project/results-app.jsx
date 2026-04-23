const { useState: uSR, useEffect: uER, useRef: uRR } = React;

function ResultsApp() {
  const [sample] = uSR({
    id: "a8f2c1e9",
    hash: "a8f2c1e9b3d4",
    type: "image",
    filename: "press-conference.jpg",
    src: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=900&q=80&auto=format&fit=crop",
    verdict: "SUSPICIOUS",
    score: 48,
    color: "warn",
  });

  const [heatmapMode, setHeatmapMode] = uSR("heatmap");
  const [alpha, setAlpha] = uSR(0.65);
  const [expanded, setExpanded] = uSR(null);

  // ring count-up
  const [displayScore, setDisplayScore] = uSR(0);
  uER(() => {
    let start = performance.now();
    const dur = 900;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setDisplayScore(Math.round(sample.score * e));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, []);

  const { SharedNav, SharedFooter } = window.DSShared;

  return (
    <>
      <SharedNav current="history" />
      <section className="results-shell page-shell">
        <div className="results-header">
          <div>
            <div className="crumbs">
              <a href="DeepShield.html">Home</a>
              <span className="sep">/</span>
              <a href="History.html">History</a>
              <span className="sep">/</span>
              <span>{sample.id}</span>
            </div>
            <span className="eyebrow">Analysis report</span>
            <h1 className="display">{sample.filename}</h1>
            <div className="meta-row">
              <span>sha · <b>{sample.hash}</b></span>
              <span>·</span>
              <span>type · <b>{sample.type}</b></span>
              <span>·</span>
              <span>ingested · <b>2026-04-22 14:22 UTC</b></span>
              <span>·</span>
              <span>latency · <b>2.14s</b></span>
              <span>·</span>
              <span>model · <b>EfficientNetAutoAttB4 + ViT</b></span>
            </div>
          </div>
          <div className="actions">
            <a href="Analyze.html" className="btn btn-ghost btn-sm" style={{textDecoration:"none"}}>↻ New</a>
            <button className="btn btn-glass btn-sm">⤓ PDF</button>
            <button className="btn btn-glass btn-sm">⎘ Link</button>
            <button className="btn btn-primary btn-sm btn-shiny">Share →</button>
          </div>
        </div>

        <div className="results-grid">
          {/* VERDICT */}
          <VerdictCard sample={sample} displayScore={displayScore} />

          {/* MEDIA + HEATMAP + EXIF */}
          <div className="result-grid">
            <HeatmapCard sample={sample} heatmapMode={heatmapMode} setHeatmapMode={setHeatmapMode} alpha={alpha} setAlpha={setAlpha} />
            <EXIFCard />
          </div>

          {/* DETAILED BREAKDOWN (VLM) */}
          <BreakdownCard expanded={expanded} setExpanded={setExpanded} />

          {/* SOURCES + ARTIFACTS */}
          <div className="result-grid">
            <SourcesCard />
            <ArtifactsCard />
          </div>

          {/* AUDIO + TEMPORAL (collapsed for image, shown as placeholders) */}
          <div className="result-grid">
            <AudioCard />
            <TemporalCard />
          </div>

          {/* PROCESSING SUMMARY */}
          <ProcessingSummaryCard />
        </div>

        <StickyActions />
      </section>
      <SharedFooter />
    </>
  );
}

// =========== sub components ===========

function VerdictCard({ sample, displayScore }) {
  const c = sample.color;
  return (
    <div className={`verdict-card verdict-${c}`}>
      <div className="verdict-left">
        <ScoreRing value={displayScore} size={120} color={c} />
        <div>
          <span className="eyebrow">Authenticity verdict</span>
          <h3 className="display verdict-label">{sample.verdict}</h3>
          <div className="verdict-meta mono">
            <span>score · {sample.score}/100</span>
            <span>·</span>
            <span>confidence · calibrated (isotonic)</span>
          </div>
        </div>
      </div>
      <div className="verdict-llm">
        <span className="eyebrow">Plain-English summary · Gemini 1.5</span>
        <p>
          The compression profile and lighting in this image are inconsistent with a native camera capture. Skin texture shows mild over-smoothing around the jawline — a common GAN signature — but EXIF metadata and sensor noise patterns partially support authenticity. <em style={{color:"var(--ds-ink)"}}>No single signal is conclusive</em>; treat this as suspicious until corroborated with a trusted source.
        </p>
        <div className="verdict-bullets">
          <span>• Facial symmetry · uneven (62% real-like)</span>
          <span>• Skin texture · mild over-smoothing</span>
          <span>• Frequency fingerprint · no strong GAN signature</span>
        </div>
      </div>
    </div>
  );
}

function ScoreRing({ value, size = 120, color = "safe" }) {
  const r = size/2 - 7;
  const c = 2 * Math.PI * r;
  const off = c - (value/100) * c;
  const stroke = color === "safe" ? "var(--ds-safe)" : color === "warn" ? "var(--ds-warn)" : "var(--ds-danger)";
  return (
    <svg width={size} height={size} className="score-ring">
      <circle cx={size/2} cy={size/2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="5" fill="none"/>
      <circle cx={size/2} cy={size/2} r={r} stroke={stroke} strokeWidth="5" fill="none"
        strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`}
        style={{ filter: `drop-shadow(0 0 10px ${stroke})`, transition:"stroke-dashoffset 120ms linear" }}/>
      <text x={size/2} y={size/2+2} textAnchor="middle" dominantBaseline="middle"
        fontFamily="var(--ff-mono)" fontSize={size*0.28} fill="var(--ds-ink)" fontWeight="500">{value}</text>
      <text x={size/2} y={size/2 + size*0.22} textAnchor="middle" dominantBaseline="middle"
        fontFamily="var(--ff-mono)" fontSize={size*0.09} fill="var(--ds-muted)" letterSpacing="0.1em">/100</text>
    </svg>
  );
}

function HeatmapCard({ sample, heatmapMode, setHeatmapMode, alpha, setAlpha }) {
  return (
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
            <rect x="34" y="20" width="30" height="38" fill="none" stroke="var(--ds-warn)" strokeWidth="0.3" strokeDasharray="1.2"/>
            <rect x="40" y="46" width="18" height="12" fill="none" stroke="var(--ds-danger)" strokeWidth="0.3"/>
            <text x="35" y="18" fill="var(--ds-warn)" fontSize="2" className="mono">face · 0.71</text>
            <text x="41" y="45" fill="var(--ds-danger)" fontSize="1.8" className="mono">mouth · 0.62</text>
          </svg>
        )}
      </div>
      <div className="heatmap-foot">
        <span className="mono">α {alpha.toFixed(2)}</span>
        <input type="range" min="0" max="1" step="0.01" value={alpha} onChange={e=>setAlpha(+e.target.value)} />
        <span className="mono status-chip">heatmap · ready</span>
      </div>
    </div>
  );
}

function EXIFCard() {
  const rows = [
    ["Make", "Canon", "ok"],
    ["Model", "EOS R5", "ok"],
    ["DateTimeOriginal", "2026:03:14 09:22:01", "ok"],
    ["GPSInfo", "37.78°N 122.41°W", "ok"],
    ["Software", "Adobe Photoshop 24.1", "bad"],
    ["LensModel", "RF 50mm F1.2 L", "ok"],
    ["ColorSpace", "sRGB", "ok"],
    ["ExposureTime", "1/125", "ok"],
  ];
  return (
    <div className="card exif-card">
      <div className="card-head">
        <span className="eyebrow">EXIF metadata</span>
        <span className="mono small">8 fields · <span style={{color:"var(--ds-warn)"}}>−12 trust</span></span>
      </div>
      <ul className="exif-list mono">
        {rows.map(([k,v,s])=>(
          <li key={k}>
            <span>{k}</span>
            <b className={s==="bad"?"bad":""}>{v}</b>
            <em className={s}>{s==="ok"?"✓":s==="bad"?"✗":"⚠"}</em>
          </li>
        ))}
      </ul>
      <p style={{marginTop:14, fontSize:11, color:"var(--ds-muted)", lineHeight:1.6}}>
        <span style={{color:"var(--ds-warn)"}}>⚠ Software field</span> indicates post-processing in Adobe Photoshop. This weakens authenticity by 12 points but does not imply malicious manipulation.
      </p>
    </div>
  );
}

function BreakdownCard({ expanded, setExpanded }) {
  const bd = [
    { k: "Facial symmetry", v: 62, note: "Left-right alignment across eye, nose, and jaw landmarks. Slight asymmetry detected at jaw line (Δ 2.8%)." },
    { k: "Skin texture", v: 48, note: "Pore distribution and micro-shading appear over-smoothed around cheeks — mild but consistent with early-stage GAN." },
    { k: "Lighting", v: 71, note: "Light-source direction coherent across face and background. Shadow falloff matches soft-box studio lighting." },
    { k: "Background", v: 84, note: "Depth, focal blur, and edge coherence all match a medium-telephoto shot at f/2.8." },
    { k: "Anatomy", v: 29, note: "Ear geometry on left side shows unnatural curl — classic GAN failure zone." },
    { k: "Context", v: 66, note: "Objects and setting plausible. Lanyard and podium details are consistent with a real press event." },
  ];
  return (
    <div className="breakdown card">
      <div className="card-head">
        <span className="eyebrow">Detailed breakdown · Gemini Vision</span>
        <span className="mono small">6 components · click to expand</span>
      </div>
      <div className="breakdown-grid">
        {bd.map((b,i)=>(
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
  );
}

function SourcesCard() {
  const srcs = [
    { dom: "reuters.com", fav: "R", w: 1.0, sim: 0.72, title: "Press event at SF tech summit · March 14 coverage.", state: "partial" },
    { dom: "apnews.com", fav: "AP", w: 1.0, sim: 0.64, title: "AP does not have a matching pool image in this window.", state: "partial" },
    { dom: "altnews.in", fav: "AN", w: 0.95, sim: 0.41, title: "Fact-check: similar image circulating on WhatsApp — unverified origin.", state: "contradict" },
  ];
  return (
    <div className="card sources-card">
      <div className="card-head">
        <span className="eyebrow">Trusted sources · cross-reference</span>
        <span className="mono small">3 matches · 1 contradicting</span>
      </div>
      <ul className="src-list">
        {srcs.map(s=>(
          <li key={s.dom}>
            <div className="src-head">
              <span className="mono" style={{display:"inline-flex",alignItems:"center",gap:8}}>
                <span style={{width:16,height:16,display:"inline-flex",alignItems:"center",justifyContent:"center",background:s.state==="contradict"?"rgba(255,94,122,0.15)":"rgba(108,125,255,0.15)",color:s.state==="contradict"?"var(--ds-danger)":"var(--ds-brand)",borderRadius:3,fontSize:9}}>{s.fav}</span>
                {s.dom}
              </span>
              <div className="src-bar"><i style={{width: `${s.w*100}%`, background: s.state==="contradict"?"var(--ds-danger)":"var(--ds-safe)"}}/></div>
            </div>
            <p>{s.title}</p>
            <div className="src-foot mono">
              <span>sim {s.sim}</span>
              <span>weight {s.w.toFixed(2)}</span>
              {s.state==="contradict" && <span style={{color:"var(--ds-danger)"}}>contradicting</span>}
              <a>open ↗</a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ArtifactsCard() {
  const arts = [
    { k: "GAN frequency fingerprint", lvl: "low", val: 0.22 },
    { k: "JPEG Q-table anomaly", lvl: "medium", val: 0.48 },
    { k: "FaceMesh jaw jitter", lvl: "medium", val: 0.55 },
    { k: "Luminance imbalance", lvl: "low", val: 0.18 },
    { k: "Over-smoothing (high-pass)", lvl: "medium", val: 0.52 },
    { k: "Sensor noise (PRNU)", lvl: "low", val: 0.19 },
  ];
  return (
    <div className="card artifact-card">
      <div className="card-head">
        <span className="eyebrow">Artifact indicators</span>
        <span className="mono small">{arts.length} signals</span>
      </div>
      <ul className="art-list">
        {arts.map(a=>(
          <li key={a.k}>
            <span>{a.k}</span>
            <span className={`art-chip ${a.lvl}`}>{a.lvl}</span>
            <span className="mono art-val">{a.val.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function AudioCard() {
  return (
    <div className="card" style={{minHeight: 200}}>
      <div className="card-head">
        <span className="eyebrow">Audio waveform · WavLM</span>
        <span className="mono small" style={{color:"var(--ds-muted)"}}>not applicable (image input)</span>
      </div>
      <div style={{display:"flex", alignItems:"center", gap:3, height:80, opacity:0.35}}>
        {Array.from({length:80}).map((_,i)=>{
          const h = 20 + Math.abs(Math.sin(i*0.3)) * 60;
          return <span key={i} style={{flex:1, height:`${h}%`, background:"var(--ds-muted)", borderRadius:1}}/>;
        })}
      </div>
      <p style={{marginTop:14, fontSize:12, color:"var(--ds-muted)", fontFamily:"var(--ff-mono)"}}>
        audio_analysis · skipped · input is single frame · rerun as video to enable lip-sync correlation
      </p>
    </div>
  );
}

function TemporalCard() {
  return (
    <div className="card" style={{minHeight: 200}}>
      <div className="card-head">
        <span className="eyebrow">Temporal consistency</span>
        <span className="mono small" style={{color:"var(--ds-muted)"}}>not applicable (image input)</span>
      </div>
      <svg viewBox="0 0 200 80" style={{width:"100%", height:80, opacity:0.35}}>
        <path d="M0 40 Q 20 20 40 38 T 80 42 T 120 36 T 160 44 T 200 40" fill="none" stroke="var(--ds-muted)" strokeWidth="1.5"/>
        <path d="M0 50 Q 20 30 40 48 T 80 52 T 120 46 T 160 54 T 200 50" fill="none" stroke="var(--ds-muted)" strokeWidth="0.6" strokeDasharray="2 2"/>
      </svg>
      <p style={{marginTop:14, fontSize:12, color:"var(--ds-muted)", fontFamily:"var(--ff-mono)"}}>
        per_frame_score · n/a · no frames to aggregate
      </p>
    </div>
  );
}

function ProcessingSummaryCard() {
  const steps = [
    ["14:22:01.012", "Upload received", "42 KB"],
    ["14:22:01.118", "Preprocess (resize 512², BlazeFace gate)", "1 face detected"],
    ["14:22:01.334", "Ensemble forward pass (ViT + EfficientNetAutoAttB4)", "fake_p 0.52"],
    ["14:22:01.887", "Grad-CAM++ heatmap generated", "salience · jaw, mouth"],
    ["14:22:02.012", "ELA + EXIF pass", "8 fields · Photoshop detected"],
    ["14:22:02.140", "Gemini 1.5 Flash summary", "token · 387"],
    ["14:22:02.148", "Result cached", "sha · a8f2c1e9"],
  ];
  return (
    <div className="card">
      <div className="card-head">
        <span className="eyebrow">Processing summary · timeline</span>
        <span className="mono small">2.14s · 7 stages</span>
      </div>
      <ol style={{listStyle:"none", padding:0, margin:0, display:"flex", flexDirection:"column", gap:4, fontFamily:"var(--ff-mono)", fontSize:12}}>
        {steps.map(([t,s,m],i)=>(
          <li key={i} style={{
            display:"grid", gridTemplateColumns:"130px 1fr auto", gap:14, alignItems:"center",
            padding:"8px 12px", background: i%2? "rgba(255,255,255,0.02)":"transparent",
            borderRadius:6, color: "var(--ds-ink-2)"
          }}>
            <span style={{color:"var(--ds-muted)"}}>{t}</span>
            <span style={{color:"var(--ds-ink)"}}>{s}</span>
            <span style={{color:"var(--ds-muted)"}}>{m}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function StickyActions() {
  return (
    <div style={{
      position:"sticky", bottom:20, maxWidth:600, margin:"32px auto 0",
      display:"flex", gap:8, justifyContent:"center",
      padding:"10px 12px",
      background:"rgba(10,13,20,0.88)",
      border:"1px solid var(--ds-border-2)", borderRadius:14,
      backdropFilter:"blur(20px)",
      boxShadow: "0 20px 40px -20px rgba(0,0,0,0.6)",
      zIndex: 10
    }}>
      <a href="Analyze.html" className="btn btn-glass btn-sm" style={{textDecoration:"none"}}>↻ Analyze another</a>
      <button className="btn btn-glass btn-sm">⤓ PDF report</button>
      <button className="btn btn-glass btn-sm">⎘ Copy link</button>
      <button className="btn btn-primary btn-sm btn-shiny">Share verdict →</button>
    </div>
  );
}

function mountResults() {
  if (window.DSShared) {
    ReactDOM.createRoot(document.getElementById("root")).render(<ResultsApp />);
  } else setTimeout(mountResults, 50);
}
window.mountResults = mountResults;
