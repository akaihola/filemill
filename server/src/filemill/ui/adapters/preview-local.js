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
import { esc } from "../core/icons.js";
import { FS } from "../core/ports.js";
import { render } from "../core/render.js";
import { hlHTML, hlLang, jsonHTML } from "../core/syntax.js";
import { IMAGE_EXTENSIONS, TEXT_MAX } from "../core/limits.js";

const IMG_RE = new RegExp(`\\.(${IMAGE_EXTENSIONS.join("|")})$`, "i");

let pvURL = null;

function vttHTML(source, mode = "transcript") {
  if (mode === "raw") return `<pre class="preview-raw">${esc(source)}</pre>`;
  const text = source.replace(/^\uFEFF/, "");
  if (!/^WEBVTT(?:\s|$)/.test(text)) {
    return '<div class="preview-error">Malformed WebVTT: missing WEBVTT header.</div>';
  }
  const cues = [];
  let seenCue = false;
  for (const block of text.split(/\r?\n\s*\r?\n/).slice(1)) {
    const lines = block.split(/\r?\n/);
    if (["NOTE", "STYLE", "REGION"].includes(lines[0]?.trim())) continue;
    const i = lines.findIndex((line) => line.includes("-->"));
    if (i < 0) {
      if (
        !seenCue && block.trim() && lines.every((line) => line.includes(":"))
      ) continue;
      if (block.trim()) {
        return '<div class="preview-error">Malformed WebVTT: cue is missing a timestamp.</div>';
      }
      continue;
    }
    const m = lines[i].trim().match(
      /^(\d{2}:\d{2}(?::\d{2})?\.\d{3})\s+-->\s+(\d{2}:\d{2}(?::\d{2})?\.\d{3})(?:\s+.*)?$/,
    );
    if (!m) {
      return '<div class="preview-error">Malformed WebVTT: invalid cue timestamp.</div>';
    }
    seenCue = true;
    let cue = lines.slice(i + 1).join("\n").trim();
    const voice = cue.match(/^<v(?:\s+([^>]+))?>([\s\S]*)$/);
    const speaker = voice?.[1]?.trim() || "";
    if (voice) cue = voice[2];
    cue = cue.replace(/<[^>]+>/g, "").trim();
    if (cue) cues.push([m[1], m[2], speaker, cue]);
  }
  if (!cues.length) {
    return '<div class="preview-empty">WebVTT file has no cues.</div>';
  }
  return `<div class="preview-transcript">${
    cues.map(([start, end, speaker, cue]) =>
      `<p class="preview-cue"><span class="preview-cue-time">${esc(start)} → ${
        esc(end)
      }</span><span class="preview-cue-text">${
        speaker ? `<strong>${esc(speaker)}:</strong> ` : ""
      }${esc(cue).replace(/\n/g, "<br>")}</span></p>`
    ).join("")
  }</div>`;
}

/* .desktop is an INI file; only Type=Link entries have anything to show. */
function desktopCard(text) {
  const e = {};
  let inEntry = false;
  for (const line of text.split(/\r?\n/)) {
    const s = line.trim();
    if (s.startsWith("[")) {
      inEntry = s === "[Desktop Entry]";
      continue;
    }
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

export const PreviewLocal = {
  revoke() {
    if (pvURL) {
      URL.revokeObjectURL(pvURL);
      pvURL = null;
    }
  },

  async render(node) {
    /* Decline an oversized text file before it is fetched, not after. The FSA
       port hands back a lazy File, so blob.size below costs nothing there — but
       HTTP.blob (adapters/http.js) does `await r.blob()`, which buffers the
       whole response, and by then a 400 MB .sql is already in memory. node.meta
       is filled by fillPreview before any provider runs, the same thing canEdit
       leans on. The blob.size test below stays: this one is only as good as the
       listing's size, and the limit should not depend on that being right. */
    if ((node.meta?.size ?? 0) > TEXT_MAX) return null;
    const blob = await FS.blob(node);
    if (!blob) return null;

    if (IMG_RE.test(node.name)) {
      pvURL = URL.createObjectURL(blob);
      return `<img class="pv-img" src="${pvURL}" alt="">`;
    }
    if (/\.pdf$/i.test(node.name)) {
      pvURL = URL.createObjectURL(blob.slice(0, blob.size, "application/pdf"));
      return `<iframe class="pv-pdf" src="${pvURL}" title="${
        esc(node.name)
      }"></iframe>`;
    }
    if (/\.html?$/i.test(node.name)) {
      pvURL = URL.createObjectURL(blob.slice(0, blob.size, "text/html"));
      return `<iframe class="pv-html" src="${pvURL}" title="${
        esc(node.name)
      }"></iframe>`;
    }
    if (/\.desktop$/i.test(node.name) && blob.size <= TEXT_MAX) {
      return desktopCard(await blob.text()) ?? null;
    }

    if (/\.vtt$/i.test(node.name)) {
      return vttHTML(await blob.text(), node.previewFormat);
    }

    if (blob.size <= TEXT_MAX) {
      let text;
      try {
        text = new TextDecoder("utf-8", { fatal: true }).decode(
          await blob.arrayBuffer(),
        );
      } catch (_) {
        return null;
      }
      if (text.includes("\0")) return null;
      /* core/syntax.js colours what it has a language for and escapes the rest;
         a plain .txt or an unknown extension takes the same path it always did.
         Colouring the whole file costs 22 ms of regex and 273 ms of DOM at the
         512 KB ceiling, measured in Chromium — once, on the click that asked
         for it. Highlighting a slice at a time would be cheaper and wrong: a
         triple-quoted string spanning the cut mis-tokenises, and syntax.js
         promises every character exactly once. */
      const lang = hlLang(node.name);
      /* A .json that parses is shown pretty-printed and foldable; one that does
         not (or a .jsonc with comments) is coloured as source like any other.
         This is the whole-file preview only. Browsing a .json as columns, the
         way core/jsonl.js does for .jsonl, wraps the FS and PREVIEW ports
         outside this provider and answers for its own virtual nodes before
         they get here — jsonHTML is a plain function it can call on a subtree. */
      const json = lang === "json" ? jsonHTML(text) : null;
      const body = json ?? (lang ? hlHTML(text, lang) : esc(text));
      return `<pre class="pv-text${json ? " pv-json" : ""}">${body}</pre>`;
    }
    return null;
  },
};
