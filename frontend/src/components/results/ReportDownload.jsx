import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.jsx';
import { useToast } from '../../contexts/ToastContext.jsx';
import { generateReport, downloadReportBlob } from '../../services/reportApi.js';

export default function ReportDownload({ recordId, mediaType }) {
  const [status, setStatus] = useState('idle'); // idle | generating | ready | downloading | error
  const [error, setError] = useState(null);
  const { isAuthed } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  if (!recordId) return null;

  const handleClick = async () => {
    if (!isAuthed) {
      // Phase 15.1 — gate PDF download on auth.
      toast.warning('Sign in to download reports');
      navigate('/login');
      return;
    }
    setError(null);
    try {
      setStatus('generating');
      await generateReport(recordId);
      setStatus('downloading');
      const blob = await downloadReportBlob(recordId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `deepshield_report_${recordId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setStatus('ready');
    } catch (err) {
      // Phase 15.2 — surface rate-limit responses nicely
      const statusCode = err?.response?.status;
      if (statusCode === 429) {
        const retry = err?.response?.headers?.['retry-after'];
        const minutes = retry ? Math.max(1, Math.ceil(Number(retry) / 60)) : null;
        const msg = minutes
          ? `Rate limit reached — try again in ${minutes} minute${minutes === 1 ? '' : 's'}.`
          : 'Rate limit reached — please try again shortly.';
        setError(msg);
      } else {
        setError(err.userMessage || err.message || 'Report generation failed');
      }
      setStatus('error');
    }
  };

  const busy = status === 'generating' || status === 'downloading';
  const label = {
    idle: isAuthed ? `⬇ Download PDF Report` : '🔒 Sign in to download PDF',
    generating: 'Generating PDF…',
    downloading: 'Downloading…',
    ready: '✓ Downloaded — click to regenerate',
    error: 'Retry download',
  }[status];

  return (
    <div style={{ display: 'grid', gap: 'var(--space-2)' }}>
      <button
        onClick={handleClick}
        disabled={busy}
        style={{
          padding: 'var(--space-3) var(--space-6)',
          background: busy ? 'var(--color-border)' : 'var(--color-primary-500)',
          color: 'white',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          cursor: busy ? 'wait' : 'pointer',
          fontWeight: 'var(--font-weight-semibold)',
          boxShadow: busy ? 'none' : 'var(--shadow-md)',
          width: 'fit-content',
        }}
      >
        {label}
      </button>
      {error && (
        <div style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)' }}>
          {error}
        </div>
      )}
      {!isAuthed && (
        <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
          <Link to="/login">Sign in</Link> to generate and download PDF reports for your analyses.
        </div>
      )}
      <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
        PDF contains verdict, indicators, sources, and pipeline summary for this {mediaType}. Reports expire after 1 hour.
      </div>
    </div>
  );
}
