/* Nodes are plain {name, dir, kids} objects. null kids means unread.
   Adapters retain source-specific fields; this module owns the column state. */
const BYTE_BASE = 1024; // File sizes use binary units.
const KB_DECIMAL_LIMIT = 10; // Small KB values keep one decimal place.
const KB_DECIMAL_DIGITS = 1; // One decimal keeps small sizes readable.
const KB_DIGITS = 0; // Larger KB values do not need fractional precision.
const MB_DECIMAL_DIGITS = 1; // MB values retain one decimal for useful precision.
const GB_DECIMAL_DIGITS = 2; // GB values retain two decimals for useful precision.
const DATE_PART_DIGITS = "2-digit"; // Clock fields align consistently in the metadata line.

export let path = []; // node chain, [0] = root
export let sel = []; // per-column selected name
export let focusCol = 0;
export let widths = []; // natural width per column
export let folded = 0; // columns currently folded
export let pvToken = 0; // guards async preview fills
export let pvFullscreen = false;
/* Module bindings are read-only for importers, so the files that used to
   assign these directly go through here. */
export function setState(patch) {
  if ("path" in patch) path = patch.path;
  if ("sel" in patch) sel = patch.sel;
  if ("focusCol" in patch) focusCol = patch.focusCol;
  if ("widths" in patch) widths = patch.widths;
  if ("folded" in patch) folded = patch.folded;
  if ("pvFullscreen" in patch) pvFullscreen = patch.pvFullscreen;
}
export const nextPvToken = () => ++pvToken;
export const state = {
  dotfiles: false,
  sort: { key: "name", desc: false },
};
let sortOrder = (kids) => kids;
export const setSortKids = (value) => sortOrder = value;

/* One filtered copy per call, ordered by model/sort.js. Every column build, every
   width measurement and every path walk comes through here, which is what keeps
   the rows and a restored chain agreeing on what row 4 is. */
export const visibleKids = (node) =>
  ((kids) =>
    node.ordered && state.sort.key === "name" ? kids : sortOrder(kids))(
      (node.kids || []).filter((k) =>
        state.dotfiles || !k.name.startsWith(".")
      ),
    );

export const rowIndex = (node, name) =>
  visibleKids(node).findIndex((k) => k.name === name);

export const fmtSize = (b) =>
  b < BYTE_BASE ? `${b} B` : b < BYTE_BASE ** 2
    ? `${
      (b / BYTE_BASE).toFixed(
        b < BYTE_BASE * KB_DECIMAL_LIMIT ? KB_DECIMAL_DIGITS : KB_DIGITS,
      )
    } KB`
    : b < BYTE_BASE ** 3
    ? `${(b / BYTE_BASE ** 2).toFixed(MB_DECIMAL_DIGITS)} MB`
    : `${(b / BYTE_BASE ** 3).toFixed(GB_DECIMAL_DIGITS)} GB`;

export const fmtDate = (ms) =>
  new Date(ms).toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: DATE_PART_DIGITS,
    minute: DATE_PART_DIGITS,
  });

export const splitName = (name) => {
  const i = name.lastIndexOf(".");
  return (i > 0) ? [name.slice(0, i), name.slice(i)] : [name, ""];
};

export const previewNode = () => {
  const selected = selectedNode();
  if (selected && !selected.dir) return selected;
  const current = path[path.length - 1];
  return current?.json && current.value !== undefined ? current : null;
};

export const selectedNode = () => {
  const last = path[path.length - 1], s = sel[path.length - 1];
  return s !== undefined && (last.kids || []).find((k) => k.name === s) || null;
};
