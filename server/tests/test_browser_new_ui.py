"""The shared Miller-columns UI, driven in a real browser against this server.

This is the test that actually proves the sharing works: `ui/` is filemill's
frontend byte-for-byte, and here it is browsing a real directory tree over
`/api/dir` and `/api/preview` with nothing about `core/` changed.

Unlike the HTMX suite, nothing here reaches the network. The app serves every
asset, `test_nothing_is_fetched_from_a_cdn` holds it to that, and so these 27
tests pass in an offline sandbox.

    timeout 600 uv run pytest tests/test_browser_new_ui.py

No `--with`: `uv sync` installs the Playwright `pyproject.toml` pins, and that is
the one whose driver matches the browsers at `$PLAYWRIGHT_BROWSERS_PATH`. See
CONTRIBUTING.md, "Do Not Pass `--with playwright==…`".
"""

from __future__ import annotations

import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.integration


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def ui_root(tmp_path: Path) -> Path:
    """A tree with enough shape to exercise columns, previews and deep links."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "deep").mkdir()
    (tmp_path / "notes" / "deep" / "leaf.md").write_text("# Leaf\n**bold** text\n")
    (tmp_path / "notes" / "plain.txt").write_text("hello")
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "sample.py").write_text("def f():\n    return 1\n")
    (tmp_path / "empty").mkdir()
    (tmp_path / "README.md").write_text("# Readme\n")
    (tmp_path / ".hidden").write_text("h")
    con = sqlite3.connect(str(tmp_path / "sample.db"))
    con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    for i in range(1, 4):
        con.execute("INSERT INTO users VALUES (?, ?)", (i, f"User{i}"))
    con.commit()
    con.close()
    return tmp_path


@pytest.fixture()
def server(ui_root: Path, tmp_path_factory):
    """Run the real app in a subprocess — TestClient cannot serve a browser."""
    port = _free_port()
    # Keep stderr: when this does not come up, its traceback is the only thing
    # that says why, and discarding it turns every cause into "did not start".
    log = tmp_path_factory.mktemp("server") / "stderr.log"
    with log.open("wb") as fh:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import uvicorn, filemill.app as a; "
                    f"uvicorn.run(a.app, host='127.0.0.1', port={port}, "
                    "log_level='error')"
                ),
            ],
            env={"FILEMILL_ROOT": str(ui_root), "PATH": "/usr/bin:/bin"},
            stdout=subprocess.DEVNULL,
            stderr=fh,
        )
    base = f"http://127.0.0.1:{port}"
    # Importing FastHTML takes a couple of seconds, and every test in this
    # module pays it in a fresh process — on a loaded machine ten seconds was
    # not enough, which read as a flake.
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            pytest.fail(f"server exited early:\n{log.read_text()}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail(f"server did not start within 60s:\n{log.read_text()}")
    try:
        yield base
    finally:
        proc.terminate()
        proc.wait(timeout=10)


class Harness:
    """A Page plus the two things every test here needs beside it.

    Attribute access falls through to the page, so the tests read as if they
    were driving it directly.
    """

    def __init__(self, pg, base: str):
        self._pg = pg
        self.base = base
        self.errors: list[str] = []
        pg.on("pageerror", lambda e: self.errors.append(str(e)))
        pg.on(
            "console",
            lambda m: self.errors.append(m.text) if m.type == "error" else None,
        )

    def __getattr__(self, name):
        return getattr(self._pg, name)

    def open(self, path: str = "") -> None:
        self._pg.goto(f"{self.base}/n/{path}")
        self._pg.wait_for_function("typeof path !== 'undefined' && path.length >= 1")
        self._pg.wait_for_timeout(400)


@pytest.fixture()
def page(server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield Harness(browser.new_page(viewport={"width": 1500, "height": 900}), server)
        browser.close()


def test_the_root_column_lists_the_served_directory(page):
    page.open()
    names = page.eval_on_selector_all(
        '.col[data-i="0"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert {"notes", "code", "empty", "README.md", "sample.db"} <= set(names)
    assert ".hidden" not in names  # dotfiles off by default, as in filemill


def test_clicking_a_folder_opens_its_column(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_selector('.col[data-i="1"]')
    page.wait_for_timeout(300)
    names = page.eval_on_selector_all(
        '.col[data-i="1"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert set(names) == {"deep", "plain.txt"}
    # filemill's focus model: opening a column does not move focus into it
    assert page.evaluate("focusCol") == 0


def test_the_keyboard_model_is_the_shared_one(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(300)
    assert page.evaluate("focusCol") == 1
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(300)
    assert page.evaluate("focusCol") == 0


def test_an_empty_directory_says_so(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("empty")')
    page.wait_for_timeout(400)
    assert "Empty" in page.inner_text('.col[data-i="1"] .col-note')


def test_the_preview_comes_from_the_python_renderer(page):
    """The point of preview-http.js: markdown-it-py output, in filemill's pane."""
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=5000)
    assert "Readme" in page.inner_text("#preview .pv-rich h1")


def test_source_is_highlighted_by_pygments(page):
    page.open("code/sample.py")
    page.wait_for_selector("#preview .pv-rich .preview-code", timeout=5000)
    assert page.locator("#preview .pv-rich .highlight").count() >= 1


def test_metadata_rides_along_with_the_listing(page):
    """No getFile() equivalent on this side: size and mtime arrive with the
    directory, so the pane is filled without a second round-trip."""
    page.open("notes/plain.txt")
    page.wait_for_timeout(400)
    assert "5 B" in page.inner_text("#pv-size")
    assert page.inner_text("#pv-mod").strip() not in ("", "—")


def test_the_url_path_mirrors_the_file_path(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_timeout(300)
    assert page.url.endswith("/n/notes")
    page.click('.col[data-i="1"] .row:has-text("plain.txt")')
    page.wait_for_timeout(300)
    assert page.url.endswith("/n/notes/plain.txt")


def test_a_deep_link_restores_the_whole_column_chain(page):
    page.open("notes/deep/leaf.md")
    assert page.evaluate("path.map(p => p.name)") == [
        page.evaluate("document.documentElement.dataset.root"),
        "notes",
        "deep",
    ]
    assert page.evaluate("sel") == ["notes", "deep", "leaf.md"]
    assert "Leaf" in page.inner_text("#preview .pv-rich h1")


def test_back_steps_out_of_the_folder_it_entered(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowRight")  # entering a column is the navigation
    page.wait_for_timeout(300)
    page.click('.col[data-i="1"] .row:has-text("deep")')
    page.wait_for_timeout(300)
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(400)
    deep_url = page.url
    page.go_back()
    page.wait_for_timeout(500)
    assert page.url != deep_url
    assert page.evaluate("sel").count("deep") <= 1


# A fake FileSystemDirectoryHandle — the whole API surface the FSA adapter
# touches. The OS picker itself cannot be driven headlessly, but everything
# behind it can: mount() is what the picker calls once a folder is granted.
FAKE_HANDLE = r"""
window.__local = () => {
  const F = (name, text) => ({kind: 'file', name,
    getFile: async () => new File([text], name, {lastModified: Date.now()})});
  const D = (name, kids) => ({kind: 'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  return D('my-laptop-folder', [
    F('local.md', '# Local heading\n\n**bold** from a folder the server cannot see\n'),
    F('local.py', 'def f():\n    return 1\n'),
  ]);
};
"""


def test_open_local_folder_is_offered(page):
    """The hybrid: the served page carries the FSA adapter too."""
    page.open()
    assert page.is_visible("#open")
    assert page.evaluate("typeof FSA === 'object' && typeof PreviewUpload === 'object'")
    assert page.evaluate("typeof window.showDirectoryPicker === 'function'")


def test_a_local_folder_replaces_the_served_tree(page):
    page.open()
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(400)
    assert page.evaluate("path[0].name") == "my-laptop-folder"
    names = page.eval_on_selector_all(
        '.col[data-i="0"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert set(names) == {"local.md", "local.py"}
    assert page.is_visible("#local-badge")


def test_local_files_are_still_rendered_by_python(page):
    """The point of POST /api/render: opening a local folder is not a downgrade.

    markdown-it-py renders bytes the server has never had a path to.
    """
    page.open()
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    page.click('.col[data-i="0"] .row:has-text("local.md")')
    page.wait_for_selector("#preview .pv-rich h1", timeout=5000)
    assert "Local heading" in page.inner_text("#preview .pv-rich h1")
    assert page.locator("#preview .pv-rich strong").count() >= 1


def test_local_source_is_still_highlighted_by_pygments(page):
    page.open()
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    page.click('.col[data-i="0"] .row:has-text("local.py")')
    page.wait_for_selector("#preview .pv-rich .preview-code", timeout=5000)


def test_local_mode_stops_writing_the_url(page):
    """A URL path names a file under the server's root; a granted folder is not
    under it, so the address bar has to go quiet rather than lie."""
    page.open("notes/plain.txt")
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    before = page.url
    page.click('.col[data-i="0"] .row:has-text("local.md")')
    page.wait_for_timeout(400)
    assert page.url == before
    assert page.url.rstrip("/").endswith("/n")


def test_leaving_local_mode_restores_the_served_tree(page):
    page.open()
    root_name = page.evaluate("document.documentElement.dataset.root")
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    page.click("#leave-local")
    page.wait_for_timeout(600)
    assert page.evaluate("path[0].name") == root_name
    assert not page.is_visible("#local-badge")
    names = page.eval_on_selector_all(
        '.col[data-i="0"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert "notes" in names


def test_nothing_is_fetched_from_a_cdn(page):
    """The HTMX UI pulls htmx and mermaid off the network; this one must not,
    or 'open a folder and browse it' would depend on being online."""
    external = []
    page.on(
        "request",
        lambda r: (
            external.append(r.url)
            if not r.url.startswith((page.base, "data:", "blob:"))
            else None
        ),
    )
    page.open("notes/deep/leaf.md")
    assert external == []


def test_no_console_errors(page):
    page.open("notes/deep/leaf.md")
    page.click('.col[data-i="0"] .row:has-text("code")')
    page.wait_for_timeout(400)
    assert page.errors == []


# ── virtual filesystems ──────────────────────────────────────────────────────
#
# The claim in ui/src/core/ports.js is that a node only needs name/dir/kids, so a
# SQLite table can be a directory with no change to core/. These are what make
# that a fact rather than an assertion.


def test_a_database_opens_as_a_column_of_tables(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=5000)
    names = page.eval_on_selector_all(
        '.col[data-i="1"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert "users" in names


def test_a_table_opens_as_a_column_of_rows(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=5000)
    page.click('.col[data-i="1"] .row:has-text("users")')
    page.wait_for_selector('.col[data-i="2"] .row', timeout=5000)
    assert page.locator('.col[data-i="2"] .row').count() == 3


def test_a_row_previews_through_the_provider(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=5000)
    page.click('.col[data-i="1"] .row:has-text("users")')
    page.wait_for_selector('.col[data-i="2"] .row', timeout=5000)
    page.click('.col[data-i="2"] .row >> nth=0')
    page.wait_for_selector("#preview .pv-rich", timeout=5000)
    assert "User1" in page.inner_text("#preview .pv-rich")


def test_virtual_nodes_keep_the_real_path_and_descend_by_vpath(page):
    """The rule the whole design rests on: one file on disk, many nodes."""
    page.open("sample.db/users")
    assert page.evaluate("path.map(p => p.rel)")[-1] == "sample.db"
    assert page.evaluate("path.map(p => p.vpath)")[-1] == "users"


def test_a_virtual_entry_uses_the_provider_glyph(page):
    page.open("sample.db")
    page.wait_for_selector('.col[data-i="1"] .row .ico.glyph', timeout=5000)
    assert page.locator('.col[data-i="1"] .row .ico.glyph').count() >= 1


def test_the_url_names_a_row_inside_a_database(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=5000)
    page.click('.col[data-i="1"] .row:has-text("users")')
    page.wait_for_timeout(400)
    assert page.url.endswith("/n/sample.db/users")


def test_a_row_shows_no_invented_size_or_date(page):
    """A row inside a database is not a file. Zeroed metadata would print
    "0 B · modified 1 Jan 1970", which is worse than nothing."""
    page.open("sample.db/users/1")
    page.wait_for_selector("#preview .pv-rich", timeout=5000)
    assert page.inner_text("#pv-sub").strip() == ""
    assert page.inner_text("#pv-size").strip() == "—"
    assert page.inner_text("#pv-mod").strip() == "—"


def test_a_real_file_still_shows_its_size_and_date(page):
    page.open("notes/plain.txt")
    page.wait_for_timeout(400)
    assert "5 B" in page.inner_text("#pv-size")
    assert "modified" in page.inner_text("#pv-sub")


def test_a_deep_link_into_a_database_restores_the_columns(page):
    page.open("sample.db/users/1")
    assert page.evaluate("sel")[-1] == "1"
    page.wait_for_selector("#preview .pv-rich", timeout=5000)
    assert "User1" in page.inner_text("#preview .pv-rich")
