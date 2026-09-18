/* ═══════════════════════════════════════════════════════════════════════════
   Renderer registry — one table for every preview kind.

   An entry is `{kind, render, fallback}`. `kind` is the `preview` string from
   core/file-kind.js. `render(node, blob)` returns the HTML for the preview
   body, null for "no inline preview", or throws. `fallback` names the kind to
   render instead when it throws. renderNode walks that chain.

   CORE_RENDERERS is what the browser can do from the bytes alone, with no
   download and no server: images, PDF and HTML as object URLs, .desktop as a
   link card, WebVTT as a transcript, and everything else as coloured text.
   Both editions register this list at boot; each app module adds the entries
   of its own adapters after it (adapters/app-fsa.js, adapters/app-http.js).
   Adding a kind is one entry here or in an adapter, plus one test.
   ═══════════════════════════════════════════════════════════════════════════ */
import { esc } from "./icons.js";
import { hlHTML, hlLang, jsonHTML } from "./syntax.js";
import { TEXT_MAX } from "./limits.js";
import { classifyFile } from "./file-kind.js";

let pvURL = null;

/* Release the object URL of the last image, PDF or HTML preview. */
export function revokeObjectURL() {
  if (pvURL) {
    URL.revokeObjectURL(pvURL);
    pvURL = null;
  }
}

function vttHTML(source, mode = "transcript") {
  if (mode === "raw") return `<pre class="preview-raw">${esc(source)}</pre>`;
  const text = source.replace(/^\uFEFF/, "");
  if (!/^WEBVTT(?:\s|$)/.test(text)) {
    return '<div class="preview-error">Malformed WebVTT: missing WEBVTT header.</div>';
  }
  const cues = [];
  let seenCue = false;
  let pendingCue = null;
  for (const block of text.split(/\r?\n\s*\r?\n/).slice(1)) {
    const lines = block.split(/\r?\n/);
    if (["NOTE", "STYLE", "REGION"].includes(lines[0]?.trim())) continue;
    const i = lines.findIndex((line) => line.includes("-->"));
    if (i < 0) {
      if (
        !seenCue && block.trim() && lines.every((line) => line.includes(":"))
      ) continue;
      if (pendingCue && block.trim()) {
        const continuation = block.replace(/<[^>]+>/g, "").trim();
        if (continuation) {
          cues.push([...pendingCue, continuation]);
          pendingCue = null;
        }
        continue;
      }
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
    else pendingCue = [m[1], m[2], speaker];
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

async function textHTML(node, blob) {
  if (blob.size > TEXT_MAX) return null;
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
     way adapters/vfs-json.js does, wraps the FS and PREVIEW ports outside
     the registry and answers for its own virtual nodes before they get
     here — jsonHTML is a plain function it can call on a subtree. */
  const json = lang === "json" ? jsonHTML(text) : null;
  const body = json ?? (lang ? hlHTML(text, lang) : esc(text));
  return `<pre class="pv-text${json ? " pv-json" : ""}">${body}</pre>`;
}

export const CORE_RENDERERS = [
  {
    kind: "image",
    render(_node, blob) {
      pvURL = URL.createObjectURL(blob);
      return `<img class="pv-img" src="${pvURL}" alt="">`;
    },
  },
  {
    kind: "video",
    render(_node, blob) {
      pvURL = URL.createObjectURL(blob);
      return `<video class="pv-video" src="${pvURL}" controls></video>`;
    },
  },
  {
    kind: "pdf",
    render(node, blob) {
      pvURL = URL.createObjectURL(blob.slice(0, blob.size, "application/pdf"));
      return `<iframe class="pv-pdf" src="${pvURL}" title="${
        esc(node.name)
      }"></iframe>`;
    },
  },
  {
    kind: "html",
    render(node, blob) {
      pvURL = URL.createObjectURL(blob.slice(0, blob.size, "text/html"));
      return `<iframe class="pv-html" src="${pvURL}" title="${
        esc(node.name)
      }"></iframe>`;
    },
  },
  {
    kind: "desktop",
    async render(_node, blob) {
      if (blob.size > TEXT_MAX) return null;
      return desktopCard(await blob.text()) ?? null;
    },
  },
  {
    kind: "vtt",
    async render(node, blob) {
      return vttHTML(await blob.text(), node.previewFormat);
    },
  },
  { kind: "text", render: textHTML },
];

/* The live table. Empty until an app module fills it. */
export const RENDERERS = [];

export const addRenderers = (entries) => {
  RENDERERS.push(...entries);
};

/* The first entry for `kind` renders; an unknown kind renders as text. When an
   entry throws and names a fallback, that kind renders instead — the chain
   ends at an entry with no fallback, whose error reaches the caller. */
export async function renderNode(
  node,
  blob,
  kind = classifyFile(node.name, node).preview,
  list = RENDERERS,
) {
  const entry = list.find((e) => e.kind === kind) ??
    list.find((e) => e.kind === "text");
  if (!entry) return null;
  try {
    return await entry.render(node, blob);
  } catch (err) {
    if (!entry.fallback) throw err;
    return renderNode(node, blob, entry.fallback, list);
  }
}
