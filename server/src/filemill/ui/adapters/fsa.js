/* ═══════════════════════════════════════════════════════════════════════════
   Filesystem adapter — File System Access API, one level at a time.

   Fills the FS port (see core/ports.js). Nodes carry the handle they came
   from; nothing else in the app ever touches it. write() and remove() ask for
   readwrite permission first; reading needs only the picker's grant.
   ═══════════════════════════════════════════════════════════════════════════ */
import { classifyFile } from "../core/file-kind.js";

const revisionOf = async (blob) =>
  Array.from(
    new Uint8Array(
      await crypto.subtle.digest("SHA-256", await blob.arrayBuffer()),
    ),
    (b) => b.toString(16).padStart(2, "0"),
  ).join("");

const FSA_COLLATOR = new Intl.Collator(undefined, { numeric: true });

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
      node.kids = kids.sort((a, b) => {
        const kind = !!b.dir - !!a.dir;
        return kind || FSA_COLLATOR.compare(a.name, b.name);
      });
      node.ordered = true;
      node.loading = null;
    })();
    return node.loading;
  },

  invalidate(node) {
    node.file = null;
    node.meta = undefined;
  },

  /* File metadata is a separate round-trip per file — fetched on preview, or
     per row when the sort is by size or modified time (core/sort.js). */
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
    const blob = node.file || null;
    if (blob) blob.revision = node.revision = await revisionOf(blob);
    return blob;
  },

  /* Optional — see ports.js. A picked folder can be written back through its
     handles; the permission prompt is the browser's own. */
  async write(node, text, expected = node.revision) {
    if (
      node.handle.requestPermission &&
      await node.handle.requestPermission({ mode: "readwrite" }) !== "granted"
    ) {
      throw new Error("No permission to write");
    }
    const current = await node.handle.getFile();
    if (!expected || expected !== await revisionOf(current)) {
      throw new Error("Conflict: file changed; draft kept");
    }
    const w = await node.handle.createWritable();
    try {
      await w.write(text);
      // A picker grants no compare-and-swap primitive. Recheck before commit.
      if (expected !== await revisionOf(await node.handle.getFile())) {
        throw new Error("Conflict: file changed; draft kept");
      }
      await w.close();
    } catch (error) {
      try {
        await w.abort();
      } catch (_) { /* Preserve the original error. */ }
      throw error;
    }
    node.revision = await revisionOf(new Blob([text]));
    node.file = null; /* stale — reread on the next preview */
    node.meta = null;
  },

  async remove(node) {
    if (!node.parent) throw new Error("Cannot delete this entry");
    if (
      node.parent.requestPermission &&
      await node.parent.requestPermission({ mode: "readwrite" }) !== "granted"
    ) {
      throw new Error("No permission to delete");
    }
    await node.parent.removeEntry(node.name, { recursive: node.dir });
  },
};
