/* ════════════════════════════════════════════════════════════════
   IndexedDB persistence for FSA handles
   (handles are structured-cloneable; queryPermission needs no gesture)
   ════════════════════════════════════════════════════════════════ */
async function _fsaDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('fndr-fsa', 1);
    req.onupgradeneeded = e => e.target.result.createObjectStore('handles', { keyPath: 'label' });
    req.onsuccess = e => resolve(e.target.result);
    req.onerror   = e => reject(e.target.error);
  });
}

async function saveFSAHandlesToIDB() {
  try {
    const db    = await _fsaDB();
    const tx    = db.transaction('handles', 'readwrite');
    const store = tx.objectStore('handles');
    store.clear();
    for (const si of SIDEBAR_ITEMS) {
      if (si.type === 'fsa' && si.node?.handle) {
        store.put({ label: si.label, handle: si.node.handle });
      }
    }
    await new Promise((res, rej) => { tx.oncomplete = res; tx.onerror = rej; });
  } catch (e) { console.warn('FSA IDB save failed:', e); }
}

async function restoreFSAHandlesFromIDB() {
  try {
    const db    = await _fsaDB();
    const tx    = db.transaction('handles', 'readonly');
    const items = await new Promise((res, rej) => {
      const r = tx.objectStore('handles').getAll();
      r.onsuccess = e => res(e.target.result);
      r.onerror   = rej;
    });
    let added = 0;
    for (const { label, handle } of items) {
      // Only restore handles for which permission is already granted —
      // requestPermission() needs a user gesture; queryPermission() does not.
      const perm = await handle.queryPermission({ mode: 'read' });
      if (perm !== 'granted') continue;
      if (SIDEBAR_ITEMS.find(s => s.type === 'fsa' && s.label === label)) continue;
      const rootNode = makeFSANode(handle.name, handle);
      SIDEBAR_ITEMS.unshift({ label, icon: sidebarFolderIcon('#1070cf'), type: 'fsa', node: rootNode });
      // Compensate: unshift shifts all indices up by 1
      activeSidebarIdx++;
      added++;
    }
    if (added > 0) { render(); console.log(`FSA: restored ${added} handle(s) from IDB`); }
  } catch (e) { console.warn('FSA IDB restore failed:', e); }
}

/* ════════════════════════════════════════════════════════════════
   File System Access API — lazy loading
   ════════════════════════════════════════════════════════════════ */

function makeFSANode(name, handle) {
  return {
    name,
    type: handle.kind === 'directory' ? 'folder' : getFileType(name),
    handle,
    // null = directory not yet loaded; undefined = not applicable (file)
    children: handle.kind === 'directory' ? null : undefined,
    _loading: false,
    _metaLoaded: false,
  };
}

async function ensureLoaded(node) {
  // Only directories with unloaded children need loading
  if (!node || node.children !== null || node.handle?.kind !== 'directory') return;
  // Debounce concurrent calls
  if (node._loading) {
    while (node._loading) await new Promise(r => setTimeout(r, 30));
    return;
  }
  node._loading = true;
  render(); // show spinner immediately
  try {
    const children = [];
    for await (const [name, handle] of node.handle.entries()) {
      if (!name.startsWith('.')) children.push(makeFSANode(name, handle));
    }
    children.sort((a, b) => {
      const af = a.type === 'folder', bf = b.type === 'folder';
      if (af !== bf) return af ? -1 : 1;
      return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
    });
    node.children = children;
  } catch (err) {
    console.warn('Cannot read', node.name, err);
    node.children = [];
  }
  node._loading = false;
}

async function loadFileMeta(node) {
  if (!node.handle || node.handle.kind !== 'file' || node._metaLoaded) return;
  try {
    const file = await node.handle.getFile();
    node.size     = formatFileSize(file.size);
    node.modified = formatDate(file.lastModified);
    node._metaLoaded = true;
  } catch (e) { /* permission denied etc. */ }
}

async function openFolderPicker() {
  if (!window.showDirectoryPicker) {
    alert('File System Access API not supported.\nUse Chrome or Edge (desktop).');
    return;
  }
  try {
    const handle = await window.showDirectoryPicker({ mode: 'read' });
    const rootNode = makeFSANode(handle.name, handle);

    // Prepend to sidebar as an FSA entry (before ensureLoaded so sidebar shows immediately)
    const existing = SIDEBAR_ITEMS.findIndex(s => s.type === 'fsa' && s.label === handle.name);
    if (existing >= 0) SIDEBAR_ITEMS.splice(existing, 1);
    SIDEBAR_ITEMS.unshift({
      label: handle.name,
      icon: sidebarFolderIcon('#1070cf'),
      type: 'fsa',
      node: rootNode,
    });
    activeSidebarIdx = 0; // select the new entry

    // Wire up state BEFORE ensureLoaded so the spinner renders into the correct column
    sidebarRootNode = rootNode;
    sidebarRootPath = [handle.name];
    columns         = [{ node: rootNode, selectedName: null }];
    selectedFile    = null;

    await ensureLoaded(rootNode); // render() inside now shows spinner in col 0
    render();
    pushHistory();
    saveFSAHandlesToIDB();        // persist so it survives hot-reload / page refresh
  } catch (err) {
    if (err.name !== 'AbortError') console.error('FSA:', err);
  }
}
