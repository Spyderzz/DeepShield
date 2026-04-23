// Dotted Surface — three.js version, matching 21st.dev/efferd/dotted-surface
// 40×60 grid of points on a ground plane, camera angled down, two sine waves animate Y.
(function () {
  const SEPARATION = 150;
  const AMOUNTX = 40;
  const AMOUNTY = 60;

  function mount(container, { theme = "dark" } = {}) {
    if (!window.THREE) {
      console.warn("three.js not loaded");
      return () => {};
    }
    const THREE = window.THREE;

    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x000000, 2000, 10000);

    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 10000);
    camera.position.set(0, 355, 1220);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const positions = [];
    const colors = [];
    const geometry = new THREE.BufferGeometry();

    const dotColor = theme === "light" ? [20, 24, 40] : [200, 205, 220];

    for (let ix = 0; ix < AMOUNTX; ix++) {
      for (let iy = 0; iy < AMOUNTY; iy++) {
        const x = ix * SEPARATION - (AMOUNTX * SEPARATION) / 2;
        const y = 0;
        const z = iy * SEPARATION - (AMOUNTY * SEPARATION) / 2;
        positions.push(x, y, z);
        colors.push(dotColor[0], dotColor[1], dotColor[2]);
      }
    }

    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 8,
      vertexColors: true,
      transparent: true,
      opacity: theme === "light" ? 0.55 : 0.8,
      sizeAttenuation: true,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    let count = 0;
    let animationId;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const positionAttribute = geometry.attributes.position;
      const posArr = positionAttribute.array;
      let i = 0;
      for (let ix = 0; ix < AMOUNTX; ix++) {
        for (let iy = 0; iy < AMOUNTY; iy++) {
          const index = i * 3;
          posArr[index + 1] =
            Math.sin((ix + count) * 0.3) * 50 +
            Math.sin((iy + count) * 0.5) * 50;
          i++;
        }
      }
      positionAttribute.needsUpdate = true;
      renderer.render(scene, camera);
      if (!reduced) count += 0.1;
    };

    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("resize", onResize);

    // theme update API
    const setTheme = (newTheme) => {
      const nextColor = newTheme === "light" ? [20, 24, 40] : [200, 205, 220];
      const colorAttr = geometry.attributes.color;
      const arr = colorAttr.array;
      for (let i = 0; i < arr.length; i += 3) {
        arr[i] = nextColor[0]; arr[i+1] = nextColor[1]; arr[i+2] = nextColor[2];
      }
      colorAttr.needsUpdate = true;
      material.opacity = newTheme === "light" ? 0.55 : 0.8;
    };

    animate();

    return {
      setTheme,
      destroy() {
        cancelAnimationFrame(animationId);
        window.removeEventListener("resize", onResize);
        scene.traverse(obj => {
          if (obj instanceof THREE.Points) {
            obj.geometry.dispose();
            if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
            else obj.material.dispose();
          }
        });
        renderer.dispose();
        if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    };
  }

  window.DottedSurface3D = { mount };

  // Auto-mount the legacy #ds-bg-surface host if it exists and three.js is loaded.
  function autoMount() {
    const host = document.getElementById("ds-bg-surface");
    if (!host || host.dataset.mounted) return;
    if (!window.THREE) {
      // retry once three loads
      setTimeout(autoMount, 100);
      return;
    }
    host.dataset.mounted = "1";
    const inst = mount(host, { theme: "dark" });
    window.__dotsInstance = inst;
  }
  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(autoMount, 0);
  } else {
    document.addEventListener("DOMContentLoaded", autoMount);
  }
})();
