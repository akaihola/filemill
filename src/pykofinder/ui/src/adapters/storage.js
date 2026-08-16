/* ═══════════════════════════════════════════════════════════════════════════
   Remembering folders across sessions.

   FileSystemHandle is structured-cloneable, so the picked roots survive in
   IndexedDB and the OS folder dialog is not needed twice for the same folder.
   What does NOT survive is the *permission*: Chrome usually downgrades it to
   "prompt" when the tab session ends, and requestPermission() needs a user
   gesture. So a remembered folder is either re-mounted silently (still
   'granted') or offered as a one-click button on the welcome screen.
   ═══════════════════════════════════════════════════════════════════════════ */
const RECENT_MAX = 8;

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

async function rememberRoot(handle) {
  try {
    const db = await idb();
    const kept = [];
    for (const h of (await kvGet(db, "recent")) || [])
      if (!(await h.isSameEntry(handle))) kept.push(h);   /* same folder, one entry */
    kvPut(db, "recent", [handle, ...kept].slice(0, RECENT_MAX));
  } catch (err) { console.warn("could not remember folder:", err); }
}

async function recallRoots() {
  try {
    const db = await idb();
    return (await kvGet(db, "recent")) || [];
  } catch (err) { return []; }         /* private mode, file://, … — just ask */
}

async function forgetRoots() {
  try { kvPut(await idb(), "recent", []); } catch (err) { /* nothing to forget */ }
}
