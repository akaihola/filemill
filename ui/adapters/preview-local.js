/* ═══════════════════════════════════════════════════════════════════════════
   Preview provider — in-browser, zero dependencies.

   Fills the PREVIEW port (see core/ports.js). Everything here works from the
   bytes alone, so it costs nothing in the bundle and works with no network:

     images   → object URL
     PDF      → object URL in an <iframe>; Chromium renders it natively, so a
                PDF viewer is not something this has to carry
     .desktop → the same link card the server build shows, parsed in 20 lines
     text     → escaped <pre>, whole, and coloured by core/syntax.js when
                the extension names a language it knows. TEXT_MAX is the only
                limit: what is previewed at all is previewed entire

   Rich rendering (Markdown, docx, pptx) is a *different provider*, not a
   bigger version of this one: see preview-http.js for the server-rendered
   variant, and preview-rich.js for the downloaded one.
   ═══════════════════════════════════════════════════════════════════════════ */
const TEXT_RE = /\.(txt|md|markdown|log|json|jsonc|ya?ml|toml|ini|cfg|conf|csv|tsv|xml|svg|css|scss|less|js|mjs|cjs|jsx|ts|tsx|py|rb|rs|go|java|kt|c|h|cpp|hpp|cs|sh|bash|zsh|fish|sql|nix|lua|php|pl|swift|r|tex|gitignore|env)$/i;
const IMG_RE  = /\.(png|jpe?g|gif|webp|avif|bmp|ico|svg)$/i;
const TEXT_MAX = 512 * 1024;

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
    if (/\.html?$/i.test(node.name)) {
      pvURL = URL.createObjectURL(blob.slice(0, blob.size, "text/html"));
      return `<iframe class="pv-html" src="${pvURL}" title="${esc(node.name)}"></iframe>`;
    }
    if (/\.desktop$/i.test(node.name) && blob.size <= TEXT_MAX)
      return desktopCard(await blob.text()) ?? null;

    if (TEXT_RE.test(node.name) && blob.size <= TEXT_MAX) {
      const text = await blob.text();
      /* core/syntax.js colours what it has a language for and escapes the rest;
         a plain .txt or an unknown extension takes the same path it always did.
         Colouring the whole file costs 22 ms of regex and 273 ms of DOM at the
         512 KB ceiling, measured in Chromium — once, on the click that asked
         for it. Highlighting a slice at a time would be cheaper and wrong: a
         triple-quoted string spanning the cut mis-tokenises, and syntax.js
         promises every character exactly once. */
      const lang = hlLang(node.name);
      const body = lang ? hlHTML(text, lang) : esc(text);
      return `<pre class="pv-text">${body}</pre>`;
    }
    return null;
  },
};
