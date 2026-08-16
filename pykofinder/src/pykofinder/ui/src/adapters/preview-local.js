/* ═══════════════════════════════════════════════════════════════════════════
   Preview provider — in-browser, zero dependencies.

   Fills the PREVIEW port (see core/ports.js). Everything here works from the
   bytes alone, so it costs nothing in the bundle and works with no network:

     images   → object URL
     PDF      → object URL in an <iframe>; Chromium renders it natively, so a
                PDF viewer is not something this has to carry
     .desktop → the same link card the server build shows, parsed in 20 lines
     text     → escaped <pre>, clipped

   Rich rendering (Markdown, syntax highlighting, docx, pptx) is a *different
   provider*, not a bigger version of this one: see preview-http.js for the
   server-rendered variant, and the "full" build profile for a bundled one.
   ═══════════════════════════════════════════════════════════════════════════ */
const TEXT_RE = /\.(txt|md|markdown|log|json|jsonc|ya?ml|toml|ini|cfg|conf|csv|tsv|xml|svg|html?|css|scss|less|js|mjs|cjs|jsx|ts|tsx|py|rb|rs|go|java|kt|c|h|cpp|hpp|cs|sh|bash|zsh|fish|sql|nix|lua|php|pl|swift|r|tex|gitignore|env)$/i;
const IMG_RE  = /\.(png|jpe?g|gif|webp|avif|bmp|ico|svg)$/i;
const TEXT_MAX = 512 * 1024, TEXT_CHARS = 8000;

let pvURL = null;

/* .desktop is an INI file; only Type=Link entries have anything to show. */
function desktopCard(text) {
  const e = {};
  let inEntry = false;
  for (const line of text.split(/\r?\n/)) {
    const s = line.trim();
    if (s.startsWith("[")) { inEntry = s === "[Desktop Entry]"; continue; }
    if (!inEntry || !s || s.startsWith("#")) continue;
    const i = s.indexOf("=");
    if (i > 0) e[s.slice(0, i).trim()] = s.slice(i + 1).trim();
  }
  if (e.Type !== "Link" || !e.URL) return null;
  const url = esc(e.URL);
  return `<div class="pv-link">
      <h3>${esc(e.Name || "")}</h3>
      ${e.Comment ? `<p class="sub">${esc(e.Comment)}</p>` : ""}
      <p>🔗 <a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a></p>
    </div>`;
}

const PreviewLocal = {
  revoke() { if (pvURL) { URL.revokeObjectURL(pvURL); pvURL = null; } },

  async render(node) {
    const blob = await FS.blob(node);
    if (!blob) return null;

    if (IMG_RE.test(node.name)) {
      pvURL = URL.createObjectURL(blob);
      return `<img class="pv-img" src="${pvURL}" alt="">`;
    }
    if (/\.pdf$/i.test(node.name)) {
      pvURL = URL.createObjectURL(blob.slice(0, blob.size, "application/pdf"));
      return `<iframe class="pv-pdf" src="${pvURL}" title="${esc(node.name)}"></iframe>`;
    }
    if (/\.desktop$/i.test(node.name) && blob.size <= TEXT_MAX)
      return desktopCard(await blob.text()) ?? null;

    if (TEXT_RE.test(node.name) && blob.size <= TEXT_MAX) {
      const text = await blob.slice(0, TEXT_MAX).text();
      const clipped = text.length > TEXT_CHARS;
      return `<pre class="pv-text">${esc(text.slice(0, TEXT_CHARS))}${clipped ? "\n…" : ""}</pre>`;
    }
    return null;
  },
};
