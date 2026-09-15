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
import { initSettings } from "../core/settings.js";
import { initLayout } from "../core/layout.js";
import { initSort, setSortActions, sortKids } from "../core/sort.js";
import { FSA } from "./fsa.js";
import { API, HTTP } from "./http.js";
import { PreviewHTTP } from "./preview-http.js";
import { PreviewLocal } from "./preview-local.js";
import { withPptxPreview } from "./preview-rich.js";
import { PreviewUpload } from "./preview-upload.js";
import { RouterPath } from "./router-path.js";
import { rememberRoot } from "./storage.js";
import { withCsv, withCsvPreview } from "./vfs-csv.js";
import { applyPath, setDeepLinkActions, startRouting } from "../core/deeplink.js";
import {
  withJson,
  withJsonl,
  withJsonlPreview,
  withJsonPreview,
} from "../core/jsonl.js";
import { FS, useFilesystem, usePreview, useRouter } from "../core/ports.js";
import { colCache, render, setActions } from "../core/render.js";
import { choose, refreshColumn, renderCrumbs, saySt, unfoldTo } from "../core/nav.js";
import { focusCol, path, sel, setState, setSortKids, welcome } from "../core/state.js";
import { hlLang } from "../core/syntax.js";

/* The load-time work sort.js, layout.js and settings.js did as classic scripts,
   in the order they used to load. */
initSort();
setSortKids(sortKids);
setActions({ choose, refreshColumn, renderCrumbs, saySt, unfoldTo });
setSortActions({ render });
setDeepLinkActions({ render, colCache });
initLayout(render);
initSettings();

const ROOT_NAME = document.documentElement.dataset.root || "/";

/* Local mode gives up the address bar: a URL path names a file under the
   *server's* root, and a folder the browser granted is not under it.
   Pretending otherwise would produce links that resolve to the wrong file —
   hence useRouter(null) below, and the badge that says which side you are on. */

/* Source files are coloured in the browser by core/syntax.js, not by Pygments
   on the way out — see that file for why. The server still renders everything
   else it is better at (Markdown, .docx, database rows), so this wraps the
   provider rather than replacing it: a file with a language we know is read
   through FS.blob and highlighted here, and anything else goes on as before.
   A virtual path is never diverted, because only the server can read one. */
const withHighlighting = (provider) => ({
  revoke() {
    provider.revoke?.();
    PreviewLocal.revoke();
  },
  render: (n) =>
    (!n.vpath && document.documentElement.dataset.filemill === "highlight" &&
        hlLang(n.name)
      ? PreviewLocal
      : provider).render(n),
});

async function mountServer() {
  useFilesystem(withCsv(withJson(withJsonl(HTTP))));
  usePreview(
    withCsvPreview(
      withJsonPreview(
        withJsonlPreview(withPptxPreview(withHighlighting(PreviewHTTP))),
      ),
    ),
  );
  useRouter(RouterPath);

  /* Read the link *before* the first render. render() syncs the URL, and the
     state it syncs from is the bare root — so rendering first would rewrite
     /notes/deep/leaf.md down to / and then faithfully restore nothing. */
  const loc = RouterPath.read();

  const node = HTTP.node(ROOT_NAME, "");
  colCache.clear();
  setState({ path: [node], sel: [], focusCol: 0 });
  if (welcome) welcome.hidden = true;
  document.title = ROOT_NAME;
  render();
  await FS.ensureLoaded(node);

  if (node.denied) {
    showServerUnavailable();
    return;
  }

  if (loc && loc.path.length) await applyPath(loc.path);
  else render();
  startRouting();
}

function showServerUnavailable() {
  welcome.hidden = false;
  document.getElementById("w-title").textContent =
    "Filemill server unavailable";
  document.getElementById("w-msg").innerHTML =
    "Start Filemill locally with <code>uv run filemill</code>, then retry. " +
    "The installed app can connect to the service but cannot start it.";
  const button = document.getElementById("w-pick");
  button.hidden = false;
  button.textContent = "Retry connection";
  button.onclick = () => {
    button.disabled = true;
    mountServer().finally(() => {
      button.disabled = false;
    });
  };
  document.getElementById("w-recent").hidden = true;
}

/* The local-folder mode of the server build. Previews still come from the
   Python renderers — see PreviewUpload — so switching sides costs no fidelity;
   only the URL goes quiet. */
export async function mount(handle) {
  useFilesystem(withCsv(withJson(withJsonl(FSA))));
  usePreview(
    withCsvPreview(
      withJsonPreview(
        withJsonlPreview(withPptxPreview(withHighlighting(PreviewUpload))),
      ),
    ),
  );
  useRouter(null);
  const node = FSA.node(handle.name, handle);
  colCache.clear();
  setState({ path: [node], sel: [], focusCol: 0 });
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
    alert(
      "This browser has no File System Access API. " +
        "Local folders need Chrome, Edge or another Chromium-based desktop browser.",
    );
    return;
  }
  try {
    const handle = await window.showDirectoryPicker({
      mode: "read",
      id: "filemill",
    });
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
