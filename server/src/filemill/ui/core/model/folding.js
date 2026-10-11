const FOLD_RANGE = 0.99; // The last percent slides the folded strip away.
export const foldStep = (count) => FOLD_RANGE / count;
export const columnSpan = (sizes, count, gutter, spine) =>
  sizes.reduce((sum, width, i) => sum + (i < count ? spine : width), 0) +
  gutter * (sizes.length + 1);
export const scrollRange = (sizes, gutter, spine) =>
  Math.max(1, columnSpan(sizes, 0, gutter, spine) - gutter);
export function automaticFold(
  sizes,
  gutter,
  spine,
  preview,
  viewport,
  focus,
  previous,
  compressed,
) {
  let count = 0;
  while (
    count < sizes.length &&
    columnSpan(sizes, count, gutter, spine) + gutter + preview > viewport
  ) count++;
  return compressed ? sizes.length : Math.min(focus, Math.max(count, previous));
}
export function foldPosition(scroll, step) {
  // Snap rounded landings without adding half a pixel to every partial fold.
  const position = scroll / step;
  const boundary = Math.round(position);
  return Math.abs(scroll - boundary * step) <= 0.5 ? boundary : position;
}
export function foldingAt(scroll, maximum, count) {
  if (!count) return { raw: 0, folded: 0, t: 0 };
  const raw = Math.min(
    1 / foldStep(count),
    foldPosition(scroll, maximum * foldStep(count)),
  );
  const folded = Math.min(count, Math.floor(raw));
  return { raw, folded, t: Math.min(1, Math.max(0, raw - folded)) };
}
export const columnWidth = (width, index, count, progress, spine) =>
  index < count
    ? spine
    : index === count
    ? Math.round(width + (spine - width) * progress)
    : width;
export const focusPan = (raw, focus, left, right, viewport, gutter) =>
  Math.min(1, Math.max(0, raw - focus + 1)) *
  Math.min(Math.max(0, right - viewport), Math.max(0, left - gutter));
export const tailShift = (progress, pan, count, spine, gutter) =>
  (progress > FOLD_RANGE ? (progress - FOLD_RANGE) / 0.01 : 0) * count *
    (spine + gutter) + pan;

export function columnMetrics(sizes, count, progress, focus, gutter, spine) {
  const rendered = sizes.map((width, index) =>
    columnWidth(width, index, count, progress, spine)
  );
  let left = gutter, focusLeft = 0, focusRight = 0;
  rendered.forEach((width, index) => {
    if (index === focus) [focusLeft, focusRight] = [left, left + width];
    left += width + gutter;
  });
  return { sizes: rendered, focusLeft, focusRight };
}

/* ── Dial stops ([81]) ──────────────────────────────────────────────────
   A fling runs to the end of the scrollbar, so the scrollbar is kept one
   stop long in each direction: its range is the span between the stops on
   either side of the dial, and layout.js re-bases it once a scroll settles.
   Right of natural the stops are today's dial: the rightmost column alone
   unfolded, every column folded, the preview alone. Left of natural the
   leftmost columns widen to fill the finder, one fewer at each stop. */
const STOP_TOLERANCE = 0.5; // scroll positions are whole pixels, stops are not

/* How many natural columns fit beside the preview reserve: 3.8 on a 1440px
   laptop ("almost four"), 1.2 on a portrait phone. */
export const fitCount = (width, viewport, preview, gutter) =>
  Math.max(1, Math.floor((viewport - preview - gutter) / (width + gutter)));
export const fillWidth = (count, viewport, gutter) =>
  (viewport - gutter * (count + 1)) / count;

/* The column counts of the widening stops, nearest natural first: one fewer
   than fit, down to two — down to one where fewer than two fit. */
export function wideCounts(columns, fit) {
  const floor = fit < 2 ? 1 : 2;
  const counts = [];
  for (let n = Math.min(columns, fit); n >= floor; n--) counts.push(n);
  return counts;
}

export function dialStops(sizes, counts, gutter, spine) {
  const maximum = scrollRange(sizes, gutter, spine);
  const unit = foldStep(sizes.length) * maximum;
  const stops = counts.map((_, j) => -(j + 1) * unit).reverse();
  for (
    const x of [0, (sizes.length - 1) * unit, sizes.length * unit, maximum]
  ) {
    if (!stops.length || x - stops[stops.length - 1] > STOP_TOLERANCE) {
      stops.push(x);
    }
  }
  return stops;
}

/* The two stops the scrollbar spans around dial position x: the neighbours
   of the stop x rests on, or the pair enclosing x in between. */
export function dialWindow(stops, x) {
  const last = stops.length - 1;
  const at = stops.findIndex((s) => Math.abs(s - x) <= STOP_TOLERANCE);
  if (at >= 0) {
    return {
      lower: stops[Math.max(0, at - 1)],
      upper: stops[Math.min(last, at + 1)],
    };
  }
  const above = stops.findIndex((s) => s > x);
  if (above < 0) return { lower: stops[last], upper: stops[last] };
  return { lower: stops[Math.max(0, above - 1)], upper: stops[above] };
}

/* Column widths at a dial position left of natural: between two stops each
   column slides from its width at one to its width at the next. */
export function widenedSizes(sizes, x, unit, counts, viewport, gutter) {
  const at = (j) => {
    if (j < 1) return sizes;
    const count = counts[Math.min(j, counts.length) - 1];
    const fill = fillWidth(count, viewport, gutter);
    return sizes.map((width, i) => i < count ? fill : width);
  };
  const u = Math.max(0, -x / unit);
  const j = Math.floor(u), t = u - j;
  const from = at(j), to = at(j + 1);
  return from.map((width, i) => width + (to[i] - width) * t);
}
