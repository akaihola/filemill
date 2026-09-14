/* ═══════════════════════════════════════════════════════════════════════════
   Render
   ═══════════════════════════════════════════════════════════════════════════ */
/* Building a column is O(entries), and real directories hold thousands of them
   — far too expensive to redo on every arrow key. A column's DOM is therefore
   built once per (node, entry list) and cached; a re-render only re-applies the
   state that actually changed: depth, selection, cursor, width.
   Anything that alters how a row *looks* (dotfile filter, density, theme icon
   colours) is part of the signature and drops the whole cache. */
const colCache = new Map();
let cacheSig = null;
const CACHE_MAX = 24;

/* Writing the value a property already holds still dirties it — and a width or
   custom-property write on a column relays out every row inside it. Guard the
   writes and a re-render of an unchanged column costs nothing. */
const set = (obj, key, value) => {
  if (obj[key] !== value) obj[key] = value;
};
const setVar = (el, name, value) => {
  if (el.style.getPropertyValue(name) !== value) {
    el.style.setProperty(name, value);
  }
};

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
    if (el.classList.contains("spine")) unfoldTo(+el.dataset.i);
  };
  /* Read the index off the element for the same reason a row does: the node
     keeps its DOM across re-renders, and only render time knows its column.
     stopPropagation, or a ⟳ on a folded spine would unfold it instead. */
  el.querySelector(".rf").onclick = (e) => {
    e.stopPropagation();
    refreshColumn(+el.dataset.i);
  };

  const rows = kids.map((k, ri) => {
    const [stem, ext] = splitName(k.name);
    const row = document.createElement("div");
    row.className = "row" + (k.name.startsWith(".") ? " dotfile" : "");
    row.title = k.name; /* the full name is always one hover away */
    row.setAttribute("aria-label", k.name);
    row.innerHTML = iconHTML(k) +
      `<span class="label"><span class="stem">${
        esc(stem)
      }</span><span class="dim">${esc(ext)}</span></span>` +
      (k.dir ? `<span class="chev">›</span>` : "");
    /* read the index off the element: the same node keeps its DOM across
       re-renders, and its column position is only known at render time */
    row.onclick = () => choose(+el.dataset.i, k, ri);
    body.appendChild(row);
    return row;
  });
  body.onscroll = paintTrail;

  return {
    el,
    body,
    kids,
    rows,
    kidsRef: node.kids,
    metaRef: !!node.metaDone,
    dot: el.querySelector(".dot"),
    width: measure(node),
  };
}

function columnFor(node) {
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

function render(keepScroll) {
  if (!path.length) return;
  const sig =
    `${state.dotfiles}|${root.dataset.density}|${root.dataset.theme}` +
    `|${state.sort.key}|${state.sort.desc}`;
  if (sig !== cacheSig) {
    colCache.clear();
    cacheSig = sig;
  }

  widths = [];
  const cols = path.map((node, i) => {
    /* Before columnFor, so a directory that needs no fetch — the server build,
       or one a preview has already read — is built once in the sorted order
       rather than built and rebuilt. */
    sweepMeta(node);
    const had = colCache.get(node);
    const c = columnFor(node);
    /* A rebuilt column is the only place row indices can have moved: a sweep
       re-ordered it, the sort changed, dotfiles appeared, the read landed. The
       cursor is an index, so re-point it at the entry that is still selected
       here, or ↓ resumes from whatever slid into that number. Reading c.kids,
       which the build just produced, keeps this off the keystroke path — an
       unchanged column skips it entirely. */
    if (c !== had && sel[i] !== undefined) {
      const ri = c.kids.findIndex((k) => k.name === sel[i]);
      if (ri >= 0) cursor[i] = ri;
    }
    /* No column may be wider than two-thirds of the live finder. The fold cap keeps the
       touched column unfolded and applyScroll's pan slides it into view, but
       neither can show a full-width column on a narrow phone —
       the row would still lose its right edge. Clamped here rather than in
       measure() because columnFor caches the built column: a width measured
       against the old viewport would survive a rotation, while `widths` is
       rebuilt by every render, including the one `resize` fires.

       Measured against #finder, not #stage, because the stage is one render
       behind: its width is `--stage-w`, which layout() writes *after* this
       loop has already chosen the widths. Turning a phone from 568 px to 375
       therefore clamped this render against 568 — oversized columns on a 375 px
       screen, and the pan can only choose which edge to lose, so the tapped
       row sat 10 px past the right one until the next render healed it.
       #finder is `flex: 1` in the viewport, so it is the live number, and it
       is the one layout() reads to set --stage-w in the first place. */
    const w = Math.min(c.width, Math.floor(finder.clientWidth * 2 / 3));
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
    set(c.el.dataset, "depth", String(Math.min(5, Math.max(0, focusCol - i))));
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
      row.classList.toggle("cursor", i === focusCol && cursor[i] === ri);
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
  for (const c of cols) {
    c.el.classList.toggle(
      "scrollable-down",
      c.body.scrollHeight > c.body.clientHeight + 4,
    );
  }
  renderCrumbs();
  sortSay(sortStatus());
  layout(keepScroll);
  syncURL();
}

function renderPreview() {
  const n = previewNode();
  const pv = document.createElement("div");
  pv.id = "preview";
  PREVIEW.revoke?.();
  if (!n) {
    pv.innerHTML = `<div class="pv-empty"><div class="glyph">◫</div>
                    <div>Select a file to preview</div></div>`;
    return pv;
  }
  const [stem, ext] = splitName(n.name);
  const rawPath = "/" + currentPath().map(encodeURIComponent).join("/");
  pv.innerHTML = `
    <div class="col-head pv-head"><span class="name"><span>${
    esc(n.name)
  }</span></span>
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
        <button id="pv-view" class="pv-action" hidden type="button"></button>
        <button id="pv-fullscreen" class="pv-action" type="button" aria-pressed="${pvFullscreen}"
                title="Toggle fullscreen preview">Fullscreen</button>
      </span>
    </div>
    <div class="pv-body">
      <div class="pv-hero">
        ${iconHTML(n)}
        <div><h2>${esc(stem)}<span style="color:var(--ink-3)">${
    esc(ext)
  }</span></h2>
             <div class="sub" id="pv-sub">reading…</div></div>
        <button id="pv-edit" hidden>Edit</button>
      </div>
      <div id="pv-content" class="pv-content"></div>
    </div>`;
  fillPreview(n);
  pv.classList.toggle("pv-is-fullscreen", pvFullscreen);
  setupPreviewActions(n);
  return pv;
}

const RENDERED_RE = /\.(md|markdown|docx|pptx|html?|desktop)$/i;
const MARKDOWN_RE = /\.(md|markdown)$/i;
let markdownView = "rendered";

async function rawMarkdown(node) {
  try {
    const blob = await FS.blob(node);
    return blob ? `<pre class="pv-text">${esc(await blob.text())}</pre>` : null;
  } catch (_) {
    return null;
  }
}

function previewView() {
  const view = document.documentElement.dataset.filemill || "raw";
  return view === "highlight"
    ? "highlight"
    : view === "render"
    ? "render"
    : "raw";
}

function setPreviewView(view) {
  if (!ROUTER || !location.pathname) return;
  const url = new URL(location.href);
  url.searchParams.set("filemill", view);
  location.href = url.pathname + url.search + url.hash;
}

function setupPreviewActions(n) {
  const view = previewView();
  const toggle = document.getElementById("pv-view");
  const mdViews = document.getElementById("pv-md-views");
  const markdown = MARKDOWN_RE.test(n.name);
  const applicable = markdown || (!!ROUTER && RENDERED_RE.test(n.name));
  if (mdViews) {
    mdViews.hidden = !markdown;
    for (const [id, mode, label] of [
      ["pv-md-rendered", "rendered", "View rendered Markdown"],
      ["pv-md-raw", "raw", "View raw Markdown source"],
    ]) {
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
  if (toggle) {
    toggle.hidden = markdown || !applicable;
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
    full.onclick = () => {
      pvFullscreen = !pvFullscreen;
      root.classList.toggle("pv-fullscreen", pvFullscreen);
      full.setAttribute("aria-pressed", pvFullscreen);
      full.textContent = pvFullscreen ? "Exit fullscreen" : "Fullscreen";
      full.title = full.textContent;
    };
    full.textContent = pvFullscreen ? "Exit fullscreen" : "Fullscreen";
  }
}

/* Metadata and contents arrive after the layout is already on screen; the token
   makes sure a slow read for a file you have since navigated away from is
   dropped. That guard lives here, not in the provider, so a provider is free to
   be as slow as it needs to be — a server round-trip, a WASM highlighter. */
async function fillPreview(n) {
  const token = ++pvToken;
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
    html = MARKDOWN_RE.test(n.name) && markdownView === "raw"
      ? (await rawMarkdown(n) || await PREVIEW.render(n))
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
  hlFences(host);
  const btn = document.getElementById("pv-edit");
  if (btn) {
    btn.hidden = true;
    if (await editableText(n) !== null) {
      btn.hidden = false;
      btn.onclick = () => openEditor(n);
    }
  }
  paintTrail();
}

/* ── Edit mode ──────────────────────────────────────────────────────────────
   A plain textarea over FS.write — see ports.js. The gate mirrors the text
   preview in adapters/preview-local.js (same extensions, same cap), but it is
   core's own copy: a build picks its preview provider freely, and Edit has to
   work with any of them. Keep the two lists in step. */
const EDIT_MAX = 512 * 1024;
const EDIT_MAX_LINE = 10_000;
const NON_EDIT_RE =
  /\.(desktop|docx|pptx|pdf|html?|png|jpe?g|gif|webp|avif|bmp|ico|svg)$/i;

async function editableText(n) {
  if (
    !FS.write || n.dir || n.vpath || NON_EDIT_RE.test(n.name) ||
    (n.meta?.size ?? 0) > EDIT_MAX
  ) return null;
  const blob = await FS.blob(n);
  if (!blob || blob.size > EDIT_MAX) return null;
  try {
    const text = new TextDecoder("utf-8", { fatal: true }).decode(
      await blob.arrayBuffer(),
    );
    return !text.includes("\0") &&
        Math.max(...text.split(/\r?\n/).map((line) => line.length), 0) <=
          EDIT_MAX_LINE
      ? text
      : null;
  } catch (_) {
    return null;
  }
}

async function openEditor(n) {
  const token = pvToken;
  const blob = await FS.blob(n);
  if (token !== pvToken || !blob) return;
  /* Read again rather than lifting the text out of the pane: the preview is
     HTML by then, coloured and escaped, and un-escaping it back into source
     is a round trip that can only lose. Same bytes either way — EDIT_MAX and
     the provider's TEXT_MAX are the same 512 KB. */
  const text = await blob.text();
  const host = document.getElementById("pv-content");
  if (token !== pvToken || !host) return;
  document.getElementById("pv-edit").hidden = true;
  host.innerHTML = `
    <textarea id="pv-editor" spellcheck="false" aria-label="Edit ${
    esc(n.name)
  }"></textarea>
    <div class="pv-edit-bar">
      <button id="pv-save">Save</button>
      <button id="pv-cancel">Cancel</button>
      <span class="pv-err" id="pv-edit-err"></span>
    </div>`;
  const ta = document.getElementById("pv-editor");
  ta.value = text;
  ta.focus();
  ta.setSelectionRange(0, 0);
  ta.scrollTop = 0;
  document.getElementById("pv-cancel").onclick = () => fillPreview(n);
  document.getElementById("pv-save").onclick = async () => {
    try {
      await FS.write(n, ta.value);
    } catch (err) {
      const box = document.getElementById("pv-edit-err");
      if (box) box.textContent = String(err.message || err);
      return;
    }
    /* the pane may have moved on while the write was in flight */
    if (ta.isConnected) fillPreview(n);
  };
}
