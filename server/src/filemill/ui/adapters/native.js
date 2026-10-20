import { classifyFile } from "../core/file-kind.js";
import { PreviewRich } from "./preview-rich.js";

export const nativeCall = (op, args = {}) =>
  window.webkit.messageHandlers.filemill.postMessage({ op, ...args });
const nativeOrder = new Intl.Collator(undefined, { numeric: true });
const nativeNode = (name, rel = "", dir = true) => ({
  name,
  rel,
  dir,
  kids: dir ? null : undefined,
  fileKind: classifyFile(name, { dir }),
});
export const NativeFS = {
  node: nativeNode,
  async ensureLoaded(node) {
    if (!node.dir || node.kids !== null) return;
    if (node.loading) return node.loading;
    node.loading = (async () => {
      try {
        const entries = await nativeCall("list", { path: node.rel });
        node.kids = entries.map((e) => nativeNode(e.name, e.path, e.dir));
        node.kids.sort((a, b) =>
          +b.dir - +a.dir || nativeOrder.compare(a.name, b.name)
        );
        node.ordered = true;
      } catch (error) {
        node.denied = /\bEACCES\b/.test(String(error))
          ? "No permission to read"
          : String(error);
        node.kids = [];
      } finally {
        node.loading = null;
      }
    })();
    return node.loading;
  },
  async loadMeta(node) {
    if (node.dir || node.meta) return;
    try {
      node.meta = await nativeCall("stat", { path: node.rel });
    } catch (error) {
      node.meta = { error: String(error) };
    }
  },
  async blob(node) {
    const result = await nativeCall("read", { path: node.rel });
    const blob = new Blob([
      Uint8Array.from(atob(result.bytes), (c) => c.charCodeAt(0)),
    ]);
    blob.revision = node.revision = result.revision;
    return blob;
  },
  async write(node, text, expected = node.revision) {
    node.revision = await nativeCall("write", {
      path: node.rel,
      text,
      revision: expected,
    });
    node.meta = null;
  },
};
export const NativePreview = {
  render: (node) => PreviewRich.render(node),
  revoke: () => PreviewRich.revoke(),
};
let nativeLocation = null, nativeQueue = Promise.resolve(), nativeNavigate;
let nativeRevision = 0, nativeFullscreenForward = false;
export const NativeRouter = {
  read: () => nativeLocation,
  write(state, replace) {
    const snapshot = { ...nativeLocation, ...state };
    if (JSON.stringify(snapshot) === JSON.stringify(nativeLocation)) return;
    nativeLocation = snapshot;
    nativeRevision++;
    nativeFullscreenForward = false;
    nativeQueue = nativeQueue.then(() =>
      nativeCall("route", { state: snapshot, replace })
    )
      .catch(console.error);
  },
  onNavigate(callback) {
    nativeNavigate = callback;
  },
};
export async function nativeMove(delta) {
  const fullscreen = document.documentElement.classList.contains(
    "pv-fullscreen",
  );
  if ((delta < 0 && fullscreen) || (delta > 0 && nativeFullscreenForward)) {
    nativeFullscreenForward = delta < 0;
    document.getElementById("pv-fullscreen")?.click();
    return;
  }
  const revision = nativeRevision;
  nativeQueue = nativeQueue.then(async () => {
    const state = await nativeCall("navigate", { delta });
    if (state && revision === nativeRevision) {
      nativeLocation = state;
      nativeNavigate?.(state);
    }
  });
  return nativeQueue;
}
export async function nativeRoot() {
  const state = await nativeCall("root");
  nativeLocation = { root: state.name, path: [], view: "render" };
  return NativeFS.node(state.name);
}
