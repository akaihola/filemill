/* ═══════════════════════════════════════════════════════════════════════════
   Opening a folder — the only entry point into the tree.

   The picked handle is kept in IndexedDB (FileSystemHandle is structured-
   cloneable), so a reload can offer the same folder back. queryPermission()
   needs no user gesture; requestPermission() does — hence the second button.
   ═══════════════════════════════════════════════════════════════════════════ */
const idb = () => new Promise((res, rej) => {
  const r = indexedDB.open("filemill", 1);
  r.onupgradeneeded = e => e.target.result.createObjectStore("kv");
  r.onsuccess = e => res(e.target.result);
  r.onerror   = e => rej(e.target.error);
});

async function rememberRoot(handle) {
  try {
    const db = await idb();
    db.transaction("kv", "readwrite").objectStore("kv").put(handle, "root");
  } catch (err) { console.warn("could not remember folder:", err); }
}

async function recallRoot() {
  try {
    const db = await idb();
    const st = db.transaction("kv", "readonly").objectStore("kv");
    return await new Promise((res, rej) => {
      const r = st.get("root");
      r.onsuccess = () => res(r.result || null);
      r.onerror   = () => rej(r.error);
    });
  } catch (err) { return null; }
}
