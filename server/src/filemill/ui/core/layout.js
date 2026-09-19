import {
  automaticFold,
  columnMetrics,
  columnSpan,
  focusPan,
  foldingAt,
  foldPosition,
  foldStep,
  scrollRange,
  tailShift,
} from "./model/folding.js";
/* ═══════════════════════════════════════════════════════════════════════════
   Layout + the scroll dial

   scrollLeft is not a translation — it is a 0–100% condensing dial:
     0%       every column unfolded; preview overflows off the right edge
     k·unit   the leftmost k columns folded to spines   (unit = 99% / ncols)
     99%      every column folded; preview fills what is left
     99–100%  the spine strip itself slides away; at 100% the preview is alone
   ═══════════════════════════════════════════════════════════════════════════ */
import { set, setVar } from "./dom.js";
import { focusCol, folded, path, setState, widths } from "./model/state.js";
import {
  finder,
  GUTTER,
  previewTarget,
  rail,
  root,
  SPINE,
  stage,
  strip,
} from "./dom-renderer.js";
import { paintTrail } from "./trail.js";

export const stripSpan = (k) => columnSpan(widths, k, GUTTER(), SPINE());
export const foldUnit = () => foldStep(path.length);
export const range = () => scrollRange(widths, GUTTER(), SPINE());

let scrollStep = 0;
let scrollColumns = 0;

export function layout(keepScroll) {
  // Preserve the fold position, not pixels whose meaning changes with the path.
  const position = scrollStep ? foldPosition(finder.scrollLeft, scrollStep) : 0;
  const stageW = finder.clientWidth;
  setVar(root, "--stage-w", stageW + "px");
  setVar(root, "--preview-w", previewTarget() + "px");
  rail.style.width = (stageW + range()) + "px";

  const nextStep = foldUnit() * range();
  const geometryChanged = nextStep !== scrollStep ||
    path.length !== scrollColumns;
  if (keepScroll && scrollStep && geometryChanged) {
    const nextPosition = position > scrollColumns
      ? path.length * position / scrollColumns
      : position;
    finder.scrollTo({
      left: Math.round(nextPosition * nextStep),
      behavior: "instant",
    });
  }
  scrollStep = nextStep;
  scrollColumns = path.length;

  // A new column or density can consume the preview reserve even during ↑/↓.
  // Keep deliberate partial folds and the fully folded preview position intact.
  if (
    !keepScroll ||
    (geometryChanged && Number.isInteger(position) && position <= focusCol)
  ) {
    const k = automaticFold(
      widths,
      GUTTER(),
      SPINE(),
      previewTarget(),
      stageW,
      focusCol,
      keepScroll ? position : folded,
      root.dataset.layout === "compressed-columns",
    );
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
  const max = Math.max(1, rail.clientWidth - finder.clientWidth);
  const p = Math.min(1, finder.scrollLeft / max);
  const n = path.length;

  const { raw, t } = foldFromScroll(max);
  const { focusLeft, focusRight } = applyWidths(t);
  const pan = panFocus(raw, focusLeft, focusRight);
  slideTail(p, pan, n);

  document.getElementById("st-fold").textContent = folded
    ? `${folded}/${n} folded`
    : "";
  paintTrail();
}

function foldFromScroll(max) {
  const result = foldingAt(finder.scrollLeft, max, path.length);
  setState({ folded: result.folded });
  return result;
}

function applyWidths(t) {
  const g = GUTTER(), sp = SPINE(), n = path.length;
  const metrics = columnMetrics(widths, folded, t, focusCol, g, sp);
  [...strip.querySelectorAll(".col")].forEach((col, i) => {
    col.classList.toggle("spine", i < folded);
    col.classList.toggle("folding", i === folded && folded < n);
    const w = metrics.sizes[i];
    if (i < folded) {
      set(col.style, "width", "");
      return;
    }
    set(col.dataset, "fold", String(i === folded ? t : 0));
    setVar(col, "--fold", col.dataset.fold); /* custom props need setProperty */
    set(col.style, "width", w + "px");
  });
  return metrics;
}

function panFocus(raw, focusLeft, focusRight) {
  return focusPan(
    raw,
    focusCol,
    focusLeft,
    focusRight,
    finder.clientWidth,
    GUTTER(),
  );
}

function slideTail(p, pan, n) {
  const shift = tailShift(p, pan, n, SPINE(), GUTTER());
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
  const body = row.closest(".col-body");
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
