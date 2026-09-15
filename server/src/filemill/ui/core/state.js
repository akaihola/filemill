/* ═══════════════════════════════════════════════════════════════════════════
   State
   ═══════════════════════════════════════════════════════════════════════════ */
import "./shell.js";

export const root = document.documentElement;
export const finder = document.getElementById("finder");
export const rail = document.getElementById("rail");
export const stage = document.getElementById("stage");
export const strip = document.getElementById("strip");
export const trail = document.getElementById("trail");

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
  dotfiles: root.dataset.hidden === "show",
  sort: { key: "name", desc: false },
};
let sortOrder = (kids) => kids;
export const setSortKids = (value) => sortOrder = value;

export const GUTTER = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--gutter"));
export const SPINE = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--spine-w"));

const COL_MIN = 148; // Keep columns wide enough for readable rows and controls.
const COL_MAX = 380; // Fit long page titles while folding columns outside focus.
const BYTE_BASE = 1024; // File sizes use binary units.
const KB_DECIMAL_LIMIT = 10; // Small KB values keep one decimal place.
const KB_DECIMAL_DIGITS = 1; // One decimal keeps small sizes readable.
const KB_DIGITS = 0; // Larger KB values do not need fractional precision.
const MB_DECIMAL_DIGITS = 1; // MB values retain one decimal for useful precision.
const GB_DECIMAL_DIGITS = 2; // GB values retain two decimals for useful precision.
const DATE_PART_DIGITS = "2-digit"; // Clock fields align consistently in the metadata line.
const CODE_COLUMNS = 88; // Preview text targets an 88-character reading width.
const CODE_HORIZONTAL_PADDING = 82; // Preview padding is 30px plus 52px.
const PREVIEW_MAX_WIDTH = 760; // Keep the preview from becoming too wide to read.
const PREVIEW_MIN_RATIO = 0.45; // Preserve nearly half the stage for preview content.
const EMPTY_PREVIEW_WIDTH = 300; // Keep the empty preview stable before a file is selected.
const HEADER_HORIZONTAL_PADDING = 34; // Reserve space for the column heading chrome.
const COLUMN_HORIZONTAL_PADDING = 58; // Reserve space for row padding and scrollbar.
const CODE_FONT_SIZE = 11.5; // Match the compact monospace preview typography.

/* One filtered copy per call, ordered by core/sort.js. Every column build, every
   width measurement and every path walk comes through here, which is what keeps
   the rows and a restored chain agreeing on what row 4 is. */
export const visibleKids = (node) =>
  ((kids) => node.ordered ? kids : sortOrder(kids))(
    (node.kids || []).filter((k) => state.dotfiles || !k.name.startsWith(".")),
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
  const last = path[path.length - 1], s = sel[path.length - 1];
  const n = s && (last.kids || []).find((k) => k.name === s);
  return (n && !n.dir) ? n : null;
};

export const selectedNode = () => {
  const last = path[path.length - 1], s = sel[path.length - 1];
  return s && (last.kids || []).find((k) => k.name === s) || null;
};

/* 88 columns of .pv-text plus its and .pv-body's horizontal padding (30 + 52),
   measured from the real monospace font so it agrees with the CSS min-width */
const codeMin = () =>
  codeMin._w ||= (() => {
    const c = document.createElement("canvas").getContext("2d");
    const cs = getComputedStyle(root);
    c.font = `${CODE_FONT_SIZE}px ${cs.getPropertyValue("--mono")}`;
    return Math.ceil(c.measureText("0").width * CODE_COLUMNS) +
      CODE_HORIZONTAL_PADDING;
  })();

/* target reading width for the preview — the thing scrolling tries to protect.
   Never wider than the stage itself: a phone cannot show 88 columns, and a
   pane that runs past the right edge is clipped, not scrollable — so there
   the pane fits and .pv-body pans over the code instead. */
export const previewTarget = () =>
  previewNode()
    ? Math.min(
      PREVIEW_MAX_WIDTH,
      stage.clientWidth,
      Math.max(codeMin(), Math.round(stage.clientWidth * PREVIEW_MIN_RATIO)),
    )
    : EMPTY_PREVIEW_WIDTH;

export function measure(node) {
  /* content-driven width, clamped — no manual resizing, no wasted space */
  const c = (measure._c ||= document.createElement("canvas").getContext("2d"));
  const cs = getComputedStyle(root);
  c.font = `${cs.getPropertyValue("--fs-row").trim()} ${
    cs.getPropertyValue("--font")
  }`;
  let w = 0;
  for (const k of visibleKids(node)) {
    w = Math.max(w, c.measureText(k.name).width);
  }
  c.font = `600 ${cs.getPropertyValue("--fs-head").trim()} ${
    cs.getPropertyValue("--font")
  }`;
  w = Math.max(w, c.measureText(node.name).width + HEADER_HORIZONTAL_PADDING);
  return Math.min(
    COL_MAX,
    Math.max(COL_MIN, Math.ceil(w) + COLUMN_HORIZONTAL_PADDING),
  );
}
