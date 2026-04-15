import { SEVERITY_COLORS } from '../../utils/constants.js';

const SEVERITY_BG = {
  high:   'rgba(229, 57, 53, 0.15)',
  medium: 'rgba(255, 167, 38, 0.15)',
  low:    'rgba(66, 165, 245, 0.12)',
};
const SEVERITY_BORDER = {
  high:   'rgba(229, 57, 53, 0.5)',
  medium: 'rgba(255, 167, 38, 0.5)',
  low:    'rgba(66, 165, 245, 0.35)',
};

export default function TextHighlighter({ text, indicators = [] }) {
  if (!text) return null;
  if (!indicators.length) {
    return (
      <div style={{
        whiteSpace: 'pre-wrap',
        fontFamily: 'var(--font-family)',
        fontSize: 'var(--font-size-base)',
        lineHeight: 1.7,
        color: 'var(--color-text-primary)',
        padding: 'var(--space-4)',
        background: 'var(--color-surface)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
      }}>
        {text}
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-4)', fontStyle: 'italic' }}>
          No manipulation patterns detected in this text.
        </p>
      </div>
    );
  }

  // Build highlighted segments
  const sorted = [...indicators].sort((a, b) => a.start_pos - b.start_pos);
  const parts = [];
  let cursor = 0;

  for (const ind of sorted) {
    if (ind.start_pos > cursor) {
      parts.push({ type: 'text', content: text.slice(cursor, ind.start_pos) });
    }
    parts.push({ type: 'highlight', content: text.slice(ind.start_pos, ind.end_pos), indicator: ind });
    cursor = ind.end_pos;
  }
  if (cursor < text.length) {
    parts.push({ type: 'text', content: text.slice(cursor) });
  }

  return (
    <div>
      <div style={{
        whiteSpace: 'pre-wrap',
        fontFamily: 'var(--font-family)',
        fontSize: 'var(--font-size-base)',
        lineHeight: 1.7,
        color: 'var(--color-text-primary)',
        padding: 'var(--space-4)',
        background: 'var(--color-surface)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
      }}>
        {parts.map((part, i) =>
          part.type === 'text' ? (
            <span key={i}>{part.content}</span>
          ) : (
            <span
              key={i}
              title={`${part.indicator.pattern_type}: ${part.indicator.description}`}
              style={{
                background: SEVERITY_BG[part.indicator.severity] || SEVERITY_BG.low,
                borderBottom: `2px solid ${SEVERITY_BORDER[part.indicator.severity] || SEVERITY_BORDER.low}`,
                borderRadius: '2px',
                padding: '1px 2px',
                cursor: 'help',
                transition: 'background 0.2s',
              }}
            >
              {part.content}
            </span>
          )
        )}
      </div>

      {/* Legend */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 'var(--space-3)',
        marginTop: 'var(--space-3)',
        fontSize: 'var(--font-size-xs)',
        color: 'var(--color-text-secondary)',
      }}>
        {indicators.length > 0 && (
          <span style={{ fontWeight: 'var(--font-weight-medium)' }}>
            {indicators.length} pattern{indicators.length !== 1 ? 's' : ''} detected:
          </span>
        )}
        {[...new Set(indicators.map(i => i.pattern_type))].map(pt => (
          <span key={pt} style={{
            padding: '2px 8px',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
          }}>
            {pt.replace(/_/g, ' ')}
          </span>
        ))}
      </div>
    </div>
  );
}
