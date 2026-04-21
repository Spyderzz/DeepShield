import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.jsx';
import { useToast } from '../../contexts/ToastContext.jsx';
import { generateReport, downloadReportBlob } from '../../services/reportApi.js';

export default function StickyActionBar({ recordId, mediaType, onAnalyzeAnother }) {
  const [pdfBusy, setPdfBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const { isAuthed } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const handlePdf = async () => {
    if (!isAuthed) {
      toast.warning('Sign in to download reports');
      navigate('/login');
      return;
    }
    if (!recordId || pdfBusy) return;
    setPdfBusy(true);
    try {
      await generateReport(recordId);
      const blob = await downloadReportBlob(recordId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `deepshield_report_${recordId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success('Report downloaded');
    } catch (err) {
      const status = err?.response?.status;
      if (status === 429) {
        toast.error('Rate limit reached — try again shortly.');
      } else {
        toast.error(err.userMessage || 'Report generation failed');
      }
    } finally {
      setPdfBusy(false);
    }
  };

  const handleShare = async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success('Link copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Could not copy link');
    }
  };

  const handleAnalyzeAnother = () => {
    if (onAnalyzeAnother) {
      onAnalyzeAnother();
    } else {
      navigate('/analyze');
    }
  };

  const btn = (onClick, label, primary = false, disabled = false) => ({
    onClick,
    disabled,
    style: {
      padding: 'var(--space-2) var(--space-4)',
      background: primary ? 'var(--color-primary-500)' : 'rgba(255,255,255,0.15)',
      color: 'white',
      border: primary ? 'none' : '1px solid rgba(255,255,255,0.3)',
      borderRadius: 'var(--radius-md)',
      cursor: disabled ? 'wait' : 'pointer',
      fontWeight: 'var(--font-weight-semibold)',
      fontSize: 'var(--font-size-sm)',
      backdropFilter: 'blur(4px)',
      whiteSpace: 'nowrap',
      opacity: disabled ? 0.6 : 1,
    },
    children: label,
  });

  return (
    <div
      role="toolbar"
      aria-label="Result actions"
      style={{
        position: 'fixed',
        bottom: 'var(--space-6)',
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        gap: 'var(--space-2)',
        padding: 'var(--space-3) var(--space-4)',
        background: 'rgba(30, 30, 40, 0.85)',
        backdropFilter: 'blur(12px)',
        borderRadius: 'var(--radius-lg, 16px)',
        boxShadow: '0 4px 24px rgba(0,0,0,0.35)',
        border: '1px solid rgba(255,255,255,0.12)',
        zIndex: 100,
      }}
    >
      <button {...btn(handleAnalyzeAnother, `+ Analyze Another`)}>+ Analyze Another</button>
      {recordId && (
        <button {...btn(handlePdf, pdfBusy ? 'Generating…' : '⬇ Generate PDF', true, pdfBusy)}>
          {pdfBusy ? 'Generating…' : '⬇ Generate PDF'}
        </button>
      )}
      <button {...btn(handleShare, copied ? '✓ Copied' : '⎘ Share')}>
        {copied ? '✓ Copied' : '⎘ Share'}
      </button>
    </div>
  );
}
