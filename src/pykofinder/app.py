import configparser
import html as html_lib
import os
from pathlib import Path
from urllib.parse import unquote as urlunquote

from fasthtml.common import (
    Body,
    Div,
    Head,
    Html,
    NotStr,
    Script,
    Style,
    Title,
    fast_app,
)
from starlette.responses import FileResponse, HTMLResponse, RedirectResponse

from pykofinder.columns import initial_columns, list_column
from pykofinder.preview import render_preview
from pykofinder.styles import APP_CSS, COLUMN_JS

# Overridden by cli.py before serve() is called; also supports env var for reload mode
ROOT: Path = Path(os.environ.get("PYKOFINDER_ROOT", str(Path.home())))

app, rt = fast_app(
    hdrs=(
        Style(APP_CSS),
        Script(COLUMN_JS),
    ),
    pico=False,
    live=False,
)


def _resolve_safe(path_str: str, root: Path | None = None) -> Path | None:
    """Resolve a user-supplied path and verify it falls within an allowed zone.

    Allowed zones
    -------------
    1. ROOT itself – any real file or directory that lives under ROOT.
    2. The resolved target of any *direct* symlink child of ROOT – lets
       directory symlinks placed in ROOT act as bookmarks whose subtrees are
       fully browsable.

    Symlinks *within* a bookmark subtree are only allowed when their resolved
    target falls inside zone 1 or the same zone-2 directory (or another
    bookmark target).  Symlinks that escape all allowed zones are denied.

    Path-traversal via ``..`` is defeated because the containment check
    operates on the fully-resolved path, not the raw string.
    """
    effective_root = root if root is not None else ROOT
    try:
        resolved_root = effective_root.resolve()
        resolved = Path(os.path.normpath(urlunquote(path_str))).resolve()

        # Zone 1: within ROOT
        try:
            resolved.relative_to(resolved_root)
            return resolved
        except ValueError:
            pass

        # Zone 2: within the resolved target of a direct symlink child of ROOT
        for child in effective_root.iterdir():
            if child.is_symlink():
                target = child.resolve()
                try:
                    resolved.relative_to(target)
                    return resolved
                except ValueError:
                    continue

        return None
    except Exception:
        return None


@rt("/")
def index():
    """Serve the full shell page."""
    return Html(
        Head(
            Title("pykofinder"),
            Style(APP_CSS),
            Script(src="https://unpkg.com/htmx.org@1.9.12"),
            Script(COLUMN_JS),
        ),
        Body(initial_columns(ROOT)),
    )


@rt("/click")
def click(path: str, col: int):
    """Handle click on a directory or file entry."""
    p = _resolve_safe(path)
    if p is None:
        error_div = Div(
            "Access denied.",
            id=f"col-{col}",
            cls="column",
            style="color:#c00; padding:1rem;",
        )
        return error_div

    if p.is_dir():
        # Return new column as main swap target; preview cleared via OOB
        new_col = list_column(p, ROOT, col_index=col)
        preview_clear = Div(id="preview", hx_swap_oob="true")
        return new_col, preview_clear
    else:
        # File: return rendered preview as main swap (target="#preview")
        try:
            preview_html = render_preview(p)
        except Exception as e:
            preview_html = f'<div class="preview-error">Preview error: {html_lib.escape(str(e))}</div>'
        # Prune columns col-{col} and beyond (left over from prior directory navigation),
        # then recreate the col-{col} sentinel so directory links in col-{col-1} still
        # have a valid hx_target when the user later clicks a directory instead of a file.
        prune_js = f"""<script>
(function(){{
    var el = document.getElementById('col-{col}');
    while (el && el.id !== 'preview') {{
        var next = el.nextElementSibling;
        el.remove();
        el = next;
    }}
    var sentinel = document.createElement('div');
    sentinel.id = 'col-{col}';
    var preview = document.getElementById('preview');
    if (preview) preview.parentNode.insertBefore(sentinel, preview);
}})();
</script>"""
        return NotStr(preview_html + prune_js)


@rt("/raw")
def raw(path: str):
    """Serve raw file bytes (used by PDF iframe)."""
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(str(p))


def _parse_desktop_url(path: Path) -> str | None:
    """Parse a .desktop file and return URL if Type=Link, else None."""
    try:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(str(path), encoding="utf-8")
        if "Desktop Entry" in cp:
            entry = cp["Desktop Entry"]
            if entry.get("Type", "").strip() == "Link":
                url = entry.get("URL", "").strip()
                return url or None
    except Exception:
        pass
    return None


@rt("/open-link")
def open_link(path: str):
    """Redirect the browser to the URL stored in a .desktop link file."""
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    url = _parse_desktop_url(p)
    if not url:
        return HTMLResponse("Not a .desktop link file", status_code=400)
    return RedirectResponse(url, status_code=302)
