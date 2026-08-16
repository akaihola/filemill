/* ═══════════════════════════════════════════════════════════════════════════
   Navigation
   ═══════════════════════════════════════════════════════════════════════════ */
async function choose(colIdx, node, rowIdx) {
  path = path.slice(0, colIdx + 1);
  sel  = sel.slice(0, colIdx);
  sel[colIdx] = node.name;
  cursor = { [colIdx]: rowIdx };
  focusCol = colIdx;
  if (node.dir) { path.push(node); focusCol = colIdx + 1; cursor[focusCol] = 0; }
  render();
  if (node.dir && node.kids === null) {
    await ensureLoaded(node);
    if (path.includes(node)) render();          /* still on screen? repaint it */
  }
}

/* clicking a spine scrolls back just far enough to unfold it */
function unfoldTo(i) {
  finder.scrollTo({ left: Math.round(i * foldUnit() * range()), behavior: "smooth" });
}

function renderCrumbs() {
  const el = document.getElementById("crumbs");
  el.textContent = "";
  path.forEach((p, i) => {
    if (i) el.insertAdjacentHTML("beforeend", `<span class="crumb-sep">›</span>`);
    const b = document.createElement("span");
    b.className = "crumb" + (i === path.length - 1 ? " here" : "");
    b.textContent = p.name;
    b.onclick = () => { path = path.slice(0, i+1); sel = sel.slice(0, i); focusCol = i; render(); };
    el.appendChild(b);
  });
  document.getElementById("st-path").textContent =
    path.map(p => p.name).join(" / ") + (sel[path.length-1] ? " / " + sel[path.length-1] : "");
}

document.addEventListener("keydown", e => {
  if (!welcome.hidden) return;
  /* the cached column knows its rows — never re-query them, a directory can
     hold tens of thousands and this runs on every keystroke */
  const c = colCache.get(path[focusCol]);
  if (!c) return;
  const rows = c.rows;
  let ci = cursor[focusCol] ?? c.kids.findIndex(k => k.name === sel[focusCol]);
  if (ci < 0) ci = 0;

  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    if (!rows.length) return;
    /* a freshly opened column has a cursor but no selection yet — the first
       press should commit that row, not skip past it */
    if (sel[focusCol] !== undefined)
      ci = Math.max(0, Math.min(rows.length - 1, ci + (e.key === "ArrowDown" ? 1 : -1)));
    rows[ci].click();
    rows[ci].scrollIntoView({ block: "nearest" });
  } else if (e.key === "ArrowRight" || e.key === "Enter") {
    e.preventDefault();
    const next = path[focusCol + 1];
    /* nothing open to the right yet: commit the cursor row, which descends
       into it when it is a directory */
    if (!next) return void rows[ci]?.click();
    focusCol++; cursor[focusCol] ??= 0;
    /* the column may still be reading — land on its first row once it is there */
    const enter = () => strip
      .querySelectorAll(`.col[data-i="${focusCol}"] .row`)[cursor[focusCol]]?.click();
    if (next.kids === null) ensureLoaded(next).then(enter); else enter();
  } else if (e.key === "ArrowLeft") {
    e.preventDefault();
    if (focusCol > 0) { focusCol--; if (folded > focusCol) unfoldTo(focusCol); render(true); }
  } else if (e.key === "Escape") {
    closeSettings();
  }
});
