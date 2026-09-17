/* ═══════════════════════════════════════════════════════════════════════════
   Preview provider — local bytes, server renderer.

   The awkward case: the server build has opened a folder through the browser's
   File System Access API, so the server cannot read the file — but the Python
   renderers are right there, on the same origin, on this machine. So post the
   bytes and get the fragment back.

   That is what keeps "Open local folder…" from being a downgrade. Markdown
   still renders with the full markdown-it-py plugin set, source still gets
   Pygments, .docx still goes through mammoth — from a folder the server has
   never heard of.

   Anything the browser can already do itself is done without the round-trip:
   images and PDFs become object URLs, because uploading a 40 MB scan to render
   an <img> would be silly.
   ═══════════════════════════════════════════════════════════════════════════ */
import { API } from "./http.js";
import { PreviewLocal } from "./preview-local.js";
import { FS } from "../core/ports.js";
import { render } from "../core/render.js";
import { IMAGE_EXTENSIONS } from "../core/limits.js";
import { classifyFile } from "../core/file-kind.js";

const UPLOAD_MAX = 4 * 1024 * 1024;
const IMAGE_RE = new RegExp(`\\.(${IMAGE_EXTENSIONS.join("|")}|pdf)$`, "i");

export const PreviewUpload = {
  revoke() {
    PreviewLocal.revoke();
  },

  async render(node) {
    if (classifyFile(node.name, node).preview === "vtt") return PreviewLocal.render(node);
    /* object-URL cases, and the ones too big to be worth sending */
    if (
      ["image", "pdf"].includes(classifyFile(node.name, node).preview) ||
      (node.meta?.size ?? 0) > UPLOAD_MAX
    ) {
      return PreviewLocal.render(node);
    }

    const blob = await FS.blob(node);
    if (!blob) return null;
    const body = new FormData();
    body.append("file", blob, node.name);
    let r;
    try {
      r = await fetch(`${API}/render`, { method: "POST", body });
    } catch (err) {
      return PreviewLocal.render(node); /* server gone — better than nothing */
    }
    if (!r.ok) return PreviewLocal.render(node);
    const html = await r.text();
    return html.trim() ? `<div class="pv-rich">${html}</div>` : null;
  },
};
