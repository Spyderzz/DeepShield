import { useState } from 'react';
import { generateReport, downloadReportBlob } from '../../services/reportApi.js';

export default function ReportDownload({ recordId, mediaType }) {
  const [status, setStatus] = useState('idle'); // idle | generating | ready | downloading | error
  const [error, setError] = useState(null);

  if (!recordId) return null;

  const handleClick = async () => {
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
      setError(err.userMessage || err.message || 'Report generation failed');
      setStatus('error');
    }
  };

  const busy = status === 'generating' || status === 'downloading';
  const label = {
    idle: `⬇ Download PDF Report`,
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
      <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
        PDF contains verdict, indicators, sources, and pipeline summary for this {mediaType}. Reports expire after 1 hour.
      </div>
    </div>
  );
}
