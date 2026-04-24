export default function LLMExplainCard({ llmSummary }) {
  if (!llmSummary || !llmSummary.paragraph) return null;

  const modelUsed = llmSummary.model_used || '';
  const isUnavailable = modelUsed === 'none' || modelUsed === 'error';
  const isRateLimited = modelUsed === 'static-fallback:rate_limited';
  const isNoKey = modelUsed === 'static-fallback:no_api_key';
  const isFallback = isRateLimited || isNoKey;

  return (
    <div
      className="glass-panel"
      style={{
        background: 'linear-gradient(135deg, rgba(237,231,246,0.80) 0%, rgba(232,234,246,0.80) 100%)',
        padding: 'var(--space-5)',
        borderRadius: 'var(--radius-md)',
        borderLeft: '4px solid var(--color-primary-500)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)', gap: 'var(--space-3)' }}>
        <h3 style={{ margin: 0, fontSize: 'var(--font-size-base)' }}>AI Summary</h3>
        {isFallback ? (
          <span
            title={isRateLimited ? 'LLM hit its quota. Automatic summary shown; retry in a few minutes.' : 'LLM API key not configured. Automatic summary shown.'}
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-accent-600, #FF8F00)',
              background: 'rgba(255, 167, 38, 0.12)',
              border: '1px solid rgba(255, 167, 38, 0.35)',
              padding: '2px 8px',
              borderRadius: 'var(--radius-full, 999px)',
              fontWeight: 500,
              whiteSpace: 'nowrap',
            }}
          >
            {isRateLimited ? 'LLM paused (quota)' : 'LLM not configured'}
          </span>
        ) : modelUsed && !isUnavailable && (
          <span style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-disabled)',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}>
            {llmSummary.cached && 'cached · '}
            {modelUsed}
          </span>
        )}
      </div>

      <p style={{
        margin: 0,
        fontSize: 'var(--font-size-sm)',
        lineHeight: 1.6,
        color: 'var(--color-text-primary)',
      }}>
        {llmSummary.paragraph}
      </p>

      {llmSummary.bullets?.length > 0 && (
        <ul style={{
          margin: 'var(--space-3) 0 0 0',
          paddingLeft: 'var(--space-5)',
          display: 'grid',
          gap: 'var(--space-2)',
        }}>
          {llmSummary.bullets.map((bullet, i) => (
            <li key={i} style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              lineHeight: 1.5,
            }}>
              {bullet}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
