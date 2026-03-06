"""JSON VFS provider for pykofinder."""

from __future__ import annotations

import html as html_lib
import json as json_module
from pathlib import Path

from pykofinder.vfs import REGISTRY, VFSEntry


class JSONProvider:
    """VFS provider for .json files – renders formatted JSON with syntax highlighting."""

    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        return []

    def render_preview(
        self,
        path: Path,
        vpath: str,
        fmt: str,
        page: int,
        limit: int,
        col: int = 0,
    ) -> str:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return '<div class="preview-unsupported"><em>Cannot read file as UTF-8.</em></div>'

        # Pretty-print if valid JSON; fall back to raw text if malformed
        try:
            data = json_module.loads(text)
            pretty = json_module.dumps(data, indent=2, ensure_ascii=False)
        except json_module.JSONDecodeError:
            pretty = text

        # Pygments syntax highlighting for JSON
        try:
            from pygments import highlight as pyg_highlight
            from pygments.formatters import HtmlFormatter as PygHtmlFormatter
            from pygments.lexers import get_lexer_by_name

            lexer = get_lexer_by_name("json")
            formatter = PygHtmlFormatter(style="friendly", nowrap=False)
            highlighted = pyg_highlight(pretty, lexer, formatter)
            return f'<div class="preview-code">{highlighted}</div>'
        except Exception:
            return f'<pre class="preview-raw">{html_lib.escape(pretty)}</pre>'

    def default_fmt(self, vpath: str) -> str:
        return "formatted"


REGISTRY.register(JSONProvider())
