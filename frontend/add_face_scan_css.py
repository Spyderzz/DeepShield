css_to_add = """
/* Image Deepfake Detection Face Scan */
.mv-image-scan {
  position: relative;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 50% 50%, #151a28, #0a0d14);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.face-scan-svg {
  width: 60%;
  height: 60%;
  filter: drop-shadow(0 0 10px rgba(108,125,255,0.3));
}
.face-outline {
  fill: none;
  stroke: rgba(108,125,255,0.6);
  stroke-width: 1.5;
  stroke-dasharray: 300;
  stroke-dashoffset: 300;
  animation: drawOutline 4s linear infinite;
}
.face-wire {
  fill: none;
  stroke: rgba(108,125,255,0.2);
  stroke-width: 0.8;
}
.face-node {
  fill: rgba(108,125,255,0.4);
}
.face-node.active {
  fill: var(--ds-danger);
  animation: nodePulse 2s infinite;
}
.scan-line-v {
  position: absolute;
  top: 0; bottom: 0;
  width: 2px;
  background: var(--ds-brand-2);
  box-shadow: 0 0 15px 2px var(--ds-brand-2);
  left: 0;
  animation: scanHoriz 3s ease-in-out infinite;
}
.scan-highlight-box {
  position: absolute;
  border: 1px dashed var(--ds-danger);
  background: rgba(255,94,122,0.15);
  width: 16px; height: 16px;
  top: 45%; left: 75%;
  transform: translate(-50%, -50%);
  animation: scanBoxAnim 3s infinite;
}

@keyframes drawOutline {
  0% { stroke-dashoffset: 300; }
  40% { stroke-dashoffset: 0; }
  60% { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: -300; }
}
@keyframes nodePulse {
  0%, 100% { r: 1.5; filter: drop-shadow(0 0 2px var(--ds-danger)); opacity: 0.5; }
  50% { r: 3; filter: drop-shadow(0 0 8px var(--ds-danger)); opacity: 1; }
}
@keyframes scanHoriz {
  0% { left: 10%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: 90%; opacity: 0; }
}
@keyframes scanBoxAnim {
  0%, 40% { opacity: 0; transform: translate(-50%, -50%) scale(1.5); }
  50%, 80% { opacity: 1; transform: translate(-50%, -50%) scale(1); box-shadow: 0 0 10px rgba(255,94,122,0.5); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(1); }
}
"""

path = "src/pages/deepshield-landing.css"
with open(path, "a", encoding="utf-8") as f:
    f.write("\n" + css_to_add)
