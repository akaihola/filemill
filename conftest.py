import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def bundle(request):
    name = "index-dev.html" if request.config.getoption("--dev") else "index.html"
    return Path(__file__).parent / "static" / name


@pytest.fixture
def fake_handle(request):
    return request.module.FAKE


@pytest.fixture
def opfs_root():
    return "navigator.storage.getDirectory()"


@pytest.fixture
def playwright():
    return pytest.importorskip("playwright.sync_api").sync_playwright


@pytest.fixture()
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from filemill import app as app_module

    (tmp_path / "subdir").mkdir()
    (tmp_path / "readme.md").write_text("# Hello\n**world**\n")
    (tmp_path / ".hidden").write_text("hidden")
    (tmp_path / "link.desktop").write_text("[Desktop Entry]\nType=Link\nURL=https://example.com\nName=Example\n")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(app_module.app.state, "root", tmp_path)
    yield tmp_path


@pytest.fixture()
def client(tmp_root: Path):
    from filemill.app import app
    from starlette.testclient import TestClient

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
    from filemill.app import app
    from starlette.testclient import TestClient

    return TestClient(app, raise_server_exceptions=False)


def pytest_addoption(parser):
    parser.addoption("--dev", action="store_true", help="test modular static sources")
