# Milestone 10 – Browser-side behaviour

Until now `styles.py` contained the full CSS but only placeholder JavaScript.
This final milestone replaces those stubs with the complete client-side
behaviour layer: zoom toggling, dotfile visibility persistence, dynamic
column-width calculation, URL synchronisation, deep-link restoration,
selection highlighting, VFS format persistence, keyboard navigation, and
live reload.

## Full column script

Our empty `COLUMN_JS` stub from Milestone 2 did nothing. We now replace it
with the complete script that drives the interactive Finder experience.

```python "column js"
"""
// Workaround for Firefox Android not applying CSS on first direct load of a
// /f/ URL: force a fresh page load with ?_=1, then clean the param from the
// address bar on the reloaded page.
if (location.pathname.startsWith('/f/') && !location.search) {
    location.replace(location.href + '?_=1');
} else if (location.search === '?_=1') {
    history.replaceState(null, '', location.pathname);
}

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
    _syncZoomBtn();
}

function recalcColumnWidth() {
    var columns = document.querySelectorAll('.column');
    if (!columns.length) return;

    var canvas = recalcColumnWidth._canvas ||
                 (recalcColumnWidth._canvas = document.createElement('canvas'));
    var ctx = canvas.getContext('2d');
    ctx.font = '13px -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif';

    var showDots = document.body.classList.contains('show-dotfiles');
    var maxTextPx = 0;
    columns.forEach(function(col) {
        col.querySelectorAll('li').forEach(function(li) {
            if (li.classList.contains('dotfile') && !showDots) return;
            var a = li.querySelector('a');
            if (!a) return;
            var text = '';
            a.childNodes.forEach(function(node) {
                if (node.nodeType === Node.TEXT_NODE) text += node.textContent;
            });
            var w = ctx.measureText(text.trim()).width;
            if (w > maxTextPx) maxTextPx = w;
        });
    });

    var PADDING = 32;
    var ICON_WIDTH = 20;
    var MIN_WIDTH = 160;
    var PREVIEW_MIN = Math.round(window.innerWidth / 3);
    var colCount = columns.length;

    var available = window.innerWidth - PREVIEW_MIN;
    var maxWidth = colCount > 0 ? Math.floor(available / colCount) : available;
    maxWidth = Math.max(maxWidth, MIN_WIDTH);

    var computed = Math.min(
        Math.max(Math.ceil(maxTextPx) + PADDING + ICON_WIDTH, MIN_WIDTH),
        maxWidth
    );

    document.documentElement.style.setProperty('--col-width', computed + 'px');
}

var _pendingPath = null;
var _pendingVpath = null;
var _pendingFinderUrl = null;

function _syncUrl(path, vpath, finderUrl) {
    if (finderUrl) {
        history.pushState({path: path, vpath: vpath || null}, '', finderUrl);
        return;
    }
    history.pushState({}, '', '/f/');
}

function _capturePathStateFromLink(a) {
    if (!a) return {path: null, vpath: null, finderUrl: null};
    var hxGet = a.getAttribute('hx-get') || a.getAttribute('data-hx-get');
    if (!hxGet) return {path: null, vpath: null, finderUrl: null};
    try {
        var url = new URL(hxGet, window.location.href);
        return {
            path: url.searchParams.get('path'),
            vpath: url.searchParams.get('vpath') || null,
            finderUrl: a.getAttribute('data-finder-url') || null
        };
    } catch(err) {
        return {path: null, vpath: null, finderUrl: null};
    }
}

document.addEventListener('click', function(e) {
    var a = e.target.closest('.column li a[hx-get], .column li a[data-hx-get]');
    if (!a) return;
    var state = _capturePathStateFromLink(a);
    _pendingPath = state.path;
    _pendingVpath = state.vpath;
    _pendingFinderUrl = state.finderUrl;
});

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

function scrollFinderToReveal(el, behavior) {
    var finder = document.getElementById('finder');
    if (!finder || !el) return;
    var nextLeft = Math.min(
        el.offsetLeft + el.offsetWidth - finder.clientWidth,
        el.offsetLeft
    );
    var maxLeft = Math.max(0, finder.scrollWidth - finder.clientWidth);
    nextLeft = Math.max(0, Math.min(nextLeft, maxLeft));
    if (Math.abs(nextLeft - finder.scrollLeft) < 1) return;
    finder.scrollTo({ left: nextLeft, behavior: behavior || 'smooth' });
}

document.addEventListener('htmx:afterSettle', function(e) {
    recalcColumnWidth();
    _syncDotBtn();
    _syncZoomBtn();
    if (e.detail.target) {
        if (e.detail.target.id === 'preview') {
            scrollFinderToReveal(e.detail.target, 'smooth');
        } else if (/^col-\\d+$/.test(e.detail.target.id)) {
            var newCol = document.getElementById(e.detail.target.id);
            if (newCol && newCol.classList.contains('column')) {
                scrollFinderToReveal(newCol, 'smooth');
            }
        }
    }
    if (_pendingPath || _pendingFinderUrl) {
        _syncUrl(_pendingPath, _pendingVpath, _pendingFinderUrl);
        _pendingPath = null;
        _pendingVpath = null;
        _pendingFinderUrl = null;
    }
});

window.addEventListener('popstate', function(e) {
    var path = e.state && e.state.path;
    var vpath = (e.state && e.state.vpath) || null;
    if (path) {
        _deepNavigate(path, vpath);
    } else {
        window.location.href = '/f/';
    }
});

function _deepNavigate(fullPath, vpath) {
    var restoreUrl = '/restore?path=' + encodeURIComponent(fullPath);
    if (vpath) restoreUrl += '&vpath=' + encodeURIComponent(vpath);
    fetch(restoreUrl)
        .then(function(r) { return r.text(); })
        .then(function(html) {
            var shell = document.getElementById('app-shell');
            if (shell) {
                shell.outerHTML = html;
                var newShell = document.getElementById('app-shell');
                if (newShell) htmx.process(newShell);
                recalcColumnWidth();
                initZoomButton();
                _kbApplyFocus();
                var previewEl = document.getElementById('preview');
                if (previewEl && previewEl.children.length > 0) {
                    scrollFinderToReveal(previewEl, 'auto');
                } else {
                    var cols = getColumns();
                    if (cols.length) scrollFinderToReveal(cols[cols.length - 1], 'auto');
                }
            }
        })
        .catch(function() {});
}

document.addEventListener('DOMContentLoaded', function() {
    recalcColumnWidth();
    initZoomButton();
    initDotfilesToggle();
    var params = new URLSearchParams(window.location.search);
    var deepPath = params.get('path');
    var deepVpath = params.get('vpath') || null;
    if (deepPath) {
        _deepNavigate(deepPath, deepVpath);
    }
});

document.addEventListener('click', function(e) {
    var a = e.target.closest('.column li a');
    if (!a) return;
    if (!a.hasAttribute('hx-get') && !a.hasAttribute('data-hx-get')) return;
    var li = a.closest('li');
    var ul = a.closest('ul');
    if (!li || !ul) return;
    ul.querySelectorAll('li').forEach(function(sibling) {
        sibling.classList.remove('selected');
    });
    li.classList.add('selected');
});

(function () {
  var FMTKEY_TYPE = function (ext) {
    return "vfmt_type_" + ext;
  };
  var FMTKEY_FILE = function (fpath, vpath) {
    return "vfmt_file_" + fpath + "::" + vpath;
  };

  document.addEventListener("htmx:configRequest", function (evt) {
    var elt = evt.detail.elt;
    var fpath = elt.dataset.fpath;
    var vpath = elt.dataset.vpath;
    var ext = elt.dataset.ext;
    if (fpath === undefined) return;
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

  document.addEventListener("click", function (evt) {
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

var _kbApplyFocus = function() {};

(function() {
    var _focusedColIndex = -1;

    function getColumns() {
        return Array.from(document.querySelectorAll('#finder .column'));
    }

    function visibleItems(col) {
        var showDots = document.body.classList.contains('show-dotfiles');
        return Array.from(col.querySelectorAll('li')).filter(function(li) {
            return showDots || !li.classList.contains('dotfile');
        });
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

    function focusIndex() {
        var cols = getColumns();
        if (!cols.length) return -1;
        if (_focusedColIndex >= 0 && _focusedColIndex < cols.length) return _focusedColIndex;
        return cols.length - 1;
    }

    function pageSize(col, items) {
        if (!items.length || !col.clientHeight) return 10;
        var h = items[0].offsetHeight;
        return h ? Math.max(1, Math.floor(col.clientHeight / h) - 1) : 10;
    }

    function applyFocusClasses() {
        var cols = getColumns();
        var fi = focusIndex();
        cols.forEach(function(col, i) {
            col.classList.remove('col-focused', 'col-ancestor', 'col-descendant');
            if (i < fi) col.classList.add('col-ancestor');
            else if (i === fi) col.classList.add('col-focused');
            else col.classList.add('col-descendant');
        });
    }
    _kbApplyFocus = applyFocusClasses;

    function triggerNav(sel) {
        if (!sel) return;
        var a = sel.querySelector('a');
        if (!a) return;
        if (a.getAttribute('hx-get') || a.getAttribute('data-hx-get')) {
            htmx.trigger(a, 'click');
        } else {
            a.click();
        }
    }

    var _lastColCount = 0;

    document.addEventListener('htmx:afterSettle', function() {
        var cols = getColumns();
        var isNewCol = cols.length > _lastColCount && _lastColCount > 0;
        _lastColCount = cols.length;
        _focusedColIndex = cols.length - 1;
        if (isNewCol) {
            var newCol = cols[cols.length - 1];
            if (newCol) {
                var items = visibleItems(newCol);
                if (items.length && !getSelectedLi(newCol)) {
                    selectLi(items[0]);
                }
            }
        }
        applyFocusClasses();
    });

    document.addEventListener('DOMContentLoaded', function() {
        _lastColCount = getColumns().length;
        applyFocusClasses();
    });

    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        var cols = getColumns();
        if (!cols.length) return;

        var ci = focusIndex();
        var col = cols[ci];
        var items = col ? visibleItems(col) : [];
        var sel = getSelectedLi(col);
        var selIdx = sel ? items.indexOf(sel) : -1;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (items.length) {
                    if (selIdx < 0) { selectLi(items[0]); }
                    else if (selIdx < items.length - 1) { selectLi(items[selIdx + 1]); }
                }
                break;

            case 'ArrowUp':
                e.preventDefault();
                if (items.length) {
                    if (selIdx < 0) { selectLi(items[items.length - 1]); }
                    else if (selIdx > 0) { selectLi(items[selIdx - 1]); }
                }
                break;

            case 'ArrowRight':
                e.preventDefault();
                if (sel) {
                    var a = sel.querySelector('a');
                    if (a && (a.getAttribute('hx-get') || a.getAttribute('data-hx-get'))) {
                        var hxGet = a.getAttribute('hx-get') || a.getAttribute('data-hx-get');
                        if (hxGet && hxGet.indexOf('col=') !== -1) {
                            triggerNav(sel);
                        } else if (ci >= cols.length - 1) {
                            triggerNav(sel);
                        }
                    }
                }
                break;

            case 'Enter':
                e.preventDefault();
                triggerNav(sel);
                break;

            case 'ArrowLeft':
                e.preventDefault();
                if (ci > 0) {
                    var finder = document.getElementById('finder');
                    var preview = document.getElementById('preview');
                    var el = cols[ci];
                    while (el && el !== preview) {
                        var nextEl = el.nextElementSibling;
                        el.remove();
                        el = nextEl;
                    }
                    var sentinel = document.createElement('div');
                    sentinel.id = 'col-' + ci;
                    if (finder && preview) finder.insertBefore(sentinel, preview);
                    if (preview) preview.innerHTML = '';
                    _lastColCount = ci;
                    _focusedColIndex = ci - 1;
                    var lc = cols[_focusedColIndex];
                    if (lc) {
                        var lsel = getSelectedLi(lc);
                        if (lsel) {
                            lsel.scrollIntoView({ block: 'nearest' });
                            var la = lsel.querySelector('a');
                            var leftState = _capturePathStateFromLink(la);
                            _syncUrl(leftState.path, leftState.vpath, leftState.finderUrl);
                        }
                        lc.scrollIntoView({ inline: 'nearest', block: 'nearest' });
                    }
                    applyFocusClasses();
                } else if (ci === 0) {
                    var preview = document.getElementById('preview');
                    if (preview) preview.innerHTML = '';
                    document.querySelectorAll('#finder li.selected').forEach(function(li) {
                        li.classList.remove('selected');
                    });
                    _syncUrl(null, null);
                }
                break;

            case 'Home':
                e.preventDefault();
                if (items.length) selectLi(items[0]);
                break;

            case 'End':
                e.preventDefault();
                if (items.length) selectLi(items[items.length - 1]);
                break;

            case 'PageUp':
                e.preventDefault();
                if (items.length) {
                    if (selIdx < 0) { selectLi(items[0]); }
                    else { selectLi(items[Math.max(0, selIdx - pageSize(col, items))]); }
                }
                break;

            case 'PageDown':
                e.preventDefault();
                if (items.length) {
                    if (selIdx < 0) { selectLi(items[items.length - 1]); }
                    else { selectLi(items[Math.min(items.length - 1, selIdx + pageSize(col, items))]); }
                }
                break;

            case 'Escape':
                e.preventDefault();
                document.querySelectorAll('#finder li.selected').forEach(function(li) {
                    li.classList.remove('selected');
                });
                break;
        }
    });
})();
"""
```

## Live reload script

The live-reload script is intentionally tiny. It opens an EventSource
connection to `/sse/reload` and refreshes the page whenever the server
emits a `reload` event.

```python "live reload js"
"""
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
```

## Reading order

The milestone files now form a complete LMT book for the Python source tree:

1. `01-foundation.md` – package metadata and the first runnable CLI stub
2. `02-styles.md` – CSS, theming, and formatter setup
3. `03-vfs.md` – virtual filesystem protocol and registry
4. `04-columns.md` – breadcrumb and column HTML generation
5. `05-preview.md` – Markdown rendering and file-preview dispatch
6. `06-app.md` – FastHTML application, routes, path safety, deep links
7. `07-cli.md` – full Typer + uvicorn entry point
8. `08-providers.md` – SQLite, JSON, and CSV VFS providers
9. `09-pwa.md` – manifest, service worker, and icon assets
10. `10-keyboard-js.md` – browser-side behaviour and final interactivity

To tangle the whole project into a fresh output directory:

```bash
mkdir -p _tangle_out && cd _tangle_out
~/go/bin/lmt ../lmt/01-*.md ../lmt/02-*.md ../lmt/03-*.md ../lmt/04-*.md \
  ../lmt/05-*.md ../lmt/06-*.md ../lmt/07-*.md ../lmt/08-*.md ../lmt/09-*.md \
  ../lmt/10-*.md
```

## Verification

```bash
rm -rf _tangle_out && mkdir _tangle_out && cd _tangle_out
~/go/bin/lmt ../01-*.md ../02-*.md ../03-*.md ../04-*.md ../05-*.md \
  ../06-*.md ../07-*.md ../08-*.md ../09-*.md ../10-*.md
uv sync
python -c "from pykofinder.styles import COLUMN_JS, LIVE_RELOAD_JS; print(len(COLUMN_JS), len(LIVE_RELOAD_JS))"
```
