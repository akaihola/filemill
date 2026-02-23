/* ════════════════════════════════════════════════════════════════
   HTML helpers
   ════════════════════════════════════════════════════════════════ */
function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Return an HTML string for `name` with the best match of `query`
 * wrapped in <mark>. Priority: prefix → substring → fuzzy.
 * Returns plain escaped name when query is empty or there is no match.
 */
function highlightLabel(name, query) {
  if (!query) return escapeHtml(name);
  const nameLower  = name.toLowerCase();
  const q          = query.toLowerCase();

  // 1. Prefix match
  if (nameLower.startsWith(q)) {
    return `<mark>${escapeHtml(name.slice(0, q.length))}</mark>${escapeHtml(name.slice(q.length))}`;
  }
  // 2. Substring match
  const si = nameLower.indexOf(q);
  if (si >= 0) {
    return `${escapeHtml(name.slice(0, si))}<mark>${escapeHtml(name.slice(si, si + q.length))}</mark>${escapeHtml(name.slice(si + q.length))}`;
  }
  // 3. Fuzzy — highlight individual matched chars
  let result = '', qi = 0;
  for (let i = 0; i < name.length; i++) {
    if (qi < q.length && name[i].toLowerCase() === q[qi]) {
      result += `<mark>${escapeHtml(name[i])}</mark>`;
      qi++;
    } else {
      result += escapeHtml(name[i]);
    }
  }
  if (qi === q.length) return result;
  return escapeHtml(name); // no match — plain text
}

/* ════════════════════════════════════════════════════════════════
   Render — Sidebar
   ════════════════════════════════════════════════════════════════ */
function renderSidebar() {
  const sb = document.getElementById('sidebar');
  let html = `<div class="sidebar-section-header">Favorites</div>`;
  SIDEBAR_ITEMS.forEach((item, idx) => {
    const isSel = idx === activeSidebarIdx;
    const isKbd = isSel && sidebarFocused;
    const cls   = 'sidebar-item' + (isSel ? ' selected' : '') + (isKbd ? ' kbd-focused' : '');
    html += `<div class="${cls}" data-sb-idx="${idx}">
      <span class="si-icon">${item.icon}</span>
      <span class="si-label">${escapeHtml(item.label)}</span>
    </div>`;
  });
  html += `<div class="sidebar-section-header">Tags</div>`;
  SIDEBAR_TAGS.forEach(t => {
    html += `<div class="sidebar-item" data-tag="${t.label}">
      <span class="si-icon"><span class="sidebar-tag-dot" style="background:${t.color}"></span></span>
      <span class="si-label">${t.label}</span>
    </div>`;
  });
  sb.innerHTML = html;
}

/* ════════════════════════════════════════════════════════════════
   Render — Columns
   ════════════════════════════════════════════════════════════════ */
function renderColumns() {
  const inner     = document.getElementById('columns-inner');
  const container = document.getElementById('columns-container');
  inner.innerHTML = '';

  // Remove any stale placeholder
  container.querySelectorAll('.columns-empty-state').forEach(el => el.remove());

  // Builtin sidebar items (AirDrop, iCloud Drive, All My Files) show a
  // centred placeholder instead of file columns.
  if (sidebarBuiltin) {
    const label = SIDEBAR_ITEMS[activeSidebarIdx]?.label || 'This location';
    const ph = document.createElement('div');
    ph.className = 'columns-empty-state';
    ph.textContent = `${label} is not available in this view.`;
    container.appendChild(ph);
    return;
  }

  columns.forEach((col, ci) => {
    const colEl = document.createElement('div');
    const isFocused = ci === focusedColIdx && !sidebarFocused;
    colEl.className = 'col' + (isFocused ? ' focused' : '');
    colEl.dataset.colidx = ci;

    const scroll = document.createElement('div');
    scroll.className = 'col-scroll';

    if (col.node._loading) {
      // Show spinner while FSA directory loads
      const ld = document.createElement('div');
      ld.className = 'col-loading';
      ld.innerHTML = '<div class="spinner"></div> Loading…';
      scroll.appendChild(ld);
    } else {
      const items = getChildrenFiltered(col.node) || [];
      if (items.length === 0 && col.node.children !== null) {
        const empty = document.createElement('div');
        empty.className = 'col-loading';
        empty.textContent = 'Empty';
        scroll.appendChild(empty);
      }
      // Only apply type-ahead highlights to the focused column
      const queryForHighlight = isFocused ? colSearch : '';
      items.forEach(item => {
        const isFolder   = item.type === 'folder';
        const isSelected = item.name === col.selectedName;
        const div = document.createElement('div');
        div.className   = 'col-item' + (isSelected ? ' selected-active' : '');
        div.dataset.colidx = ci;
        div.dataset.name   = item.name;
        div.innerHTML = `<span class="item-icon">${getIconSVG(item)}</span>` +
                        `<span class="item-label">${highlightLabel(item.name, queryForHighlight)}</span>` +
                        (isFolder && !(Array.isArray(item.children) && item.children.length === 0) ? '<span class="col-arrow">▶</span>' : '');
        scroll.appendChild(div);
      });
    }

    const rh = document.createElement('div');
    rh.className = 'col-resize';
    rh.dataset.colidx = ci;

    colEl.appendChild(scroll);
    colEl.appendChild(rh);
    inner.appendChild(colEl);
  });
}

/* ════════════════════════════════════════════════════════════════
   Render — Preview Panel
   ════════════════════════════════════════════════════════════════ */
function renderPreview() {
  const pv = document.getElementById('preview');
  const f  = selectedFile;

  if (!f) {
    // Show selected folder info if any
    const lastSel = columns.findLast(c => c.selectedName);
    const child   = lastSel?.node.children?.find(c => c.name === lastSel.selectedName);
    if (child?.type === 'folder') {
      const count = child.children === null ? '—' : child.children.length;
      pv.innerHTML =
        `<div style="margin-top:16px">${bigFolderSVG()}</div>
         <div id="preview-name">${child.name}</div>
         <div id="preview-kind">Folder</div>
         <div id="preview-sep"></div>
         <div id="preview-meta">
           <div class="meta-row"><span class="meta-key">Items</span><span class="meta-val">${count}</span></div>
         </div>
         <div id="preview-tags"><a>Add Tags…</a></div>`;
    } else {
      pv.innerHTML = '<div id="preview-empty">Select a file<br>to see a preview</div>';
    }
    return;
  }

  const ext = f.name.split('.').pop().toLowerCase();
  const kindMap = {
    tiff:'TIFF image', tif:'TIFF image',
    jpg:'JPEG image', jpeg:'JPEG image',
    png:'PNG image', gif:'GIF image', webp:'WebP image', heic:'HEIC image',
    mp4:'MPEG-4 movie', mov:'QuickTime movie',
    mp3:'MP3 audio', aac:'AAC audio',
    pdf:'PDF document', doc:'Word document', docx:'Word document',
    txt:'Plain text', md:'Markdown text',
    zip:'ZIP archive', dmg:'Disk Image', pkg:'Installer package',
    pages:'Pages document', numbers:'Numbers spreadsheet', key:'Keynote presentation',
  };
  const kind = kindMap[ext] || (f.type === 'app' ? 'Application' : 'Document');

  pv.innerHTML =
    `<div id="preview-icon">${getBigIcon(f)}</div>
     <div id="preview-name">${f.name}</div>
     <div id="preview-kind">${kind}</div>
     <div id="preview-sep"></div>
     <div id="preview-meta">
       ${f.size       ? `<div class="meta-row"><span class="meta-key">Size</span><span class="meta-val">${f.size}</span></div>` : ''}
       ${f.created    ? `<div class="meta-row"><span class="meta-key">Created</span><span class="meta-val">${f.created}</span></div>` : ''}
       ${f.modified   ? `<div class="meta-row"><span class="meta-key">Modified</span><span class="meta-val">${f.modified}</span></div>` : ''}
       ${f.lastOpened ? `<div class="meta-row"><span class="meta-key">Last opened</span><span class="meta-val">${f.lastOpened}</span></div>` : ''}
       ${f.dims       ? `<div class="meta-row"><span class="meta-key">Dimensions</span><span class="meta-val">${f.dims}</span></div>` : ''}
     </div>
     <div id="preview-tags"><a>Add Tags…</a></div>`;
}

/* ════════════════════════════════════════════════════════════════
   Render — Path Bar & Status Bar
   ════════════════════════════════════════════════════════════════ */
function renderPathBar() {
  const pb = document.getElementById('pathbar');
  if (sidebarBuiltin) {
    const si = SIDEBAR_ITEMS[activeSidebarIdx];
    pb.innerHTML = si ? `<span class="path-item active">${si.label}</span>` : '';
    return;
  }
  const allNames = [...sidebarRootPath, ...getFullPath()];
  let html = '';
  allNames.forEach((name, i) => {
    const last = i === allNames.length - 1;
    html += `<span class="path-item${last ? ' active' : ''}" data-pathidx="${i}">${name}</span>`;
    if (!last) html += `<span class="path-sep">▸</span>`;
  });
  pb.innerHTML = html || '<span class="path-item">Finder</span>';
}

function renderStatusBar() {
  const sb = document.getElementById('statusbar');
  if (selectedFile) {
    const parentCol = columns.findLast(c => c.selectedName &&
      c.node.children?.find(ch => ch.name === c.selectedName && ch.type !== 'folder'));
    const total = parentCol ? parentCol.node.children.length : 1;
    sb.textContent = `1 of ${total} selected, 709.59 GB available`;
  } else {
    const lastSel = columns.findLast(c => c.selectedName);
    const child   = lastSel?.node.children?.find(c => c.name === lastSel.selectedName);
    if (child?.type === 'folder' && child.children !== null) {
      sb.textContent = `${child.children.length} items, 709.59 GB available`;
    } else {
      sb.textContent = '709.59 GB available';
    }
  }
}

function render() {
  renderSidebar();
  renderColumns();
  renderPreview();
  renderPathBar();
  renderStatusBar();
  applyColumnWidths();
  // Scroll after paint so the DOM is fully laid out
  requestAnimationFrame(() => {
    scrollSelectedIntoView();
  });
  // Window title = deepest open folder (last column's node), matching real Finder
  // behaviour where the title shows the folder whose *contents* are displayed,
  // not the name of the selected file within it.
  const si = SIDEBAR_ITEMS[activeSidebarIdx];
  const windowTitle = sidebarBuiltin
    ? (si?.label || 'Finder')
    : (columns.at(-1)?.node.name || si?.label || 'Finder');
  document.title = windowTitle === 'Finder' ? 'Finder' : `${windowTitle} — Finder`;
  const wt = document.getElementById('window-title');
  if (wt) wt.textContent = windowTitle;
}

/* ════════════════════════════════════════════════════════════════
   Scroll active item into view within its column
   ════════════════════════════════════════════════════════════════ */
function scrollSelectedIntoView() {
  document.querySelectorAll('.col-item.selected-active').forEach(el => {
    el.scrollIntoView({ block: 'nearest' });
  });
}

/* ════════════════════════════════════════════════════════════════
   Dynamic column width — canvas.measureText()
   ════════════════════════════════════════════════════════════════ */
function applyColumnWidths() {
  if (globalColWidth > 0) {
    document.documentElement.style.setProperty('--col-width', globalColWidth + 'px');
    return;
  }

  const container = document.getElementById('columns-container');
  const available = container.offsetWidth;
  const numCols   = columns.length;
  if (numCols === 0 || sidebarBuiltin) return;

  const canvas = document.createElement('canvas');
  const ctx    = canvas.getContext('2d');
  // Match the font used for column items
  ctx.font = '13px -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif';

  let maxTextWidth = 80;
  columns.forEach(col => {
    const items = getChildrenFiltered(col.node) || [];
    items.forEach(item => {
      const w = ctx.measureText(item.name).width;
      if (w > maxTextWidth) maxTextWidth = w;
    });
  });

  // icon (16) + gap (5) + text + right-pad (24 for arrow) + left-pad (8)
  const padding   = 16 + 5 + 24 + 8 + 8;
  const computed  = Math.min(maxTextWidth + padding, Math.floor(available / numCols));
  const clamped   = Math.max(120, Math.min(600, computed));
  document.documentElement.style.setProperty('--col-width', clamped + 'px');
}

/* ════════════════════════════════════════════════════════════════
   Auto-scroll columns to keep selection visible
   ════════════════════════════════════════════════════════════════ */
function scrollToActiveColumn() {
  const container = document.getElementById('columns-container');
  const inner     = document.getElementById('columns-inner');
  setTimeout(() => { container.scrollLeft = inner.scrollWidth; }, 0);
}
