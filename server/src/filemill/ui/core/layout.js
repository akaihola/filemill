/* ═══════════════════════════════════════════════════════════════════════════
   Layout + the scroll dial

   scrollLeft is not a translation — it is a 0–100% condensing dial:
     0%       every column unfolded; preview overflows off the right edge
     k·unit   the leftmost k columns folded to spines   (unit = 99% / ncols)
     99%      every column folded; preview fills what is left
     99–100%  the spine strip itself slides away; at 100% the preview is alone
   ═══════════════════════════════════════════════════════════════════════════ */
import { set, setVar } from "./dom.js";
import {
  finder,
  focusCol,
  folded,
  GUTTER,
  path,
  previewTarget,
  rail,
  root,
  setState,
  SPINE,
  stage,
  strip,
  widths,
} from "./state.js";
import { paintTrail } from "./trail.js";

export function stripSpan(k) {
  /* width of the column strip with k folded */
  const g = GUTTER(), n = path.length;
  const cols = widths.reduce((a, w, i) => a + (i < k ? SPINE() : w), 0);
  return cols + g * (n + 1); /* padding either side + inter-column gaps */
}
const FOLD_RANGE = 0.99; // Reserve the final one percent for sliding the spine strip.
const MIN_SCROLL_RANGE = 1; // Keep division and scroll arithmetic valid before layout settles.
const BOUNDARY_SLACK = 0.5; // Absorb rounding that can otherwise land one column short.
const FULL_FOLD_THRESHOLD = 0.99; // Treat the dial's first 99 percent as column folding.
const TAIL_RANGE = 0.01; // The final one percent slides the folded strip away.
export const foldUnit = () => FOLD_RANGE / path.length;
export const range = () => Math.max(MIN_SCROLL_RANGE, stripSpan(0) - GUTTER());
export const foldAll = () => {
  setState({ folded: path.length });
  applyWidths(path.length, 0);
  slideTail(1, 0, path.length);
};

export function layout(keepScroll, preserveFolded = false) {
  const stageW = finder.clientWidth;
  setVar(root, "--stage-w", stageW + "px");
  setVar(root, "--preview-w", previewTarget() + "px");
  rail.style.width = (stageW + range()) + "px";

  if (!keepScroll) {
    /* default: the least folding that still gives the preview its full width.
       ?layout=compressed-columns asks for every column folded instead, which is
       the dial at 99% and the one thing the HTMX shell could never do. */
    let k = 0;
    while (k < path.length && stripSpan(k) + previewTarget() > stageW) k++;
    /* Fold more when the new contents need it, but never past the focused
       column: that is the one under the user's finger, and the column to its
       right is what opening it just produced — answering a tap by hiding
       either is not condensing, it is discarding the answer. What is left of
       focus has been walked past and may condense; folding further than this
       is a user action: scroll, spine, ←. */
    k = Math.min(focusCol, Math.max(k, folded));
    if (root.dataset.layout === "compressed-columns") k = path.length;
    finder.scrollLeft = Math.round(k * foldUnit() * range());
  }
  applyScroll();
}

function applyScroll() {
  if (!path.length) return;
  /* The dial is the only thing that may move the strip, and #stage is where
     that gets decided: overflow hidden stops a finger, not a programmatic
     scroll. Now that the strip may be wider than the stage — a column right of
     focus peeks past the edge instead of folding — anything that scrolls an
     element into view drags every column out through the left edge, and the
     dial writes #finder, so nothing would put them back. revealRow keeps the
     app's own row reveals from doing it; this undoes whatever else did, at the
     next repaint. */
  if (stage.scrollLeft) stage.scrollLeft = 0;
  const max = Math.max(MIN_SCROLL_RANGE, rail.clientWidth - finder.clientWidth);
  const p = Math.min(1, finder.scrollLeft / max);
  const n = path.length;

  const { raw, t } = foldFromScroll(max);
  const { focusLeft, focusRight } = applyWidths(raw, t);
  const pan = panFocus(raw, focusLeft, focusRight);
  slideTail(p, pan, n);

  document.getElementById("st-fold").textContent = folded
    ? `${folded}/${n} folded`
    : "";
  paintTrail();
}

function foldFromScroll(max) {
  /* Half a pixel of slack, in pixels: layout() and unfoldTo() write
     round(k·unit·range), which can fall up to 0.5 px short of the boundary. A
     fixed 0.002 units was only 0.3 px once seven columns made a unit 160 px
     wide, and a landing read one column short paints the column ← just
     reached as a spine, with folded === focusCol so the next ← never scrolls. */
  const raw = Math.min(1, (finder.scrollLeft + BOUNDARY_SLACK) / max) /
    foldUnit();
  setState({ folded: Math.min(path.length, Math.floor(raw)) });
  /* how far into folding the next column is — 0 = full width, 1 = a spine */
  const t = Math.min(1, Math.max(0, raw - folded));
  return { raw, t };
}

function applyWidths(raw, t) {
  const g = GUTTER(), sp = SPINE(), n = path.length;
  let x = g, focusLeft = 0, focusRight = 0;
  [...strip.querySelectorAll(".col")].forEach((col, i) => {
    col.classList.toggle("spine", i < folded);
    col.classList.toggle("folding", i === folded && folded < n);
    const w = i < folded
      ? sp
      : i === folded
      ? Math.round(widths[i] + (sp - widths[i]) * t)
      : widths[i];
    if (i === focusCol) [focusLeft, focusRight] = [x, x + w];
    x += w + g;
    if (i < folded) {
      set(col.style, "width", "");
      return;
    }
    set(col.dataset, "fold", String(i === folded ? t : 0));
    setVar(col, "--fold", col.dataset.fold); /* custom props need setProperty */
    set(col.style, "width", w + "px");
  });
  return { focusLeft, focusRight };
}

function panFocus(raw, focusLeft, focusRight) {
  const g = GUTTER();
  const reach = Math.min(1, Math.max(0, raw - focusCol + 1));
  const pan = reach *
    Math.min(
      Math.max(0, focusRight - finder.clientWidth),
      Math.max(0, focusLeft - g),
    );
  return pan;
}

function slideTail(p, pan, n) {
  const sp = SPINE(), g = GUTTER();
  const tail = p > FULL_FOLD_THRESHOLD
    ? (p - FULL_FOLD_THRESHOLD) / TAIL_RANGE
    : 0;
  const shift = tail * n * (sp + g) + pan;
  set(strip.style, "minWidth", (finder.clientWidth + shift) + "px");
  set(strip.style, "transform", `translateX(${-shift}px)`);
}

/* Keep a row visible without letting it move the strip.

   scrollIntoView() is the obvious call and the wrong one here: it scrolls
   whichever ancestor brings the row into view, and now that a column can reach
   past the viewport that ancestor is #stage. Measured at 390 px on a chain
   seven deep: one keystroke moved it 28 px, and a walk in left it at 141 with
   the first three columns dragged off the left edge — for good, because the
   dial writes #finder and nothing writes #stage back. A row only ever needs
   its own column to scroll, and that is vertical. The arithmetic below is
   `block: "nearest"`: nothing if the row is already inside, otherwise the
   shorter of the two edges — the same numbers scrollIntoView produced. */
export function revealRow(row) {
  const body = row.parentElement; /* .col-body scrolls */
  const r = row.getBoundingClientRect(), b = body.getBoundingClientRect();
  if (r.top < b.top) body.scrollTop += r.top - b.top;
  else if (r.bottom > b.bottom) body.scrollTop += r.bottom - b.bottom;
}

export function initLayout(render) {
  finder.addEventListener("scroll", applyScroll, { passive: true });
  /* Nothing may leave #stage scrolled — see applyScroll. A click that brings
     its button into view drags the strip out through the left edge, and if the
     dial is at rest no scroll or render follows to put it back. Undo it here,
     when it happens, rather than at whatever event comes next. */
  stage.addEventListener("scroll", () => {
    if (stage.scrollLeft) stage.scrollLeft = 0;
  }, { passive: true });
  addEventListener("resize", () => render());
}
