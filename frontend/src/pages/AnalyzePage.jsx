import { useState } from 'react';
import UploadZone from '../components/upload/UploadZone.jsx';
import TextInput from '../components/upload/TextInput.jsx';
import LoadingSpinner from '../components/common/LoadingSpinner.jsx';
import PipelineVisualizer from '../components/common/PipelineVisualizer.jsx';
import AnalysisResultView from '../components/results/AnalysisResultView.jsx';
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
        <AnalysisResultView
          analysis={result}
          originalUrl={originalUrl}
          textContent={textContent}
          onAnalyzeAnother={reset}
        />
      )}
    </section>
  );
}
