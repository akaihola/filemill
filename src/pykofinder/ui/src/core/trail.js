/* ═══════════════════════════════════════════════════════════════════════════
   The trail: an elbow from each selected row into the next column's header.
   The vertical run sits on the centre line of the gutter between the columns.
   ═══════════════════════════════════════════════════════════════════════════ */
function paintTrail() {
  const fr = stage.getBoundingClientRect();
  trail.setAttribute("viewBox", `0 0 ${fr.width} ${fr.height}`);
  trail.style.width = fr.width + "px"; trail.style.height = fr.height + "px";
  let out = "";

  /* a column past the crossfade midpoint anchors on its spine icon, not its rows */
  const asSpine = el => el.classList.contains("spine") || +(el.dataset.fold || 0) > 0.5;

  const cols = [...strip.querySelectorAll(".col")];
  cols.forEach((col, i) => {
    const next = cols[i + 1] || document.getElementById("preview");
    if (!next) return;
    const cr = col.getBoundingClientRect(), nr = next.getBoundingClientRect();

    /* start: right edge of the selected pill, or the spine's icon when folded */
    let x1, y1;
    if (asSpine(col)) {
      const dot = col.querySelector(".dot").getBoundingClientRect();
      x1 = cr.right - fr.left; y1 = dot.top + dot.height / 2 - fr.top;
    } else {
      const selRow = col.querySelector(".row.sel");
      if (!selRow) return;
      const rr = selRow.getBoundingClientRect();
      const br = col.querySelector(".col-body").getBoundingClientRect();
      const cy = rr.top + rr.height / 2;
      if (cy < br.top + 2 || cy > br.bottom - 2) return;   /* scrolled out of view */
      x1 = rr.right - fr.left; y1 = cy - fr.top;
    }
    if (x1 < 0) return;   /* origin has slid off the left edge — no dangling hook */

    /* end: the next column's header — or its spine icon when that one is folded */
    const anchor = asSpine(next)
      ? next.querySelector(".dot") : next.querySelector(".col-head");
    const ar = anchor && anchor.getBoundingClientRect();
    const x2 = nr.left - fr.left;
    const y2 = ar ? ar.top + ar.height / 2 - fr.top : nr.top + 15 - fr.top;

    /* the vertical run bisects the gutter, not the pill-to-column span */
    const mx = (cr.right + nr.left) / 2 - fr.left;
    const r  = Math.min(6, Math.abs(y2 - y1) / 2, Math.abs(mx - x1), Math.abs(x2 - mx));
    const s  = Math.sign(y2 - y1) || 1;
    const dp = Math.abs(y2 - y1) < 1
      ? `M${x1},${y1} L${x2},${y2}`
      : `M${x1},${y1} L${mx - r},${y1} Q${mx},${y1} ${mx},${y1 + s*r}` +
        ` L${mx},${y2 - s*r} Q${mx},${y2} ${mx + r},${y2} L${x2},${y2}`;

    out += `<path class="${+col.dataset.i === focusCol ? "" : "thread"}" d="${dp}"/>`;
  });
  trail.innerHTML = out;
}
