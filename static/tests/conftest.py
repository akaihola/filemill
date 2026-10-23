"""Static browser fixtures, isolated per test in bundle and development modes."""

import functools
import http.server
import threading
from pathlib import Path

import pytest
import pytest_asyncio

ROOT = Path(__file__).parents[2]


@pytest.fixture
def bundle(request):
    name = "index-dev.html" if request.config.getoption("--dev") else "index.html"
    return ROOT / "static" / name


@pytest.fixture
def fake_handle(request):
    return request.module.FAKE


@pytest.fixture
def static_origin(request):
    stubs = getattr(request.module, "STUBS", {})

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            name = self.path.rsplit("/", 1)[-1]
            if self.path.startswith("/__stub/") and name in stubs:
                body = stubs[name].encode()
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/css" if name.endswith(".css") else "application/javascript",
                )
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                super().do_GET()

    handler = functools.partial(Handler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


@pytest.fixture
def base(static_origin, bundle):
    return f"{static_origin}/static/{bundle.name}"


@pytest_asyncio.fixture
async def browser(async_browser):
    return async_browser


@pytest_asyncio.fixture
async def page(browser, bundle, fake_handle, request):
    page = await browser.new_page(viewport={"width": 1500, "height": 900})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    is_ui = request.module.__name__.endswith("test_ui")
    if is_ui or request.module.__name__.endswith("test_url"):
        page.on(
            "console", lambda m: errors.append(m.text) if m.type == "error" else None
        )
    if request.module.__name__.endswith("test_url"):
        page.on(
            "response",
            lambda r: (
                errors.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 else None
            ),
        )
    await page.goto(bundle.as_uri())
    await page.evaluate("localStorage.setItem('filemill.rich','off')")
    await page.evaluate(fake_handle)
    if not is_ui:
        await page.route("https://esm.sh/**", lambda route: route.abort())
        await page.route("https://cdn.jsdelivr.net/**", lambda route: route.abort())
    yield page
    assert not errors, errors


@pytest_asyncio.fixture
async def requests(page):
    urls = []
    page.on("request", lambda r: urls.append(r.url))
    return urls


@pytest_asyncio.fixture
async def opfs_root(page, base, request):
    await request.module.open_at(page, base)
    await page.evaluate(request.module.OPFS_BUILD, 3000)
    handle = await page.evaluate_handle("navigator.storage.getDirectory()")
    try:
        yield handle
    finally:
        await handle.evaluate("root => root.removeEntry('bench', {recursive: true})")
        await handle.dispose()
