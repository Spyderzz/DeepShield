import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { SharedNav, SharedFooter } from '../layout/SharedNav.jsx';
import useDottedSurface from '../../hooks/useDottedSurface.js';
import { useAuth } from '../../contexts/AuthContext.jsx';
import { beginOAuth } from '../../services/authApi.js';
import '../../pages/deepshield-landing.css';
import '../../pages/deepshield-pages.css';

export default function DeepShieldAuth({ mode: initial = 'login' }) {
  useDottedSurface();
  const [mode, setMode] = useState(initial);
  const [email, setEmail] = useState('');
  const [pw, setPw] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [name, setName] = useState('');
  const [remember, setRemember] = useState(true);
  const [busy, setBusy] = useState(false);
  const [oauthBusy, setOauthBusy] = useState(null);
  const [error, setError] = useState(null);
  const { login, register, isAuthed } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || '/analyze';

  // Redirect already-authenticated users away from the login/register page
  useEffect(() => {
    if (isAuthed) navigate(from, { replace: true });
  }, [isAuthed, navigate, from]);

  const isLogin = mode === 'login';

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (isLogin) await login(email, pw, remember);
      else await register(email, pw, name);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Authentication failed');
    } finally {
      setBusy(false);
    }
  };

  const onOAuth = async (provider) => {
    setOauthBusy(provider);
    setError(null);
    try {
      const { authorization_url } = await beginOAuth(provider, from, remember);
      window.location.assign(authorization_url);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || `${provider} sign-in failed`);
      setOauthBusy(null);
    }
  };

  return (
    <>
      <SharedNav />
      <section className="auth-shell">
        <div className="auth-bg">
          <svg viewBox="0 0 800 800" preserveAspectRatio="xMidYMid slice" className="auth-bg-svg">
            <defs>
              <linearGradient id="abg1" x1="0" y1="0" x2="1" y2="1">
                <stop stopColor="#6C7DFF" stopOpacity="0.08"/><stop offset="1" stopColor="#3DDBB3" stopOpacity="0.02"/>
              </linearGradient>
              <pattern id="abgrid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M50 0L0 0 0 50" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="800" height="800" fill="url(#abg1)"/>
            <rect width="800" height="800" fill="url(#abgrid)"/>
            {Array.from({ length: 8 }).map((_, i) => (
              <circle key={i} cx={100 + i * 80} cy={120 + (i * 67) % 600} r={1 + (i % 3)} fill="#6C7DFF" opacity={0.1 + (i % 4) * 0.1}/>
            ))}
          </svg>
        </div>

        <div className="auth-grid">
          <div className="auth-quote">
            <span className="eyebrow">DeepShield Platform</span>
            <h2 className="display italic accent">"Evidence over assertion. Calm over alarm."</h2>
            <p>Sign {isLogin ? 'in' : 'up'} to unlock your personal workspace. Save your scans, generate shareable reports, and uncover the truth behind viral media.</p>
            <ul className="auth-bullets">
              <li><span className="dot"/>Detect deepfakes across 5 media types</li>
              <li><span className="dot"/>Save and search past analyses</li>
              <li><span className="dot"/>Download detailed PDF reports</li>
              <li><span className="dot"/>Cross-check against trusted news</li>
            </ul>
            <div className="auth-trust mono">
              <span>· 100% Private</span><span>· Secure</span><span>· Transparent AI</span>
            </div>
          </div>

          <div className="auth-card">
            <div className="auth-tabs">
              <button className={isLogin ? 'active' : ''} onClick={() => setMode('login')}>Sign in</button>
              <button className={!isLogin ? 'active' : ''} onClick={() => setMode('register')}>Create account</button>
              <div className="auth-tab-pill" style={{ left: isLogin ? 4 : '50%', width: 'calc(50% - 4px)' }}/>
            </div>

            <h3 className="display">{isLogin ? 'Welcome back.' : 'Create your account.'}</h3>
            <p className="auth-sub">{isLogin ? 'Sign in to continue to DeepShield.' : 'Start analyzing media in under a minute.'}</p>

            <div className="auth-social">
              <button type="button" className="btn btn-glass btn-sm" onClick={() => onOAuth('google')} disabled={busy || oauthBusy === 'google'}>
                <span className="mono">G</span> {oauthBusy === 'google' ? 'Redirecting…' : 'Google'}
              </button>
              <button type="button" className="btn btn-glass btn-sm" onClick={() => onOAuth('github')} disabled={busy || oauthBusy === 'github'}>
                <span className="mono">◎</span> {oauthBusy === 'github' ? 'Redirecting…' : 'GitHub'}
              </button>
              <button type="button" className="btn btn-glass btn-sm" disabled title="SSO/OIDC not configured yet"><span className="mono">⎆</span> SSO</button>
            </div>
            <div className="auth-divider"><span>or with email</span></div>

            <form className="auth-form" onSubmit={onSubmit}>
              {!isLogin && (
                <label className="field">
                  <span>Full name</span>
                  <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Priya Sharma" />
                </label>
              )}
              <label className="field">
                <span>Email</span>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@org.com" required />
              </label>
              <label className="field">
                <span>Password {isLogin && <a className="field-aux">Forgot?</a>}</span>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                  <input type={showPw ? "text" : "password"} value={pw} onChange={e => setPw(e.target.value)} placeholder={isLogin ? '••••••••' : 'min 10 characters'} required style={{ width: '100%', paddingRight: '40px' }} />
                  <button type="button" onClick={() => setShowPw(!showPw)} style={{ position: 'absolute', right: '10px', background: 'none', border: 'none', color: 'var(--ds-muted)', cursor: 'pointer', padding: 4, display: 'flex', alignItems: 'center', justifyContent: 'center' }} aria-label={showPw ? 'Hide password' : 'Show password'}>
                    {showPw ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    )}
                  </button>
                </div>
                {!isLogin && pw.length > 0 && (
                  <div className="pw-meter">
                    <i style={{ width: `${Math.min(100, pw.length * 10)}%`, background: pw.length < 6 ? 'var(--ds-danger)' : pw.length < 10 ? 'var(--ds-warn)' : 'var(--ds-safe)' }}/>
                    <span className="mono">{pw.length < 6 ? 'weak' : pw.length < 10 ? 'fair' : 'strong'}</span>
                  </div>
                )}
              </label>
              {isLogin ? (
                <label className="check-row">
                  <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} />
                  <span>Keep me signed in for 30 days</span>
                </label>
              ) : (
                <label className="check-row">
                  <input type="checkbox" defaultChecked />
                  <span>I agree to the <a>Terms</a> and <a>Privacy Policy</a></span>
                </label>
              )}
              {error && <p style={{ color: 'var(--ds-danger)', fontSize: 13, margin: 0 }}>{error}</p>}
              <button type="submit" disabled={busy} className="btn btn-primary btn-lg btn-shiny" style={{ width: '100%', opacity: busy ? 0.7 : 1 }}>
                {busy ? 'Working…' : (isLogin ? 'Sign in →' : 'Create account →')}
              </button>
            </form>

            <p className="auth-foot">
              {isLogin ? 'New to DeepShield? ' : 'Have an account? '}
              <a onClick={() => setMode(isLogin ? 'register' : 'login')} style={{ cursor: 'pointer' }}>
                {isLogin ? 'Create account' : 'Sign in'}
              </a>
            </p>
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}
