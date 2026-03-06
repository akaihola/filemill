from pygments.formatters import HtmlFormatter

PYGMENTS_FORMATTER = HtmlFormatter(nowrap=True)
HIGHLIGHT_CSS = HtmlFormatter(style="friendly").get_style_defs(".highlight")
FRIENDLY_CSS = HtmlFormatter(style="friendly").get_style_defs(".highlight")

APP_CSS = (
    """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    font-size: 13px;
    background: #f0f0f0;
    margin: 0;
    overflow: hidden;
    height: 100vh;
}

#app-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
}

#breadcrumb {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    font-size: 12px;
    background: #ebebeb;
    border-bottom: 1px solid #c7c7c7;
    flex-shrink: 0;
    color: #333;
    overflow: hidden;
}

.bc-toggle {
    margin-left: auto;
    flex-shrink: 0;
    padding: 1px 6px;
    border: 1px solid #bbb;
    border-radius: 3px;
    background: #fff;
    cursor: pointer;
    font-size: 11px;
    font-family: "SF Mono", "Fira Code", monospace;
    color: #999;
    line-height: 1.4;
    user-select: none;
}
.bc-toggle:hover {
    background: #e8e8e8;
}
.bc-toggle.active {
    background: #0070c9;
    color: #fff;
    border-color: #0070c9;
}
.bc-toggle.active:hover {
    background: #005da6;
}

/* Dotfiles: hidden by default, visible when body carries .show-dotfiles */
.column li.dotfile {
    display: none;
}
body.show-dotfiles .column li.dotfile {
    display: list-item;
}
body.show-dotfiles .column li.dotfile > a {
    opacity: 0.65;
}

.bc-root, .bc-seg {
    font-weight: 500;
}

.bc-sep {
    color: #999;
    margin: 0 4px;
}

#finder {
    display: flex;
    flex: 1;
    min-height: 0;
    overflow-x: auto;
    overflow-y: hidden;
}

.column {
    width: var(--col-width, 220px);
    height: 100%;
    overflow-y: auto;
    border-right: 1px solid #c7c7c7;
    background: #fff;
    flex-shrink: 0;
}

.column ul {
    list-style: none;
    margin: 0;
    padding: 0;
}

.column li a {
    display: block;
    padding: 4px 8px 4px 24px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #000;
    text-decoration: none;
    cursor: pointer;
    position: relative;
}

.column li.selected > a {
    background: #0070c9;
    color: #fff;
}

.column li.selected > a .icon {
    color: #fff;
}

.column li:not(.selected) a:hover {
    background: #e8e8e8;
}

.icon {
    position: absolute;
    left: 6px;
}

#preview {
    flex: 1;
    min-width: 33.333vw;
    overflow-y: auto;
    padding: 1rem 1.5rem;
    background: #fff;
    border-left: 1px solid #c7c7c7;
}

.preview-md {
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.6;
}

.preview-md h1, .preview-md h2, .preview-md h3,
.preview-md h4, .preview-md h5, .preview-md h6 {
    margin-top: 1.2em;
    margin-bottom: 0.4em;
    font-weight: 600;
}

.preview-md h1 { font-size: 1.8em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }
.preview-md h2 { font-size: 1.4em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }
.preview-md h3 { font-size: 1.2em; }

.preview-md p { margin: 0.6em 0; }

.preview-md code {
    background: #f3f3f3;
    border-radius: 3px;
    padding: 0.1em 0.3em;
    font-size: 0.9em;
    font-family: "SF Mono", "Fira Code", monospace;
}

.preview-md pre {
    background: #f3f3f3;
    border-radius: 5px;
    padding: 0.8em 1em;
    overflow-x: auto;
    margin: 0.8em 0;
}

.preview-md pre code {
    background: none;
    padding: 0;
    font-size: 0.85em;
}

.preview-md .highlight {
    background: #f3f3f3;
    border-radius: 5px;
    padding: 0.8em 1em;
    overflow-x: auto;
    margin: 0.8em 0;
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.85em;
}

.preview-md table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.8em 0;
}

.preview-md th, .preview-md td {
    border: 1px solid #ccc;
    padding: 6px 10px;
    text-align: left;
}

.preview-md th {
    background: #f0f0f0;
    font-weight: 600;
}

.preview-md blockquote {
    border-left: 3px solid #0070c9;
    margin: 0.8em 0;
    padding: 0.2em 1em;
    color: #555;
    background: #f8f8f8;
}

.preview-md ul, .preview-md ol {
    margin: 0.4em 0;
    padding-left: 1.8em;
}

.preview-md li { margin: 0.2em 0; }

.preview-md input[type="checkbox"] { margin-right: 0.4em; }

.preview-md hr {
    border: none;
    border-top: 1px solid #eee;
    margin: 1.2em 0;
}

.preview-md a { color: #0070c9; }

.preview-pdf iframe {
    width: 100%;
    height: 90vh;
    border: none;
}

.preview-pptx .slide {
    border: 1px solid #ddd;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    background: #fafafa;
}

.preview-pptx .slide h3 {
    margin: 0 0 0.5em 0;
    font-size: 1em;
    color: #666;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.3em;
}

.preview-raw {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.85em;
    background: #f8f8f8;
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    padding: 1rem;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
}

.preview-error {
    color: #c00;
    font-style: italic;
}

.preview-empty {
    color: #999;
    font-style: italic;
    padding: 1rem;
}

.preview-image {
    background-color: #fff;
    background-image:
        linear-gradient(45deg, #ccc 25%, transparent 25%),
        linear-gradient(-45deg, #ccc 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #ccc 75%),
        linear-gradient(-45deg, transparent 75%, #ccc 75%);
    background-size: 16px 16px;
    background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
    display: inline-block;
    max-width: 100%;
}

.preview-image img {
    display: block;
    max-width: 100%;
    max-height: 100%;
}

body.zoomed .column {
    display: none;
}
body.zoomed #preview {
    width: 100vw;
    min-width: unset;
    box-sizing: border-box;
}

"""
    + f"""
/* Pygments syntax highlighting */
.highlight {{ background: #f3f3f3; }}
{HIGHLIGHT_CSS}

/* Source code preview block */
.preview-code {{
    padding: 0.5rem;
}}
.preview-code .highlight {{
    border-radius: 5px;
    overflow-x: auto;
}}

{FRIENDLY_CSS}

/* ── VFS / format toggle ──────────────────────────────────────────────── */
.fmt-bar {{
    display: flex;
    gap: 4px;
    padding: 4px 8px;
    background: #f5f5f5;
    border-bottom: 1px solid #ddd;
    flex-shrink: 0;
}}
.fmt-btn {{
    padding: 2px 8px;
    border: 1px solid #bbb;
    border-radius: 3px;
    background: #fff;
    cursor: pointer;
    font-size: 12px;
}}
.fmt-btn.active {{
    background: #0070c9;
    color: #fff;
    border-color: #0070c9;
    cursor: default;
}}

/* DB spreadsheet preview */
.preview-db-spreadsheet {{
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
}}
.db-table-wrap {{
    flex: 1;
    overflow: auto;
    min-height: 0;
}}
.db-table {{
    border-collapse: collapse;
    font-size: 12px;
    width: 100%;
}}
.db-table th {{
    background: #f0f0f0;
    border: 1px solid #ddd;
    padding: 4px 8px;
    position: sticky;
    top: 0;
    z-index: 1;
    white-space: nowrap;
}}
.db-table td {{
    border: 1px solid #eee;
    padding: 4px 8px;
    white-space: nowrap;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
}}

/* DB KV row detail */
.preview-db-row {{
    padding: 1rem;
    overflow: auto;
    height: 100%;
    box-sizing: border-box;
}}
.db-kv-table {{
    border-collapse: collapse;
    width: 100%;
}}
.db-kv-table th {{
    text-align: left;
    padding: 4px 12px 4px 0;
    color: #666;
    font-weight: 600;
    white-space: nowrap;
    vertical-align: top;
    min-width: 120px;
}}
.db-kv-table td {{
    padding: 4px 0;
    word-break: break-word;
}}

/* DB pagination bar */
.db-pagination {{
    padding: 6px 8px;
    border-top: 1px solid #ddd;
    font-size: 12px;
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
    color: #555;
}}
.db-pagination a {{
    color: #0070c9;
    text-decoration: none;
    cursor: pointer;
}}

/* Virtual breadcrumb segments */
.bc-virtual {{
    font-style: italic;
    color: #555;
}}
"""
)

COLUMN_JS = """
function _syncZoomBtn() {
    var btn = document.getElementById('zoom-btn');
    if (!btn) return;
    var zoomed = document.body.classList.contains('zoomed');
    btn.textContent = zoomed ? '✕' : '⛶';
    btn.title = zoomed ? 'Restore columns' : 'Expand preview';
    btn.classList.toggle('active', zoomed);
}

function toggleZoom() {
    document.body.classList.toggle('zoomed');
    _syncZoomBtn();
    recalcColumnWidth();
}

function initZoomButton() {
    _syncZoomBtn(); // button is server-rendered in breadcrumb; just sync state
}

function recalcColumnWidth() {
    var columns = document.querySelectorAll('.column');
    if (!columns.length) return;

    // --- measure longest anchor text ---
    // Use a hidden canvas for pixel-accurate text measurement with the
    // same font as the column anchors (13px system-ui, matching body).
    var canvas = recalcColumnWidth._canvas ||
                 (recalcColumnWidth._canvas = document.createElement('canvas'));
    var ctx = canvas.getContext('2d');
    ctx.font = '13px -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif';

    var showDots = document.body.classList.contains('show-dotfiles');
    var maxTextPx = 0;
    columns.forEach(function(col) {
        col.querySelectorAll('li').forEach(function(li) {
            // Skip hidden dotfile entries so they don't inflate column width
            if (li.classList.contains('dotfile') && !showDots) return;
            var a = li.querySelector('a');
            if (!a) return;
            // Clone the text content without the icon span
            var text = '';
            a.childNodes.forEach(function(node) {
                if (node.nodeType === Node.TEXT_NODE) text += node.textContent;
            });
            var w = ctx.measureText(text.trim()).width;
            if (w > maxTextPx) maxTextPx = w;
        });
    });

    // padding: 4px top/bottom, 8px right, 24px left (icon gutter) → 32px horizontal padding
    var PADDING = 32;
    var ICON_WIDTH = 20;   // space already included in the 24px left-padding
    var MIN_WIDTH = 160;
    var PREVIEW_MIN = Math.round(window.innerWidth / 3); // always ≥ 1/3 viewport
    var colCount = columns.length;

    var available = window.innerWidth - PREVIEW_MIN;
    var maxWidth = colCount > 0 ? Math.floor(available / colCount) : available;
    maxWidth = Math.max(maxWidth, MIN_WIDTH); // never go below minimum even if crowded

    var computed = Math.min(
        Math.max(Math.ceil(maxTextPx) + PADDING + ICON_WIDTH, MIN_WIDTH),
        maxWidth
    );

    document.documentElement.style.setProperty('--col-width', computed + 'px');
}

// Track the path param from the most recent click for URL sync
var _pendingPath = null;

// Capture path from hx-get attribute before HTMX fires
document.addEventListener('click', function(e) {
    var a = e.target.closest('.column li a[hx-get], .column li a[data-hx-get]');
    if (!a) return;
    var hxGet = a.getAttribute('hx-get') || a.getAttribute('data-hx-get');
    if (!hxGet) return;
    try {
        var url = new URL(hxGet, window.location.href);
        _pendingPath = url.searchParams.get('path');
    } catch(err) {}
});

// After HTMX settles, push/replace the URL
// ── Dotfiles visibility toggle ──────────────────────────────────────────────
var _DOT_KEY = 'pykofinder_show_dotfiles';

function _syncDotBtn() {
    var btn = document.getElementById('dotfiles-btn');
    if (!btn) return;
    var show = document.body.classList.contains('show-dotfiles');
    btn.classList.toggle('active', show);
    btn.title = show ? 'Hide dotfiles' : 'Show dotfiles';
}

function toggleDotfiles() {
    var show = document.body.classList.toggle('show-dotfiles');
    localStorage.setItem(_DOT_KEY, show ? '1' : '0');
    _syncDotBtn();
    recalcColumnWidth();
}

function initDotfilesToggle() {
    if (localStorage.getItem(_DOT_KEY) === '1') {
        document.body.classList.add('show-dotfiles');
    }
    _syncDotBtn();
}

document.addEventListener('htmx:afterSettle', function(e) {
    recalcColumnWidth();
    _syncDotBtn();
    _syncZoomBtn();
    var finder = document.getElementById('finder');
    if (finder) finder.scrollLeft = finder.scrollWidth;
    if (_pendingPath) {
        var newUrl = '/f/?path=' + encodeURIComponent(_pendingPath);
        history.pushState({path: _pendingPath}, '', newUrl);
        _pendingPath = null;
    }
});

// Handle browser back/forward
window.addEventListener('popstate', function(e) {
    var path = e.state && e.state.path;
    if (path) {
        _deepNavigate(path);
    } else {
        // Back to root – reload to reset state
        window.location.href = '/f/';
    }
});

function _deepNavigate(fullPath) {
    // Navigate to fullPath via the /restore endpoint which returns a ready-made column set.
    fetch('/restore?path=' + encodeURIComponent(fullPath))
        .then(function(r) { return r.text(); })
        .then(function(html) {
            var shell = document.getElementById('app-shell');
            if (shell) {
                shell.outerHTML = html;
                recalcColumnWidth();
                initZoomButton();
                var finder = document.getElementById('finder');
                if (finder) finder.scrollLeft = finder.scrollWidth;
            }
        })
        .catch(function() {});
}

document.addEventListener('DOMContentLoaded', function() {
    recalcColumnWidth();
    initZoomButton();
    initDotfilesToggle();
    // Deep-link: restore state from URL
    var params = new URLSearchParams(window.location.search);
    var deepPath = params.get('path');
    if (deepPath) {
        _deepNavigate(deepPath);
    }
});

// Selection highlighting – mark the clicked <li> as selected within its column
document.addEventListener('click', function(e) {
    var a = e.target.closest('.column li a');
    if (!a) return;
    // Only handle HTMX-driven links (not .desktop target=_blank links)
    if (!a.hasAttribute('hx-get') && !a.hasAttribute('data-hx-get')) return;
    var li = a.closest('li');
    var ul = a.closest('ul');
    if (!li || !ul) return;
    ul.querySelectorAll('li').forEach(function(sibling) {
        sibling.classList.remove('selected');
    });
    li.classList.add('selected');
});

// ── VFS format persistence ──────────────────────────────────────────────────
(function () {
  var FMTKEY_TYPE = function (ext) {
    return "vfmt_type_" + ext;
  };
  var FMTKEY_FILE = function (fpath, vpath) {
    return "vfmt_file_" + fpath + "::" + vpath;
  };

  // Inject stored fmt into every HTMX request that carries data-fpath
  document.body.addEventListener("htmx:configRequest", function (evt) {
    var elt = evt.detail.elt;
    var fpath = elt.dataset.fpath;
    var vpath = elt.dataset.vpath;
    var ext = elt.dataset.ext;
    // Only intercept VFS navigation links (those with data-fpath)
    if (fpath === undefined) return;
    // Don't override an explicit fmt already in the request params
    if (evt.detail.parameters && evt.detail.parameters.fmt) return;
    var stored =
      localStorage.getItem(
        FMTKEY_FILE(fpath, vpath !== undefined ? vpath : ""),
      ) || (ext ? localStorage.getItem(FMTKEY_TYPE(ext)) : null);
    if (stored) {
      evt.detail.parameters = evt.detail.parameters || {};
      evt.detail.parameters.fmt = stored;
    }
  });

  // Toggle buttons write to localStorage when clicked (before HTMX fires)
  document.body.addEventListener("click", function (evt) {
    var btn = evt.target.closest(".fmt-btn[data-fmt]");
    if (!btn || btn.classList.contains("active")) return;
    var fpath = btn.dataset.fpath;
    var vpath = btn.dataset.vpath;
    var ext = btn.dataset.ext;
    var fmt = btn.dataset.fmt;
    if (fpath !== undefined && vpath !== undefined) {
      localStorage.setItem(FMTKEY_FILE(fpath, vpath), fmt);
    }
    if (ext) {
      localStorage.setItem(FMTKEY_TYPE(ext), fmt);
    }
  });
})();

// ── Keyboard navigation ──────────────────────────────────────────────────────
(function() {
    function getColumns() {
        return Array.from(document.querySelectorAll('#finder .column'));
    }

    function getSelectedLi(col) {
        return col ? col.querySelector('li.selected') : null;
    }

    function selectLi(li) {
        if (!li) return;
        var ul = li.closest('ul');
        if (ul) ul.querySelectorAll('li').forEach(function(s) { s.classList.remove('selected'); });
        li.classList.add('selected');
        li.scrollIntoView({ block: 'nearest' });
    }

    function focusedColIndex() {
        var cols = getColumns();
        // Focused column = rightmost column that has a selected item,
        // or the rightmost column overall.
        for (var i = cols.length - 1; i >= 0; i--) {
            if (getSelectedLi(cols[i])) return i;
        }
        return cols.length - 1;
    }

    document.addEventListener('keydown', function(e) {
        // Don't hijack input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        var cols = getColumns();
        if (!cols.length) return;

        var ci = focusedColIndex();
        var col = cols[ci];
        var sel = getSelectedLi(col);
        var items = col ? Array.from(col.querySelectorAll('li')) : [];

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (!sel && items.length) {
                    selectLi(items[0]);
                } else if (sel) {
                    var idx = items.indexOf(sel);
                    if (idx < items.length - 1) selectLi(items[idx + 1]);
                }
                break;

            case 'ArrowUp':
                e.preventDefault();
                if (sel) {
                    var idx = items.indexOf(sel);
                    if (idx > 0) selectLi(items[idx - 1]);
                }
                break;

            case 'ArrowRight':
            case 'Enter':
                e.preventDefault();
                if (sel) {
                    var a = sel.querySelector('a');
                    if (a) {
                        if (a.getAttribute('hx-get') || a.getAttribute('data-hx-get')) {
                            htmx.trigger(a, 'click');
                        } else {
                            a.click();
                        }
                    }
                }
                break;

            case 'ArrowLeft':
                e.preventDefault();
                if (ci > 0) {
                    // Move focus to parent column – its selected item is already marked.
                    // If no selected item in parent col, select the first item.
                    var parentCol = cols[ci - 1];
                    var parentSel = getSelectedLi(parentCol);
                    if (!parentSel) {
                        var parentItems = parentCol.querySelectorAll('li');
                        if (parentItems.length) selectLi(parentItems[0]);
                    }
                    // Remove selection from current column
                    items.forEach(function(li) { li.classList.remove('selected'); });
                    // Prune columns to the right of parent
                    // (this mimics clicking the parent – but we don't want to re-fetch)
                    // Just collapse: remove all columns to right of ci-1
                    for (var j = cols.length - 1; j > ci - 1; j--) {
                        if (cols[j]) cols[j].remove();
                    }
                    // Also clear preview
                    var preview = document.getElementById('preview');
                    if (preview) { preview.innerHTML = ''; preview.className = 'preview-empty'; }
                    recalcColumnWidth();
                }
                break;

            case 'Escape':
                e.preventDefault();
                // Clear all selections
                document.querySelectorAll('#finder li.selected').forEach(function(li) {
                    li.classList.remove('selected');
                });
                break;
        }
    });
})();
"""


LIVE_RELOAD_JS = """
(function() {
    var evtSource = new EventSource('/sse/reload');
    evtSource.onmessage = function(e) {
        if (e.data === 'reload') window.location.reload();
    };
    evtSource.onerror = function() {
        // Connection lost – retry is automatic for EventSource
    };
})();
"""
