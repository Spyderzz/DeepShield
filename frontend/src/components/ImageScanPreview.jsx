import React from 'react';
import '../pages/deepshield-landing.css';

export default function ImageScanPreview({ size = 320 }) {
  return (
    <div className="mv-image-scan" style={{ width: size, height: Math.round(size * 0.65), borderRadius: 'inherit' }}>
      <svg className="face-scan-svg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
        <path className="face-outline" d="M30,20 C45,10 55,10 70,20 C85,45 75,70 60,90 C50,90 40,90 25,70 C15,45 30,20 Z" />
        <path className="face-wire" d="M30,20 L70,20 M25,45 L75,45 M25,70 L60,90 M50,10 L50,90" />
        <path className="face-wire" d="M30,20 L50,45 L70,20 M25,45 L50,70 L75,45" />
        
        <circle className="face-node" cx="30" cy="20" r="1.5" />
        <circle className="face-node active" cx="70" cy="20" r="1.5" />
        <circle className="face-node" cx="25" cy="45" r="1.5" />
        <circle className="face-node" cx="50" cy="45" r="1.5" />
        <circle className="face-node active" cx="75" cy="45" r="1.5" />
        <circle className="face-node" cx="25" cy="70" r="1.5" />
        <circle className="face-node" cx="50" cy="70" r="1.5" />
        <circle className="face-node" cx="60" cy="90" r="1.5" />
        <circle className="face-node active" cx="40" cy="90" r="1.5" />
      </svg>
      <div className="scan-line-v"></div>
      <div className="scan-highlight-box"></div>
    </div>
  );
}
