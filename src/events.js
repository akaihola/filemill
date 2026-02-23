/* ════════════════════════════════════════════════════════════════
   Type-ahead helpers
   ════════════════════════════════════════════════════════════════ */
function clearColSearch(doRender = true) {
  clearTimeout(colSearchTimer);
  colSearchTimer = null;
  if (!colSearch) return;
  colSearch = '';
  // Commit the type-ahead landing position to history now that the
  // search is done, then re-render without highlights.
  pushHistory();
  if (doRender) render();
}

function findColSearchMatch(items, query) {
  const q = query.toLowerCase();
  // 1. Exact prefix
  let m = items.find(i => i.name.toLowerCase().startsWith(q));
  if (m) return m;
  // 2. Substring
  m = items.find(i => i.name.toLowerCase().includes(q));
  if (m) return m;
  // 3. Fuzzy — all query chars appear in order
  return items.find(i => {
    let qi = 0;
    for (const c of i.name.toLowerCase()) {
      if (c === q[qi]) { qi++; if (qi === q.length) return true; }
    }
    return false;
  }) || null;
}

/* ════════════════════════════════════════════════════════════════
   Keyboard Navigation
   ════════════════════════════════════════════════════════════════ */
document.getElementById('columns-container').addEventListener('keydown', async e => {
  const isPrintable = e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey;
  const isBackspace = e.key === 'Backspace';
  const isEscape    = e.key === 'Escape';
  const isArrow     = e.key.startsWith('Arrow');
  const isEnter     = e.key === 'Enter';
  const isHome      = e.key === 'Home';
  const isEnd       = e.key === 'End';

  if (!isPrintable && !isBackspace && !isEscape && !isArrow && !isEnter && !isHome && !isEnd) return;
  if (isArrow || isEnter || isHome || isEnd) e.preventDefault();

  /* ── Sidebar focus mode ─────────────────────────────────────── */
  if (sidebarFocused) {
    if (isArrow || isEnter) {
      e.preventDefault();
      if (e.key === 'ArrowUp') {
        const newIdx = Math.max(0, activeSidebarIdx - 1);
        if (newIdx !== activeSidebarIdx) {
          activeSidebarIdx = newIdx;
          const si = SIDEBAR_ITEMS[activeSidebarIdx];
          if (si?.type === 'mock') { sidebarBuiltin = false; initToMockPath(si.path, []); }
          else if (si?.type === 'fsa') {
            sidebarBuiltin  = false;
            sidebarRootNode = si.node;
            sidebarRootPath = [si.node.name];
            columns         = [{ node: si.node, selectedName: null }];
            selectedFile    = null;
          } else { sidebarBuiltin = true; columns = []; selectedFile = null; }
          render();
          scrollToActiveColumn();
          pushHistory();
        }
      } else if (e.key === 'ArrowDown') {
        const newIdx = Math.min(SIDEBAR_ITEMS.length - 1, activeSidebarIdx + 1);
        if (newIdx !== activeSidebarIdx) {
          activeSidebarIdx = newIdx;
          const si = SIDEBAR_ITEMS[activeSidebarIdx];
          if (si?.type === 'mock') { sidebarBuiltin = false; initToMockPath(si.path, []); }
          else if (si?.type === 'fsa') {
            sidebarBuiltin  = false;
            sidebarRootNode = si.node;
            sidebarRootPath = [si.node.name];
            columns         = [{ node: si.node, selectedName: null }];
            selectedFile    = null;
          } else { sidebarBuiltin = true; columns = []; selectedFile = null; }
          render();
          scrollToActiveColumn();
          pushHistory();
        }
      } else if (e.key === 'ArrowRight' || isEnter) {
        // Move keyboard focus into column 0, restoring the last highlighted item
        if (columns.length > 0) {
          sidebarFocused = false;
          focusedColIdx = 0;
          const col0  = columns[0];
          const items = getChildrenFiltered(col0.node) || [];
          const saved = col0.node._lastSelected
            ? items.find(i => i.name === col0.node._lastSelected)?.name
            : null;
          if (saved) {
            await navigateTo(0, saved);
          } else {
            render();
          }
        }
      }
      // ArrowLeft in sidebar → do nothing (already at leftmost)
    }
    return; // swallow all other keys while sidebar is focused
  }

  /* ── Type-ahead search ──────────────────────────────────────── */
  if (isPrintable || isBackspace || isEscape) {
    if (isEscape) { clearColSearch(); return; }
    if (isBackspace) {
      if (colSearch.length > 0) colSearch = colSearch.slice(0, -1);
      else return;
    } else {
      colSearch += e.key;
    }

    if (colSearch) {
      clearTimeout(colSearchTimer);
      colSearchTimer = setTimeout(clearColSearch, 1500);

      if (focusedColIdx < 0 || focusedColIdx >= columns.length)
        focusedColIdx = columns.length - 1;

      const col   = columns[focusedColIdx];
      const items = getChildrenFiltered(col.node) || [];
      const match = findColSearchMatch(items, colSearch);
      if (match) {
        // Navigate without pushing history — clearColSearch will commit it
        await navigateTo(focusedColIdx, match.name, { skipHistory: true });
      } else {
        render(); // still re-render to show updated highlights
      }
    } else {
      // colSearch became empty via backspace — just re-render, don't commit
      clearTimeout(colSearchTimer);
      colSearchTimer = null;
      render();
    }
    return;
  }

  /* ── Arrow / Enter navigation ───────────────────────────────── */
  // Any arrow key clears type-ahead (without a history commit — we're
  // about to navigate somewhere new, which will push its own entry).
  if (colSearch) {
    clearTimeout(colSearchTimer);
    colSearchTimer = null;
    colSearch = '';
    // No render here — navigation below will render
  }

  if (focusedColIdx < 0 || focusedColIdx >= columns.length)
    focusedColIdx = columns.length - 1;

  const col   = columns[focusedColIdx];
  if (!col && e.key !== 'ArrowLeft') return;

  // col may be undefined when columns=[] (builtin empty-state) and key=ArrowLeft
  const items  = col ? (getChildrenFiltered(col.node) || []) : [];
  const curIdx = col?.selectedName ? items.findIndex(i => i.name === col.selectedName) : -1;

  if (e.key === 'ArrowDown') {
    const next = curIdx < 0 ? 0 : Math.min(curIdx + 1, items.length - 1);
    if (items[next]) await navigateTo(focusedColIdx, items[next].name);

  } else if (e.key === 'ArrowUp') {
    const prev = curIdx < 0 ? 0 : Math.max(curIdx - 1, 0);
    if (items[prev]) await navigateTo(focusedColIdx, items[prev].name);

  } else if (isHome) {
    if (items[0]) await navigateTo(focusedColIdx, items[0].name);

  } else if (isEnd) {
    const last = items[items.length - 1];
    if (last) await navigateTo(focusedColIdx, last.name);

  } else if (e.key === 'ArrowRight') {
    const nextIdx = focusedColIdx + 1;
    if (nextIdx < columns.length) {
      // Column already exists — move into it
      const nextCol = columns[nextIdx];
      if (nextCol.selectedName) {
        focusedColIdx = nextIdx;
        render();
      } else {
        const nextItems = getChildrenFiltered(nextCol.node) || [];
        if (nextItems.length > 0) {
          focusedColIdx = nextIdx;
          // Restore last-selected item, fall back to topmost
          const itemName = nextCol.node._lastSelected
            ? nextItems.find(i => i.name === nextCol.node._lastSelected)?.name
            : null;
          await navigateTo(nextIdx, itemName || nextItems[0].name);
        }
        // else: empty column — do nothing (no-op)
      }
    } else {
      // No next column yet — try to open the selected folder
      if (col.selectedName) {
        const child = col.node.children?.find(c => c.name === col.selectedName);
        if (child?.type === 'folder') {
          const lenBefore = columns.length;
          await navigateTo(focusedColIdx, col.selectedName);
          if (columns.length > lenBefore) focusedColIdx = columns.length - 1;
        }
      }
    }

  } else if (e.key === 'ArrowLeft') {
    // Find the rightmost column that has a selection
    let rightmost = -1;
    for (let i = columns.length - 1; i >= 0; i--) {
      if (columns[i].selectedName) { rightmost = i; break; }
    }
    if (rightmost >= 0) {
      columns[rightmost].selectedName = null;
      columns = columns.slice(0, rightmost + 1);
      selectedFile = null;
      if (rightmost === 0) {
        // Leftmost column had the only selection — retreat to sidebar
        sidebarFocused = true;
        focusedColIdx  = -1;
      } else {
        focusedColIdx = rightmost - 1;
      }
      render();
      pushHistory();
    } else if (focusedColIdx > 0) {
      focusedColIdx--;
      render();
    } else {
      // Already at leftmost column with no selection — go to sidebar
      sidebarFocused = true;
      focusedColIdx  = -1;
      render();
    }

  } else if (e.key === 'Enter') {
    if (col.selectedName) await navigateTo(focusedColIdx, col.selectedName);
  }
});

/* ════════════════════════════════════════════════════════════════
   Column item clicks
   ════════════════════════════════════════════════════════════════ */
document.getElementById('columns-inner').addEventListener('click', async e => {
  const item = e.target.closest('.col-item');
  if (!item) return;
  // Clicking a column always cancels type-ahead and sidebar focus
  clearColSearch(false);
  sidebarFocused = false;
  focusedColIdx = parseInt(item.dataset.colidx);
  await navigateTo(focusedColIdx, item.dataset.name);
  document.getElementById('columns-container').focus();
});

/* ════════════════════════════════════════════════════════════════
   Sidebar clicks
   ════════════════════════════════════════════════════════════════ */
document.getElementById('sidebar').addEventListener('click', async e => {
  const item = e.target.closest('.sidebar-item');
  if (!item) return;
  const idx = parseInt(item.dataset.sbIdx);
  if (isNaN(idx)) return;
  const si = SIDEBAR_ITEMS[idx];
  if (!si) return;

  activeSidebarIdx = idx;
  clearColSearch(false);
  sidebarFocused = false;
  focusedColIdx  = 0;
  globalColWidth = 0; // reset drag-override on sidebar change

  if (si.type === 'fsa') {
    sidebarBuiltin  = false;
    sidebarRootNode = si.node;
    sidebarRootPath = [si.node.name];
    columns         = [{ node: si.node, selectedName: null }];
    selectedFile    = null;
  } else if (si.type === 'mock') {
    sidebarBuiltin = false;
    initToMockPath(si.path, []);
  } else {
    // builtin (AirDrop, iCloud Drive, All My Files, …) — show placeholder
    sidebarBuiltin  = true;
    sidebarRootNode = MOCK_FS;
    sidebarRootPath = [];
    columns         = [];
    selectedFile    = null;
  }
  render();
  scrollToActiveColumn();
  pushHistory();
  // Return keyboard focus to the columns area after sidebar click
  document.getElementById('columns-container').focus();
});

/* ════════════════════════════════════════════════════════════════
   Open Folder button (FSA)
   ════════════════════════════════════════════════════════════════ */
document.getElementById('btn-open-folder').addEventListener('click', openFolderPicker);

/* ════════════════════════════════════════════════════════════════
   Column resize (drag) — adjusts globalColWidth so all columns
   resize together (matches real macOS Finder column-view behaviour)
   ════════════════════════════════════════════════════════════════ */
let resizing = null;
document.getElementById('columns-inner').addEventListener('mousedown', e => {
  const rh = e.target.closest('.col-resize');
  if (!rh) return;
  e.preventDefault();
  const colEl = rh.parentElement;
  resizing = { startX: e.clientX, startW: colEl.offsetWidth };
  document.body.classList.add('col-resizing');
});
document.addEventListener('mousemove', e => {
  if (!resizing) return;
  const w = Math.max(120, Math.min(600, resizing.startW + e.clientX - resizing.startX));
  globalColWidth = w;
  document.documentElement.style.setProperty('--col-width', w + 'px');
});
document.addEventListener('mouseup', () => {
  resizing = null;
  document.body.classList.remove('col-resizing');
});

/* ════════════════════════════════════════════════════════════════
   View mode toggle
   ════════════════════════════════════════════════════════════════ */
document.querySelectorAll('.view-btn').forEach(btn => btn.addEventListener('click', () => {
  document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}));

/* ════════════════════════════════════════════════════════════════
   Back / Forward
   ════════════════════════════════════════════════════════════════ */
document.getElementById('btn-back').addEventListener('click', () => {
  if (historyIndex > 0) { historyIndex--; restoreState(historyStack[historyIndex]); }
});
document.getElementById('btn-fwd').addEventListener('click', () => {
  if (historyIndex < historyStack.length - 1) { historyIndex++; restoreState(historyStack[historyIndex]); }
});

/* ════════════════════════════════════════════════════════════════
   Search
   ════════════════════════════════════════════════════════════════ */
document.getElementById('search-input').addEventListener('input', e => {
  clearColSearch(false);
  sidebarFocused = false;
  searchQuery = e.target.value.trim();
  render();
});

/* ════════════════════════════════════════════════════════════════
   Path bar clicks
   ════════════════════════════════════════════════════════════════ */
document.getElementById('pathbar').addEventListener('click', async e => {
  const item = e.target.closest('.path-item');
  if (!item) return;
  const idx   = parseInt(item.dataset.pathidx);
  const sbLen = sidebarRootPath.length;

  if (idx < sbLen - 1) {
    // Clicked an ancestor above the sidebar root — navigate in mock FS
    const newSbPath = sidebarRootPath.slice(0, idx + 1);
    initToMockPath(newSbPath, []);
    const str = newSbPath.join('/');
    const mi  = SIDEBAR_ITEMS.findIndex(s => s.path?.join('/') === str);
    if (mi >= 0) activeSidebarIdx = mi;
  } else {
    // Within column-relative path
    const colRelIdx = idx - sbLen;
    if (colRelIdx >= 0 && colRelIdx < columns.length && columns[colRelIdx].selectedName) {
      await navigateTo(colRelIdx, columns[colRelIdx].selectedName);
    }
  }
  render();
  pushHistory();
});
