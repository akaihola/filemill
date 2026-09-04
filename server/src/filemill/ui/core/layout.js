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
  const max = Math.max(1, rail.clientWidth - finder.clientWidth);
  const p = Math.min(1, finder.scrollLeft / max);
  const n = path.length;

  /* Half a pixel of slack, in pixels: layout() and unfoldTo() write
     round(k·unit·range), which can fall up to 0.5 px short of the boundary. A
     fixed 0.002 units was only 0.3 px once seven columns made a unit 160 px
     wide, and a landing read one column short paints the column ← just
     reached as a spine, with folded === focusCol so the next ← never scrolls. */
  const raw = Math.min(1, (finder.scrollLeft + 0.5) / max) / foldUnit();
  folded = Math.min(n, Math.floor(raw));
  /* how far into folding the next column is — 0 = full width, 1 = a spine */
  const t = Math.min(1, Math.max(0, raw - folded));

  /* the strip lays out left to right from the stage's edge, so walking it with
     the widths this pass is about to write is where the focused column's own
     box comes from — arithmetic, not a rect read on every scroll event */
  const g = GUTTER(), sp = SPINE();   /* both read a computed style — once, not per column */
  let x = g, focusLeft = 0, focusRight = 0;
  [...strip.querySelectorAll(".col")].forEach((col, i) => {
    col.classList.toggle("spine", i < folded);
    col.classList.toggle("folding", i === folded && folded < n);
    const w = i < folded ? sp
            : i === folded ? Math.round(widths[i] + (sp - widths[i]) * t)
            : widths[i];
    if (i === focusCol) { focusLeft = x; focusRight = x + w; }
    x += w + g;
    if (i < folded) { set(col.style, "width", ""); return; }
    set(col.dataset, "fold", String(i === folded ? t : 0));
    setVar(col, "--fold", col.dataset.fold);   /* custom props need setProperty */
    set(col.style, "width", w + "px");
  });

  /* The cap in layout() keeps the column under the finger out of the spines. It
     cannot keep it on screen: every folded ancestor still costs a spine and a
     gutter, and the column itself can be as wide as measure() allows. Measured
     at 390 px on a tree of long names, tapping two levels down left 292 px of a
     376 px column inside the viewport and clipped the rest — the row the finger
     had just hit, cut off at the right edge, which is the whole bug. Folding
     further is the one answer the cap forbids, so the strip slides left instead:
     by exactly the overflow, and never past focus's own left edge. A column
     wider than the whole stage therefore gets its left edge, which is all a
     stage that narrow has to give.

     `reach` is what keeps this the tap's answer rather than a second dial. It
     is 0 until the dial has folded everything left of focus — the resting place
     layout() targets after a tap — so scrolling back left unfolds the strip
     where it stands instead of dragging it after a focus five columns along.
     Between the two it fades in with the fold it belongs to, so the slide is
     part of that motion and not a jump at the end of it. */
  const reach = Math.min(1, Math.max(0, raw - focusCol + 1));
  const pan = reach * Math.min(Math.max(0, focusRight - finder.clientWidth),
                               Math.max(0, focusLeft - g));

  /* last 1%: slide the spine strip itself off the left edge. Widening the strip
     by the same amount keeps the preview's flex-grow filling to the right edge. */
  const tail  = p > 0.99 ? (p - 0.99) / 0.01 : 0;
  const shift = tail * n * (sp + g) + pan;
  set(strip.style, "minWidth", (finder.clientWidth + shift) + "px");
  set(strip.style, "transform", `translateX(${-shift}px)`);

  document.getElementById("st-fold").textContent =
    folded ? `${folded}/${n} folded` : "";
  paintTrail();
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
function revealRow(row) {
  const body = row.parentElement;                      /* .col-body scrolls */
  const r = row.getBoundingClientRect(), b = body.getBoundingClientRect();
  if (r.top < b.top) body.scrollTop += r.top - b.top;
  else if (r.bottom > b.bottom) body.scrollTop += r.bottom - b.bottom;
}

finder.addEventListener("scroll", applyScroll, { passive: true });
addEventListener("resize", () => render());
