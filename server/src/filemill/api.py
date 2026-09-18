"""JSON/fragment API behind the shared Miller-columns UI.

The UI in ``ui/`` is filemill's, unchanged. It reaches a filesystem through
three small ports; this module fills the two that need a server:

    GET  /api/dir?p=<rel>      → {"entries": [{name, dir, size, mod}], "denied"}
    GET  /api/raw?p=<rel>      → the bytes, with a detected media type
    GET  /api/preview?p=<rel>  → an HTML fragment from ``preview.render_preview``
    POST /api/save?p=<rel>     → overwrite the file with the request body

``p`` is always **relative to ROOT** — that is the whole point of the new URL
contract, and it is also what makes the API safe to state: there is no request
shape that names an absolute filesystem path, so there is nothing to smuggle.
Every path still goes through ``_resolve_safe`` afterwards, because a relative
path can still climb with ``..`` and ROOT can still contain symlinks.

When the browser has granted a folder the server cannot see, the UI renders the
file in the browser through the same PreviewRich provider as the static edition.
"""

from __future__ import annotations

import html as html_lib
import json
import math
import mimetypes
import os
import shutil
import subprocess
from pathlib import Path

from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response

from filemill.preview import read_text, valid_text
from filemill.vfs import REGISTRY, classify_path, entry_order_key

# Largest body /api/save will write.
RENDER_MAX = 8 * 1024 * 1024
SEARCH_QUERY_MAX = 200
SEARCH_MATCH_MAX = 100
# The demo proxy allows more than the old two-second subprocess limit.
SEARCH_TIMEOUT = 10
DIR_PAGE_SIZE = 500


class SearchError(Exception):
    """A search could not be completed by the server."""


def search_root(root: Path, query: str, focused: str = "") -> list[dict]:
    """Find bounded fixed-string matches below the focused directory."""
    query = query.strip()
    if not query:
        raise SearchError("Search query is empty")
    if len(query) > SEARCH_QUERY_MAX:
        raise SearchError(f"Search query is limited to {SEARCH_QUERY_MAX} characters")
    try:
        result = subprocess.run(
            [
                "rg",
                "--json",
                "--fixed-strings",
                "--line-number",
                "--column",
                "--max-count",
                "1",
                "--max-columns",
                "240",
                "--max-columns-preview",
                "--glob",
                "!.git/**",
                "--glob",
                "!node_modules/**",
                "--glob",
                "!.venv/**",
                "--glob",
                "!__pycache__/**",
                "--glob",
                "!.cache/**",
                "--",
                query,
                focused or ".",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=SEARCH_TIMEOUT,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SearchError("Search is unavailable: ripgrep is not installed") from exc
    except subprocess.TimeoutExpired as exc:
        raise SearchError("Search timed out") from exc
    if result.returncode not in (0, 1):
        raise SearchError("Search failed")
    matches = []
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "match":
            continue
        data = event["data"]
        path = data["path"]["text"]
        matches.append(
            {
                "path": path.removeprefix("./"),
                "line": data["line_number"],
                "column": data["submatches"][0]["start"] + 1,
                "context": data["lines"]["text"].rstrip("\n"),
            }
        )
        if len(matches) == SEARCH_MATCH_MAX:
            break
    return matches


def rel_to_abs(rel: str, root: Path) -> Path | None:
    """Resolve a root-relative request path, or None if it is not addressable.

    Absolute inputs are rejected outright rather than normalised: ``Path("/a") /
    "/etc/passwd"`` is ``/etc/passwd``, so treating an absolute ``p`` as
    root-relative would hand out the whole disk. Containment is still checked by
    the caller's ``_resolve_safe``; this is the guard that has to come first.
    """
    rel = (rel or "").strip()
    if rel.startswith(("/", "\\")):
        return None
    if os.path.isabs(rel) or (len(rel) > 1 and rel[1] == ":"):
        return None
    return root / rel if rel else root


def dir_json(target: Path, page: int = 1) -> JSONResponse:
    """List a directory in the shape the UI's HTTP adapter expects.

    Sizes and mtimes ride along with the listing. The File System Access API
    needs a separate call per file for those, which is why the static build only
    fetches them on preview — here they are free, so the preview pane is
    populated before its provider has said anything.
    """
    entries, denied = [], None
    try:
        for child in target.iterdir():
            try:
                is_dir = child.is_dir()
                e = {"name": child.name, "dir": is_dir, "ordered": True}
                if not is_dir:
                    st = child.stat()
                    e["size"] = st.st_size
                    e["mod"] = int(st.st_mtime * 1000)
                    if _opens_as_folder(child):
                        e["dir"] = True
                entries.append(e)
            except OSError:
                # A broken symlink is an entry that exists and cannot be
                # stat()ed; showing it as an unreadable file beats dropping it.
                entries.append(
                    {
                        "name": child.name,
                        "dir": False,
                        "size": 0,
                        "mod": 0,
                        "ordered": True,
                    }
                )
    except PermissionError:
        denied = "No permission to read"
    except OSError as exc:
        denied = str(exc)
    entries.sort(key=lambda e: entry_order_key(e["name"], e["dir"]))
    total = len(entries)
    if total > DIR_PAGE_SIZE:
        pages = math.ceil(total / DIR_PAGE_SIZE)
        page = min(page, pages)
        entries = entries[(page - 1) * DIR_PAGE_SIZE : page * DIR_PAGE_SIZE]
        return JSONResponse(
            {
                "entries": entries,
                "denied": denied,
                "page": page,
                "pages": pages,
                "total": total,
            }
        )
    return JSONResponse({"entries": entries, "denied": denied})


def _opens_as_folder(path: Path) -> bool:
    """True when a *file* should open a column instead of a preview.

    A `.db` is a directory of tables as far as the UI is concerned. Asking the
    provider rather than trusting the extension keeps a provider that yields
    nothing — the CSV stub — a plain file with a preview, instead of a folder
    that is always empty.
    """
    provider = REGISTRY.get(path)
    if provider is None:
        return False
    try:
        return bool(provider.list_entries(path, "")) and classify_path(
            path, provider=True
        ).kind == "vfs"
    except Exception:
        return False


def vfs_dir_json(target: Path, vpath: str, page: int = 1) -> JSONResponse:
    """List one level inside a virtual filesystem.

    The entries carry their own `vpath`, which is how the client knows to keep
    the real path and descend virtually instead of joining a name onto it.
    """
    provider = REGISTRY.get(target)
    if provider is None:
        return JSONResponse({"entries": [], "denied": "Not a virtual filesystem"}, 404)
    try:
        listed = provider.list_entries(target, vpath)
    except Exception as exc:
        return JSONResponse({"entries": [], "denied": str(exc)})
    entries = [
        {
            "name": e.name,
            "dir": e.is_folder,
            "vpath": e.vpath,
            "icon": e.icon,
            "ordered": e.ordered,
            "size": 0,
            "mod": 0,
            **({"record": e.record} if e.record is not None else {}),
        }
        for e in listed
    ]
    total = len(entries)
    pagination = {}
    if total > DIR_PAGE_SIZE:
        pages = math.ceil(total / DIR_PAGE_SIZE)
        page = min(page, pages)
        entries = entries[(page - 1) * DIR_PAGE_SIZE : page * DIR_PAGE_SIZE]
        pagination = {"page": page, "pages": pages, "total": total}
    return JSONResponse(
        {
            "entries": entries,
            "denied": None,
            **pagination,
        }
    )


def vfs_preview(target: Path, vpath: str, fmt: str = "") -> Response:
    """Render the preview for one virtual entry."""
    provider = REGISTRY.get(target)
    render = getattr(provider, "render_preview", None)
    default_fmt = getattr(provider, "default_fmt", None)
    if render is None or default_fmt is None:
        return HTMLResponse("", status_code=404)
    try:
        return HTMLResponse(
            render(target, vpath, fmt or default_fmt(vpath), page=1, limit=1000),
            headers={"Cache-Control": "no-store"},
        )
    except Exception as exc:
        return HTMLResponse(
            f'<div class="preview-error">Preview error: '
            f"{html_lib.escape(str(exc))}</div>",
            headers={"Cache-Control": "no-store"},
        )


def split_vfs(rel: str, root: Path, resolve) -> tuple[str, str] | None:
    """Split a root-relative path into its real part and its virtual remainder.

    `sample.db/users/42` is one URL but two things: a file on disk and a key
    inside it. Only the address bar ever sees them joined — the API keeps them
    apart — so this is what a deep link has to be validated through.

    Returns None when the real part does not resolve safely.
    """
    parts = [p for p in rel.split("/") if p]
    for i in range(len(parts), 0, -1):
        candidate = rel_to_abs("/".join(parts[:i]), root)
        if candidate is None:
            return None
        real = resolve(str(candidate))
        if real is None or not real.exists():
            continue
        if i == len(parts):
            return "/".join(parts[:i]), ""
        # .jsonl is browsed on the client (ui/core/jsonl.js); its rows still
        # need a URL that reloads.
        if REGISTRY.get(real) is not None or classify_path(real).preview in {"jsonl", "csv"}:
            return "/".join(parts[:i]), "/".join(parts[i:])
        return None
    return ("", "") if not parts else None


def raw_response(target: Path) -> Response:
    """Serve a file's bytes with a guessed media type."""
    if not target.is_file():
        return HTMLResponse("Not found", status_code=404)
    media, _ = mimetypes.guess_type(target.name)
    return FileResponse(
        str(target),
        media_type=media or "application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


def save_file(target: Path, data: bytes) -> Response:
    """Overwrite an existing file with the posted bytes.

    Only a file that already exists is writable: edit mode edits what it
    previews, so there is no create, no mkdir, and no new name to validate.
    """
    if not target.is_file():
        return JSONResponse({"error": "Not found"}, status_code=404)
    if len(data) > RENDER_MAX:
        return JSONResponse({"error": "Too large"}, status_code=413)
    if read_text(target) is None or valid_text(data) is None:
        return JSONResponse({"error": "Not editable"}, status_code=415)
    try:
        target.write_bytes(data)
    except OSError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    st = target.stat()
    return JSONResponse({"size": st.st_size, "mod": int(st.st_mtime * 1000)})


def delete_file(target: Path) -> Response:
    """Delete one existing real file or directory."""
    if not target.exists() and not target.is_symlink():
        return JSONResponse({"error": "Not found"}, status_code=404)
    try:
        if target.is_symlink() or not target.is_dir():
            target.unlink()
        else:
            shutil.rmtree(target)
    except OSError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    return JSONResponse({"deleted": True})


def preview_fragment(target: Path, render) -> Response:
    """Render a preview body for a file the server can read."""
    if not target.is_file():
        return HTMLResponse("", status_code=404)
    try:
        return HTMLResponse(render(target), headers={"Cache-Control": "no-store"})
    # One bad file must not 500 a route that was only listing a directory.
    except Exception as exc:
        return HTMLResponse(
            f'<div class="preview-error">Preview error: '
            f"{html_lib.escape(str(exc))}</div>",
            headers={"Cache-Control": "no-store"},
        )
