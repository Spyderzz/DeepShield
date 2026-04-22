// Shared navbar/footer for inner pages — dark editorial theme
const { useState: useStateNav, useEffect: useEffectNav, useRef: useRefNav } = React;

function SharedNav({ current = "" }) {
  const [scrolled, setScrolled] = useStateNav(false);
  useEffectNav(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = [
    { label: "Analyze", href: "Analyze.html", key: "analyze" },
    { label: "History", href: "History.html", key: "history" },
    { label: "About", href: "About.html", key: "about" },
  ];

  const refs = useRefNav([]);
  const [pill, setPill] = useStateNav({ left: 0, width: 0, opacity: 0 });
  const [hovered, setHovered] = useStateNav(null);
  useEffectNav(() => {
    const idx = hovered ?? links.findIndex(l => l.key === current);
    const el = refs.current[idx];
    if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth, opacity: 1 });
    else setPill(p => ({ ...p, opacity: 0 }));
  }, [hovered, current]);

  return (
    <header className={`ds-nav ${scrolled ? "scrolled" : ""}`}>
      <div className="ds-nav-inner">
        <a href="DeepShield.html" className="ds-logo">
          <svg width="22" height="26" viewBox="0 0 22 26" fill="none">
            <path d="M11 1L21 5V12.5C21 18.5 16.5 23.5 11 25C5.5 23.5 1 18.5 1 12.5V5L11 1Z" stroke="url(#lgN)" strokeWidth="1.5" fill="rgba(108,125,255,0.1)"/>
            <path d="M6 11L10 15L16 8" stroke="#6C7DFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            <defs><linearGradient id="lgN" x1="0" y1="0" x2="22" y2="26"><stop stopColor="#7F8FFF"/><stop offset="1" stopColor="#3DDBB3"/></linearGradient></defs>
          </svg>
          <span>DeepShield</span>
        </a>
        <nav className="ds-nav-links">
          <div className="slide-tabs" onMouseLeave={() => setHovered(null)}>
            <div className="slide-tabs-pill" style={{ left: pill.left, width: pill.width, opacity: pill.opacity }}/>
            {links.map((l, i) => (
              <a key={l.key} ref={el => refs.current[i] = el}
                href={l.href}
                onMouseEnter={() => setHovered(i)}
                className={`slide-tab ${current === l.key ? "active" : ""}`}
                style={{ textDecoration: "none" }}>
                {l.label}
              </a>
            ))}
          </div>
        </nav>
        <div className="ds-nav-right">
          <a href="Login.html" className="btn btn-ghost btn-sm" style={{textDecoration:"none"}}>Sign in</a>
          <a href="Analyze.html" className="btn btn-glass btn-sm btn-shiny" style={{textDecoration:"none"}}>
            Run analysis
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6h8m0 0L6 2m4 4L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
          </a>
        </div>
      </div>
    </header>
  );
}

function SharedFooter() {
  return (
    <footer className="ds-footer">
      <div className="ds-container ds-footer-inner">
        <div className="foot-brand">
          <a href="DeepShield.html" className="ds-logo" style={{textDecoration:"none"}}>
            <svg width="22" height="26" viewBox="0 0 22 26"><path d="M11 1L21 5V12.5C21 18.5 16.5 23.5 11 25C5.5 23.5 1 18.5 1 12.5V5L11 1Z" stroke="#6C7DFF" strokeWidth="1.5" fill="rgba(108,125,255,0.1)"/><path d="M6 11L10 15L16 8" stroke="#6C7DFF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>
            <span>DeepShield</span>
          </a>
          <p>Forensic AI for synthetic media. Open models, local-first, no retention.</p>
          <div className="foot-trust mono">
            <span>· Local-first</span><span>· Open models</span><span>· AA contrast</span>
          </div>
        </div>
        <div className="foot-cols">
          <div><h5>Product</h5>
            <a href="Analyze.html">Analyze</a>
            <a href="History.html">History</a>
            <a href="DeepShield.html">Pipeline</a>
          </div>
          <div><h5>Research</h5><a>Model cards</a><a>Benchmarks</a><a>Papers</a></div>
          <div><h5>Company</h5><a href="About.html">About</a><a>Privacy</a><a>Contact</a></div>
        </div>
      </div>
      <div className="ds-container foot-bottom mono">
        <span>© 2026 DeepShield · all signals open</span>
        <span>build · v2.0.42</span>
      </div>
    </footer>
  );
}

window.DSShared = { SharedNav, SharedFooter };
