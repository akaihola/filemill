/* ═══════════════════════════════════════════════════════════════════════════
   Filesystem — File System Access API, read-only, loaded one level at a time.

   Node shape mirrors the design study's mock nodes so the renderer is
   unchanged:  { name, dir, kids }  — plus a handle and lazy metadata.
     kids === null   directory not read yet
     kids === []     read, and empty (or unreadable — see .denied)
   ═══════════════════════════════════════════════════════════════════════════ */
const mkNode = (name, handle) => ({
  name, handle,
  dir: handle.kind === "directory",
  kids: handle.kind === "directory" ? null : undefined,
});

async function ensureLoaded(node) {
  if (!node.dir || node.kids !== null) return;
  if (node.loading) return node.loading;          /* debounce concurrent calls */
  node.loading = (async () => {
    const kids = [];
    try {
      for await (const [name, handle] of node.handle.entries()) kids.push(mkNode(name, handle));
    } catch (err) {
      node.denied = err.name === "NotAllowedError" ? "No permission to read" : String(err.message || err);
    }
    node.kids = kids;
    node.loading = null;
  })();
  return node.loading;
}

/* File metadata is a separate round-trip per file — only fetched on preview. */
async function loadMeta(node) {
  if (node.dir || node.meta) return;
  try {
    const file = await node.handle.getFile();
    node.meta = { size: file.size, mod: file.lastModified, type: file.type };
    node.file = file;
  } catch (err) {
    node.meta = { error: String(err.message || err) };
  }
}

const fmtSize = b =>
  b < 1024 ? `${b} B`
  : b < 1024 ** 2 ? `${(b / 1024).toFixed(b < 10240 ? 1 : 0)} KB`
  : b < 1024 ** 3 ? `${(b / 1024 ** 2).toFixed(1)} MB`
  : `${(b / 1024 ** 3).toFixed(2)} GB`;

const fmtDate = ms => new Date(ms).toLocaleString(undefined,
  { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
