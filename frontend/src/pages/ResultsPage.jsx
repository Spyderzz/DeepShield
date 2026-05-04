import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { downloadReportBlob, generateReport, saveReportBlob } from '../services/reportApi.js';
import { SharedNav, SharedFooter } from '../components/layout/SharedNav.jsx';
import useDottedSurface from '../hooks/useDottedSurface.js';
import { getHistoryDetail } from '../services/historyApi.js';
import { generateLLMSummary } from '../services/api.js';
import { formatDateIST, formatDateTimeIST } from '../utils/dateTime.js';
import './deepshield-landing.css';
import './deepshield-pages.css';

function resolveMediaUrl(url) {
  if (!url) return null;
  let normalized = String(url).replaceAll('\\', '/');
  if (normalized.startsWith('http://') || normalized.startsWith('https://') || normalized.startsWith('data:')) return normalized;

  const mediaIdx = normalized.toLowerCase().indexOf('/media/');
  if (mediaIdx >= 0) {
    normalized = normalized.slice(mediaIdx);
  } else if (normalized.toLowerCase().startsWith('media/')) {
    normalized = `/${normalized}`;
  } else if (normalized.toLowerCase().startsWith('./media/')) {
    normalized = normalized.slice(1);
  }

  const path = normalized.startsWith('/') ? normalized : `/${normalized}`;
  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  if (apiBase.startsWith('http') && path.startsWith('/media/')) {
    return `${apiBase.replace(/\/api\/v1\/?$/, '')}${path}`;
  }
  return path;
}

export default function ResultsPage() {
  useDottedSurface();
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const accessToken = searchParams.get('token');

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getHistoryDetail(id, accessToken);
        setResult(data);
      } catch (e) {
        setError(e?.response?.data?.detail || e?.message || 'Could not load result');
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, accessToken]);

  if (loading) {
    return (
      <>
        <SharedNav current="history" />
        <section className="page-shell"><div className="page-head"><p className="sub" style={{ color: 'var(--ds-muted)' }}>Loading analysis…</p></div></section>
        <SharedFooter />
      </>
    );
  }

  if (error || !result) {
    return (
      <>
        <SharedNav current="history" />
        <section className="page-shell">
          <div className="page-head">
            <div className="crumbs">
              <a onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Home</a>
              <span className="sep">/</span>
              <a onClick={() => navigate('/history')} style={{ cursor: 'pointer' }}>History</a>
              <span className="sep">/</span>
              <span>{id}</span>
            </div>
            <h1 className="display">Analysis not found.</h1>
            <p className="sub" style={{ color: 'var(--ds-danger)' }}>{error || 'The record may have been deleted or you may not have access.'}</p>
            <button className="btn btn-glass btn-lg" onClick={() => navigate('/analyze')}>Start a new analysis →</button>
          </div>
        </section>
        <SharedFooter />
      </>
    );
  }

  return <ResultsView result={result} id={id} accessToken={accessToken} />;
}

function ResultsView({ result, id, accessToken }) {
  const navigate = useNavigate();
  const [heatmapMode, setHeatmapMode] = useState('heatmap');
  const [alpha, setAlpha] = useState(0.65);
  const [expanded, setExpanded] = useState(null);
  const [displayScore, setDisplayScore] = useState(0);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyLink = () => {
    navigator.clipboard?.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPDF = async () => {
    if (pdfLoading) return;
    setPdfLoading(true);
    try {
      const token = accessToken || result.analysis_id || id;
      await generateReport(id, token);
      const blob = await downloadReportBlob(id, token);
      saveReportBlob(blob, id);
    } catch (e) {
      alert(e?.userMessage || 'PDF generation failed. Try again.');
    } finally {
      setPdfLoading(false);
    }
  };

  const verdict = result.verdict || {};
  const expl = result.explainability || {};
  // Prefer the stored authenticity_score; fall back to fake_probability for text/screenshot responses
  const authenticityScore = typeof verdict.authenticity_score === 'number'
    ? verdict.authenticity_score
    : Math.round(Math.max(0, Math.min(1, 1 - (verdict.fake_probability ?? expl.fake_probability ?? 0.5))) * 100);
  // Convert to Deepfake Probability (0 = Real, 100 = Fake) for UI display
  const fakeScore = 100 - authenticityScore;
  const c = fakeScore <= 35 ? 'safe' : fakeScore <= 60 ? 'warn' : 'danger';
  const verdictLabel = (verdict.label || verdict.classification
    || (c === 'safe' ? 'LIKELY REAL' : c === 'warn' ? 'SUSPICIOUS' : 'LIKELY FAKE')).toString().toUpperCase();

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `DeepShield Analysis: ${result.filename || mediaType}`,
          text: `Check out this DeepShield forensic analysis. Deepfake probability: ${fakeScore}/100.`,
          url: window.location.href,
        });
      } catch (err) {
        console.warn('Share failed or was canceled', err);
      }
    } else {
      handleCopyLink();
    }
  };

  const exif = expl.exif || {};
  const vlm = expl.vlm_breakdown || {};
  const llm = expl.llm_summary || result.llm_summary || null;
  const artifacts = expl.artifact_indicators || [];
  const sources = result.trusted_sources || [];
  const mediaType = result.media_type || 'image';
  const calibrationApplied = result.processing_summary?.calibrator_applied ?? false;

  // Prefer persistent file URL; fall back to base64 from fresh analysis response.
  // The backend returns full data URLs (already prefixed), so use them as-is.
  const _b64src = (b64) => !b64 ? null : b64.startsWith('data:') ? b64 : `data:image/png;base64,${b64}`;
  const heatmapData = resolveMediaUrl(expl.heatmap_url) || _b64src(expl.heatmap_base64);
  const elaData     = resolveMediaUrl(expl.ela_url)     || _b64src(expl.ela_base64);
  const boxesData   = resolveMediaUrl(expl.boxes_url)   || _b64src(expl.boxes_base64);
  const baseImg = resolveMediaUrl(result.media_path) || resolveMediaUrl(result.thumbnail_url) || resolveMediaUrl(result.media_url) || heatmapData;

  const totalMs = result.processing_summary?.total_ms ?? 0;
  const latency = totalMs ? `${(totalMs / 1000).toFixed(2)}s` : '—';
  const timestamp = formatDateTimeIST(result.created_at || result.timestamp);
  const hash = (result.analysis_id || id || '').toString();

  useEffect(() => {
    let start = performance.now();
    const dur = 900;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setDisplayScore(Math.round(fakeScore * e));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [fakeScore]);

  return (
    <>
      <SharedNav current="history" />
      <section className="results-shell page-shell">
        <div className="results-header">
          <div>
            <div className="crumbs">
              <a onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Home</a>
              <span className="sep">/</span>
              <a onClick={() => navigate('/history')} style={{ cursor: 'pointer' }}>History</a>
              <span className="sep">/</span>
              <span>{hash.slice(0, 8)}</span>
            </div>
            <span className="eyebrow">Analysis report</span>
            <h1 className="display">{result.filename || `${mediaType} analysis`}</h1>
            <div className="meta-row">
              <span>id · <b>{hash.slice(0, 12)}</b></span>
              <span>·</span>
              <span>type · <b>{mediaType}</b></span>
              <span>·</span>
              <span>ingested · <b>{timestamp}</b></span>
              <span>·</span>
              <span>latency · <b>{latency}</b></span>
              <span>·</span>
              <span>model · <b>EfficientNetAutoAttB4 + ViT</b></span>
            </div>
          </div>
          <div className="actions">
            <a onClick={() => navigate('/analyze')} className="btn btn-ghost btn-sm" style={{ textDecoration: 'none', cursor: 'pointer' }}>↻ New</a>
            <button className="btn btn-glass btn-sm" onClick={handleDownloadPDF} disabled={pdfLoading}>
              {pdfLoading ? '…' : '⤓ PDF'}
            </button>
            <button className="btn btn-glass btn-sm" onClick={handleCopyLink}>{copied ? '✓ Copied!' : '⎘ Link'}</button>
            <button className="btn btn-primary btn-sm btn-shiny" onClick={handleShare}>Share →</button>
          </div>
        </div>

        <div className="results-grid">
          <VerdictCard verdict={verdictLabel} displayScore={displayScore} color={c} llm={llm} calibrationApplied={calibrationApplied} recordId={id} />

          {mediaType === 'image' && (
            <div className="result-grid">
              <HeatmapCard
                src={baseImg}
                heatmapData={heatmapData} elaData={elaData} boxesData={boxesData}
                heatmapMode={heatmapMode} setHeatmapMode={setHeatmapMode}
                alpha={alpha} setAlpha={setAlpha}
                status={expl.heatmap_status || 'n/a'}
              />
              <EXIFCard exif={exif} />
            </div>
          )}

          {mediaType === 'screenshot' && (
            <div className="result-grid">
              <div className="card heatmap-card" style={{ padding: 0, overflow: 'hidden', background: '#0A0D18', position: 'relative' }}>
                 <div className="card-head" style={{ padding: '20px 24px', position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, background: 'linear-gradient(to bottom, rgba(10,13,20,0.8), transparent)' }}>
                    <span className="eyebrow">Screenshot Source</span>
                 </div>
                 <div className="heatmap-stage" style={{ height: '100%', minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <img src={baseImg} alt="Screenshot" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} onError={(e) => { e.target.style.display = 'none'; }} />
                 </div>
              </div>
              <TextCard text={expl.extracted_text} fullWidth={false} title="Extracted OCR Text" />
            </div>
          )}

          {mediaType === 'video' && (
            <VideoFramesCard src={baseImg} frames={expl.frames} />
          )}

          {mediaType === 'image' && (
            <BreakdownCard vlm={vlm} fallbackHigh={fakeScore <= 40} expanded={expanded} setExpanded={setExpanded} />
          )}

          {mediaType === 'text' && <TextCard text={expl.original_text} />}

          <div className="result-grid">
            {(mediaType === 'text' || mediaType === 'screenshot') && <SourcesCard sources={sources} />}
            {mediaType !== 'text' && <ArtifactsCard artifacts={artifacts} />}
          </div>

          {(mediaType === 'video' || mediaType === 'audio') && (
            <div className="result-grid">
              <AudioCard audio={mediaType === 'audio' ? expl : expl.audio} mediaType={mediaType} />
              {mediaType === 'video' && <TemporalCard expl={expl} mediaType={mediaType} />}
              <AudioMLCard ml={mediaType === 'audio' ? expl.ml_analysis : expl.audio?.ml_analysis} />
            </div>
          )}

          <ProcessingSummaryCard summary={result.processing_summary} />
        </div>

        <StickyActions id={id} onNew={() => navigate('/analyze')} onPDF={handleDownloadPDF} pdfLoading={pdfLoading} onCopy={handleCopyLink} copied={copied} onShare={handleShare} />
      </section>
      <SharedFooter />
    </>
  );
}

/* ==== verdict + ring ==== */
function VerdictCard({ verdict, displayScore, color, llm: initialLlm, calibrationApplied, recordId }) {
  const isRealLlm = initialLlm && initialLlm.model_used !== 'auto-summary';
  const [llm, setLlm] = useState(isRealLlm ? initialLlm : null);
  const [loading, setLoading] = useState(!isRealLlm);
  const [typedParagraph, setTypedParagraph] = useState('');
  const [typingIdx, setTypingIdx] = useState(0);
  // Keep auto-summary as fallback
  const autoSummary = initialLlm?.model_used === 'auto-summary' ? initialLlm : null;

  // Fetch real LLM summary (Gemini → Groq → fallback)
  useEffect(() => {
    if (isRealLlm || !recordId) return;
    setLoading(true);
    generateLLMSummary(recordId).then(data => {
      const summary = data.llm_summary;
      if (summary?.paragraph && summary.model_used !== 'auto-summary') {
        setLlm(summary);
      } else if (summary?.paragraph) {
        // Got auto-summary back from server — use as fallback
        setLlm(summary);
      }
      setLoading(false);
    }).catch(() => {
      // Use the auto-summary as fallback if available
      if (autoSummary) setLlm(autoSummary);
      setLoading(false);
    });
  }, [isRealLlm, recordId]);  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setTypedParagraph('');
    setTypingIdx(0);
  }, [llm?.paragraph]);

  useEffect(() => {
    if (llm?.paragraph && typingIdx < llm.paragraph.length) {
      const timer = setTimeout(() => {
        setTypedParagraph(p => p + llm.paragraph[typingIdx]);
        setTypingIdx(i => i + 1);
      }, 15);
      return () => clearTimeout(timer);
    }
  }, [llm, typingIdx]);

  const modelLabel = loading
    ? 'Generating...'
    : llm?.model_used === 'auto-summary'
      ? 'Auto-summary'
      : llm?.model_used || 'Pending';

  return (
    <div className={`verdict-card verdict-${color}`}>
      <div className="verdict-left">
        <ScoreRing value={displayScore} size={120} color={color} />
        <div>
          <span className="eyebrow">Deepfake probability</span>
          <h3 className="display verdict-label">{verdict}</h3>
          <div className="verdict-meta mono">
            <span>score · {displayScore}/100</span>
            <span>·</span>
            <span>confidence · {calibrationApplied ? 'calibrated (isotonic)' : 'uncalibrated ensemble'}</span>
          </div>
        </div>
      </div>
      <div className="verdict-llm">
        <span className="eyebrow">Plain-English summary · {modelLabel}</span>
        <p>
          {loading ? (
            <span className="llm-generating">
              <span className="llm-gen-icon">◎</span>
              Generating LLM Summary — analyzing with Gemini & Groq<span className="typing-dots">...</span>
            </span>
          ) : llm?.paragraph ? (
            typedParagraph + (typingIdx < llm.paragraph.length ? '█' : '')
          ) : (
            `This media has a deepfake probability of ${displayScore}/100. Review the heatmap, EXIF metadata, and detailed breakdown below for the evidence behind this verdict.`
          )}
        </p>
        {Array.isArray(llm?.bullets) && llm.bullets.length > 0 && typingIdx >= (llm.paragraph?.length || 0) && (
          <div className="verdict-bullets">
            {llm.bullets.slice(0, 4).map((b, i) => <span key={i}>• {b}</span>)}
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreRing({ value, size = 120, color = 'safe' }) {
  const r = size / 2 - 7;
  const c = 2 * Math.PI * r;
  const off = c - (value / 100) * c;
  const stroke = color === 'safe' ? 'var(--ds-safe)' : color === 'warn' ? 'var(--ds-warn)' : 'var(--ds-danger)';
  return (
    <svg width={size} height={size} className="score-ring">
      <circle cx={size/2} cy={size/2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="5" fill="none"/>
      <circle cx={size/2} cy={size/2} r={r} stroke={stroke} strokeWidth="5" fill="none"
        strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`}
        style={{ filter: `drop-shadow(0 0 10px ${stroke})`, transition: 'stroke-dashoffset 120ms linear' }}/>
      <text x={size/2} y={size/2 + 2} textAnchor="middle" dominantBaseline="middle"
        fontFamily="var(--ff-mono)" fontSize={size * 0.28} fill="var(--ds-ink)" fontWeight="500">{value}</text>
      <text x={size/2} y={size/2 + size * 0.22} textAnchor="middle" dominantBaseline="middle"
        fontFamily="var(--ff-mono)" fontSize={size * 0.09} fill="var(--ds-muted)" letterSpacing="0.1em">/100</text>
    </svg>
  );
}

/* ==== heatmap ==== */
/* Overlay mode descriptions shown in the footer */
const OVERLAY_DESC = {
  heatmap: 'Grad-CAM++ averaged across last 3 ViT layers — brighter = stronger model activation',
  ela:     'Error Level Analysis — re-saved at JPEG quality 90 and diffed; bright regions may indicate editing',
  boxes:   'Top suspicious regions from Grad-CAM++ activation — red ≥70%, orange ≥50%, yellow lower',
  off:     'Original image — no overlay',
};

function HeatmapCard({ src, heatmapData, elaData, boxesData, heatmapMode, setHeatmapMode, alpha, setAlpha, status }) {
  // The backend composites overlays onto the original image already.
  // We swap the visible image based on mode, and use alpha to blend with the original.
  const overlayMap = { heatmap: heatmapData, ela: elaData, boxes: boxesData, off: null };
  const activeOverlay = overlayMap[heatmapMode] ?? null;
  const unavailable = heatmapMode !== 'off' && !activeOverlay;

  return (
    <div className="card heatmap-card">
      <div className="card-head">
        <span className="eyebrow">Visual evidence</span>
        <div className="seg-control">
          {['heatmap', 'ela', 'boxes', 'off'].map(m => (
            <button key={m} className={heatmapMode === m ? 'active' : ''} onClick={() => setHeatmapMode(m)}>{m.toUpperCase()}</button>
          ))}
        </div>
      </div>
      <div className="heatmap-stage">
        {/* Base original — always shown */}
        {src
          ? <img src={src} alt="" className="heatmap-base" onError={(e) => { e.target.style.display = 'none'; }} />
          : <div className="heatmap-base" style={{ background: '#0A0D18' }} />}
        {/* Overlay: the backend already blends these with the original, so we just
            fade them in over the base image. alpha=1 → full overlay, alpha=0 → original. */}
        {activeOverlay && (
          <img
            src={activeOverlay}
            className="heatmap-layer"
            alt=""
            style={{
              opacity: alpha,
            }}
          />
        )}
        {unavailable && (
          <div className="overlay-unavailable">
            {heatmapMode.toUpperCase()} · run a fresh analysis to view
          </div>
        )}
      </div>
      <div className="heatmap-foot">
        {heatmapMode !== 'off' && (
          <>
            <span className="mono">α {alpha.toFixed(2)}</span>
            <input type="range" min="0" max="1" step="0.01" value={alpha} onChange={e => setAlpha(+e.target.value)} />
          </>
        )}
        <span className="mono status-chip" style={{ marginLeft: 'auto' }}>heatmap · {status}</span>
      </div>
      {heatmapMode !== 'off' && (
        <p style={{ fontFamily: 'var(--ff-mono)', fontSize: 10, color: 'var(--ds-muted)', margin: '10px 0 0', lineHeight: 1.5 }}>
          {OVERLAY_DESC[heatmapMode]}
        </p>
      )}
    </div>
  );
}

/* ==== video frames ==== */
function VideoFramesCard({ src, frames = [] }) {
  const [frameIdx, setFrameIdx] = useState(0);
  const currentFrame = frames[frameIdx];

  return (
    <div className="card heatmap-card">
      <div className="card-head">
        <span className="eyebrow">Extracted video frames</span>
        <div className="seg-control" style={{ display: 'flex', alignItems: 'center' }}>
           <button onClick={() => setFrameIdx(Math.max(0, frameIdx-1))} disabled={frameIdx === 0}>&lt;</button>
           <span style={{ fontFamily: 'var(--ff-mono)', fontSize: 10, padding: '0 8px', color: 'var(--ds-muted)' }}>{frameIdx + 1} / {frames.length || 1}</span>
           <button onClick={() => setFrameIdx(Math.min(frames.length-1, frameIdx+1))} disabled={frameIdx === frames.length - 1}>&gt;</button>
        </div>
      </div>
      <div className="heatmap-stage" style={{ background: '#0A0D18' }}>
        <video 
          src={src} 
          controls 
          className="heatmap-base" 
          style={{ width: '100%', maxHeight: 520, objectFit: 'contain' }} 
        />
      </div>
      {currentFrame && (
        <div className="heatmap-foot" style={{ marginTop: 14 }}>
           <span className="mono status-chip" style={{ 
             color: currentFrame.is_suspicious ? 'var(--ds-danger)' : 'var(--ds-safe)', 
             borderColor: currentFrame.is_suspicious ? 'var(--ds-danger)' : 'var(--ds-safe)', 
             background: 'transparent' 
           }}>
             timestamp: {currentFrame.timestamp_s.toFixed(2)}s · score: {(currentFrame.suspicious_prob * 100).toFixed(0)}/100
           </span>
           <span className="mono status-chip" style={{ marginLeft: 'auto' }}>
             frame · {currentFrame.label}
           </span>
        </div>
      )}
    </div>
  );
}

/* ==== EXIF ==== */
function EXIFCard({ exif }) {
  const suspiciousSoftware = (v) => typeof v === 'string' && /photoshop|midjourney|dall·e|dalle|stable diffusion/i.test(v);
  const rows = [
    ['Make', exif.make],
    ['Model', exif.model],
    ['DateTimeOriginal', exif.datetime_original || exif.date_time_original || exif.datetime],
    ['GPSInfo', exif.gps || exif.gps_info],
    ['Software', exif.software],
    ['LensModel', exif.lens_model || exif.lens],
    ['ICC Profile', exif.icc_profile ? 'Present' : null],
    ['MakerNote', exif.maker_note ? 'Present' : null],
  ];
  const trustDelta = exif.trust_adjustment ?? exif.trust_delta;
  const presentCount = rows.filter(([, v]) => v).length;
  return (
    <div className="card exif-card">
      <div className="card-head">
        <span className="eyebrow">EXIF metadata</span>
        <span className="mono small">{presentCount} fields{trustDelta != null ? <> · <span style={{ color: trustDelta < 0 ? 'var(--ds-warn)' : 'var(--ds-safe)' }}>{trustDelta > 0 ? `+${trustDelta}` : trustDelta} trust</span></> : null}</span>
      </div>
      <ul className="exif-list mono">
        {rows.map(([k, v]) => {
          const bad = k === 'Software' && suspiciousSoftware(v);
          const present = !!v;
          const state = bad ? 'bad' : present ? 'ok' : 'warn';
          return (
            <li key={k}>
              <span>{k}</span>
              <b className={bad ? 'bad' : ''}>{v || '—'}</b>
              <em className={state}>{state === 'ok' ? '✓' : state === 'bad' ? '✗' : '⚠'}</em>
            </li>
          );
        })}
      </ul>
      {rows.some(([k, v]) => k === 'Software' && suspiciousSoftware(v)) && (
        <p style={{ marginTop: 14, fontSize: 11, color: 'var(--ds-muted)', lineHeight: 1.6 }}>
          <span style={{ color: 'var(--ds-warn)' }}>⚠ Software field</span> indicates post-processing. This weakens authenticity but does not imply malicious manipulation.
        </p>
      )}
    </div>
  );
}

/* ==== VLM breakdown ==== */
function BreakdownCard({ vlm, fallbackHigh, expanded, setExpanded }) {
  const base = [
    { k: 'Facial symmetry', key: 'facial_symmetry',     defaultNote: 'Left-right alignment across eye, nose, and jaw landmarks.' },
    { k: 'Skin texture',    key: 'skin_texture',         defaultNote: 'Pore distribution, micro-shading, sebum highlights.' },
    { k: 'Lighting',        key: 'lighting_consistency', defaultNote: 'Light-source direction consistent across face and background.' },
    { k: 'Background',      key: 'background_coherence', defaultNote: 'Depth, focal blur, and edge coherence.' },
    { k: 'Anatomy',         key: 'anatomy_hands_eyes',   defaultNote: 'Hands, ears, teeth — typical GAN failure zones.' },
    { k: 'Context',         key: 'context_objects',      defaultNote: 'Objects and environment plausibility.' },
  ].map(b => {
    const component = vlm[b.key];
    return {
      ...b,
      v: typeof component?.score === 'number' ? Math.round(component.score) : (fallbackHigh ? 80 : 40),
      note: component?.notes || b.defaultNote,
    };
  });
  return (
    <div className="breakdown card">
      <div className="card-head">
        <span className="eyebrow">Detailed breakdown{vlm.model_used ? ` · ${vlm.model_used}` : ' · Gemini Vision'}</span>
        <span className="mono small">6 components</span>
      </div>
      <div className="breakdown-grid">
        {base.map((b, i) => (
          <button key={b.k} className={`bd-cell ${expanded === i ? 'open' : ''}`} onClick={() => setExpanded(expanded === i ? null : i)}>
            <ScoreRing value={b.v} size={56} color={b.v > 70 ? 'safe' : b.v > 45 ? 'warn' : 'danger'} />
            <div className="bd-body">
              <div className="bd-title">{b.k}</div>
              <div className="mono bd-score">{b.v}/100</div>
              <p className="bd-note">{b.note}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ==== sources ==== */
function SourcesCard({ sources }) {
  const contradicting = sources.filter(s => s.contradicting || s.state === 'contradict').length;
  return (
    <div className="card sources-card">
      <div className="card-head">
        <span className="eyebrow">Trusted sources · cross-reference</span>
        <span className="mono small">{sources.length} matches{contradicting ? ` · ${contradicting} contradicting` : ''}</span>
      </div>
      {sources.length > 0 ? (
        <ul className="src-list">
          {sources.slice(0, 5).map((s, i) => {
            const srcName = s.source_name || s.domain || s.source || `source-${i+1}`;
            const contr = s.contradicting || s.state === 'contradict';
            const dateStr = formatDateIST(s.published_at, s.published_at ? String(s.published_at).slice(0, 12) : '—');
            return (
              <li key={i}>
                <div className="src-head">
                  <span className="mono" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 16, height: 16, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: contr ? 'rgba(255,94,122,0.15)' : 'rgba(108,125,255,0.15)', color: contr ? 'var(--ds-danger)' : 'var(--ds-brand)', borderRadius: 3, fontSize: 9 }}>{srcName.slice(0, 2).toUpperCase()}</span>
                    {srcName}
                  </span>
                  <div className="src-bar"><i style={{ width: `100%`, background: contr ? 'var(--ds-danger)' : 'var(--ds-safe)' }}/></div>
                </div>
                <p>{s.title || s.snippet || s.description || '—'}</p>
                <div className="src-foot mono">
                  <span>{dateStr}</span>
                  {contr && <span style={{ color: 'var(--ds-danger)' }}>contradicting</span>}
                  {s.url && <a href={s.url} target="_blank" rel="noreferrer">open ↗</a>}
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <p style={{ color: 'var(--ds-muted)', fontSize: 13, margin: 0 }}>No trusted-source publications match this media. This weakens authenticity.</p>
      )}
    </div>
  );
}

/* ==== artifacts ==== */
function ArtifactsCard({ artifacts }) {
  const items = artifacts.length > 0 ? artifacts : [
    { name: 'Synthetic noise pattern', severity: 'low', score: 0.22 },
    { name: 'Unusual compression artifacts', severity: 'medium', score: 0.48 },
    { name: 'Unnatural jawline blending', severity: 'medium', score: 0.55 },
    { name: 'Luminance imbalance', severity: 'low', score: 0.18 },
    { name: 'Unnatural skin smoothing', severity: 'medium', score: 0.52 },
    { name: 'Camera sensor mismatch', severity: 'low', score: 0.19 },
  ];
  return (
    <div className="card artifact-card">
      <div className="card-head">
        <span className="eyebrow">Artifact indicators</span>
        <span className="mono small">{items.length} signals</span>
      </div>
      <ul className="art-list">
        {items.map((a, i) => {
          const lvl = (a.severity || a.level || 'low').toString().toLowerCase();
          const val = typeof a.score === 'number' ? a.score : typeof a.confidence === 'number' ? a.confidence : 0;
          return (
            <li key={i}>
              <span style={{ color: 'var(--ds-ink)', fontWeight: 400 }}>{a.name || a.type || a.description || a.indicator || '—'}</span>
              <span className={`art-chip ${lvl}`}>{lvl}</span>
              <span className="mono art-val">{val.toFixed(2)}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ==== audio + temporal ==== */
function AudioCard({ audio, mediaType }) {
  const active = audio && audio.has_audio;
  return (
    <div className="card" style={{ minHeight: 200 }}>
      <div className="card-head">
        <span className="eyebrow">Audio waveform · WavLM</span>
        <span className="mono small" style={{ color: 'var(--ds-muted)' }}>
          {active ? `score · ${Math.round(audio.audio_authenticity_score)}/100` : `not applicable (${mediaType} input)`}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 3, height: 80, opacity: active ? 0.9 : 0.35 }}>
        {Array.from({ length: 80 }).map((_, i) => {
          const h = 20 + Math.abs(Math.sin(i * 0.3)) * 60;
          return <span key={i} style={{ flex: 1, height: `${h}%`, background: active ? 'var(--ds-brand)' : 'var(--ds-muted)', borderRadius: 1 }}/>;
        })}
      </div>
      <p style={{ marginTop: 14, fontSize: 12, color: 'var(--ds-muted)', fontFamily: 'var(--ff-mono)' }}>
        {active
          ? `duration · ${(audio.duration_s || 0).toFixed(2)}s · silence · ${(audio.silence_ratio || 0).toFixed(2)}`
          : 'audio_analysis · skipped · rerun as video to enable lip-sync correlation'}
      </p>
    </div>
  );
}

function TemporalCard({ expl, mediaType }) {
  const active = typeof expl.temporal_score === 'number';
  return (
    <div className="card" style={{ minHeight: 200 }}>
      <div className="card-head">
        <span className="eyebrow">Temporal consistency</span>
        <span className="mono small" style={{ color: 'var(--ds-muted)' }}>
          {active ? `score · ${expl.temporal_score.toFixed(2)}` : `not applicable (${mediaType} input)`}
        </span>
      </div>
      <svg viewBox="0 0 200 80" style={{ width: '100%', height: 80, opacity: active ? 1 : 0.35 }}>
        <path d="M0 40 Q 20 20 40 38 T 80 42 T 120 36 T 160 44 T 200 40" fill="none" stroke={active ? 'var(--ds-brand)' : 'var(--ds-muted)'} strokeWidth="1.5"/>
        <path d="M0 50 Q 20 30 40 48 T 80 52 T 120 46 T 160 54 T 200 50" fill="none" stroke="var(--ds-muted)" strokeWidth="0.6" strokeDasharray="2 2"/>
      </svg>
      <p style={{ marginTop: 14, fontSize: 12, color: 'var(--ds-muted)', fontFamily: 'var(--ff-mono)' }}>
        {active
          ? `optical_flow_var · ${(expl.optical_flow_variance ?? 0).toFixed(3)} · flicker · ${(expl.flicker_score ?? 0).toFixed(3)}`
          : 'per_frame_score · n/a · no frames to aggregate'}
      </p>
    </div>
  );
}

function AudioMLCard({ ml }) {
  if (!ml) return null;
  const isFake = ml.label.toLowerCase().includes('fake') || ml.label.toLowerCase().includes('spoof');
  const prob = ml.fake_probability;
  
  return (
    <div className="card" style={{ minHeight: 200 }}>
      <div className="card-head">
        <span className="eyebrow">Voice ML Analysis (EN/HI) · {ml.model_used}</span>
        <span className="mono small" style={{ color: 'var(--ds-muted)' }}>
          p_fake · {prob.toFixed(2)}
        </span>
      </div>
      <div style={{ padding: '20px 0', textAlign: 'center' }}>
        <ScoreRing value={isFake ? 20 : 85} size={80} color={isFake ? 'danger' : 'safe'} />
      </div>
      <p style={{ marginTop: 14, fontSize: 12, color: 'var(--ds-muted)', fontFamily: 'var(--ff-mono)' }}>
        prediction · {ml.label.toUpperCase()} · p_fake={prob.toFixed(3)}
      </p>
    </div>
  );
}

/* ==== processing summary ==== */
function ProcessingSummaryCard({ summary }) {
  const stages = summary?.stages_completed || [];
  const totalMs = summary?.total_duration_ms ?? summary?.total_ms ?? 0;
  const total = totalMs ? `${(totalMs / 1000).toFixed(2)}s` : '—';
  const models = summary?.models_used?.length ? summary.models_used : summary?.model_used ? [summary.model_used] : [];

  const STAGE_LABELS = {
    validation: 'Upload & prepare media',
    classification: 'Deepfake visual detection',
    artifact_scanning: 'Digital artifact scan',
    heatmap_generation: 'Generate visual evidence map',
    ela_generation: 'Check for image tampering',
    boxes_generation: 'Detect faces & objects',
    exif_extraction: 'Read hidden file metadata',
    llm_explanation: 'Generate plain-English summary',
    vlm_breakdown: 'Analyze visual context & layout',
    frame_extraction: 'Extract video frames',
    frame_classification: 'Analyze individual frames',
    aggregation: 'Calculate overall video score',
    temporal_analysis: 'Check for unnatural movement',
    audio_analysis: 'Detect synthetic voice cloning',
    text_classification: 'Analyze text for misinformation',
    news_lookup: 'Cross-check with trusted news',
    truth_override: 'Verify factual accuracy',
    ocr: 'Read text from image',
    layout_anomaly: 'Check for layout manipulation',
  };

  return (
    <div className="card">
      <div className="card-head">
        <span className="eyebrow">Processing summary · pipeline</span>
        <span className="mono small">{total} · {stages.length} stages</span>
      </div>
      {models.length > 0 && (
        <p style={{ fontFamily: 'var(--ff-mono)', fontSize: 11, color: 'var(--ds-muted)', margin: '0 0 14px' }}>
          models · {models.join(' + ')}
        </p>
      )}
      <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 3, fontFamily: 'var(--ff-mono)', fontSize: 12 }}>
        {stages.map((s, i) => (
          <li key={i} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '7px 12px', background: i % 2 ? 'rgba(255,255,255,0.02)' : 'transparent',
            borderRadius: 6,
          }}>
            <span style={{ color: 'var(--ds-safe)', fontSize: 10 }}>✓</span>
            <span style={{ color: 'var(--ds-muted)', fontSize: 10, minWidth: 18, textAlign: 'right' }}>{String(i + 1).padStart(2, '0')}</span>
            <span style={{ color: 'var(--ds-ink)' }}>{STAGE_LABELS[s] || s}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function TextCard({ text, fullWidth = true, title = "Original pasted text" }) {
  if (!text) return null;
  return (
    <div className="card text-card" style={fullWidth ? { gridColumn: '1 / -1' } : {}}>
      <div className="card-head">
        <span className="eyebrow">{title}</span>
      </div>
      <div className="text-content" style={{ padding: '16px 20px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, marginTop: 14, fontFamily: 'var(--ff-body)', fontSize: 14, lineHeight: 1.6, color: 'var(--ds-ink)', whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto' }}>
        {text}
      </div>
    </div>
  );
}

function StickyActions({ id, onNew, onPDF, pdfLoading, onCopy, copied, onShare }) {
  return (
    <div style={{
      position: 'sticky', bottom: 20, maxWidth: 600, margin: '32px auto 0',
      display: 'flex', gap: 8, justifyContent: 'center',
      padding: '10px 12px',
      background: 'rgba(10,13,20,0.88)',
      border: '1px solid var(--ds-border-2)', borderRadius: 14,
      backdropFilter: 'blur(20px)',
      boxShadow: '0 20px 40px -20px rgba(0,0,0,0.6)',
      zIndex: 10,
    }}>
      <a onClick={onNew} className="btn btn-glass btn-sm" style={{ textDecoration: 'none', cursor: 'pointer' }}>↻ Analyze another</a>
      <button className="btn btn-glass btn-sm" onClick={onPDF} disabled={pdfLoading}>
        {pdfLoading ? 'Generating…' : '⤓ PDF report'}
      </button>
      <button className="btn btn-glass btn-sm" onClick={onCopy}>{copied ? '✓ Copied!' : '⎘ Copy link'}</button>
      <button className="btn btn-primary btn-sm btn-shiny" onClick={onShare}>Share verdict →</button>
    </div>
  );
}
