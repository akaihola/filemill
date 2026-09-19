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
    columnSpan(sizes, count, gutter, spine) + preview > viewport
  ) count++;
  return compressed ? sizes.length : Math.min(focus, Math.max(count, previous));
}
export function foldingAt(scroll, maximum, count) {
  if (!count) return { raw: 0, folded: 0, t: 0 };
  // Half a pixel compensates for rounded scroll positions at fold boundaries.
  const raw = Math.min(1, (scroll + 0.5) / maximum) / foldStep(count);
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
