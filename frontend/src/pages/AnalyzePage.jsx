import { useState } from 'react';
import UploadZone from '../components/upload/UploadZone.jsx';
import TextInput from '../components/upload/TextInput.jsx';
import VerdictCard from '../components/results/VerdictCard.jsx';
import ScoreMeter from '../components/results/ScoreMeter.jsx';
import HeatmapOverlay from '../components/results/HeatmapOverlay.jsx';
import IndicatorCards from '../components/results/IndicatorCards.jsx';
import ProcessingSummary from '../components/results/ProcessingSummary.jsx';
import FrameTimeline from '../components/results/FrameTimeline.jsx';
import TextHighlighter from '../components/results/TextHighlighter.jsx';
import SensationalismMeter from '../components/results/SensationalismMeter.jsx';
import SourcePanel from '../components/results/SourcePanel.jsx';
import ContradictionPanel from '../components/results/ContradictionPanel.jsx';
import ScreenshotOverlay from '../components/results/ScreenshotOverlay.jsx';
import ResponsibleAIBanner from '../components/common/ResponsibleAIBanner.jsx';
import ReportDownload from '../components/results/ReportDownload.jsx';
import LoadingSpinner from '../components/common/LoadingSpinner.jsx';
import PipelineVisualizer from '../components/common/PipelineVisualizer.jsx';
import LLMExplainCard from '../components/results/LLMExplainCard.jsx';
import EXIFCard from '../components/results/EXIFCard.jsx';
import LanguageBadge from '../components/results/LanguageBadge.jsx';
import DetailedBreakdownCards from '../components/results/DetailedBreakdownCards.jsx';
import { analyzeImage, analyzeVideo, analyzeText, analyzeScreenshot } from '../services/analyzeApi.js';
import { useToast } from '../contexts/ToastContext.jsx';

const MODES = {
  image:      { label: 'Image',      maxMB: 20,  spinner: 'Running ViT + Grad-CAM + artifact scan…', cta: 'Analyze image', analyze: analyzeImage, type: 'file' },
  video:      { label: 'Video',      maxMB: 100, spinner: 'Sampling frames + classifying…', cta: 'Analyze video', analyze: analyzeVideo, type: 'file' },
  text:       { label: 'Text',       maxMB: 0,   spinner: 'Running BERT classifier + sensationalism + manipulation scan…', cta: 'Analyze text', analyze: analyzeText, type: 'text' },
  screenshot: { label: 'Screenshot', maxMB: 20,  spinner: 'OCR + text classifier + layout scan…', cta: 'Analyze screenshot', analyze: analyzeScreenshot, type: 'file' },
};

export default function AnalyzePage() {
  const [mode, setMode] = useState('image');
  const [file, setFile] = useState(null);
  const [originalUrl, setOriginalUrl] = useState(null);
  const [textContent, setTextContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const toast = useToast();

  const cfg = MODES[mode];

  const onFileAccepted = (f) => {
    setFile(f);
    setResult(null);
    setError(null);
    setOriginalUrl(URL.createObjectURL(f));
  };

  const submitFile = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await cfg.analyze(file);
      setResult(data);
      toast.success(`Analysis complete: ${data.verdict?.label || 'done'}`);
    } catch (err) {
      const msg = err.userMessage || err.message || 'Analysis failed';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const submitText = async (text) => {
    setTextContent(text);
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeText(text);
      setResult(data);
      toast.success(`Analysis complete: ${data.verdict?.label || 'done'}`);
    } catch (err) {
      const msg = err.userMessage || err.message || 'Analysis failed';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setOriginalUrl(null);
    setTextContent('');
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
    transition: 'all 0.2s',
  });

  return (
    <section style={{ display: 'grid', gap: 'var(--space-6)' }}>
      <div>
        <h2 style={{ marginBottom: 'var(--space-2)' }}>Media Analysis</h2>
        <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
          Upload an image, video, or paste text to detect deepfake / manipulation signals with explainable AI.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        {Object.entries(MODES).map(([key, val]) => (
          <button key={key} style={tabBtn(key)} onClick={() => switchMode(key)}>{val.label}</button>
        ))}
      </div>

      {!result && (
        <>
          {cfg.type === 'file' && (
            <>
              <UploadZone mediaType={mode} maxSizeMB={cfg.maxMB} onFileAccepted={onFileAccepted} disabled={loading} />
              <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
                <button
                  id="file-analyze-btn"
                  onClick={submitFile}
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
              {loading && <PipelineVisualizer mediaType={mode} running />}
            </>
          )}

          {cfg.type === 'text' && (
            <>
              <TextInput onTextSubmit={submitText} disabled={loading} />
              {loading && <LoadingSpinner label={cfg.spinner} />}
              {loading && <PipelineVisualizer mediaType={mode} running />}
            </>
          )}

          {error && (
            <div style={{ color: 'var(--color-danger)', background: '#FFEBEE', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
              {error}
            </div>
          )}
        </>
      )}

      {result && (
        <div style={{ display: 'grid', gap: 'var(--space-6)' }}>
          {/* Verdict + Score */}
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: 'var(--space-6)', alignItems: 'start' }}>
            <VerdictCard verdict={result.verdict} mediaType={result.media_type} timestamp={result.timestamp} />
            <div style={{ display: 'flex', justifyContent: 'center', background: 'var(--color-surface)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
              <ScoreMeter score={result.verdict.authenticity_score} />
            </div>
          </div>

          {/* ── Phase 12: LLM Explain Card — first card for ALL media types ─��� */}
          {(result.llm_summary || result.explainability?.llm_summary) && (
            <LLMExplainCard llmSummary={result.llm_summary || result.explainability?.llm_summary} />
          )}

          {/* ── Image results ── */}
          {result.media_type === 'image' && (
            <>
              {result.explainability?.exif && (
                <EXIFCard exif={result.explainability.exif} />
              )}
              <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                <h3 style={{ marginTop: 0 }}>Explainability</h3>
                <HeatmapOverlay
                  originalUrl={originalUrl}
                  heatmapBase64={result.explainability.heatmap_base64}
                  elaBase64={result.explainability.ela_base64}
                  boxesBase64={result.explainability.boxes_base64}
                />
              </div>
              <div>
                <h3>Artifact indicators</h3>
                <IndicatorCards indicators={result.explainability.artifact_indicators} />
              </div>
              {result.explainability?.vlm_breakdown && (
                <DetailedBreakdownCards breakdown={result.explainability.vlm_breakdown} />
              )}
            </>
          )}

          {/* ── Video results ── */}
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

          {/* ── Text results ── */}
          {result.media_type === 'text' && (
            <>
              {/* Phase 13: Language + truth-override badges */}
              <LanguageBadge
                language={result.explainability.detected_language}
                truthOverride={result.explainability.truth_override}
              />

              {/* Sensationalism */}
              <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                <h3 style={{ marginTop: 0 }}>Sensationalism Analysis</h3>
                <SensationalismMeter sensationalism={result.explainability.sensationalism} />
              </div>

              {/* Manipulation indicators highlighted in text */}
              <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                <h3 style={{ marginTop: 0 }}>Manipulation Pattern Analysis</h3>
                <TextHighlighter text={textContent} indicators={result.explainability.manipulation_indicators} />
              </div>

              {/* Keywords */}
              {result.explainability.keywords?.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', alignItems: 'center' }}>
                  <span style={{ fontWeight: 'var(--font-weight-medium)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                    Extracted keywords:
                  </span>
                  {result.explainability.keywords.map(kw => (
                    <span key={kw} style={{
                      padding: '3px 10px',
                      background: 'var(--color-primary-50, rgba(99,102,241,0.08))',
                      color: 'var(--color-primary-500)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: 'var(--font-size-sm)',
                      fontWeight: 'var(--font-weight-medium)',
                    }}>
                      {kw}
                    </span>
                  ))}
                </div>
              )}

              {/* Contradicting fact-checks */}
              {result.contradicting_evidence?.length > 0 && (
                <ContradictionPanel items={result.contradicting_evidence} />
              )}

              {/* Trusted sources */}
              {result.trusted_sources?.length > 0 && (
                <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                  <SourcePanel sources={result.trusted_sources} />
                </div>
              )}
            </>
          )}

          {/* ── Screenshot results ── */}
          {result.media_type === 'screenshot' && (
            <>
              {/* Phase 13: Language + truth-override badges */}
              <LanguageBadge
                language={result.explainability.detected_language}
                truthOverride={result.explainability.truth_override}
              />

              <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                <h3 style={{ marginTop: 0 }}>Overlay — OCR + suspicious phrases</h3>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-3)' }}>
                  {result.explainability.ocr_boxes?.length || 0} text regions detected ·
                  {' '}{result.explainability.suspicious_phrases?.length || 0} flagged phrases ·
                  {' '}{result.explainability.layout_anomalies?.length || 0} layout anomalies
                </div>
                <ScreenshotOverlay
                  originalUrl={originalUrl}
                  ocrBoxes={result.explainability.ocr_boxes}
                  suspiciousPhrases={result.explainability.suspicious_phrases}
                />
              </div>

              {result.explainability.extracted_text && (
                <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                  <h3 style={{ marginTop: 0 }}>Extracted text</h3>
                  <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', whiteSpace: 'pre-wrap', marginBottom: 'var(--space-4)' }}>
                    {result.explainability.extracted_text}
                  </div>
                  <h4>Sensationalism</h4>
                  <SensationalismMeter sensationalism={result.explainability.sensationalism} />
                </div>
              )}

              {result.explainability.layout_anomalies?.length > 0 && (
                <div>
                  <h3>Layout anomalies</h3>
                  <IndicatorCards indicators={result.explainability.layout_anomalies.map(la => ({
                    type: la.type, severity: la.severity, description: la.description, confidence: la.confidence,
                  }))} />
                </div>
              )}

              {result.contradicting_evidence?.length > 0 && (
                <ContradictionPanel items={result.contradicting_evidence} />
              )}

              {result.trusted_sources?.length > 0 && (
                <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
                  <SourcePanel sources={result.trusted_sources} />
                </div>
              )}
            </>
          )}

          <PipelineVisualizer
            mediaType={result.media_type}
            running={false}
            completedStages={result.processing_summary?.stages_completed}
          />
          <ProcessingSummary summary={result.processing_summary} />
          <ReportDownload recordId={result.record_id} mediaType={result.media_type} />
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
