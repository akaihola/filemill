import {
  path,
  previewable,
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

/* ADR 0050: history pushes on entering a column and rewrites otherwise. The
   key is the open directory chain, so a click that opens another folder is a
   new entry and choosing a file inside the open folder rewrites it. Stepping
   with ↑/↓, Home/End or paging always rewrites, however many folders the walk
   opens on the way: one entry per row would make Back useless. */
export function locationState(viewMode, previousKey) {
  const key = path.map((p) => p.name).join("/");
  const node = previewNode();
  /* A whole JSON file still needs the shell when opened as a column.
     Its bare URL serves bytes; virtual containers already address a member. */
  const view = previewable(node) || (node?.json && !node.meta?.virtual)
    ? (viewMode === "highlight" ? "highlight" : "render")
    : undefined;
  return {
    key,
    replace: previousKey === key || state.stepping,
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
      if (!node.dir) {
        complete = i === names.length - 1;
        break;
      }
      await ensureLoaded(node);
      if (!node.dir) break; /* a virtual wrapper declined it while reading */
      path.push(node);
    }
    if (!complete) {
      const documentIndex = path.findIndex((node) => node.doc);
      if (documentIndex >= 0) {
        /* A broken section link opens the file, rather than a parent section. */
        path.splice(documentIndex + 1);
        sel.splice(documentIndex);
        setState({ focusCol: Math.max(0, documentIndex - 1) });
      }
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
