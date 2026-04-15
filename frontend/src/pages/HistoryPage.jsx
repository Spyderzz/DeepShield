import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { listHistory, deleteHistory } from '../services/historyApi.js';

const MEDIA_ICON = { image: 'IMG', video: 'VID', text: 'TXT', screenshot: 'SS' };

function verdictColor(score) {
  if (score >= 70) return 'var(--color-success, #2E7D32)';
  if (score >= 40) return 'var(--color-warning, #EF6C00)';
  return 'var(--color-danger, #C62828)';
}

export default function HistoryPage() {
  const { isAuthed, user } = useAuth();
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthed) {
      nav('/login', { replace: true, state: { from: '/history' } });
      return;
    }
    let live = true;
    setLoading(true);
    listHistory(50, 0)
      .then((data) => { if (live) { setItems(data.items); setTotal(data.total); } })
      .catch((err) => live && setError(err.userMessage || err.message || 'Failed to load history'))
      .finally(() => live && setLoading(false));
    return () => { live = false; };
  }, [isAuthed, nav]);

  const handleDelete = async (id) => {
    if (!confirm('Delete this analysis?')) return;
    try {
      await deleteHistory(id);
      setItems((xs) => xs.filter((x) => x.id !== id));
      setTotal((n) => Math.max(0, n - 1));
    } catch (err) {
      alert(err.userMessage || 'Delete failed');
    }
  };

  if (!isAuthed) return null;

  return (
    <section style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <div>
        <h2 style={{ marginBottom: 'var(--space-2)' }}>History</h2>
        <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
          {user?.email} · {total} saved {total === 1 ? 'analysis' : 'analyses'}
        </p>
      </div>

      {loading && <p>Loading…</p>}
      {error && <div style={{ color: 'var(--color-danger)' }}>{error}</div>}

      {!loading && !error && items.length === 0 && (
        <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
          <p style={{ margin: 0 }}>No analyses yet. <Link to="/analyze" style={{ color: 'var(--color-primary-600)' }}>Run your first analysis →</Link></p>
        </div>
      )}

      {items.length > 0 && (
        <div style={{ display: 'grid', gap: 'var(--space-2)' }}>
          {items.map((it) => (
            <div key={it.id} style={{
              display: 'grid',
              gridTemplateColumns: '48px 1fr auto auto',
              gap: 'var(--space-4)',
              alignItems: 'center',
              padding: 'var(--space-3) var(--space-4)',
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 'var(--radius-sm)',
                background: 'var(--color-primary-50, rgba(99,102,241,0.08))',
                color: 'var(--color-primary-600)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 'var(--font-weight-bold)', fontSize: 'var(--font-size-xs)',
              }}>{MEDIA_ICON[it.media_type] || '?'}</div>
              <div style={{ display: 'grid', gap: 2, minWidth: 0 }}>
                <div style={{ fontWeight: 'var(--font-weight-semibold)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {it.verdict}
                </div>
                <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  {it.media_type} · {new Date(it.created_at).toLocaleString()}
                </div>
              </div>
              <div style={{
                fontWeight: 'var(--font-weight-bold)',
                color: verdictColor(it.authenticity_score),
                fontSize: 'var(--font-size-lg)',
              }}>
                {Math.round(it.authenticity_score)}
              </div>
              <button
                onClick={() => handleDelete(it.id)}
                style={{
                  padding: 'var(--space-2) var(--space-3)',
                  background: 'transparent',
                  color: 'var(--color-danger)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontSize: 'var(--font-size-xs)',
                }}
              >Delete</button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
