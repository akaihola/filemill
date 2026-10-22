"""WebVTT transcript provider.

It claims ``.vtt`` files but lists no entries, so a transcript stays a plain
file. The browser renders transcripts (``ui/core/renderers.js``). No route
needs a Python transcript renderer.
"""

from __future__ import annotations

from pathlib import Path

from filemill.vfs import REGISTRY, VFSEntry


class VTTProvider:
    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".vtt"

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        return []


REGISTRY.register(VTTProvider())
