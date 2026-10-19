/* ═══════════════════════════════════════════════════════════════════════════
   Preview provider — in-browser, zero dependencies.

   Fills the PREVIEW port (see core/ports.js) from the bytes alone, so it costs
   nothing in the bundle and works with no network. The kinds it draws are the
   CORE_RENDERERS table in core/renderers.js: images, PDF, HTML, .desktop,
   WebVTT, and escaped text coloured by core/syntax.js. TEXT_MAX is the only
   limit: what is previewed at all is previewed entire.

   Rich rendering (Markdown, docx, pptx) is a *different provider*, not a
   bigger version of this one: see PreviewHTTP in app-http.js for the
   server-rendered variant, and preview-rich.js for the browser one. This one renders only
   the core table, so a switched-off rich renderer leaves a .md as text.
   ═══════════════════════════════════════════════════════════════════════════ */
import { FS } from "../core/ports.js";
import { classifyFile } from "../core/file-kind.js";
import { TEXT_MAX } from "../core/limits.js";
import { hlLang } from "../core/syntax.js";
import {
  CORE_RENDERERS,
  renderNode,
  revokeObjectURL,
} from "../core/renderers.js";

export const PreviewLocal = {
  revoke() {
    revokeObjectURL();
  },

  async render(node, kind = classifyFile(node.name, node).preview) {
    /* Decline an oversized text file before it is fetched, not after. The FSA
       port hands back a lazy File, so blob.size below costs nothing there — but
       HTTP.blob (adapters/http.js) does `await r.blob()`, which buffers the
       whole response, and by then a 400 MB .sql is already in memory. node.meta
       is filled by fillPreview before any provider runs, the same thing
       editableText leans on. The blob.size test in the text entry stays: this one is only
       as good as the listing's size, and the limit should not depend on that
       being right. */
    if (
      (node.meta?.size ?? 0) > TEXT_MAX &&
      kind === "text"
    ) return null;
    const blob = await FS.blob(node);
    if (!blob) return null;
    return renderNode(node, blob, kind, CORE_RENDERERS);
  },
};

/* Source uses the same text renderer in every edition. Virtual providers
   answer for their own nodes before this wrapper runs. */
export const withHighlighting = (provider) => ({
  revoke() {
    provider.revoke?.();
    PreviewLocal.revoke();
  },
  render: (n) =>
    !n.vpath && document.documentElement.dataset.filemill === "highlight" &&
      (hlLang(n.name) || classifyFile(n.name, n).preview === "vtt")
      ? PreviewLocal.render(n, "text")
      : provider.render(n),
});
