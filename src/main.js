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

/* Both failure modes end at the welcome screen, since there is nothing to show
   without a folder. Keep the wording actionable — the fix differs per case. */
function showBlocked(why) {
  welcome.hidden = false;
  document.getElementById("w-pick").hidden = why === "unsupported";
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
  const handle = await recallRoot();
  if (!handle) return;
  if (await handle.queryPermission({ mode: "read" }) === "granted") return mount(handle);
  /* permission lapsed with the session — one click re-grants it */
  const again = document.getElementById("w-again");
  again.textContent = `Reopen “${handle.name}”`;
  again.hidden = false;
  again.onclick = async () => {
    if (await handle.requestPermission({ mode: "read" }) === "granted") mount(handle);
  };
})();

document.fonts.ready.then(() => render(true));
