import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.jsx';
import logoImg from '../../assets/logo.png';

export function SharedNav({ current = '' }) {
  const [scrolled, setScrolled] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const links = [
    { label: 'Home', to: '/', key: 'home' },
    { label: 'Analyze', to: '/analyze', key: 'analyze' },
    { label: 'History', to: '/history', key: 'history' },
    { label: 'About', to: '/about', key: 'about' },
    { label: 'Privacy', to: '/privacy', key: 'privacy' },
    { label: 'Contact', to: '/contact', key: 'contact' },
  ];

  const refs = useRef([]);
  const [pill, setPill] = useState({ left: 0, width: 0, opacity: 0 });
  const [hovered, setHovered] = useState(null);
  useEffect(() => {
    const idx = hovered ?? links.findIndex(l => l.key === current);
    const el = refs.current[idx];
    if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth, opacity: 1 });
    else setPill(p => ({ ...p, opacity: 0 }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hovered, current]);

  return (
    <header className={`ds-nav ${scrolled ? 'scrolled' : ''}`}>
      <div className="ds-nav-inner">
        <Link to="/" className="ds-logo">
          <img src={logoImg} alt="DeepShield Logo" className="ds-logo-img" />
        </Link>
        <nav className="ds-nav-links">
          <div className="slide-tabs" onMouseLeave={() => setHovered(null)}>
            <div className="slide-tabs-pill" style={{ left: pill.left, width: pill.width, opacity: pill.opacity }} />
            {links.map((l, i) => (
              <NavLink key={l.key} ref={el => refs.current[i] = el}
                to={l.to}
                onMouseEnter={() => setHovered(i)}
                className={({ isActive }) => `slide-tab ${current === l.key || isActive ? 'active' : ''}`}
                style={{ textDecoration: 'none' }}>
                {l.label}
              </NavLink>
            ))}
          </div>
        </nav>
        <div className="ds-nav-right">
          {user ? (
            <>
              <span className="btn btn-ghost btn-sm" style={{ cursor: 'default' }}>{user.name || user.email}</span>
              <button className="btn btn-ghost btn-sm" onClick={() => { logout(); navigate('/'); }}>Sign out</button>
            </>
          ) : (
            <Link to="/login" state={{ from: location.pathname }} className="btn btn-ghost btn-sm" style={{ textDecoration: 'none' }}>Sign in</Link>
          )}
          <Link to="/analyze" className="btn btn-glass btn-sm btn-shiny" style={{ textDecoration: 'none' }}>
            Run analysis
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6h8m0 0L6 2m4 4L6 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
          </Link>
        </div>
      </div>
    </header>
  );
}

export function SharedFooter() {
  return (
    <footer className="ds-footer">
      <div className="ds-container ds-footer-inner">
        <div className="foot-brand">
          <Link to="/" className="ds-logo" style={{ textDecoration: 'none' }}>
            <img src={logoImg} alt="DeepShield Logo" className="ds-logo-img" />
          </Link>
          <p>Forensic AI for synthetic media. Open models, local-first, no retention.</p>
          <div className="foot-trust mono">
            <span>· Local-first</span><span>· Open models</span><span>· AA contrast</span>
          </div>
        </div>
        <div className="foot-cols">
          <div>
            <h5>Product</h5>
            <Link to="/analyze">Analyze</Link>
            <Link to="/history">History</Link>
            <Link to="/">Pipeline</Link>
          </div>
          <div>
            <h5>Research</h5>
            <Link to="/models">Models</Link>
            <a href="https://paperswithcode.com/task/deepfake-detection" target="_blank" rel="noreferrer">Benchmarks</a>
            <a href="https://arxiv.org/abs/1901.08971" target="_blank" rel="noreferrer">Papers</a>
          </div>
          <div>
            <h5>Company</h5>
            <Link to="/about">About</Link>
            <Link to="/privacy">Privacy</Link>
            <Link to="/contact">Contact</Link>
          </div>
        </div>
      </div>
      <div className="ds-container foot-bottom mono">
        <span>© 2026 DeepShield · all signals open</span>
        <span>build · v2.0.42</span>
      </div>
    </footer>
  );
}
