function AboutApp() {
  const { SharedNav, SharedFooter } = window.DSShared;
  const team = [
    { n:"Arjun Mehta", r:"Forensic ML lead", bio:"PhD in computer vision, ex-Meta Integrity.", init:"AM" },
    { n:"Priya Sharma", r:"Research, NLP", bio:"Led XLM-R fine-tuning for low-resource Indian languages.", init:"PS" },
    { n:"Rohan Iyer", r:"Systems", bio:"Built the caching layer and on-device inference.", init:"RI" },
    { n:"Diya Krishnan", r:"Policy + partnerships", bio:"Works with Indian newsrooms on verification workflows.", init:"DK" },
  ];
  const partners = ["Reuters","AP","AltNews","BoomLive","The Hindu","PTI","BBC","NDTV","AFP","ANI"];
  return (
    <>
      <SharedNav current="about" />
      <section className="page-shell about-shell">
        <div className="page-head">
          <div className="crumbs"><a href="DeepShield.html">Home</a><span className="sep">/</span><span>About</span></div>
          <span className="eyebrow">Our mission</span>
          <h1 className="display" style={{maxWidth:900}}>We believe the <em className="italic accent">truth</em> still deserves a fighting chance.</h1>
          <p className="sub" style={{maxWidth:640}}>DeepShield is a forensic AI system built for journalists, fact-checkers, and everyday readers. We don't chase virality. We ship evidence — layered, open, and auditable.</p>
        </div>

        <div className="about-wrap">
          <div className="about-manifesto">
            <span className="eyebrow">Manifesto</span>
            <div className="manifesto-grid">
              <h2 className="display italic">Speed + calm.</h2>
              <p>Fake media moves fast. So do we — but never at the cost of clarity. Every verdict comes with layered evidence: model confidence, visual heatmaps, EXIF fingerprints, and human-readable summaries.</p>
              <h2 className="display italic">Open + local.</h2>
              <p>We run open-source models where we can — EfficientNetAutoAttB4, XLM-RoBERTa, Wav2Lip, WavLM. On-device inference for sensitive uploads. No retention by default. Your media is yours.</p>
              <h2 className="display italic">Plural + Indian-first.</h2>
              <p>Built for Indian newsrooms and linguistic realities — Hindi, Tamil, Bengali, Marathi, English. Trusted-source lists include AltNews, BoomLive, PTI, The Hindu, alongside global wires.</p>
            </div>
          </div>

          <div className="about-metrics">
            <span className="eyebrow">Numbers that matter</span>
            <div className="metric-row">
              <div><b className="display">12</b><span>open models composed</span></div>
              <div><b className="display italic accent">91%</b><span>detection accuracy (DFDC)</span></div>
              <div><b className="display">2.14<em style={{fontSize:"0.5em",color:"var(--ds-muted)"}}>s</em></b><span>median latency (cached)</span></div>
              <div><b className="display">11</b><span>languages supported</span></div>
            </div>
          </div>

          <div className="about-team">
            <span className="eyebrow">Team</span>
            <h2 className="display">A small, opinionated team.</h2>
            <div className="team-grid">
              {team.map(t=>(
                <div key={t.n} className="team-card">
                  <div className="team-avatar">{t.init}</div>
                  <h4>{t.n}</h4>
                  <p className="mono team-role">{t.r}</p>
                  <p className="team-bio">{t.bio}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="about-partners">
            <span className="eyebrow">Trusted source partners</span>
            <div className="partners-marquee">
              <div className="pm-track">
                {[...partners, ...partners, ...partners].map((p,i)=>(
                  <span key={i} className="partner-chip display italic">{p}</span>
                ))}
              </div>
            </div>
          </div>

          <div className="about-cta">
            <h2 className="display italic">Build with us.</h2>
            <p>We're hiring ML engineers, designers, and policy researchers who care about information integrity.</p>
            <div style={{display:"flex", gap:12, justifyContent:"center", marginTop:28}}>
              <a href="Analyze.html" className="btn btn-primary btn-lg btn-shiny" style={{textDecoration:"none"}}>Try DeepShield →</a>
              <a className="btn btn-glass btn-lg" style={{textDecoration:"none"}}>Open roles ↗</a>
            </div>
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}

function mountAbout() {
  if (window.DSShared) ReactDOM.createRoot(document.getElementById("root")).render(<AboutApp />);
  else setTimeout(mountAbout, 50);
}
window.mountAbout = mountAbout;
