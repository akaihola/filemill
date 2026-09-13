from pygments.formatters import HtmlFormatter

HIGHLIGHT_CSS = HtmlFormatter(style="friendly").get_style_defs(".highlight")

APP_CSS = (
    """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
    font-size: 13px;
    background: #f0f0f0;
    margin: 0;
    overflow: hidden;
    height: 100vh;
    height: 100dvh;
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

.preview-html iframe {
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

"""
)


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
