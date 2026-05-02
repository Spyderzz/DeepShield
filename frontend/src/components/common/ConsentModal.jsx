/**
 * ConsentModal.jsx — Phase 22.4
 * First-upload consent modal. Shown once per browser (localStorage flag).
 * Tells the user what happens to their file before the first analysis runs.
 */
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import './consent-modal.css';

const STORAGE_KEY = 'ds_consent_v1';

export function useConsent() {
  const [needed, setNeeded] = useState(false);
  const [resolveRef] = useState(() => ({ resolve: null }));

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setNeeded(true);
    }
  }, []);

  /**
   * Call before the first upload. Resolves true when accepted, false when cancelled.
   */
  const requestConsent = () => {
    if (localStorage.getItem(STORAGE_KEY)) return Promise.resolve(true);
    return new Promise((resolve) => {
      resolveRef.resolve = resolve;
      setNeeded(true);
    });
  };

  const accept = () => {
    localStorage.setItem(STORAGE_KEY, '1');
    setNeeded(false);
    resolveRef.resolve?.(true);
  };

  const decline = () => {
    setNeeded(false);
    resolveRef.resolve?.(false);
  };

  return { needed, requestConsent, accept, decline };
}

export default function ConsentModal({ onAccept, onDecline }) {
  const dialogRef = useRef(null);

  // Trap focus inside modal
  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    el.focus();
    const focusable = el.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    const trap = (e) => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === first) { e.preventDefault(); last.focus(); }
      } else {
        if (document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    el.addEventListener('keydown', trap);

    // Close on Escape
    const onEsc = (e) => { if (e.key === 'Escape') onDecline(); };
    document.addEventListener('keydown', onEsc);

    return () => {
      el.removeEventListener('keydown', trap);
      document.removeEventListener('keydown', onEsc);
    };
  }, [onDecline]);

  return (
    <div className="consent-backdrop" role="dialog" aria-modal="true" aria-labelledby="consent-title">
      <div className="consent-modal" ref={dialogRef} tabIndex="-1">
        <div className="consent-icon" aria-hidden="true">
          <svg viewBox="0 0 48 48" width="40" height="40" fill="none">
            <circle cx="24" cy="24" r="22" stroke="#7f8fff" strokeWidth="2" />
            <path d="M24 14v14M24 34v2" stroke="#7f8fff" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
        </div>

        <h2 id="consent-title" className="consent-title">Before you upload</h2>
        <p className="consent-desc">
          DeepShield processes your file on our servers to detect deepfakes and manipulation.
          Here's exactly what happens to it:
        </p>

        <ul className="consent-list" aria-label="Data handling commitments">
          <li>
            <span className="consent-check" aria-hidden="true">✓</span>
            Your file is sent over TLS-encrypted HTTPS
          </li>
          <li>
            <span className="consent-check" aria-hidden="true">✓</span>
            It is automatically deleted within 5 minutes of analysis
          </li>
          <li>
            <span className="consent-check" aria-hidden="true">✓</span>
            We never use your file for model training
          </li>
          <li>
            <span className="consent-check" aria-hidden="true">✓</span>
            No raw pixels are shared with any third-party AI service
          </li>
        </ul>

        <p className="consent-link-line">
          Full details in our{' '}
          <Link to="/privacy" className="consent-link" onClick={onDecline}>
            Privacy &amp; Data Policy
          </Link>
        </p>

        <div className="consent-actions">
          <button className="btn btn-ghost btn-sm" onClick={onDecline} id="consent-cancel">
            Cancel
          </button>
          <button className="btn btn-primary btn-sm btn-shiny" onClick={onAccept} id="consent-accept" autoFocus>
            I understand — proceed
          </button>
        </div>
      </div>
    </div>
  );
}
