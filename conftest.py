import functools
import http.server
import sqlite3
import threading
from pathlib import Path

import pytest


@pytest.fixture
def bundle(request):
    name = "index-dev.html" if request.config.getoption("--dev") else "index.html"
    return Path(__file__).parent / "static" / name


@pytest.fixture
def static_origin():
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(Path(__file__).parent)
    )
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()


@pytest.fixture
def fake_handle(request):
    return request.module.FAKE


@pytest.fixture
def opfs_root():
    return "navigator.storage.getDirectory()"


@pytest.fixture
def playwright():
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with sync_playwright() as p:
        yield p


@pytest.fixture
def async_playwright():
    return pytest.importorskip("playwright.async_api")


@pytest.fixture(autouse=True)
def reset_checks(request):
    for name in ("passed", "failed"):
        results = getattr(request.module, name, None)
        if isinstance(results, list):
            results.clear()


@pytest.fixture()
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from filemill import app as app_module

    (tmp_path / "subdir").mkdir()
    (tmp_path / "readme.md").write_text("# Hello\n**world**\n")
    (tmp_path / ".hidden").write_text("hidden")
    (tmp_path / "link.desktop").write_text("[Desktop Entry]\nType=Link\nURL=https://example.com\nName=Example\n")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / "image.jpg").write_bytes(b"\xff\xd8\xff")
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(app_module.app.state, "root", tmp_path)
    yield tmp_path


@pytest.fixture()
def client(tmp_root: Path):
    from starlette.testclient import TestClient

    from filemill.app import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def db_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from filemill import app as app_module

    (tmp_path / "subdir").mkdir()
    db = tmp_path / "sample.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, bio TEXT)")
    for i in range(1, 6):
        con.execute("INSERT INTO users VALUES (?, ?, ?)", (i, f"User{i}", f"Bio{i}"))
    con.commit()
    con.close()
    monkeypatch.setattr(app_module.app.state, "root", tmp_path)
    yield tmp_path


@pytest.fixture()
def db_client(db_root: Path):
    from starlette.testclient import TestClient

    from filemill.app import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def archive_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A root with a .tar.zst and a .zip, the same members in each."""
    import io
    import tarfile
    import zipfile

    from filemill import app as app_module
    from filemill.providers.archive import zstd_compress

    members = {
        "top.txt": b"top level\n",
        "docs/readme.md": b"# Hello from the archive\n",
        "docs/pic.png": b"\x89PNG\r\n",
        "src/app.py": b"print('hi')\n",
    }
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    (tmp_path / "demo.tar.zst").write_bytes(zstd_compress(buf.getvalue()))
    with zipfile.ZipFile(tmp_path / "demo.zip", "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    (tmp_path / "empty.tar").write_bytes(b"\0" * 1024)
    monkeypatch.setattr(app_module.app.state, "root", tmp_path)
    yield tmp_path


@pytest.fixture()
def archive_client(archive_root: Path):
    from starlette.testclient import TestClient

    from filemill.app import app

    return TestClient(app, raise_server_exceptions=False)


def pytest_addoption(parser):
    parser.addoption("--native", action="store_true", help="test the native WebView host")
    parser.addoption("--dev", action="store_true", help="test modular static sources")
