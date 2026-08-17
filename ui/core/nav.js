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

/* Where you are, from the root down to the selected row. The first element is a
   folder *name*, not an absolute path: the File System Access API never hands
   one out, so this is everything the app knows about the location. */
function pathParts() {
  const parts = path.map(p => p.name);
  const leaf = sel[path.length - 1];
  if (leaf) parts.push(leaf);
  return parts;
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
  document.getElementById("st-path").textContent = pathParts().join(" / ");
}

/* ── Copy path ──────────────────────────────────────────────────────────────
   The status strip already shows where you are; ⌘C, or a click on it, puts that
   path on the clipboard.

   navigator.clipboard.writeText can be refused: a browser policy, a page the
   user has not touched yet, an insecure context with no clipboard object at
   all. A silent refusal is the worst outcome, because the next paste hands over
   whatever was on the clipboard before and nothing says so. So a refusal says
   so and selects the path, which leaves the browser's own ⌘C one keystroke
   away — the fallback needs no permission because the user presses it. */
function sayCopy(msg, ok) {
  const el = document.getElementById("st-copy");
  el.textContent = msg;
  el.classList.toggle("bad", !ok);
  clearTimeout(sayCopy.t);
  /* a success can flash; a refusal has to stay long enough to be read and
     acted on, because it is asking for a second keystroke */
  sayCopy.t = setTimeout(() => { el.textContent = ""; el.classList.remove("bad"); },
                         ok ? 1600 : 8000);
}

function selectPath() {
  const r = document.createRange();
  r.selectNodeContents(document.getElementById("st-path"));
  const s = getSelection();
  s.removeAllRanges();
  s.addRange(r);
}

async function copyPath() {
  const text = pathParts().join("/");
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    sayCopy("copied", true);
  } catch (err) {
    selectPath();
    sayCopy(`clipboard refused (${err.name || "error"}) — press ${COPY_KEY} again`, false);
  }
}

const MAC = /Mac|iP(hone|ad)/.test(navigator.userAgentData?.platform || navigator.platform || "");
const COPY_KEY = MAC ? "⌘C" : "Ctrl+C";
document.getElementById("kbd-copy").textContent = COPY_KEY;
document.getElementById("st-path").onclick = copyPath;

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

  /* ⌘C / Ctrl+C. A live text selection wins: the user highlighted something and
     asked for *that*, and after a refused copy the selected path is exactly
     what the second press has to reach. */
  if (e.key === "c" && (e.metaKey || e.ctrlKey) && !getSelection().toString()) {
    e.preventDefault();
    return void copyPath();
  }
  /* Letters go to the search unless an arrow, Home/End or Escape claimed the
     keystroke first — those four are the navigation model and type-ahead does
     not get to argue with them. Each of them also ends a live search. */
  if (taWants(e)) {
    e.preventDefault();
    return void taType(e.key, c);
  }
  if (e.key !== "Escape") taCancel();

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
    /* one Escape does one thing: abandon the search if there is one, otherwise
       close the popover. Both at once would make it impossible to tell which
       one the key just did. */
    if (taLive()) taCancel(); else closeSettings();
  }
});
