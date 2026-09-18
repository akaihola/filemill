/* ═══════════════════════════════════════════════════════════════════════════
   Preview provider — rich rendering, fetched on demand.

   Markdown, .docx, and reStructuredText, which only Python renders well. The
   libraries are an order of magnitude larger than this app, so they are not in
   the static bundle: they are imported from a CDN the first time a file that
   needs one is previewed, and cached for the session. The server edition
   serves the Markdown and .docx modules itself from ui/vendor/ and points
   FILEMILL_CDN at them, so there nothing is fetched from a third party.

   Source files and fenced code are not on that list. They are coloured by
   core/syntax.js, in the page, with no download and no switch to find —
   highlighting that only arrived over the network would be missing from
   exactly the offline build the app is built to be. What is left here is what
   genuinely needs a library.

   Which means this is the one thing in filemill that talks to the network, and
   the app's whole pitch is that your folder does not. So:

     · it is a setting, off-switchable, and the choice is remembered — consent
       that resets on every reload is not consent;
     · nothing about the file is ever *sent*. The request is for the library,
       not with your content;
     · every failure falls back to PreviewLocal — the raw <pre>, or nothing for
       a binary — so offline is a downgrade in fidelity, never a broken pane.

   Version pins are deliberate: "@latest" would mean a preview that renders
   differently next week, and a supply chain that can change under you.
   ═══════════════════════════════════════════════════════════════════════════ */
import { PreviewLocal } from "./preview-local.js";
import { TEXT_MAX } from "../core/limits.js";
import { classifyFile } from "../core/file-kind.js";
import { esc } from "../core/icons.js";
import { choose } from "../core/nav.js";
import { FS } from "../core/ports.js";
import { render } from "../core/render.js";
import { renderNode } from "../core/renderers.js";
import { path, splitName, state, visibleKids } from "../core/state.js";

const offerRichToggle = (get, set) => {
  document.getElementById("s-previews").hidden = false;
  document.getElementById("s-rich").hidden = false;
  document.getElementById("s-rich-hr").hidden = false;
  const button = document.getElementById("s-rich");
  button.onclick = () => {
    set(!get());
    button.setAttribute("aria-checked", String(get()));
    render(true);
  };
  button.setAttribute("aria-checked", String(get()));
};

const CDN = {
  "markdown-it": "https://esm.sh/markdown-it@14.1.0",
  "markdown-it-footnote": "https://esm.sh/markdown-it-footnote@4.0.0",
  "markdown-it-deflist": "https://esm.sh/markdown-it-deflist@3.0.0",
  "markdown-it-task-lists": "https://esm.sh/markdown-it-task-lists@2.1.1",
  "markdown-it-anchor": "https://esm.sh/markdown-it-anchor@9.2.0",
  "mammoth": "https://esm.sh/mammoth@1.8.0",
  /* No JavaScript reStructuredText parser handles directives, tables or
     footnotes, and the one that exists emits unescaped HTML — so docutils runs
     as itself, on Pyodide. The runtime plus docutils is ~6 MB on the wire, 13 MB
     unpacked, once per session; docs/adr/0002-rst-in-browser.md has the
     figures. The release directory on jsDelivr is immutable, and docutils'
     version is fixed by that release's lock file, so one pin covers both. */
  "pyodide": "https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.mjs",
};

/* Tests point this at local stubs — there is no other way to exercise the
   loaded path without a network. */
const cdn = (name) =>
  (globalThis.FILEMILL_CDN && globalThis.FILEMILL_CDN[name]) || CDN[name];

/* A module served from this origin is not a download the visitor has to agree
   to, so the rich switch below does not apply to it. */
const vendored = (name) => cdn(name).startsWith("/");

/* The module each kind needs first; the switch is asked about that one. */
const NEEDS = {
  md: "markdown-it",
  markdown: "markdown-it",
  rst: "pyodide",
  docx: "mammoth",
};

const RICH_KEY = "filemill.rich";
const richEnabled = () => localStorage.getItem(RICH_KEY) !== "off";
const setRich = (on) => {
  localStorage.setItem(RICH_KEY, on ? "on" : "off");
  loaded.clear(); /* re-attempt after being switched on */
  pyInstance = null;
};

/* Cache the promise, not the module: two previews opened in the same tick must
   not each start a download. A rejected load is dropped so that reconnecting
   and clicking again retries, rather than being offline once and forever. */
const loaded = new Map();

function load(name) {
  if (loaded.has(name)) return loaded.get(name);
  const p = import(cdn(name))
    .then((m) => m.default || m)
    .catch((err) => {
      loaded.delete(name);
      throw err;
    });
  loaded.set(name, p);
  return p;
}

offerRichToggle(richEnabled, setRich);

const NOTE =
  `<p class="pv-note">Offline — showing the source. Rich rendering ` +
  `needs a one-time download.</p>`;

/* ── Markdown ────────────────────────────────────────────────────────────── */
let mdInstance = null;

function homeHref(href) {
  if (!href.startsWith("~/")) return href;
  const mount = document.documentElement.dataset.root;
  return mount && mount !== "/" ? `/w/${encodeURIComponent(mount)}/${href.slice(2)}` : href.slice(2);
}

/* A relative link resolves against the document's own folder and becomes the
   target's root-relative URL, so it lands on the file the author meant even
   when the page is a deep link. A Markdown target gets ?filemill=render: a
   link from one document to another should land on the rendered document,
   not its bytes. Only a served node has a folder here (`node.rel`); the files
   of a local or static folder have no URL, and their links stay as written. */
function localHref(href, dir) {
  if (dir === undefined || /^(?:[a-z][a-z0-9+.-]*:|\/|#)/i.test(href)) {
    return href;
  }
  const clean = href.split("#")[0].split("?")[0];
  if (!clean) return href;
  const parts = dir ? dir.split("/").map(encodeURIComponent) : [];
  for (const p of clean.split("/")) {
    if (p === "..") parts.pop();
    else if (p && p !== ".") parts.push(p);
  }
  const url = "/" + parts.join("/");
  return /\.md$/i.test(url) ? url + "?filemill=render" : url;
}

async function markdown(text, node) {
  if (!mdInstance) {
    const [MarkdownIt, footnote, deflist, tasklists, anchor] = await Promise
      .all([
        load("markdown-it"),
        load("markdown-it-footnote"),
        load("markdown-it-deflist"),
        load("markdown-it-task-lists"),
        load("markdown-it-anchor"),
      ]);
    /* No highlight option: fences come out as <pre><code class="language-x">,
       and core/syntax.js colours them after they land — see hlFences. */
    mdInstance = new MarkdownIt({
      linkify: true,
      typographer: false,
      html: false,
    })
      .use(footnote).use(deflist).use(tasklists)
      /* No tabindex on headings: markdown-it-py's anchors plugin never set
         one, and a focusable heading landing in a fullscreen preview nudges
         the stage sideways for a frame. Same ids as before, nothing else. */
      .use(anchor, { tabIndex: false });
    const linkOpen = mdInstance.renderer.rules.link_open ||
      ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options));
    mdInstance.renderer.rules.link_open = (tokens, idx, options, env, self) => {
      const token = tokens[idx];
      const href = token.attrGet("href");
      if (href) {
        const home = homeHref(href);
        token.attrSet("href", home === href ? localHref(href, env.dir) : home);
      }
      return linkOpen(tokens, idx, options, env, self);
    };

    /* filemill renders [[PageName]]; markdown-it has no such plugin, and the
       rule is small enough that matching it is cheaper than finding one. The
       target is resolved by the shared navigator, not by the browser, so the
       link stays inside the app. */
    mdInstance.core.ruler.push("wikilink", (state) => {
      for (const tok of state.tokens) {
        if (tok.type !== "inline") continue;
        for (const child of tok.children) {
          if (child.type !== "text" || !child.content.includes("[[")) continue;
          child.type = "html_inline";
          child.content = child.content.replace(
            /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,
            (_, target, label) =>
              `<a class="wikilink" href="#" data-wiki="${
                esc(target.trim())
              }">` +
              `${esc((label || target).trim())}</a>`,
          );
        }
      }
    });
  }
  const dir = typeof node.rel === "string"
    ? node.rel.replace(/\/?[^/]*$/, "")
    : undefined;
  return mdInstance.render(text, { dir });
}

/* ── reStructuredText ────────────────────────────────────────────────────── */
let pyInstance = null;

/* The interpreter is cached like mdInstance, as a promise so that two .rst
   previews in one tick share a single download; a failed boot is dropped so
   the next click retries. `raw` and file insertion are off: a document must
   not be able to inject markup or read the visitor's files. Level 5 keeps
   docutils' own error paragraphs out of the pane — the file still renders as
   far as it parses, which is how the Markdown side behaves too. */
const RST_PY = `
from docutils.core import publish_parts
publish_parts(src, writer_name="html5", settings_overrides={
    "raw_enabled": False,
    "file_insertion_enabled": False,
    "report_level": 5,
    "doctitle_xform": False,
    "initial_header_level": 1,
    "syntax_highlight": "none",
    "embed_stylesheet": False,
})["body"]
`;

async function rst(text) {
  if (!pyInstance) {
    pyInstance = load("pyodide")
      .then(async (m) => {
        const py = await m.loadPyodide({
          indexURL: cdn("pyodide").replace(/[^/]*$/, ""),
        });
        await py.loadPackage("docutils");
        return py;
      })
      .catch((err) => {
        pyInstance = null;
        throw err;
      });
  }
  const py = await pyInstance;
  // Each asynchronous preview owns its source, even while another is rendering.
  const globals = py.toPy({ src: text });
  let html;
  try {
    html = await py.runPythonAsync(RST_PY, { globals });
  } finally {
    globals.destroy();
  }
  /* docutils writes `.. code-block:: x` as <pre class="code x literal-block">
     <code>; hlFences looks for <pre><code class="language-x">, the shape the
     Markdown renderers emit. Same colours for the same fence, either syntax. */
  return html.replace(
    /<pre class="code (\S+) literal-block"><code>/g,
    '<pre><code class="language-$1">',
  );
}

/* ── The entries ─────────────────────────────────────────────────────────── */
async function unzipPptx(blob) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  const view = new DataView(bytes.buffer);
  const slides = [];
  for (let at = 0; at + 30 <= bytes.length && view.getUint32(at, true) === 0x04034b50;) {
    const method = view.getUint16(at + 8, true);
    const compressed = view.getUint32(at + 18, true);
    const nameSize = view.getUint16(at + 26, true);
    const extraSize = view.getUint16(at + 28, true);
    const name = new TextDecoder().decode(bytes.subarray(at + 30, at + 30 + nameSize));
    const start = at + 30 + nameSize + extraSize;
    const end = start + compressed;
    if (end > bytes.length) throw new Error("truncated ZIP entry");
    if (/^ppt\/slides\/slide\d+\.xml$/.test(name)) {
      let data = bytes.slice(start, end);
      if (method === 8) {
        data = new Uint8Array(await new Response(
          new Blob([data]).stream().pipeThrough(new DecompressionStream("deflate-raw")),
        ).arrayBuffer());
      } else if (method !== 0) {
        throw new Error("unsupported ZIP compression");
      }
      const xml = new DOMParser().parseFromString(new TextDecoder().decode(data), "application/xml");
      const text = [...xml.getElementsByTagNameNS("*", "t")].map((n) => n.textContent).join("").trim();
      slides.push({ number: Number(name.match(/slide(\d+)/)[1]), text });
    }
    at = end;
  }
  return slides.sort((a, b) => a.number - b.number);
}

const pptxHTML = async (_node, blob) => {
  try {
    const slides = await unzipPptx(blob);
    if (!slides.length) return '<div class="preview-empty">PowerPoint has no slides.</div>';
    return `<div class="pv-pptx">${slides.map(({ number, text }) =>
      `<section class="slide"><h2>Slide ${number}</h2><p>${esc(text) || "(No slide text)"}</p></section>`
    ).join("")}</div>`;
  } catch (err) {
    return `<div class="preview-error">PowerPoint preview failed: ${
      esc(String(err.message || err))
    }</div>`;
  }
};

const docxHTML = async (_node, blob) => {
  const mammoth = await load("mammoth");
  const { value } = await mammoth.convertToHtml(
    { arrayBuffer: await blob.arrayBuffer() },
  );
  return `<div class="pv-rich">${value}</div>`;
};

/* A text renderer: oversize files take the plain path, like the local one. */
const richText = (convert) => async (node, blob) => {
  if (blob.size > TEXT_MAX) return renderNode(node, blob, "text");
  return `<div class="pv-rich">${await convert(await blob.text(), node)}</div>`;
};

/* Offline, blocked, or the CDN moved. The file is still readable. */
const offlineHTML = async (node, blob) => {
  const fallback = await renderNode(node, blob, "text");
  return fallback ? NOTE + fallback : null;
};

export const RICH_RENDERERS = [
  { kind: "md", render: richText(markdown), fallback: "offline" },
  { kind: "markdown", render: richText(markdown), fallback: "offline" },
  { kind: "rst", render: richText(rst), fallback: "offline" },
  { kind: "docx", render: docxHTML, fallback: "offline" },
  { kind: "pptx", render: pptxHTML },
  { kind: "offline", render: offlineHTML },
];

/* ── The provider ────────────────────────────────────────────────────────── */
export const PreviewRich = {
  revoke() {
    PreviewLocal.revoke();
  },

  async render(node) {
    const kind = classifyFile(node.name, node).preview;
    const need = NEEDS[kind];
    if ((!need && kind !== "pptx") || (need && !richEnabled() && !vendored(need))) {
      return PreviewLocal.render(node);
    }
    const blob = await FS.blob(node);
    if (!blob) return PreviewLocal.render(node);
    return renderNode(node, blob, kind);
  },
};

/* A wikilink resolves against the folder being browsed, not the web — so it
   selects a row in the column the file itself is in, exactly as clicking that
   row would. Only that directory is searched: walking the whole tree would mean
   reading every folder under the root to resolve one link. */
function openWikilink(target) {
  const col = path.length - 1;
  const kids = visibleKids(path[col]);
  const want = target.toLowerCase();
  const ri = kids.findIndex((k) => {
    const n = k.name.toLowerCase();
    return n === want || n === want + ".md" ||
      splitName(k.name)[0].toLowerCase() === want;
  });
  if (ri >= 0) choose(col, kids[ri]);
}

document.addEventListener("click", (e) => {
  const a = e.target.closest && e.target.closest("a.wikilink");
  if (!a) return;
  e.preventDefault();
  openWikilink(a.dataset.wiki);
});
