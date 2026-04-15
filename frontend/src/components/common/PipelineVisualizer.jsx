import { useEffect, useState, useRef } from 'react';

const STAGES = {
  image: [
    { key: 'validation',          label: 'Validating file' },
    { key: 'classification',      label: 'ViT deepfake classifier' },
    { key: 'artifact_scanning',   label: 'Artifact scan (FFT + JPEG + face + lighting)' },
    { key: 'heatmap_generation',  label: 'Grad-CAM heatmap' },
  ],
  video: [
    { key: 'validation',           label: 'Validating video' },
    { key: 'frame_extraction',     label: 'Sampling frames' },
    { key: 'frame_classification', label: 'Per-frame ViT + face detection' },
    { key: 'aggregation',          label: 'Timeline aggregation' },
  ],
  text: [
    { key: 'classification',            label: 'BERT fake-news classifier' },
    { key: 'sensationalism_analysis',   label: 'Sensationalism scoring' },
    { key: 'manipulation_detection',    label: 'Manipulation pattern scan' },
    { key: 'keyword_extraction',        label: 'Keyword extraction' },
    { key: 'news_lookup',               label: 'Trusted source lookup' },
  ],
  screenshot: [
    { key: 'validation',               label: 'Validating image' },
    { key: 'ocr',                      label: 'EasyOCR text extraction' },
    { key: 'classification',           label: 'BERT fake-news classifier' },
    { key: 'sensationalism_analysis',  label: 'Sensationalism scoring' },
    { key: 'manipulation_detection',   label: 'Manipulation pattern scan' },
    { key: 'phrase_overlay_mapping',   label: 'Phrase→bbox mapping' },
    { key: 'layout_anomaly_detection', label: 'Layout anomaly scan' },
    { key: 'keyword_extraction',       label: 'Keyword extraction' },
    { key: 'news_lookup',              label: 'Trusted source lookup' },
  ],
};

function Dot({ state }) {
  const color = state === 'done' ? '#43A047'
    : state === 'active' ? 'var(--color-primary-500)'
    : 'var(--color-border)';
  return (
    <div style={{
      width: 14, height: 14, borderRadius: '50%',
      background: state === 'active' ? 'transparent' : color,
      border: state === 'active' ? `2px solid ${color}` : 'none',
      flexShrink: 0,
      boxShadow: state === 'active' ? `0 0 0 4px rgba(99,102,241,0.2)` : 'none',
      animation: state === 'active' ? 'dspulse 1.1s ease-in-out infinite' : 'none',
    }} />
  );
}

/**
 * Animates a per-media pipeline while the analysis request is in flight.
 *   - `mediaType`: one of image|video|text|screenshot
 *   - `running`: true while request pending
 *   - `completedStages`: optional array from API response (final sync)
 */
export default function PipelineVisualizer({ mediaType = 'image', running = false, completedStages = null }) {
  const stages = STAGES[mediaType] || STAGES.image;
  const [activeIdx, setActiveIdx] = useState(0);
  const timerRef = useRef(null);

  useEffect(() => {
    clearInterval(timerRef.current);
    if (!running) return;
    setActiveIdx(0);
    // advance through stages at 700ms each, cap at last stage (stay there until done)
    timerRef.current = setInterval(() => {
      setActiveIdx(i => Math.min(i + 1, stages.length - 1));
    }, 700);
    return () => clearInterval(timerRef.current);
  }, [running, mediaType, stages.length]);

  // When API returns, snap all stages returned by the server to "done"
  const doneSet = completedStages && !running
    ? new Set(completedStages)
    : null;

  const stateFor = (stage, idx) => {
    if (doneSet) return doneSet.has(stage.key) ? 'done' : 'pending';
    if (!running) return 'pending';
    if (idx < activeIdx) return 'done';
    if (idx === activeIdx) return 'active';
    return 'pending';
  };

  return (
    <div style={{
      display: 'grid', gap: 'var(--space-2)',
      padding: 'var(--space-4)',
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
    }}>
      <div style={{ fontWeight: 'var(--font-weight-semibold)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-2)' }}>
        Processing Pipeline
      </div>
      {stages.map((s, i) => {
        const st = stateFor(s, i);
        return (
          <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <Dot state={st} />
            <span style={{
              fontSize: 'var(--font-size-sm)',
              color: st === 'pending' ? 'var(--color-text-secondary)' : 'var(--color-text-primary)',
              fontWeight: st === 'active' ? 'var(--font-weight-medium)' : 'normal',
            }}>
              {s.label}
            </span>
            {st === 'done' && <span style={{ color: '#43A047', fontSize: 'var(--font-size-xs)' }}>✓</span>}
          </div>
        );
      })}
      <style>{`@keyframes dspulse { 0%,100% { box-shadow: 0 0 0 4px rgba(99,102,241,0.2); } 50% { box-shadow: 0 0 0 7px rgba(99,102,241,0.05); } }`}</style>
    </div>
  );
}
