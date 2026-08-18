/* ═══════════════════════════════════════════════════════════════════════════
   Static build — boot, folder picker, welcome screen.

   The only file that knows this is the local-folder flavour of the app. It
   picks the adapters (fsa + preview-local + router-hash, all loaded before
   this) and owns the one entry point into the tree, mount().
   ═══════════════════════════════════════════════════════════════════════════ */

/* Adapters define themselves; the app entry is what chooses. Selecting here
   rather than at the bottom of each adapter file means a page may load more
   than one of them — which the server build does — without script order
   silently deciding which wins. */
useFilesystem(FSA);
usePreview(PreviewRich);
useRouter(RouterHash);

/* A deep link read at startup, held until a root is mounted that can satisfy
   it — the URL names a folder, but a folder is not browsable until the browser
   has granted it. */
let pendingLoc = null;

async function mount(handle, loc) {
  const node = FS.node(handle.name, handle);
  colCache.clear();
  path = [node]; sel = []; focusCol = 0; cursor = { 0: 0 };
  welcome.hidden = true;
  document.title = handle.name + " — Filemill";
  render();
  await FS.ensureLoaded(node);

  const want = loc ?? takePending(handle.name);
  if (want && want.path.length) await applyPath(want.path);
  else render();
  startRouting();
}

/* A pending link only applies to the root it named — mounting some other folder
   must not try to walk that folder's path into it. */
function takePending(rootName) {
  const p = pendingLoc;
  pendingLoc = null;
  return p && (!p.root || p.root === rootName) ? p : null;
}

async function pickFolder() {
  if (!window.showDirectoryPicker) return showBlocked("unsupported");
  try {
    const handle = await window.showDirectoryPicker({ mode: "read", id: "filemill" });
    await rememberRoot(handle);
    await mount(handle);
  } catch (err) {
    if (err.name === "AbortError") return;
    /* Chrome refuses the picker on an opaque origin — i.e. a file:// page */
    if (err.name === "SecurityError") return showBlocked("file");
    console.error(err);
  }
}

/* Opening a remembered folder. 'granted' mounts straight away; anything else
   needs requestPermission(), which is only allowed from this click. */
async function openRemembered(handle) {
  const perm = await handle.queryPermission({ mode: "read" });
  if (perm === "granted" || await handle.requestPermission({ mode: "read" }) === "granted")
    return mount(handle);
}

function renderRecents(handles) {
  const box = document.getElementById("w-recent");
  const list = box.querySelector(".rec-list");
  list.textContent = "";
  handles.forEach(h => {
    const b = document.createElement("button");
    b.className = "rec";
    b.innerHTML = `<svg viewBox="0 0 16 16" aria-hidden="true">${FOLDER_PATH}</svg>`;
    b.appendChild(document.createTextNode(h.name));
    b.onclick = () => openRemembered(h);
    list.appendChild(b);
  });
  box.hidden = !handles.length;
}

/* Both failure modes end at the welcome screen, since there is nothing to show
   without a folder. Keep the wording actionable — the fix differs per case. */
function showBlocked(why) {
  welcome.hidden = false;
  document.getElementById("w-pick").hidden = why === "unsupported";
  document.getElementById("w-recent").hidden = true;
  document.getElementById("w-msg").innerHTML = why === "unsupported"
    ? "This browser has no File System Access API, so local folders cannot be opened. " +
      "Try Chrome, Edge or another Chromium-based desktop browser."
    : "Chrome blocks folder access on <code>file://</code> pages. Serve this file over " +
      "localhost instead:<br><code>python3 -m http.server -d " +
      "&lt;folder containing index.html&gt;</code><br>then open " +
      "<code>http://localhost:8000/index.html</code>.";
}

document.getElementById("open").onclick = pickFolder;
document.getElementById("w-pick").onclick = pickFolder;

(async function start() {
  if (!window.showDirectoryPicker) return showBlocked("unsupported");
  if (location.protocol === "file:") return showBlocked("file");

  pendingLoc = ROUTER.read();
  const handles = await recallRoots();
  if (!handles.length) return;

  /* A link names its root, so prefer that folder over the most recent one —
     otherwise reopening a bookmark would silently browse the wrong tree. */
  const wanted = pendingLoc?.root
    ? handles.find(h => h.name === pendingLoc.root) : null;
  const first = wanted || handles[0];

  /* queryPermission needs no gesture, so a folder still granted from an earlier
     visit opens with no dialog at all */
  if (await first.queryPermission({ mode: "read" }) === "granted") return mount(first);
  renderRecents(handles);
})();

document.fonts.ready.then(() => render(true));
