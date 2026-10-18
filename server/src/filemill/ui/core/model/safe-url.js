/* The protocols a preview may link to (A2); a scheme-less address resolves
   against the page, so it may stay too. Browsers drop tabs, newlines and
   leading controls before they read a scheme, so the literal value is tested:
   one that does not start with a listed protocol must have no colon before its
   first slash, query or fragment, or a browser may read any scheme there.
   server/src/filemill/preview.py holds the server's copy of this rule. */
export const SAFE_PROTOCOLS = ["http:", "https:", "mailto:"];

export const safeURL = (url) =>
  SAFE_PROTOCOLS.some((p) => url.toLowerCase().startsWith(p)) ||
  !/^[^/?#]*:/.test(url);
