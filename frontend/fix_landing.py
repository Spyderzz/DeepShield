import re

def update_css():
    path = "src/pages/deepshield-landing.css"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update .mq-card contrast
    mq_old = """
.mq-card {
  width: 340px;
  padding: 20px;
  flex-shrink: 0;
  display: flex; flex-direction: column; gap: 10px;
}
.mq-head { display: flex; justify-content: space-between; align-items: center; }
.mq-head .mono { font-size: 11px; color: var(--ds-muted); }
.mq-verdict {
  font-family: var(--ff-mono);
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.mq-verdict.fake { background: rgba(255,94,122,0.15); color: var(--ds-danger); border: 1px solid rgba(255,94,122,0.3); }
.mq-verdict.suspicious { background: rgba(255,179,71,0.15); color: var(--ds-warn); border: 1px solid rgba(255,179,71,0.3); }
.mq-card h4 { margin: 0; font-family: var(--ff-display); font-size: 22px; font-weight: 400; letter-spacing: -0.01em; line-height: 1.15; }
.mq-src { font-size: 10px; color: var(--ds-muted); letter-spacing: 0.1em; margin-top: auto; }
""".strip()
    mq_new = """
.mq-card {
  width: 340px;
  padding: 24px;
  flex-shrink: 0;
  display: flex; flex-direction: column; gap: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  backdrop-filter: blur(16px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 4px 20px rgba(0,0,0,0.4);
}
.mq-head { display: flex; justify-content: space-between; align-items: center; }
.mq-head .mono { font-size: 11px; color: var(--ds-ink-2); }
.mq-verdict {
  font-family: var(--ff-mono);
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.mq-verdict.fake { background: rgba(255,94,122,0.15); color: var(--ds-danger); border: 1px solid rgba(255,94,122,0.3); }
.mq-verdict.suspicious { background: rgba(255,179,71,0.15); color: var(--ds-warn); border: 1px solid rgba(255,179,71,0.3); }
.mq-card h4 { margin: 0; font-family: var(--ff-display); font-size: 24px; font-weight: 400; letter-spacing: -0.01em; line-height: 1.15; color: #FFFFFF; }
.mq-src { font-size: 11px; color: var(--ds-muted); letter-spacing: 0.1em; margin-top: auto; }
""".strip()

    content = content.replace(mq_old, mq_new)

    # 2. Update .cmp-cell.highlight
    cmp_old = """
.cmp-cell.highlight { background: rgba(108,125,255,0.04); position: relative; }
.cmp-cell.highlight::before {
  content: ""; position: absolute; left: 0; right: 0; top: 0; bottom: 0;
  border-left: 1px solid rgba(108,125,255,0.2);
  border-right: 1px solid rgba(108,125,255,0.2);
  pointer-events: none;
}
.cmp-head .cmp-cell.highlight { color: var(--ds-brand); }
""".strip()
    cmp_new = """
.cmp-cell.highlight { background: rgba(108,125,255,0.04); position: relative; }
.cmp-cell.highlight::before {
  content: ""; position: absolute; left: 0; right: 0; top: 0; bottom: 0;
  border-left: 1px solid rgba(108,125,255,0.3);
  border-right: 1px solid rgba(108,125,255,0.3);
  background: linear-gradient(180deg, rgba(108,125,255,0.08) 0%, transparent 100%);
  pointer-events: none;
}
.cmp-head .cmp-cell.highlight { color: var(--ds-brand); font-weight: 500; text-shadow: 0 0 12px rgba(108,125,255,0.4); }
""".strip()

    content = content.replace(cmp_old, cmp_new)

    # 3. Update .mv block
    # We will use regex to replace everything from .mv-image to .mv-shot-line.hl
    pattern = re.compile(r'\.mv-image \{.*?\.mv-shot-line\.hl \{[^\}]+\}', re.DOTALL)
    
    mv_new = """
.mv-image { background: linear-gradient(135deg, #0a0d14, #151a28); }
.img-wireframe {
  position: absolute; inset: 10px;
  background: 
    linear-gradient(rgba(108,125,255,0.1) 1px, transparent 1px) 0 0 / 20px 20px,
    linear-gradient(90deg, rgba(108,125,255,0.1) 1px, transparent 1px) 0 0 / 20px 20px;
  mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
}
.img-scanline {
  position: absolute; left: 0; right: 0; height: 2px;
  background: var(--ds-brand-2); box-shadow: 0 0 10px var(--ds-brand-2);
  animation: imgScan 3s linear infinite;
}
@keyframes imgScan { 0% { top: 0; opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { top: 100%; opacity: 0; } }
.img-bbox {
  position: absolute; top: 30%; left: 30%; width: 40%; height: 40%;
  border: 1px dashed var(--ds-danger);
  background: rgba(255,94,122,0.1);
  box-shadow: 0 0 0 4px rgba(255,94,122,0.05);
  animation: pulseBox 2s infinite alternate;
}
@keyframes pulseBox { from { transform: scale(0.98); opacity: 0.8; } to { transform: scale(1.02); opacity: 1; } }

.mv-video { background: #0A0D14; perspective: 400px; display: flex; align-items: center; justify-content: center; }
.mv-video-track {
  position: relative; width: 120px; height: 80px;
  transform-style: preserve-3d;
  transform: rotateY(-30deg) rotateX(10deg);
}
.mv-video-frame {
  position: absolute; inset: 0;
  border: 1px solid rgba(108,125,255,0.3);
  background: rgba(108,125,255,0.05);
  border-radius: 4px;
}
.mv-video-frame.f1 { transform: translateZ(-30px); opacity: 0.4; }
.mv-video-frame.f2 { transform: translateZ(0px); border-color: var(--ds-danger); background: rgba(255,94,122,0.1); box-shadow: 0 0 15px rgba(255,94,122,0.2); }
.mv-video-frame.f3 { transform: translateZ(30px); opacity: 0.8; }
.mv-video-playhead {
  position: absolute; bottom: 10px; left: 10%; width: 80%; height: 2px; background: rgba(255,255,255,0.2);
}
.mv-video-playhead::after {
  content: ''; position: absolute; top: -4px; left: 40%; width: 10px; height: 10px;
  background: var(--ds-danger); border-radius: 50%; box-shadow: 0 0 8px var(--ds-danger);
}

.mv-audio { background: #0A0D14; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.mv-audio-wave { display: flex; align-items: center; gap: 2px; height: 80px; }
.mv-audio-wave span {
  width: 4px; border-radius: 2px;
  background: var(--ds-safe);
  height: calc(10px + var(--s) * 60px);
  animation: waveAnim 1s infinite alternate ease-in-out;
  animation-delay: calc(var(--i, 0) * -0.1s);
}
.mv-audio-wave span.warn { background: var(--ds-warn); box-shadow: 0 0 8px var(--ds-warn); }
@keyframes waveAnim { 0% { transform: scaleY(0.8); } 100% { transform: scaleY(1.2); } }

.mv-text {
  padding: 14px;
  font-size: 11px;
  line-height: 1.6;
  color: var(--ds-ink-2);
  background: linear-gradient(180deg, #0a0d14, #0f1420);
}
.mv-text p { margin: 0 0 6px; }
.mv-text mark {
  color: inherit; background: transparent;
  padding: 0 2px;
  border-radius: 2px;
}
.hl-danger { background: rgba(255,94,122,0.18); color: var(--ds-danger); border-bottom: 1px solid var(--ds-danger); }
.hl-warn { background: rgba(255,179,71,0.15); color: var(--ds-warn); border-bottom: 1px solid var(--ds-warn); }
.hl-safe { background: rgba(61,219,179,0.15); color: var(--ds-safe); border-bottom: 1px solid var(--ds-safe); }

.mv-shot { background: #0A0D14; position: relative; }
.shot-box {
  position: absolute; border: 1px solid rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.03); border-radius: 2px;
}
.shot-box.b1 { top: 20%; left: 10%; width: 60%; height: 15px; }
.shot-box.b2 { top: 40%; left: 10%; width: 40%; height: 30px; border-color: var(--ds-danger); background: rgba(255,94,122,0.1); box-shadow: 0 0 10px rgba(255,94,122,0.15); }
.shot-box.b3 { top: 75%; left: 10%; width: 80%; height: 15px; }
.shot-score {
  position: absolute; top: -8px; right: -8px;
  font-size: 8px; font-family: var(--ff-mono);
  padding: 1px 4px; border-radius: 2px; background: #000;
}
.shot-score.safe { color: var(--ds-safe); border: 1px solid var(--ds-safe); }
.shot-score.danger { color: var(--ds-danger); border: 1px solid var(--ds-danger); }
""".strip()
    
    content = pattern.sub(mv_new, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_jsx():
    path = "src/pages/HomePage.jsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update ModalityVisual
    pattern1 = re.compile(r'function ModalityVisual\(\{ kind \}\) \{.*?  \);\n\}', re.DOTALL)
    mv_jsx = """
function ModalityVisual({ kind }) {
  if (kind === 'Video') return (
    <div className="mv mv-video">
      <div className="mv-video-track">
        <div className="mv-video-frame f1"></div>
        <div className="mv-video-frame f2"></div>
        <div className="mv-video-frame f3"></div>
      </div>
      <div className="mv-video-playhead"></div>
    </div>
  );
  if (kind === 'Audio') return (
    <div className="mv mv-audio">
      <div className="mv-audio-wave">
        {Array.from({ length: 40 }).map((_, i) => {
          const s = Math.abs(Math.sin(i * 0.3) * Math.cos(i * 0.7));
          return <span key={i} style={{ '--s': s, '--i': i }} className={s > 0.6 ? 'warn' : ''} />;
        })}
      </div>
    </div>
  );
  if (kind === 'Text') return (
    <div className="mv mv-text mono">
      <p><mark className="hl-warn">BREAKING:</mark> sources <mark className="hl-danger">allegedly confirm</mark> that <mark className="hl-safe">Reuters</mark> published…</p>
      <p><mark className="hl-danger">SHOCKING truth</mark> experts refuse to believe.</p>
    </div>
  );
  if (kind === 'Screenshot') return (
    <div className="mv mv-shot">
      <div className="shot-box b1"><div className="shot-score safe">98%</div></div>
      <div className="shot-box b2"><div className="shot-score danger">12%</div></div>
      <div className="shot-box b3"><div className="shot-score safe">89%</div></div>
    </div>
  );
  // Image default
  return (
    <div className="mv mv-image">
      <div className="img-wireframe"></div>
      <div className="img-scanline"></div>
      <div className="img-bbox"></div>
    </div>
  );
}
""".strip()
    content = pattern1.sub(mv_jsx, content)

    # 2. Update Comparison columns
    content = content.replace("const cols = ['DeepShield', 'Reality Defender', 'Deepware', 'Manual review'];", "const cols = ['DeepShield', 'Enterprise API Providers', 'Legacy Forensic Tools', 'Manual Review (OSINT)'];")

    # 3. Update AnalyzeDemo initial state
    demo_old = """
function AnalyzeDemo() {
  const [stage, setStage] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [activeStage, setActiveStage] = useState(0);
  const [sampleIdx, setSampleIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [uploadedUrl, setUploadedUrl] = useState(null);
""".strip()

    demo_new = """
const DEFAULT_RESULT = {
  analysis_id: "demo-8f9a2b",
  authenticity_score: 18,
  verdict: "fake",
  processing_time_ms: 840,
  models: {
    ensemble: { prediction: "fake", confidence: 0.88 },
    exif: { suspicious_tags: {"Software": "Adobe Photoshop 24.0"} },
    ela: { suspicious_regions_detected: true },
  },
  llm_summary: {
    model: "Cognitive Analysis",
    summary: "Our cognitive analysis indicates multiple structural anomalies consistent with synthetic generation. Error-Level Analysis reveals significant JPEG compression variance in the facial region, and visual heatmapping highlights structural discontinuities typical of diffusion models. Metadata shows recent manipulation in a photo editing suite."
  },
  trusted_sources: [
    { title: "AI Generated Portraits Database", url: "#", domain: "example.com", sim: 0.94, trust_weight: 0.8 },
    { title: "Synthetic Media Tracker", url: "#", domain: "example.com", sim: 0.88, trust_weight: 0.9 }
  ],
  artifacts: [
    { name: 'GAN frequency fingerprint', severity: 'high', score: 0.84 },
    { name: 'JPEG Q-table anomaly', severity: 'medium', score: 0.62 },
    { name: 'FaceMesh jaw jitter', severity: 'low', score: 0.18 },
  ]
};

function AnalyzeDemo() {
  const [stage, setStage] = useState('result');
  const [progress, setProgress] = useState(100);
  const [activeStage, setActiveStage] = useState(STAGES.length - 1);
  const [sampleIdx, setSampleIdx] = useState(0);
  const [result, setResult] = useState(DEFAULT_RESULT);
  const [uploadedUrl, setUploadedUrl] = useState(SAMPLES[0].src);
""".strip()

    content = content.replace(demo_old, demo_new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    update_css()
    update_jsx()
    print("Done")
