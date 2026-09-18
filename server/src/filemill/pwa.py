"""PWA assets bundled with the package: manifest, service worker and icons.

The handlers are plain functions; ``app.py`` registers them on its router so
this module never imports the app.
"""

from pathlib import Path
from textwrap import dedent

from starlette.responses import FileResponse, HTMLResponse, Response

STATIC_DIR: Path = Path(__file__).parent / "static"

# Inline JS injected into every page to register the service worker
SW_REGISTER_JS: str = dedent("""\
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js', {scope: '/'});
    }
""")


def manifest():
    """Serve the Web App Manifest."""
    return FileResponse(
        str(STATIC_DIR / "manifest.json"), media_type="application/manifest+json"
    )


def service_worker():
    """Serve the service worker with the required Service-Worker-Allowed header."""
    data = (STATIC_DIR / "sw.js").read_bytes()
    return Response(
        content=data,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


def icon(name: str):
    """Serve a named icon from the bundled static/icons/ directory."""
    safe_name = Path(name).name  # strip any directory traversal
    icon_path = STATIC_DIR / "icons" / safe_name
    if not icon_path.exists() or not icon_path.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(str(icon_path))
