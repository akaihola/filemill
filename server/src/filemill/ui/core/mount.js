import { setContentSearch } from "./search.js";
import { FS } from "./ports.js";
import { resetDial } from "./layout.js";
import { colCache, render } from "./render.js";
import { setState } from "./model/state.js";

export async function mountRoot(node, title = node.name) {
  setContentSearch(
    FS.search
      ? (q, focused, signal) => FS.search(node, q, focused, signal)
      : null,
  );
  colCache.clear();
  setState({ path: [node], sel: [], focusCol: 0 });
  resetDial();
  document.title = title;
  render();
  await FS.ensureLoaded(node);
}
