import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SharedNav, SharedFooter } from '../components/layout/SharedNav.jsx';
import useDottedSurface from '../hooks/useDottedSurface.js';
import { useAuth } from '../contexts/AuthContext.jsx';
import { listHistory, deleteHistory } from '../services/historyApi.js';
import './deepshield-landing.css';
import './deepshield-pages.css';

function toDisplayItem(r) {
  const score = typeof r.authenticity_score === 'number' ? Math.round(r.authenticity_score) : 50;
  const c = score >= 65 ? 'safe' : score >= 40 ? 'warn' : 'danger';
  const verdict = c === 'safe' ? 'REAL' : c === 'warn' ? 'SUSP' : 'FAKE';
  const idStr = String(r.id);
  return {
    id: r.id,
    type: r.media_type || 'image',
    verdict,
    c,
    score,
    title: r.title || `${r.media_type || 'analysis'} · #${idStr}`,
    sub: r.verdict ? `verdict · ${r.verdict}` : '',
    when: r.created_at ? new Date(r.created_at).toLocaleString() : '',
    src: r.thumbnail_url || null,
    hash: idStr.padStart(8, '0'),
  };
}

export default function HistoryPage() {
  useDottedSurface();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [filter, setFilter] = useState('all');
  const [view, setView] = useState('grid');
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('recent');
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    (async () => {
      setLoading(true);
      try {
        const data = await listHistory(200, 0);
        setRows((data.items || []).map(toDisplayItem));
      } catch (e) {
        setError(e?.response?.data?.detail || e?.message || 'Failed to load history');
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  const items = useMemo(() => {
    let arr = rows.filter(i =>
      (filter === 'all' || i.type === filter) &&
      (!search || i.title.toLowerCase().includes(search.toLowerCase()) || String(i.id).includes(search))
    );
    if (sort === 'score') arr = [...arr].sort((a, b) => a.score - b.score);
    else if (sort === 'type') arr = [...arr].sort((a, b) => a.type.localeCompare(b.type));
    return arr;
  }, [rows, filter, search, sort]);

  const stats = useMemo(() => ({
    total: rows.length,
    fake: rows.filter(i => i.c === 'danger').length,
    susp: rows.filter(i => i.c === 'warn').length,
    real: rows.filter(i => i.c === 'safe').length,
    avg: rows.length ? Math.round(rows.reduce((s, i) => s + i.score, 0) / rows.length) : 0,
  }), [rows]);

  if (!user) {
    return (
      <>
        <SharedNav current="history" />
        <section className="page-shell history-shell">
          <div className="page-head">
            <div className="crumbs">
              <a onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Home</a>
              <span className="sep">/</span>
              <span>History</span>
            </div>
            <span className="eyebrow">Analysis history</span>
            <h1 className="display">Sign in to see <em className="italic accent">your verdicts.</em></h1>
            <p className="sub">DeepShield only stores history for signed-in users. Sign in or create a free account to save and cross-reference past analyses.</p>
            <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
              <button className="btn btn-primary btn-lg btn-shiny" onClick={() => navigate('/login')}>Sign in →</button>
              <button className="btn btn-glass btn-lg" onClick={() => navigate('/register')}>Create account</button>
            </div>
          </div>
        </section>
        <SharedFooter />
      </>
    );
  }

  return (
    <>
      <SharedNav current="history" />
      <section className="page-shell history-shell">
        <div className="page-head">
          <div className="crumbs">
            <a onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Home</a>
            <span className="sep">/</span>
            <span>History</span>
          </div>
          <span className="eyebrow">Analysis history</span>
          <h1 className="display">Every verdict, <em className="italic accent">indexed.</em></h1>
          <p className="sub">Search and filter past analyses. Results are content-addressable by SHA — re-submitting the same file returns the cached verdict instantly.</p>
        </div>

        <div className="history-wrap">
          <div className="hist-stats">
            <div className="hs-cell"><span className="eyebrow">Total</span><b>{stats.total}</b></div>
            <div className="hs-cell"><span className="eyebrow" style={{ color: 'var(--ds-danger)' }}>Fake</span><b>{stats.fake}</b></div>
            <div className="hs-cell"><span className="eyebrow" style={{ color: 'var(--ds-warn)' }}>Suspicious</span><b>{stats.susp}</b></div>
            <div className="hs-cell"><span className="eyebrow" style={{ color: 'var(--ds-safe)' }}>Real</span><b>{stats.real}</b></div>
            <div className="hs-cell avg"><span className="eyebrow">Avg score</span><b>{stats.avg}</b></div>
            <div className="hs-cell"><span className="eyebrow">Cache hit</span><b>—</b></div>
          </div>

          <div className="hist-toolbar">
            <div className="hist-search">
              <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="6" cy="6" r="4.5" stroke="currentColor" fill="none"/><path d="M9.5 9.5L13 13" stroke="currentColor" strokeLinecap="round"/></svg>
              <input placeholder="Search filename, id, domain…" value={search} onChange={e => setSearch(e.target.value)} />
              {search && <button onClick={() => setSearch('')} className="clear">×</button>}
            </div>
            <div className="hist-filters">
              {[['all', 'All'], ['image', 'Image'], ['video', 'Video'], ['text', 'Text'], ['screenshot', 'Screenshot']].map(([k, l]) => (
                <button key={k} className={`chip ${filter === k ? 'active' : ''}`} onClick={() => setFilter(k)}>{l}</button>
              ))}
            </div>
            <div className="grow"/>
            <select className="hist-sort" value={sort} onChange={e => setSort(e.target.value)}>
              <option value="recent">Sort · most recent</option>
              <option value="score">Sort · lowest score</option>
              <option value="type">Sort · by type</option>
            </select>
            <div className="view-toggle">
              <button className={view === 'grid' ? 'active' : ''} onClick={() => setView('grid')}>▦</button>
              <button className={view === 'table' ? 'active' : ''} onClick={() => setView('table')}>≡</button>
            </div>
          </div>

          {loading && <p style={{ color: 'var(--ds-muted)' }}>Loading…</p>}
          {error && <p style={{ color: 'var(--ds-danger)' }}>{error}</p>}

          {!loading && view === 'grid' && (
            <div className="hist-grid">
              {items.map(i => (
                <a onClick={() => navigate(`/results/${i.id}`)} key={i.id} className="hist-card" style={{ cursor: 'pointer' }}>
                  <div className="hist-thumb" style={i.src ? { backgroundImage: `url(${i.src})` } : { background: 'linear-gradient(135deg, rgba(108,125,255,0.08), rgba(61,219,179,0.04))' }}>
                    {!i.src && <span className="hist-typeicon">{i.type === 'text' ? '¶' : '▦'}</span>}
                    <span className={`verdict-dot h-verdict ${i.c}`}>{i.verdict}</span>
                    <span className="hist-type mono">{i.type}</span>
                  </div>
                  <div className="hist-body">
                    <h4>{i.title}</h4>
                    <p>{i.sub}</p>
                    <div className="hist-foot mono">
                      <span>id · {i.hash.slice(0, 6)}</span>
                      <span>· score {i.score}</span>
                      <span>· {i.when}</span>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          )}

          {!loading && view === 'table' && (
            <table className="hist-table">
              <thead>
                <tr><th>Verdict</th><th>Title</th><th>Type</th><th>Score</th><th>ID</th><th>Timestamp</th><th></th></tr>
              </thead>
              <tbody>
                {items.map(i => (
                  <tr key={i.id}>
                    <td><span className={`verdict-dot h-verdict ${i.c}`}>{i.verdict}</span></td>
                    <td><b>{i.title}</b><span className="mono" style={{ color: 'var(--ds-muted)', marginLeft: 8, fontSize: 11 }}>{i.sub}</span></td>
                    <td className="mono">{i.type}</td>
                    <td>
                      <div className="tbl-bar"><i style={{ width: `${i.score}%`, background: i.c === 'safe' ? 'var(--ds-safe)' : i.c === 'warn' ? 'var(--ds-warn)' : 'var(--ds-danger)' }}/></div>
                      <span className="mono" style={{ marginLeft: 8, fontSize: 11 }}>{i.score}</span>
                    </td>
                    <td className="mono" style={{ color: 'var(--ds-muted)' }}>{i.hash}</td>
                    <td className="mono" style={{ color: 'var(--ds-muted)' }}>{i.when}</td>
                    <td>
                      <a onClick={() => navigate(`/results/${i.id}`)} className="mono" style={{ color: 'var(--ds-brand)', cursor: 'pointer' }}>open →</a>
                      <a
                        className="mono"
                        style={{ color: 'var(--ds-danger)', cursor: 'pointer', marginLeft: 12 }}
                        onClick={async () => {
                          if (!confirm('Delete this analysis?')) return;
                          try { await deleteHistory(i.id); setRows(rs => rs.filter(r => r.id !== i.id)); } catch (_e) {}
                        }}
                      >delete</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {!loading && items.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">⌕</div>
              <h3>{rows.length === 0 ? 'No analyses yet' : 'No matches'}</h3>
              <p>{rows.length === 0 ? 'Run your first analysis to see it here.' : 'Try a different filter or clear your search.'}</p>
              <button
                className="btn btn-glass btn-sm"
                onClick={() => { if (rows.length === 0) navigate('/analyze'); else { setSearch(''); setFilter('all'); } }}
              >
                {rows.length === 0 ? 'Analyze media →' : 'Reset'}
              </button>
            </div>
          )}
        </div>
      </section>
      <SharedFooter />
    </>
  );
}
