/* ═══════════════════════════════════════════════════════════════════════════
   Type-ahead

   Typing letters jumps to a row in the focused column. In a folder of 400
   entries that is three keystrokes instead of 200 presses of ↓.

   Three rungs, tried in order over the whole column, first hit wins:

     1. prefix     "re" → readme.md
     2. substring  "notes" → beta-notes.md, when nothing *starts* with "notes"
     3. fuzzy      "arp" → Alpha Report.txt, the letters in order, gaps allowed

   The rung that matched also decides what gets marked, so the highlight is the
   explanation: a solid run for rungs 1 and 2, scattered characters for rung 3.

   Nothing here knows where the entries came from, so it is shared with the
   server build — a column is a list of names either way.
   ═══════════════════════════════════════════════════════════════════════════ */

/* How long the buffer survives a pause. 1.2 s is long enough to type "adme"
   after "re" without hurrying, short enough that a search you walked away from
   is gone before you touch the keyboard again. */
const TA_IDLE = 1200;

let taBuf   = "";     /* what has been typed since the last pause */
let taTimer = null;
let taRow   = null;   /* the row wearing <mark> right now, so it can be undone */
let taName  = "";     /* its plain name, to rebuild the label from */

const taLive = () => taBuf !== "";

/* A letter with Ctrl, ⌘ or Alt held belongs to the browser or to a command —
   ⌘C copies the path, ⌘R reloads. Swallowing those into a search is the kind
   of bug you notice only when reload stops working. Shift does not disqualify:
   capital letters are part of file names. Backspace counts only while a search
   is live, so it stays free for anything else to claim later. */
const taWants = e =>
  !e.ctrlKey && !e.metaKey && !e.altKey &&
  (e.key.length === 1 || (e.key === "Backspace" && taLive()));

/* All of `q` in `n`, in order, gaps allowed. No allocation: this runs once per
   entry per keystroke, and a column can hold thousands. */
const taFuzzy = (n, q) => {
  let qi = 0;
  for (let i = 0; i < n.length && qi < q.length; i++) if (n[i] === q[qi]) qi++;
  return qi === q.length;
};

/* Row index of the winner, or -1. Three passes, each stopping at its own first
   hit — a prefix match on row 2 never looks at rows 3…3000. A prefix match on
   row 2 800 still beats a substring match on row 3, which is the point of
   separate passes rather than one scan that scores. */
function taSearch(lower, q) {
  let i = lower.findIndex(n => n.startsWith(q));
  if (i < 0) i = lower.findIndex(n => n.includes(q));
  if (i < 0) i = lower.findIndex(n => taFuzzy(n, q));
  return i;
}

/* Which characters of `lower` the query landed on: a contiguous run for prefix
   and substring, scattered ones for fuzzy. Runs once, on the winner only. */
function taHits(lower, q) {
  const hit = new Array(lower.length).fill(false);
  const at = lower.indexOf(q);
  if (at >= 0) {
    for (let k = 0; k < q.length; k++) hit[at + k] = true;
    return hit;
  }
  let qi = 0;
  for (let i = 0; i < lower.length && qi < q.length; i++)
    if (lower[i] === q[qi]) { hit[i] = true; qi++; }
  return qi === q.length ? hit : null;
}

/* Consecutive hits become one <mark>, so "notes" is a single pill and a fuzzy
   match is a row of beads. */
const taRuns = (text, hit, off) => {
  let out = "", open = false;
  for (let i = 0; i < text.length; i++) {
    const on = !!hit[off + i];
    if (on !== open) { out += on ? "<mark>" : "</mark>"; open = on; }
    out += esc(text[i]);
  }
  return out + (open ? "</mark>" : "");
};

/* The same structure buildCol writes, so un-marking restores it exactly. */
const taLabel = (name, hit) => {
  const [stem, ext] = splitName(name);
  return hit
    ? taRuns(stem, hit, 0) + `<span class="dim">${taRuns(ext, hit, stem.length)}</span>`
    : `${esc(stem)}<span class="dim">${esc(ext)}</span>`;
};

const taSay = msg => { document.getElementById("st-find").textContent = msg; };

function taUnmark() {
  if (taRow) taRow.querySelector(".label").innerHTML = taLabel(taName, null);
  taRow = null;
}

/* Only two rows are ever rewritten per keystroke: the one that was marked and
   the one that now is. Marking every matching row would be an innerHTML write
   per entry, which is the O(entries)-per-keystroke cost this app spent a lot of
   effort deleting (740 ms → 4–9 ms at 3 000 entries). */
function taMark(row, name, hit) {
  taUnmark();
  if (!hit) return;
  row.querySelector(".label").innerHTML = taLabel(name, hit);
  taRow = row;
  taName = name;
}

function taCancel() {
  clearTimeout(taTimer);
  taTimer = null;
  if (!taLive()) return;
  taBuf = "";
  taUnmark();
  taSay("");
}

/* One keystroke. `c` is the focused column's cache entry, which nav.js has
   already looked up — never re-query the rows, a directory can hold tens of
   thousands of them. */
function taType(key, c) {
  taBuf = key === "Backspace" ? taBuf.slice(0, -1) : taBuf + key;
  clearTimeout(taTimer);
  if (!taLive()) return void taSay("");
  taTimer = setTimeout(taCancel, TA_IDLE);

  /* The match runs on the rows the column already holds. A directory still
     being read has none, so nothing matches and the buffer waits — there is no
     re-run when the read lands, because by then you have typed more anyway. */
  if (!c.rows.length) return void taSay(`⌕ ${taBuf} — still reading`);

  /* Lower-cased names, cached beside the rows they were built from, so the two
     die together. Lower-casing 3 000 names costs ~1.4 ms; paying it once per
     column instead of once per keystroke is what keeps a search inside the
     budget the arrow keys set. */
  const lower = (c.lower ||= c.kids.map(k => k.name.toLowerCase()));
  const q = taBuf.toLowerCase();
  const i = taSearch(lower, q);
  taSay(i < 0 ? `⌕ ${taBuf} — no match` : `⌕ ${taBuf}`);
  if (i < 0) return;   /* keep the buffer: Backspace should undo the typo */

  const name = c.kids[i].name;
  taUnmark();          /* before the click, so the row it re-selects is clean */
  c.rows[i].click();   /* the ordinary selection path: preview, trail, URL */
  revealRow(c.rows[i]);
  /* toLowerCase can change a string's length ("İ" → two characters), and then
     the hit positions no longer index the original name. Skip the marks rather
     than paint them one character off. */
  taMark(c.rows[i], name, lower[i].length === name.length ? taHits(lower[i], q) : null);
}

/* A real click means you went somewhere by hand, so the search is over. The
   click taType fires is untrusted, which is exactly the distinction needed —
   no flag to set and unset around it. */
document.addEventListener("click", e => { if (e.isTrusted) taCancel(); });
