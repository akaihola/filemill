/* ═══════════════════════════════════════════════════════════════════════════
   Preview provider — rich rendering, fetched on demand.

   Markdown and .docx, to match what filemill's Python renderers produce, and
   reStructuredText, which only Python renders well. The libraries are an order
   of magnitude larger than this app, so they are not in the bundle: they are
   imported from a CDN the first time a file that needs one is previewed, and
   cached for the session.

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
import { esc } from "../core/icons.js";
import { choose } from "../core/nav.js";
import { FS } from "../core/ports.js";
import { render } from "../core/render.js";
import { offerRichToggle } from "../core/settings.js";
import { path, splitName, state, visibleKids } from "../core/state.js";

const CDN = {
  "markdown-it": "https://esm.sh/markdown-it@14.1.0",
  "markdown-it-footnote": "https://esm.sh/markdown-it-footnote@4.0.0",
  "markdown-it-deflist": "https://esm.sh/markdown-it-deflist@3.0.0",
  "markdown-it-task-lists": "https://esm.sh/markdown-it-task-lists@2.1.1",
  "markdown-it-anchor": "https://esm.sh/markdown-it-anchor@9.2.0",
  "mammoth": "https://esm.sh/mammoth@1.8.0",
  "pptx-vanilla-viewer":
    "https://cdn.jsdelivr.net/npm/pptx-vanilla-viewer@2.1.4/+esm",
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

const MD_RE = /\.(md|markdown)$/i;
const DOCX_RE = /\.docx$/i;
const RST_RE = /\.rst$/i;
const PPTX_RE = /\.pptx$/i;

const NOTE =
  `<p class="pv-note">Offline — showing the source. Rich rendering ` +
  `needs a one-time download.</p>`;

/* ── Markdown ────────────────────────────────────────────────────────────── */
let mdInstance = null;

async function markdown(text) {
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
      .use(footnote).use(deflist).use(tasklists).use(anchor);

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
  return mdInstance.render(text);
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
  py.globals.set("src", text);
  const html = await py.runPythonAsync(RST_PY);
  /* docutils writes `.. code-block:: x` as <pre class="code x literal-block">
     <code>; hlFences looks for <pre><code class="language-x">, the shape the
     Markdown renderers emit. Same colours for the same fence, either syntax. */
  return html.replace(
    /<pre class="code (\S+) literal-block"><code>/g,
    '<pre><code class="language-$1">',
  );
}

/* ── The provider ────────────────────────────────────────────────────────── */
export const PreviewRich = {
  revoke() {
    PreviewLocal.revoke();
  },

  async render(node) {
    if (!richEnabled()) return PreviewLocal.render(node);

    if (
      !MD_RE.test(node.name) && !DOCX_RE.test(node.name) &&
      !RST_RE.test(node.name) && !PPTX_RE.test(node.name)
    ) {
      return PreviewLocal.render(node);
    }

    const blob = await FS.blob(node);
    if (!blob) return PreviewLocal.render(node);

    try {
      if (PPTX_RE.test(node.name)) {
        const { createPptxViewer } = await load("pptx-vanilla-viewer");
        const id = `pptx-${crypto.randomUUID()}`;
        queueMicrotask(async () => {
          const host = document.getElementById(id);
          if (!host) return;
          host.textContent = "Loading PowerPoint preview…";
          try {
            const viewer = createPptxViewer(host, {
              source: blob,
              editable: false,
              showToolbar: true,
              showThumbnails: true,
              onError: (message) => {
                host.textContent = `PowerPoint preview failed: ${message}`;
              },
            });
            host._pptxViewer = viewer;
          } catch (err) {
            host.textContent = `PowerPoint preview failed: ${
              err.message || err
            }`;
          }
        });
        return `<div id="${id}" class="pv-pptx" aria-live="polite">Loading PowerPoint preview…</div>`;
      }
      if (DOCX_RE.test(node.name)) {
        const mammoth = await load("mammoth");
        const { value } = await mammoth.convertToHtml(
          { arrayBuffer: await blob.arrayBuffer() },
        );
        return `<div class="pv-rich">${value}</div>`;
      }

      if (blob.size > 512 * 1024) return PreviewLocal.render(node);
      const text = await blob.text();

      if (RST_RE.test(node.name)) {
        return `<div class="pv-rich">${await rst(text)}</div>`;
      }
      return `<div class="pv-rich">${await markdown(text)}</div>`;
    } catch (err) {
      /* Offline, blocked, or the CDN moved. The file is still readable. */
      if (PPTX_RE.test(node.name)) {
        return `<div class="preview-error">PowerPoint preview unavailable: ${
          esc(String(err.message || err))
        }</div>`;
      }
      const fallback = await PreviewLocal.render(node);
      return fallback ? NOTE + fallback : null;
    }
  },
};

export const withPptxPreview = (provider) => ({
  revoke() {
    provider.revoke?.();
    PreviewRich.revoke();
  },
  render(node) {
    return PPTX_RE.test(node.name)
      ? PreviewRich.render(node)
      : provider.render(node);
  },
});

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
