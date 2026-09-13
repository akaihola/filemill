/* ═══════════════════════════════════════════════════════════════════════════
   Remembering folders across sessions.

   FileSystemHandle is structured-cloneable, so the picked roots survive in
   IndexedDB and the OS folder dialog is not needed twice for the same folder.
   What does NOT survive is the *permission*: Chrome usually downgrades it to
   "prompt" when the tab session ends, and requestPermission() needs a user
   gesture. So a remembered folder is either re-mounted silently (still
   'granted') or offered as a one-click button on the welcome screen.

   A record is the handle *and* the selection chain inside it:

       { handle: FileSystemDirectoryHandle, path: ["src", "core", "nav.js"] }

   The chain is a list of names rather than nodes, because a node is built from
   a read that has not happened yet when the page loads, and a name survives
   anything. It is the same list a deep link carries, so one walk restores both.
   ═══════════════════════════════════════════════════════════════════════════ */
const RECENT_MAX = 8;

/* Databases written before the chain existed hold a bare handle. Normalising on
   read is what keeps those folders in the list instead of dropping eight of
   them the first time a user loads a newer build. */
const asRoot = r => (r && r.kind === "directory") ? { handle: r, path: [] } : r;

const idb = () => new Promise((res, rej) => {
  const r = indexedDB.open("filemill", 1);
  r.onupgradeneeded = e => e.target.result.createObjectStore("kv");
  r.onsuccess = e => res(e.target.result);
  r.onerror   = e => rej(e.target.error);
});

const kvGet = (db, key) => new Promise((res, rej) => {
  const r = db.transaction("kv", "readonly").objectStore("kv").get(key);
  r.onsuccess = () => res(r.result);
  r.onerror   = () => rej(r.error);
});

const kvPut = (db, key, value) =>
  db.transaction("kv", "readwrite").objectStore("kv").put(value, key);

/* Move a root to the front of the list. `path` is the selection chain inside
   it; leave it out and whatever was stored stays, because picking the same
   folder again from the OS dialog must not forget where you were in it. */
async function rememberRoot(handle, path) {
  try {
    const db = await idb();
    const kept = [];
    let had = null;
    for (const r of ((await kvGet(db, "recent")) || []).map(asRoot))
      if (await r.handle.isSameEntry(handle)) had = r;    /* same folder, one entry */
      else kept.push(r);
    kvPut(db, "recent", [{ handle, path: path ?? had?.path ?? [] }, ...kept]
      .slice(0, RECENT_MAX));
  } catch (err) { console.warn("could not remember folder:", err); }
}

async function recallRoots() {
  try {
    const db = await idb();
    return ((await kvGet(db, "recent")) || []).map(asRoot);
  } catch (err) { return []; }         /* private mode, file://, … — just ask */
}

/* The chain stored for one folder, in the shape applyPath already speaks. Null
   when the folder is new, or was last left sitting on its own root — there is
   nothing to restore then, and mounting plainly is the honest result. */
async function recallView(handle) {
  for (const r of await recallRoots())
    if (await r.handle.isSameEntry(handle))
      return r.path.length ? { root: handle.name, path: r.path } : null;
  return null;
}
