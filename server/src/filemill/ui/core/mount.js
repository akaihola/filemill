import { FS } from "./ports.js";
import { dialTo } from "./layout.js";
import { colCache, render } from "./render.js";
import { setState } from "./model/state.js";

export async function mountRoot(node, title = node.name) {
  colCache.clear();
  setState({ path: [node], sel: [], focusCol: 0 });
  dialTo(0, false);
  document.title = title;
  render();
  await FS.ensureLoaded(node);
}
