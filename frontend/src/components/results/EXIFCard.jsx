export default function EXIFCard({ exif }) {
  if (!exif) return null;

  const fields = [
    { label: 'Camera Make', value: exif.make },
    { label: 'Camera Model', value: exif.model },
    { label: 'Date Taken', value: exif.datetime_original },
    { label: 'GPS Location', value: exif.gps_info },
    { label: 'Software', value: exif.software },
    { label: 'Lens Model', value: exif.lens_model },
  ].filter((f) => f.value);

  const adjustment = exif.trust_adjustment || 0;
  const badgeColor = adjustment < 0 ? '#2E7D32' : adjustment > 0 ? '#C62828' : '#757575';
  const badgeBg = adjustment < 0 ? '#E8F5E9' : adjustment > 0 ? '#FFEBEE' : '#F5F5F5';
  const badgeLabel = adjustment < 0 ? 'Trust boost' : adjustment > 0 ? 'Trust penalty' : 'Neutral';

  return (
    <div style={{
      background: 'var(--color-surface)',
      padding: 'var(--space-5)',
      borderRadius: 'var(--radius-md)',
      boxShadow: 'var(--shadow-sm)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <h3 style={{ margin: 0 }}>EXIF Metadata</h3>
        <span style={{
          fontSize: 'var(--font-size-xs)',
          padding: '3px 10px',
          borderRadius: 'var(--radius-full)',
          background: badgeBg,
          color: badgeColor,
          fontWeight: 'var(--font-weight-semibold)',
        }}>
          {badgeLabel} ({adjustment > 0 ? '+' : ''}{adjustment})
        </span>
      </div>

      {fields.length === 0 ? (
        <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
          No EXIF metadata found. Many platforms strip metadata on upload.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 'var(--space-3)' }}>
          {fields.map((f) => {
            // Color-code software field
            const isSuspicious = f.label === 'Software' && adjustment > 0;
            const isGood = f.label !== 'Software' && adjustment < 0;
            return (
              <div key={f.label} style={{
                padding: 'var(--space-3)',
                background: isSuspicious ? '#FFF3E0' : isGood ? '#F1F8E9' : 'var(--color-bg, #fafafa)',
                borderRadius: 'var(--radius-sm)',
                borderLeft: `3px solid ${isSuspicious ? '#EF6C00' : isGood ? '#43A047' : 'var(--color-border)'}`,
              }}>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)', marginBottom: '2px' }}>{f.label}</div>
                <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)' }}>{f.value}</div>
              </div>
            );
          })}
        </div>
      )}

      {exif.trust_reason && (
        <div style={{ marginTop: 'var(--space-3)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)' }}>
          {exif.trust_reason}
        </div>
      )}
    </div>
  );
}
