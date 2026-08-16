/* ═══════════════════════════════════════════════════════════════════════════
   Filesystem adapter — a server, over fetch.

   Fills the FS port (see core/ports.js). The counterpart of fsa.js: same node
   shape, same two calls, so core/ cannot tell the difference.

   One round-trip returns names, kinds, sizes and mtimes together, so unlike the
   File System Access API there is no per-file syscall — loadMeta is already
   satisfied by the listing. That is what makes server-side sorting by size or
   date affordable, where the local build would need a getFile() sweep.
   ═══════════════════════════════════════════════════════════════════════════ */
const API = (document.currentScript?.dataset.api) || "/api";

/* Nodes carry their root-relative path instead of a handle. Joining here rather
   than in the caller keeps the root itself at "" — the server's own idea of the
   root — instead of leaking the root's display name into every request. */
const relOf = (parentRel, name) => (parentRel ? parentRel + "/" + name : name);

const httpNode = (name, rel, dir, meta) => ({
  name, rel, dir,
  kids: dir ? null : undefined,
  meta: meta || undefined,
});

const q = rel => `${API}/dir?p=${encodeURIComponent(rel)}`;

const HTTP = {
  node: (name, rel) => httpNode(name, rel || "", true),

  async ensureLoaded(node) {
    if (!node.dir || node.kids !== null) return;
    if (node.loading) return node.loading;
    node.loading = (async () => {
      try {
        const r = await fetch(q(node.rel), { headers: { Accept: "application/json" } });
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        const j = await r.json();
        node.denied = j.denied || undefined;
        node.kids = (j.entries || []).map(e =>
          httpNode(e.name, relOf(node.rel, e.name), e.dir,
                 e.dir ? undefined : { size: e.size, mod: e.mod }));
      } catch (err) {
        node.denied = String(err.message || err);
        node.kids = [];
      }
      node.loading = null;
    })();
    return node.loading;
  },

  /* The listing already carried it. */
  async loadMeta(node) {
    if (!node.dir && !node.meta) node.meta = { error: "no metadata" };
  },

  async blob(node) {
    const r = await fetch(`${API}/raw?p=${encodeURIComponent(node.rel)}`);
    return r.ok ? await r.blob() : null;
  },

  rawURL: node => `${API}/raw?p=${encodeURIComponent(node.rel)}`,
};

useFilesystem(HTTP);
