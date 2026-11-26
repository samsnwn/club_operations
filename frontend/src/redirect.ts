// Validates the `?redirect=` value used after sign-in. It imports nothing and
// uses only erasable syntax, so Node can check it directly (see README).

const BASE = 'http://x.invalid';

/**
 * Returns `value` when it is a same-origin path such as `/invoices?x=1`, and
 * `/` otherwise, so a crafted link can never send the user to another site.
 */
export function safeRedirect(value: unknown): string {
  if (typeof value !== 'string') return '/';
  if (value[0] !== '/' || value[1] === '/' || value[1] === '\\') return '/';
  for (const char of value) {
    const code = char.charCodeAt(0);
    if (char === '\\' || code <= 0x20 || code === 0x7f || /\s/.test(char)) {
      return '/';
    }
  }
  try {
    const url = new URL(value, BASE);
    if (url.origin !== BASE) return '/';
    // Dot segments can collapse into `//host` (e.g. `/..//evil.com`), which
    // a later consumer could read as protocol-relative.
    if (url.pathname.startsWith('//')) return '/';
  } catch {
    return '/';
  }
  return value;
}
