/* ═══════════════════════════════════════════════════════════════════════════
   DOM handles and measurements for the browser renderer
   ═══════════════════════════════════════════════════════════════════════════ */
import "./shell.js";
import { previewNode, state, visibleKids } from "./model/state.js";
state.dotfiles = document.documentElement.dataset.hidden === "show";

export const root = document.documentElement;
export const finder = document.getElementById("finder");
export const rail = document.getElementById("rail");
export const stage = document.getElementById("stage");
export const strip = document.getElementById("strip");
export const trail = document.getElementById("trail");

export const GUTTER = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--gutter"));
export const SPINE = () =>
  parseInt(getComputedStyle(root).getPropertyValue("--spine-w"));

const COL_MIN = 148; // Keep columns wide enough for readable rows and controls.
const COL_MAX = 380; // Fit long page titles while folding columns outside focus.
const CODE_COLUMNS = 88; // Preview text targets an 88-character reading width.
const CODE_HORIZONTAL_PADDING = 82; // Preview padding is 30px plus 52px.
const PREVIEW_MAX_WIDTH = 760; // Keep the preview from becoming too wide to read.
const PREVIEW_MIN_RATIO = 0.45; // Preserve nearly half the stage for preview content.
const EMPTY_PREVIEW_WIDTH = 300; // Keep the empty preview stable before a file is selected.
const HEADER_HORIZONTAL_PADDING = 34; // Reserve space for the column heading chrome.
const COLUMN_HORIZONTAL_PADDING = 58; // Reserve space for row padding and scrollbar.
const CODE_FONT_SIZE = 11.5; // Match the compact monospace preview typography.

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
