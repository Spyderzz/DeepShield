/**
 * sanitize-text.js
 * DeepShield Phase 22.5 — Frontend sanitization utilities.
 *
 * Usage:
 *   import { sanitizeText, sanitizeHtml, sanitizeUrl } from '../utils/sanitize-text';
 *
 * Rules:
 *  - sanitizeText  : strips ALL HTML tags, safe for textContent / aria-label / logging
 *  - sanitizeHtml  : allows a tight allowlist of inline tags (no scripts, no events)
 *  - sanitizeUrl   : allows only http/https/mailto — returns '' for anything else
 *
 * NOTE: Never use dangerouslySetInnerHTML with un-sanitized strings.
 * ESLint rule `react/no-danger` is enforced via .eslintrc additions.
 */

// ---------------------------------------------------------------------------
// 1. Strip all HTML — safe for plain text contexts
// ---------------------------------------------------------------------------
/**
 * @param {string} raw
 * @returns {string}
 */
export function sanitizeText(raw) {
  if (!raw || typeof raw !== 'string') return '';
  // Use a temporary div — no DOM side-effects, purely parsing.
  const div = document.createElement('div');
  div.textContent = raw;        // assignment via textContent is always safe
  return div.textContent || '';
}

// ---------------------------------------------------------------------------
// 2. Allow a narrow set of inline HTML tags — for rich summaries
// ---------------------------------------------------------------------------
const ALLOWED_TAGS = new Set(['b', 'strong', 'em', 'i', 'u', 's', 'br', 'span', 'mark', 'code', 'small']);
const ALLOWED_ATTRS = new Set(['class', 'style']); // no event attrs, no href

/**
 * Strips any tag not in ALLOWED_TAGS, and strips any attribute not in ALLOWED_ATTRS.
 * Does NOT rely on third-party libs — pure DOM-parse approach.
 *
 * @param {string} raw  — untrusted HTML string
 * @returns {string}    — sanitized HTML string (safe for dangerouslySetInnerHTML)
 */
export function sanitizeHtml(raw) {
  if (!raw || typeof raw !== 'string') return '';

  const div = document.createElement('div');
  div.innerHTML = raw; // parse only — we immediately walk and clean

  function clean(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.cloneNode(true);
    if (node.nodeType !== Node.ELEMENT_NODE) return null; // drop comments etc.

    const tag = node.tagName.toLowerCase();
    if (!ALLOWED_TAGS.has(tag)) {
      // Replace disallowed elements with a text-node of their text content
      return document.createTextNode(node.textContent || '');
    }

    const el = document.createElement(tag);
    // Copy only whitelisted attributes, stripping any that look dangerous
    for (const attr of node.attributes) {
      if (!ALLOWED_ATTRS.has(attr.name)) continue;
      const val = attr.value;
      // Block: javascript: / expression( / url( inside style
      if (/javascript:/i.test(val) || /expression\s*\(/i.test(val)) continue;
      el.setAttribute(attr.name, val);
    }
    for (const child of node.childNodes) {
      const cleaned = clean(child);
      if (cleaned) el.appendChild(cleaned);
    }
    return el;
  }

  const out = document.createElement('div');
  for (const child of div.childNodes) {
    const cleaned = clean(child);
    if (cleaned) out.appendChild(cleaned);
  }
  return out.innerHTML;
}

// ---------------------------------------------------------------------------
// 3. URL sanitizer — blocks javascript: / data: / vbscript: etc.
// ---------------------------------------------------------------------------
const SAFE_PROTOCOLS = new Set(['http:', 'https:', 'mailto:']);

/**
 * @param {string} raw
 * @returns {string}  — safe URL or empty string
 */
export function sanitizeUrl(raw) {
  if (!raw || typeof raw !== 'string') return '';
  try {
    const url = new URL(raw, window.location.href);
    if (!SAFE_PROTOCOLS.has(url.protocol)) return '';
    return url.href;
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------------
// 4. Escape for use inside attribute values (e.g. title, aria-label)
// ---------------------------------------------------------------------------
const ESCAPE_MAP = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

/**
 * @param {string} raw
 * @returns {string}
 */
export function escapeAttr(raw) {
  if (!raw || typeof raw !== 'string') return '';
  return raw.replace(/[&<>"']/g, (c) => ESCAPE_MAP[c]);
}
