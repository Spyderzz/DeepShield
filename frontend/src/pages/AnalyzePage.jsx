import { useState } from 'react';
import UploadZone from '../components/upload/UploadZone.jsx';
import VerdictCard from '../components/results/VerdictCard.jsx';
import ScoreMeter from '../components/results/ScoreMeter.jsx';
import HeatmapOverlay from '../components/results/HeatmapOverlay.jsx';
import IndicatorCards from '../components/results/IndicatorCards.jsx';
import ProcessingSummary from '../components/results/ProcessingSummary.jsx';
import FrameTimeline from '../components/results/FrameTimeline.jsx';
import ResponsibleAIBanner from '../components/common/ResponsibleAIBanner.jsx';
import LoadingSpinner from '../components/common/LoadingSpinner.jsx';
import { analyzeImage, analyzeVideo } from '../services/analyzeApi.js';

const MODES = {
  image: { label: 'Image', maxMB: 20, spinner: 'Running ViT + Grad-CAM + artifact scan…', cta: 'Analyze image', analyze: analyzeImage },
  video: { label: 'Video', maxMB: 100, spinner: 'Sampling frames + classifying…', cta: 'Analyze video', analyze: analyzeVideo },
};

export default function AnalyzePage() {
  const [mode, setMode] = useState('image');
  const [file, setFile] = useState(null);
  const [originalUrl, setOriginalUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const cfg = MODES[mode];

  const onFileAccepted = (f) => {
    setFile(f);
    setResult(null);
    setError(null);
    setOriginalUrl(URL.createObjectURL(f));
  };

  const submit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await cfg.analyze(file);
      setResult(data);
    } catch (err) {
      setError(err.userMessage || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setOriginalUrl(null);
  };

  const switchMode = (m) => {
    if (m === mode) return;
    setMode(m);
    reset();
  };

  const tabBtn = (m) => ({
    padding: 'var(--space-2) var(--space-4)',
    background: mode === m ? 'var(--color-primary-500)' : 'var(--color-surface)',
    color: mode === m ? 'white' : 'var(--color-text-primary)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    cursor: 'pointer',
    fontWeight: 'var(--font-weight-medium)',
  });

  return (
    <section style={{ display: 'grid', gap: 'var(--space-6)' }}>
      <div>
        <h2 style={{ marginBottom: 'var(--space-2)' }}>Media Analysis</h2>
        <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
          Upload an image or video to detect deepfake / manipulation signals with explainable AI.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        <button style={tabBtn('image')} onClick={() => switchMode('image')}>Image</button>
        <button style={tabBtn('video')} onClick={() => switchMode('video')}>Video</button>
      </div>

      {!result && (
        <>
          <UploadZone mediaType={mode} maxSizeMB={cfg.maxMB} onFileAccepted={onFileAccepted} disabled={loading} />

          <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
            <button
              onClick={submit}
              disabled={!file || loading}
              style={{
                padding: 'var(--space-3) var(--space-6)',
                background: file && !loading ? 'var(--color-primary-500)' : 'var(--color-border)',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: file && !loading ? 'pointer' : 'not-allowed',
                fontWeight: 'var(--font-weight-semibold)',
                boxShadow: file && !loading ? 'var(--shadow-md)' : 'none',
              }}
            >
              {loading ? 'Analyzing…' : cfg.cta}
            </button>
            {loading && <LoadingSpinner label={cfg.spinner} />}
          </div>

          {error && (
            <div style={{ color: 'var(--color-danger)', background: '#FFEBEE', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
              {error}
            </div>
          )}
        </>
      )}

      {result && (
        <div style={{ display: 'grid', gap: 'var(--space-6)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: 'var(--space-6)', alignItems: 'start' }}>
            <VerdictCard verdict={result.verdict} mediaType={result.media_type} timestamp={result.timestamp} />
            <div style={{ display: 'flex', justifyContent: 'center', background: 'var(--color-surface)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
              <ScoreMeter score={result.verdict.authenticity_score} />
            </div>
          </div>

          {result.media_type === 'image' && (
            <>
              <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                <h3 style={{ marginTop: 0 }}>Explainability</h3>
                <HeatmapOverlay originalUrl={originalUrl} heatmapBase64={result.explainability.heatmap_base64} />
              </div>

              <div>
                <h3>Artifact indicators</h3>
                <IndicatorCards indicators={result.explainability.artifact_indicators} />
              </div>
            </>
          )}

          {result.media_type === 'video' && (
            <>
              {result.explainability.insufficient_faces && (
                <div style={{ background: '#FFF8E1', border: '1px solid #FFE082', color: '#6D4C00', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)' }}>
                  <b>Insufficient face content.</b> The deepfake model is trained on face-centric content.
                  Only {result.explainability.num_face_frames} / {result.explainability.num_frames_sampled} sampled frames contained a detectable face,
                  so no deepfake verdict is issued. Try a clip where faces are visible.
                </div>
              )}
              <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                <h3 style={{ marginTop: 0 }}>Frame-level timeline</h3>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-4)' }}>
                  {result.explainability.num_face_frames} / {result.explainability.num_frames_sampled} frames with faces ·
                  {' '}{result.explainability.num_suspicious_frames} flagged suspicious ·
                  {' '}mean {(result.explainability.mean_suspicious_prob * 100).toFixed(1)}% ·
                  {' '}max {(result.explainability.max_suspicious_prob * 100).toFixed(1)}%
                </div>
                <FrameTimeline frames={result.explainability.frames} />
              </div>

              {originalUrl && (
                <div style={{ background: 'var(--color-surface)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)', textAlign: 'center' }}>
                  <video src={originalUrl} controls style={{ maxHeight: 360, maxWidth: '100%', borderRadius: 'var(--radius-sm, 4px)' }} />
                </div>
              )}
            </>
          )}

          <ProcessingSummary summary={result.processing_summary} />
          <ResponsibleAIBanner text={result.responsible_ai_notice} />

          <div>
            <button
              onClick={reset}
              style={{
                padding: 'var(--space-3) var(--space-6)',
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                fontWeight: 'var(--font-weight-medium)',
              }}
            >
              Analyze another {result.media_type}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
