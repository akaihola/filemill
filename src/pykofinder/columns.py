import html as html_lib
from pathlib import Path
from urllib.parse import quote as urlquote

from fasthtml.common import A, Div, Li, NotStr, Script, Ul


def render_breadcrumb(path: Path, root: Path, vpath: str = "") -> str:
    """Return a <nav id="breadcrumb"> HTML string for the given path under root.

    If *vpath* is provided, its slash-separated segments are appended as
    italic ``bc-virtual`` spans after the filesystem path segments.
    """
    parts: list[str] = []
    parts.append('<span class="bc-root">~</span>')

    try:
        rel = path.relative_to(root)
        segments = list(rel.parts)
    except ValueError:
        segments = []

    for seg in segments:
        parts.append('<span class="bc-sep">/</span>')
        parts.append(f'<span class="bc-seg">{html_lib.escape(seg)}</span>')

    if vpath:
        for vseg in vpath.split("/"):
            if vseg:
                parts.append('<span class="bc-sep">/</span>')
                parts.append(
                    f'<span class="bc-seg bc-virtual">{html_lib.escape(vseg)}</span>'
                )

    inner = " ".join(parts)
    toggle_btn = (
        '<button id="dotfiles-btn" class="bc-toggle"'
        ' title="Show dotfiles"'
        ' onclick="toggleDotfiles()">.*</button>'
    )
    return f'<nav id="breadcrumb">{inner}{toggle_btn}</nav>'


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
    elif ext == ".db":
        return "🗄️"
    else:
        return "📄"


def list_column(path: Path, root: Path, col_index: int) -> object:
    """Return a FastHTML Div component representing one column panel."""
    from pykofinder.vfs import (
        is_vfs_file,
    )  # lazy to avoid circular import at module level

    next_col = col_index + 1

    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        entries = []

    items = []
    for p in entries:
        is_dot = p.name.startswith(".")
        li_cls = "dotfile" if is_dot else None
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
                cls=li_cls,
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
                cls=li_cls,
            )
        elif is_vfs_file(p):
            # VFS navigable file (e.g. .db): opens a column, not a preview
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
                cls=li_cls,
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
                cls=li_cls,
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


def list_vfs_column(
    entries: list,  # list[VFSEntry]
    fs_path_encoded: str,  # URL-quoted real filesystem path (for hx-get URLs)
    fs_path_raw: str,  # raw (unquoted) filesystem path (for data-fpath)
    vpath: str,  # virtual path for this column level (for fmt-bar + data-vpath)
    col_index: int,
    show_fmt_bar: bool = False,
    active_fmt: str = "folders",
    ext: str = "",  # file extension e.g. ".db" (for data-ext + localStorage)
) -> object:
    """Return a FastHTML Div for a VFS column panel.

    Each entry is either a folder (opens a new column) or a leaf (updates preview).
    When *show_fmt_bar* is True, a format-toggle bar is rendered at the top of the
    column allowing the user to switch between Rows and Spreadsheet views.
    """
    from pykofinder.vfs import VFSEntry  # local import to avoid top-level circular

    next_col = col_index + 1
    items = []

    for entry in entries:
        if not isinstance(entry, VFSEntry) or not entry.name:
            continue
        encoded_vpath = urlquote(entry.vpath) if entry.vpath else ""

        common_data = {
            "data-fpath": fs_path_raw,
            "data-vpath": entry.vpath,
            "data-ext": ext,
        }

        if entry.is_folder:
            a = A(
                NotStr(f'<span class="icon">{entry.icon}</span>'),
                entry.name,
                href="#",
                hx_get=(
                    f"/click?path={fs_path_encoded}"
                    f"&col={next_col}"
                    f"&vpath={encoded_vpath}"
                ),
                hx_target=f"#col-{next_col}",
                hx_swap="outerHTML",
                title=entry.name,
                **common_data,
            )
        else:
            # Leaf node (row entry or info sentinel): updates preview.
            # leaf=1 signals to the server that this request targets #preview
            # so it can respond with inline content rather than sentinel+OOB.
            hx_get_val = (
                (
                    f"/click?path={fs_path_encoded}"
                    f"&col={next_col}&vpath={encoded_vpath}&leaf=1"
                )
                if entry.vpath
                else "#"
            )
            a = A(
                NotStr(f'<span class="icon">{entry.icon}</span>'),
                entry.name,
                href="#",
                hx_get=hx_get_val,
                hx_target="#preview",
                hx_swap="innerHTML",
                title=entry.name,
                **common_data,
            )
        items.append(Li(a))

    # Fmt-bar (shown only at the row-listing level when folders mode is active)
    fmt_bar_html = ""
    if show_fmt_bar:
        encoded_vpath_bar = urlquote(vpath)
        vpath_esc = html_lib.escape(vpath)
        ext_esc = html_lib.escape(ext)
        spreadsheet_btn = (
            f'<button class="fmt-btn"'
            f' data-fmt="spreadsheet"'
            f' data-fpath="{html_lib.escape(fs_path_raw)}"'
            f' data-vpath="{vpath_esc}"'
            f' data-ext="{ext_esc}"'
            f' hx-get="/click?path={fs_path_encoded}'
            f"&vpath={encoded_vpath_bar}"
            f'&col={col_index}&fmt=spreadsheet"'
            f' hx-target="#col-{col_index}" hx-swap="outerHTML">'
            f"📊 Spreadsheet</button>"
        )
        rows_btn = '<button class="fmt-btn active">📋 Rows</button>'
        fmt_bar_html = (
            f'<div class="fmt-bar col-header">{rows_btn}{spreadsheet_btn}</div>'
        )

    # Prune script (same pattern as list_column)
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
    if (!document.getElementById('col-{next_col}')){{
        var sentinel = document.createElement('div');
        sentinel.id = 'col-{next_col}';
        var preview = document.getElementById('preview');
        if (preview) preview.parentNode.insertBefore(sentinel, preview);
    }}
}})();
"""
    )

    children = []
    if fmt_bar_html:
        children.append(NotStr(fmt_bar_html))
    children.append(Ul(*items))
    children.append(prune_script)

    return Div(
        *children,
        id=f"col-{col_index}",
        cls="column",
    )


def initial_columns(root: Path) -> object:
    """Return the initial #app-shell with breadcrumb + #finder shell."""
    return Div(
        NotStr(render_breadcrumb(root, root)),
        Div(
            list_column(root, root, col_index=0),
            Div(id="col-1"),
            Div(id="preview", cls="preview-empty"),
            id="finder",
        ),
        id="app-shell",
    )
