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
const set = (obj, key, value) => { if (obj[key] !== value) obj[key] = value; };
const setVar = (el, name, value) => {
  if (el.style.getPropertyValue(name) !== value) el.style.setProperty(name, value);
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
    body.innerHTML = `<div class="col-note"><span class="spinner"></span>Reading…</div>`;
  } else if (node.denied) {
    body.innerHTML = `<div class="col-note">⚠ ${esc(node.denied)}</div>`;
  } else if (!kids.length) {
    body.innerHTML = `<div class="col-note">Empty</div>`;
  }
  /* a folded column hides its rows, so the click lands on the column itself —
     that is what makes the advertised "click a spine to unfold" work */
  el.onclick = () => { if (el.classList.contains("spine")) unfoldTo(+el.dataset.i); };
  /* Read the index off the element for the same reason a row does: the node
     keeps its DOM across re-renders, and only render time knows its column.
     stopPropagation, or a ⟳ on a folded spine would unfold it instead. */
  el.querySelector(".rf").onclick = e => {
    e.stopPropagation();
    refreshColumn(+el.dataset.i);
  };

  const rows = kids.map((k, ri) => {
    const [stem, ext] = splitName(k.name);
    const row = document.createElement("div");
    row.className = "row" + (k.name.startsWith(".") ? " dotfile" : "");
    row.title = k.name;   /* the full name is always one hover away */
    row.innerHTML = iconHTML(k)
      + `<span class="label">${esc(stem)}<span class="dim">${esc(ext)}</span></span>`
      + (k.dir ? `<span class="chev">›</span>` : "");
    /* read the index off the element: the same node keeps its DOM across
       re-renders, and its column position is only known at render time */
    row.onclick = () => choose(+el.dataset.i, k, ri);
    body.appendChild(row);
    return row;
  });
  body.onscroll = paintTrail;

  return { el, body, kids, rows, kidsRef: node.kids, metaRef: !!node.metaDone,
           dot: el.querySelector(".dot"), width: measure(node) };
}

function columnFor(node) {
  let c = colCache.get(node);
  /* Two ways this DOM stops being the column: the directory was re-read, or a
     metadata sweep landed and re-ordered the rows under it. Same test, one
     field along. */
  if (c && (c.kidsRef !== node.kids || c.metaRef !== !!node.metaDone)) c = null;
  if (!c) c = buildCol(node);
  colCache.delete(node);                            /* re-insert = most recently used */
  colCache.set(node, c);
  for (const k of colCache.keys()) {
    if (colCache.size <= CACHE_MAX) break;
    if (!path.includes(k)) colCache.delete(k);
  }
  return c;
}

function render(keepScroll) {
  if (!path.length) return;
  const sig = `${state.dotfiles}|${root.dataset.density}|${root.dataset.theme}` +
              `|${state.sort.key}|${state.sort.desc}`;
  if (sig !== cacheSig) { colCache.clear(); cacheSig = sig; }

  widths = [];
  const cols = path.map((node, i) => {
    /* Before columnFor, so a directory that needs no fetch — the server build,
       or one a preview has already read — is built once in the sorted order
       rather than built and rebuilt. */
    sweepMeta(node);
    const c = columnFor(node);
    widths.push(c.width);

    /* `sorting` goes in the class string rather than on classList, because this
       write replaces the whole attribute and would drop it a frame later. */
    set(c.el, "className", "col " +
      (i < focusCol ? "ancestor" : i > focusCol ? "descendant" : "focus") +
      (node.metaLoading ? " sorting" : ""));
    set(c.el.dataset, "depth", String(Math.min(5, Math.max(0, focusCol - i))));
    set(c.el.dataset, "i", String(i));
    set(c.el.style, "width", c.width + "px");

    if (c.dotFor !== sel[i]) {                 /* spine icon of the chosen child */
      const chosen = c.kids.find(k => k.name === sel[i]);
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
  const want = [...cols.map(c => c.el), renderPreview()];
  want.forEach((el, i) => {
    if (strip.childNodes[i] !== el) strip.insertBefore(el, strip.childNodes[i] || null);
  });
  while (strip.childNodes.length > want.length) strip.lastChild.remove();
  for (const c of cols)
    c.el.classList.toggle("scrollable-down", c.body.scrollHeight > c.body.clientHeight + 4);
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
  pv.innerHTML = `
    <div class="col-head"><span class="name"><span>${esc(n.name)}</span></span></div>
    <div class="pv-body">
      <div class="pv-hero">
        ${iconHTML(n)}
        <div><h2>${esc(stem)}<span style="color:var(--ink-3)">${esc(ext)}</span></h2>
             <div class="sub" id="pv-sub">reading…</div></div>
      </div>
      <div id="pv-content"></div>
      <dl class="meta">
        <dt>Where</dt><dd>${esc(path.map(p => p.name).join(" / "))}</dd>
        <dt>Size</dt><dd id="pv-size">—</dd>
        <dt>Modified</dt><dd id="pv-mod">—</dd>
      </dl>
    </div>`;
  fillPreview(n);
  return pv;
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
  const sub  = document.getElementById("pv-sub");
  if (!sub) return;
  if (m.error) { sub.textContent = "unreadable"; return; }
  /* Not everything a column can hold is a file. A row inside a database has no
     size and no mtime, and inventing them prints "0 B · 1 Jan 1970" — so leave
     the fields at their dashes and go straight to the body. */
  if (m.size == null) {
    sub.textContent = "";
  } else {
    sub.textContent = `${fmtSize(m.size)} · modified ${fmtDate(m.mod)}`;
    document.getElementById("pv-size").textContent = `${fmtSize(m.size)} (${m.size.toLocaleString()} bytes)`;
    document.getElementById("pv-mod").textContent  = fmtDate(m.mod);
  }

  let html = null;
  try {
    html = await PREVIEW.render(n);
  } catch (err) {
    html = `<p class="pv-err">Preview failed: ${esc(String(err.message || err))}</p>`;
  }
  if (token !== pvToken) return;
  const host = document.getElementById("pv-content");
  if (!host) return;
  host.innerHTML = html ?? `<p>No inline preview for this file type.</p>`;
  paintTrail();
}
