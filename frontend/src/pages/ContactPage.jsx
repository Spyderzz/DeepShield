import { useNavigate } from 'react-router-dom';
import { SharedNav, SharedFooter } from '../components/layout/SharedNav.jsx';
import useDottedSurface from '../hooks/useDottedSurface.js';
import './deepshield-landing.css';
import './deepshield-pages.css';

export default function ContactPage() {
  useDottedSurface();
  const navigate = useNavigate();

  return (
    <>
      <SharedNav current="contact" />
      <section className="page-shell about-shell">
        <div className="page-head">
          <div className="crumbs">
            <a onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Home</a>
            <span className="sep">/</span>
            <span>Contact</span>
          </div>
          <span className="eyebrow">Get in touch</span>
          <h1 className="display" style={{ maxWidth: 900 }}>Reach out. Let's build the <em className="italic accent">future of trust</em> together.</h1>
          <p className="sub" style={{ maxWidth: 640 }}>
            Whether you are a journalist looking to integrate DeepShield into your newsroom, a researcher wanting to collaborate, or just want to say hi — we'd love to hear from you.
          </p>
        </div>

        <div className="about-wrap">
          <div className="about-manifesto">
            <span className="eyebrow">Direct Contact</span>
            <div className="manifesto-grid" style={{ gridTemplateColumns: '1fr', gap: '32px' }}>
              <div>
                <h2 className="display italic" style={{ fontSize: '2.5rem' }}>GitHub</h2>
                <p>Check out our open source repositories, report issues, or contribute directly to the DeepShield core engine.</p>
                <a href="https://github.com/Spyderzz" target="_blank" rel="noreferrer" className="btn btn-primary btn-shiny" style={{ marginTop: '16px', textDecoration: 'none', display: 'inline-block' }}>Visit GitHub →</a>
              </div>
              
              <div>
                <h2 className="display italic" style={{ fontSize: '2.5rem' }}>Email</h2>
                <p>For partnership inquiries, deployment support, and press, please reach out to our team directly via email.</p>
                <a href="mailto:deepshield@ar07xd.com" className="btn btn-glass" style={{ marginTop: '16px', textDecoration: 'none', display: 'inline-block' }}>deepshield@ar07xd.com ↗</a>
              </div>
            </div>
          </div>

          <div className="about-metrics" style={{ marginTop: '120px' }}>
            <span className="eyebrow">Headquarters</span>
            <div className="metric-row" style={{ gridTemplateColumns: '1fr' }}>
              <div>
                <b className="display">New Delhi, India</b>
                <span>28°37′47.3″N 77°2′20.2″E</span>
              </div>
            </div>
          </div>

          <div className="about-cta" style={{ marginTop: '120px' }}>
            <h2 className="display italic">Ready to deploy?</h2>
            <p>Start verifying synthetic media in seconds with our highly accurate, explainable pipeline.</p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 28 }}>
              <a onClick={() => navigate('/analyze')} className="btn btn-primary btn-lg btn-shiny" style={{ textDecoration: 'none', cursor: 'pointer' }}>Run analysis →</a>
            </div>
          </div>
        </div>
      </section>
      <SharedFooter />
    </>
  );
}
