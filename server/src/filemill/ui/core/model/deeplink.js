import {
  path,
  previewNode,
  sel,
  setState,
  state,
  visibleKids,
} from "./state.js";
export function currentPath() {
  const names = path.slice(1).map((p) => p.name);
  const leaf = sel[path.length - 1];
  if (leaf !== undefined) names.push(leaf);
  return names;
}

// History is grouped by the open directory chain, as in the browser editions.
export function locationState(viewMode, previousKey) {
  const key = path.map((p) => p.name).join("/");
  const node = previewNode();
  const view = node && !node.dir
    ? (viewMode === "highlight" ? "highlight" : "render")
    : undefined;
  return {
    key,
    replace: previousKey === key,
    location: { root: path[0].name, path: currentPath(), view },
  };
}
export async function walkPath(names, ensureLoaded, wantFocus) {
  if (!path.length) return false;
  names = (names || []).filter(Boolean);

  /* a link to a dotfile has to reveal dotfiles, or visibleKids would hide the
     very thing the URL asked for */
  if (!state.dotfiles && names.some((n) => n.startsWith("."))) {
    state.dotfiles = true;
  }

  try {
    const rootNode = path[0];
    setState({ path: [rootNode], sel: [], focusCol: 0 });
    await ensureLoaded(rootNode);
    let complete = true;

    for (let i = 0; i < names.length; i++) {
      const parent = path[i];
      const kids = visibleKids(parent);
      const ri = kids.findIndex((k) => k.name === names[i]);
      if (ri < 0) {
        complete = false;
        break;
      }

      const node = kids[ri];
      sel[i] = node.name;
      setState({ focusCol: i }); /* focus stays on the column holding it */
      if (!node.dir) break;
      await ensureLoaded(node);
      path.push(node);
    }
    return complete;
  } finally {
    /* clamped: the chain may have come back shorter than the column that had
       focus, and focusing a column that is no longer open kills ↑/↓ */
    if (wantFocus != null) {
      setState({ focusCol: Math.max(0, Math.min(wantFocus, path.length - 1)) });
    }
  }
}
