const { useState: uS3, useEffect: uE3, useRef: uR3 } = React;

// ============ COMPARISON MATRIX ============
function Comparison() {
  const rows = [
    ["Multimodal (img/video/text/screenshot)", true, false, "partial", false],
    ["Grad-CAM++ heatmap + ELA + EXIF", true, "partial", false, false],
    ["LLM plain-English explanation", true, false, false, false],
    ["Trusted-source cross-reference", true, false, false, "manual"],
    ["Temporal + audio video analysis", true, false, false, false],
    ["Local-first processing", true, false, false, true],
    ["Open-source models", true, false, false, true],
    ["PDF forensic report", true, "partial", false, false],
  ];
  const cols = ["DeepShield", "Reality Defender", "Deepware", "Manual review"];
  return (
    <section className="ds-compare" id="compare">
      <div className="ds-container">
        <div className="ds-section-head">
          <span className="eyebrow">Why DeepShield</span>
          <h2 className="display">Forensics <em className="italic accent">without the noise.</em></h2>
        </div>
        <div className="cmp glass">
          <div className="cmp-row cmp-head">
            <div className="cmp-cell"/>
            {cols.map((c,i)=>(
              <div key={c} className={`cmp-cell ${i===0?"highlight":""}`}>{c}</div>
            ))}
          </div>
          {rows.map(([label, ...vals])=>(
            <div key={label} className="cmp-row">
              <div className="cmp-cell cmp-label">{label}</div>
              {vals.map((v,i)=>(
                <div key={i} className={`cmp-cell ${i===0?"highlight":""}`}>
                  {v===true && <span className="chk ok">●</span>}
                  {v===false && <span className="chk no">○</span>}
                  {v==="partial" && <span className="chk part mono">partial</span>}
                  {v==="manual" && <span className="chk part mono">manual</span>}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ============ IMPACT MARQUEE ============
function Marquee() {
  const incidents = [
    { date: "Mar 2024", head: "Fabricated Zelensky surrender broadcast", src: "REUTERS", verdict: "FAKE" },
    { date: "Feb 2024", head: "AI-generated Biden robocall targets NH voters", src: "AP", verdict: "FAKE" },
    { date: "Jan 2024", head: "Taylor Swift deepfakes surge across X", src: "BBC", verdict: "FAKE" },
    { date: "Nov 2023", head: "Manipulated Netanyahu audio circulates", src: "FT", verdict: "SUSPICIOUS" },
    { date: "Jul 2023", head: "Synthetic Xi speech on Taiwan", src: "WSJ", verdict: "FAKE" },
    { date: "May 2023", head: "Pentagon explosion image goes viral", src: "AP", verdict: "FAKE" },
  ];
  const doubled = [...incidents, ...incidents];
  return (
    <section className="ds-marquee">
      <div className="ds-section-head center">
        <span className="eyebrow">Real-world impact</span>
        <h2 className="display">The incidents <em className="italic accent">we train on.</em></h2>
      </div>
      <div className="mq-track-wrap">
        <div className="mq-track">
          {doubled.map((it,i)=>(
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

// ============ FAQ ============
function FAQ() {
  const qs = [
    ["How accurate is DeepShield?", "Our ensemble (EfficientNetAutoAttB4 + ViT) achieves 92.4% accuracy on the FaceForensics++ c40 test set with an isotonic-calibrated false-positive rate below 3% on unedited camera photos."],
    ["Which media types are supported?", "Images (JPEG/PNG/WebP), videos (MP4/WebM/MOV up to 100MB), news text (50–10,000 chars), and social-media screenshots via EasyOCR."],
    ["Do you retain uploaded files?", "No. Files are hashed, analyzed, and deleted within the request lifecycle unless you opt in to the 30-day dedup cache, which stores only the SHA-256 and derived signals — never the raw media."],
    ["What models power the explainability layer?", "Grad-CAM++ for visual evidence, Error-Level Analysis for compression tampering, Pillow/exifread for metadata, and Gemini 1.5 Flash for the plain-English summary."],
    ["Can I run this on-premise?", "Yes. The FastAPI backend runs entirely offline with local model weights. NewsData.io lookup is optional and disabled by env flag."],
    ["Which languages do you handle?", "English and Hindi at launch via XLM-RoBERTa for text and a bilingual EasyOCR reader. Tamil, Bengali, and Marathi are on the near-term roadmap."],
  ];
  const [open, setOpen] = uS3(null);
  return (
    <section className="ds-faq">
      <div className="ds-container ds-faq-inner">
        <div className="faq-left">
          <span className="eyebrow">Questions</span>
          <h2 className="display">We're here<br/>to help.</h2>
          <p>Straight answers from the engineers who built the forensic pipeline.</p>
          <button className="btn btn-glass btn-lg">All FAQs ↗</button>
        </div>
        <div className="faq-right">
          {qs.map(([q,a],i)=>(
            <button key={q} className={`faq-item ${open===i?"open":""}`} onClick={()=>setOpen(open===i?-1:i)}>
              <div className="faq-q">
                <span>{q}</span>
                <span className="faq-plus">{open===i?"−":"+"}</span>
              </div>
              <div className="faq-a-wrap"><p className="faq-a">{a}</p></div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

// ============ CTA + FOOTER ============
function CTAFooter() {
  return (
    <>
      <section className="ds-cta">
        <div className="ds-mesh"/>
        <div className="ds-container">
          <div className="cta-card glass-strong">
            <span className="eyebrow">Start detecting</span>
            <h2 className="display">Deploy forensic certainty<br/><em className="italic accent">in your newsroom today.</em></h2>
            <p>Join newsrooms, platforms, and research labs using DeepShield as their trust instrument.</p>
            <div className="cta-row">
              <button className="btn btn-primary btn-lg btn-shiny">Get started free
                <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 7h8m0 0L7 3m4 4L7 11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" fill="none"/></svg>
              </button>
              <button className="btn btn-glass btn-lg">Request a live demo</button>
            </div>
          </div>
        </div>
      </section>
      <footer className="ds-footer">
        <div className="ds-container ds-footer-inner">
          <div className="foot-brand">
            <div className="ds-logo">
              <svg width="22" height="26" viewBox="0 0 22 26"><path d="M11 1L21 5V12.5C21 18.5 16.5 23.5 11 25C5.5 23.5 1 18.5 1 12.5V5L11 1Z" stroke="#6C7DFF" strokeWidth="1.5" fill="rgba(108,125,255,0.1)"/><path d="M6 11L10 15L16 8" stroke="#6C7DFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>
              <span>DeepShield</span>
            </div>
            <p>Forensic AI for synthetic media. Open models, local-first, no retention.</p>
            <div className="foot-trust mono">
              <span>· Local-first</span><span>· Open models</span><span>· AA contrast</span>
            </div>
          </div>
          <div className="foot-cols">
            <div><h5>Product</h5><a>Analyze</a><a>Pipeline</a><a>Explainability</a><a>API</a></div>
            <div><h5>Research</h5><a>Model cards</a><a>Benchmarks</a><a>Papers</a><a>Changelog</a></div>
            <div><h5>Company</h5><a>About</a><a>Privacy</a><a>Responsible AI</a><a>Contact</a></div>
          </div>
        </div>
        <div className="ds-container foot-bottom mono">
          <span>© 2026 DeepShield · all signals open</span>
          <span>build · v2.0.{Math.floor(Math.random()*90+10)}</span>
        </div>
      </footer>
    </>
  );
}

// ============ TWEAKS PANEL ============
function TweaksPanel({ open, onClose, state, setState }) {
  if (!open) return null;
  return (
    <div className="tweaks">
      <div className="tweaks-head">
        <strong>Tweaks</strong>
        <button onClick={onClose} className="btn btn-ghost btn-sm">×</button>
      </div>
      <div className="tweak-row">
        <label>Accent</label>
        <div className="swatches">
          {["#6C7DFF","#3DDBB3","#FFB347","#FF5E7A","#B084FF"].map(c=>(
            <button key={c} style={{background:c}} className={state.accent===c?"active":""} onClick={()=>setState({...state, accent:c})}/>
          ))}
        </div>
      </div>
      <div className="tweak-row">
        <label>Display font</label>
        <select value={state.font} onChange={e=>setState({...state, font:e.target.value})}>
          <option value="serif">Instrument Serif</option>
          <option value="sans">Geist Display</option>
          <option value="mix">Serif + italic accent</option>
        </select>
      </div>
      <div className="tweak-row">
        <label>Atmosphere</label>
        <select value={state.atmos} onChange={e=>setState({...state, atmos:e.target.value})}>
          <option value="mesh">Mesh gradient</option>
          <option value="dots">Dotted surface</option>
          <option value="both">Both</option>
          <option value="none">Clean</option>
        </select>
      </div>
      <div className="tweak-row">
        <label>Density</label>
        <input type="range" min="0.8" max="1.2" step="0.05" value={state.density} onChange={e=>setState({...state, density:+e.target.value})}/>
      </div>
      <p className="tweak-note">Changes apply live to the whole page.</p>
    </div>
  );
}

window.DSParts3 = { Comparison, Marquee, FAQ, CTAFooter, TweaksPanel };
