/* ═══════════════════════════════════════════════════════════════════════════
   Filesystem adapter — File System Access API, read-only, one level at a time.

   Fills the FS port (see core/ports.js). Nodes carry the handle they came
   from; nothing else in the app ever touches it.
   ═══════════════════════════════════════════════════════════════════════════ */
import { classifyFile } from "../core/file-kind.js";

const fsaNode = (name, handle, parent = null) => ({
  name,
  handle,
  parent,
  dir: handle.kind === "directory",
  kids: handle.kind === "directory" ? null : undefined,
  fileKind: classifyFile(name, { dir: handle.kind === "directory" }),
});

export const FSA = {
  node: fsaNode,

  async ensureLoaded(node) {
    if (!node.dir || node.kids !== null) return;
    if (node.loading) return node.loading; /* debounce concurrent calls */
    node.loading = (async () => {
      const kids = [];
      try {
        for await (const [name, handle] of node.handle.entries()) {
          kids.push(fsaNode(name, handle, node.handle));
        }
      } catch (err) {
        node.denied = err.name === "NotAllowedError"
          ? "No permission to read"
          : String(err.message || err);
      }
      node.kids = kids;
      node.loading = null;
    })();
    return node.loading;
  },

  /* File metadata is a separate round-trip per file — only fetched on preview. */
  async loadMeta(node) {
    if (node.dir || node.meta) return;
    try {
      const file = await node.handle.getFile();
      node.meta = { size: file.size, mod: file.lastModified, type: file.type };
      node.file = file;
    } catch (err) {
      node.meta = { error: String(err.message || err) };
    }
  },

  /* The preview providers read bytes through this, so they never need to know
     whether the node came from a handle or a URL. */
  async blob(node) {
    await FSA.loadMeta(node);
    return node.file || null;
  },

  /* Optional — see ports.js. A picked folder can be written back through its
     handles; the permission prompt is the browser's own. */
  async write(node, text) {
    if (
      node.handle.requestPermission &&
      await node.handle.requestPermission({ mode: "readwrite" }) !== "granted"
    ) {
      throw new Error("No permission to write");
    }
    const w = await node.handle.createWritable();
    await w.write(text);
    await w.close();
    node.file = null; /* stale — reread on the next preview */
    node.meta = null;
  },

  async remove(node) {
    if (
      node.handle.requestPermission &&
      await node.handle.requestPermission({ mode: "readwrite" }) !== "granted"
    ) {
      throw new Error("No permission to delete");
    }
    if (!node.handle.parent) throw new Error("Cannot delete this entry");
    await node.handle.parent.removeEntry(node.name, { recursive: node.dir });
  },
};
