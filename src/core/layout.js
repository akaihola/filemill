/* ═══════════════════════════════════════════════════════════════════════════
   Layout + the scroll dial

   scrollLeft is not a translation — it is a 0–100% condensing dial:
     0%       every column unfolded; preview overflows off the right edge
     k·unit   the leftmost k columns folded to spines   (unit = 99% / ncols)
     99%      every column folded; preview fills what is left
     99–100%  the spine strip itself slides away; at 100% the preview is alone
   ═══════════════════════════════════════════════════════════════════════════ */
function stripSpan(k) {                     /* width of the column strip with k folded */
  const g = GUTTER(), n = path.length;
  const cols = widths.reduce((a, w, i) => a + (i < k ? SPINE() : w), 0);
  return cols + g * (n + 1);                /* padding either side + inter-column gaps */
}
const foldUnit = () => 0.99 / path.length;
const range    = () => Math.max(1, stripSpan(0) - GUTTER());

function layout(keepScroll) {
  const stageW = finder.clientWidth;
  setVar(root, "--stage-w", stageW + "px");
  setVar(root, "--preview-w", previewTarget() + "px");
  rail.style.width = (stageW + range()) + "px";

  if (!keepScroll) {
    /* default: the least folding that still gives the preview its full width */
    let k = 0;
    while (k < path.length && stripSpan(k) + previewTarget() > stageW) k++;
    finder.scrollLeft = Math.round(k * foldUnit() * range());
  }
  applyScroll();
}

function applyScroll() {
  if (!path.length) return;
  const max = Math.max(1, rail.clientWidth - finder.clientWidth);
  const p = Math.min(1, finder.scrollLeft / max);
  const n = path.length;

  /* the epsilon absorbs sub-pixel scrollLeft rounding at the fold boundaries */
  const raw = p / foldUnit() + 0.002;
  folded = Math.min(n, Math.floor(raw));
  /* how far into folding the next column is — 0 = full width, 1 = a spine */
  const t = Math.min(1, Math.max(0, raw - folded));

  [...strip.querySelectorAll(".col")].forEach((col, i) => {
    col.classList.toggle("spine", i < folded);
    col.classList.toggle("folding", i === folded && folded < n);
    if (i < folded) { set(col.style, "width", ""); return; }
    set(col.dataset, "fold", String(i === folded ? t : 0));
    setVar(col, "--fold", col.dataset.fold);   /* custom props need setProperty */
    set(col.style, "width", (i === folded
      ? Math.round(widths[i] + (SPINE() - widths[i]) * t)
      : widths[i]) + "px");
  });

  /* last 1%: slide the spine strip itself off the left edge. Widening the strip
     by the same amount keeps the preview's flex-grow filling to the right edge. */
  const tail  = p > 0.99 ? (p - 0.99) / 0.01 : 0;
  const shift = tail * n * (SPINE() + GUTTER());
  set(strip.style, "minWidth", (finder.clientWidth + shift) + "px");
  set(strip.style, "transform", `translateX(${-shift}px)`);

  document.getElementById("st-fold").textContent =
    folded ? `${folded}/${n} folded` : "";
  paintTrail();
}

finder.addEventListener("scroll", applyScroll, { passive: true });
addEventListener("resize", () => render());
