import { initCore } from "../core/boot.js";
import { withCsv, withCsvPreview } from "./vfs-csv.js";
import { withDocumentPreview, withDocuments } from "./vfs-doc.js";
import { withVirtual, withVirtualPreview } from "./vfs-json.js";
import { startRouting } from "../core/deeplink.js";
import { useFilesystem, usePreview, useRouter } from "../core/ports.js";
import { render } from "../core/render.js";
import { addRenderers, CORE_RENDERERS } from "../core/renderers.js";
import { initRichSettings, RICH_RENDERERS } from "./preview-rich.js";
import { mountRoot } from "../core/mount.js";
import {
  nativeCall,
  NativeFS,
  nativeMove,
  NativePreview,
  nativeRoot,
  NativeRouter,
} from "./native.js";

initCore();
addRenderers([...CORE_RENDERERS, ...RICH_RENDERERS]);
initRichSettings();
useFilesystem(withDocuments(withCsv(withVirtual(NativeFS))));
usePreview(
  withDocumentPreview(withCsvPreview(withVirtualPreview(NativePreview))),
);
useRouter(NativeRouter);
for (const [label, delta] of [["Back", -1], ["Forward", 1]]) {
  const button = document.createElement("button");
  button.className = "tb";
  button.textContent = label;
  button.onclick = () => nativeMove(delta);
  document.getElementById("bar").append(button);
}
addEventListener("keydown", (event) => {
  if (event.altKey && ["ArrowLeft", "ArrowRight"].includes(event.key)) {
    event.preventDefault();
    event.stopImmediatePropagation();
    nativeMove(event.key === "ArrowLeft" ? -1 : 1);
  }
}, true);
export async function mountNative() {
  await mountRoot(await nativeRoot());
  startRouting();
  render();
}
mountNative();
document.fonts.ready.then(() => render(true));

const nativeOpen = document.createElement("button");
nativeOpen.className = "tb";
nativeOpen.id = "open";
nativeOpen.textContent = "Open Folder…";
nativeOpen.onclick = async () => {
  if (await nativeCall("pick")) await mountNative();
};
document.getElementById("bar").append(nativeOpen);
