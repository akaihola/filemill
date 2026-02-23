/* ════════════════════════════════════════════════════════════════
   Type detection & formatting helpers
   ════════════════════════════════════════════════════════════════ */
function getFileType(name) {
  const ext = (name.split('.').pop() || '').toLowerCase();
  if (['jpg','jpeg','png','gif','tiff','tif','webp','heic','bmp','svg','raw'].includes(ext)) return 'image';
  if (['mov','mp4','avi','mkv','m4v','wmv','mpg','mpeg'].includes(ext))                      return 'video';
  if (['mp3','aac','m4a','flac','wav','ogg','opus'].includes(ext))                            return 'audio';
  if (['pdf','doc','docx','txt','md','rtf','pages','numbers','key','xls','xlsx','ppt','pptx'].includes(ext)) return 'doc';
  if (['zip','tar','gz','bz2','7z','rar','dmg','pkg','iso'].includes(ext))                   return 'archive';
  if (['js','ts','html','css','py','rb','java','c','cpp','h','swift','kt','go','rs'].includes(ext)) return 'code';
  if (name.endsWith('.app'))  return 'app';
  return 'file';
}

function formatFileSize(bytes) {
  if (bytes < 1024)            return bytes + ' bytes';
  if (bytes < 1024 * 1024)     return (bytes / 1024).toFixed(0) + ' KB';
  if (bytes < 1024 ** 3)       return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  return (bytes / 1024 ** 3).toFixed(2) + ' GB';
}

function formatDate(ms) {
  const d   = new Date(ms);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dday  = new Date(d.getFullYear(),   d.getMonth(),  d.getDate());
  const diff  = Math.round((today - dday) / 86400000);
  const t = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (diff === 0) return `Today, ${t}`;
  if (diff === 1) return `Yesterday, ${t}`;
  return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
}

/* ════════════════════════════════════════════════════════════════
   Navigation State
   ════════════════════════════════════════════════════════════════ */
let columns        = [];  // [{ node, selectedName }]
let selectedFile   = null;
let sidebarRootNode = null;
let sidebarRootPath = [];
let historyStack   = [];
let historyIndex   = -1;
let searchQuery    = '';
// Derived at runtime in main.js once SIDEBAR_ITEMS is available
let activeSidebarIdx = -1;

// Keyboard focus state — shared between events.js and render.js
let focusedColIdx  = -1;   // which column has keyboard focus (-1 = none)
let sidebarFocused = false; // true while keyboard focus is in the sidebar
let sidebarBuiltin = false; // true when a builtin sidebar item (AirDrop etc.) is selected

// Type-ahead search state
let colSearch      = '';   // current type-ahead query
let colSearchTimer = null; // setTimeout handle for auto-clear

// Dynamic column width: 0 = compute automatically; positive = user overrode with drag
let globalColWidth = 0;

/* ════════════════════════════════════════════════════════════════
   Mock FS utilities
   ════════════════════════════════════════════════════════════════ */
function findMockNodeByPath(path) {
  let node = MOCK_FS;
  for (const seg of path) {
    if (!node.children) return null;
    node = node.children.find(c => c.name === seg);
    if (!node) return null;
  }
  return node;
}

function getChildren(node) {
  if (!node) return [];
  if (node._loading) return null;   // signal: still loading
  if (!node.children) return [];    // file or empty
  return node.children;
}

function getChildrenFiltered(node) {
  const ch = getChildren(node);
  if (!ch) return null;             // loading
  if (!searchQuery) return ch;
  const q = searchQuery.toLowerCase();
  return ch.filter(c => c.name.toLowerCase().includes(q));
}

/* ════════════════════════════════════════════════════════════════
   Column State — init from mock path
   ════════════════════════════════════════════════════════════════ */
function initToMockPath(sbPath, relPath = []) {
  sidebarRootPath = sbPath;
  sidebarRootNode = findMockNodeByPath(sbPath) || MOCK_FS;

  columns      = [];
  selectedFile = null;
  let node     = sidebarRootNode;

  for (const seg of relPath) {
    const child = node.children?.find(c => c.name === seg);
    if (!child) break;
    columns.push({ node, selectedName: seg });
    if (!child.children) { selectedFile = child; break; }
    node = child;
  }

  if (columns.length === 0) columns.push({ node: sidebarRootNode, selectedName: null });

  // If deepest selection is a folder, open it
  const last = columns.at(-1);
  if (last?.selectedName) {
    const lastChild = last.node.children?.find(c => c.name === last.selectedName);
    if (lastChild?.children) columns.push({ node: lastChild, selectedName: null });
  }
}

/* ════════════════════════════════════════════════════════════════
   Core navigation — async to support FSA lazy loading
   ════════════════════════════════════════════════════════════════ */
let _navigating = false; // prevent re-entrant navigation

async function navigateTo(colIdx, itemName, { skipHistory = false } = {}) {
  if (_navigating) return;
  _navigating = true;
  try {
    columns = columns.slice(0, colIdx + 1);
    columns[colIdx].selectedName = itemName;
    // Remember the last-selected child per folder for right-arrow restoration
    columns[colIdx].node._lastSelected = itemName;
    selectedFile = null;

    const parentNode = columns[colIdx].node;
    const child = parentNode.children?.find(c => c.name === itemName);

    if (child?.type === 'folder') {
      if (child.children === null) {
        // Push loading column first so the spinner is visible during FSA fetch
        columns.push({ node: child, selectedName: null });
        await ensureLoaded(child);
        // Remove the column again if the folder turned out to be empty
        if ((child.children || []).length === 0) columns.pop();
      } else if ((child.children || []).length > 0) {
        columns.push({ node: child, selectedName: null });
      }
    } else if (child) {
      selectedFile = child;
      await loadFileMeta(child); // FSA: get file size/date
    }

    render();
    scrollToActiveColumn();
    if (!skipHistory) pushHistory();
  } finally {
    _navigating = false;
  }
}

function getFullPath() {
  return columns.filter(c => c.selectedName).map(c => c.selectedName);
}

/* ════════════════════════════════════════════════════════════════
   History — store direct node references (no serialisation needed)
   ════════════════════════════════════════════════════════════════ */
function pushHistory() {
  const state = {
    columns:        columns.map(c => ({ node: c.node, selectedName: c.selectedName })),
    selectedFile,
    sidebarRootNode,
    sidebarRootPath: [...sidebarRootPath],
    activeSidebarIdx,
    sidebarBuiltin,
  };
  historyStack = historyStack.slice(0, historyIndex + 1);
  historyStack.push(state);
  // Cap at 100 entries to avoid unbounded growth
  if (historyStack.length > 100) {
    historyStack.shift();
  } else {
    historyIndex++;
  }
  updateNavButtons();
}

function restoreState(state) {
  columns          = state.columns.map(c => ({ node: c.node, selectedName: c.selectedName }));
  selectedFile     = state.selectedFile;
  sidebarRootNode  = state.sidebarRootNode;
  sidebarRootPath  = state.sidebarRootPath || [];
  activeSidebarIdx = state.activeSidebarIdx;
  sidebarBuiltin   = state.sidebarBuiltin ?? false;
  render();
  updateNavButtons();
}

function updateNavButtons() {
  document.getElementById('btn-back').disabled = historyIndex <= 0;
  document.getElementById('btn-fwd').disabled  = historyIndex >= historyStack.length - 1;
}
