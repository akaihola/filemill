from pathlib import Path
from urllib.parse import quote as urlquote

from fasthtml.common import A, Div, Li, NotStr, Script, Ul


def entry_icon(p: Path) -> str:
    """Return the emoji icon string for a file/directory entry."""
    if p.is_dir():
        return "📁"
    ext = p.suffix.lower()
    if ext == ".desktop":
        return "🔗"
    elif ext == ".md":
        return "📝"
    elif ext == ".pdf":
        return "📑"
    elif ext == ".docx":
        return "📄"
    elif ext == ".pptx":
        return "🎞"
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        return "🖼"
    elif ext in (".xlsx", ".xls", ".csv"):
        return "📊"
    else:
        return "📄"


def list_column(path: Path, root: Path, col_index: int) -> object:
    """Return a FastHTML Div component representing one column panel."""
    next_col = col_index + 1

    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        entries = []

    items = []
    for p in entries:
        if p.name.startswith("."):
            continue
        icon = entry_icon(p)
        encoded_path = urlquote(str(p))
        if p.is_dir():
            # Directory: load next column + clear preview via /click
            li = Li(
                A(
                    NotStr(f'<span class="icon">{icon}</span>'),
                    p.name,
                    href="#",
                    hx_get=f"/click?path={encoded_path}&col={next_col}",
                    hx_target=f"#col-{next_col}",
                    hx_swap="outerHTML",
                    title=p.name,
                ),
            )
        elif p.suffix.lower() == ".desktop":
            # .desktop link file: open the destination URL directly in a new tab
            li = Li(
                A(
                    NotStr(f'<span class="icon">{icon}</span>'),
                    p.name,
                    href=f"/open-link?path={encoded_path}",
                    target="_blank",
                    rel="noopener noreferrer",
                    title=p.name,
                ),
            )
        else:
            # File: update preview only
            li = Li(
                A(
                    NotStr(f'<span class="icon">{icon}</span>'),
                    p.name,
                    href="#",
                    hx_get=f"/click?path={encoded_path}&col={next_col}",
                    hx_target="#preview",
                    hx_swap="innerHTML",
                    title=p.name,
                ),
            )
        items.append(li)

    # Inline script to prune sibling columns to the right when this column is rendered
    prune_script = Script(
        f"""
(function(){{
    var col = document.getElementById('col-{col_index}');
    if (!col) return;
    var next = col.nextElementSibling;
    while(next && next.id !== 'preview'){{
        var toRemove = next;
        next = next.nextElementSibling;
        toRemove.remove();
    }}
    // Ensure a sentinel slot exists for the next column
    if (!document.getElementById('col-{next_col}')){{
        var sentinel = document.createElement('div');
        sentinel.id = 'col-{next_col}';
        var preview = document.getElementById('preview');
        if (preview) preview.parentNode.insertBefore(sentinel, preview);
    }}
}})();
"""
    )

    return Div(
        Ul(*items),
        prune_script,
        id=f"col-{col_index}",
        cls="column",
    )


def initial_columns(root: Path) -> object:
    """Return the initial #finder shell with first column, sentinel, and preview pane."""
    return Div(
        list_column(root, root, col_index=0),
        Div(id="col-1"),
        Div(id="preview", cls="preview-empty"),
        id="finder",
    )
