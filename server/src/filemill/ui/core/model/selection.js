import { path, sel, setState, visibleKids } from "./state.js";
export function autoPreview(node) {
  const i = path.length - 1;
  if (path[i] !== node || sel[i] !== undefined) return;
  const files = visibleKids(node).filter((k) => !k.dir);
  const pick = files.find((k) => k.name === "README") ||
    files.find((k) => k.name.startsWith("README.")) ||
    files.find((k) => k.name === "index.html");
  if (pick) sel[i] = pick.name;
}

export function selectNode(colIdx, node) {
  setState({
    path: path.slice(0, colIdx + 1),
    sel: sel.slice(0, colIdx),
    focusCol: colIdx,
  });
  sel[colIdx] = node.name;
}
