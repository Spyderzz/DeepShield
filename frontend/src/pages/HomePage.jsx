import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

/* ─── CONSTANTS ──────────────────────────────────────────────── */
const DARK   = '#0A0A0F';
const DARK2  = '#0F1018';
const CREAM  = '#F2EEE7';
const CREAM2 = '#E8E3DA';
const BLUE   = '#2B70E8';
const AMBER  = '#F5A623';
const GREEN  = '#22C55E';
const WHITE  = '#F0EDE8';
const FONT_D = "'Libre Bodoni', Georgia, serif";
const FONT_B = "'Figtree', -apple-system, BlinkMacSystemFont, sans-serif";

/* ─── CSS KEYFRAMES + GOOGLE FONTS ───────────────────────────── */
function useHeadAssets() {
  useEffect(() => {
    const fontLink = document.createElement('link');
    fontLink.rel = 'stylesheet';
    fontLink.href = 'https://fonts.googleapis.com/css2?family=Libre+Bodoni:ital,wght@0,400;0,700;0,800;1,400;1,700;1,800&family=Figtree:wght@300;400;500;600;700&display=swap';
    document.head.appendChild(fontLink);

    const style = document.createElement('style');
    style.textContent = `
      @keyframes ds-float-a {
        0%,100% { transform: translateY(0px) translateX(0px) scale(1); }
        33%     { transform: translateY(-38px) translateX(22px) scale(1.07); }
        66%     { transform: translateY(18px) translateX(-14px) scale(0.95); }
      }
      @keyframes ds-float-b {
        0%,100% { transform: translateY(0px) translateX(0px) scale(1); }
        40%     { transform: translateY(28px) translateX(-32px) scale(1.1); }
        75%     { transform: translateY(-20px) translateX(18px) scale(0.93); }
      }
      @keyframes ds-float-c {
        0%,100% { transform: translateY(0px) translateX(0px); }
        50%     { transform: translateY(-25px) translateX(25px); }
      }
      @keyframes ds-card-float {
        0%,100% { transform: perspective(1100px) rotateX(6deg) rotateY(-14deg) rotateZ(1.5deg) translateY(0px); }
        50%     { transform: perspective(1100px) rotateX(4deg) rotateY(-11deg) rotateZ(1deg) translateY(-14px); }
      }
      @keyframes ds-scan {
        0%   { top: 8%; opacity: 1; }
        90%  { top: 88%; opacity: 1; }
        100% { top: 88%; opacity: 0; }
      }
      @keyframes ds-marquee {
        from { transform: translateX(0); }
        to   { transform: translateX(-50%); }
      }
      @keyframes ds-hero-in {
        from { opacity: 0; transform: translateY(32px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes ds-reveal {
        from { opacity: 0; transform: translateY(44px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes ds-pulse-ring {
        0%   { transform: scale(0.92); opacity: 0.7; }
        50%  { transform: scale(1.06); opacity: 0.3; }
        100% { transform: scale(0.92); opacity: 0.7; }
      }
      .ds-reveal-item {
        opacity: 0;
        transform: translateY(44px);
      }
      .ds-reveal-item.ds-visible {
        animation: ds-reveal 0.75s cubic-bezier(0.22,1,0.36,1) forwards;
      }
      .ds-marquee-track:hover .ds-marquee-inner {
        animation-play-state: paused !important;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(fontLink);
      document.head.removeChild(style);
    };
  }, []);
}

/* ─── REVEAL ITEM COMPONENT ──────────────────────────────────── */
function RevealItem({ children, delay = 0, style = {} }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { el.classList.add('ds-visible'); obs.disconnect(); } },
      { threshold: 0.1 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div
      ref={ref}
      className="ds-reveal-item"
      style={{ animationDelay: `${delay}ms`, ...style }}
    >
      {children}
    </div>
  );
}

/* ─── BOKEH BG COMPONENT ─────────────────────────────────────── */
function BokehBg({ variant = 'dark' }) {
  const circles = variant === 'dark' ? [
    { w:520, h:520, top:'8%',  left:'-12%', color:'rgba(43,112,232,0.18)',  blur:110, anim:'ds-float-a 11s ease-in-out infinite' },
    { w:380, h:380, top:'55%', left:'70%',  color:'rgba(245,166,35,0.12)',  blur:90,  anim:'ds-float-b 14s ease-in-out infinite' },
    { w:300, h:300, top:'25%', left:'60%',  color:'rgba(43,112,232,0.10)',  blur:80,  anim:'ds-float-c 9s ease-in-out infinite' },
    { w:240, h:240, top:'70%', left:'15%',  color:'rgba(34,197,94,0.10)',   blur:70,  anim:'ds-float-a 16s ease-in-out infinite 2s' },
    { w:200, h:200, top:'5%',  left:'80%',  color:'rgba(139,92,246,0.12)',  blur:65,  anim:'ds-float-b 12s ease-in-out infinite 4s' },
  ] : [
    { w:460, h:460, top:'5%',  left:'-8%', color:'rgba(43,112,232,0.07)',  blur:100, anim:'ds-float-b 13s ease-in-out infinite' },
    { w:320, h:320, top:'50%', left:'72%', color:'rgba(245,166,35,0.06)',  blur:80,  anim:'ds-float-a 11s ease-in-out infinite 1s' },
    { w:280, h:280, top:'30%', left:'55%', color:'rgba(34,197,94,0.05)',   blur:70,  anim:'ds-float-c 10s ease-in-out infinite' },
  ];

  return (
    <div style={{ position:'absolute', inset:0, overflow:'hidden', pointerEvents:'none', zIndex:0 }}>
      {circles.map((c, i) => (
        <div key={i} style={{
          position:'absolute', top:c.top, left:c.left,
          width:c.w, height:c.h, borderRadius:'50%',
          background:c.color, filter:`blur(${c.blur}px)`,
          animation:c.anim,
        }} />
      ))}
    </div>
  );
}

/* ─── ANIMATED COUNTER ───────────────────────────────────────── */
function useCounter(target, duration = 1800) {
  const [count, setCount] = useState(0);
  const [started, setStarted] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !started) { setStarted(true); obs.disconnect(); } },
      { threshold: 0.4 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [started]);

  useEffect(() => {
    if (!started) return;
    let startTime = null;
    const step = (ts) => {
      if (!startTime) startTime = ts;
      const pct = Math.min((ts - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - pct, 3);
      setCount(Math.round(eased * target));
      if (pct < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [started, target, duration]);

  return [count, ref];
}

function Counter({ target, suffix = '', prefix = '' }) {
  const [count, ref] = useCounter(target);
  return <span ref={ref}>{prefix}{count.toLocaleString()}{suffix}</span>;
}

/* ─── 3D ANALYSIS CARD ───────────────────────────────────────── */
function AnalysisCard3D() {
  const circumference = 2 * Math.PI * 54;
  return (
    <div style={{ animation: 'ds-card-float 5s ease-in-out infinite', transformOrigin: 'center center' }}>
      <div style={{
        transform: 'perspective(1100px) rotateX(6deg) rotateY(-14deg) rotateZ(1.5deg)',
        width: 320, background: 'linear-gradient(145deg, #141520 0%, #0D0E1A 100%)',
        borderRadius: 20, border: '1px solid rgba(43,112,232,0.25)',
        boxShadow: '0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05), inset 0 1px 0 rgba(255,255,255,0.07)',
        overflow: 'hidden', position: 'relative',
      }}>
        {/* scanning line */}
        <div style={{
          position:'absolute', left:0, right:0, height:2,
          background:'linear-gradient(90deg, transparent, rgba(43,112,232,0.8), transparent)',
          animation:'ds-scan 3s ease-in-out infinite', zIndex:10,
        }} />
        {/* header */}
        <div style={{ padding:'16px 20px 12px', borderBottom:'1px solid rgba(255,255,255,0.06)', display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ width:8, height:8, borderRadius:'50%', background:GREEN, boxShadow:`0 0 10px ${GREEN}` }} />
          <span style={{ fontFamily:FONT_B, fontSize:11, color:'rgba(255,255,255,0.5)', letterSpacing:'0.12em', textTransform:'uppercase' }}>Live Analysis</span>
          <span style={{ marginLeft:'auto', fontFamily:FONT_B, fontSize:10, color:'rgba(255,255,255,0.3)' }}>DeepShield v3.2</span>
        </div>
        {/* face preview */}
        <div style={{ margin:'18px auto 6px', width:80, height:80, borderRadius:10, background:'linear-gradient(135deg,#1c2240,#0f1428)', position:'relative', display:'flex', alignItems:'center', justifyContent:'center' }}>
          <svg width="40" height="40" viewBox="0 0 44 44" fill="none">
            <circle cx="22" cy="16" r="10" fill="rgba(255,255,255,0.12)" />
            <ellipse cx="22" cy="38" rx="16" ry="10" fill="rgba(255,255,255,0.08)" />
            <circle cx="16" cy="15" r="2" fill="rgba(255,255,255,0.4)" />
            <circle cx="28" cy="15" r="2" fill="rgba(255,255,255,0.4)" />
            <path d="M17 21 Q22 24 27 21" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          </svg>
          <div style={{ position:'absolute', top:4, left:4, width:12, height:12, borderTop:`2px solid ${BLUE}`, borderLeft:`2px solid ${BLUE}` }} />
          <div style={{ position:'absolute', top:4, right:4, width:12, height:12, borderTop:`2px solid ${BLUE}`, borderRight:`2px solid ${BLUE}` }} />
          <div style={{ position:'absolute', bottom:4, left:4, width:12, height:12, borderBottom:`2px solid ${BLUE}`, borderLeft:`2px solid ${BLUE}` }} />
          <div style={{ position:'absolute', bottom:4, right:4, width:12, height:12, borderBottom:`2px solid ${BLUE}`, borderRight:`2px solid ${BLUE}` }} />
        </div>
        {/* score ring */}
        <div style={{ display:'flex', justifyContent:'center', marginBottom:12 }}>
          <svg width="120" height="120" viewBox="0 0 132 132">
            <circle cx="66" cy="66" r="54" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
            <motion.circle
              cx="66" cy="66" r="54" fill="none"
              stroke="url(#scoreGrad)" strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: circumference * 0.12 }}
              transition={{ duration: 1.8, ease: 'easeOut', delay: 0.5 }}
              style={{ transformOrigin:'66px 66px', transform:'rotate(-90deg)' }}
            />
            <defs>
              <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#FF4444" />
                <stop offset="100%" stopColor="#FF6B35" />
              </linearGradient>
            </defs>
            <text x="66" y="60" textAnchor="middle" fill="#FF4444" fontSize="24" fontFamily={FONT_D} fontWeight="700">88%</text>
            <text x="66" y="76" textAnchor="middle" fill="rgba(255,255,255,0.45)" fontSize="10" fontFamily={FONT_B}>DEEPFAKE</text>
          </svg>
        </div>
        {/* signal bars */}
        {[
          { label:'Facial Artifacts', pct:92, color:'#FF4444' },
          { label:'Audio Sync',       pct:76, color:AMBER },
          { label:'Metadata',         pct:44, color:GREEN },
        ].map(bar => (
          <div key={bar.label} style={{ padding:'0 20px 10px' }}>
            <div style={{ display:'flex', justifyContent:'space-between', marginBottom:4 }}>
              <span style={{ fontFamily:FONT_B, fontSize:10, color:'rgba(255,255,255,0.5)' }}>{bar.label}</span>
              <span style={{ fontFamily:FONT_B, fontSize:10, color:bar.color, fontWeight:600 }}>{bar.pct}%</span>
            </div>
            <div style={{ height:3, borderRadius:2, background:'rgba(255,255,255,0.06)' }}>
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${bar.pct}%` }}
                transition={{ duration: 1.2, ease: 'easeOut', delay: 0.8 }}
                style={{ height:'100%', borderRadius:2, background:`linear-gradient(90deg, ${bar.color}88, ${bar.color})` }}
              />
            </div>
          </div>
        ))}
        {/* footer badge */}
        <div style={{ margin:'6px 20px 18px', padding:'9px 14px', background:'rgba(255,68,68,0.1)', borderRadius:8, border:'1px solid rgba(255,68,68,0.2)', display:'flex', alignItems:'center', gap:8 }}>
          <div style={{ width:6, height:6, borderRadius:'50%', background:'#FF4444', flexShrink:0, animation:'ds-pulse-ring 1.8s ease-in-out infinite' }} />
          <span style={{ fontFamily:FONT_B, fontSize:10, color:'rgba(255,255,255,0.7)', fontWeight:500 }}>High confidence deepfake detected</span>
        </div>
      </div>
    </div>
  );
}

/* ─── MARQUEE IMPACT CARDS ───────────────────────────────────── */
const IMPACT_CARDS = [
  { icon:'$', label:'$25B+',    desc:'Financial fraud via deepfakes annually' },
  { icon:'%', label:'68%',      desc:'of voters saw AI election misinformation' },
  { icon:'↑', label:'900%',     desc:'Increase in deepfake content since 2019' },
  { icon:'!', label:'96%',      desc:'of deepfakes target women non-consensually' },
  { icon:'🌍', label:'47',      desc:'Countries hit by AI disinformation in 2024' },
  { icon:'⏱', label:'3 sec',   desc:'Time to clone a voice with AI today' },
  { icon:'🔐', label:'1 in 5', desc:'Enterprises hit by deepfake attacks in 2024' },
  { icon:'📰', label:'84%',     desc:'of news consumers can\'t spot synthetic media' },
];

function MarqueeSection() {
  return (
    <section style={{ background: DARK, padding: '60px 0', overflow: 'hidden', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <span style={{ fontFamily: FONT_B, fontSize: 12, letterSpacing: '0.18em', textTransform: 'uppercase', color: AMBER, fontWeight: 600 }}>The Crisis Is Real</span>
      </div>
      <div className="ds-marquee-track" style={{ position: 'relative', cursor: 'default' }}>
        <div className="ds-marquee-inner" style={{
          display: 'flex', gap: 20, width: 'max-content',
          animation: 'ds-marquee 40s linear infinite',
        }}>
          {[...IMPACT_CARDS, ...IMPACT_CARDS].map((card, i) => (
            <div key={i} style={{
              minWidth: 220, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
              borderRadius: 14, padding: '20px 22px', flexShrink: 0,
            }}>
              <div style={{ fontFamily: FONT_D, fontSize: 30, fontWeight: 800, color: WHITE, marginBottom: 4 }}>{card.label}</div>
              <div style={{ fontFamily: FONT_B, fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 1.5 }}>{card.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── FAQ ACCORDION ──────────────────────────────────────────── */
const FAQS = [
  { q: 'How accurate is DeepShield\'s detection?', a: 'Our ensemble of EfficientNet + ViT models achieves 97.3% accuracy on the FaceForensics++ benchmark. We continuously retrain on emerging deepfake techniques to maintain detection rates as generation methods evolve.' },
  { q: 'What media formats are supported?', a: 'DeepShield supports images (JPEG, PNG, WEBP, HEIC), videos (MP4, MOV, AVI, MKV up to 500MB), and audio (MP3, WAV, M4A). Video frames are sampled intelligently for efficiency.' },
  { q: 'How fast is the analysis?', a: 'Images return results in under 3 seconds. Videos are processed at ~2× real-time speed — a 30-second clip returns in approximately 15 seconds.' },
  { q: 'Is my uploaded content private?', a: 'Files are encrypted in transit and at rest. We delete uploaded media within 24 hours. We never use your content to train our models without explicit written consent.' },
  { q: 'Can DeepShield detect AI-generated images (not just face swaps)?', a: 'Yes. Beyond face manipulation, DeepShield detects fully synthetic portraits, GAN artifacts, diffusion model fingerprints, and metadata anomalies that indicate AI origin.' },
  { q: 'Do you offer an API for developers?', a: 'Yes — REST and WebSocket APIs with Python, JavaScript, and Go SDKs. Webhooks supported for async video processing. Enterprise plans include SLA guarantees and dedicated infrastructure.' },
];

function FAQItem({ q, a, index }) {
  const [open, setOpen] = useState(false);
  return (
    <RevealItem delay={index * 80}>
      <div style={{ borderBottom: '1px solid rgba(10,10,15,0.12)' }}>
        <button
          onClick={() => setOpen(o => !o)}
          style={{
            width: '100%', textAlign: 'left', padding: '22px 0',
            background: 'transparent', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
          }}
        >
          <span style={{ fontFamily: FONT_D, fontSize: 18, fontWeight: 700, color: DARK, lineHeight: 1.3 }}>{q}</span>
          <span style={{
            flexShrink: 0, width: 28, height: 28, borderRadius: '50%',
            background: open ? BLUE : 'rgba(10,10,15,0.08)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.25s ease', color: open ? '#fff' : DARK,
            fontSize: 18, lineHeight: 1,
          }}>{open ? '−' : '+'}</span>
        </button>
        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              style={{ overflow: 'hidden' }}
            >
              <p style={{ fontFamily: FONT_B, fontSize: 15, color: 'rgba(10,10,15,0.65)', lineHeight: 1.75, paddingBottom: 22, margin: 0 }}>{a}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </RevealItem>
  );
}

/* ─── COMPARISON DATA ────────────────────────────────────────── */
const COMPARISON = [
  { feature: 'Detection Accuracy',        ds: '97.3%',       others: '~72–85%' },
  { feature: 'Face Swap Detection',       ds: '✓',           others: 'Partial' },
  { feature: 'GAN / Diffusion Detection', ds: '✓',           others: '✗' },
  { feature: 'Audio Deepfake Analysis',   ds: '✓',           others: 'Rare' },
  { feature: 'Real-time Video API',       ds: '✓',           others: 'Limited' },
  { feature: 'Explainability Heatmaps',   ds: '✓',           others: '✗' },
  { feature: 'Open API + SDKs',           ds: '✓',           others: 'Partial' },
  { feature: 'SOC 2 Compliance',          ds: 'In Progress', others: 'Varies' },
];

/* ─── HOW IT WORKS ───────────────────────────────────────────── */
const STEPS = [
  { n:'01', title:'Upload Media',       desc:'Drag-and-drop your image, video, or audio. We support all major formats up to 500MB.' },
  { n:'02', title:'Deep Analysis',      desc:'Ensemble EfficientNet + Vision Transformer scans every frame for manipulation artifacts.' },
  { n:'03', title:'Confidence Report',  desc:'Per-frame heatmap, confidence score, and a full breakdown of detected anomalies.' },
  { n:'04', title:'Take Action',        desc:'Export the verified report, share via link, or integrate via API into your workflow.' },
];

/* ─── TECH TAGS ──────────────────────────────────────────────── */
const TECH = ['EfficientNet B4', 'Vision Transformer', 'PyTorch', 'ONNX Runtime', 'React 18', 'Node.js', 'PostgreSQL', 'Redis', 'FF++ Dataset', 'Grad-CAM Heatmaps'];

/* ─── TRUST BADGES ───────────────────────────────────────────── */
const TRUST = [
  { label: '97.3%', sub: 'Detection Accuracy' },
  { label: '<3s',   sub: 'Image Analysis Time' },
  { label: '50M+',  sub: 'Frames Analyzed' },
  { label: '12+',   sub: 'Deepfake Types Detected' },
];

/* ─── MAIN PAGE ──────────────────────────────────────────────── */
export default function HomePage() {
  useHeadAssets();
  const navigate = useNavigate();

  return (
    <div style={{ fontFamily: FONT_B, overflowX: 'hidden' }}>

      {/* ── HERO ─────────────────────────────────────────────── */}
      <section style={{
        background: DARK, position: 'relative', minHeight: '100vh',
        display: 'flex', alignItems: 'center', overflow: 'hidden',
      }}>
        <BokehBg variant="dark" />
        <div style={{
          position:'absolute', inset:0, zIndex:1, pointerEvents:'none',
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          maskImage: 'radial-gradient(ellipse 80% 60% at 50% 50%, black 40%, transparent 100%)',
          WebkitMaskImage: 'radial-gradient(ellipse 80% 60% at 50% 50%, black 40%, transparent 100%)',
        }} />

        <div style={{ position:'relative', zIndex:2, maxWidth:1240, margin:'0 auto', padding:'120px 40px 80px', width:'100%' }}>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:60, alignItems:'center' }}>
            {/* left */}
            <div>
              <div style={{ animation:'ds-hero-in 0.7s cubic-bezier(0.22,1,0.36,1) both', animationDelay:'0.1s' }}>
                <span style={{
                  display:'inline-flex', alignItems:'center', gap:8,
                  fontFamily:FONT_B, fontSize:12, fontWeight:600, letterSpacing:'0.14em', textTransform:'uppercase',
                  color:BLUE, background:'rgba(43,112,232,0.12)', border:'1px solid rgba(43,112,232,0.2)',
                  padding:'6px 14px', borderRadius:100, marginBottom:32,
                }}>
                  <span style={{ width:6, height:6, borderRadius:'50%', background:GREEN, display:'inline-block', boxShadow:`0 0 8px ${GREEN}` }} />
                  AI-Powered Deepfake Detection
                </span>
              </div>

              <div style={{ animation:'ds-hero-in 0.7s cubic-bezier(0.22,1,0.36,1) both', animationDelay:'0.2s' }}>
                <h1 style={{
                  fontFamily: FONT_D, fontSize: 'clamp(48px, 5.5vw, 78px)',
                  fontWeight: 800, fontStyle: 'italic', color: WHITE,
                  lineHeight: 1.06, margin: '0 0 24px', letterSpacing: '-0.02em',
                }}>
                  Unmask the<br />
                  <span style={{ color: BLUE }}>Synthetic.</span><br />
                  Protect the<br />
                  <span style={{ background: `linear-gradient(135deg, ${AMBER}, #FFC857)`, WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent', backgroundClip:'text' }}>Real.</span>
                </h1>
              </div>

              <div style={{ animation:'ds-hero-in 0.7s cubic-bezier(0.22,1,0.36,1) both', animationDelay:'0.35s' }}>
                <p style={{ fontFamily:FONT_B, fontSize:17, color:'rgba(240,237,232,0.62)', lineHeight:1.75, maxWidth:460, margin:'0 0 40px' }}>
                  DeepShield uses ensemble deep learning to detect face swaps, synthetic portraits, and audio clones — with 97.3% accuracy, in seconds.
                </p>
              </div>

              <div style={{ display:'flex', gap:14, flexWrap:'wrap', animation:'ds-hero-in 0.7s cubic-bezier(0.22,1,0.36,1) both', animationDelay:'0.5s' }}>
                <button
                  onClick={() => navigate('/analyze')}
                  style={{
                    background: BLUE, color: '#fff', border:'none', cursor:'pointer',
                    padding:'14px 30px', borderRadius:10, fontSize:15, fontWeight:600, fontFamily:FONT_B,
                    boxShadow:`0 0 0 1px ${BLUE}, 0 8px 32px rgba(43,112,232,0.4)`,
                    transition:'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.transform='translateY(-2px)'; e.currentTarget.style.boxShadow=`0 0 0 1px ${BLUE}, 0 14px 40px rgba(43,112,232,0.55)`; }}
                  onMouseLeave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow=`0 0 0 1px ${BLUE}, 0 8px 32px rgba(43,112,232,0.4)`; }}
                >
                  Analyze Media Free →
                </button>
                <button
                  onClick={() => navigate('/about')}
                  style={{
                    background:'transparent', color:WHITE, border:`1px solid rgba(240,237,232,0.18)`,
                    cursor:'pointer', padding:'14px 30px', borderRadius:10, fontSize:15, fontWeight:500, fontFamily:FONT_B,
                    transition:'all 0.2s ease',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor='rgba(240,237,232,0.45)'; e.currentTarget.style.background='rgba(240,237,232,0.05)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor='rgba(240,237,232,0.18)'; e.currentTarget.style.background='transparent'; }}
                >
                  How It Works
                </button>
              </div>

              <div style={{ display:'flex', gap:36, marginTop:48, animation:'ds-hero-in 0.7s cubic-bezier(0.22,1,0.36,1) both', animationDelay:'0.65s' }}>
                {[
                  { v:97, s:'%', label:'Accuracy' },
                  { v:3,  s:'s', pre:'<', label:'Analysis Speed' },
                  { v:50, s:'M+', label:'Frames Analyzed' },
                ].map(stat => (
                  <div key={stat.label}>
                    <div style={{ fontFamily:FONT_D, fontSize:30, fontWeight:800, color:WHITE, fontStyle:'italic' }}>
                      <Counter target={stat.v} suffix={stat.s} prefix={stat.pre||''} />
                    </div>
                    <div style={{ fontFamily:FONT_B, fontSize:11, color:'rgba(255,255,255,0.38)', marginTop:2, letterSpacing:'0.05em' }}>{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* right — 3D card */}
            <div style={{ display:'flex', justifyContent:'center', alignItems:'center' }}>
              <AnalysisCard3D />
            </div>
          </div>
        </div>

        <div style={{ position:'absolute', bottom:0, left:0, right:0, height:120, background:`linear-gradient(to bottom, transparent, ${DARK})`, zIndex:2, pointerEvents:'none' }} />
      </section>

      {/* ── MARQUEE ───────────────────────────────────────────── */}
      <MarqueeSection />

      {/* ── PROBLEM — CREAM ──────────────────────────────────── */}
      <section style={{ background: CREAM, padding: '120px 40px', position:'relative', overflow:'hidden' }}>
        <BokehBg variant="cream" />
        <div style={{ maxWidth:1240, margin:'0 auto', position:'relative', zIndex:1 }}>
          <RevealItem>
            <span style={{ fontFamily:FONT_B, fontSize:12, fontWeight:600, letterSpacing:'0.14em', textTransform:'uppercase', color:BLUE, marginBottom:20, display:'block' }}>The Problem</span>
          </RevealItem>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:80, alignItems:'start' }}>
            <RevealItem delay={100}>
              <h2 style={{ fontFamily:FONT_D, fontSize:'clamp(36px,4.2vw,60px)', fontWeight:800, fontStyle:'italic', color:DARK, lineHeight:1.1, margin:0 }}>
                Synthetic media is eroding trust at scale.
              </h2>
            </RevealItem>
            <div>
              {[
                { h:'Politicians impersonated',  b:'AI-generated video of political figures making false statements has influenced elections in 6 countries since 2023.' },
                { h:'Executives cloned for fraud', b:'Deepfake voice and video calls have successfully impersonated CEOs to authorize $25M+ in fraudulent wire transfers.' },
                { h:'Non-consensual imagery',     b:'Over 96% of deepfakes online are non-consensual intimate imagery, targeting private individuals.' },
              ].map((item, i) => (
                <RevealItem key={i} delay={160 + i * 100}>
                  <div style={{ marginBottom: 28 }}>
                    <h3 style={{ fontFamily:FONT_D, fontSize:19, fontWeight:700, color:DARK, margin:'0 0 8px' }}>{item.h}</h3>
                    <p style={{ fontFamily:FONT_B, fontSize:15, color:'rgba(10,10,15,0.58)', lineHeight:1.75, margin:0 }}>{item.b}</p>
                  </div>
                </RevealItem>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── COMPARISON — DARK ────────────────────────────────── */}
      <section style={{ background: DARK2, padding: '120px 40px', position:'relative', overflow:'hidden' }}>
        <BokehBg variant="dark" />
        <div style={{ maxWidth:1100, margin:'0 auto', position:'relative', zIndex:1 }}>
          <RevealItem style={{ textAlign:'center', marginBottom:64 }}>
            <span style={{ fontFamily:FONT_B, fontSize:12, fontWeight:600, letterSpacing:'0.14em', textTransform:'uppercase', color:AMBER, display:'block', marginBottom:16 }}>Why DeepShield</span>
            <h2 style={{ fontFamily:FONT_D, fontSize:'clamp(34px,3.8vw,54px)', fontWeight:800, fontStyle:'italic', color:WHITE, lineHeight:1.1, margin:0 }}>
              Not all detectors are built equal.
            </h2>
          </RevealItem>
          <RevealItem delay={120}>
            <div style={{ borderRadius:16, overflow:'hidden', border:'1px solid rgba(255,255,255,0.07)', background:'rgba(255,255,255,0.02)' }}>
              <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr 1fr', background:'rgba(255,255,255,0.04)', padding:'14px 28px', borderBottom:'1px solid rgba(255,255,255,0.07)' }}>
                <span style={{ fontFamily:FONT_B, fontSize:11, fontWeight:600, letterSpacing:'0.1em', textTransform:'uppercase', color:'rgba(255,255,255,0.35)' }}>Feature</span>
                <span style={{ fontFamily:FONT_B, fontSize:11, fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase', color:BLUE, textAlign:'center' }}>DeepShield</span>
                <span style={{ fontFamily:FONT_B, fontSize:11, fontWeight:600, letterSpacing:'0.1em', textTransform:'uppercase', color:'rgba(255,255,255,0.28)', textAlign:'center' }}>Others</span>
              </div>
              {COMPARISON.map((row, i) => (
                <div key={i} style={{ display:'grid', gridTemplateColumns:'2fr 1fr 1fr', padding:'15px 28px', borderBottom: i < COMPARISON.length-1 ? '1px solid rgba(255,255,255,0.05)' : 'none', alignItems:'center', background: i%2===0 ? 'transparent' : 'rgba(255,255,255,0.012)' }}>
                  <span style={{ fontFamily:FONT_B, fontSize:14, color:'rgba(255,255,255,0.62)' }}>{row.feature}</span>
                  <span style={{ fontFamily:FONT_B, fontSize:14, fontWeight:600, color:GREEN, textAlign:'center' }}>{row.ds}</span>
                  <span style={{ fontFamily:FONT_B, fontSize:14, color:'rgba(255,255,255,0.28)', textAlign:'center' }}>{row.others}</span>
                </div>
              ))}
            </div>
          </RevealItem>
        </div>
      </section>

      {/* ── HOW IT WORKS — CREAM ─────────────────────────────── */}
      <section style={{ background: CREAM2, padding: '120px 40px', overflow:'hidden' }}>
        <div style={{ maxWidth:1240, margin:'0 auto' }}>
          <RevealItem style={{ textAlign:'center', marginBottom:72 }}>
            <span style={{ fontFamily:FONT_B, fontSize:12, fontWeight:600, letterSpacing:'0.14em', textTransform:'uppercase', color:BLUE, display:'block', marginBottom:16 }}>Process</span>
            <h2 style={{ fontFamily:FONT_D, fontSize:'clamp(34px,3.8vw,54px)', fontWeight:800, fontStyle:'italic', color:DARK, lineHeight:1.1, margin:0 }}>
              From upload to verdict in seconds.
            </h2>
          </RevealItem>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:24 }}>
            {STEPS.map((step, i) => (
              <RevealItem key={i} delay={i * 110}>
                <div
                  style={{ background:'rgba(10,10,15,0.04)', borderRadius:16, padding:'30px 26px', border:'1px solid rgba(10,10,15,0.07)', position:'relative', overflow:'hidden', transition:'transform 0.25s ease, box-shadow 0.25s ease', cursor:'default' }}
                  onMouseEnter={e => { e.currentTarget.style.transform='translateY(-5px)'; e.currentTarget.style.boxShadow='0 20px 50px rgba(10,10,15,0.1)'; }}
                  onMouseLeave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow='none'; }}
                >
                  <div style={{ fontFamily:FONT_D, fontSize:60, fontWeight:800, color:'rgba(10,10,15,0.04)', position:'absolute', top:4, right:14, lineHeight:1 }}>{step.n}</div>
                  <div style={{ fontFamily:FONT_D, fontStyle:'italic', fontSize:36, fontWeight:800, color:`rgba(43,112,232,0.2)`, marginBottom:14, lineHeight:1 }}>{step.n}</div>
                  <h3 style={{ fontFamily:FONT_D, fontSize:21, fontWeight:700, color:DARK, margin:'0 0 10px' }}>{step.title}</h3>
                  <p style={{ fontFamily:FONT_B, fontSize:14, color:'rgba(10,10,15,0.52)', lineHeight:1.75, margin:0 }}>{step.desc}</p>
                </div>
              </RevealItem>
            ))}
          </div>
        </div>
      </section>

      {/* ── TECH STACK — DARK ────────────────────────────────── */}
      <section style={{ background: DARK, padding: '80px 40px', position:'relative', overflow:'hidden' }}>
        <BokehBg variant="dark" />
        <div style={{ maxWidth:1240, margin:'0 auto', position:'relative', zIndex:1 }}>
          <RevealItem style={{ textAlign:'center', marginBottom:48 }}>
            <span style={{ fontFamily:FONT_B, fontSize:12, fontWeight:600, letterSpacing:'0.14em', textTransform:'uppercase', color:'rgba(255,255,255,0.3)', display:'block', marginBottom:14 }}>Built With</span>
            <h2 style={{ fontFamily:FONT_D, fontSize:'clamp(28px,3vw,44px)', fontWeight:800, fontStyle:'italic', color:'rgba(255,255,255,0.65)', lineHeight:1.1, margin:0 }}>
              Industry-grade infrastructure.
            </h2>
          </RevealItem>
          <div style={{ display:'flex', flexWrap:'wrap', gap:14, justifyContent:'center' }}>
            {TECH.map((t, i) => (
              <RevealItem key={i} delay={i * 55}>
                <div
                  style={{ background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:100, padding:'9px 20px', fontFamily:FONT_B, fontSize:13, color:'rgba(255,255,255,0.55)', fontWeight:500, transition:'all 0.2s ease', cursor:'default' }}
                  onMouseEnter={e => { e.currentTarget.style.background='rgba(43,112,232,0.12)'; e.currentTarget.style.borderColor='rgba(43,112,232,0.3)'; e.currentTarget.style.color=WHITE; }}
                  onMouseLeave={e => { e.currentTarget.style.background='rgba(255,255,255,0.04)'; e.currentTarget.style.borderColor='rgba(255,255,255,0.07)'; e.currentTarget.style.color='rgba(255,255,255,0.55)'; }}
                >
                  {t}
                </div>
              </RevealItem>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ — CREAM ──────────────────────────────────────── */}
      <section style={{ background: CREAM, padding: '120px 40px', overflow:'hidden' }}>
        <div style={{ maxWidth:780, margin:'0 auto' }}>
          <RevealItem style={{ marginBottom:60 }}>
            <span style={{ fontFamily:FONT_B, fontSize:12, fontWeight:600, letterSpacing:'0.14em', textTransform:'uppercase', color:BLUE, display:'block', marginBottom:16 }}>FAQ</span>
            <h2 style={{ fontFamily:FONT_D, fontSize:'clamp(34px,3.8vw,52px)', fontWeight:800, fontStyle:'italic', color:DARK, lineHeight:1.1, margin:0 }}>
              Questions, answered.
            </h2>
          </RevealItem>
          {FAQS.map((faq, i) => (
            <FAQItem key={i} q={faq.q} a={faq.a} index={i} />
          ))}
        </div>
      </section>

      {/* ── TRUST + CTA — DARK ───────────────────────────────── */}
      <section style={{ background: DARK, padding: '120px 40px', position:'relative', overflow:'hidden' }}>
        <BokehBg variant="dark" />
        <div style={{ maxWidth:1240, margin:'0 auto', position:'relative', zIndex:1 }}>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:18, marginBottom:100 }}>
            {TRUST.map((badge, i) => (
              <RevealItem key={i} delay={i * 80}>
                <div style={{ textAlign:'center', padding:'28px 20px', borderRadius:14, background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.07)' }}>
                  <div style={{ fontFamily:FONT_D, fontSize:36, fontWeight:800, fontStyle:'italic', color:WHITE, marginBottom:6 }}>{badge.label}</div>
                  <div style={{ fontFamily:FONT_B, fontSize:11, color:'rgba(255,255,255,0.38)', textTransform:'uppercase', letterSpacing:'0.1em' }}>{badge.sub}</div>
                </div>
              </RevealItem>
            ))}
          </div>

          <RevealItem delay={80} style={{ textAlign:'center' }}>
            <h2 style={{ fontFamily:FONT_D, fontSize:'clamp(40px,4.8vw,70px)', fontWeight:800, fontStyle:'italic', color:WHITE, lineHeight:1.06, margin:'0 0 24px', maxWidth:720, marginLeft:'auto', marginRight:'auto' }}>
              Start detecting deepfakes<br />
              <span style={{ color:BLUE }}>right now.</span>
            </h2>
            <p style={{ fontFamily:FONT_B, fontSize:17, color:'rgba(255,255,255,0.48)', lineHeight:1.7, maxWidth:480, margin:'0 auto 44px' }}>
              Free for the first 10 analyses. No credit card required. Enterprise plans with SLA guarantees available.
            </p>
            <div style={{ display:'flex', gap:14, justifyContent:'center', flexWrap:'wrap' }}>
              <button
                onClick={() => navigate('/analyze')}
                style={{
                  background: BLUE, color:'#fff', border:'none', cursor:'pointer',
                  padding:'16px 38px', borderRadius:10, fontSize:16, fontWeight:600, fontFamily:FONT_B,
                  boxShadow:`0 0 0 1px ${BLUE}, 0 8px 40px rgba(43,112,232,0.4)`,
                  transition:'all 0.22s ease',
                }}
                onMouseEnter={e => { e.currentTarget.style.transform='translateY(-2px)'; e.currentTarget.style.boxShadow=`0 0 0 1px ${BLUE}, 0 16px 50px rgba(43,112,232,0.6)`; }}
                onMouseLeave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow=`0 0 0 1px ${BLUE}, 0 8px 40px rgba(43,112,232,0.4)`; }}
              >
                Analyze Media Free →
              </button>
              <button
                onClick={() => navigate('/register')}
                style={{
                  background:'transparent', color:WHITE, border:`1px solid rgba(240,237,232,0.18)`,
                  cursor:'pointer', padding:'16px 38px', borderRadius:10, fontSize:16, fontWeight:500, fontFamily:FONT_B,
                  transition:'all 0.22s ease',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor='rgba(240,237,232,0.45)'; e.currentTarget.style.background='rgba(240,237,232,0.05)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor='rgba(240,237,232,0.18)'; e.currentTarget.style.background='transparent'; }}
              >
                Create Free Account
              </button>
            </div>
          </RevealItem>
        </div>
      </section>

    </div>
  );
}
