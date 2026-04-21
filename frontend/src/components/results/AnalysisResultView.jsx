import VerdictCard from './VerdictCard.jsx';
import ScoreMeter from './ScoreMeter.jsx';
import HeatmapOverlay from './HeatmapOverlay.jsx';
import IndicatorCards from './IndicatorCards.jsx';
import ProcessingSummary from './ProcessingSummary.jsx';
import FrameTimeline from './FrameTimeline.jsx';
import TextHighlighter from './TextHighlighter.jsx';
import SensationalismMeter from './SensationalismMeter.jsx';
import SourcePanel from './SourcePanel.jsx';
import ContradictionPanel from './ContradictionPanel.jsx';
import ScreenshotOverlay from './ScreenshotOverlay.jsx';
import ReportDownload from './ReportDownload.jsx';
import LLMExplainCard from './LLMExplainCard.jsx';
import EXIFCard from './EXIFCard.jsx';
import LanguageBadge from './LanguageBadge.jsx';
import DetailedBreakdownCards from './DetailedBreakdownCards.jsx';
import ResponsibleAIBanner from '../common/ResponsibleAIBanner.jsx';
import PipelineVisualizer from '../common/PipelineVisualizer.jsx';

export default function AnalysisResultView({ analysis, originalUrl, textContent, onAnalyzeAnother }) {
  const r = analysis;
  const ex = r.explainability || {};

  return (
    <div style={{ display: 'grid', gap: 'var(--space-6)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)', gap: 'var(--space-6)', alignItems: 'start' }}>
        <VerdictCard verdict={r.verdict} mediaType={r.media_type} timestamp={r.timestamp} />
        <div style={{ display: 'flex', justifyContent: 'center', background: 'var(--color-surface)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
          <ScoreMeter score={r.verdict.authenticity_score} />
        </div>
      </div>

      {(r.llm_summary || ex.llm_summary) && (
        <LLMExplainCard llmSummary={r.llm_summary || ex.llm_summary} />
      )}

      {r.media_type === 'image' && (
        <>
          {ex.exif && <EXIFCard exif={ex.exif} />}
          <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
            <h3 style={{ marginTop: 0 }}>Explainability</h3>
            {originalUrl ? (
              <HeatmapOverlay
                originalUrl={originalUrl}
                heatmapBase64={ex.heatmap_base64}
                elaBase64={ex.ela_base64}
                boxesBase64={ex.boxes_base64}
              />
            ) : (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', margin: 0 }}>
                Heatmap overlay requires the original image file — re-analyze to view.
              </p>
            )}
          </div>
          <div>
            <h3>Artifact indicators</h3>
            <IndicatorCards indicators={ex.artifact_indicators} />
          </div>
          {ex.vlm_breakdown && <DetailedBreakdownCards breakdown={ex.vlm_breakdown} />}
        </>
      )}

      {r.media_type === 'video' && (
        <>
          {ex.insufficient_faces && (
            <div style={{ background: '#FFF8E1', border: '1px solid #FFE082', color: '#6D4C00', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)' }}>
              <b>Insufficient face content.</b> Only {ex.num_face_frames} / {ex.num_frames_sampled} sampled frames contained a detectable face.
            </div>
          )}
          <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
            <h3 style={{ marginTop: 0 }}>Frame-level timeline</h3>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-4)' }}>
              {ex.num_face_frames} / {ex.num_frames_sampled} frames with faces ·
              {' '}{ex.num_suspicious_frames} flagged suspicious ·
              {' '}mean {(ex.mean_suspicious_prob * 100).toFixed(1)}% ·
              {' '}max {(ex.max_suspicious_prob * 100).toFixed(1)}%
            </div>
            <FrameTimeline frames={ex.frames} />
          </div>
          {originalUrl && (
            <div style={{ background: 'var(--color-surface)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)', textAlign: 'center' }}>
              <video src={originalUrl} controls style={{ maxHeight: 360, maxWidth: '100%', borderRadius: 'var(--radius-sm, 4px)' }} />
            </div>
          )}
        </>
      )}

      {r.media_type === 'text' && (
        <>
          <LanguageBadge language={ex.detected_language} truthOverride={ex.truth_override} />
          <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
            <h3 style={{ marginTop: 0 }}>Sensationalism Analysis</h3>
            <SensationalismMeter sensationalism={ex.sensationalism} />
          </div>
          <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
            <h3 style={{ marginTop: 0 }}>Manipulation Pattern Analysis</h3>
            <TextHighlighter text={textContent || ''} indicators={ex.manipulation_indicators} />
          </div>
          {ex.keywords?.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', alignItems: 'center' }}>
              <span style={{ fontWeight: 'var(--font-weight-medium)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                Extracted keywords:
              </span>
              {ex.keywords.map(kw => (
                <span key={kw} style={{
                  padding: '3px 10px',
                  background: 'var(--color-primary-50, rgba(99,102,241,0.08))',
                  color: 'var(--color-primary-500)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 'var(--font-weight-medium)',
                }}>{kw}</span>
              ))}
            </div>
          )}
          {r.contradicting_evidence?.length > 0 && <ContradictionPanel items={r.contradicting_evidence} />}
          {r.trusted_sources?.length > 0 && (
            <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
              <SourcePanel sources={r.trusted_sources} />
            </div>
          )}
        </>
      )}

      {r.media_type === 'screenshot' && (
        <>
          <LanguageBadge language={ex.detected_language} truthOverride={ex.truth_override} />
          <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
            <h3 style={{ marginTop: 0 }}>Overlay — OCR + suspicious phrases</h3>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-3)' }}>
              {ex.ocr_boxes?.length || 0} text regions · {ex.suspicious_phrases?.length || 0} flagged phrases · {ex.layout_anomalies?.length || 0} layout anomalies
            </div>
            {originalUrl ? (
              <ScreenshotOverlay originalUrl={originalUrl} ocrBoxes={ex.ocr_boxes} suspiciousPhrases={ex.suspicious_phrases} />
            ) : (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', margin: 0 }}>
                Overlay requires the original file — re-analyze to view.
              </p>
            )}
          </div>
          {ex.extracted_text && (
            <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
              <h3 style={{ marginTop: 0 }}>Extracted text</h3>
              <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', whiteSpace: 'pre-wrap', marginBottom: 'var(--space-4)' }}>
                {ex.extracted_text}
              </div>
              <h4>Sensationalism</h4>
              <SensationalismMeter sensationalism={ex.sensationalism} />
            </div>
          )}
          {ex.layout_anomalies?.length > 0 && (
            <div>
              <h3>Layout anomalies</h3>
              <IndicatorCards indicators={ex.layout_anomalies.map(la => ({
                type: la.type, severity: la.severity, description: la.description, confidence: la.confidence,
              }))} />
            </div>
          )}
          {r.contradicting_evidence?.length > 0 && <ContradictionPanel items={r.contradicting_evidence} />}
          {r.trusted_sources?.length > 0 && (
            <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
              <SourcePanel sources={r.trusted_sources} />
            </div>
          )}
        </>
      )}

      <PipelineVisualizer
        mediaType={r.media_type}
        running={false}
        completedStages={r.processing_summary?.stages_completed}
      />
      <ProcessingSummary summary={r.processing_summary} />
      <ReportDownload recordId={r.record_id} mediaType={r.media_type} />
      <ResponsibleAIBanner text={r.responsible_ai_notice} />

      {onAnalyzeAnother && (
        <div>
          <button
            onClick={onAnalyzeAnother}
            style={{
              padding: 'var(--space-3) var(--space-6)',
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              fontWeight: 'var(--font-weight-medium)',
            }}
          >
            Analyze another {r.media_type}
          </button>
        </div>
      )}
    </div>
  );
}
