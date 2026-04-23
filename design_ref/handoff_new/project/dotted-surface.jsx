// Animated dotted surface — rendered via canvas, fixed behind page content
// Inspired by 21st.dev/community/components/efferd/dotted-surface
// Single waveform across a dot field, drifting with time + subtle mouse parallax.

(function () {
  function DottedSurface({
    dotColor = "rgba(255,255,255,0.42)",
    dotSize = 1.1,
    gap = 18,
    waveAmp = 8,
    waveSpeed = 0.00055,
    waveLen = 180,
  } = {}) {
    const ref = React.useRef(null);
    const raf = React.useRef(null);
    const mouse = React.useRef({ x: 0, y: 0, tx: 0, ty: 0 });

    React.useEffect(() => {
      const canvas = ref.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      let dpr = Math.min(window.devicePixelRatio || 1, 2);
      let W = 0, H = 0;

      const resize = () => {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        const rect = canvas.getBoundingClientRect();
        W = rect.width; H = rect.height;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      };
      resize();
      window.addEventListener("resize", resize);

      const onMove = (e) => {
        mouse.current.tx = (e.clientX / window.innerWidth - 0.5) * 2;
        mouse.current.ty = (e.clientY / window.innerHeight - 0.5) * 2;
      };
      window.addEventListener("pointermove", onMove, { passive: true });

      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const draw = (t) => {
        ctx.clearRect(0, 0, W, H);
        // ease mouse
        mouse.current.x += (mouse.current.tx - mouse.current.x) * 0.04;
        mouse.current.y += (mouse.current.ty - mouse.current.y) * 0.04;
        const mx = mouse.current.x * 14;
        const my = mouse.current.y * 10;

        const cols = Math.ceil(W / gap) + 2;
        const rows = Math.ceil(H / gap) + 2;

        // center of wave travels diagonally
        const cx = W * 0.3 + Math.sin(t * waveSpeed * 0.7) * W * 0.4;
        const cy = H * 0.55 + Math.cos(t * waveSpeed * 0.5) * H * 0.25;

        for (let j = 0; j < rows; j++) {
          for (let i = 0; i < cols; i++) {
            const x0 = i * gap - gap/2 + mx * 0.3;
            const y0 = j * gap - gap/2 + my * 0.3;

            // distance from moving center
            const dx = x0 - cx;
            const dy = y0 - cy;
            const d = Math.sqrt(dx*dx + dy*dy);

            // sinusoidal wave + time phase
            const phase = reduced ? 0 : (d / waveLen) - t * waveSpeed * 2.2;
            const offset = reduced ? 0 : Math.sin(phase) * waveAmp;

            // radial fade — dots fade as they get further from center
            const fade = Math.max(0, 1 - d / (Math.max(W, H) * 0.8));
            const alpha = (0.15 + fade * 0.75) * (reduced ? 0.6 : 1);

            // perspective tilt: y-offset grows with depth
            const y = y0 + offset * 0.9;
            const x = x0 + offset * 0.25;

            // hue shift near wave peak
            const peak = Math.max(0, (Math.sin(phase) + 1) * 0.5);
            const size = dotSize + peak * 1.1;

            ctx.beginPath();
            if (peak > 0.78) {
              // rare tinted highlight
              ctx.fillStyle = `rgba(127, 143, 255, ${alpha * (0.4 + peak*0.3)})`;
            } else {
              ctx.fillStyle = dotColor.replace(/[\d.]+\)$/, `${alpha.toFixed(3)})`);
            }
            ctx.arc(x, y, size, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        raf.current = requestAnimationFrame(draw);
      };
      raf.current = requestAnimationFrame(draw);

      return () => {
        cancelAnimationFrame(raf.current);
        window.removeEventListener("resize", resize);
        window.removeEventListener("pointermove", onMove);
      };
    }, [dotColor, dotSize, gap, waveAmp, waveSpeed, waveLen]);

    return React.createElement("canvas", {
      ref: ref,
      className: "ds-dotted-surface",
      "aria-hidden": "true",
    });
  }

  window.DottedSurface = DottedSurface;

  // auto-mount if container exists
  function autoMount() {
    const host = document.getElementById("ds-bg-surface");
    if (host && !host.dataset.mounted) {
      host.dataset.mounted = "1";
      ReactDOM.createRoot(host).render(React.createElement(DottedSurface));
    }
  }
  window.DottedSurfaceMount = autoMount;
  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(autoMount, 0);
  } else {
    document.addEventListener("DOMContentLoaded", autoMount);
  }
})();
