/* ═══════════════════════════════════════════════════════════════════════════
   Navigation

   Focus follows the *selection*, not the newly opened column: selecting a
   directory opens its column as a preview but keeps you where you are, so ↑/↓
   keep walking the current column. → is what moves you in, ← what moves out.
   ═══════════════════════════════════════════════════════════════════════════ */
import { applyPath, currentPath, scrollCursorIntoView } from "./deeplink.js";
import { foldAll, foldUnit, range, revealRow } from "./layout.js";
import { FS } from "./ports.js";
import { colCache, columnFor, render } from "./render.js";
import { closeSettings } from "./settings.js";
import {
  finder,
  focusCol,
  path,
  rowIndex,
  sel,
  setState,
  visibleKids,
} from "./state.js";
import { taCancel, taLive, taType, taWants } from "./typeahead.js";

const OPEN_GRACE = 50; // Let ordinary local reads land before showing the column.
const STATUS_OK_MS = 1600; // Successful status messages need only a brief confirmation.
const STATUS_ERROR_MS = 8000; // Error status messages stay visible long enough to act on.
const PREVIEW_SCROLL_STEP = 40; // Arrow keys move the preview by a small readable increment.

let navSeq = 0; /* a read that outlives its selection must not repaint */

/* When a folder opens with nothing chosen inside it, dash-select its README
   (exact name first, then README.*, then index.html) so the preview shows it.
   Focus stays where it is — this is a preview, not a navigation. */
function autoPreview(node) {
  const i = path.length - 1;
  if (path[i] !== node || sel[i] !== undefined) return;
  const files = visibleKids(node).filter((k) => !k.dir);
  const pick = files.find((k) => k.name === "README") ||
    files.find((k) => k.name.startsWith("README.")) ||
    files.find((k) => k.name === "index.html");
  if (pick) sel[i] = pick.name;
}

export async function choose(colIdx, node, keepScroll = false) {
  const seq = ++navSeq;
  setState({ path: path.slice(0, colIdx + 1), sel: sel.slice(0, colIdx) });
  sel[colIdx] = node.name;
  setState({ focusCol: colIdx });
  if (!node.dir) return void render(keepScroll);

  const reading = node.kids === null ? FS.ensureLoaded(node) : null;
  if (reading) {
    /* Highlight the row at once, but hold its column back for a moment: a
       column measures the names it holds, and one built before the read lands
       measures empty — it would open at the minimum width and jump wider a
       frame later. Most directories arrive well inside the grace; a slower one
       opens on the spinner, which is honest about the wait. */
    render(keepScroll);
    await Promise.race([
      reading,
      new Promise((r) => setTimeout(r, OPEN_GRACE)),
    ]);
    if (seq !== navSeq) return; /* selection moved on while it was read */
    if (!node.dir) {
      /* a virtual wrapper declined the file */
      return void render(keepScroll);
    }
  }
  path.push(node);
  autoPreview(node); /* kids already in memory (revisit, fast read) */
  render(keepScroll);
  if (reading) {
    await reading;
    if (seq !== navSeq || !path.includes(node)) return; /* still up? repaint */
    autoPreview(node); /* kids landed after the grace period */
    render(keepScroll);
  }
}

/* ── Refresh ────────────────────────────────────────────────────────────────
   Neither port can tell the app that a directory changed. The File System
   Access API has no watch call at all, and the server one would need a socket
   the static build cannot open. So a folder read once stays as it was read
   until somebody asks again, and asking has to be a thing the user does.

   Refreshing is *not* a second way to load a directory. It empties node.kids
   and calls the same FS.ensureLoaded every other caller uses — one loading
   path, one debounce, one place where node.kids is written. A separate
   "reload" call would be two writers on one field, and the interleaving that
   loses is the one you never reproduce.

   Which columns it touches, and what survives:

     the focused column          re-read from the port
     columns open below it       re-read too — they are on screen, and a fresh
                                 column beside three stale ones is worse than
                                 the extra reads. Closed subtrees are untouched
     the selection at each level matched again by name: a re-read hands back
                                 new node objects, so the chain is re-walked
                                 rather than kept by identity
     a selected name that is gone the walk stops there, and nothing is selected —
                                 ↓ resumes at the top of the remaining rows, and
                                 the app never shows a selection that is not real
     columns below the stop      closed, because their parent no longer has the
                                 entry that opened them
     focus                       where it was, clamped to the new depth        */
export async function refreshColumn(i) {
  const node = path[i];
  if (!node || !node.dir || !FS) return;

  const seq = ++navSeq; /* a click, a key or a second ⟳ overtakes */
  const names = currentPath();
  const keepFocus = focusCol;
  /* the ⟳ spins on the column that is on screen now; the re-render replaces
     that element, which is exactly when the spinning should stop */
  const spinning = colCache.get(node)?.el;
  spinning?.classList.add("busy");

  try {
    /* A read already in flight owns node.kids. Wait for it before invalidating:
       ensureLoaded hands a concurrent caller the in-flight promise, so asking
       now would return the very listing this refresh was called to replace,
       and two reads would race to write the same field. */
    if (node.loading) await node.loading;
    if (seq !== navSeq) return;

    const before = new Set(visibleKids(node).map((k) => k.name));
    node.kids = null;
    node.denied = undefined;
    /* The entries are about to be different objects, so what was swept is about
       to be about files that are no longer in this listing. A size sort re-reads
       them; a name sort never asked. */
    node.metaDone = false;
    /* Nothing renders between here and the read landing. The column cache still
       holds the previous DOM, so the screen keeps showing the old listing
       instead of flashing back to "Reading…" and losing its scroll position. */
    await FS.ensureLoaded(node);
    if (seq !== navSeq) return;

    const after = visibleKids(node);
    const added = after.reduce((n, k) => n + !before.has(k.name), 0);
    const gone = before.size - (after.length - added);

    /* The same walk a deep link uses: down from the root by name, stopping at
       the first segment that is not there. Three callers, one implementation —
       refresh, a pasted link, and a restored folder cannot disagree about what
       a half-valid chain means. */
    const complete = await applyPath(names, keepFocus);
    if (seq !== navSeq) return;

    if (complete) {
      saySt(
        "st-refresh",
        added || gone ? `⟳ ${added} new, ${gone} gone` : "⟳ no change",
        true,
      );
      return;
    }
    const stop = path.length - 1; /* where the walk ran out */
    const col = colCache.get(path[stop]);
    render(true);
    scrollCursorIntoView();
    saySt("st-refresh", `⟳ ${names[stop]} is gone`, false);
  } finally {
    spinning?.classList.remove("busy");
  }
}

/* clicking a spine scrolls back just far enough to unfold it */
export function unfoldTo(i) {
  finder.scrollTo({
    left: Math.round(i * foldUnit() * range()),
    behavior: "smooth",
  });
}

/* Where you are, from the root down to the selected row. The first element is a
   folder *name*, not an absolute path: the File System Access API never hands
   one out, so this is everything the app knows about the location. */
export function renderCrumbs() {
  const el = document.getElementById("crumbs");
  el.textContent = "";
  path.forEach((p, i) => {
    if (i) {
      el.insertAdjacentHTML("beforeend", `<span class="crumb-sep">›</span>`);
    }
    const b = document.createElement("span");
    b.className = "crumb" + (i === path.length - 1 ? " here" : "");
    b.textContent = p.name;
    b.onclick = () => {
      setState({
        path: path.slice(0, i + 1),
        sel: sel.slice(0, i),
        focusCol: i,
      });
      render();
    };
    el.appendChild(b);
  });
  /* "/" rather than the " / " this strip used to show: clicking it copies the
     string, and a fallback selection copies the characters on screen. The two
     have to be the same string or the fallback quietly hands over a path that
     no shell will take. */
  document.getElementById("st-path").textContent = currentPath().join("/");
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
/* One transient line in the status strip, per slot, cleared on a timer. A
   success can flash; a refusal or a loss stays long enough to be read and acted
   on, because it is asking the user to do something about it. */
export function saySt(id, msg, ok) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.toggle("bad", !ok);
  clearTimeout((saySt.t ||= {})[id]);
  saySt.t[id] = setTimeout(() => {
    el.textContent = "";
    el.classList.remove("bad");
  }, ok ? STATUS_OK_MS : STATUS_ERROR_MS);
}

document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest("#row-menu")) document.getElementById("row-menu").hidden = true;
});

const sayCopy = (msg, ok) => saySt("st-copy", msg, ok);

function selectPath() {
  const r = document.createRange();
  r.selectNodeContents(document.getElementById("st-path"));
  const s = getSelection();
  s.removeAllRanges();
  s.addRange(r);
}

async function copyPath() {
  const text = document.getElementById("st-path").textContent;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    sayCopy("copied", true);
  } catch (err) {
    selectPath();
    sayCopy(
      `clipboard refused (${err.name || "error"}) — press ${COPY_KEY} again`,
      false,
    );
  }
}

const MAC = /Mac|iP(hone|ad)/.test(
  navigator.userAgentData?.platform || navigator.platform || "",
);
const COPY_KEY = MAC ? "⌘C" : "Ctrl+C";
document.getElementById("kbd-copy").textContent = COPY_KEY;
document.getElementById("st-path").onclick = copyPath;

/* Entering a column: the row it was left on, else the one it remembers, else
   the first. The column may still be reading, so this can run twice. */
function enterColumn(i) {
  const c = colCache.get(path[i]);
  if (!c || !c.rows.length) return;
  const remembered = sel[i];
  let ri = rowIndex(path[i], remembered);
  ri = Math.max(0, Math.min(c.rows.length - 1, ri < 0 ? 0 : ri));
  const row = c.ensureRow(ri);
  row.click();
  revealRow(row);
}

/* Stepping right into a column that has no rows would move focus with nothing
   to highlight — the screen would not change, yet ↑/↓ would go dead. Stay put.
   columnFor rebuilds the column if it finished reading since the last render. */
function stepInto(node) {
  const i = path.indexOf(node);
  if (i < 0) return; /* moved on while it was still reading */
  if (!columnFor(node).rows.length) return;
  setState({ focusCol: i });
  enterColumn(i);
}

function pageMove(c, dir, ci) {
  const body = c.body;
  if (!body || !c.rows.length) return;
  const edge = () => {
    const b = body.getBoundingClientRect();
    const visible = c.rows.filter(Boolean).filter((row) => {
      const r = row.getBoundingClientRect();
      return r.bottom > b.top && r.top < b.bottom;
    });
    return dir < 0 ? visible[0] : visible.at(-1);
  };
  let row = edge();
  if (!row) return;
  if (c.rows[ci] === row) {
    const h = row.offsetHeight;
    const lines = h ? Math.max(1, Math.floor(body.clientHeight / h)) : 1;
    body.scrollTop += dir * lines * h;
    row = edge();
  }
  row?.click();
  if (row) revealRow(row);
}

document.addEventListener("keydown", (e) => {
  /* a keystroke inside a form field (the preview editor) is typing, not
     navigation — leave it alone */
  if (
    e.target.matches?.("input, textarea, select") || e.target.isContentEditable
  ) {
    return;
  }
  if (!document.getElementById("welcome")?.hidden) return;
  if (e.target.closest?.("#preview")) {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      if (focusCol > 0) {
        setState({ focusCol: focusCol - 1 });
        unfoldTo(focusCol);
        render(true);
      }
      return;
    }
    if (["ArrowUp", "ArrowDown", "PageUp", "PageDown"].includes(e.key)) {
      const body = document.querySelector("#preview .pv-body");
      e.preventDefault();
      body?.scrollBy({
        top: e.key === "ArrowUp"
          ? -PREVIEW_SCROLL_STEP
          : e.key === "ArrowDown"
          ? PREVIEW_SCROLL_STEP
          : (e.key === "PageUp" ? -1 : 1) * body.clientHeight,
      });
    }
    return;
  }
  /* the cached column knows its rows — never re-query them, a directory can
     hold tens of thousands and this runs on every keystroke */
  const c = colCache.get(path[focusCol]);
  if (!c) return;
  const rows = c.rows;
  let ci = rowIndex(path[focusCol], sel[focusCol]);
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
    /* a freshly entered column has no selection yet — the first
       press should commit that row, not skip past it */
    if (sel[focusCol] !== undefined) {
      ci = Math.max(
        0,
        Math.min(rows.length - 1, ci + (e.key === "ArrowDown" ? 1 : -1)),
      );
    }
    choose(focusCol, c.kids[ci], true);
    revealRow(c.ensureRow(ci));
  } else if (e.key === "Home" || e.key === "End") {
    e.preventDefault();
    if (!rows.length) return;
    const ri = e.key === "Home" ? 0 : rows.length - 1;
    const row = c.ensureRow(ri);
    row.click();
    revealRow(row);
  } else if (e.key === "PageUp" || e.key === "PageDown") {
    e.preventDefault();
    pageMove(c, e.key === "PageUp" ? -1 : 1, ci);
  } else if (e.key === "ArrowRight" || e.key === "Enter") {
    e.preventDefault();
    const next = path[focusCol + 1];
    /* nothing open to the right: commit the row, which opens it when it
       is a directory — a second → then steps into that column */
    if (!next) {
      const row = c.ensureRow(ci);
      row?.click();
      if (e.key === "ArrowRight" && c.kids[ci] && !c.kids[ci].dir) {
        foldAll();
        document.getElementById("preview")?.focus();
      }
      return;
    }
    if (next.kids === null) {
      FS.ensureLoaded(next).then(() => {
        render();
        stepInto(next);
      });
    } else stepInto(next);
  } else if (e.key === "ArrowLeft") {
    e.preventDefault();
    if (focusCol > 0) {
      setState({ focusCol: focusCol - 1 });
      unfoldTo(focusCol);
      render(true);
    }
  } else if (e.key === "F5" && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
    /* Every desktop file manager reads F5 as "re-read this folder", and here a
       page reload is a far worse trade: it drops the mounted root, the whole
       column chain and the scroll position, then asks the browser for the
       folder again. ⌘R, Ctrl+R and Ctrl+F5 are left alone, so a real reload is
       still one keystroke away — the same rule type-ahead follows for ⌘R. */
    e.preventDefault();
    refreshColumn(focusCol);
  } else if (e.key === "Escape") {
    /* one Escape does one thing: abandon the search if there is one, otherwise
       close the popover. Both at once would make it impossible to tell which
       one the key just did. */
    if (taLive()) taCancel();
    else closeSettings();
  }
});
