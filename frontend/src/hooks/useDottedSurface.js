import { useEffect } from 'react';

/**
 * Ensures the dotted three.js background is active while this page is mounted.
 *
 * #ds-bg-surface and dotted-surface.js are declared once in index.html so the
 * host survives route changes. This hook just (a) toggles body.ds-page so
 * pages.css z-index rules apply, and (b) makes sure a three.js instance is
 * actually mounted on the host — retrying a few times because the `three`
 * CDN + dotted-surface.js scripts may not have finished loading yet.
 */
export default function useDottedSurface({ theme = 'dark' } = {}) {
  useEffect(() => {
    const body = document.body;
    body.classList.add('ds-page');

    let host = document.getElementById('ds-bg-surface');
    if (!host) {
      host = document.createElement('div');
      host.id = 'ds-bg-surface';
      document.body.insertBefore(host, document.body.firstChild);
    }

    // Clear "mounted" marker if the canvas is gone (eg. previous page destroyed it)
    if (host.dataset.mounted && !host.querySelector('canvas')) {
      delete host.dataset.mounted;
      window.__dotsInstance = null;
    }

    let cancelled = false;
    const ensureMounted = (tries = 0) => {
      if (cancelled) return;
      if (window.__dotsInstance && host.querySelector('canvas')) {
        if (window.__dotsInstance.setTheme) window.__dotsInstance.setTheme(theme);
        window.__lastTheme = theme;
        return;
      }
      if (window.DottedSurface3D && window.THREE) {
        try {
          host.dataset.mounted = '1';
          window.__dotsInstance = window.DottedSurface3D.mount(host, { theme });
          window.__lastTheme = theme;
        } catch (_e) { /* swallow and retry */ }
        return;
      }
      if (tries < 40) setTimeout(() => ensureMounted(tries + 1), 100);
    };
    ensureMounted();

    return () => {
      cancelled = true;
      body.classList.remove('ds-page');
      // Intentionally do NOT destroy __dotsInstance here — the host is global and
      // reused across pages. Destroying would cause the exact "blank background on
      // navigation" bug we're fixing.
    };
  }, [theme]);
}
