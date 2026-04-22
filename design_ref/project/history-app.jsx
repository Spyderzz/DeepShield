const { useState: uSH, useMemo: uMH } = React;

function HistoryApp() {
  const [filter, setFilter] = uSH("all");
  const [view, setView] = uSH("grid"); // grid | table
  const [search, setSearch] = uSH("");
  const [sort, setSort] = uSH("recent");

  const items = uMH(() => [
    { id:"a8f2c1e9", type:"image", verdict:"SUSP", c:"warn", score:48, title:"press-conference.jpg", sub:"studio portrait · Photoshop detected", when:"2m ago", src:"https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80&auto=format" },
    { id:"b2d9e414", type:"video", verdict:"FAKE", c:"danger", score:18, title:"ceo-statement.mp4", sub:"3.2s · lip-sync anomaly", when:"18m ago", src:"https://images.unsplash.com/photo-1488554378835-f7acf46e6c98?w=400&q=80&auto=format" },
    { id:"c4e1b7a2", type:"text", verdict:"FAKE", c:"danger", score:22, title:"WhatsApp forward", sub:"sensationalism 0.91 · no source match", when:"41m ago", src:null },
    { id:"d9e88f01", type:"image", verdict:"REAL", c:"safe", score:92, title:"wedding-candid.jpg", sub:"clean EXIF · Canon EOS R5", when:"1h ago", src:"https://images.unsplash.com/photo-1519741497674-611481863552?w=400&q=80&auto=format" },
    { id:"e2f4a9b6", type:"screenshot", verdict:"SUSP", c:"warn", score:51, title:"tweet-screenshot.png", sub:"layout mismatch · font rendering", when:"3h ago", src:"https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=400&q=80&auto=format" },
    { id:"f7c9d013", type:"image", verdict:"REAL", c:"safe", score:88, title:"field-report.jpg", sub:"Reuters pool · matched", when:"4h ago", src:"https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&q=80&auto=format" },
    { id:"1a3b4c5d", type:"video", verdict:"REAL", c:"safe", score:84, title:"interview-raw.mp4", sub:"18.4s · temporal coherent", when:"yesterday", src:"https://images.unsplash.com/photo-1496128858413-b36217c2ce36?w=400&q=80&auto=format" },
    { id:"2e5f7a8b", type:"image", verdict:"FAKE", c:"danger", score:9, title:"ai-portrait.png", sub:"GAN signature strong · Midjourney-like", when:"yesterday", src:"https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=400&q=80&auto=format" },
    { id:"3b6c9d0e", type:"text", verdict:"REAL", c:"safe", score:81, title:"PR statement", sub:"matched Reuters + AP · low sensationalism", when:"2 days ago", src:null },
    { id:"4d7e0f12", type:"screenshot", verdict:"FAKE", c:"danger", score:14, title:"fake-bank-alert.png", sub:"OCR: phishing phrase map", when:"2 days ago", src:"https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=400&q=80&auto=format" },
  ], []);

  const filtered = items.filter(i => (filter==="all" || i.type===filter) && (!search || i.title.toLowerCase().includes(search.toLowerCase()) || i.id.includes(search)));

  const { SharedNav, SharedFooter } = window.DSShared;

  const stats = {
    total: items.length,
    fake: items.filter(i=>i.c==="danger").length,
    susp: items.filter(i=>i.c==="warn").length,
    real: items.filter(i=>i.c==="safe").length,
  };

  return (
    <>
      <SharedNav current="history" />
      <section className="page-shell history-shell">
        <div className="page-head">
          <div className="crumbs"><a href="DeepShield.html">Home</a><span className="sep">/</span><span>History</span></div>
          <span className="eyebrow">Analysis history</span>
          <h1 className="display">Every verdict, <em className="italic accent">indexed.</em></h1>
          <p className="sub">Search and filter past analyses. Results are content-addressable by SHA — re-submitting the same file returns the cached verdict instantly.</p>
        </div>

        <div className="history-wrap">
          <div className="hist-stats">
            <div className="hs-cell"><span className="eyebrow">Total</span><b>{stats.total}</b></div>
            <div className="hs-cell"><span className="eyebrow" style={{color:"var(--ds-danger)"}}>Fake</span><b>{stats.fake}</b></div>
            <div className="hs-cell"><span className="eyebrow" style={{color:"var(--ds-warn)"}}>Suspicious</span><b>{stats.susp}</b></div>
            <div className="hs-cell"><span className="eyebrow" style={{color:"var(--ds-safe)"}}>Real</span><b>{stats.real}</b></div>
            <div className="hs-cell avg"><span className="eyebrow">Avg score</span><b>{Math.round(items.reduce((s,i)=>s+i.score,0)/items.length)}</b></div>
            <div className="hs-cell"><span className="eyebrow">Cache hit</span><b>68%</b></div>
          </div>

          <div className="hist-toolbar">
            <div className="hist-search">
              <svg width="14" height="14" viewBox="0 0 14 14"><circle cx="6" cy="6" r="4.5" stroke="currentColor" fill="none"/><path d="M9.5 9.5L13 13" stroke="currentColor" strokeLinecap="round"/></svg>
              <input placeholder="Search filename, hash, domain…" value={search} onChange={e=>setSearch(e.target.value)} />
              {search && <button onClick={()=>setSearch("")} className="clear">×</button>}
            </div>
            <div className="hist-filters">
              {[["all","All"],["image","Image"],["video","Video"],["text","Text"],["screenshot","Screenshot"]].map(([k,l])=>(
                <button key={k} className={`chip ${filter===k?"active":""}`} onClick={()=>setFilter(k)}>{l}</button>
              ))}
            </div>
            <div className="grow"/>
            <select className="hist-sort" value={sort} onChange={e=>setSort(e.target.value)}>
              <option value="recent">Sort · most recent</option>
              <option value="score">Sort · lowest score</option>
              <option value="type">Sort · by type</option>
            </select>
            <div className="view-toggle">
              <button className={view==="grid"?"active":""} onClick={()=>setView("grid")}>▦</button>
              <button className={view==="table"?"active":""} onClick={()=>setView("table")}>≡</button>
            </div>
          </div>

          {view==="grid" ? (
            <div className="hist-grid">
              {filtered.map(i=>(
                <a href="Results.html" key={i.id} className="hist-card">
                  <div className="hist-thumb" style={i.src ? { backgroundImage:`url(${i.src})` } : { background:"linear-gradient(135deg, rgba(108,125,255,0.08), rgba(61,219,179,0.04))" }}>
                    {!i.src && <span className="hist-typeicon">{i.type==="text"?"¶":"▦"}</span>}
                    <span className={`verdict-dot h-verdict ${i.c}`}>{i.verdict}</span>
                    <span className="hist-type mono">{i.type}</span>
                  </div>
                  <div className="hist-body">
                    <h4>{i.title}</h4>
                    <p>{i.sub}</p>
                    <div className="hist-foot mono">
                      <span>sha · {i.id.slice(0,6)}</span>
                      <span>· score {i.score}</span>
                      <span>· {i.when}</span>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <table className="hist-table">
              <thead>
                <tr><th>Verdict</th><th>Title</th><th>Type</th><th>Score</th><th>SHA</th><th>Timestamp</th><th></th></tr>
              </thead>
              <tbody>
                {filtered.map(i=>(
                  <tr key={i.id}>
                    <td><span className={`verdict-dot h-verdict ${i.c}`}>{i.verdict}</span></td>
                    <td><b>{i.title}</b><span className="mono" style={{color:"var(--ds-muted)", marginLeft:8, fontSize:11}}>{i.sub}</span></td>
                    <td className="mono">{i.type}</td>
                    <td><div className="tbl-bar"><i style={{width:`${i.score}%`, background: i.c==="safe"?"var(--ds-safe)":i.c==="warn"?"var(--ds-warn)":"var(--ds-danger)"}}/></div><span className="mono" style={{marginLeft:8, fontSize:11}}>{i.score}</span></td>
                    <td className="mono" style={{color:"var(--ds-muted)"}}>{i.id}</td>
                    <td className="mono" style={{color:"var(--ds-muted)"}}>{i.when}</td>
                    <td><a href="Results.html" className="mono" style={{color:"var(--ds-brand)"}}>open →</a></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {filtered.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">⌕</div>
              <h3>No matches</h3>
              <p>Try a different filter or clear your search.</p>
              <button className="btn btn-glass btn-sm" onClick={()=>{setSearch("");setFilter("all");}}>Reset</button>
            </div>
          )}
        </div>
      </section>
      <SharedFooter />
    </>
  );
}

function mountHistory() {
  if (window.DSShared) ReactDOM.createRoot(document.getElementById("root")).render(<HistoryApp />);
  else setTimeout(mountHistory, 50);
}
window.mountHistory = mountHistory;
