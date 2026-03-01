from pygments.formatters import HtmlFormatter

PYGMENTS_FORMATTER = HtmlFormatter(nowrap=True)
HIGHLIGHT_CSS = HtmlFormatter().get_style_defs(".highlight")

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
    min-width: 220px;
    max-width: 220px;
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

.column li a:hover:not(.selected a) {
    background: #e8e8e8;
}

.icon {
    position: absolute;
    left: 6px;
}

#preview {
    flex: 1;
    min-width: 320px;
    overflow-y: auto;
    padding: 1rem 1.5rem;
    background: #fff;
    border-left: 1px solid #c7c7c7;
}

.preview-md {
    max-width: 800px;
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

.preview-error {
    color: #c00;
    font-style: italic;
}

.preview-empty {
    color: #999;
    font-style: italic;
    padding: 1rem;
}

"""
    + f"""
/* Pygments syntax highlighting */
.highlight {{ background: #f3f3f3; }}
{HIGHLIGHT_CSS}
"""
)

COLUMN_JS = """
document.addEventListener('htmx:afterSettle', function(e) {
    var finder = document.getElementById('finder');
    if (finder) finder.scrollLeft = finder.scrollWidth;
});
"""
