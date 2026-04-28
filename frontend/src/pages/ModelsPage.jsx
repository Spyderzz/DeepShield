import { useRef, useEffect } from 'react';
import { SharedNav, SharedFooter } from '../components/layout/SharedNav.jsx';
import useDottedSurface from '../hooks/useDottedSurface.js';
import './deepshield-landing.css';
import './deepshield-pages.css';
import './models-page.css';

const MODELS = [
  {
    type: 'Vision / Spatial',
    title: 'DeepShield-ViT',
    desc: 'Fine-tuned Vision Transformer (ViT) hardened on FaceForensics++. Extracts spatial inconsistencies, blending boundaries, and noise residuals via multi-head self-attention mechanisms.',
    acc: '94.8%',
    param: '86M',
  },
  {
    type: 'Audio / Voice',
    title: 'WavLM / wav2vec2',
    desc: 'Self-supervised acoustic models trained on ASVspoof. Processes raw waveforms to detect spectral variance, zero-crossing anomalies, and synthesized voiceprints indicative of AI cloning.',
    acc: '91.3%',
    param: '316M',
  },
  {
    type: 'NLP / Linguistic',
    title: 'Multilingual BERT / XLM-R',
    desc: 'Text credibility classifier handling English and Hindi. Performs Named Entity Recognition (NER), analyzes sensationalism, perplexity bursts, and semantic manipulation.',
    acc: '92.7%',
    param: '278M',
  },
  {
    type: 'Computer Vision',
    title: 'EasyOCR (CRAFT + CRNN)',
    desc: 'Optical Character Recognition pipeline using CRAFT for text detection and CRNN for recognition. Identifies edited overlays, tampered UI, and layout anomalies in social media screenshots.',
    acc: '96.1%',
    param: '20M',
  },
  {
    type: 'Orchestrator & VLM',
    title: 'Gemini 1.5 Flash',
    desc: 'The multimodal reasoning engine. Synthesizes raw tensors and anomaly maps from specialist models into executive-level, plain-English forensic summaries and granular component scores.',
    acc: 'N/A',
    param: 'API',
  }
];

function TiltCard({ model }) {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Update CSS vars for the glow effect
    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);

    // Calculate 3D tilt
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -8; // Max 8 deg rotation
    const rotateY = ((x - centerX) / centerX) * 8;
    
    cardRef.current.style.transform = `perspective(1500px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
  };

  const handleMouseLeave = () => {
    if (!cardRef.current) return;
    cardRef.current.style.transform = `perspective(1500px) rotateX(0deg) rotateY(0deg)`;
  };

  return (
    <div className="model-card-wrapper">
      <div 
        ref={cardRef}
        className="model-card"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div className="mc-content">
          <span className="mc-type">{model.type}</span>
          <h3 className="mc-title display" style={{ fontSize: '32px' }}>{model.title}</h3>
          <p className="mc-desc">{model.desc}</p>
          <div className="mc-stats">
            <div className="mc-stat">
              <span className="mc-stat-val">{model.acc}</span>
              <span className="mc-stat-label">Accuracy</span>
            </div>
            <div className="mc-stat">
              <span className="mc-stat-val">{model.param}</span>
              <span className="mc-stat-label">Parameters</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ModelsPage() {
  useDottedSurface();

  return (
    <>
      <SharedNav current="models" />
      <div className="page-shell models-shell">
        <div className="models-header">
          <span className="eyebrow">Architecture</span>
          <h1 className="display">Ensemble Intelligence.</h1>
          <p className="sub">
            DeepShield isn't a single monolithic black box. It is a highly specialized ensemble of state-of-the-art 
            vision, audio, and language models working in concert to tear apart synthetic media.
          </p>
        </div>

        <div className="models-grid">
          {MODELS.map((m, i) => <TiltCard key={i} model={m} />)}
        </div>

        <div className="datasets-section ds-container">
          <span className="eyebrow">Ground Truth</span>
          <h2 className="display italic">FaceForensics++</h2>
          <p className="sub" style={{ maxWidth: 600 }}>
            To catch the best deepfakes, you have to train on them. Our core visual engine is 
            hardened against the industry-standard FaceForensics++ dataset.
          </p>
          
          <div className="dataset-row">
            <div className="dataset-visual">
              <img src="https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=1200&q=80" alt="FaceForensics Visualizer" />
              <div className="dataset-overlay">
                <code>1,000+ sequences / 4 manipulation methods</code>
              </div>
            </div>
            <div className="dataset-info">
              <h3>Comprehensive Coverage</h3>
              <p style={{ color: 'var(--ds-ink-2)', lineHeight: 1.6, marginBottom: 20 }}>
                The dataset includes pristine, unmanipulated source videos alongside identically compressed 
                fake counterparts generated via four distinct state-of-the-art methods:
              </p>
              <ul style={{ color: 'var(--ds-ink-2)', lineHeight: 1.8, paddingLeft: 20 }}>
                <li><strong>Deepfakes:</strong> Autoencoder-based face replacement.</li>
                <li><strong>Face2Face:</strong> Real-time facial reenactment.</li>
                <li><strong>FaceSwap:</strong> Graphics-based face transfer.</li>
                <li><strong>NeuralTextures:</strong> GAN-based lip manipulation.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <SharedFooter />
    </>
  );
}
