const { useState: uSA, useEffect: uEA, useRef: uRA } = React;

function AnalyzeApp() {
  const [mode, setMode] = uSA("image");
  const [stage, setStage] = uSA("idle"); // idle | processing | done
  const [progress, setProgress] = uSA(0);
  const [activeStage, setActiveStage] = uSA(0);
  const [textVal, setTextVal] = uSA("");
  const [cache, setCache] = uSA(true);
  const [urlVal, setUrlVal] = uSA("");
  const [lang, setLang] = uSA("en");

  const segRefs = uRA([]);
  const [segPill, setSegPill] = uSA({ left: 0, width: 0 });

  const modes = [
    { k: "image", label: "Image", icon: "🖼" },
    { k: "video", label: "Video", icon: "▶" },
    { k: "text", label: "Text", icon: "¶" },
    { k: "screenshot", label: "Screenshot", icon: "▭" },
  ];

  uEA(() => {
    const idx = modes.findIndex(m => m.k === mode);
    const el = segRefs.current[idx];
    if (el) setSegPill({ left: el.offsetLeft, width: el.offsetWidth });
  }, [mode]);

  const modeStages = {
    image: ["Upload", "Preprocess", "ViT + EfficientNet", "Grad-CAM++", "ELA + EXIF", "LLM summary"],
    video: ["Upload", "Extract frames", "Per-frame classify", "Temporal consistency", "Audio lip-sync", "LLM summary"],
    text: ["Paste", "Tokenize (XLM-R)", "Sensationalism", "NER + source lookup", "Truth-override", "LLM summary"],
    screenshot: ["Upload", "EasyOCR", "Layout anomaly", "Claim credibility", "Phrase map", "LLM summary"],
  };

  uEA(() => {
    if (stage !== "processing") return;
    const stages = modeStages[mode];
    let p = 0;
    const id = setInterval(() => {
      p += 1.8;
      setProgress(p);
      setActiveStage(Math.min(stages.length - 1, Math.floor(p / (100 / stages.length))));
      if (p >= 100) {
        clearInterval(id);
        setTimeout(() => {
          // navigate to results with pretend id
          window.location.href = "Results.html";
        }, 400);
      }
    }, 80);
    return () => clearInterval(id);
  }, [stage, mode]);

  const start = () => { setProgress(0); setActiveStage(0); setStage("processing"); };
  const canStart = mode === "text" ? textVal.trim().length > 50 : true;

  const sampleSrc = "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=640&q=80&auto=format&fit=crop";

  const { SharedNav, SharedFooter } = window.DSShared;
  const { LayerStack } = window.DSParts1;

  return (
    <>
      <SharedNav current="analyze" />
      <section className="analyze-shell page-shell">
        <div className="page-head">
          <div className="crumbs">
            <a href="DeepShield.html">Home</a>
            <span className="sep">/</span>
            <span>Analyze</span>
          </div>
          <span className="eyebrow">Forensic console</span>
          <h1 className="display">Analyze <em className="italic accent">any media.</em></h1>
          <p className="sub">Drop an image, video, article, or screenshot. The pipeline routes to the right forensic stack and returns a calm, evidence-backed verdict.</p>
        </div>

        <div style={{display:"flex", justifyContent:"center", marginBottom: 32}}>
          <div className="mode-seg">
            <div className="mode-seg-pill" style={{ left: segPill.left, width: segPill.width }}/>
            {modes.map((m, i) => (
              <button key={m.k} ref={el => segRefs.current[i] = el}
                className={`mode-seg-btn ${mode===m.k?"active":""}`}
                onClick={() => { setMode(m.k); setStage("idle"); }}>
                <span style={{opacity:0.6}}>{m.icon}</span>{m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="analyze-panel">
          <div className="analyze-console">
            {stage === "idle" && mode !== "text" && (
              <>
                <div className="drop-large" onClick={start}>
                  <div className="blob">
                    <svg viewBox="0 0 200 200">
                      <defs>
                        <linearGradient id="blobg" x1="0" y1="0" x2="1" y2="1">
                          <stop stopColor="#7F8FFF"/><stop offset="1" stopColor="#3DDBB3"/>
                        </linearGradient>
                      </defs>
                      <path d="M100 20 C140 20 170 50 170 90 C170 130 140 170 100 170 C60 170 30 130 30 90 C30 50 60 20 100 20 Z"
                        fill="none" stroke="url(#blobg)" strokeWidth="1.2" strokeDasharray="5 7" opacity="0.55"/>
                      <path d="M100 60 L100 120 M80 100 L100 120 L120 100" stroke="url(#blobg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                    </svg>
                  </div>
                  <h2 className="display">Drop {mode} here</h2>
                  <p className="hint">{mode==="image"?"PNG · JPEG · WebP · 20MB":mode==="video"?"MP4 · WebM · MOV · 100MB":"PNG · JPEG · 20MB"}</p>
                  <p className="or-paste">or paste a URL · or click to browse</p>
                  <button className="btn btn-glass btn-sm" onClick={(e)=>{e.stopPropagation(); start();}}>Use sample</button>
                </div>
                <div className="options-row">
                  <label className="opt"><input type="checkbox" checked={cache} onChange={e=>setCache(e.target.checked)} /> Cache result</label>
                  <input type="text" placeholder={mode==="image"?"…or paste image URL":"…or paste media URL"} value={urlVal} onChange={e=>setUrlVal(e.target.value)} />
                  <div className="grow"/>
                  <select value={lang} onChange={e=>setLang(e.target.value)}>
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="ta">Tamil</option>
                    <option value="bn">Bengali</option>
                  </select>
                </div>
              </>
            )}

            {stage === "idle" && mode === "text" && (
              <>
                <div className="text-panel">
                  <div className="ta-head">
                    <span className="eyebrow">Paste article text</span>
                    <span className="ta-meta">{textVal.length} / 10000 chars · min 50</span>
                  </div>
                  <textarea
                    placeholder="Paste a news headline and article body. DeepShield runs XLM-RoBERTa, NER-anchored source lookup, and truth-override against trusted Indian + international domains."
                    value={textVal}
                    onChange={e=>setTextVal(e.target.value.slice(0,10000))}
                  />
                  <button
                    className="btn btn-primary btn-lg btn-shiny"
                    disabled={!canStart}
                    style={{ alignSelf: "flex-start", opacity: canStart?1:0.5, cursor: canStart?"pointer":"not-allowed" }}
                    onClick={start}>
                    Analyze text →
                  </button>
                </div>
                <div className="options-row">
                  <label className="opt"><input type="checkbox" checked={cache} onChange={e=>setCache(e.target.checked)}/> Cache result</label>
                  <div className="grow"/>
                  <select value={lang} onChange={e=>setLang(e.target.value)}>
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                  </select>
                </div>
              </>
            )}

            {stage === "processing" && (
              <div className="processing-wrap">
                <div>
                  {mode !== "text" ? (
                    <div className="stack-scene mini" style={{height: 380}}>
                      <LayerStack src={sampleSrc} density={6} />
                    </div>
                  ) : (
                    <TextProcessingViz />
                  )}
                </div>
                <div>
                  <div className="p-stages-head">
                    <span className="eyebrow">Pipeline</span>
                    <span className="mono" style={{fontSize:11, color:"var(--ds-muted)"}}>{Math.round(progress)}%</span>
                  </div>
                  <div className="p-stages-bar"><i style={{ width: `${progress}%` }}/></div>
                  <ol className="stage-list">
                    {modeStages[mode].map((s,i)=>(
                      <li key={s} className={i<activeStage?"done":i===activeStage?"active":""}>
                        <span className="stage-dot"/>
                        <span className="stage-label">{s}</span>
                        <span className="mono stage-status">{i<activeStage?"✓":i===activeStage?"···":"—"}</span>
                      </li>
                    ))}
                  </ol>
                  <p style={{color:"var(--ds-muted)", fontSize:12, marginTop:20, fontFamily:"var(--ff-mono)"}}>
                    job · {Math.random().toString(36).slice(2,10).toUpperCase()} · cache · {cache?"on":"off"} · lang · {lang}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="recent-rail">
          <h3>Recent analyses</h3>
          <div className="recent-grid">
            {[
              { src: "https://images.unsplash.com/photo-1488554378835-f7acf46e6c98?w=300&q=80&auto=format", v: "FAKE", c: "danger", t: "Staged portrait", d: "2m ago" },
              { src: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&q=80&auto=format", v: "REAL", c: "safe", t: "Press photo", d: "14m ago" },
              { src: "https://images.unsplash.com/photo-1496128858413-b36217c2ce36?w=300&q=80&auto=format", v: "SUSP", c: "warn", t: "Social post", d: "1h ago" },
              { src: "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=300&q=80&auto=format", v: "FAKE", c: "danger", t: "Pipeline test", d: "3h ago" },
            ].map((r,i)=>(
              <a className="recent-card" href="Results.html" key={i}>
                <div className="recent-thumb" style={{backgroundImage:`url(${r.src})`}}>
                  <span className={`verdict-dot h-verdict ${r.c}`} style={{position:"absolute", top:8, right:8, padding:"2px 7px", fontSize:9}}>{r.v}</span>
                </div>
                <div className="recent-title">{r.t}</div>
                <div className="recent-meta"><span>sha · {Math.random().toString(36).slice(2,8)}</span><span>{r.d}</span></div>
              </a>
            ))}
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}

function TextProcessingViz() {
  const [idx, setIdx] = uSA(0);
  const lines = [
    { t: "BREAKING: sources allegedly confirm", hl: [[0,9,"warn"],[19,38,"danger"]] },
    { t: "shocking truth experts refuse to believe", hl: [[0,16,"danger"]] },
    { t: "cross-reference · Reuters · matched", hl: [[18,25,"safe"]] },
    { t: "sensationalism score 0.74 · truth -0.41", hl: [[22,27,"warn"],[37,42,"danger"]] },
  ];
  uEA(() => {
    const id = setInterval(()=>setIdx(i=>(i+1)%lines.length), 900);
    return () => clearInterval(id);
  }, []);
  return (
    <div style={{
      padding:24, background:"rgba(0,0,0,0.4)", border:"1px solid var(--ds-border)",
      borderRadius:14, fontFamily:"var(--ff-mono)", fontSize:13, color:"var(--ds-ink-2)",
      minHeight: 380, display:"flex", flexDirection:"column", justifyContent:"center", gap:14
    }}>
      {lines.map((line,i) => {
        const active = i === idx;
        return (
          <div key={i} style={{
            opacity: i <= idx ? 1 : 0.25,
            transition:"opacity 400ms, transform 400ms",
            transform: active?"translateX(6px)":"translateX(0)",
            color: active?"var(--ds-ink)":"var(--ds-ink-2)",
          }}>
            <span style={{color:"var(--ds-muted)", marginRight:10}}>&gt;</span>{line.t}
            {active && <span style={{marginLeft:10, color:"var(--ds-brand-2)"}}>◉</span>}
          </div>
        );
      })}
    </div>
  );
}

function mountAnalyze() {
  if (window.DSShared && window.DSParts1) {
    ReactDOM.createRoot(document.getElementById("root")).render(<AnalyzeApp />);
  } else setTimeout(mountAnalyze, 50);
}
window.mountAnalyze = mountAnalyze;
