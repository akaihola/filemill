"""WebVTT transcript provider."""

from __future__ import annotations

import html
import re
from pathlib import Path

from filemill.vfs import REGISTRY, VFSEntry

TIMESTAMP = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})"
    r"\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})(?:\s+.*)?$"
)
TAG = re.compile(r"<[^>]+>")
VOICE = re.compile(r"^<v(?:\s+([^>]+))?>(.*)$", re.DOTALL)


def _read(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as f:
        return f.read()


def _cue(block: str) -> tuple[str, str, str] | None:
    lines = block.splitlines()
    if not lines:
        return None
    stamp = next((i for i, line in enumerate(lines) if "-->" in line), None)
    if stamp is None:
        return None
    match = TIMESTAMP.match(lines[stamp].strip())
    if not match:
        raise ValueError("invalid cue timestamp")
    text = "\n".join(lines[stamp + 1 :]).strip()
    voice = VOICE.match(text)
    speaker = voice.group(1).strip() if voice and voice.group(1) else ""
    if voice:
        text = voice.group(2)
    text = TAG.sub("", text).strip()
    return match.group("start"), match.group("end"), speaker + "\x00" + text


def parse(text: str) -> list[tuple[str, str, str, str]]:
    source = text.removeprefix("\ufeff")
    if not re.match(r"^WEBVTT(?:\s|$)", source):
        raise ValueError("missing WEBVTT header")
    cues = []
    seen_cue = False
    pending = None
    for block in re.split(r"\r?\n\s*\r?\n", source)[1:]:
        lines = block.splitlines()
        if not lines or lines[0].strip() in {"NOTE", "STYLE", "REGION"}:
            continue
        parsed = _cue(block)
        if parsed is None and block.strip():
            if not seen_cue and all(":" in line for line in lines):
                continue
            if pending:
                continuation = TAG.sub("", block).strip()
                if continuation:
                    start, end, speaker = pending
                    cues.append((start, end, speaker, continuation))
                    pending = None
                continue
            raise ValueError("cue is missing a timestamp")
        if parsed:
            seen_cue = True
            start, end, tagged = parsed
            speaker, cue_text = tagged.split("\x00", 1)
            if cue_text:
                cues.append((start, end, speaker, cue_text))
            else:
                pending = (start, end, speaker)
    return cues


class VTTProvider:
    def handles(self, path: Path) -> bool:
        return path.suffix.lower() == ".vtt"

    def list_entries(self, path: Path, vpath: str) -> list[VFSEntry]:
        return []

    def default_fmt(self, vpath: str) -> str:
        return "transcript"

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
            source = _read(path)
            if fmt == "raw":
                return f'<pre class="preview-raw">{html.escape(source)}</pre>'
            cues = parse(source)
        except (OSError, UnicodeDecodeError) as exc:
            return f'<div class="preview-error">VTT preview error: {html.escape(str(exc))}</div>'
        except ValueError as exc:
            return f'<div class="preview-error">Malformed WebVTT: {html.escape(str(exc))}</div>'
        if not cues:
            return '<div class="preview-empty">WebVTT file has no cues.</div>'
        rows = []
        for start, end, speaker, text in cues:
            label = f"<strong>{html.escape(speaker)}:</strong> " if speaker else ""
            rows.append(
                '<p class="preview-cue">'
                f'<span class="preview-cue-time">{html.escape(start)} → {html.escape(end)}</span>'
                f'<span class="preview-cue-text">{label}{html.escape(text).replace(chr(10), "<br>")}</span>'
                "</p>"
            )
        return f'<div class="preview-transcript">{"".join(rows)}</div>'


REGISTRY.register(VTTProvider())
