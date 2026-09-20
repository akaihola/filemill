/* ═══════════════════════════════════════════════════════════════════════════
   Render
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  closeEditor,
  editableText,
  editingPreview,
  openEditor,
} from "../editor/editor.js";
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
const ROW_STEP = 23; // 21px row plus its 1px vertical margins.
const LONG_PRESS_MS = 500;
const touchUI = () =>
  matchMedia("(pointer: coarse)").matches || navigator.maxTouchPoints > 0;

let longPressTimer;
let suppressClick = false;

let menuRow, menuFocus, updateMenuDelete;
const removing = new WeakMap();
const entryPath = (node, parent) =>
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

async function deleteEntry(node, parent, button) {
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
  const rel = entryPath(node, parent);
  const absolute = node.abs || "/" + rel;
  const menu = document.getElementById("row-menu");
  menu.innerHTML = [
    ["Copy name", node.name],
    ["Copy relative path", rel],
    ["Copy absolute path", absolute],
  ].map(([label, text]) =>
    `<button type="button" role="menuitem" data-copy="${
      esc(text)
    }">${label}</button>`
  ).join("");
  menu.querySelectorAll("button").forEach((button) =>
    button.onclick = async () => {
      suppressClick = false;
      try {
        await navigator.clipboard.writeText(button.dataset.copy);
        closeRowMenu();
      } catch (err) {
        actions.saySt(
          "st-copy",
          `clipboard refused (${err.name || "error"})`,
          false,
        );
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
  if (node.pages > 1) {
    const pager = document.createElement("div");
    pager.className = "pager";
    pager.innerHTML =
      `<button type="button" aria-label="Previous page">‹</button>
      <span>Page ${node.page} of ${node.pages}</span>
      <button type="button" aria-label="Next page">›</button>`;
    const [prev, next] = pager.querySelectorAll("button");
    prev.disabled = node.page === 1;
    next.disabled = node.page === node.pages;
    prev.onclick = (e) => {
      e.stopPropagation();
      FS.loadPage(node, node.page - 1);
    };
    next.onclick = (e) => {
      e.stopPropagation();
      FS.loadPage(node, node.page + 1);
    };
    el.appendChild(pager);
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
  const layer = virtual
    ? Object.assign(document.createElement("div"), { className: "row-layer" })
    : body;
  if (virtual) {
    layer.style.height = `${kids.length * ROW_STEP}px`;
    body.appendChild(layer);
  }
  const rows = new Array(kids.length);
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
      longPressTimer = setTimeout(() => {
        openRowMenu(k, node, row, event);
        suppressClick = true;
      }, LONG_PRESS_MS);
    };
    row.onpointerup = row.onpointercancel = row.onpointerleave = () =>
      clearTimeout(longPressTimer);
    row.oncontextmenu = (event) => {
      event.preventDefault();
      const held = suppressClick;
      openRowMenu(k, node, row, event);
      suppressClick = held;
    };
    if (virtual) {
      row.style.top = `${ri * ROW_STEP}px`;
      layer.appendChild(row);
    } else layer.appendChild(row);
    rows[ri] = row;
    return row;
  };
  const paintRange = () => {
    if (!virtual) return;
    const first = Math.max(0, Math.floor(body.scrollTop / ROW_STEP) - 10);
    const last = Math.min(
      kids.length,
      Math.ceil((body.scrollTop + body.clientHeight) / ROW_STEP) + 10,
    );
    for (let i = first; i < last; i++) makeRow(i);
  };
  if (!virtual) kids.forEach((_, i) => makeRow(i));
  body.onscroll = () => {
    paintRange();
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
  /* ?layout=no-columns asks for the representation alone. The server puts
     the value on <html>; a document then fills the pane and a directory shows
     only its own listing. The static build never sets it. */
  if (root.dataset.layout === "no-columns") {
    root.classList.toggle("pv-only", !!previewNode());
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
  if (!n && !selected) {
    pv.innerHTML = `<div class="pv-empty"><div class="glyph">◫</div>
                    <div>Select a file to preview</div></div>`;
    return pv;
  }
  const target = n || selected;
  const [stem, ext] = splitName(target.name);
  const rawPath = "/" + currentPath().map(encodeURIComponent).join("/") +
    "?filemill=raw";
  pv.innerHTML = `
    <div class="col-head pv-head"><span class="name"><span>${
    esc(target.name)
  }</span><span id="pv-modified" hidden role="img" aria-label="Modified" title="Unsaved changes">●</span></span>
      <span class="pv-actions">
        ${
    ROUTER
      ? `<a id="pv-raw" class="pv-action" href="${rawPath}" title="View raw file">Raw</a>`
      : ""
  }
        <span id="pv-md-views" hidden role="group" aria-label="Markdown view">
          <button id="pv-md-rendered" class="pv-action" type="button">Rendered</button>
          <button id="pv-md-raw" class="pv-action" type="button">Raw</button>
        </span>
        <span id="pv-vtt-views" hidden role="group" aria-label="WebVTT view">
          <button id="pv-vtt-transcript" class="pv-action" type="button">Transcript</button>
          <button id="pv-vtt-raw" class="pv-action" type="button">Raw</button>
        </span>
        <button id="pv-view" class="pv-action" type="button"></button>
        <button id="pv-delete" class="pv-action" type="button"
                title="Delete selected item">Delete</button>
        <button id="pv-fullscreen" class="pv-action" type="button" aria-pressed="${pvFullscreen}"
                title="Toggle fullscreen preview">Fullscreen</button>
      </span>
    </div>
    <div class="pv-body">
      <div class="pv-hero">
        ${iconHTML(target)}
        <div><h2>${esc(stem)}<span style="color:var(--ink-3)">${
    esc(ext)
  }</span></h2>
             <div class="sub" id="pv-sub">reading…</div></div>
        <button id="pv-edit" hidden>Edit</button>
      </div>
      <div id="pv-content" class="pv-content"></div>
    </div>`;
  if (n) fillPreview(n);
  pv.classList.toggle("pv-is-fullscreen", pvFullscreen);
  return pv;
}

let markdownView = "rendered";
let vttView = "transcript";

export function resetPreviewModes() {
  markdownView = "rendered";
  vttView = "transcript";
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

// Touch browsers need a history step for both native and layout fullscreen.
let fullscreenURL = null;

function leaveFullscreen() {
  if (history.state?.filemillFullscreen) {
    history.back();
    return;
  }
  applyFullscreen(false);
  if (document.fullscreenElement) document.exitFullscreen();
}

addEventListener("popstate", (event) => {
  if (
    location.href !== fullscreenURL ||
    (!pvFullscreen && !event.state?.filemillFullscreen)
  ) return;
  // The file did not change. Do not let the path router rebuild its preview.
  event.stopImmediatePropagation();
  applyFullscreen(!!event.state?.filemillFullscreen);
  if (!pvFullscreen && document.fullscreenElement) document.exitFullscreen();
}, { capture: true });

document.addEventListener("fullscreenchange", () => {
  if (!document.fullscreenElement && pvFullscreen) leaveFullscreen();
});

async function rawMarkdown(node) {
  try {
    const blob = await FS.blob(node);
    return blob ? `<pre class="pv-text">${esc(await blob.text())}</pre>` : null;
  } catch (_) {
    return null;
  }
}

function previewView() {
  const view = new URL(location.href).searchParams.get("filemill") ||
    document.documentElement.dataset.filemill || "raw";
  return view === "highlight"
    ? "highlight"
    : view === "render"
    ? "render"
    : "raw";
}

function setPreviewView(view) {
  if (!ROUTER) return;
  document.documentElement.dataset.filemill = view;
  ROUTER.write({ path: currentPath(), view }, false);
  const n = previewNode();
  if (n) {
    fillPreview(n);
    setupPreviewActions(n);
  }
}

function setupPreviewActions(n) {
  const view = previewView();
  const toggle = document.getElementById("pv-view");
  const mdViews = document.getElementById("pv-md-views");
  const vttViews = document.getElementById("pv-vtt-views");
  const name = String(n.name || "");
  const fileKind = n.fileKind || classifyFile(name, n);
  const markdown = fileKind.preview === "md" || fileKind.preview === "markdown";
  const vtt = (n.fileKind || classifyFile(n.name, n)).preview === "vtt";
  const applicable = fileKind.preview !== "text";
  if (mdViews) {
    mdViews.hidden = !markdown;
    for (
      const [id, mode, label] of [
        ["pv-md-rendered", "rendered", "View rendered Markdown"],
        ["pv-md-raw", "raw", "View raw Markdown source"],
      ]
    ) {
      const button = document.getElementById(id);
      if (!button) continue;
      button.setAttribute("aria-pressed", String(markdownView === mode));
      button.setAttribute("aria-label", label);
      button.title = label;
      button.onclick = () => {
        if (markdownView === mode) return;
        markdownView = mode;
        fillPreview(n);
        setupPreviewActions(n);
      };
    }
  }
  if (vttViews) {
    vttViews.hidden = !vtt || view === "highlight";
    for (
      const [id, mode, label] of [
        ["pv-vtt-transcript", "transcript", "View WebVTT transcript"],
        ["pv-vtt-raw", "raw", "View raw WebVTT source"],
      ]
    ) {
      const button = document.getElementById(id);
      if (!button) continue;
      button.setAttribute("aria-pressed", String(vttView === mode));
      button.setAttribute("aria-label", label);
      button.title = label;
      button.onclick = () => {
        if (vttView === mode) return;
        vttView = mode;
        fillPreview({ ...n, previewFormat: mode });
        setupPreviewActions(n);
      };
    }
  }
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
    full.onclick = async () => {
      if (pvFullscreen) {
        leaveFullscreen();
        return;
      }
      if (matchMedia("(pointer: coarse)").matches) {
        fullscreenURL = location.href;
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
    };
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
  if (!sub) return;
  if (m.error) {
    sub.textContent = "unreadable";
    return;
  }
  /* Not everything a column can hold is a file. A row inside a database has no
     size and no mtime, and inventing them prints "0 B · 1 Jan 1970" — so leave
     the sub-line empty and go straight to the body. */
  if (m.size == null) {
    sub.textContent = "";
  } else {
    sub.textContent = `${fmtSize(m.size)} · modified ${fmtDate(m.mod)}`;
  }

  let html = null;
  try {
    html = ["md", "markdown"].includes(
        (n.fileKind || classifyFile(n.name, n)).preview,
      ) && markdownView === "raw"
      ? (await rawMarkdown(n) || await PREVIEW.render(n))
      : (n.fileKind || classifyFile(n.name, n)).preview === "vtt" &&
          previewView() !== "highlight"
      ? await PREVIEW.render({ ...n, previewFormat: vttView })
      : await PREVIEW.render(n);
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
