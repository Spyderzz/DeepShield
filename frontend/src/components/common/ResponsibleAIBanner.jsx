export default function ResponsibleAIBanner({ text }) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 'var(--space-3)',
        background: '#FFF8E1',
        border: '1px solid #FFE082',
        color: '#6D4C00',
        padding: 'var(--space-4)',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-sm)',
      }}
    >
      <span aria-hidden style={{ fontSize: 'var(--font-size-lg)' }}>⚠</span>
      <span>
        {text ||
          'AI-based analysis may not be 100% accurate. Cross-check with trusted sources before sharing. This tool aids verification — it does not replace human judgment.'}
      </span>
    </div>
  );
}
