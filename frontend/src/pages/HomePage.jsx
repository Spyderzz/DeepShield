import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';

// ─── Inject font + marquee keyframe into <head> ───────────────────────────────
function useHeadAssets() {
  useEffect(() => {
    const font = document.createElement('link');
    font.rel = 'stylesheet';
    font.href = 'https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&display=swap';
    document.head.appendChild(font);

    const style = document.createElement('style');
    style.id = 'ds-landing-styles';
    style.textContent = `
      html { scroll-behavior: smooth; }
      @keyframes ds-scroll {
        from { transform: translateX(0); }
        to   { transform: translateX(-50%); }
      }
      .ds-marquee-track {
        display: flex; gap: 16px; width: max-content;
        animation: ds-scroll 38s linear infinite;
      }
      .ds-marquee-wrap:hover .ds-marquee-track { animation-play-state: paused; }
      @media (prefers-reduced-motion: reduce) {
        .ds-marquee-track { animation: none; }
        html { scroll-behavior: auto; }
      }
      @media (max-width: 820px) {
        .ds-hero-cols { grid-template-columns: 1fr !important; }
        .ds-auth-mock { display: none !important; }
        .ds-steps-grid { grid-template-columns: 1fr 1fr !important; }
      }
      @media (max-width: 500px) {
        .ds-steps-grid { grid-template-columns: 1fr !important; }
        .ds-tech-grid  { grid-template-columns: 1fr 1fr !important; }
        .ds-trust-grid { grid-template-columns: 1fr !important; }
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(font);
      const s = document.getElementById('ds-landing-styles');
      if (s) document.head.removeChild(s);
    };
  }, []);
}

// ─── SVG Icons ────────────────────────────────────────────────────────────────
const Ic = ({ d, size = 20, fill = 'none', sw = 2 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke="currentColor"
    strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {d}
  </svg>
);

const IShield   = ({ s }) => <Ic size={s} d={<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />} />;
const ICode     = ({ s }) => <Ic size={s} d={<><polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" /></>} />;
const ILock     = ({ s }) => <Ic size={s} d={<><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></>} />;
const IEye      = ({ s }) => <Ic size={s} d={<><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></>} />;
const ICheck    = ({ s = 16 }) => <Ic size={s} sw={2.5} d={<polyline points="20 6 9 17 4 12" />} />;
const IXmark    = ({ s = 16 }) => <Ic size={s} sw={2.5} d={<><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>} />;
const IMinus    = ({ s = 16 }) => <Ic size={s} sw={2.5} d={<line x1="5" y1="12" x2="19" y2="12" />} />;
const IUpload   = ({ s }) => <Ic size={s} d={<><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></>} />;
const ICpu      = ({ s }) => <Ic size={s} d={<><rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" /><line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" /><line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" /><line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" /></>} />;
const ISearch   = ({ s }) => <Ic size={s} d={<><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></>} />;
const IFile     = ({ s }) => <Ic size={s} d={<><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></>} />;
const IChevron  = ({ s = 18 }) => <Ic size={s} sw={2.5} d={<polyline points="6 9 12 15 18 9" />} />;
const IAlert    = ({ s }) => <Ic size={s} d={<><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></>} />;
const IDollar   = ({ s }) => <Ic size={s} d={<><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></>} />;
const IImage    = ({ s }) => <Ic size={s} d={<><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></>} />;
const IBroadcast= ({ s }) => <Ic size={s} d={<><circle cx="12" cy="12" r="2" /><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14" /></>} />;
const IUser     = ({ s }) => <Ic size={s} d={<><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></>} />;
const IMsg      = ({ s }) => <Ic size={s} d={<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />} />;

// ─── Data ─────────────────────────────────────────────────────────────────────
const STORIES = [
  { id:1, Icon:IAlert,     badge:'HIGH RISK',  bc:'#C62828', title:'2024 US Election Deepfakes',     desc:'AI-generated candidate videos circulated on social media days before elections, reaching millions of voters.' },
  { id:2, Icon:IDollar,    badge:'FINANCIAL',  bc:'#E65100', title:'CEO Voice Clone Fraud',          desc:'Synthetic audio of a CEO used to authorize a $243K wire transfer — undetected by the finance team.' },
  { id:3, Icon:IImage,     badge:'MISLEADING', bc:'#6A1B9A', title:'Viral Fake Protest Photos',      desc:'AI-generated crowd images shared as real protest evidence across major news networks worldwide.' },
  { id:4, Icon:IMsg,       badge:'HEALTH',     bc:'#1565C0', title:'Fake News Screenshot Chains',   desc:'Fabricated WhatsApp screenshots spread dangerous medical misinformation during a public health crisis.' },
  { id:5, Icon:IBroadcast, badge:'PROPAGANDA', bc:'#B71C1C', title:'Synthetic Face News Anchors',   desc:'State-sponsored deepfake news anchors broadcast political propaganda across international audiences.' },
  { id:6, Icon:IUser,      badge:'HARMFUL',    bc:'#37474F', title:'Sports Star Face Swap',         desc:'Celebrity face-swap videos created and distributed without the subject\'s consent.' },
];
const DOUBLED = [...STORIES, ...STORIES];

const ROWS = [
  { f:'Explainable AI (Grad-CAM++)',  ds:true,  rd:false,      dw:false, m:false },
  { f:'Multi-modal (4 media types)',  ds:true,  rd:'partial',  dw:false, m:false },
  { f:'LLM Plain-English Summary',    ds:true,  rd:false,      dw:false, m:false },
  { f:'EXIF Metadata Analysis',       ds:true,  rd:false,      dw:false, m:'partial' },
  { f:'Audio Deepfake Detection',     ds:true,  rd:'partial',  dw:false, m:false },
  { f:'Open-Source Model Weights',    ds:true,  rd:false,      dw:false, m:false },
  { f:'Free Tier Available',          ds:true,  rd:false,      dw:true,  m:true },
  { f:'PDF Audit Report',             ds:true,  rd:true,       dw:false, m:false },
  { f:'Privacy-First (local run)',    ds:true,  rd:false,      dw:false, m:true },
];

const STEPS = [
  { n:1, Icon:IUpload, title:'Upload',  desc:'Drop an image, video, screenshot, or paste article text. Supports JPG, PNG, MP4, WebM and more.' },
  { n:2, Icon:ICpu,    title:'Analyze', desc:'Multi-model AI ensemble runs in parallel — EfficientNet, ViT, Grad-CAM++, LLM, and audio checks.' },
  { n:3, Icon:ISearch, title:'Explain', desc:'Inspect heatmaps, manipulation indicators, EXIF signals, and trusted-source evidence in full detail.' },
  { n:4, Icon:IFile,   title:'Report',  desc:'Download a PDF audit trail or revisit any past analysis through your personal history dashboard.' },
];

const TECH = [
  { name:'EfficientNet B4',        task:'Image Deepfake',        detail:'DFDC-trained ensemble',  ac:'#1565C0' },
  { name:'ViT + FaceForensics++',  task:'Face Manipulation',     detail:'Fine-tuned on c40',      ac:'#0D47A1' },
  { name:'Grad-CAM++',             task:'Visual Explainability', detail:'Last 3 encoder layers',  ac:'#1E88E5' },
  { name:'Gemini Flash',           task:'LLM Summary Card',      detail:'Free tier · SHA cached', ac:'#43A047' },
  { name:'WavLM / wav2vec2',       task:'Audio Deepfake',        detail:'ASVspoof 2019 trained',  ac:'#FF8F00' },
];

const FAQS = [
  { q:'How accurate is DeepShield?', a:'The image pipeline runs a weighted ensemble of EfficientNet B4 (DFDC-trained) and a ViT fine-tuned on FaceForensics++ c40 compression, achieving ≥92% accuracy with ≤3% false-positive rate on real camera photos. Text analysis adds a cosine-similarity truth-override that cross-checks against major trusted sources — Reuters, AP, BBC — to reduce false alarms on legitimate news.' },
  { q:'What file formats are supported?', a:'Images: JPG, PNG, WEBP, BMP. Videos: MP4, MOV, WebM, AVI up to 100 MB. Text: paste any article up to 10,000 characters. Screenshots: any image format — EasyOCR extracts the embedded text automatically for a full layout + content analysis.' },
  { q:'Is my data stored or shared?', a:"Media is processed in-memory and only persisted when you're signed in (for history). Nothing is shared with third parties. LLM explainability sends only non-sensitive analysis signals to Gemini — never your original media file. You can delete any record from your history at any time." },
  { q:'How does the Authenticity Score (0–100) work?', a:'The score is a calibrated ensemble output — 0 means almost certainly manipulated, 100 means highly authentic. For images, it blends EfficientNet confidence, ViT confidence, EXIF trust adjustment, and artifact scan signals through isotonic regression calibration. For text, the fake-news classifier probability is modulated by the truth-override rule and a 15-pattern sensationalism score.' },
  { q:'Can DeepShield detect AI-generated text?', a:'Yes. The text pipeline uses a multilingual BERT-family classifier trained on fake-news corpora, plus 15 manipulation pattern checks (urgency, emotional manipulation, sensationalism), NER-based keyword extraction for source cross-checking, and truth-override via cosine similarity against trusted-source headlines.' },
  { q:'What is Grad-CAM++ and why does it matter?', a:"Grad-CAM++ generates a heatmap showing exactly which pixels drove the model's decision. Instead of a black-box verdict you can see whether the model focused on facial boundary artifacts (common with GANs), lighting inconsistencies, or background anomalies — making every verdict auditable and defensible." },
  { q:'Does it work on screenshots and WhatsApp forwards?', a:'Yes. The screenshot pipeline uses EasyOCR to extract all embedded text, then runs layout-anomaly detection (unusual font sizes, misaligned bounding boxes), phrase-level manipulation scoring, and the full text analysis pipeline on the extracted content — effective against the forwarded-screenshot pattern common in messaging apps.' },
  { q:'Is DeepShield free to use?', a:'Core analysis is free with no sign-up required. Creating an account unlocks analysis history, PDF report generation, and higher rate limits (50 analyses/hour vs 5/hour anonymous). LLM explainability uses Gemini Flash free tier and is cached per unique file SHA-256 — so repeated analyses incur no extra API cost.' },
];

const BADGES = [
  { Icon:IShield, title:'Local Processing',   desc:'Media is analyzed in-process — never uploaded to third-party infrastructure.' },
  { Icon:ICode,   title:'Open-Source Models', desc:'EfficientNet, ViT, and WavLM weights are publicly auditable on Hugging Face.' },
  { Icon:ILock,   title:'Privacy-First',      desc:'No tracking, no advertising. Opt out of LLM calls at any time with one toggle.' },
  { Icon:IEye,    title:'Explainable AI',     desc:'Every verdict ships with heatmaps, indicators, and a plain-English LLM summary.' },
];

// ─── Shared tokens ────────────────────────────────────────────────────────────
const SORA = "'Sora', -apple-system, BlinkMacSystemFont, sans-serif";
const INTER = "-apple-system, BlinkMacSystemFont, 'Inter', sans-serif";
const BG_SECTION_ALT = '#EEF2F7';

// ─── Sub-components ───────────────────────────────────────────────────────────

function AuthMock() {
  const R = 48;
  const C = 2 * Math.PI * R;
  return (
    <div className="ds-auth-mock" style={{
      width: 218,
      background: 'rgba(255,255,255,0.92)',
      backdropFilter: 'blur(14px)',
      WebkitBackdropFilter: 'blur(14px)',
      border: '1px solid rgba(255,255,255,0.7)',
      borderRadius: 16,
      padding: '20px 20px 18px',
      boxShadow: '0 0 0 1px rgba(67,160,71,0.10), 0 8px 32px rgba(30,136,229,0.14), 0 2px 8px rgba(0,0,0,0.06)',
      flexShrink: 0,
    }}>
      <p style={{ margin:'0 0 14px', fontSize:11, fontWeight:700, letterSpacing:'0.1em', color:'#8C9BAA', textTransform:'uppercase', fontFamily:INTER }}>
        Authenticity Score
      </p>
      <div style={{ display:'flex', alignItems:'center', gap:14 }}>
        <svg width={108} height={108} viewBox="0 0 108 108" style={{ flexShrink:0 }}>
          <circle cx="54" cy="54" r={R} fill="none" stroke="#E8EEF4" strokeWidth={8} />
          <motion.circle
            cx="54" cy="54" r={R}
            fill="none" stroke="#43A047" strokeWidth={8} strokeLinecap="round"
            strokeDasharray={C}
            transform="rotate(-90 54 54)"
            initial={{ strokeDashoffset: C }}
            animate={{ strokeDashoffset: C * 0.06 }}
            transition={{ delay: 0.4, duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
          />
          <text x="54" y="50" textAnchor="middle" fontSize="23" fontWeight="800" fill="#1A2638" fontFamily={SORA}>94</text>
          <text x="54" y="64" textAnchor="middle" fontSize="9" fontWeight="700" fill="#43A047" fontFamily={INTER} letterSpacing="1">AUTHENTIC</text>
        </svg>
        <div style={{ display:'grid', gap:8, flex:1 }}>
          {[['EfficientNet','97%','#43A047'],['ViT model','91%','#43A047'],['EXIF trust','+8','#1E88E5']].map(([l,v,c]) => (
            <div key={l} style={{ display:'flex', justifyContent:'space-between' }}>
              <span style={{ fontSize:11, color:'#8C9BAA', fontFamily:INTER }}>{l}</span>
              <span style={{ fontSize:11, fontWeight:700, color:c, fontFamily:INTER }}>{v}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ marginTop:14, padding:'8px 10px', background:'rgba(67,160,71,0.08)', borderRadius:8, display:'flex', alignItems:'center', gap:6 }}>
        <span style={{ color:'#43A047', display:'flex' }}><ICheck s={13} /></span>
        <span style={{ fontSize:11, fontWeight:600, color:'#43A047', fontFamily:INTER }}>No manipulation detected</span>
      </div>
    </div>
  );
}

function Cell({ v }) {
  if (v === true)      return <span style={{ color:'#43A047', display:'flex', justifyContent:'center' }}><ICheck /></span>;
  if (v === false)     return <span style={{ color:'#CDD5E0', display:'flex', justifyContent:'center' }}><IXmark /></span>;
  if (v === 'partial') return <span style={{ color:'#FFA726', display:'flex', justifyContent:'center' }}><IMinus /></span>;
  return null;
}

function FAQ({ item, open, onToggle }) {
  return (
    <div style={{ background:'#fff', borderRadius:12, border:'1px solid #E4E9F0', overflow:'hidden' }}>
      <button
        onClick={onToggle}
        aria-expanded={open}
        style={{
          width:'100%', display:'flex', justifyContent:'space-between', alignItems:'center',
          padding:'18px 22px', background:'none', border:'none', cursor:'pointer',
          textAlign:'left', gap:16, fontFamily:INTER,
        }}
      >
        <span style={{ fontSize:15, fontWeight:600, color:'#1A2638', lineHeight:1.4 }}>{item.q}</span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration:0.2, ease:'easeInOut' }}
          style={{ flexShrink:0, color:'#1E88E5', display:'flex' }}
        >
          <IChevron />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="body"
            initial={{ height:0, opacity:0 }}
            animate={{ height:'auto', opacity:1 }}
            exit={{ height:0, opacity:0 }}
            transition={{ duration:0.25, ease:[0.4,0,0.2,1] }}
            style={{ overflow:'hidden' }}
          >
            <p style={{ margin:0, padding:'0 22px 20px', fontSize:14, color:'#5B6B82', lineHeight:1.75, maxWidth:'70ch', fontFamily:INTER }}>
              {item.a}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function HomePage() {
  useHeadAssets();
  const [openFaq, setOpenFaq] = useState(null);

  /* shared section wrapper */
  const Wrap = ({ children, style }) => (
    <div style={{ maxWidth:1140, margin:'0 auto', padding:'0 clamp(1.25rem,4vw,3rem)', ...style }}>
      {children}
    </div>
  );

  const SectionPad = 'clamp(3rem,6vw,5.5rem)';

  return (
    <article style={{ overflowX:'hidden' }}>

      {/* ── HERO ─────────────────────────────────────────────────────── */}
      <section style={{
        padding:`clamp(4rem,9vw,7rem) 0 clamp(3rem,6vw,5rem)`,
        background:`
          radial-gradient(ellipse 70% 55% at 6% 45%, rgba(30,136,229,0.11) 0%, transparent 58%),
          radial-gradient(ellipse 50% 40% at 90% 12%, rgba(21,101,192,0.07) 0%, transparent 52%),
          #F8FAFC
        `,
      }}>
        <Wrap>
          <div className="ds-hero-cols" style={{ display:'grid', gridTemplateColumns:'1fr auto', gap:'3rem', alignItems:'center' }}>
            {/* Copy */}
            <div style={{ display:'grid', gap:'1.5rem', maxWidth:640 }}>
              {/* Badge */}
              <div>
                <span style={{
                  display:'inline-flex', alignItems:'center', gap:7,
                  padding:'5px 14px',
                  background:'rgba(30,136,229,0.09)', border:'1px solid rgba(30,136,229,0.2)',
                  borderRadius:9999,
                  fontSize:11, fontWeight:700, letterSpacing:'0.08em', color:'#1565C0', fontFamily:INTER,
                }}>
                  <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden="true">
                    <circle cx="4" cy="4" r="3.5" fill="#43A047" />
                  </svg>
                  EXPLAINABLE AI · MULTIMODAL · OPEN-SOURCE
                </span>
              </div>

              {/* Headline */}
              <h1 style={{
                fontFamily:SORA, fontWeight:800,
                fontSize:'clamp(2.4rem,5.5vw,3.9rem)',
                lineHeight:1.08, letterSpacing:'-0.025em',
                color:'#1A2638', margin:0,
              }}>
                See through the fake.<br />
                <span style={{ color:'#1565C0' }}>Trust what&rsquo;s real.</span>
              </h1>

              {/* Sub */}
              <p style={{
                margin:0, fontSize:'clamp(1rem,2vw,1.1rem)',
                color:'#5B6B82', lineHeight:1.7, maxWidth:'60ch', fontFamily:INTER,
              }}>
                DeepShield runs a multi-model AI ensemble — EfficientNet, ViT, Grad-CAM++, and LLM explainability — to detect deepfakes and misinformation across images, videos, text, and screenshots.
              </p>

              {/* CTAs */}
              <div style={{ display:'flex', gap:12, flexWrap:'wrap' }}>
                <Link to="/analyze" style={{
                  display:'inline-flex', alignItems:'center', gap:6,
                  padding:'13px 28px', background:'#1565C0', color:'#fff',
                  borderRadius:8, fontWeight:700, fontSize:15, textDecoration:'none',
                  boxShadow:'0 4px 14px rgba(21,101,192,0.32)', fontFamily:INTER,
                  transition:'background 150ms ease, transform 150ms ease, box-shadow 150ms ease',
                }}
                  onMouseEnter={e => { e.currentTarget.style.background='#0D47A1'; e.currentTarget.style.transform='translateY(-1px)'; }}
                  onMouseLeave={e => { e.currentTarget.style.background='#1565C0'; e.currentTarget.style.transform=''; }}
                >
                  Analyze Now →
                </Link>
                <a href="#how-it-works" style={{
                  display:'inline-flex', alignItems:'center', gap:6,
                  padding:'13px 26px', background:'transparent', color:'#1565C0',
                  border:'2px solid #BBDEFB', borderRadius:8,
                  fontWeight:600, fontSize:15, textDecoration:'none', fontFamily:INTER,
                  transition:'border-color 150ms ease, background 150ms ease',
                }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor='#90CAF9'; e.currentTarget.style.background='#E3F2FD'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor='#BBDEFB'; e.currentTarget.style.background='transparent'; }}
                >
                  See How It Works
                </a>
              </div>

              {/* Mini stats */}
              <div style={{ display:'flex', gap:32, flexWrap:'wrap', paddingTop:4 }}>
                {[['4','media pipelines'],['≥92%','image accuracy'],['5','AI models fused']].map(([v,l]) => (
                  <div key={l}>
                    <div style={{ fontSize:22, fontWeight:800, color:'#1565C0', fontFamily:SORA, lineHeight:1 }}>{v}</div>
                    <div style={{ fontSize:11, color:'#8C9BAA', marginTop:3, fontWeight:500, fontFamily:INTER }}>{l}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Score card */}
            <AuthMock />
          </div>
        </Wrap>
      </section>

      {/* ── IMPACT MARQUEE ───────────────────────────────────────────── */}
      <section style={{ padding:`clamp(2.5rem,5vw,4rem) 0`, background:BG_SECTION_ALT }}>
        <Wrap style={{ marginBottom:'1.25rem' }}>
          <p style={{ margin:0, fontSize:11, fontWeight:700, letterSpacing:'0.1em', color:'#8C9BAA', textTransform:'uppercase', fontFamily:INTER }}>
            Real-world deepfakes DeepShield is built to catch
          </p>
        </Wrap>
        <div className="ds-marquee-wrap" style={{ overflow:'hidden' }}>
          <div className="ds-marquee-track" style={{ paddingLeft:'clamp(1.25rem,4vw,3rem)' }}>
            {DOUBLED.map((s, i) => {
              const SIcon = s.Icon;
              return (
                <div key={`${s.id}-${i}`} style={{
                  flexShrink:0, width:268,
                  background:'#fff', borderRadius:12, padding:'18px 18px 16px',
                  border:'1px solid #E4E9F0', boxShadow:'0 1px 4px rgba(0,0,0,0.05)',
                }}>
                  <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:12 }}>
                    <div style={{
                      width:36, height:36, borderRadius:8, flexShrink:0,
                      background:`${s.bc}14`,
                      display:'flex', alignItems:'center', justifyContent:'center', color:s.bc,
                    }}>
                      <SIcon s={18} />
                    </div>
                    <span style={{
                      fontSize:10, fontWeight:700, letterSpacing:'0.07em',
                      padding:'3px 9px', borderRadius:9999,
                      background:`${s.bc}13`, color:s.bc, fontFamily:INTER,
                    }}>{s.badge}</span>
                  </div>
                  <h4 style={{ margin:'0 0 7px', fontSize:13, fontWeight:700, color:'#1A2638', lineHeight:1.35, fontFamily:SORA }}>{s.title}</h4>
                  <p style={{ margin:0, fontSize:12.5, color:'#5B6B82', lineHeight:1.6, fontFamily:INTER }}>{s.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── COMPARISON ───────────────────────────────────────────────── */}
      <section style={{ padding:`${SectionPad} 0`, background:'#fff' }}>
        <Wrap>
          <div style={{ marginBottom:'clamp(2rem,4vw,3rem)' }}>
            <h2 style={{ fontFamily:SORA, fontWeight:700, fontSize:'clamp(1.7rem,3.5vw,2.4rem)', lineHeight:1.15, letterSpacing:'-0.018em', color:'#1A2638', margin:'0 0 10px' }}>
              Why researchers &amp; fact-checkers<br />choose DeepShield
            </h2>
            <p style={{ margin:0, fontSize:15, color:'#5B6B82', lineHeight:1.6, maxWidth:'54ch', fontFamily:INTER }}>
              Complete, explainable, and open — where others show a verdict, we show you exactly why.
            </p>
          </div>
          <div style={{ overflowX:'auto' }}>
            <table style={{ width:'100%', borderCollapse:'separate', borderSpacing:0, fontSize:14, minWidth:540 }}>
              <thead>
                <tr>
                  <th style={{ textAlign:'left', padding:'10px 16px', fontWeight:600, color:'#8C9BAA', fontSize:12, borderBottom:'2px solid #E4E9F0', letterSpacing:'0.04em', fontFamily:INTER }}>Feature</th>
                  {[
                    { label:'DeepShield',      hi:true },
                    { label:'Reality Defender',hi:false },
                    { label:'Deepware',        hi:false },
                    { label:'Manual Check',    hi:false },
                  ].map(col => (
                    <th key={col.label} style={{
                      padding:'10px 16px', textAlign:'center', fontSize:12, fontWeight:700,
                      borderBottom:'2px solid #E4E9F0',
                      color: col.hi ? '#1565C0' : '#5B6B82',
                      background: col.hi ? 'rgba(30,136,229,0.05)' : 'transparent',
                      borderRadius: col.hi ? '8px 8px 0 0' : undefined,
                      fontFamily:INTER,
                    }}>
                      {col.label}
                      {col.hi && <span style={{ display:'block', fontSize:9.5, fontWeight:600, color:'#43A047', letterSpacing:'0.06em', marginTop:2 }}>★ RECOMMENDED</span>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((row, i) => (
                  <tr key={row.f} style={{ background: i%2===0 ? '#FAFBFC' : '#fff' }}>
                    <td style={{ padding:'12px 16px', color:'#1A2638', fontWeight:500, lineHeight:1.4, fontFamily:INTER }}>{row.f}</td>
                    <td style={{ padding:'12px 16px', background:'rgba(30,136,229,0.04)' }}><Cell v={row.ds} /></td>
                    <td style={{ padding:'12px 16px' }}><Cell v={row.rd} /></td>
                    <td style={{ padding:'12px 16px' }}><Cell v={row.dw} /></td>
                    <td style={{ padding:'12px 16px' }}><Cell v={row.m}  /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ marginTop:10, display:'flex', gap:20, fontSize:11, color:'#8C9BAA', flexWrap:'wrap', fontFamily:INTER }}>
              {[[ICheck,'#43A047','Available'],[IMinus,'#FFA726','Partial'],[IXmark,'#CDD5E0','Not available']].map(([Ico,c,l]) => (
                <span key={l} style={{ display:'flex', alignItems:'center', gap:5 }}>
                  <span style={{ color:c }}><Ico s={13} /></span>{l}
                </span>
              ))}
            </div>
          </div>
        </Wrap>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────────────────── */}
      <section id="how-it-works" style={{ padding:`${SectionPad} 0`, background:BG_SECTION_ALT }}>
        <Wrap>
          <h2 style={{ fontFamily:SORA, fontWeight:700, fontSize:'clamp(1.7rem,3.5vw,2.4rem)', lineHeight:1.15, letterSpacing:'-0.018em', color:'#1A2638', margin:'0 0 clamp(2rem,4vw,3rem)', textAlign:'center' }}>
            From upload to verdict in seconds
          </h2>
          <div className="ds-steps-grid" style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:'2rem' }}>
            {STEPS.map(step => {
              const SIcon = step.Icon;
              return (
                <div key={step.n} style={{ display:'grid', gap:14, textAlign:'center' }}>
                  <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:14 }}>
                    <div style={{
                      width:62, height:62, borderRadius:9999, flexShrink:0,
                      background:'#1565C0',
                      display:'flex', alignItems:'center', justifyContent:'center', color:'#fff',
                      boxShadow:'0 4px 18px rgba(21,101,192,0.28)',
                    }}>
                      <SIcon s={26} />
                    </div>
                    <div>
                      <div style={{ fontSize:10, fontWeight:700, letterSpacing:'0.1em', color:'#1E88E5', marginBottom:4, fontFamily:INTER }}>STEP {step.n}</div>
                      <h3 style={{ margin:'0 0 8px', fontSize:16, fontWeight:700, color:'#1A2638', fontFamily:SORA }}>{step.title}</h3>
                      <p style={{ margin:0, fontSize:13.5, color:'#5B6B82', lineHeight:1.65, maxWidth:'28ch', marginLeft:'auto', marginRight:'auto', fontFamily:INTER }}>{step.desc}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Wrap>
      </section>

      {/* ── TECH STACK ───────────────────────────────────────────────── */}
      <section style={{ padding:`${SectionPad} 0`, background:'#fff' }}>
        <Wrap>
          <div style={{ marginBottom:'clamp(2rem,4vw,3rem)' }}>
            <h2 style={{ fontFamily:SORA, fontWeight:700, fontSize:'clamp(1.7rem,3.5vw,2.4rem)', lineHeight:1.15, letterSpacing:'-0.018em', color:'#1A2638', margin:'0 0 10px' }}>
              Powered by state-of-the-art AI
            </h2>
            <p style={{ margin:0, fontSize:15, color:'#5B6B82', lineHeight:1.6, maxWidth:'54ch', fontFamily:INTER }}>
              Every pipeline is built on peer-reviewed, open-weight architectures — nothing proprietary, nothing opaque.
            </p>
          </div>
          <div className="ds-tech-grid" style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:14 }}>
            {TECH.map(card => (
              <div key={card.name} style={{
                background:'#FAFBFC', borderRadius:12, padding:'18px 16px',
                border:'1px solid #E4E9F0',
                transition:'transform 200ms ease, box-shadow 200ms ease',
              }}
                onMouseEnter={e => { e.currentTarget.style.transform='translateY(-3px)'; e.currentTarget.style.boxShadow='0 8px 24px rgba(0,0,0,0.09)'; }}
                onMouseLeave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow=''; }}
              >
                <div style={{ width:10, height:10, borderRadius:'50%', background:card.ac, marginBottom:14 }} />
                <div style={{ fontSize:10, fontWeight:700, letterSpacing:'0.09em', color:'#8C9BAA', textTransform:'uppercase', marginBottom:6, fontFamily:INTER }}>{card.task}</div>
                <h4 style={{ margin:'0 0 10px', fontSize:14, fontWeight:700, color:'#1A2638', fontFamily:SORA, lineHeight:1.3 }}>{card.name}</h4>
                <span style={{
                  display:'inline-block', fontSize:11, fontWeight:600,
                  padding:'3px 10px', borderRadius:9999,
                  background:`${card.ac}14`, color:card.ac, fontFamily:INTER,
                }}>{card.detail}</span>
              </div>
            ))}
          </div>
        </Wrap>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────── */}
      <section id="faq" style={{ padding:`${SectionPad} 0`, background:BG_SECTION_ALT }}>
        <Wrap style={{ maxWidth:780 }}>
          <div style={{ marginBottom:'clamp(2rem,4vw,3rem)' }}>
            <h2 style={{ fontFamily:SORA, fontWeight:700, fontSize:'clamp(1.7rem,3.5vw,2.4rem)', lineHeight:1.15, letterSpacing:'-0.018em', color:'#1A2638', margin:'0 0 10px' }}>
              Common questions
            </h2>
            <p style={{ margin:0, fontSize:15, color:'#5B6B82', lineHeight:1.6, fontFamily:INTER }}>
              Everything you need to know before running your first analysis.
            </p>
          </div>
          <div style={{ display:'grid', gap:10 }}>
            {FAQS.map((item, i) => (
              <FAQ key={i} item={item} open={openFaq===i} onToggle={() => setOpenFaq(openFaq===i ? null : i)} />
            ))}
          </div>
        </Wrap>
      </section>

      {/* ── TRUST BADGES ─────────────────────────────────────────────── */}
      <section style={{ padding:`${SectionPad} 0`, background:'#fff' }}>
        <Wrap>
          <h2 style={{ fontFamily:SORA, fontWeight:700, fontSize:'clamp(1.7rem,3.5vw,2.4rem)', lineHeight:1.15, letterSpacing:'-0.018em', color:'#1A2638', margin:'0 0 clamp(2rem,4vw,3rem)', textAlign:'center' }}>
            Built on trust, by design
          </h2>
          <div className="ds-trust-grid" style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:18 }}>
            {BADGES.map(b => {
              const BIcon = b.Icon;
              return (
                <div key={b.title} style={{ display:'flex', flexDirection:'column', gap:14, padding:'22px 20px', background:'#FAFBFC', borderRadius:12, border:'1px solid #E4E9F0' }}>
                  <div style={{ width:46, height:46, borderRadius:10, flexShrink:0, background:'rgba(30,136,229,0.09)', display:'flex', alignItems:'center', justifyContent:'center', color:'#1565C0' }}>
                    <BIcon s={22} />
                  </div>
                  <div>
                    <h4 style={{ margin:'0 0 6px', fontSize:15, fontWeight:700, color:'#1A2638', fontFamily:SORA }}>{b.title}</h4>
                    <p style={{ margin:0, fontSize:13.5, color:'#5B6B82', lineHeight:1.6, fontFamily:INTER }}>{b.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </Wrap>
      </section>

      {/* ── CTA STRIP ────────────────────────────────────────────────── */}
      <section style={{ padding:`clamp(3.5rem,8vw,6rem) 0`, background:'#0D47A1' }}>
        <Wrap style={{ maxWidth:700, textAlign:'center', display:'grid', gap:'1.25rem' }}>
          <h2 style={{
            fontFamily:SORA, fontWeight:800,
            fontSize:'clamp(1.9rem,4.5vw,3rem)',
            color:'#fff', margin:0, lineHeight:1.1, letterSpacing:'-0.02em',
          }}>
            Ready to verify what you see?
          </h2>
          <p style={{ margin:0, fontSize:'clamp(0.95rem,2vw,1.05rem)', color:'rgba(255,255,255,0.8)', lineHeight:1.65, fontFamily:INTER }}>
            No sign-up required. Drop any image, video, article, or screenshot and get a full explainable AI report in seconds.
          </p>
          <div style={{ display:'flex', gap:12, justifyContent:'center', flexWrap:'wrap', paddingTop:4 }}>
            <Link to="/analyze" style={{
              display:'inline-flex', alignItems:'center', gap:6,
              padding:'14px 32px', background:'#fff', color:'#0D47A1',
              borderRadius:8, fontWeight:700, fontSize:15, textDecoration:'none',
              boxShadow:'0 4px 18px rgba(0,0,0,0.22)', fontFamily:INTER,
              transition:'transform 150ms ease, box-shadow 150ms ease',
            }}
              onMouseEnter={e => { e.currentTarget.style.transform='translateY(-1px)'; e.currentTarget.style.boxShadow='0 6px 24px rgba(0,0,0,0.28)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow='0 4px 18px rgba(0,0,0,0.22)'; }}
            >
              Start Free Analysis →
            </Link>
            <Link to="/about" style={{
              display:'inline-flex', alignItems:'center',
              padding:'14px 26px', background:'transparent',
              color:'rgba(255,255,255,0.88)',
              border:'2px solid rgba(255,255,255,0.28)',
              borderRadius:8, fontWeight:600, fontSize:15, textDecoration:'none', fontFamily:INTER,
              transition:'border-color 150ms ease',
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor='rgba(255,255,255,0.6)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor='rgba(255,255,255,0.28)'; }}
            >
              Learn About DeepShield
            </Link>
          </div>
        </Wrap>
      </section>

    </article>
  );
}
