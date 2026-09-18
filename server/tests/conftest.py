import sqlite3
from pathlib import Path

import pytest
from starlette.testclient import TestClient

import filemill.app as app_module


@pytest.fixture()
def tmp_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Populate a temp directory tree and configure the app root for the test."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "readme.md").write_text("# Hello\n**world**\n")
    (tmp_path / ".hidden").write_text("hidden")
    (tmp_path / "link.desktop").write_text(
        "[Desktop Entry]\nType=Link\nURL=https://example.com\nName=Example\n"
    )
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(app_module.app.state, "root", tmp_path)
    yield tmp_path


@pytest.fixture()
def client(tmp_root: Path):
    """Return a Starlette TestClient configured for tmp_root."""
    return TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture()
def db_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """tmp_root with a SQLite .db file containing a users table (5 rows)."""
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
    return TestClient(app_module.app, raise_server_exceptions=False)
