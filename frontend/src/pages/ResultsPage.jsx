import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getHistoryDetail } from '../services/historyApi.js';
import AnalysisResultView from '../components/results/AnalysisResultView.jsx';

export default function ResultsPage() {
  const { id } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let live = true;
    setLoading(true);
    setNotFound(false);
    setError(null);
    getHistoryDetail(id)
      .then((data) => { if (live) setResult(data); })
      .catch((err) => {
        if (!live) return;
        const status = err?.response?.status;
        if (status === 404 || status === 401 || status === 403) {
          setNotFound(true);
        } else {
          setError(err.userMessage || err.message || 'Failed to load analysis');
        }
      })
      .finally(() => live && setLoading(false));
    return () => { live = false; };
  }, [id]);

  if (loading) {
    return (
      <section style={{ display: 'grid', gap: 'var(--space-4)' }}>
        <p style={{ color: 'var(--color-text-secondary)' }}>Loading analysis…</p>
      </section>
    );
  }

  if (notFound) {
    return (
      <section style={{ display: 'grid', gap: 'var(--space-6)', justifyItems: 'center', padding: 'var(--space-16) var(--space-4)', textAlign: 'center' }}>
        <div style={{ fontSize: '3rem' }}>🔍</div>
        <div>
          <h2 style={{ margin: '0 0 var(--space-2)' }}>Analysis not found</h2>
          <p style={{ color: 'var(--color-text-secondary)', margin: '0 0 var(--space-6)' }}>
            This analysis doesn't exist or you don't have access to it.
          </p>
          <Link
            to="/history"
            style={{
              padding: 'var(--space-3) var(--space-6)',
              background: 'var(--color-primary-500)',
              color: 'white',
              borderRadius: 'var(--radius-md)',
              textDecoration: 'none',
              fontWeight: 'var(--font-weight-semibold)',
            }}
          >
            ← Back to History
          </Link>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section style={{ display: 'grid', gap: 'var(--space-4)' }}>
        <div style={{ color: 'var(--color-danger)', background: '#FFEBEE', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
          {error}
        </div>
        <Link to="/history" style={{ color: 'var(--color-primary-600)' }}>← Back to History</Link>
      </section>
    );
  }

  return (
    <section style={{ display: 'grid', gap: 'var(--space-6)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <Link
          to="/history"
          style={{ color: 'var(--color-text-secondary)', textDecoration: 'none', fontSize: 'var(--font-size-sm)' }}
        >
          ← History
        </Link>
        <h2 style={{ margin: 0 }}>Analysis #{id}</h2>
      </div>
      <AnalysisResultView analysis={result} originalUrl={null} textContent="" />
    </section>
  );
}
