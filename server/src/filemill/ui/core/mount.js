import { FS } from "./ports.js";
import { colCache, render } from "./render.js";
import { setState } from "./state.js";

export async function mountRoot(node, title = node.name) {
  colCache.clear();
  setState({ path: [node], sel: [], focusCol: 0 });
  document.title = title;
  render();
  await FS.ensureLoaded(node);
}
