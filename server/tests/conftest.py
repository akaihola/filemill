import sqlite3

import pytest
from pathlib import Path
from starlette.testclient import TestClient

import filemill.app as app_module


@pytest.fixture()
def tmp_root(tmp_path: Path):
    """Populate a temp directory tree and point app.ROOT at it for the duration of the test."""
    (tmp_path / "subdir").mkdir()
    (tmp_path / "readme.md").write_text("# Hello\n**world**\n")
    (tmp_path / ".hidden").write_text("hidden")
    (tmp_path / "link.desktop").write_text(
        "[Desktop Entry]\nType=Link\nURL=https://example.com\nName=Example\n"
    )
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / "doc.pdf").write_bytes(b"%PDF-1.4")
    original = app_module.ROOT
    app_module.ROOT = tmp_path
    yield tmp_path
    app_module.ROOT = original


@pytest.fixture()
def client(tmp_root: Path):
    """Return a Starlette TestClient with ROOT pointing at tmp_root."""
    return TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture()
def db_root(tmp_path: Path):
    """tmp_root with a SQLite .db file containing a users table (5 rows)."""
    (tmp_path / "subdir").mkdir()
    db = tmp_path / "sample.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, bio TEXT)")
    for i in range(1, 6):
        con.execute("INSERT INTO users VALUES (?, ?, ?)", (i, f"User{i}", f"Bio{i}"))
    con.commit()
    con.close()
    original = app_module.ROOT
    app_module.ROOT = tmp_path
    yield tmp_path
    app_module.ROOT = original


@pytest.fixture()
def db_client(db_root: Path):
    return TestClient(app_module.app, raise_server_exceptions=False)
