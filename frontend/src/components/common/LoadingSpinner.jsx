export default function LoadingSpinner({ label = 'Analyzing…' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', color: 'var(--color-text-secondary)' }}>
      <div
        style={{
          width: 20,
          height: 20,
          borderRadius: '50%',
          border: '3px solid var(--color-border)',
          borderTopColor: 'var(--color-primary-500)',
          animation: 'dsspin 0.9s linear infinite',
        }}
      />
      <span>{label}</span>
      <style>{`@keyframes dsspin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
