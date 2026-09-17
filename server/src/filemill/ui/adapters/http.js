/* ═══════════════════════════════════════════════════════════════════════════
   Filesystem adapter — a server, over fetch.

   Fills the FS port (see core/ports.js). The counterpart of fsa.js: same node
   shape, same two calls, so core/ cannot tell the difference.

   One round-trip returns names, kinds, sizes and mtimes together, so unlike the
   File System Access API there is no per-file syscall — loadMeta is already
   satisfied by the listing. That is what makes server-side sorting by size or
   date affordable, where the local build would need a getFile() sweep.
   ═══════════════════════════════════════════════════════════════════════════ */
import { render } from "../core/render.js";
import { classifyFile } from "../core/file-kind.js";
import { focusCol, path, sel, setState } from "../core/state.js";

export const API = document.documentElement.dataset.api || "/api";

/* Nodes carry their root-relative path instead of a handle. Joining here rather
   than in the caller keeps the root itself at "" — the server's own idea of the
   root — instead of leaking the root's display name into every request. */
const relOf = (parentRel, name) => (parentRel ? parentRel + "/" + name : name);

/* `vpath` is a path *inside* a file: a table in a SQLite database, a key in a
   JSON document. Such an entry keeps its parent's `rel` — the file on disk is
   the same one — and descends virtually instead. The server tells them apart by
   putting a `vpath` on the entries it returns; there is nothing to detect here,
   and core/ never learns that virtual nodes exist at all. */
const httpNode = (name, rel, dir, meta, vpath, icon, ordered = false) => ({
  name,
  rel,
  dir,
  ordered,
  vpath: vpath || "",
  icon: icon || undefined,
  kids: dir ? null : undefined,
  meta: meta || undefined,
  fileKind: classifyFile(name, { dir, vpath }),
});

const q = (rel, vpath) =>
  `${API}/dir?p=${encodeURIComponent(rel)}` +
  (vpath ? `&v=${encodeURIComponent(vpath)}` : "");

const pageQ = (rel, vpath, page) => `${q(rel, vpath)}&page=${page}`;

export const HTTP = {
  node: (name, rel) => httpNode(name, rel || "", true),

  async ensureLoaded(node) {
    if (!node.dir || node.kids !== null) return;
    if (node.loading) return node.loading;
    node.loading = (async () => {
      try {
        const r = await fetch(pageQ(node.rel, node.vpath, 1), {
          headers: { Accept: "application/json" },
        });
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        const j = await r.json();
        node.denied = j.denied || undefined;
        node.page = j.page;
        node.pages = j.pages;
        node.total = j.total;
        node.kids = (j.entries || []).map((e) =>
          e.vpath !== undefined
            /* virtual: same file, deeper key */
            ? httpNode(
              e.name,
              node.rel,
              e.dir,
              { virtual: true },
              e.vpath,
              e.icon,
              e.ordered,
            )
            : httpNode(
              e.name,
              relOf(node.rel, e.name),
              e.dir,
              e.dir ? undefined : { size: e.size, mod: e.mod },
            )
        );
      } catch (err) {
        node.denied = String(err.message || err);
        node.kids = [];
      }
      node.loading = null;
    })();
    return node.loading;
  },

  async loadPage(node, page) {
    if (!node.pages || page < 1 || page > node.pages || node.loading) return;
    node.loading = (async () => {
      const r = await fetch(pageQ(node.rel, node.vpath, page), {
        headers: { Accept: "application/json" },
      });
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
      const j = await r.json();
      const i = path.indexOf(node);
      if (i >= 0) {
        setState({
          path: path.slice(0, i + 1),
          sel: sel.slice(0, i),
          focusCol: Math.min(focusCol, i),
        });
      }
      node.kids = (j.entries || []).map((e) =>
        e.vpath !== undefined
          ? httpNode(
            e.name,
            node.rel,
            e.dir,
            { virtual: true },
            e.vpath,
            e.icon,
            e.ordered,
          )
          : httpNode(
            e.name,
            relOf(node.rel, e.name),
            e.dir,
            e.dir ? undefined : { size: e.size, mod: e.mod },
          )
      );
      node.page = j.page;
      node.pages = j.pages;
      node.total = j.total;
      node.loading = null;
    })();
    try {
      await node.loading;
    } catch (err) {
      node.denied = String(err.message || err);
      node.loading = null;
    }
    render();
  },

  /* The listing already carried it — or there is none to carry, for a node
     that is not a file. Either way there is nothing to fetch. */
  async loadMeta(node) {
    if (!node.dir && !node.meta) node.meta = { error: "no metadata" };
  },

  async blob(node) {
    const r = await fetch(`${API}/raw?p=${encodeURIComponent(node.rel)}`);
    return r.ok ? await r.blob() : null;
  },

  /* Optional — see ports.js. POST the whole new content; the reply carries the
     fresh {size, mod}, so the pane's sub-line stays truthful after a save. */
  async write(node, text) {
    const r = await fetch(`${API}/save?p=${encodeURIComponent(node.rel)}`, {
      method: "POST",
      body: text,
    });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    node.meta = await r.json();
  },

  async remove(node) {
    if (node.vpath) throw new Error("Virtual entries cannot be deleted");
    const r = await fetch(`${API}/delete?p=${encodeURIComponent(node.rel)}`, {
      method: "DELETE",
    });
    if (!r.ok) {
      let message = `${r.status} ${r.statusText}`;
      try {
        message = (await r.json()).error || message;
      } catch (_) { /* text error */ }
      throw new Error(message);
    }
  },
};
