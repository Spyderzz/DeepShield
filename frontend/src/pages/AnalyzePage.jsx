import { useState } from 'react';
import { motion } from 'framer-motion';
import UploadZone from '../components/upload/UploadZone.jsx';
import TextInput from '../components/upload/TextInput.jsx';
import ProcessingAnimation from '../components/common/ProcessingAnimation.jsx';
import LoadingSpinner from '../components/common/LoadingSpinner.jsx';
import PipelineVisualizer from '../components/common/PipelineVisualizer.jsx';
import AnalysisResultView from '../components/results/AnalysisResultView.jsx';
import { analyzeImage, analyzeVideo, analyzeText, analyzeScreenshot } from '../services/analyzeApi.js';
import { useToast } from '../contexts/ToastContext.jsx';

const MODES = {
  image:      { label: 'Image',      maxMB: 20,  spinner: 'Running ViT + Grad-CAM + artifact scan…', cta: 'Analyze image', analyze: analyzeImage, type: 'file' },
  video:      { label: 'Video',      maxMB: 100, spinner: 'Sampling frames + classifying…', cta: 'Analyze video', analyze: analyzeVideo, type: 'file' },
  text:       { label: 'Text',       maxMB: 0,   spinner: 'Running BERT + sensationalism scan…', cta: 'Analyze text', analyze: analyzeText, type: 'text' },
  screenshot: { label: 'Screenshot', maxMB: 20,  spinner: 'OCR + text + layout scan…', cta: 'Analyze screenshot', analyze: analyzeScreenshot, type: 'file' },
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

  return (
    <section style={{ display: 'grid', gap: 'var(--space-6)' }}>
      <div>
        <h2 style={{ marginBottom: 'var(--space-2)' }}>Media Analysis</h2>
        <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
          Upload an image, video, or paste text to detect deepfake and manipulation signals with explainable AI.
        </p>
      </div>

      {/* iOS-style segmented controller */}
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div
          style={{
            display: 'inline-flex',
            background: 'rgba(118, 118, 128, 0.12)',
            borderRadius: 'var(--radius-full)',
            padding: 3,
          }}
        >
          {Object.entries(MODES).map(([key, val]) => (
            <button
              key={key}
              onClick={() => switchMode(key)}
              style={{
                position: 'relative',
                padding: '8px 22px',
                border: 'none',
                borderRadius: 'var(--radius-full)',
                background: 'transparent',
                color: mode === key ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                fontWeight: mode === key ? 'var(--font-weight-semibold)' : 'var(--font-weight-normal)',
                fontSize: 'var(--font-size-sm)',
                cursor: 'pointer',
                transition: 'color 0.2s',
                zIndex: 1,
                userSelect: 'none',
              }}
            >
              {mode === key && (
                <motion.div
                  layoutId="seg-pill"
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'var(--color-surface)',
                    borderRadius: 'var(--radius-full)',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
                  }}
                  transition={{ type: 'spring', stiffness: 420, damping: 38 }}
                />
              )}
              <span style={{ position: 'relative', zIndex: 1 }}>{val.label}</span>
            </button>
          ))}
        </div>
      </div>

      {!result && (
        <div
          style={{
            background: `
              radial-gradient(at 25% 25%, rgba(30, 136, 229, 0.13) 0px, transparent 50%),
              radial-gradient(at 75% 75%, rgba(99, 102, 241, 0.10) 0px, transparent 50%),
              radial-gradient(at 65% 10%, rgba(16, 185, 129, 0.07) 0px, transparent 50%),
              var(--color-surface)
            `,
            borderRadius: 'var(--radius-xl)',
            padding: 'var(--space-8)',
            border: '1px solid var(--color-border)',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          {cfg.type === 'file' && !loading && (
            <>
              <UploadZone
                mediaType={mode}
                maxSizeMB={cfg.maxMB}
                onFileAccepted={onFileAccepted}
                disabled={false}
              />
              <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', marginTop: 'var(--space-5)' }}>
                <motion.button
                  id="file-analyze-btn"
                  onClick={submitFile}
                  disabled={!file}
                  whileHover={file ? { scale: 1.02 } : {}}
                  whileTap={file ? { scale: 0.97 } : {}}
                  style={{
                    padding: 'var(--space-3) var(--space-8)',
                    background: file
                      ? 'linear-gradient(135deg, var(--color-primary-500) 0%, var(--color-primary-600) 100%)'
                      : 'var(--color-border)',
                    color: 'white',
                    border: 'none',
                    borderRadius: 'var(--radius-full)',
                    cursor: file ? 'pointer' : 'not-allowed',
                    fontWeight: 'var(--font-weight-semibold)',
                    fontSize: 'var(--font-size-base)',
                    boxShadow: file ? '0 4px 14px rgba(30,136,229,0.30)' : 'none',
                    transition: 'background 0.2s, box-shadow 0.2s',
                  }}
                >
                  {cfg.cta}
                </motion.button>
              </div>
            </>
          )}

          {cfg.type === 'file' && loading && (
            <ProcessingAnimation imageUrl={originalUrl} mediaType={mode} label={cfg.spinner} />
          )}

          {cfg.type === 'text' && (
            <>
              <TextInput onTextSubmit={submitText} disabled={loading} />
              {loading && (
                <div style={{ marginTop: 'var(--space-4)' }}>
                  <LoadingSpinner label={cfg.spinner} />
                </div>
              )}
            </>
          )}

          {loading && (
            <div style={{ marginTop: 'var(--space-4)' }}>
              <PipelineVisualizer mediaType={mode} running />
            </div>
          )}

          {error && (
            <div style={{
              color: 'var(--color-danger)',
              background: '#FFEBEE',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-md)',
              marginTop: 'var(--space-4)',
            }}>
              {error}
            </div>
          )}
        </div>
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
