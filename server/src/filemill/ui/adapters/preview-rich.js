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
import { classifyFile, fileKind } from "../core/file-kind.js";
import { esc } from "../core/icons.js";
import { choose } from "../core/nav.js";
import { FS } from "../core/ports.js";
import { markdownHref } from "../core/markdown-links.js";
import { render } from "../core/render.js";
import { renderNode } from "../core/renderers.js";
import { safeURL } from "../core/model/safe-url.js";
import { path, splitName, state, visibleKids } from "../core/model/state.js";

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
    const validateLink = mdInstance.validateLink;
    mdInstance.validateLink = (href) =>
      validateLink(href) &&
      (/^data:/i.test(href) || markdownHref(href) !== null);
    const linkOpen = mdInstance.renderer.rules.link_open ||
      ((tokens, idx, options, env, self) =>
        self.renderToken(tokens, idx, options));
    mdInstance.renderer.rules.link_open = (tokens, idx, options, env, self) => {
      const token = tokens[idx];
      const href = token.attrGet("href");
      if (href) {
        const target = markdownHref(href, env.dir);
        if (target === null) {
          token.attrs = token.attrs.filter(([name]) => name !== "href");
        } else token.attrSet("href", target);
      }
      return linkOpen(tokens, idx, options, env, self);
    };

    /* A task checkbox names the source line of its list item and its text, so
       a click can rewrite that line; see editor/task-toggle.js. */
    mdInstance.core.ruler.push("task-source-line", (state) => {
      const lines = state.src.split("\n");
      state.tokens.forEach((tok, i) => {
        const box = tok.type === "inline" && tok.children?.[0];
        const line = state.tokens[i - 1]?.map?.[0];
        if (
          box?.type === "html_inline" && Number.isInteger(line) &&
          box.content.startsWith('<input class="task-list-item-checkbox"')
        ) {
          box.content = box.content.replace(
            "<input",
            `<input data-source-line="${line}" data-source-text="${
              esc(lines[line] ?? "")
            }"`,
          );
        }
      });
    });

    /* filemill renders [[PageName]]; markdown-it has no such plugin, and the
       rule is small enough that matching it is cheaper than finding one. The
       target is resolved by the shared navigator, not by the browser, so the
       link stays inside the app. A match becomes link tokens and the text
       around it stays a text token, which markdown-it escapes like any other:
       a wikilink must not turn its neighbours into markup (A2). */
    const WIKILINK = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
    mdInstance.core.ruler.push("wikilink", (state) => {
      const text = (content) =>
        Object.assign(new state.Token("text", "", 0), { content });
      for (const tok of state.tokens) {
        if (tok.type !== "inline") continue;
        tok.children = tok.children.flatMap((child) => {
          if (child.type !== "text" || !child.content.includes("[[")) {
            return [child];
          }
          const out = [];
          let at = 0;
          for (const m of child.content.matchAll(WIKILINK)) {
            if (m.index > at) out.push(text(child.content.slice(at, m.index)));
            const open = new state.Token("link_open", "a", 1);
            open.attrs = [
              ["class", "wikilink"],
              ["href", "#"],
              ["data-wiki", m[1].trim()],
            ];
            out.push(
              open,
              text((m[2] || m[1]).trim()),
              new state.Token("link_close", "a", -1),
            );
            at = m.index + m[0].length;
          }
          if (at < child.content.length) {
            out.push(text(child.content.slice(at)));
          }
          return out;
        });
      }
    });
  }
  const doc = node.section?.root || node;
  const dir = typeof doc.rel === "string"
    ? (doc.vpath ? `${doc.rel}/${doc.vpath}` : doc.rel).replace(/\/?[^/]*$/, "")
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
  return inert(html.replace(
    /<pre class="code (\S+) literal-block"><code>/g,
    '<pre><code class="language-$1">',
  ));
}

/* ── Converter output ────────────────────────────────────────────────────── */
/* docutils and mammoth escape a document's text but write a link's target as
   the document gives it, javascript: included, and their HTML lands in this
   page (A2). So an event handler never stays, a link keeps its target only
   when core/model/safe-url.js allows it, and a picture may also be inline
   image data. A .docx can carry a style map naming any element, so its output
   may also keep only the tags and attributes mammoth itself writes; any other
   element is replaced by its contents. DOMParser builds an inert document:
   nothing in it loads or runs while it is checked. */
const DOCX = {
  tags: new Set(
    ("a br dd div dl dt em h1 h2 h3 h4 h5 h6 img li ol p pre s strong sub sup " +
      "table tbody td th thead tr u ul").split(" "),
  ),
  attrs: new Set(["alt", "colspan", "href", "id", "rowspan", "src"]),
};

function inert(html, allow) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  for (const el of doc.body.querySelectorAll("*")) {
    if (allow && !allow.tags.has(el.localName)) {
      el.replaceWith(...el.childNodes);
      continue;
    }
    for (const { name, value } of [...el.attributes]) {
      if (
        (allow && !allow.attrs.has(name)) || name.startsWith("on") ||
        (name === "href" && !safeURL(value)) ||
        (name === "src" && !safeURL(value) && !/^data:image\//i.test(value))
      ) el.removeAttribute(name);
    }
  }
  return doc.body.innerHTML;
}

/* ── The entries ─────────────────────────────────────────────────────────── */
async function unzipPptx(blob) {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  const view = new DataView(bytes.buffer);
  if (
    bytes.length < 4 ||
    ![0x04034b50, 0x06054b50].includes(view.getUint32(0, true))
  ) {
    throw new Error("Invalid ZIP archive");
  }
  const slides = [];
  for (
    let at = 0;
    at + 30 <= bytes.length && view.getUint32(at, true) === 0x04034b50;
  ) {
    const method = view.getUint16(at + 8, true);
    const compressed = view.getUint32(at + 18, true);
    const nameSize = view.getUint16(at + 26, true);
    const extraSize = view.getUint16(at + 28, true);
    const name = new TextDecoder().decode(
      bytes.subarray(at + 30, at + 30 + nameSize),
    );
    const start = at + 30 + nameSize + extraSize;
    const end = start + compressed;
    if (end > bytes.length) throw new Error("truncated ZIP entry");
    if (/^ppt\/slides\/slide\d+\.xml$/.test(name)) {
      let data = bytes.slice(start, end);
      if (method === 8) {
        data = new Uint8Array(
          await new Response(
            new Blob([data]).stream().pipeThrough(
              new DecompressionStream("deflate-raw"),
            ),
          ).arrayBuffer(),
        );
      } else if (method !== 0) {
        throw new Error("unsupported ZIP compression");
      }
      const xml = new DOMParser().parseFromString(
        new TextDecoder().decode(data),
        "application/xml",
      );
      const text = [...xml.getElementsByTagNameNS("*", "p")]
        .map((paragraph) =>
          [...paragraph.getElementsByTagNameNS("*", "t")]
            .map((run) => run.textContent).join(" ")
        )
        .filter(Boolean).join("\n").trim();
      slides.push({ number: Number(name.match(/slide(\d+)/)[1]), text });
    }
    at = end;
  }
  return slides.sort((a, b) => a.number - b.number);
}

const pptxHTML = async (_node, blob) => {
  try {
    const slides = await unzipPptx(blob);
    if (!slides.length) {
      return '<div class="preview-empty">PowerPoint has no slides.</div>';
    }
    return `<div class="pv-pptx">${
      slides.map(({ number, text }) =>
        `<section class="slide"><h2>Slide ${number}</h2><p>${
          esc(text) || "(No slide text)"
        }</p></section>`
      ).join("")
    }</div>`;
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
  return `<div class="pv-rich">${inert(value, DOCX)}</div>`;
};

/* A text renderer: oversize files take the plain path, like the local one. */
const richText = (convert, className = "") => async (node, blob) => {
  if (blob.size > TEXT_MAX) return renderNode(node, blob, "text");
  return `<div class="pv-rich${
    className ? ` ${className}` : ""
  }">${await convert(await blob.text(), node)}</div>`;
};

/* Offline, blocked, or the CDN moved. The file is still readable. */
const offlineHTML = async (node, blob) => {
  const fallback = await renderNode(node, blob, "text");
  return fallback ? NOTE + fallback : null;
};

export const RICH_RENDERERS = [
  {
    kind: "md",
    render: richText(markdown, "pv-markdown"),
    fallback: "offline",
  },
  {
    kind: "markdown",
    render: richText(markdown, "pv-markdown"),
    fallback: "offline",
  },
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
    /* By the file's own kind: a member of an archive is "virtual" to
       classifyFile, and its bytes arrive through FS.blob all the same. */
    const kind = fileKind(node);
    const need = NEEDS[kind];
    if (
      (!need && kind !== "pptx") || (need && !richEnabled() && !vendored(need))
    ) {
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
  /* The file itself may be the open column (a Markdown file browsed by its
     headings, adapters/vfs-doc.js); the folder is the column holding it. */
  let col = path.length - 1;
  while (col > 0 && (path[col].doc || path[col].section)) col--;
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
