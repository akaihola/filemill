"""Request handlers behind the shared Miller-columns UI.

The UI in ``ui/`` reaches a filesystem through three small ports. ``app.py``
routes these requests to this module:

    GET    /api/dir?p=<rel>&v=<vpath>     → {"entries": [{name, dir, size, mod,
                                             …}], "denied"}
    GET    /api/raw?p=<rel>&v=<vpath>     → the bytes, with a detected media type
    GET    /api/preview?p=<rel>&v=<vpath> → HTML for RST and archive members
    GET    /api/search?q=<text>&p=<rel>   → content matches from ripgrep
    POST   /api/save?p=<rel>              → overwrite the file with the body
    DELETE /api/delete?p=<rel>            → remove the file or folder

``v`` is optional and names a path inside a virtual filesystem.

``p`` is always **relative to ROOT** — that is the whole point of the new URL
contract, and it is also what makes the API safe to state: there is no request
shape that names an absolute filesystem path, so there is nothing to smuggle.
Every path still goes through ``paths.resolve_safe`` afterwards, because a relative
path can still climb with ``..`` and ROOT can still contain symlinks.

When the browser has granted a folder the server cannot see, the UI renders the
file in the browser through the same PreviewRich provider as the static edition.
"""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import mimetypes
import os
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import cast

from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response

from filemill.preview import render_preview, valid_text
from filemill.vfs import (
    REGISTRY,
    VFSMember,
    VFSMemberProvider,
    classify_path,
    entry_order_key,
)

# Largest body /api/save will write.
RENDER_MAX = 8 * 1024 * 1024
SEARCH_QUERY_MAX = 200
SEARCH_MATCH_MAX = 100
# The demo proxy allows more than the old two-second subprocess limit.
SEARCH_TIMEOUT = 10


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
    the caller's ``paths.resolve_safe``; this is the guard that has to come first.
    """
    rel = (rel or "").strip()
    if rel.startswith(("/", "\\")):
        return None
    if os.path.isabs(rel) or (len(rel) > 1 and rel[1] == ":"):
        return None
    return root / rel if rel else root


def dir_json(target: Path, keep: Callable[[Path], bool] | None = None) -> JSONResponse:
    """List a directory in the shape the UI's HTTP adapter expects.

    Sizes and mtimes ride along with the listing. The File System Access API
    needs a separate call per file for those, which is why the static build only
    fetches them on preview or for a size or time sort — here they are free, so
    the preview pane is
    populated before its provider has said anything.

    *keep*, when given, decides which children are listed at all.
    """
    entries, denied = [], None
    try:
        for child in target.iterdir():
            if keep is not None and not keep(child):
                continue
            try:
                is_dir = child.is_dir()
                e = {
                    "name": child.name,
                    "dir": is_dir,
                    "ordered": True,
                    "abs": child.resolve().as_posix(),
                }
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
                        "abs": child.absolute().as_posix(),
                    }
                )
    except PermissionError:
        denied = "No permission to read"
    except OSError as exc:
        denied = str(exc)
    entries.sort(
        key=lambda e: entry_order_key(cast(str, e["name"]), cast(bool, e["dir"]))
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
        return (
            bool(provider.list_entries(path, ""))
            and classify_path(path, provider=True).kind == "vfs"
        )
    except Exception:
        return False


def vfs_dir_json(
    target: Path, vpath: str, keep: Callable[[str], bool] | None = None
) -> JSONResponse:
    """List one level inside a virtual filesystem.

    The entries carry their own `vpath`, which is how the client knows to keep
    the real path and descend virtually instead of joining a name onto it.
    *keep*, when given, decides by `vpath` which entries are listed at all.
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
            "abs": (target / e.name).resolve().as_posix(),
            "icon": e.icon,
            "ordered": e.ordered,
            "size": 0,
            "mod": 0,
            **({"record": e.record} if e.record is not None else {}),
        }
        for e in listed
        if keep is None or keep(e.vpath)
    ]
    return JSONResponse({"entries": entries, "denied": None})


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
        # JSON, JSONL, CSV, Markdown and reStructuredText are browsed on the client
        # (ui/adapters/vfs-*.js); their rows and sections still need a URL that
        # reloads. Whether the virtual part exists is the client's to decide.
        browser_json = real.is_file() and real.suffix.lower() in {".json", ".jsonc"}
        if (
            REGISTRY.get(real) is not None
            or browser_json
            or classify_path(real).preview
            in {
                "jsonl",
                "csv",
                "md",
                "markdown",
                "rst",
            }
        ):
            return "/".join(parts[:i]), "/".join(parts[i:])
        return None
    return ("", "") if not parts else None


def file_revision(data: bytes) -> str:
    """A strong ETag for a byte snapshot, independent of filesystem timestamps."""
    return f'"{hashlib.sha256(data).hexdigest()}"'


def raw_response(target: Path, *, snapshot: bool = False) -> Response:
    """With snapshot=True, bind bounded editor bytes to a strong ETag.

    Ordinary downloads retain FileResponse streaming and Range support. Large
    snapshots also stream, but exceed the editor limit and carry no edit revision.
    """
    if not target.is_file():
        return HTMLResponse("Not found", status_code=404)
    media, _ = mimetypes.guess_type(target.name)
    if not snapshot:
        return FileResponse(
            str(target),
            media_type=media or "application/octet-stream",
            headers={"Cache-Control": "no-store"},
        )
    with target.open("rb") as source:
        before = os.fstat(source.fileno())
        if before.st_size <= RENDER_MAX:
            data = source.read(RENDER_MAX + 1)
            after = os.fstat(source.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                return JSONResponse(
                    {"error": "Conflict: file changed during read"}, status_code=409
                )
            if len(data) <= RENDER_MAX:
                return Response(
                    data,
                    media_type=media or "application/octet-stream",
                    headers={"Cache-Control": "no-store", "ETag": file_revision(data)},
                )
    return FileResponse(
        str(target),
        media_type=media or "application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


def member_of(target: Path, vpath: str) -> VFSMember | None:
    """The file member *vpath* names inside *target*, when its provider has
    bytes to give — an archive does, a database does not."""
    provider = REGISTRY.get(target)
    if not isinstance(provider, VFSMemberProvider):
        return None
    return provider.member(target, vpath)


def member_raw_response(target: Path, vpath: str) -> Response:
    """Serve a member's bytes with a media type guessed from its own name."""
    member = member_of(target, vpath)
    if member is None:
        return HTMLResponse("Not found", status_code=404)
    if member.data is None:
        return HTMLResponse("Too large", status_code=413)
    media, _ = mimetypes.guess_type(member.name)
    return Response(
        member.data,
        media_type=media or "application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


def member_preview_response(target: Path, vpath: str, preview_url: str) -> Response:
    """Render a member the way the same file would render on disk.

    Only the kinds the server renders for a file on disk arrive here: the
    browser keeps Markdown, .docx and .pptx members for its own renderers
    (ui/adapters/app-http.js), reading their bytes through the raw route.
    The renderers read paths, so the bytes go to a temporary file under the
    member's own name — the suffix is what picks the renderer — and are gone
    before the response leaves. *preview_url* is where an image or PDF member
    fetches itself from: the raw route with the same vpath.
    """
    member = member_of(target, vpath)
    if member is None:
        return HTMLResponse("Not found", status_code=404)
    if member.data is None:
        html = (
            '<div class="preview-unsupported"><em>Too large to preview '
            f"({member.size:,} bytes inside the archive).</em></div>"
        )
    else:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / member.name
            path.write_bytes(member.data)
            html = render_preview(path, preview_url=preview_url)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


# shortcut: serialize saves in this process; use a shared lock if multi-worker
# serving is introduced. External writers require the final revision recheck.
_save_lock = threading.Lock()


def save_file(target: Path, data: bytes, expected: str | None = None) -> Response:
    """Replace an existing text file after checking its read revision.

    Resolve symlinks to the authorized target; keep the symlink itself. Replace
    one directory entry, so other hard links retain the old inode and bytes.
    Preserve uid, gid and permission bits, or fail before replacement. ACLs and
    extended attributes are not copied. A same-directory temporary file is
    flushed and fsynced before rename. All pre-rename failures retain old bytes.
    Filemill saves serialize; unrelated writers cannot be locked by this API.
    """
    with _save_lock:
        temporary = None
        try:
            target = target.resolve()
            if not target.is_file():
                return JSONResponse({"error": "Not found"}, status_code=404)
            if len(data) > RENDER_MAX:
                return JSONResponse({"error": "Too large"}, status_code=413)
            with target.open("rb") as source:
                current_data = source.read(RENDER_MAX + 1)
            if valid_text(current_data) is None or valid_text(data) is None:
                return JSONResponse({"error": "Not editable"}, status_code=415)
            if not expected:
                return JSONResponse(
                    {"error": "Read revision required"}, status_code=428
                )
            original = target.stat()
            if expected != file_revision(current_data):
                return JSONResponse(
                    {"error": "Conflict: file changed; draft kept"}, status_code=409
                )
            # Retain the existing file's write-permission check, without truncation.
            fd = os.open(target, os.O_WRONLY)
            os.close(fd)
            with tempfile.NamedTemporaryFile(
                dir=target.parent, prefix=".filemill-", delete=False
            ) as output:
                temporary = Path(output.name)
                output.write(data)
                output.flush()
                current = os.fstat(output.fileno())
                if (current.st_uid, current.st_gid) != (
                    original.st_uid,
                    original.st_gid,
                ):
                    os.fchown(output.fileno(), original.st_uid, original.st_gid)
                os.fchmod(output.fileno(), original.st_mode & 0o7777)
                os.fsync(output.fileno())
                st = os.fstat(output.fileno())
            with target.open("rb") as source:
                latest = source.read(RENDER_MAX + 1)
            if expected != file_revision(latest):
                return JSONResponse(
                    {"error": "Conflict: file changed; draft kept"}, status_code=409
                )
            # Prepare the reply before the commit point: no fallible metadata
            # lookup may turn a successful replacement into a reported failure.
            response = JSONResponse(
                {
                    "size": st.st_size,
                    "mod": int(st.st_mtime * 1000),
                    "revision": file_revision(data),
                },
                headers={"ETag": file_revision(data)},
            )
            os.replace(temporary, target)
            temporary = None
            return response
        except OSError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


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
