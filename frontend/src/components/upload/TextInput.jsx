import { useState } from 'react';

const MIN_CHARS = 50;
const MAX_CHARS = 10000;

export default function TextInput({ onTextSubmit, disabled = false }) {
  const [text, setText] = useState('');

  const charCount = text.length;
  const isValid = charCount >= MIN_CHARS && charCount <= MAX_CHARS;

  return (
    <div style={{
      display: 'grid',
      gap: 'var(--space-3)',
    }}>
      <textarea
        id="text-analysis-input"
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
        disabled={disabled}
        placeholder="Paste a news article, social media post, or any text you'd like to verify for misinformation…"
        rows={10}
        style={{
          width: '100%',
          padding: 'var(--space-4)',
          fontFamily: 'var(--font-family)',
          fontSize: 'var(--font-size-base)',
          lineHeight: 1.6,
          color: 'var(--color-text-primary)',
          background: 'var(--color-surface)',
          border: `2px solid ${isValid ? 'var(--color-primary-300)' : charCount > 0 ? 'var(--color-warning)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-md)',
          resize: 'vertical',
          transition: 'border-color 0.2s',
          outline: 'none',
          boxSizing: 'border-box',
        }}
        onFocus={(e) => { if (isValid) e.target.style.borderColor = 'var(--color-primary-500)'; }}
        onBlur={(e) => { e.target.style.borderColor = isValid ? 'var(--color-primary-300)' : charCount > 0 ? 'var(--color-warning)' : 'var(--color-border)'; }}
      />
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: 'var(--font-size-sm)',
        color: charCount < MIN_CHARS && charCount > 0 ? 'var(--color-warning)' : 'var(--color-text-secondary)',
      }}>
        <span>
          {charCount < MIN_CHARS && charCount > 0
            ? `Need at least ${MIN_CHARS - charCount} more characters`
            : charCount >= MIN_CHARS
              ? '✓ Ready for analysis'
              : `Minimum ${MIN_CHARS} characters required`}
        </span>
        <span>{charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()}</span>
      </div>

      <button
        id="text-analyze-btn"
        onClick={() => onTextSubmit(text)}
        disabled={!isValid || disabled}
        style={{
          padding: 'var(--space-3) var(--space-6)',
          background: isValid && !disabled ? 'var(--color-primary-500)' : 'var(--color-border)',
          color: 'white',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          cursor: isValid && !disabled ? 'pointer' : 'not-allowed',
          fontWeight: 'var(--font-weight-semibold)',
          fontSize: 'var(--font-size-base)',
          boxShadow: isValid && !disabled ? 'var(--shadow-md)' : 'none',
          transition: 'all 0.2s',
          justifySelf: 'start',
        }}
      >
        {disabled ? 'Analyzing…' : 'Analyze Text'}
      </button>
    </div>
  );
}
