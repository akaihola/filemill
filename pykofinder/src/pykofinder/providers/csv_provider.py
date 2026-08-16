"""CSV VFS provider stub for pykofinder."""

from __future__ import annotations

from pathlib import Path

from pykofinder.vfs import REGISTRY, VFSEntry


class CSVProvider:
    """Stub VFS provider for .csv files (spreadsheet vs raw, not yet implemented)."""

    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".csv"

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
        return (
            '<div class="preview-unsupported">'
            "<em>CSV VFS not yet implemented.</em></div>"
        )

    def default_fmt(self, vpath: str) -> str:
        return "spreadsheet"


REGISTRY.register(CSVProvider())
