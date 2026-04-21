import { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Link } from 'react-router-dom';

// ─── SVG Icons ────────────────────────────────────────────────────────────────

const IconShield = ({ size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);
const IconCode = ({ size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
  </svg>
);
const IconLock = ({ size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);
const IconEye = ({ size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
  </svg>
);
const IconCheck = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const IconX = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);
const IconMinus = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);
const IconUpload = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);
const IconCpu = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" />
    <line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" />
    <line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" />
    <line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" />
    <line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" />
  </svg>
);
const IconSearch = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);
const IconFileText = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
  </svg>
);
const IconChevronDown = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="6 9 12 15 18 9" />
  </svg>
);
const IconAlert = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);
const IconDollarSign = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);
const IconImage = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" />
  </svg>
);
const IconBroadcast = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="2" />
    <path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14" />
  </svg>
);
const IconUser = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);
const IconMessageSquare = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

// ─── Data ─────────────────────────────────────────────────────────────────────

const IMPACT_STORIES = [
  { id: 1, Icon: IconAlert,       badge: 'HIGH RISK',  badgeColor: '#C62828', title: '2024 US Election Deepfakes',      desc: 'AI-generated candidate videos circulated on social media days before elections, reaching millions of voters.' },
  { id: 2, Icon: IconDollarSign,  badge: 'FINANCIAL',  badgeColor: '#E65100', title: 'CEO Voice Clone Fraud',           desc: 'Synthetic audio of a CEO used to authorize a $243K wire transfer — undetected by the finance team.' },
  { id: 3, Icon: IconImage,       badge: 'MISLEADING', badgeColor: '#6A1B9A', title: 'Viral Fake Protest Photos',        desc: 'AI-generated crowd images shared as real protest evidence across major news networks worldwide.' },
  { id: 4, Icon: IconMessageSquare, badge: 'HEALTH',   badgeColor: '#1565C0', title: 'Fake News Screenshot Chains',     desc: 'Fabricated WhatsApp screenshots spread dangerous medical misinformation during a public health crisis.' },
  { id: 5, Icon: IconBroadcast,   badge: 'PROPAGANDA', badgeColor: '#B71C1C', title: 'Synthetic Face News Anchors',     desc: 'State-sponsored deepfake news anchors broadcast political propaganda across international audiences.' },
  { id: 6, Icon: IconUser,        badge: 'HARMFUL',    badgeColor: '#37474F', title: 'Sports Star Face Swap',           desc: 'Celebrity face-swap videos produced and distributed without consent, causing reputational damage.' },
];
const DOUBLED_STORIES = [...IMPACT_STORIES, ...IMPACT_STORIES];

const COMPARISON_ROWS = [
  { feature: 'Explainable AI (Grad-CAM++)', ds: true,      rd: false,     dw: false, manual: false },
  { feature: 'Multi-modal (4 media types)', ds: true,      rd: 'partial', dw: false, manual: false },
  { feature: 'LLM Plain-English Summary',   ds: true,      rd: false,     dw: false, manual: false },
  { feature: 'EXIF Metadata Analysis',      ds: true,      rd: false,     dw: false, manual: 'partial' },
  { feature: 'Audio Deepfake Detection',    ds: true,      rd: 'partial', dw: false, manual: false },
  { feature: 'Open-Source Model Weights',   ds: true,      rd: false,     dw: false, manual: false },
  { feature: 'Free Tier Available',         ds: true,      rd: false,     dw: true,  manual: true },
  { feature: 'PDF Audit Report',            ds: true,      rd: true,      dw: false, manual: false },
  { feature: 'Privacy-First (local run)',   ds: true,      rd: false,     dw: false, manual: true },
];

const STEPS = [
  { n: 1, Icon: IconUpload,   title: 'Upload',  desc: 'Drop an image, video, screenshot, or paste article text. Supports JPG, PNG, MP4, WebM and more.' },
  { n: 2, Icon: IconCpu,      title: 'Analyze', desc: 'A multi-model AI ensemble runs in parallel — EfficientNet, ViT, Grad-CAM++, LLM, and audio checks.' },
  { n: 3, Icon: IconSearch,   title: 'Explain', desc: 'Inspect heatmaps, manipulation indicators, EXIF signals, and trusted-source evidence in full detail.' },
  { n: 4, Icon: IconFileText, title: 'Report',  desc: 'Download a PDF audit trail or revisit any past analysis through your personal history dashboard.' },
];

const TECH_CARDS = [
  { name: 'EfficientNet B4',        task: 'Image Deepfake Detection', detail: 'DFDC-trained ensemble',    accent: '#1565C0' },
  { name: 'ViT + FaceForensics++',  task: 'Face Manipulation',        detail: 'Fine-tuned on c40',        accent: '#0D47A1' },
  { name: 'Grad-CAM++',             task: 'Visual Explainability',    detail: 'Last 3 encoder layers',    accent: '#1E88E5' },
  { name: 'Gemini Flash',           task: 'LLM Plain-English Card',   detail: 'Free tier · SHA cached',   accent: '#43A047' },
  { name: 'WavLM / wav2vec2',       task: 'Audio Deepfake Detection', detail: 'ASVspoof 2019 trained',    accent: '#FF8F00' },
];

const FAQ_ITEMS = [
  {
    q: 'How accurate is DeepShield?',
    a: 'The image pipeline runs a weighted ensemble of EfficientNet B4 (DFDC-trained) and a ViT fine-tuned on FaceForensics++ c40 compression. On held-out test sets this achieves ≥92% accuracy with ≤3% false-positive rate on real camera photos. Text analysis adds a cosine-similarity truth-override that cross-checks against major trusted sources (Reuters, AP, BBC) to reduce false alarms on legitimate news.',
  },
  {
    q: 'What file formats are supported?',
    a: 'Images: JPG, PNG, WEBP, BMP (static GIF). Videos: MP4, MOV, WebM, AVI up to 100 MB. Text: paste any article or excerpt up to 10,000 characters. Screenshots: any image format — EasyOCR extracts the embedded text automatically for a full layout + content analysis.',
  },
  {
    q: 'Is my data stored or shared?',
    a: 'Media is processed in-memory and only persisted when you are signed in (for history). Nothing is shared with third parties. LLM explainability sends only non-sensitive analysis signals to Gemini — never your original media file. You can delete any record from your history at any time.',
  },
  {
    q: 'How does the Authenticity Score (0–100) work?',
    a: 'The score is a calibrated ensemble output — 0 means almost certainly manipulated, 100 means highly authentic. For images, it blends EfficientNet confidence, ViT confidence, EXIF trust adjustment, and artifact scan signals through isotonic regression calibration. For text, the fake-news classifier probability is modulated by the truth-override rule and a 15-pattern sensationalism score.',
  },
  {
    q: 'Can DeepShield detect AI-generated text?',
    a: 'Yes. The text pipeline uses a multilingual BERT-family classifier trained on fake-news corpora, plus 15 manipulation pattern checks (urgency, emotional manipulation, sensationalism), NER-based keyword extraction for source cross-checking, and truth-override via cosine similarity against trusted-source headlines with ≥0.6 similarity threshold.',
  },
  {
    q: 'What is Grad-CAM++ and why does it matter?',
    a: 'Grad-CAM++ (Gradient-weighted Class Activation Mapping, 2nd gen) generates a heatmap showing which pixels drove the model\'s decision. Instead of a black-box verdict you can see whether the model focused on facial boundary artifacts (common with GANs), lighting inconsistencies, or background anomalies — making every verdict auditable and defensible.',
  },
  {
    q: 'Does it work on screenshots and WhatsApp forwards?',
    a: 'Yes. The screenshot pipeline uses EasyOCR to extract all embedded text, then runs layout-anomaly detection (unusual font sizes, misaligned bounding boxes, suspicious overlaps), phrase-level manipulation scoring, and the full text analysis pipeline on the extracted content — making it effective against the forwarded-screenshot pattern common in messaging apps.',
  },
  {
    q: 'Is DeepShield free to use?',
    a: 'Core analysis — image, text, and screenshot — is free with no sign-up required. Creating an account unlocks analysis history, PDF report generation, and higher rate limits (50 analyses/hour vs 5/hour anonymous). LLM explainability uses Gemini Flash free tier and is cached per unique file SHA-256, so repeated analyses incur no extra cost.',
  },
];

const TRUST_BADGES = [
  { Icon: IconShield, title: 'Local Processing',    desc: 'Media is analyzed in-process — never uploaded to third-party infrastructure.' },
  { Icon: IconCode,   title: 'Open-Source Models',  desc: 'EfficientNet, ViT, and WavLM weights are publicly auditable on Hugging Face.' },
  { Icon: IconLock,   title: 'Privacy-First',        desc: 'No tracking, no advertising. Opt out of LLM calls at any time with one toggle.' },
  { Icon: IconEye,    title: 'Explainable AI',       desc: 'Every verdict ships with heatmaps, indicators, and a plain-English LLM summary.' },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

function AuthenticityMock({ reduced }) {
  const R = 50;
  const circ = 2 * Math.PI * R;
  const score = 0.94;

  return (
    <motion.div
      aria-hidden="true"
      initial={reduced ? false : { opacity: 0, y: 20, scale: 0.93 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: 0.55, duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
      style={{
        width: 210,
        background: 'rgba(255,255,255,0.88)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(255,255,255,0.6)',
        borderRadius: 16,
        padding: '20px 20px 18px',
        boxShadow: '0 0 0 1px rgba(67,160,71,0.12), 0 8px 32px rgba(30,136,229,0.12), 0 2px 8px rgba(0,0,0,0.06)',
        flexShrink: 0,
      }}
    >
      <p style={{ margin: '0 0 14px', fontSize: '0.65rem', fontWeight: 700, letterSpacing: '0.1em', color: '#8C9BAA', textTransform: 'uppercase' }}>
        Authenticity Score
      </p>

      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <svg width={112} height={112} viewBox="0 0 112 112" style={{ flexShrink: 0 }}>
          <circle cx="56" cy="56" r={R} fill="none" stroke="#EEF2F7" strokeWidth="9" />
          <motion.circle
            cx="56" cy="56" r={R}
            fill="none"
            stroke="#43A047"
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray={circ}
            transform="rotate(-90 56 56)"
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: circ * (1 - score) }}
            transition={reduced ? { duration: 0 } : { delay: 0.9, duration: 1.3, ease: [0.22, 1, 0.36, 1] }}
          />
          <text x="56" y="51" textAnchor="middle" fontSize="24" fontWeight="800" fill="#1A2638" fontFamily="Sora, sans-serif">94</text>
          <text x="56" y="66" textAnchor="middle" fontSize="9.5" fontWeight="700" fill="#43A047" fontFamily="Sora, sans-serif" letterSpacing="1">AUTHENTIC</text>
        </svg>

        <div style={{ display: 'grid', gap: 7, flex: 1 }}>
          {[
            { label: 'EfficientNet', val: '97%', color: '#43A047' },
            { label: 'ViT model',    val: '91%', color: '#43A047' },
            { label: 'EXIF trust',   val: '+8',  color: '#1E88E5' },
          ].map(row => (
            <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.68rem', color: '#8C9BAA' }}>{row.label}</span>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: row.color }}>{row.val}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 14, padding: '8px 10px', background: 'rgba(67,160,71,0.08)', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ color: '#43A047' }}><IconCheck size={13} /></span>
        <span style={{ fontSize: '0.68rem', fontWeight: 600, color: '#43A047' }}>No manipulation detected</span>
      </div>
    </motion.div>
  );
}

function ComparisonCell({ val }) {
  if (val === true)      return <span style={{ color: '#43A047', display: 'flex', justifyContent: 'center', alignItems: 'center' }}><IconCheck /></span>;
  if (val === false)     return <span style={{ color: '#D0D5DD', display: 'flex', justifyContent: 'center', alignItems: 'center' }}><IconX /></span>;
  if (val === 'partial') return <span style={{ color: '#FFA726', display: 'flex', justifyContent: 'center', alignItems: 'center' }}><IconMinus /></span>;
  return null;
}

function AccordionItem({ item, isOpen, onToggle, reduced }) {
  return (
    <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #E4E9F0', overflow: 'hidden' }}>
      <button
        onClick={onToggle}
        aria-expanded={isOpen}
        style={{
          width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '18px 22px', background: 'none', border: 'none', cursor: 'pointer',
          textAlign: 'left', gap: 16, fontFamily: 'inherit',
        }}
      >
        <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1A2638', lineHeight: 1.4 }}>{item.q}</span>
        <motion.span
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={reduced ? { duration: 0 } : { duration: 0.2, ease: 'easeInOut' }}
          style={{ flexShrink: 0, color: '#1E88E5', display: 'flex' }}
        >
          <IconChevronDown />
        </motion.span>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            key="body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={reduced ? { duration: 0 } : { duration: 0.26, ease: [0.4, 0, 0.2, 1] }}
            style={{ overflow: 'hidden' }}
          >
            <p style={{ margin: 0, padding: '0 22px 20px', fontSize: '0.875rem', color: '#5B6B82', lineHeight: 1.75, maxWidth: '72ch' }}>
              {item.a}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function HomePage() {
  const prefersReducedMotion = useReducedMotion();
  const [openFaq, setOpenFaq] = useState(null);

  const fadeUp = (delay = 0) =>
    prefersReducedMotion
      ? {}
      : {
          initial: { opacity: 0, y: 22 },
          whileInView: { opacity: 1, y: 0 },
          viewport: { once: true, margin: '-60px' },
          transition: { duration: 0.52, delay, ease: [0.22, 1, 0.36, 1] },
        };

  return (
    <>
      {/* Font: Sora for display headings */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&display=swap" rel="stylesheet" />

      <style>{`
        html { scroll-behavior: smooth; }
        @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }

        .ds-headline {
          font-family: 'Sora', var(--font-family);
          font-weight: 800;
          font-size: clamp(2.5rem, 6vw, 4rem);
          line-height: 1.08;
          letter-spacing: -0.025em;
          color: #1A2638;
          margin: 0;
        }
        .ds-section-title {
          font-family: 'Sora', var(--font-family);
          font-weight: 700;
          font-size: clamp(1.7rem, 3.5vw, 2.5rem);
          line-height: 1.15;
          letter-spacing: -0.018em;
          color: #1A2638;
          margin: 0;
        }
        .ds-cta-primary {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 14px 30px;
          background: #1565C0; color: #fff;
          border-radius: 8px; font-weight: 700; font-size: 0.95rem;
          text-decoration: none; cursor: pointer;
          transition: background 150ms ease, transform 150ms ease, box-shadow 150ms ease;
          box-shadow: 0 4px 14px rgba(21,101,192,0.32);
          font-family: inherit;
        }
        .ds-cta-primary:hover { background: #0D47A1; transform: translateY(-1px); box-shadow: 0 6px 20px rgba(21,101,192,0.42); color: #fff; }
        .ds-cta-secondary {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 14px 28px;
          background: transparent; color: #1565C0;
          border: 2px solid #BBDEFB; border-radius: 8px;
          font-weight: 600; font-size: 0.95rem; text-decoration: none; cursor: pointer;
          transition: border-color 150ms ease, background 150ms ease;
          font-family: inherit;
        }
        .ds-cta-secondary:hover { border-color: #90CAF9; background: #E3F2FD; color: #1565C0; }

        /* Marquee */
        @keyframes ds-marquee {
          from { transform: translateX(0); }
          to   { transform: translateX(-50%); }
        }
        .ds-marquee-track {
          display: flex;
          gap: 16px;
          width: max-content;
          animation: ds-marquee 36s linear infinite;
          padding: 4px 0;
        }
        .ds-marquee-wrap:hover .ds-marquee-track { animation-play-state: paused; }
        @media (prefers-reduced-motion: reduce) { .ds-marquee-track { animation: none; } }

        /* Hero responsive */
        .ds-hero-grid { display: grid; grid-template-columns: 1fr auto; gap: 3rem; align-items: center; }
        @media (max-width: 800px) { .ds-hero-grid { grid-template-columns: 1fr; } .ds-auth-mock { display: none !important; } }

        /* Comparison table */
        @media (max-width: 640px) { .ds-compare-col-hide { display: none; } }

        /* Tech grid */
        .ds-tech-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; }

        /* Trust badges grid */
        .ds-trust-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 20px; }

        /* Steps grid */
        .ds-steps-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 2rem; }

        /* Hover lift on cards */
        .ds-lift { transition: transform 200ms ease, box-shadow 200ms ease; }
        .ds-lift:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(0,0,0,0.10); }
      `}</style>

      <article style={{ display: 'grid', gap: 0, overflowX: 'hidden' }}>

        {/* ══ 1. HERO ══════════════════════════════════════════════════════ */}
        <section style={{
          padding: 'clamp(4rem, 9vw, 7rem) clamp(1.5rem, 5vw, 3rem) clamp(3rem, 7vw, 5.5rem)',
          background: `
            radial-gradient(ellipse 70% 60% at 8% 45%, rgba(30,136,229,0.10) 0%, transparent 60%),
            radial-gradient(ellipse 50% 40% at 88% 15%, rgba(21,101,192,0.07) 0%, transparent 55%),
            #F8FAFC
          `,
        }}>
          <div style={{ maxWidth: 1120, margin: '0 auto' }}>
            <div className="ds-hero-grid">
              {/* Copy */}
              <div style={{ display: 'grid', gap: '1.5rem', maxWidth: 640 }}>
                <motion.div
                  initial={prefersReducedMotion ? false : { opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                >
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 7,
                    padding: '5px 14px',
                    background: 'rgba(30,136,229,0.09)',
                    border: '1px solid rgba(30,136,229,0.22)',
                    borderRadius: 9999,
                    fontSize: '0.68rem', fontWeight: 700, letterSpacing: '0.08em', color: '#1565C0',
                  }}>
                    <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden="true">
                      <circle cx="4" cy="4" r="3.5" fill="#43A047" />
                    </svg>
                    EXPLAINABLE AI · MULTIMODAL · OPEN-SOURCE
                  </span>
                </motion.div>

                <motion.h1
                  className="ds-headline"
                  initial={prefersReducedMotion ? false : { opacity: 0, y: 24 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                >
                  See through the fake.<br />
                  <span style={{ color: '#1565C0' }}>Trust what's real.</span>
                </motion.h1>

                <motion.p
                  initial={prefersReducedMotion ? false : { opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
                  style={{ margin: 0, fontSize: '1.05rem', color: '#5B6B82', lineHeight: 1.68, maxWidth: '60ch' }}
                >
                  DeepShield runs a multi-model AI ensemble — EfficientNet, ViT, Grad-CAM++, and LLM explainability — to detect deepfakes and misinformation across images, videos, text, and screenshots.
                </motion.p>

                <motion.div
                  initial={prefersReducedMotion ? false : { opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                  style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}
                >
                  <Link to="/analyze" className="ds-cta-primary">Analyze Now →</Link>
                  <a href="#how-it-works" className="ds-cta-secondary">See How It Works</a>
                </motion.div>

                {/* Quick-stat row */}
                <motion.div
                  initial={prefersReducedMotion ? false : { opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                  style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', paddingTop: 4 }}
                >
                  {[
                    { val: '4',    label: 'media pipelines' },
                    { val: '≥92%', label: 'image accuracy' },
                    { val: '5',    label: 'AI models fused' },
                  ].map(s => (
                    <div key={s.label}>
                      <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#1565C0', fontFamily: "'Sora', var(--font-family)", lineHeight: 1 }}>{s.val}</div>
                      <div style={{ fontSize: '0.72rem', color: '#8C9BAA', marginTop: 3, fontWeight: 500 }}>{s.label}</div>
                    </div>
                  ))}
                </motion.div>
              </div>

              {/* Authenticity score mock card */}
              <div className="ds-auth-mock">
                <AuthenticityMock reduced={!!prefersReducedMotion} />
              </div>
            </div>
          </div>
        </section>

        {/* ══ 2. IMPACT MARQUEE ════════════════════════════════════════════ */}
        <section style={{ padding: 'clamp(2.5rem, 5vw, 4rem) 0', background: '#EEF2F7' }}>
          <div style={{ maxWidth: 1120, margin: '0 auto', padding: '0 clamp(1.5rem, 5vw, 3rem)', marginBottom: '1.25rem' }}>
            <p style={{ margin: 0, fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', color: '#8C9BAA', textTransform: 'uppercase' }}>
              Real-world deepfakes DeepShield is built to catch
            </p>
          </div>

          <div className="ds-marquee-wrap" style={{ overflow: 'hidden', cursor: 'default' }}>
            <div className="ds-marquee-track" style={{ paddingLeft: 'clamp(1.5rem, 5vw, 3rem)' }}>
              {DOUBLED_STORIES.map((story, i) => {
                const StoryIcon = story.Icon;
                return (
                  <div
                    key={`${story.id}-${i}`}
                    style={{
                      flexShrink: 0, width: 272,
                      background: '#fff',
                      borderRadius: 12,
                      padding: '18px 18px 16px',
                      border: '1px solid #E4E9F0',
                      boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                      <div style={{
                        width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                        background: `${story.badgeColor}14`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: story.badgeColor,
                      }}>
                        <StoryIcon size={18} />
                      </div>
                      <span style={{
                        fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.07em',
                        padding: '3px 9px', borderRadius: 9999,
                        background: `${story.badgeColor}12`, color: story.badgeColor,
                      }}>
                        {story.badge}
                      </span>
                    </div>
                    <h4 style={{ margin: '0 0 7px', fontSize: '0.85rem', fontWeight: 700, color: '#1A2638', lineHeight: 1.35 }}>
                      {story.title}
                    </h4>
                    <p style={{ margin: 0, fontSize: '0.78rem', color: '#5B6B82', lineHeight: 1.6 }}>
                      {story.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ══ 3. COMPARISON TABLE ══════════════════════════════════════════ */}
        <section style={{ padding: 'clamp(3rem, 6vw, 5.5rem) clamp(1.5rem, 5vw, 3rem)', background: '#fff' }}>
          <div style={{ maxWidth: 1000, margin: '0 auto' }}>
            <motion.div {...fadeUp()} style={{ marginBottom: 'clamp(2rem, 4vw, 3rem)' }}>
              <h2 className="ds-section-title" style={{ marginBottom: 10 }}>
                Why researchers & fact-checkers<br />choose DeepShield
              </h2>
              <p style={{ margin: 0, fontSize: '1rem', color: '#5B6B82', lineHeight: 1.6, maxWidth: '55ch' }}>
                Complete, explainable, and open — where others show a verdict, we show you exactly why.
              </p>
            </motion.div>

            <motion.div {...fadeUp(0.1)} style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0, fontSize: '0.875rem', minWidth: 560 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '11px 16px', fontWeight: 600, color: '#8C9BAA', fontSize: '0.78rem', borderBottom: '2px solid #E4E9F0', letterSpacing: '0.04em' }}>
                      Feature
                    </th>
                    {[
                      { label: 'DeepShield',      highlight: true },
                      { label: 'Reality Defender', highlight: false },
                      { label: 'Deepware',         highlight: false, hide: true },
                      { label: 'Manual Check',     highlight: false },
                    ].map(col => (
                      <th
                        key={col.label}
                        className={col.hide ? 'ds-compare-col-hide' : ''}
                        style={{
                          padding: '11px 16px', textAlign: 'center', fontSize: '0.78rem', fontWeight: 700,
                          borderBottom: '2px solid #E4E9F0',
                          color: col.highlight ? '#1565C0' : '#5B6B82',
                          background: col.highlight ? 'rgba(30,136,229,0.05)' : 'transparent',
                          borderRadius: col.highlight ? '8px 8px 0 0' : undefined,
                          letterSpacing: '0.02em',
                        }}
                      >
                        {col.label}
                        {col.highlight && (
                          <span style={{ display: 'block', fontSize: '0.6rem', fontWeight: 600, color: '#43A047', letterSpacing: '0.06em', marginTop: 2 }}>
                            ★ RECOMMENDED
                          </span>
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {COMPARISON_ROWS.map((row, i) => (
                    <tr key={row.feature} style={{ background: i % 2 === 0 ? '#FAFBFC' : '#fff' }}>
                      <td style={{ padding: '13px 16px', color: '#1A2638', fontWeight: 500, lineHeight: 1.4 }}>{row.feature}</td>
                      <td style={{ padding: '13px 16px', background: 'rgba(30,136,229,0.05)' }}>
                        <ComparisonCell val={row.ds} />
                      </td>
                      <td style={{ padding: '13px 16px' }}><ComparisonCell val={row.rd} /></td>
                      <td className="ds-compare-col-hide" style={{ padding: '13px 16px' }}><ComparisonCell val={row.dw} /></td>
                      <td style={{ padding: '13px 16px' }}><ComparisonCell val={row.manual} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: 12, display: 'flex', gap: 20, fontSize: '0.72rem', color: '#8C9BAA', flexWrap: 'wrap' }}>
                {[
                  { Icon: IconCheck, label: 'Available',     color: '#43A047' },
                  { Icon: IconMinus, label: 'Partial',       color: '#FFA726' },
                  { Icon: IconX,     label: 'Not available', color: '#D0D5DD' },
                ].map(leg => (
                  <span key={leg.label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ color: leg.color }}><leg.Icon size={13} /></span>
                    {leg.label}
                  </span>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* ══ 4. HOW IT WORKS ══════════════════════════════════════════════ */}
        <section id="how-it-works" style={{ padding: 'clamp(3rem, 6vw, 5.5rem) clamp(1.5rem, 5vw, 3rem)', background: '#F8FAFC' }}>
          <div style={{ maxWidth: 1120, margin: '0 auto' }}>
            <motion.div {...fadeUp()} style={{ marginBottom: 'clamp(2rem, 4vw, 3.5rem)', textAlign: 'center' }}>
              <h2 className="ds-section-title">From upload to verdict in seconds</h2>
            </motion.div>

            <div className="ds-steps-grid" style={{ position: 'relative' }}>
              {STEPS.map((step, i) => {
                const StepIcon = step.Icon;
                return (
                  <motion.div
                    key={step.n}
                    {...fadeUp(i * 0.09)}
                    style={{ display: 'grid', gap: 16, textAlign: 'center' }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
                      <div style={{
                        width: 64, height: 64, borderRadius: 9999, flexShrink: 0,
                        background: '#1565C0',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff',
                        boxShadow: '0 4px 18px rgba(21,101,192,0.28)',
                      }}>
                        <StepIcon size={26} />
                      </div>
                      <div>
                        <div style={{ fontSize: '0.62rem', fontWeight: 700, letterSpacing: '0.1em', color: '#1E88E5', marginBottom: 4 }}>
                          STEP {step.n}
                        </div>
                        <h3 style={{ margin: '0 0 8px', fontSize: '1.1rem', fontWeight: 700, color: '#1A2638', fontFamily: "'Sora', var(--font-family)" }}>
                          {step.title}
                        </h3>
                        <p style={{ margin: 0, fontSize: '0.875rem', color: '#5B6B82', lineHeight: 1.65, maxWidth: '30ch', marginLeft: 'auto', marginRight: 'auto' }}>
                          {step.desc}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ══ 5. TECH STACK ════════════════════════════════════════════════ */}
        <section style={{ padding: 'clamp(3rem, 6vw, 5.5rem) clamp(1.5rem, 5vw, 3rem)', background: '#fff' }}>
          <div style={{ maxWidth: 1120, margin: '0 auto' }}>
            <motion.div {...fadeUp()} style={{ marginBottom: 'clamp(2rem, 4vw, 3rem)' }}>
              <h2 className="ds-section-title" style={{ marginBottom: 10 }}>Powered by state-of-the-art AI</h2>
              <p style={{ margin: 0, fontSize: '1rem', color: '#5B6B82', lineHeight: 1.6, maxWidth: '55ch' }}>
                Every pipeline is built on peer-reviewed, open-weight architectures — nothing proprietary, nothing opaque.
              </p>
            </motion.div>

            <div className="ds-tech-grid">
              {TECH_CARDS.map((card, i) => (
                <motion.div
                  key={card.name}
                  {...fadeUp(i * 0.07)}
                  className="ds-lift"
                  style={{
                    background: '#FAFBFC',
                    borderRadius: 12,
                    padding: '20px 18px',
                    border: '1px solid #E4E9F0',
                  }}
                >
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: card.accent, marginBottom: 14 }} />
                  <div style={{ fontSize: '0.62rem', fontWeight: 700, letterSpacing: '0.09em', color: '#8C9BAA', textTransform: 'uppercase', marginBottom: 6 }}>
                    {card.task}
                  </div>
                  <h4 style={{ margin: '0 0 10px', fontSize: '0.95rem', fontWeight: 700, color: '#1A2638', fontFamily: "'Sora', var(--font-family)", lineHeight: 1.3 }}>
                    {card.name}
                  </h4>
                  <span style={{
                    display: 'inline-block', fontSize: '0.68rem', fontWeight: 600,
                    padding: '3px 10px', borderRadius: 9999,
                    background: `${card.accent}14`, color: card.accent,
                  }}>
                    {card.detail}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ══ 6. FAQ ACCORDION ═════════════════════════════════════════════ */}
        <section id="faq" style={{ padding: 'clamp(3rem, 6vw, 5.5rem) clamp(1.5rem, 5vw, 3rem)', background: '#EEF2F7' }}>
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            <motion.div {...fadeUp()} style={{ marginBottom: 'clamp(2rem, 4vw, 3rem)' }}>
              <h2 className="ds-section-title" style={{ marginBottom: 10 }}>Common questions</h2>
              <p style={{ margin: 0, fontSize: '1rem', color: '#5B6B82', lineHeight: 1.6 }}>
                Everything you need to know before running your first analysis.
              </p>
            </motion.div>

            <div style={{ display: 'grid', gap: 10 }}>
              {FAQ_ITEMS.map((item, i) => (
                <motion.div key={i} {...fadeUp(i * 0.03)}>
                  <AccordionItem
                    item={item}
                    isOpen={openFaq === i}
                    onToggle={() => setOpenFaq(openFaq === i ? null : i)}
                    reduced={!!prefersReducedMotion}
                  />
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ══ 7. TRUST BADGES ══════════════════════════════════════════════ */}
        <section style={{ padding: 'clamp(3rem, 6vw, 5.5rem) clamp(1.5rem, 5vw, 3rem)', background: '#fff' }}>
          <div style={{ maxWidth: 1120, margin: '0 auto' }}>
            <motion.div {...fadeUp()} style={{ marginBottom: 'clamp(2rem, 4vw, 3rem)', textAlign: 'center' }}>
              <h2 className="ds-section-title">Built on trust, by design</h2>
            </motion.div>

            <div className="ds-trust-grid">
              {TRUST_BADGES.map((badge, i) => {
                const BadgeIcon = badge.Icon;
                return (
                  <motion.div
                    key={badge.title}
                    {...fadeUp(i * 0.08)}
                    style={{
                      display: 'flex', flexDirection: 'column', gap: 14,
                      padding: '24px 22px',
                      background: '#FAFBFC',
                      borderRadius: 12, border: '1px solid #E4E9F0',
                    }}
                  >
                    <div style={{
                      width: 48, height: 48, borderRadius: 10, flexShrink: 0,
                      background: 'rgba(30,136,229,0.09)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#1565C0',
                    }}>
                      <BadgeIcon size={22} />
                    </div>
                    <div>
                      <h4 style={{ margin: '0 0 6px', fontSize: '0.95rem', fontWeight: 700, color: '#1A2638', fontFamily: "'Sora', var(--font-family)" }}>
                        {badge.title}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.855rem', color: '#5B6B82', lineHeight: 1.6 }}>
                        {badge.desc}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ══ 8. CTA STRIP ═════════════════════════════════════════════════ */}
        <section style={{ padding: 'clamp(3.5rem, 8vw, 6rem) clamp(1.5rem, 5vw, 3rem)', background: '#0D47A1' }}>
          <motion.div
            {...fadeUp()}
            style={{ maxWidth: 680, margin: '0 auto', textAlign: 'center', display: 'grid', gap: '1.25rem' }}
          >
            <h2 style={{
              fontFamily: "'Sora', var(--font-family)",
              fontWeight: 800, fontSize: 'clamp(1.9rem, 4.5vw, 3rem)',
              color: '#fff', margin: 0, lineHeight: 1.1, letterSpacing: '-0.02em',
            }}>
              Ready to verify what you see?
            </h2>
            <p style={{ margin: 0, fontSize: '1.05rem', color: 'rgba(255,255,255,0.78)', lineHeight: 1.65 }}>
              No sign-up required. Drop any image, video, article, or screenshot and receive a full explainable AI report in seconds.
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', paddingTop: 4 }}>
              <Link
                to="/analyze"
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  padding: '15px 34px',
                  background: '#fff', color: '#0D47A1',
                  borderRadius: 8, fontWeight: 700, fontSize: '0.95rem',
                  textDecoration: 'none', cursor: 'pointer',
                  boxShadow: '0 4px 18px rgba(0,0,0,0.22)',
                  transition: 'transform 150ms ease, box-shadow 150ms ease',
                  fontFamily: 'inherit',
                }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 6px 24px rgba(0,0,0,0.28)'; }}
                onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = '0 4px 18px rgba(0,0,0,0.22)'; }}
              >
                Start Free Analysis →
              </Link>
              <Link
                to="/about"
                style={{
                  display: 'inline-flex', alignItems: 'center',
                  padding: '15px 28px',
                  background: 'transparent', color: 'rgba(255,255,255,0.88)',
                  border: '2px solid rgba(255,255,255,0.28)',
                  borderRadius: 8, fontWeight: 600, fontSize: '0.95rem',
                  textDecoration: 'none', cursor: 'pointer',
                  transition: 'border-color 150ms ease, color 150ms ease',
                  fontFamily: 'inherit',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.62)'; e.currentTarget.style.color = '#fff'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.28)'; e.currentTarget.style.color = 'rgba(255,255,255,0.88)'; }}
              >
                Learn About DeepShield
              </Link>
            </div>
          </motion.div>
        </section>

      </article>
    </>
  );
}
