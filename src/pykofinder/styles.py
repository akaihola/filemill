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
}

#finder {
    display: flex;
    height: 100vh;
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

#zoom-btn {
    position: fixed;
    top: 0.5rem;
    right: 0.75rem;
    z-index: 100;
    background: rgba(255,255,255,0.85);
    border: 1px solid #c7c7c7;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 14px;
    cursor: pointer;
    line-height: 1.4;
    user-select: none;
}
#zoom-btn:hover {
    background: #e8e8e8;
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
"""
)

COLUMN_JS = """
function initZoomButton() {
    if (document.getElementById('zoom-btn')) return; // idempotent
    var btn = document.createElement('button');
    btn.id = 'zoom-btn';
    btn.title = 'Expand preview';
    btn.textContent = '⛶';
    btn.addEventListener('click', function() {
        var zoomed = document.body.classList.toggle('zoomed');
        btn.textContent = zoomed ? '✕' : '⛶';
        btn.title = zoomed ? 'Restore columns' : 'Expand preview';
        recalcColumnWidth();
    });
    document.body.appendChild(btn);
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

    var maxTextPx = 0;
    columns.forEach(function(col) {
        col.querySelectorAll('li a').forEach(function(a) {
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

document.addEventListener('htmx:afterSettle', function(e) {
    recalcColumnWidth();
    var finder = document.getElementById('finder');
    if (finder) finder.scrollLeft = finder.scrollWidth;
});

document.addEventListener('DOMContentLoaded', function() {
    recalcColumnWidth();
    initZoomButton();
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
"""
