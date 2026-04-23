const { useState: uSL } = React;

function AuthApp({ mode: initial = "login" }) {
  const [mode, setMode] = uSL(initial);
  const [email, setEmail] = uSL("");
  const [pw, setPw] = uSL("");
  const [name, setName] = uSL("");
  const [remember, setRemember] = uSL(true);

  const { SharedNav, SharedFooter } = window.DSShared;
  const isLogin = mode === "login";

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
            {Array.from({length:8}).map((_,i)=>(
              <circle key={i} cx={Math.random()*800} cy={Math.random()*800} r={Math.random()*3+1} fill="#6C7DFF" opacity={Math.random()*0.4+0.1}/>
            ))}
          </svg>
        </div>

        <div className="auth-grid">
          <div className="auth-quote">
            <span className="eyebrow">DeepShield</span>
            <h2 className="display italic accent">"Evidence over assertion. Calm over alarm."</h2>
            <p>Sign {isLogin?"in":"up"} to save your analysis history, get PDF reports, and cross-reference against your org's trusted source list.</p>
            <ul className="auth-bullets">
              <li><span className="dot"/>Cached verdicts by SHA</li>
              <li><span className="dot"/>Team shared history</li>
              <li><span className="dot"/>Custom trusted-source weighting</li>
              <li><span className="dot"/>API access for pipelines</li>
            </ul>
            <div className="auth-trust mono">
              <span>· SOC 2 Type II</span><span>· No retention</span><span>· Open models</span>
            </div>
          </div>

          <div className="auth-card">
            <div className="auth-tabs">
              <button className={isLogin?"active":""} onClick={()=>setMode("login")}>Sign in</button>
              <button className={!isLogin?"active":""} onClick={()=>setMode("register")}>Create account</button>
              <div className="auth-tab-pill" style={{ left: isLogin?4:"50%", width: "calc(50% - 4px)"}}/>
            </div>

            <h3 className="display">{isLogin?"Welcome back.":"Create your account."}</h3>
            <p className="auth-sub">{isLogin?"Sign in to continue to DeepShield.":"Start analyzing media in under a minute."}</p>

            <div className="auth-social">
              <button className="btn btn-glass btn-sm"><span className="mono">G</span> Google</button>
              <button className="btn btn-glass btn-sm"><span className="mono">◎</span> GitHub</button>
              <button className="btn btn-glass btn-sm"><span className="mono">⎆</span> SSO</button>
            </div>
            <div className="auth-divider"><span>or with email</span></div>

            <form className="auth-form" onSubmit={e=>{e.preventDefault(); window.location.href="History.html";}}>
              {!isLogin && (
                <label className="field">
                  <span>Full name</span>
                  <input type="text" value={name} onChange={e=>setName(e.target.value)} placeholder="Priya Sharma" />
                </label>
              )}
              <label className="field">
                <span>Email</span>
                <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@org.com" required />
              </label>
              <label className="field">
                <span>Password {isLogin && <a className="field-aux">Forgot?</a>}</span>
                <input type="password" value={pw} onChange={e=>setPw(e.target.value)} placeholder={isLogin?"••••••••":"min 10 characters"} required />
                {!isLogin && pw.length > 0 && (
                  <div className="pw-meter">
                    <i style={{ width: `${Math.min(100, pw.length*10)}%`, background: pw.length<6?"var(--ds-danger)":pw.length<10?"var(--ds-warn)":"var(--ds-safe)" }}/>
                    <span className="mono">{pw.length<6?"weak":pw.length<10?"fair":"strong"}</span>
                  </div>
                )}
              </label>
              {isLogin ? (
                <label className="check-row">
                  <input type="checkbox" checked={remember} onChange={e=>setRemember(e.target.checked)} />
                  <span>Keep me signed in for 30 days</span>
                </label>
              ) : (
                <label className="check-row">
                  <input type="checkbox" defaultChecked />
                  <span>I agree to the <a>Terms</a> and <a>Privacy Policy</a></span>
                </label>
              )}
              <button type="submit" className="btn btn-primary btn-lg btn-shiny" style={{width:"100%"}}>
                {isLogin?"Sign in":"Create account"} →
              </button>
            </form>

            <p className="auth-foot">
              {isLogin?"New to DeepShield? ":"Have an account? "}
              <a onClick={()=>setMode(isLogin?"register":"login")} style={{cursor:"pointer"}}>{isLogin?"Create account":"Sign in"}</a>
            </p>
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}

window.AuthApp = AuthApp;
function mountAuth(mode) {
  if (window.DSShared) ReactDOM.createRoot(document.getElementById("root")).render(<AuthApp mode={mode} />);
  else setTimeout(()=>mountAuth(mode), 50);
}
window.mountAuth = mountAuth;
