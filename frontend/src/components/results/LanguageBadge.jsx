const LANG_LABELS = {
  en: 'English',
  hi: 'Hindi',
  bn: 'Bengali',
  ta: 'Tamil',
  te: 'Telugu',
  mr: 'Marathi',
  ur: 'Urdu',
  fr: 'French',
  de: 'German',
  es: 'Spanish',
  ar: 'Arabic',
  zh: 'Chinese',
};

export default function LanguageBadge({ language, truthOverride }) {
  if (!language) return null;

  const langLabel = LANG_LABELS[language] || language.toUpperCase();
  const isNonEnglish = language !== 'en';

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', alignItems: 'center' }}>
      {/* Language badge */}
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '4px 12px',
        borderRadius: 'var(--radius-full)',
        background: isNonEnglish ? '#E3F2FD' : '#F3F4F6',
        color: isNonEnglish ? '#1565C0' : 'var(--color-text-secondary)',
        fontSize: 'var(--font-size-xs)',
        fontWeight: 'var(--font-weight-semibold)',
        border: `1px solid ${isNonEnglish ? '#90CAF9' : 'var(--color-border)'}`,
      }}>
        <span style={{ fontSize: '10px' }}>🌐</span>
        {langLabel}
        {isNonEnglish && (
          <span style={{ fontSize: '10px', opacity: 0.7 }}>· multilingual model</span>
        )}
      </span>

      {/* Truth-override badge */}
      {truthOverride && truthOverride.applied && (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px',
          padding: '4px 12px',
          borderRadius: 'var(--radius-full)',
          background: '#E8F5E9',
          color: '#2E7D32',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 'var(--font-weight-semibold)',
          border: '1px solid #A5D6A7',
          title: `Corroborated by ${truthOverride.source_name} (similarity ${(truthOverride.similarity * 100).toFixed(0)}%)`,
        }}>
          <span style={{ fontSize: '10px' }}>✓</span>
          Truth-override applied
          <span style={{ opacity: 0.7 }}>· {(truthOverride.similarity * 100).toFixed(0)}% match</span>
        </span>
      )}

      {/* Truth-override checked but not applied */}
      {truthOverride && !truthOverride.applied && truthOverride.source_url && (
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px',
          padding: '4px 12px',
          borderRadius: 'var(--radius-full)',
          background: '#F5F5F5',
          color: 'var(--color-text-disabled)',
          fontSize: 'var(--font-size-xs)',
          border: '1px solid var(--color-border)',
        }}>
          No corroborating source found
          <span style={{ opacity: 0.7 }}>({(truthOverride.similarity * 100).toFixed(0)}% best match)</span>
        </span>
      )}
    </div>
  );
}
