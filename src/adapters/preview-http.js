/* ═══════════════════════════════════════════════════════════════════════════
   Preview provider — rendered by the server.

   Fills the PREVIEW port (see core/ports.js). This is why the Python renderers
   do not have to be ported to JavaScript: markdown-it-py with its plugin set,
   Pygments, mammoth, python-pptx and the VFS providers all keep running where
   they already run, and their output lands in the same pane.

   The staleness guard is core's (see fillPreview), so this may take as long as
   it takes; the abort is only good manners for a preview nobody is waiting for.
   ═══════════════════════════════════════════════════════════════════════════ */
let inflight = null;

const PreviewHTTP = {
  revoke() { inflight?.abort(); inflight = null; },

  async render(node) {
    inflight?.abort();
    const ctl = (inflight = new AbortController());
    let r;
    try {
      r = await fetch(`${API}/preview?p=${encodeURIComponent(node.rel)}`,
                      { signal: ctl.signal });
    } catch (err) {
      if (err.name === "AbortError") return null;
      throw err;
    }
    if (!r.ok) return null;
    const html = await r.text();
    return html.trim() ? `<div class="pv-rich">${html}</div>` : null;
  },
};

usePreview(PreviewHTTP);
