"""The shared Miller-columns UI, driven in a real browser against this server.

This is the test that actually proves the sharing works: `ui/` is filemill's
frontend byte-for-byte, and here it is browsing a real directory tree over
`/api/dir` and `/api/preview` with nothing about `core/` changed.

Unlike the HTMX suite, nothing here reaches the network — every asset is served
by the app — so it also passes in an offline sandbox.

    timeout 300 PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH" \
      uv run --with "playwright==1.61.0" pytest tests/test_browser_new_ui.py
"""

from __future__ import annotations

import socket
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
    return tmp_path


@pytest.fixture()
def server(ui_root: Path):
    """Run the real app in a subprocess — TestClient cannot serve a browser."""
    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import uvicorn, pykofinder.app as a; "
                f"uvicorn.run(a.app, host='127.0.0.1', port={port}, "
                "log_level='error')"
            ),
        ],
        env={"PYKOFINDER_ROOT": str(ui_root), "PATH": "/usr/bin:/bin"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("server did not start")
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
    assert {"notes", "code", "empty", "README.md"} <= set(names)
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


def test_open_local_folder_is_offered(page):
    """The hybrid: the served page carries the FSA adapter too."""
    page.open()
    assert page.is_visible("#open")
    assert page.evaluate("typeof FSA === 'object' && typeof PreviewUpload === 'object'")
    assert page.evaluate("typeof window.showDirectoryPicker === 'function'")


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
