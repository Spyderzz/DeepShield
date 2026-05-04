import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SharedNav, SharedFooter } from '../components/layout/SharedNav.jsx';
import LayerStack from '../components/layout/LayerStack.jsx';
import useDottedSurface from '../hooks/useDottedSurface.js';
import { listHistory } from '../services/historyApi.js';
import {
  analyzeImage, analyzeText, analyzeScreenshot, analyzeAudio, submitVideoJob, pollVideoJob,
} from '../services/analyzeApi.js';
import { resolveMediaUrl, generateLLMSummary } from '../services/api.js';
import { formatDateTimeIST } from '../utils/dateTime.js';
import { useAuth } from '../contexts/AuthContext.jsx';
import ConsentModal, { useConsent } from '../components/common/ConsentModal.jsx';
import './deepshield-landing.css';
import './deepshield-pages.css';

const MODES = [
  { k: 'image',      label: 'Image',      icon: '🖼', accept: 'image/*' },
  { k: 'video',      label: 'Video',      icon: '▶',  accept: 'video/*' },
  { k: 'text',       label: 'Text',       icon: '¶',  accept: null },
  { k: 'screenshot', label: 'Screenshot', icon: '▭',  accept: 'image/*' },
  { k: 'audio',      label: 'Audio',      icon: '🎙',  accept: 'audio/*' },
];

const MODE_STAGES = {
  image:      ['Upload media', 'Prepare image', 'Visual deepfake detection', 'Generate evidence map', 'Check metadata & tampering', 'Finalizing verdict'],
  video:      ['Upload media', 'Extract video frames', 'Analyze individual frames', 'Check for unnatural movement', 'Analyze audio & lip-sync', 'Finalizing verdict'],
  text:       ['Read text input', 'Prepare text content', 'Scan for sensationalism', 'Cross-check trusted sources', 'Verify factual accuracy', 'Finalizing verdict'],
  screenshot: ['Upload media', 'Read text from image', 'Check for layout manipulation', 'Analyze claim credibility', 'Generate visual map', 'Finalizing verdict'],
  audio:      ['Upload media', 'Prepare audio', 'Extract vocal patterns', 'Detect synthetic voice cloning', 'Analyze acoustic signals', 'Finalizing verdict'],
};

const VIDEO_STAGE_PROGRESS = {
  queued: 5,
  frame_extraction: 20,
  aggregation: 60,
  audio_analysis: 75,
  storage: 86,
  persist: 95,
  done: 100,
};

const SAMPLE_SRC = 'https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=640&q=80&auto=format&fit=crop';

async function fetchSampleAsFile(url, filename = 'sample.jpg') {
  const r = await fetch(url);
  const b = await r.blob();
  return new File([b], filename, { type: b.type || 'image/jpeg' });
}



export default function AnalyzePage() {
  useDottedSurface();
  const navigate = useNavigate();
  const { isAuthed } = useAuth();

  const [mode, setMode] = useState('image');
  const [stage, setStage] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [activeStage, setActiveStage] = useState(0);
  const [textVal, setTextVal] = useState('');
  const [cache, setCache] = useState(true);
  const [urlVal, setUrlVal] = useState('');
  const [lang, setLang] = useState('en');
  const [error, setError] = useState(null);
  const fileRef = useRef(null);
  const jobId = useRef(Math.random().toString(36).slice(2, 10).toUpperCase());
  const [recent, setRecent] = useState([]);
  const [previewUrl, setPreviewUrl] = useState(null);
  const previewRef = useRef(null);
  const { needed: consentNeeded, requestConsent, accept: acceptConsent, decline: declineConsent } = useConsent();

  useEffect(() => {
    return () => { if (previewRef.current) URL.revokeObjectURL(previewRef.current); };
  }, []);

  const segRefs = useRef([]);
  const [segPill, setSegPill] = useState({ left: 0, width: 0 });

  useEffect(() => {
    const idx = MODES.findIndex(m => m.k === mode);
    const el = segRefs.current[idx];
    if (el) setSegPill({ left: el.offsetLeft, width: el.offsetWidth });
  }, [mode]);

  const elapsedRef = useRef(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (stage !== 'processing') { elapsedRef.current = 0; setElapsed(0); return; }
    const stages = MODE_STAGES[mode];
    const t0 = Date.now();
    elapsedRef.current = 0;
    // Asymptotic easing: fast start, smooth deceleration — never truly stops
    const id = setInterval(() => {
      const secs = (Date.now() - t0) / 1000;
      elapsedRef.current = secs;
      setElapsed(secs);
      // Approaches 98 asymptotically: progress = 98 * (1 - e^(-t/k))
      // k controls speed: smaller = faster start. 8 gives ~75% at 12s, ~90% at 18s
      const k = 8;
      const p = 98 * (1 - Math.exp(-secs / k));
      setProgress(p);
      setActiveStage(Math.min(stages.length - 1, Math.floor(p / (100 / stages.length))));
    }, 100);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, mode]);

  useEffect(() => {
    (async () => {
      try {
        if (isAuthed) {
          const data = await listHistory(6, 0);
          setRecent(data.items || []);
        } else {
          setRecent([]);
        }
      } catch (e) {
        // ignore
      }
    })();
  }, [isAuthed]);

  const canStart = mode === 'text' ? textVal.trim().length >= 50 : true;

  const runAnalysis = async (payload) => {
    setError(null);
    setProgress(0);
    setActiveStage(0);
    setStage('processing');
    try {
      const options = { cache, languageHint: lang };
      let data;
      if (mode === 'image') {
        data = await analyzeImage(payload, options);
      } else if (mode === 'video') {
        const job = await submitVideoJob(payload, options);
        jobId.current = job.job_id || jobId.current;
        data = await pollVideoJob(job.job_id, {
          onProgress: (j) => {
            const nextProgress = typeof j.progress === 'number'
              ? j.progress
              : VIDEO_STAGE_PROGRESS[j.stage] || 0;
            setProgress(Math.max(0, Math.min(99, nextProgress)));
            setActiveStage(Math.min(
              MODE_STAGES.video.length - 1,
              Math.floor(nextProgress / (100 / MODE_STAGES.video.length)),
            ));
          },
        });
      } else if (mode === 'text') {
        data = await analyzeText(payload, options);
      } else if (mode === 'screenshot') {
        data = await analyzeScreenshot(payload, options);
      } else if (mode === 'audio') {
        data = await analyzeAudio(payload, options);
      }
      setProgress(95);
      setActiveStage(MODE_STAGES[mode].length - 1);
      const id = data?.record_id || data?.analysis_id;
      const tokenParam = !isAuthed && data?.record_id && data?.analysis_id
        ? `?token=${encodeURIComponent(data.analysis_id)}`
        : '';

      if (!id) { setStage('idle'); return; }

      // Fire LLM generation while user sees "Finalizing verdict"
      // Wait up to 5s — if LLM finishes early, navigate immediately with it
      const llmResult = await Promise.race([
        generateLLMSummary(id)
          .then(res => res.llm_summary || null)
          .catch(() => null),
        new Promise(r => setTimeout(() => r(null), 5000)),
      ]);

      // If LLM resolved in time with a real summary, attach it
      if (llmResult && llmResult.model_used !== 'auto-summary') {
        if (data.explainability?.llm_summary !== undefined) {
          data.explainability.llm_summary = llmResult;
        } else {
          data.llm_summary = llmResult;
        }
      }

      setProgress(100);
      setTimeout(() => {
        navigate(`/results/${id}${tokenParam}`, { state: { result: data } });
      }, 300);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Analysis failed');
      setStage('idle');
    }
  };

  const onPickFile = async (file) => {
    if (!file) return;
    const ok = await requestConsent();
    if (!ok) return;
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    if (file instanceof File && file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      previewRef.current = url;
      setPreviewUrl(url);
    } else {
      previewRef.current = null;
      setPreviewUrl(null);
    }
    runAnalysis(file);
  };

  const start = async () => {
    if (mode === 'text') {
      if (!canStart) return;
      runAnalysis(textVal);
      return;
    }
    if (urlVal.trim()) {
      try {
        const f = await fetchSampleAsFile(urlVal.trim(), 'pasted-url');
        runAnalysis(f);
      } catch (_e) {
        setError('Could not fetch that URL');
      }
      return;
    }
    fileRef.current?.click();
  };

  const useSample = async () => {
    try {
      const f = await fetchSampleAsFile(SAMPLE_SRC, 'sample.jpg');
      runAnalysis(f);
    } catch (_e) {
      setError('Could not load sample');
    }
  };

  return (
    <>
      {consentNeeded && <ConsentModal onAccept={acceptConsent} onDecline={declineConsent} />}
      <SharedNav current="analyze" />
      <section className="analyze-shell page-shell">
        <div className="page-head">
          <div className="crumbs">
            <a onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Home</a>
            <span className="sep">/</span>
            <span>Analyze</span>
          </div>
          <span className="eyebrow">Forensic console</span>
          <h1 className="display">Analyze <em className="italic accent">any media.</em></h1>
          <p className="sub">Drop an image, video, article, or screenshot. The pipeline routes to the right forensic stack and returns a calm, evidence-backed verdict.</p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 32 }}>
          <div className="mode-seg">
            <div className="mode-seg-pill" style={{ left: segPill.left, width: segPill.width }}/>
            {MODES.map((m, i) => (
              <button key={m.k} ref={el => segRefs.current[i] = el}
                className={`mode-seg-btn ${mode === m.k ? 'active' : ''}`}
                onClick={() => { setMode(m.k); setStage('idle'); setError(null); }}>
                <span style={{ opacity: 0.6 }}>{m.icon}</span>{m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="analyze-panel">
          <div className="analyze-console">
            {stage === 'idle' && mode !== 'text' && (
              <>
                <div
                  className="drop-large"
                  onClick={start}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => { e.preventDefault(); onPickFile(e.dataTransfer.files?.[0]); }}
                >
                  <input
                    ref={fileRef}
                    type="file"
                    accept={MODES.find(m => m.k === mode)?.accept}
                    style={{ display: 'none' }}
                    onChange={(e) => onPickFile(e.target.files?.[0])}
                  />
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
                  <p className="hint">{mode === 'image' ? 'PNG · JPEG · WebP · 20MB' : mode === 'video' ? 'MP4 · WebM · MOV · 100MB' : 'PNG · JPEG · 20MB'}</p>
                  <p className="or-paste">or paste a URL · or click to browse</p>
                  <button className="btn btn-glass btn-sm" onClick={(e) => { e.stopPropagation(); useSample(); }}>Use sample</button>
                  {error && <p style={{ color: 'var(--ds-danger)', marginTop: 12, fontSize: 13 }}>{error}</p>}
                </div>
                <div className="options-row">
                  <label className="opt"><input type="checkbox" checked={cache} onChange={e => setCache(e.target.checked)} /> Cache result</label>
                  <input type="text" placeholder={mode === 'image' ? '…or paste image URL' : '…or paste media URL'} value={urlVal} onChange={e => setUrlVal(e.target.value)} />
                  <div className="grow"/>
                  <select value={lang} onChange={e => setLang(e.target.value)}>
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                    <option value="ta">Tamil</option>
                    <option value="bn">Bengali</option>
                  </select>
                </div>
              </>
            )}

            {stage === 'idle' && mode === 'text' && (
              <>
                <div className="text-panel">
                  <div className="ta-head">
                    <span className="eyebrow">Paste article text</span>
                    <span className="ta-meta">{textVal.length} / 10000 chars · min 50</span>
                  </div>
                  <textarea
                    placeholder="Paste a news headline and article body. DeepShield runs XLM-RoBERTa, NER-anchored source lookup, and truth-override against trusted Indian + international domains."
                    value={textVal}
                    onChange={e => setTextVal(e.target.value.slice(0, 10000))}
                  />
                  <button
                    className="btn btn-primary btn-lg btn-shiny"
                    disabled={!canStart}
                    style={{ alignSelf: 'flex-start', opacity: canStart ? 1 : 0.5, cursor: canStart ? 'pointer' : 'not-allowed' }}
                    onClick={start}
                  >
                    Analyze text →
                  </button>
                  {error && <p style={{ color: 'var(--ds-danger)', marginTop: 12, fontSize: 13 }}>{error}</p>}
                </div>
                <div className="options-row">
                  <label className="opt"><input type="checkbox" checked={cache} onChange={e => setCache(e.target.checked)}/> Cache result</label>
                  <div className="grow"/>
                  <select value={lang} onChange={e => setLang(e.target.value)}>
                    <option value="en">English</option>
                    <option value="hi">Hindi</option>
                  </select>
                </div>
              </>
            )}

            {stage === 'processing' && (
              <div className="processing-wrap">
                <div>
                  {mode === 'text' ? (
                    <TextProcessingViz />
                  ) : mode === 'audio' ? (
                    <AudioProcessingViz />
                  ) : (
                    <div className="stack-scene mini" style={{ height: 380 }}>
                      <LayerStack src={previewUrl || SAMPLE_SRC} density={6} />
                    </div>
                  )}
                </div>
                <div>
                  <div className="p-stages-head">
                    <span className="eyebrow">Pipeline</span>
                    <span className="mono" style={{ fontSize: 11, color: 'var(--ds-muted)' }}>{Math.round(progress)}% · {elapsed.toFixed(1)}s</span>
                  </div>
                  <div className="p-stages-bar"><i style={{ width: `${progress}%` }}/></div>
                  <ol className="stage-list">
                    {MODE_STAGES[mode].map((s, i) => {
                      const isLast = i === MODE_STAGES[mode].length - 1;
                      const isCurrent = i === activeStage;
                      const isDone = i < activeStage;
                      const isWaiting = !isDone && !isCurrent;
                      // Show elapsed timer on the active final stage
                      const statusText = isDone ? '✓'
                        : isCurrent && isLast && elapsed > 4
                          ? `${elapsed.toFixed(0)}s`
                          : isCurrent ? '···'
                          : '—';
                      return (
                        <li key={s} className={`${isDone ? 'done' : isCurrent ? 'active' : ''} ${isCurrent && isLast && elapsed > 3 ? 'stage-pulse' : ''}`}>
                          <span className="stage-dot"/>
                          <span className="stage-label">{s}</span>
                          <span className="mono stage-status">{statusText}</span>
                        </li>
                      );
                    })}
                  </ol>
                  {activeStage === MODE_STAGES[mode].length - 1 && elapsed > 6 && (
                    <p style={{ color: 'var(--ds-brand-2)', fontSize: 11, marginTop: 10, fontFamily: 'var(--ff-mono)', opacity: 0.8, animation: 'fadeInUp 400ms ease' }}>
                      {progress >= 95
                        ? '● Generating LLM summary — Gemini → Groq fallback chain'
                        : '● Models are scoring — this can take 10-25s on first run'}
                    </p>
                  )}
                  <p style={{ color: 'var(--ds-muted)', fontSize: 12, marginTop: 20, fontFamily: 'var(--ff-mono)' }}>
                    job · {jobId.current} · cache · {cache ? 'on' : 'off'} · lang · {lang}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="recent-rail">
          <h3>Recent analyses</h3>
          <div className="recent-grid">
            {(recent.length > 0 ? recent : DEFAULT_RECENT).map((r, i) => {
              const score = typeof r.authenticity_score === 'number' ? Math.round(r.authenticity_score) : null;
              const color = score == null ? 'warn' : score >= 65 ? 'safe' : score >= 40 ? 'warn' : 'danger';
              const verdictLabel = r.verdict
                ? r.verdict.toString().slice(0, 4).toUpperCase()
                : (color === 'safe' ? 'REAL' : color === 'warn' ? 'SUSP' : 'FAKE');
              const title = r.title || `${r.media_type || 'analysis'} · ${r.id}`;
              const when = r.created_at ? formatDateTimeIST(r.created_at) : (r.d || '');
              return (
                <a
                  className="recent-card"
                  key={r.id || i}
                  onClick={() => r.id && navigate(`/results/${r.id}`)}
                  style={{ cursor: r.id ? 'pointer' : 'default' }}
                >
                  <div className="recent-thumb" style={{
                    backgroundImage: (r.src || r.thumbnail_url || r.media_path)
                      ? `url("${r.src || resolveMediaUrl(r.thumbnail_url || r.media_path)}")`
                      : 'linear-gradient(135deg, rgba(108,125,255,0.15), rgba(61,219,179,0.08))',
                  }}>
                    <span className={`verdict-dot h-verdict ${color}`} style={{ position: 'absolute', top: 8, right: 8, padding: '2px 7px', fontSize: 9 }}>{verdictLabel}</span>
                  </div>
                  <div className="recent-title">{title}</div>
                  <div className="recent-meta">
                    <span>id · {String(r.id || '').slice(0, 6)}</span>
                    <span>{when}</span>
                  </div>
                </a>
              );
            })}
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}

function TextProcessingViz() {
  const [idx, setIdx] = useState(0);
  const lines = [
    { t: 'BREAKING: sources allegedly confirm' },
    { t: 'shocking truth experts refuse to believe' },
    { t: 'cross-reference · Reuters · matched' },
    { t: 'sensationalism score 0.74 · truth -0.41' },
  ];
  useEffect(() => {
    const id = setInterval(() => setIdx(i => (i + 1) % lines.length), 900);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div style={{
      padding: 24, background: 'rgba(0,0,0,0.4)', border: '1px solid var(--ds-border)',
      borderRadius: 14, fontFamily: 'var(--ff-mono)', fontSize: 13, color: 'var(--ds-ink-2)',
      minHeight: 380, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 14,
    }}>
      {lines.map((line, i) => {
        const active = i === idx;
        return (
          <div key={i} style={{
            opacity: i <= idx ? 1 : 0.25,
            transition: 'opacity 400ms, transform 400ms',
            transform: active ? 'translateX(6px)' : 'translateX(0)',
            color: active ? 'var(--ds-ink)' : 'var(--ds-ink-2)',
          }}>
            <span style={{ color: 'var(--ds-muted)', marginRight: 10 }}>&gt;</span>{line.t}
            {active && <span style={{ marginLeft: 10, color: 'var(--ds-brand-2)' }}>◉</span>}
          </div>
        );
      })}
    </div>
  );
}

function AudioProcessingViz() {
  const [bars, setBars] = useState(Array(32).fill(20));
  const [stats, setStats] = useState({ freq: 120.0, amp: 0.4 });

  useEffect(() => {
    const id = setInterval(() => {
      setBars(prev => prev.map(() => 5 + Math.random() * 95));
      setStats({
        freq: 120 + Math.random() * 80,
        amp: 0.4 + Math.random() * 0.4
      });
    }, 120);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{
      padding: 24, background: 'rgba(0,0,0,0.4)', border: '1px solid var(--ds-border)',
      borderRadius: 14, minHeight: 380, display: 'flex', flexDirection: 'column',
      justifyContent: 'center', alignItems: 'center', gap: 40, overflow: 'hidden', position: 'relative'
    }}>
      <div style={{
        position: 'absolute', width: '250px', height: '250px',
        background: 'var(--ds-brand-1)', filter: 'blur(120px)', opacity: 0.15, borderRadius: '50%'
      }}/>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, zIndex: 1, height: 100 }}>
        {bars.map((h, i) => {
          const isBrand1 = i % 2 === 0;
          return (
            <div key={i} style={{
              width: 6, height: `${h}%`, 
              backgroundColor: isBrand1 ? 'var(--ds-brand-1)' : 'var(--ds-brand-2)',
              borderRadius: 3, transition: 'height 120ms ease-out',
              boxShadow: `0 0 10px ${isBrand1 ? 'rgba(127,143,255,0.4)' : 'rgba(61,219,179,0.4)'}`,
              opacity: 0.6 + (h/250)
            }}/>
          );
        })}
      </div>
      
      <div style={{ zIndex: 1, fontFamily: 'var(--ff-mono)', fontSize: 12, display: 'flex', gap: 32, color: 'var(--ds-muted)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <span>SPECTRUM</span>
          <span style={{ color: 'var(--ds-ink)' }}>{stats.freq.toFixed(1)} Hz</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <span>AMPLITUDE</span>
          <span style={{ color: 'var(--ds-ink)' }}>{stats.amp.toFixed(2)}</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <span>NOISE FLOOR</span>
          <span style={{ color: 'var(--ds-ink)' }}>-84 dB</span>
        </div>
      </div>
    </div>
  );
}

const DEFAULT_RECENT = [
  { src: 'https://images.unsplash.com/photo-1488554378835-f7acf46e6c98?w=300&q=80&auto=format', title: 'Staged portrait', d: '2m ago',  authenticity_score: 18, verdict: 'FAKE' },
  { src: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&q=80&auto=format', title: 'Press photo',    d: '14m ago', authenticity_score: 88, verdict: 'REAL' },
  { src: 'https://images.unsplash.com/photo-1496128858413-b36217c2ce36?w=300&q=80&auto=format', title: 'Social post',    d: '1h ago',  authenticity_score: 52, verdict: 'SUSP' },
  { src: 'https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=300&q=80&auto=format', title: 'Pipeline test',  d: '3h ago',  authenticity_score: 12, verdict: 'FAKE' },
];
