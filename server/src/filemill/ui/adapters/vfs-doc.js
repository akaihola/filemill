/* ═══════════════════════════════════════════════════════════════════════════
   Documents — Markdown and reStructuredText browsed by their headings.

   The counterpart of adapters/vfs-json.js for prose: a `.md` or `.rst` file
   opens as a column of its top-level sections, a section with subsections
   opens as another column, and a section previews as its own slice of the
   file, rendered the way the whole file would be. Both builds get it by
   wrapping their FS and PREVIEW ports here — see adapters/app-fsa.js and
   adapters/app-http.js — so core/ still sees nothing but nodes.

   Unlike a JSON file, the document is still a file: selected in its folder it
   previews whole, it can be edited and deleted, and its icon is its own
   (`doc` on the node; see core/file-kind.js and core/ports.js). A file whose
   only heading is its title has no hierarchy and stays a plain file, as does
   one over TEXT_MAX; a lone title at the top names the file, so its
   subsections are the first column. Those rules and the outline itself are
   the model's, core/model/headings.js, tested without a browser; here they
   are only turned into nodes.
   ═══════════════════════════════════════════════════════════════════════════ */
import { TEXT_MAX } from "../core/limits.js";
import { classifyFile } from "../core/file-kind.js";
import { sections } from "../core/model/headings.js";

const DOC_KINDS = new Set(["md", "markdown", "rst"]);
/* A member of an archive (it has a vpath; see adapters/http.js) browses by
   its headings too when the browser renders it: a Markdown member reads and
   renders from its own bytes exactly like the file on disk. A
   reStructuredText member stays a plain file, because its sections render on
   the server, which has no route for a member plus a line span. */
const MEMBER_DOC_KINDS = new Set(["md", "markdown"]);
const isDoc = (n) =>
  !n.dir &&
  (n.vpath ? MEMBER_DOC_KINDS : DOC_KINDS).has(classifyFile(n.name).preview);

/* vpath is only a stable address for the shared router and server-shaped
   nodes, as in vfs-json.js; the URL names a section by its heading text. */
const sectionNode = (root, parent, section, i) => ({
  name: section.name,
  dir: section.kids.length > 0,
  kids: section.kids.length ? null : undefined,
  vpath: parent.vpath ? `${parent.vpath}/${i}` : String(i),
  icon: "§",
  section: { root, outline: section },
  rel: root.rel,
  ordered: true,
  meta: { virtual: true },
});

const sectionKids = (node) =>
  node.section.outline.kids.map((k, i) =>
    sectionNode(node.section.root, node, k, i)
  );

const sectionText = (n) =>
  n.section.root.lines.slice(n.section.outline.start, n.section.outline.end)
    .join("\n");

/* The doc is a directory to core; the port still reads it as the file it is. */
const asFile = (node) => ({ ...node, dir: false });

function loadDoc(fs, node) {
  if (node.loading) return node.loading;
  node.loading = (async () => {
    try {
      const blob = await fs.blob(asFile(node));
      if (!blob || blob.size > TEXT_MAX) throw new Error("not browsable");
      const text = await blob.text();
      const found = sections(text, classifyFile(node.name).preview);
      if (!found.length) throw new Error("nothing to browse");
      node.lines = text.split("\n");
      node.kids = found.map((s, i) => sectionNode(node, node, s, i));
    } catch {
      /* declined: the row is a plain file again, and nav.js / deeplink.js
         notice `dir` turning false while they were reading */
      node.dir = false;
      node.kids = undefined;
      node.lines = undefined;
    }
    node.loading = null;
  })();
  return node.loading;
}

export const withDocuments = (fs) => ({
  ...fs,
  async ensureLoaded(node) {
    if (node.section) {
      if (node.kids === null) node.kids = sectionKids(node);
      return;
    }
    if (node.doc) {
      if (node.kids !== null) return;
      return loadDoc(fs, node);
    }
    await fs.ensureLoaded(node);
    for (const k of node.kids || []) {
      if (isDoc(k)) {
        /* ordered: sections keep the file's order under a name sort */
        Object.assign(k, { dir: true, kids: null, doc: true, ordered: true });
      }
    }
  },

  async loadMeta(node) {
    if (!node.doc) return fs.loadMeta(node);
    const file = asFile(node);
    await fs.loadMeta(file);
    node.meta = file.meta;
    node.file = file.file;
  },

  async blob(node) {
    if (node.section) return new Blob([sectionText(node)]);
    return fs.blob(node.doc ? asFile(node) : node);
  },

  ...(fs.write && {
    /* The save goes to the file; the sections it was browsed by are stale
       the moment it lands, so an open outline is rebuilt from the new text. */
    async write(node, text) {
      await fs.write(node, text);
      if (node.doc && node.kids !== null) {
        node.lines = text.split("\n");
        node.kids = sections(text, classifyFile(node.name).preview)
          .map((s, i) => sectionNode(node, node, s, i));
      }
    },
  }),
});

export const withDocumentPreview = (provider) => ({
  revoke() {
    provider.revoke?.();
  },
  render(n) {
    if (!n.section) return provider.render(n);
    /* A section renders as the file it is part of: same name, same kind, same
       renderer; only the bytes — FS.blob above — are the section's slice. */
    const root = n.section.root;
    return provider.render({
      ...n,
      name: root.name,
      rel: root.rel,
      dir: false,
      vpath: "",
      icon: undefined,
      fileKind: root.fileKind,
    });
  },
});
