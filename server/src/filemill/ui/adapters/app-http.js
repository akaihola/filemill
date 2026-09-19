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
import { initSort, setSortActions } from "../core/sort.js";
import { sortKids } from "../core/model/sort.js";
import { FSA } from "./fsa.js";
import { API, HTTP } from "./http.js";
import { PreviewLocal } from "./preview-local.js";
import { PreviewRich, RICH_RENDERERS } from "./preview-rich.js";
import { RouterPath } from "./router-path.js";
import { rememberRoot } from "./storage.js";
import { withCsv, withCsvPreview } from "./vfs-csv.js";
import {
  applyPath,
  setDeepLinkActions,
  startRouting,
} from "../core/deeplink.js";
import { withVirtual, withVirtualPreview } from "./vfs-json.js";
import { FS, useFilesystem, usePreview, useRouter } from "../core/ports.js";
import { colCache, render, setActions } from "../core/render.js";
import { addRenderers, CORE_RENDERERS } from "../core/renderers.js";
import { mountRoot } from "../core/mount.js";
import {
  choose,
  refreshColumn,
  renderCrumbs,
  saySt,
  unfoldTo,
} from "../core/nav.js";
import {
  focusCol,
  path,
  sel,
  setSortKids,
  setState,
} from "../core/model/state.js";
import { hlLang } from "../core/syntax.js";
import { classifyFile } from "../core/file-kind.js";

document.getElementById("bar").insertAdjacentHTML(
  "beforeend",
  `<span id="local-badge" hidden><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M1.4 3.2h4.1l1.3 1.7h7.8c.6 0 1 .4 1 1v7c0 .6-.4 1-1 1H1.4c-.6 0-1-.4-1-1V4.2c0-.6.4-1-1-1z"/></svg><span class="nm"></span><button id="leave-local" title="Back to the served folder">✕</button></span><button class="tb" id="open" title="Open a folder on this machine">Open Folder…</button>`,
);
document.body.insertAdjacentHTML(
  "beforeend",
  `<div id="welcome"><h1 id="w-title">Filemill server unavailable</h1><p id="w-msg"></p><button class="btn" id="w-pick">Retry connection</button><div id="w-recent" hidden></div></div>`,
);
const welcome = document.getElementById("welcome");

/* The load-time work sort.js, layout.js and settings.js did as classic scripts,
   in the order they used to load. */
initSort();
setSortKids(sortKids);
setActions({ choose, refreshColumn, renderCrumbs, saySt, unfoldTo });
setSortActions({ render });
setDeepLinkActions({ render, colCache });
initLayout(render);
initSettings();

/* The renderer table, core first. Markdown, .docx and .pptx are drawn in the
   browser here too — the first two from the modules the shell serves out of
   /ui/vendor/ (see ui/vendor/README.md), .pptx from its CDN viewer. Only
   reStructuredText stays with the Python renderer. `offline` is the fallback
   the rich entries name when a module does not arrive. */
addRenderers([
  ...CORE_RENDERERS,
  ...RICH_RENDERERS.filter((e) =>
    ["md", "markdown", "docx", "pptx", "offline"].includes(e.kind)
  ),
]);

const ROOT_NAME = document.documentElement.dataset.root || "/";

/* Local mode gives up the address bar: a URL path names a file under the
   *server's* root, and a folder the browser granted is not under it.
   Pretending otherwise would produce links that resolve to the wrong file —
   hence useRouter(null) below, and the badge that says which side you are on. */

/* Source files are coloured in the browser by core/syntax.js, not by Pygments
   on the way out — see that file for why. The server still renders what it is
   better at (reStructuredText), so this wraps the provider rather than
   replacing it: a file with a language we know is read through FS.blob and
   highlighted here, and anything else goes on as before. A virtual path is
   never diverted, because only the server can read one. */
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

const PreviewHTTP = {
  revoke() {},
  async render(n) {
    const response = await fetch(`${API}/preview?p=${encodeURIComponent(n.rel)}`);
    return response.ok ? response.text() : PreviewLocal.render(n);
  },
};

/* Markdown, .docx and .pptx render in the browser in this edition too, from
   the modules the shell lists in FILEMILL_CDN (Markdown and .docx are served
   from /ui/vendor/, see ui/vendor/README.md). This sits inside withHighlighting
   so that ?filemill=highlight still shows a Markdown file as coloured source. */
const RICH = ["md", "markdown", "rst", "docx", "pptx"];
const withRichPreview = (provider) => ({
  revoke() {
    provider.revoke?.();
    PreviewRich.revoke();
  },
  render: (n) =>
    (!n.vpath && classifyFile(n.name, n).preview === "video"
      ? PreviewLocal
      : !n.vpath && classifyFile(n.name, n).preview === "rst"
      ? PreviewHTTP
      : !n.vpath && RICH.includes(classifyFile(n.name, n).preview)
      ? PreviewRich
      : provider).render(n),
});

async function mountServer() {
  useFilesystem(withCsv(withVirtual(HTTP)));
  usePreview(
    withCsvPreview(
      withVirtualPreview(
        withHighlighting(withRichPreview(PreviewLocal)),
      ),
    ),
  );
  useRouter(RouterPath);

  /* Read the link *before* the first render. render() syncs the URL, and the
     state it syncs from is the bare root — so rendering first would rewrite
     /notes/deep/leaf.md down to / and then faithfully restore nothing. */
  const loc = RouterPath.read();

  const node = HTTP.node(ROOT_NAME, "");
  if (welcome) welcome.hidden = true;
  await mountRoot(node, ROOT_NAME);

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

/* The local-folder mode of the server build. Previews the browser cannot make
   itself uses the same browser renderers as the served tree, so
   switching sides costs no fidelity; only the URL goes quiet. */
export async function mount(handle) {
  useFilesystem(withCsv(withVirtual(FSA)));
  usePreview(
    withCsvPreview(
      withVirtualPreview(
        withHighlighting(withRichPreview(PreviewRich)),
      ),
    ),
  );
  useRouter(null);
  const node = FSA.node(handle.name, handle);
  if (welcome) welcome.hidden = true;
  await mountRoot(node, handle.name);
  /* Back to the bare base, not one segment up: the URL was naming a file
     under the server's root and nothing here is under it any more. */
  history.replaceState(null, "", RouterPath.base);
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
