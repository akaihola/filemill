/* ═══════════════════════════════════════════════════════════════════════════
   Navigation

   Focus follows the *selection*, not the newly opened column: selecting a
   directory opens its column as a preview but keeps you where you are, so ↑/↓
   keep walking the current column. → is what moves you in, ← what moves out.
   ═══════════════════════════════════════════════════════════════════════════ */
/* How long a column may stay unopened while its directory is read. Long enough
   that a local read of any ordinary size lands first, short enough to pass for
   an instant response. */
const OPEN_GRACE = 50;

let navSeq = 0;   /* a read that outlives its selection must not repaint */

async function choose(colIdx, node, rowIdx) {
  const seq = ++navSeq;
  path = path.slice(0, colIdx + 1);
  sel  = sel.slice(0, colIdx);
  sel[colIdx] = node.name;
  cursor = { [colIdx]: rowIdx };
  focusCol = colIdx;
  path[colIdx].lastSel = node.name;   /* → returns to where you were last time */
  if (!node.dir) return void render();

  const reading = node.kids === null ? FS.ensureLoaded(node) : null;
  if (reading) {
    /* Highlight the row at once, but hold its column back for a moment: a
       column measures the names it holds, and one built before the read lands
       measures empty — it would open at the minimum width and jump wider a
       frame later. Most directories arrive well inside the grace; a slower one
       opens on the spinner, which is honest about the wait. */
    render();
    await Promise.race([reading, new Promise(r => setTimeout(r, OPEN_GRACE))]);
    if (seq !== navSeq) return;       /* selection moved on while it was read */
  }
  path.push(node);
  render();
  if (reading) {
    await reading;
    if (seq === navSeq && path.includes(node)) render();   /* still up? repaint */
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

/* Entering a column: the row it was left on, else the one it remembers, else
   the first. The column may still be reading, so this can run twice. */
function enterColumn(i) {
  const c = colCache.get(path[i]);
  if (!c || !c.rows.length) return;
  let ri = cursor[i];
  if (ri == null) ri = c.kids.findIndex(k => k.name === path[i].lastSel);
  cursor[i] = ri = Math.max(0, Math.min(c.rows.length - 1, ri < 0 ? 0 : ri));
  c.rows[ri].click();
  c.rows[ri].scrollIntoView({ block: "nearest" });
}

/* Stepping right into a column that has no rows would move focus with nothing
   to highlight — the screen would not change, yet ↑/↓ would go dead. Stay put.
   columnFor rebuilds the column if it finished reading since the last render. */
function stepInto(node) {
  const i = path.indexOf(node);
  if (i < 0) return;                    /* moved on while it was still reading */
  if (!columnFor(node).rows.length) return;
  focusCol = i;
  enterColumn(i);
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
    /* a freshly entered column has a cursor but no selection yet — the first
       press should commit that row, not skip past it */
    if (sel[focusCol] !== undefined)
      ci = Math.max(0, Math.min(rows.length - 1, ci + (e.key === "ArrowDown" ? 1 : -1)));
    rows[ci].click();
    rows[ci].scrollIntoView({ block: "nearest" });
  } else if (e.key === "Home" || e.key === "End") {
    e.preventDefault();
    if (!rows.length) return;
    const ri = e.key === "Home" ? 0 : rows.length - 1;
    rows[ri].click();
    rows[ri].scrollIntoView({ block: "nearest" });
  } else if (e.key === "ArrowRight" || e.key === "Enter") {
    e.preventDefault();
    const next = path[focusCol + 1];
    /* nothing open to the right: commit the cursor row, which opens it when it
       is a directory — a second → then steps into that column */
    if (!next) return void rows[ci]?.click();
    if (next.kids === null) FS.ensureLoaded(next).then(() => { render(); stepInto(next); });
    else stepInto(next);
  } else if (e.key === "ArrowLeft") {
    e.preventDefault();
    if (focusCol > 0) { focusCol--; if (folded > focusCol) unfoldTo(focusCol); render(true); }
  } else if (e.key === "Escape") {
    closeSettings();
  }
});
