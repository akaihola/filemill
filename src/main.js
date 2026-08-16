/* ═══════════════════════════════════════════════════════════════════════════
   Opening a folder — the only entry point into the tree.
   ═══════════════════════════════════════════════════════════════════════════ */
async function mount(handle) {
  const node = mkNode(handle.name, handle);
  colCache.clear();
  path = [node]; sel = []; focusCol = 0; cursor = { 0: 0 };
  welcome.hidden = true;
  document.title = handle.name + " — filemill";
  render();
  await ensureLoaded(node);
  render();
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
  const handles = await recallRoots();
  if (!handles.length) return;
  /* queryPermission needs no gesture, so a folder still granted from an earlier
     visit opens with no dialog at all */
  if (await handles[0].queryPermission({ mode: "read" }) === "granted")
    return mount(handles[0]);
  renderRecents(handles);
})();

document.fonts.ready.then(() => render(true));
