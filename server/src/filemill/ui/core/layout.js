import {
  automaticFold,
  columnMetrics,
  columnSpan,
  dialStops,
  dialWindow,
  fitCount,
  focusPan,
  foldingAt,
  foldPosition,
  foldStep,
  scrollRange,
  tailShift,
  wideCounts,
  widenedSizes,
} from "./model/folding.js";
/* ═══════════════════════════════════════════════════════════════════════════
   Layout + the scroll dial

   The dial is not a translation — it is a condensing control, read in pixels
   along one axis that `range()` spans from natural to the preview alone:
     x < 0    the leftmost columns widen to fill the finder, fewer per stop
     0        every column at natural width; preview overflows off the right
     k·unit   the leftmost k columns folded to spines   (unit = 99% / ncols)
     99%      every column folded; preview fills what is left
     99–100%  the spine strip itself slides away; at 100% the preview is alone

   The scrollbar is deliberately shorter than the axis ([81], ADR 0075): it
   spans the two stops either side of the dial, so a fling — a swipe that
   runs to the end of the scrollbar — lands on the next stop. Once a scroll
   has settled the range is re-based around the new stop, invisibly: `base`
   moves and scrollLeft moves with it. `dial()` is the axis position and the
   only thing the fold arithmetic reads; scrollLeft is scrollbar-relative.
   ═══════════════════════════════════════════════════════════════════════════ */
import { set, setVar } from "./dom.js";
import {
  focusCol,
  folded,
  path,
  pvFullscreen,
  setState,
  widths,
} from "./model/state.js";
import {
  finder,
  folderWidth,
  GUTTER,
  previewTarget,
  rail,
  root,
  SPINE,
  stage,
  strip,
} from "./dom-renderer.js";
import { paintTrail } from "./trail.js";

const SETTLE_MS = 180; // longer than the gaps between a fling's wheel events
const AXIS_SLOP = 6; // px a wheel gesture travels before it takes an axis

export const stripSpan = (k) => columnSpan(widths, k, GUTTER(), SPINE());
export const foldUnit = () => foldStep(path.length);
export const range = () => scrollRange(widths, GUTTER(), SPINE());
const unit = () => foldUnit() * range();

let base = 0; // the dial position at scrollLeft 0
let stops = [0]; // where a fling lands, ascending
let counts = []; // columns filling the finder at each stop left of natural

export const dial = () => base + finder.scrollLeft;

/* The columns that fill the finder at a widened dial position: between two
   stops, the wider of the two. */
function wideCount(x) {
  const j = Math.ceil(-foldPosition(x, unit()) - 1e-9);
  return j > 0 ? counts[Math.min(j, counts.length) - 1] : 0;
}

function measureStops() {
  const g = GUTTER();
  const fit = fitCount(
    widths[0] ?? folderWidth(),
    finder.clientWidth,
    previewTarget(),
    g,
  );
  counts = wideCounts(path.length, fit);
  stops = dialStops(widths, counts, g, SPINE());
}

let rangeFrom = 0, rangeTo = 0; // what the scrollbar spans now
let written = false; // an instant scroll write happened this frame

/* A glide issued in the same task as an instant scroll write is cut by that
   write a frame later (seen in mobile emulation); note the write so the glide
   can wait for it. With no write pending a glide starts at once, which is what
   keeps a reduced-motion dial synchronous. */
function writeScroll(left) {
  finder.scrollTo({ left, behavior: "instant" });
  if (!written) requestAnimationFrame(() => written = false);
  written = true;
}

/* Give the scrollbar the range [from, to] and keep the dial at x, which must
   lie inside it. scrollLeft is whole pixels, so base absorbs the fraction.
   Returns whether scrollLeft was written: a write cuts a glide in flight. */
function setRange(from, to, x) {
  const next = x - Math.round(x - from);
  // Relative to the finder, so a resize never shrinks the range under the
  // dial — Chrome would clamp scrollLeft to the new end and base would lie.
  // Size from the adjusted base so the native endpoint rounds to the stop.
  const width = `calc(100% + ${Math.max(1, Math.round(to - next))}px)`;
  [rangeFrom, rangeTo] = [from, to];
  if (
    next === base && rail.style.width === width &&
    Math.round(x - base) === finder.scrollLeft
  ) return false;
  base = next;
  rail.style.width = width;
  writeScroll(Math.round(x - base));
  // A finder that cannot scroll yet (not laid out) clamps; the dial stays x.
  base = x - finder.scrollLeft;
  return true;
}

/* Narrow the range to the stops around the dial once a scroll has settled. */
function rebase() {
  const x = dial();
  const around = dialWindow(stops, x);
  setRange(around.lower, around.upper, x);
}

/* Move the dial to x. A target outside the scrollbar's range first widens the
   range to hold both ends of the move; settling narrows it again. */
export function dialTo(x, smooth) {
  const now = dial();
  if (x < rangeFrom - 0.5 || x > rangeTo + 0.5) {
    const around = dialWindow(stops, x);
    setRange(
      Math.min(rangeFrom, around.lower, now),
      Math.max(rangeTo, around.upper, now),
      now,
    );
  }
  if (!smooth) writeScroll(Math.round(x - base));
  else {
    // No behavior: the stylesheet decides (smooth unless reduced motion), so
    // the glide is a CSS motion, and instant where the user asked for that.
    const go = () => finder.scrollTo({ left: Math.round(x - base) });
    if (written) requestAnimationFrame(go);
    else go();
  }
  gliding = smooth ? { target: x, waits: 0 } : null;
  scheduleSettle();
}

const GLIDE_WAITS = 10; // a glide that has not arrived after 10 settles is dead
let settleTimer = 0;
let mouseDown = false, touching = false;
let gliding = null; // the smooth dialTo in flight; a scroll write would cut it
let wheeling = false; // the dial took this wheel gesture from the preview
let wheelAxis = null; // "x" or "y": the axis this wheel gesture started on
let travelX = 0, travelY = 0; // how far it went before it took that axis
function scheduleSettle() {
  clearTimeout(settleTimer);
  settleTimer = setTimeout(settle, SETTLE_MS);
}
function settle() {
  settleTimer = 0;
  wheeling = false; // the gesture is over; the next may go to the preview
  wheelAxis = null; // and may go along either axis
  travelX = travelY = 0;
  // A held finger or a scrollbar drag keeps its range until it lets go.
  if (mouseDown || touching) return;
  // A glide on a busy machine may not have started yet; wait for it.
  if (
    gliding && Math.abs(dial() - gliding.target) > 1 &&
    gliding.waits++ < GLIDE_WAITS
  ) {
    scheduleSettle();
    return;
  }
  gliding = null;
  rebase();
}

export function advancePreviewFold() {
  const maximum = range();
  const x = dial();
  if (!path.length || x >= maximum - 0.5) return false;
  const step = unit();
  const next = Math.floor(foldPosition(x, step)) + 1;
  // Land each key synchronously so rapid presses cannot reuse a partial fold.
  dialTo(Math.min(maximum, Math.round(next * step)), false);
  applyScroll();
  return true;
}

let scrollStep = 0;
let scrollColumns = 0;

/* Where the dial rests after a tap or a geometry change at a whole stop
   (ADR 0022): never hiding the focused column, nor the one it opened. Left of
   natural that means the nearest widened stop showing both; right of natural,
   the fewest ancestor folds that fit the preview reserve. */
function restingPlace(x, position, keepScroll) {
  if (x < 0) {
    const needed = Math.min(path.length, focusCol + 2);
    if (wideCount(x) >= needed) return x;
    const j = counts.filter((n) => n >= needed).length;
    return -j * unit();
  }
  const k = automaticFold(
    widths,
    GUTTER(),
    SPINE(),
    previewTarget(),
    finder.clientWidth,
    focusCol,
    keepScroll ? position : folded,
    root.dataset.layout === "compressed-columns",
  );
  return Math.round(k * unit());
}

export function layout(keepScroll) {
  if (!path.length) return;
  // Preserve the fold position, not pixels whose meaning changes with the path.
  const x = dial();
  const position = scrollStep ? foldPosition(x, scrollStep) : 0;
  const wide = position < 0 ? wideCount(x) : 0;
  const stageW = finder.clientWidth;
  setVar(root, "--stage-w", stageW + "px");
  setVar(root, "--preview-w", previewTarget() + "px");

  const nextStep = unit();
  const geometryChanged = nextStep !== scrollStep ||
    path.length !== scrollColumns;
  const previousCounts = counts;
  measureStops();
  const stopsChanged = counts.length !== previousCounts.length ||
    counts.some((n, i) => n !== previousCounts[i]);
  let target = x;
  if (keepScroll && scrollStep && (geometryChanged || stopsChanged)) {
    const nextPosition = position > scrollColumns
      ? path.length * position / scrollColumns
      : position;
    target = Math.round(nextPosition * nextStep);
    if (wide && Number.isInteger(position)) {
      // The same number of columns filling the finder, whichever stop that is.
      const j = counts.indexOf(wide);
      target = -(j >= 0 ? j + 1 : Math.min(-position, counts.length)) *
        nextStep;
    }
    target = Math.max(stops[0], target);
  }
  scrollStep = nextStep;
  scrollColumns = path.length;

  // A new column or density can consume the preview reserve even during ↑/↓.
  // Keep deliberate partial folds and the fully folded preview position intact.
  const resting = !keepScroll ||
    (geometryChanged && Number.isInteger(position) && position <= focusCol);
  // The move that keeps the position on a new geometry lands at once, so the
  // fold it paints is already right; only the resting place glides.
  if (target !== x) dialTo(target, false);
  const rest = resting ? restingPlace(target, position, keepScroll) : target;
  if (rest !== target) {
    dialTo(rest, true);
  } else if (!gliding && !settleTimer) {
    // The same place on a new geometry: refit the range to it now, unless a
    // scroll is under way — settling will, and a fling must not re-base early.
    rebase();
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
  const max = range();
  const x = dial();
  const p = Math.min(1, Math.max(0, x) / max);
  const n = path.length;

  const { raw, t } = foldFromScroll(x, max);
  const { focusLeft, focusRight } = applyWidths(x, t);
  // The focus pan belongs to the folds; it fades out over the first widening.
  const pan = panFocus(raw, focusLeft, focusRight) *
    Math.max(0, Math.min(1, 1 + x / unit()));
  slideTail(p, pan, n);

  document.getElementById("st-fold").textContent = folded
    ? `${folded}/${n} folded`
    : "";
  paintTrail();
}

function foldFromScroll(x, max) {
  const result = foldingAt(Math.max(0, x), max, path.length);
  setState({ folded: result.folded });
  return result;
}

function applyWidths(x, t) {
  const g = GUTTER(), sp = SPINE(), n = path.length;
  const sizes = x < 0
    ? widenedSizes(widths, x, unit(), counts, finder.clientWidth, g)
    : widths;
  const metrics = columnMetrics(sizes, folded, t, focusCol, g, sp);
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

/* A sideways wheel over the preview turns the dial first ([78], ADR 0076).
   .pv-body and a wide code block are scroll containers inside the dial, so
   the browser would hand them the gesture and the preview would scroll
   instead of widening. The dial takes the wheel until it is at its end,
   where the preview is as wide as the screen allows; the preview's own
   scrollers get the next gesture. A gesture latches to the dial, as a
   browser latches one to a scroller: the fling that reaches the end does
   not run on into the code block. Fullscreen already fills the screen,
   so its scrollers always get the gesture, including a latched one. */
function previewWheel(e) {
  if (pvFullscreen || !e.target.closest?.("#preview")) return false;
  if (wheeling) return true;
  wheeling = dial() < range() - 0.5;
  return wheeling;
}

/* The innermost scroller under the wheel that can still move along axis in
   the direction of delta. #finder, the dial, is the last one, except in
   fullscreen: the preview fills the screen there, and the dial behind it
   must not turn. */
function scrollerAlong(el, axis, delta) {
  const [size, client, offset, overflow] = axis === "x"
    ? ["scrollWidth", "clientWidth", "scrollLeft", "overflowX"]
    : ["scrollHeight", "clientHeight", "scrollTop", "overflowY"];
  const last = (pvFullscreen && el.closest?.("#preview")) || finder;
  for (;; el = el.parentElement) {
    // More than a pixel: a fractional line height overflows by one.
    const room = delta > 0 ? el[size] - el[client] - el[offset] : el[offset];
    if (room > 1 && /auto|scroll/.test(getComputedStyle(el)[overflow])) {
      return el;
    }
    if (el === last) return null;
  }
}

// deltaMode: 0 pixels, 1 lines, 2 pages
const wheelPixels = (e, delta, page) =>
  delta * (e.deltaMode === 1 ? 40 : e.deltaMode === 2 ? page : 1);

export function initLayout(render) {
  finder.addEventListener("scroll", () => {
    applyScroll();
    scheduleSettle();
  }, { passive: true });
  /* A fling keeps sending wheel events after the scrollbar has hit its end;
     re-basing the range before they stop would let the rest of the momentum
     run through the stop. A finger or a scrollbar drag holds the range. */
  finder.addEventListener("wheel", (e) => {
    gliding = null; // the browser drops a glide on user input
    scheduleSettle();
    if (e.ctrlKey) return; // a pinch or Ctrl+wheel zooms; it is no scroll
    /* A gesture keeps the axis it started on ([110], ADR 0084): fingers
       scrolling a document drift sideways, and that must not turn the dial.
       The axis is the way the gesture went further in its first AXIS_SLOP
       pixels. Until then its events go nowhere: the browser would latch
       them to whichever scroller can take any part of the first one. */
    const { deltaX: dx, deltaY: dy } = e;
    if (!dx && !dy) return;
    if (!wheelAxis) {
      travelX += Math.abs(wheelPixels(e, dx, finder.clientWidth));
      travelY += Math.abs(wheelPixels(e, dy, finder.clientHeight));
      if (Math.max(travelX, travelY) < AXIS_SLOP && e.cancelable) {
        e.preventDefault();
        return;
      }
      wheelAxis = travelX > travelY ? "x" : "y";
    }
    const x = wheelAxis === "x";
    if (x && e.cancelable && previewWheel(e)) {
      e.preventDefault();
      const left = wheelPixels(e, dx, finder.clientWidth);
      finder.scrollBy({ left, behavior: "instant" });
      return;
    }
    /* Along its axis the browser scrolls the event. Drift across it is
       dropped by scrolling the axis by hand, unless the browser has latched
       a scroller and no longer lets the event be cancelled. */
    if (!(x ? dy : dx) || !e.cancelable) return;
    e.preventDefault();
    const delta = x ? dx : dy;
    const el = delta && scrollerAlong(e.target, wheelAxis, delta);
    if (!el) return;
    const px = wheelPixels(e, delta, x ? el.clientWidth : el.clientHeight);
    el.scrollBy({ [x ? "left" : "top"]: px, behavior: "instant" });
  });
  finder.addEventListener("touchmove", () => {
    gliding = null;
    scheduleSettle();
  }, { passive: true });
  finder.addEventListener("pointerdown", (e) => {
    if (e.pointerType === "mouse") mouseDown = true;
  });
  finder.addEventListener("touchstart", () => touching = true, {
    passive: true,
  });
  for (const event of ["pointerup", "pointercancel"]) {
    addEventListener(event, () => {
      mouseDown = false;
      scheduleSettle();
    });
  }
  for (const event of ["touchend", "touchcancel"]) {
    addEventListener(event, () => {
      touching = false;
      scheduleSettle();
    });
  }
  addEventListener("blur", () => {
    mouseDown = touching = false; // a release the page never saw
    scheduleSettle();
  });
  /* Nothing may leave #stage scrolled — see applyScroll. A click that brings
     its button into view drags the strip out through the left edge, and if the
     dial is at rest no scroll or render follows to put it back. Undo it here,
     when it happens, rather than at whatever event comes next. */
  stage.addEventListener("scroll", () => {
    if (stage.scrollLeft) stage.scrollLeft = 0;
  }, { passive: true });
  addEventListener("resize", () => {
    const previewFocused = document.activeElement?.id === "preview";
    render(previewFocused);
    if (previewFocused) {
      document.getElementById("preview")?.focus({ preventScroll: true });
    }
  });
}
