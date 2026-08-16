/* ═══════════════════════════════════════════════════════════════════════════
   Server build — boot, and the switch to a local folder.

   The counterpart of app-fsa.js. Both load the same core/; the only difference
   is which adapters they hand it, and where the root comes from — here the
   server already has one, so there is no welcome screen to get past.

   "Open local folder…" is the reason this file is not just three lines: the
   page can re-point the FS and PREVIEW ports at the browser's own filesystem
   at runtime and keep every other thing about the app identical. Nothing in
   core/ notices.
   ═══════════════════════════════════════════════════════════════════════════ */
const ROOT_NAME = document.documentElement.dataset.root || "/";

/* Local mode gives up the address bar: a URL path names a file under the
   *server's* root, and a folder the browser granted is not under it.
   Pretending otherwise would produce links that resolve to the wrong file —
   hence useRouter(null) below, and the badge that says which side you are on. */

async function mountServer() {
  useFilesystem(HTTP);
  usePreview(PreviewHTTP);
  useRouter(RouterPath);

  /* Read the link *before* the first render. render() syncs the URL, and the
     state it syncs from is the bare root — so rendering first would rewrite
     /notes/deep/leaf.md down to / and then faithfully restore nothing. */
  const loc = RouterPath.read();

  const node = HTTP.node(ROOT_NAME, "");
  colCache.clear();
  path = [node]; sel = []; focusCol = 0; cursor = { 0: 0 };
  if (welcome) welcome.hidden = true;
  document.title = ROOT_NAME;
  render();
  await FS.ensureLoaded(node);

  if (loc && loc.path.length) await applyPath(loc.path);
  else render();
  startRouting();
}

/* The local-folder mode of the server build. Previews still come from the
   Python renderers — see PreviewUpload — so switching sides costs no fidelity;
   only the URL goes quiet. */
async function mount(handle) {
  useFilesystem(FSA);
  usePreview(PreviewUpload);
  useRouter(null);
  const node = FSA.node(handle.name, handle);
  colCache.clear();
  path = [node]; sel = []; focusCol = 0; cursor = { 0: 0 };
  if (welcome) welcome.hidden = true;
  document.title = handle.name;
  /* Back to the bare base, not one segment up: the URL was naming a file
     under the server's root and nothing here is under it any more. */
  history.replaceState(null, "", RouterPath.base);
  render();
  await FS.ensureLoaded(node);
  render();
  setLocalBadge(handle.name);
}

async function pickFolder() {
  if (!window.showDirectoryPicker) {
    alert("This browser has no File System Access API. " +
          "Local folders need Chrome, Edge or another Chromium-based desktop browser.");
    return;
  }
  try {
    const handle = await window.showDirectoryPicker({ mode: "read", id: "filemill" });
    await rememberRoot(handle);
    await mount(handle);
  } catch (err) {
    if (err.name !== "AbortError") console.error(err);
  }
}

/* Going back to the server is a plain remount — the tree is server-owned, so
   there is nothing to hand back. */
function leaveLocal() {
  setLocalBadge(null);
  mountServer();
}

function setLocalBadge(name) {
  const b = document.getElementById("local-badge");
  if (!b) return;
  b.hidden = !name;
  if (name) b.querySelector(".nm").textContent = name;
}

document.getElementById("open")?.addEventListener("click", pickFolder);
document.getElementById("leave-local")?.addEventListener("click", leaveLocal);

mountServer();
document.fonts.ready.then(() => render(true));
