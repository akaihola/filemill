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
from starlette.responses import FileResponse, HTMLResponse

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


def _resolve_safe(path_str: str) -> Path | None:
    """Resolve a user-supplied path and verify it stays within ROOT."""
    try:
        resolved_root = ROOT.resolve()
        p = Path(urlunquote(path_str)).resolve()
        if not str(p).startswith(str(resolved_root)):
            return None
        return p
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
        return NotStr(preview_html)


@rt("/raw")
def raw(path: str):
    """Serve raw file bytes (used by PDF iframe)."""
    p = _resolve_safe(path)
    if p is None or not p.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(str(p))
