"""JSON/fragment API behind the shared Miller-columns UI.

The UI in ``ui/`` is filemill's, unchanged. It reaches a filesystem through
three small ports; this module fills the two that need a server:

    GET  /api/dir?p=<rel>      → {"entries": [{name, dir, size, mod}], "denied"}
    GET  /api/raw?p=<rel>      → the bytes, with a detected media type
    GET  /api/preview?p=<rel>  → an HTML fragment from ``preview.render_preview``
    POST /api/render           → the same, for bytes the server cannot read

``p`` is always **relative to ROOT** — that is the whole point of the new URL
contract, and it is also what makes the API safe to state: there is no request
shape that names an absolute filesystem path, so there is nothing to smuggle.
Every path still goes through ``_resolve_safe`` afterwards, because a relative
path can still climb with ``..`` and ROOT can still contain symlinks.

``POST /api/render`` is what keeps "Open local folder…" from being a downgrade.
When the browser has granted a folder the server cannot see, the UI posts the
file's bytes and gets back a fragment rendered by the same markdown-it-py,
Pygments and mammoth pipeline as everything else.
"""

from __future__ import annotations

import html as html_lib
import mimetypes
import os
import tempfile
from pathlib import Path

from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response

# Largest upload /api/render will render. Generous for text, small enough that a
# stray multi-gigabyte file cannot be turned into a memory exhaustion bug.
RENDER_MAX = 8 * 1024 * 1024


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


def dir_json(target: Path) -> JSONResponse:
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
                e = {"name": child.name, "dir": is_dir}
                if not is_dir:
                    st = child.stat()
                    e["size"] = st.st_size
                    e["mod"] = int(st.st_mtime * 1000)
                entries.append(e)
            except OSError:
                # A broken symlink is an entry that exists and cannot be
                # stat()ed; showing it as an unreadable file beats dropping it.
                entries.append({"name": child.name, "dir": False, "size": 0, "mod": 0})
    except PermissionError:
        denied = "No permission to read"
    except OSError as exc:
        denied = str(exc)
    return JSONResponse({"entries": entries, "denied": denied})


def raw_response(target: Path) -> Response:
    """Serve a file's bytes with a guessed media type."""
    if not target.is_file():
        return HTMLResponse("Not found", status_code=404)
    media, _ = mimetypes.guess_type(target.name)
    return FileResponse(str(target), media_type=media or "application/octet-stream")


def preview_fragment(target: Path, render) -> Response:
    """Render a preview body for a file the server can read."""
    if not target.is_file():
        return HTMLResponse("", status_code=404)
    try:
        return HTMLResponse(render(target))
    # One bad file must not 500 a route that was only listing a directory.
    except Exception as exc:
        return HTMLResponse(
            f'<div class="preview-error">Preview error: '
            f"{html_lib.escape(str(exc))}</div>"
        )


async def render_upload(request, render) -> Response:
    """Render posted bytes through the server-side pipeline.

    The renderers dispatch on suffix and take a path, so the upload is spooled
    to a temp file with the original name's suffix and removed straight after.
    Nothing in the response can outlive it: the providers that emit a URL to
    their source (images, PDF) are handled in the browser and never posted here.
    """
    form = await request.form()
    upload = form.get("file")
    if upload is None or not hasattr(upload, "read"):
        return HTMLResponse("", status_code=400)

    data = await upload.read()
    if len(data) > RENDER_MAX:
        return HTMLResponse(
            '<div class="preview-unsupported"><em>Too large to render '
            "remotely.</em></div>"
        )

    name = Path(getattr(upload, "filename", "") or "upload").name
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=Path(name).suffix, delete=False) as fh:
            fh.write(data)
            tmp = Path(fh.name)
        return HTMLResponse(render(tmp))
    # Same, for arbitrary uploaded bytes.
    except Exception as exc:
        return HTMLResponse(
            f'<div class="preview-error">Preview error: '
            f"{html_lib.escape(str(exc))}</div>"
        )
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
