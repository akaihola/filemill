/* ═══════════════════════════════════════════════════════════════════════════
   Render
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  closeEditor,
  editableText,
  editingPreview,
  openEditor,
} from "../editor/editor.js";
import { enableTaskToggles } from "../editor/task-toggle.js";
import { jsonCollapse } from "./model/json-collapse.js";
import { syncURL } from "./deeplink.js";
import { currentPath } from "./model/deeplink.js";
import { esc, iconHTML } from "./icons.js";
import { layout } from "./layout.js";
import { set, setVar } from "./dom.js";
import { FS, PREVIEW, ROUTER } from "./ports.js";
import { sortSay, sortStatus, sweepMeta } from "./sort.js";
import {
  fmtDate,
  fmtSize,
  focusCol,
  nextPvToken,
  path,
  previewNode,
  pvFullscreen,
  pvToken,
  rowIndex,
  sel,
  selectedNode,
  setState,
  splitName,
  state,
  visibleKids,
  widths,
} from "./model/state.js";
import { folderWidth, root, strip } from "./dom-renderer.js";
import { hlFences } from "./syntax.js";
import { IMAGE_EXTENSIONS } from "./limits.js";
import { classifyFile } from "./file-kind.js";
import { paintTrail } from "./trail.js";

/* Building a column is O(entries), and real directories hold thousands of them
   — far too expensive to redo on every arrow key. A column's DOM is therefore
   built once per (node, entry list) and cached; a re-render only re-applies the
   state that actually changed: depth, selection, width.
   Anything that alters how a row *looks* (dotfile filter, density, theme icon
   colours) is part of the signature and drops the whole cache. */
export const colCache = new Map();
let cacheSig = null;
const CACHE_MAX = 24; // Retain enough nearby columns without growing memory unbounded.
const MAX_DEPTH = 5; // Keep depth styling within the available visual scale.
const SCROLL_HINT_PADDING = 4; // Show the affordance only when content exceeds the viewport.
const VIRTUAL_ROWS = 1000;
const LONG_PRESS_MS = 500;
const touchUI = () =>
  matchMedia("(pointer: coarse)").matches || navigator.maxTouchPoints > 0;

/* A virtual row is positioned by arithmetic, so its pitch has to be the one
   the stylesheet draws: row height plus the margin above and below it. Both
   follow the density setting, which is part of the cache signature. */
function rowStep() {
  const css = getComputedStyle(document.documentElement);
  return parseFloat(css.getPropertyValue("--row-h")) +
    2 * parseFloat(css.getPropertyValue("--row-gap"));
}

let longPressTimer;
let longPressPointer; // only the pointer that started a press may end it
let suppressClick = false;

let menuRow, menuFocus, updateMenuDelete;
const removing = new WeakMap();
export const entryPath = (node, parent) =>
  node.rel ||
  path.slice(1, path.indexOf(parent) + 1).map((n) => n.name).concat(node.name)
    .join("/");
const isRemoving = (node, parent) =>
  removing.get(path[0])?.has(entryPath(node, parent)) || false;

export function closeRowMenu(restoreFocus = true) {
  const menu = document.getElementById("row-menu");
  if (!menu.hidden && restoreFocus) {
    document.activeElement?.blur();
    if (menuFocus?.isConnected) menuFocus.focus({ preventScroll: true });
  }
  menu.hidden = true;
  menuRow?.setAttribute("aria-expanded", "false");
  menuRow = menuFocus = updateMenuDelete = null;
  suppressClick = false;
  clearTimeout(longPressTimer);
}

export async function deleteEntry(node, parent, button) {
  if (isRemoving(node, parent) || !FS.remove || node.vpath) return;
  if (
    !window.confirm(
      `Delete “${node.name}”${node.dir ? " and its contents" : ""}?`,
    )
  ) return;
  const filesystem = FS;
  const deletionRoot = path[0];
  const parentNames = path.slice(0, path.indexOf(parent) + 1).map((n) =>
    n.name
  );
  const relative = entryPath(node, parent);
  const pending = removing.get(deletionRoot) || new Set();
  removing.set(deletionRoot, pending);
  pending.add(relative);
  button.disabled = true;
  let deleted = false;
  try {
    await filesystem.remove(node);
    deleted = true;
    // Invalidate even a folder left during deletion, so revisiting it is fresh.
    if (parent.loading) await parent.loading;
    // A reload can replace the containing node while removal is pending.
    const visible = FS === filesystem && path[0] === deletionRoot &&
      parentNames.every((name, i) => path[i]?.name === name);
    if (visible) await actions.refreshColumn(parentNames.length - 1);
    if (!visible || !path.includes(parent)) {
      parent.kids = null;
      parent.metaDone = false;
    }
    actions.saySt("st-refresh", `Deleted “${node.name}”`, true);
  } catch (err) {
    const message = deleted ? "Deleted; refresh failed" : "Delete failed";
    actions.saySt(
      "st-refresh",
      `${message}: ${String(err.message || err)}`,
      false,
    );
  } finally {
    pending.delete(relative);
    button.disabled = false;
    if (menuRow && !menuRow.isConnected) closeRowMenu();
    else updateMenuDelete?.();
    const preview = previewNode();
    const previewDelete = document.getElementById("pv-delete");
    if (preview && previewDelete) {
      previewDelete.disabled = isRemoving(preview, path[path.length - 1]);
    }
  }
}

export function openRowMenu(node, parent, row, event) {
  closeRowMenu();
  menuRow = row;
  menuFocus = document.activeElement;
  const menu = document.getElementById("row-menu");
  menu.innerHTML = [
    ["Copy name", 2],
    ["Copy relative path", 0],
    ["Copy absolute path", 1],
  ].map(([label, mode]) =>
    `<button type="button" role="menuitem" data-copy="${mode}">${label}</button>`
  ).join("");
  menu.querySelectorAll("button").forEach((button) =>
    button.onclick = async () => {
      suppressClick = false;
      if (await actions.copyPath(node, parent, Number(button.dataset.copy))) {
        closeRowMenu();
      }
    }
  );
  if (FS.remove && !node.vpath) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("role", "menuitem");
    button.textContent = "Delete";
    updateMenuDelete = () => {
      button.disabled = isRemoving(node, parent);
    };
    updateMenuDelete();
    button.onclick = () => {
      closeRowMenu();
      return deleteEntry(node, parent, button);
    };
    menu.appendChild(button);
  }
  menu.hidden = false;
  const bounds = row.getBoundingClientRect();
  const x = event?.clientX ?? bounds.left;
  const y = event?.clientY ?? bounds.bottom;
  menu.style.left = `${
    Math.max(8, Math.min(x, innerWidth - menu.offsetWidth - 8))
  }px`;
  menu.style.top = `${
    Math.max(8, Math.min(y, innerHeight - menu.offsetHeight - 8))
  }px`;
  row.setAttribute("aria-expanded", "true");
  menu.querySelector("button").focus({ preventScroll: true });
}

export function rowMenuKey(event) {
  const menu = document.getElementById("row-menu");
  if (menu.hidden) return false;
  if (event.key === "F5") {
    closeRowMenu();
    return false;
  }
  if (event.key === "Escape" || event.key === "Tab") {
    closeRowMenu();
    if (event.key === "Escape") event.preventDefault();
  } else if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
    event.preventDefault();
    const buttons = [...menu.querySelectorAll("button:not(:disabled)")];
    const index = buttons.indexOf(document.activeElement);
    const next = event.key === "Home"
      ? 0
      : event.key === "End"
      ? buttons.length - 1
      : (index + (event.key === "ArrowDown" ? 1 : -1) + buttons.length) %
        buttons.length;
    buttons[next]?.focus();
  }
  return true;
}

/* Writing the value a property already holds still dirties it — and a width or
   custom-property write on a column relays out every row inside it. Guard the
   writes and a re-render of an unchanged column costs nothing. */
let actions;
export const setActions = (value) => actions = value;

function buildCol(node) {
  const kids = visibleKids(node);
  const el = document.createElement("div");
  el.className = "col";
  el.innerHTML = `
    <div class="col-head">
      <span class="name"><span>${esc(node.name)}</span></span>
      <span class="count">${node.kids === null ? "" : kids.length}</span>
      <button class="rf" tabindex="-1" title="Re-read this folder (F5)"
              aria-label="Refresh ${esc(node.name)}">⟳</button>
    </div>
    <div class="col-body"></div>
    <div class="spine-label" title="${esc(node.name)} — click to unfold">
      <span class="dot"></span>
      <span class="txt">${esc(node.name)}</span>
    </div>`;

  const body = el.querySelector(".col-body");
  if (node.kids === null) {
    body.innerHTML =
      `<div class="col-note"><span class="spinner"></span>Reading…</div>`;
  } else if (node.denied) {
    body.innerHTML = `<div class="col-note">⚠ ${esc(node.denied)}</div>`;
  } else if (!kids.length) {
    body.innerHTML = `<div class="col-note">Empty</div>`;
  }
  /* a folded column hides its rows, so the click lands on the column itself —
     that is what makes the advertised "click a spine to unfold" work */
  el.onclick = () => {
    if (el.classList.contains("spine")) actions.unfoldTo(+el.dataset.i);
  };
  /* Read the index off the element for the same reason a row does: the node
     keeps its DOM across re-renders, and only render time knows its column.
     stopPropagation, or a ⟳ on a folded spine would unfold it instead. */
  el.querySelector(".rf").onclick = (e) => {
    e.stopPropagation();
    actions.refreshColumn(+el.dataset.i);
  };

  const virtual = kids.length >= VIRTUAL_ROWS;
  const ROW_STEP = rowStep();
  const layer = virtual
    ? Object.assign(document.createElement("div"), { className: "row-layer" })
    : body;
  if (virtual) {
    layer.style.height = `${kids.length * ROW_STEP}px`;
    body.appendChild(layer);
  }
  const rows = new Array(kids.length);
  const live = new Set(); /* indices of the virtual rows now in the DOM */
  const makeRow = (ri) => {
    if (rows[ri]) return rows[ri];
    const k = kids[ri];
    const [stem, ext] = splitName(k.name);
    const row = document.createElement("div");
    row.className = "row" + (k.name.startsWith(".") ? " dotfile" : "");
    row.title = k.name; /* the full name is always one hover away */
    row.setAttribute("aria-label", k.name);
    row.setAttribute("aria-haspopup", "menu");
    row.innerHTML = iconHTML(k) +
      `<span class="label"><span class="stem">${
        esc(stem)
      }</span><span class="dim">${esc(ext)}</span></span>` +
      (k.dir ? `<span class="chev">›</span>` : "");
    /* read the index off the element: the same node keeps its DOM across
       re-renders, and its column position is only known at render time */
    row.onclick = () => {
      if (suppressClick) {
        suppressClick = false;
        return;
      }
      actions.choose(+el.dataset.i, k);
    };
    row.onpointerdown = (event) => {
      if (!touchUI() || (event.pointerType === "mouse" && event.button !== 0)) {
        return;
      }
      clearTimeout(longPressTimer);
      longPressPointer = event.pointerId;
      longPressTimer = setTimeout(() => {
        openRowMenu(k, node, row, event);
        suppressClick = true;
      }, LONG_PRESS_MS);
    };
    /* The timer is shared by every row, and a fold glide moving rows under a
       resting mouse fires its pointerleave on them: that must not end a
       finger's press elsewhere. */
    row.onpointerup = row.onpointercancel = row.onpointerleave = (event) => {
      if (event.pointerId === longPressPointer) clearTimeout(longPressTimer);
    };
    row.oncontextmenu = (event) => {
      event.preventDefault();
      const held = suppressClick;
      openRowMenu(k, node, row, event);
      suppressClick = held;
    };
    if (virtual) {
      row.style.top = `${ri * ROW_STEP}px`;
      live.add(ri);
      /* An evicted row comes back without the classes render() gave it. */
      const ci = +el.dataset.i, chosen = k.name === sel[ci];
      row.classList.toggle("sel", chosen);
      row.classList.toggle("cursor", chosen && ci === focusCol);
    }
    layer.appendChild(row);
    rows[ri] = row;
    return row;
  };
  /* Only a scroll evicts: Home/End and deep links build a far row and click
     it before revealRow scrolls to it, and render() runs in between. */
  const paintRange = (evict) => {
    if (!virtual) return;
    const first = Math.max(0, Math.floor(body.scrollTop / ROW_STEP) - 10);
    const last = Math.min(
      kids.length,
      Math.ceil((body.scrollTop + body.clientHeight) / ROW_STEP) + 10,
    );
    if (evict) {
      for (const i of live) {
        if (i >= first && i < last) continue;
        rows[i].remove();
        delete rows[i]; /* a hole, which forEach and flatMap skip */
        live.delete(i);
      }
    }
    for (let i = first; i < last; i++) makeRow(i);
  };
  if (!virtual) kids.forEach((_, i) => makeRow(i));
  body.onscroll = () => {
    paintRange(true);
    paintTrail();
  };

  return {
    el,
    body,
    kids,
    rows,
    ensureRow: makeRow,
    paintRange,
    kidsRef: node.kids,
    metaRef: !!node.metaDone,
    dot: el.querySelector(".dot"),
  };
}

export function columnFor(node) {
  let c = colCache.get(node);
  /* Two ways this DOM stops being the column: the directory was re-read, or a
     metadata sweep landed and re-ordered the rows under it. Same test, one
     field along. */
  if (c && (c.kidsRef !== node.kids || c.metaRef !== !!node.metaDone)) c = null;
  if (!c) c = buildCol(node);
  colCache.delete(node); /* re-insert = most recently used */
  colCache.set(node, c);
  for (const k of colCache.keys()) {
    if (colCache.size <= CACHE_MAX) break;
    if (!path.includes(k)) colCache.delete(k);
  }
  return c;
}

export function render(keepScroll) {
  if (!path.length) return;
  const fullscreenFocused = document.activeElement?.id === "pv-fullscreen";
  const sig =
    `${state.dotfiles}|${root.dataset.density}|${root.dataset.theme}` +
    `|${state.sort.key}|${state.sort.desc}`;
  if (sig !== cacheSig) {
    colCache.clear();
    cacheSig = sig;
  }

  const w = folderWidth();
  setState({ widths: [] });
  const cols = path.map((node, i) => {
    /* Before columnFor, so a directory that needs no fetch — the server build,
       or one a preview has already read — is built once in the sorted order
       rather than built and rebuilt. */
    sweepMeta(node);
    const c = columnFor(node);
    const selectedRow = rowIndex(node, sel[i]);
    widths.push(w);

    /* `sorting` goes in the class string rather than on classList, because this
       write replaces the whole attribute and would drop it a frame later. */
    set(
      c.el,
      "className",
      "col " +
        (i < focusCol ? "ancestor" : i > focusCol ? "descendant" : "focus") +
        (node.metaLoading ? " sorting" : ""),
    );
    set(
      c.el.dataset,
      "depth",
      String(Math.min(MAX_DEPTH, Math.max(0, focusCol - i))),
    );
    set(c.el.dataset, "i", String(i));
    set(c.el.style, "width", w + "px");

    if (c.dotFor !== sel[i]) {
      /* spine icon of the chosen child */
      const chosen = c.kids.find((k) => k.name === sel[i]);
      c.dot.innerHTML = chosen ? iconHTML(chosen) : "";
      c.dotFor = sel[i];
    }
    c.rows.forEach((row, ri) => {
      if (!c.kids[ri].dir) row.querySelector(".chev")?.remove();
      row.classList.toggle("sel", c.kids[ri].name === sel[i]);
      row.classList.toggle("cursor", i === focusCol && selectedRow === ri);
    });
    return c;
  });

  /* Reconcile instead of replaceChildren: re-inserting an element detaches it,
     which throws away the style and layout of every row underneath it. Columns
     that keep their slot must not be touched at all. */
  const want = [...cols.map((c) => c.el), renderPreview()];
  want.forEach((el, i) => {
    if (strip.childNodes[i] !== el) {
      strip.insertBefore(el, strip.childNodes[i] || null);
    }
  });
  while (strip.childNodes.length > want.length) strip.lastChild.remove();
  if (previewNode()) setupPreviewActions(previewNode());
  if (fullscreenFocused) {
    document.getElementById("pv-fullscreen")?.focus({ preventScroll: true });
  }
  for (const c of cols) {
    c.paintRange();
    c.el.classList.toggle(
      "scrollable-down",
      c.body.scrollHeight > c.body.clientHeight + SCROLL_HINT_PADDING,
    );
  }
  actions.renderCrumbs();
  sortSay(sortStatus());
  layout(keepScroll);
  syncURL();
}

let rawObjectURL = null;

function revokeRawURL() {
  if (rawObjectURL) URL.revokeObjectURL(rawObjectURL);
  rawObjectURL = null;
}

function renderPreview() {
  const n = previewNode();
  const selected = selectedNode();
  const editing = editingPreview(n);
  if (editing) return editing;
  const pv = document.createElement("div");
  pv.id = "preview";
  pv.tabIndex = 0;
  pv.setAttribute("aria-label", "File preview");
  PREVIEW.revoke?.();
  revokeRawURL();
  if (!n && !selected) {
    pv.innerHTML = `<div class="pv-empty"><div class="glyph">◫</div>
                    <div>Select a file to preview</div></div>`;
    return pv;
  }
  const target = n || selected;
  const [stem, ext] = splitName(target.name);
  pv.innerHTML = `
    <div class="col-head pv-head"><span class="name"><span>${
    esc(target.name)
  }</span><span id="pv-modified" hidden role="img" aria-label="Modified" title="Unsaved changes">●</span></span>
      <span class="pv-actions">
        <a id="pv-raw" class="pv-action" hidden title="View raw file">Raw</a>
        <button id="pv-view" class="pv-action" type="button"></button>
        <button id="pv-delete" class="pv-action" type="button"
                title="Delete selected item">Delete</button>
        <button id="pv-fullscreen" class="pv-action" type="button" aria-pressed="${pvFullscreen}"
                title="Toggle fullscreen preview">Fullscreen</button>
      </span>
    </div>
    <div class="pv-body">
      ${
    target.section ? "" : `<div class="pv-hero">
        ${iconHTML(target)}
        <div><h2>${esc(stem)}<span style="color:var(--ink-3)">${
      esc(ext)
    }</span></h2>
             <div class="sub" id="pv-sub">reading…</div></div>
        <button id="pv-edit" hidden>Edit</button>
      </div>`
  }
      <div id="pv-content" class="pv-content"></div>
    </div>`;
  if (n) fillPreview(n);
  pv.classList.toggle("pv-is-fullscreen", pvFullscreen);
  return pv;
}

function applyFullscreen(value) {
  setState({ pvFullscreen: value });
  root.classList.toggle("pv-fullscreen", value);
  const full = document.getElementById("pv-fullscreen");
  if (full) {
    full.setAttribute("aria-pressed", value);
    full.textContent = value ? "Exit fullscreen" : "Fullscreen";
    full.title = full.textContent;
  }
}

export async function togglePreviewFullscreen() {
  if (pvFullscreen) return leaveFullscreen();
  if (matchMedia("(pointer: coarse)").matches) {
    history.pushState({ ...history.state, filemillFullscreen: true }, "");
  }
  applyFullscreen(true);
  // Resize rebuilds the preview, so fullscreen must use the stable root.
  if (root.requestFullscreen) {
    try {
      await root.requestFullscreen();
    } catch (_) {
      /* Keep the layout fallback when browser fullscreen is unavailable. */
    }
  }
}

// Touch browsers need a history step for both native and layout fullscreen.
applyFullscreen(!!history.state?.filemillFullscreen);

export function leaveFullscreen() {
  if (history.state?.filemillFullscreen) {
    history.back();
    return;
  }
  applyFullscreen(false);
  if (document.fullscreenElement) document.exitFullscreen();
}

addEventListener("popstate", (event) => {
  if (!pvFullscreen && !event.state?.filemillFullscreen) return;
  const loc = ROUTER?.read();
  // Bypass routing only when the selected file and preview mode are unchanged.
  if (
    loc && (!loc.root || loc.root === path[0]?.name) &&
    JSON.stringify(loc.path) === JSON.stringify(currentPath()) &&
    (loc.view || "render") === (root.dataset.filemill || "render")
  ) event.stopImmediatePropagation();
  applyFullscreen(!!event.state?.filemillFullscreen);
  if (!pvFullscreen && document.fullscreenElement) document.exitFullscreen();
}, { capture: true });

document.addEventListener("fullscreenchange", () => {
  if (!document.fullscreenElement && pvFullscreen) leaveFullscreen();
});

function previewView() {
  const view = document.documentElement.dataset.filemill || "render";
  return view === "highlight"
    ? "highlight"
    : view === "render"
    ? "render"
    : "raw";
}

function setPreviewView(view) {
  document.documentElement.dataset.filemill = view;
  ROUTER?.write({ root: path[0]?.name, path: currentPath(), view }, false);
  const n = previewNode();
  if (n) {
    fillPreview(n);
    setupPreviewActions(n);
  }
}

function setupPreviewActions(n) {
  const view = previewView();
  const toggle = document.getElementById("pv-view");
  const name = String(n.name || "");
  const fileKind = n.fileKind || classifyFile(name, n);
  const markdown = fileKind.preview === "md" || fileKind.preview === "markdown";
  const applicable = fileKind.preview !== "text";
  if (toggle) {
    toggle.hidden = !markdown && !applicable;
    toggle.textContent = view === "render" ? "Source" : "Rendered";
    toggle.title = view === "render"
      ? "View highlighted source"
      : "View rendered preview";
    toggle.setAttribute("aria-label", toggle.title);
    toggle.onclick = () => {
      setPreviewView(view === "render" ? "highlight" : "render");
    };
  }
  const full = document.getElementById("pv-fullscreen");
  if (full) {
    full.onclick = togglePreviewFullscreen;
    full.textContent = pvFullscreen ? "Exit fullscreen" : "Fullscreen";
  }
  const del = document.getElementById("pv-delete");
  if (del) {
    del.hidden = !FS.remove || !!n.vpath;
    const parent = path[path.length - 1];
    del.disabled = isRemoving(n, parent);
    del.onclick = () => deleteEntry(n, parent, del);
  }
}

/* Metadata and contents arrive after the layout is already on screen; the token
   makes sure a slow read for a file you have since navigated away from is
   dropped. That guard lives here, not in the provider, so a provider is free to
   be as slow as it needs to be — a server round-trip, a WASM highlighter. */
let previewFoldEvents;

async function fillPreview(n) {
  closeEditor();
  const token = nextPvToken();
  await FS.loadMeta(n);
  if (token !== pvToken) return;
  const m = n.meta || {};
  const sub = document.getElementById("pv-sub");
  if (!sub && !n.section) return;
  if (m.error) {
    if (sub) sub.textContent = "unreadable";
    return;
  }
  const raw = document.getElementById("pv-raw");
  if (raw) {
    try {
      let url = FS.rawURL?.(n);
      if (!FS.rawURL) {
        const blob = await FS.blob(n);
        if (token !== pvToken) return;
        revokeRawURL();
        if (blob) {
          rawObjectURL = URL.createObjectURL(
            blob.type ? blob : blob.slice(0, blob.size, "text/plain"),
          );
          url = rawObjectURL;
        }
        raw.target = "_blank";
        raw.rel = "noopener noreferrer";
      }
      raw.hidden = !url;
      if (url) raw.href = url;
    } catch (_) {
      raw.hidden = true;
    }
  }
  /* Not everything a column can hold is a file. A row inside a database has no
     size and no mtime, and inventing them prints "0 B · 1 Jan 1970" — so leave
     the sub-line empty and go straight to the body. */
  if (sub) {
    sub.textContent = m.size == null
      ? ""
      : `${fmtSize(m.size)} · modified ${fmtDate(m.mod)}`;
  }

  let html = null;
  try {
    html = await PREVIEW.render(n);
  } catch (err) {
    html = `<p class="pv-err">Preview failed: ${
      esc(String(err.message || err))
    }</p>`;
  }
  if (token !== pvToken) return;
  const host = document.getElementById("pv-content");
  if (!host) return;
  host.innerHTML = html ?? `<p>No inline preview for this file type.</p>`;
  previewFoldEvents?.abort();
  previewFoldEvents = new AbortController();
  const recordFold = (details) => {
    if (
      token !== pvToken || !details.isConnected || !details.dataset.jsonPath
    ) return;
    if (details.dataset.jsonOpen === String(details.open)) return;
    details.dataset.jsonOpen = String(details.open);
    jsonCollapse.record(
      n.jsonRoot || n,
      JSON.parse(details.dataset.jsonPath),
      n.jsonPath?.length || 0,
      details.open,
    );
  };
  // Handle activation synchronously: native toggle events can arrive after navigation.
  host.onclick = (event) => {
    const summary = event.target.closest("summary");
    const details = summary?.parentElement;
    if (!details?.dataset.jsonPath || event.defaultPrevented) return;
    event.preventDefault();
    details.open = !details.open;
    recordFold(details);
  };
  host.addEventListener("toggle", (event) => recordFold(event.target), {
    capture: true,
    signal: previewFoldEvents.signal,
  });
  hlFences(host);
  const btn = document.getElementById("pv-edit");
  if (btn) {
    btn.hidden = true;
    if (
      await editableText(n) !== null && token === pvToken && btn.isConnected
    ) {
      btn.hidden = false;
      enableTaskToggles(
        host,
        n,
        () => token === pvToken && host.isConnected,
        (message) => actions.saySt("st-refresh", message, false),
      );
      btn.onclick = () =>
        openEditor(
          n,
          () => token === pvToken && btn.isConnected,
          () => fillPreview(n),
        );
    }
  }
  paintTrail();
}
