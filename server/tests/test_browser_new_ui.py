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

import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

pytestmark = pytest.mark.integration


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# The one file both builds are checked against. static/test-ui.py previews the
# same text through the same core/syntax.js and expects the same four classes,
# which is what "highlighted in both builds" is asserted to mean.
SOURCE = 'def f():\n    # doc\n    return "s" + 42\n'
TOKEN_CLASSES = "e=>[...new Set(e.map(x=>x.className))].sort().join()"


@pytest.fixture()
def ui_root(tmp_path: Path) -> Path:
    """A tree with enough shape to exercise columns, previews and deep links."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "deep").mkdir()
    (tmp_path / "notes" / "deep" / "leaf.md").write_text("# Leaf\n**bold** text\n")
    (tmp_path / "notes" / "plain.txt").write_text("hello")
    (tmp_path / "notes" / "short.txt").write_text("short")
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "sample.py").write_text(SOURCE)
    (tmp_path / "code" / "guide.rst").write_text(
        "Guide\n=====\n\nSome *rst* text.\n\n"
        ".. code-block:: python\n\n   return 1\n"
    )
    (tmp_path / "code" / "nested.json").write_text('{"tags":["a","b"],"n":1}')
    # 11 700 chars: more than the 8 000 the preview used to clip at.
    (tmp_path / "code" / "long.py").write_text(SOURCE * 300)
    # One byte over the preview's 512 KB ceiling.
    (tmp_path / "code" / "huge.py").write_text("x" * (512 * 1024 + 1))
    (tmp_path / "empty").mkdir()
    (tmp_path / "README.md").write_text(
        "# Readme\n\nline one\nline two\n\n```python\n" + SOURCE + "```\n"
    )
    (tmp_path / "page.html").write_text("<h1>Hi</h1>\n")
    (tmp_path / "clip.mp4").write_bytes(b"not a playable video")
    (tmp_path / "soft-breaks.md").write_text("one\ntwo\n\nthree  \nfour\n")
    (tmp_path / "wide.md").write_text(
        "# Wide\n\n```bash\n" + "command-with-a-long-name " * 12 + "\n```\n"
    )
    (tmp_path / "short.txt").write_text("short")
    (tmp_path / "README").write_text("readme")
    (tmp_path / ".hidden").write_text("h")
    (
        tmp_path / "this-is-a-very-long-file-name-that-must-stay-identifiable.txt"
    ).write_text("x")
    (tmp_path / "log.jsonl").write_text(
        '{"id": 2, "title": "Second", "ts": "2026-01-02"}\n'
        '{"id": 1, "title": "First", "ts": "2026-01-01"}\n'
    )
    (tmp_path / "data.csv").write_text(
        'group,id,note\nA,101,hello\nA,102,"comma, value"\n'
    )
    (tmp_path / "duplicate.csv").write_text("group,note\nA,hello\nA,again\n")
    (tmp_path / "dot.csv").write_text("name,note\n.hidden,hello\n.visible,again\n")
    (tmp_path / "empty.csv").write_text("")
    (tmp_path / "bad.csv").write_text('name,note\nAlice,"oops\n')
    (tmp_path / "captions.vtt").write_text(
        "WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.500\n"
        "<v Alice>Hello <c.green>world</c>\n\n"
        "00:00:04.000 --> 00:00:05.000\nBye\n",
        newline="",
    )
    (tmp_path / "empty.vtt").write_text("WEBVTT\n\n", newline="")
    (tmp_path / "bad.vtt").write_text(
        "WEBVTT\n\n00:00:00.000 --> nope\ntext\n", newline=""
    )
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
    rg_dir = str(Path(shutil.which("rg") or "/usr/bin/rg").parent)
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
            env={"FILEMILL_ROOT": str(ui_root), "PATH": f"{rg_dir}:/usr/bin:/bin"},
            stdout=subprocess.DEVNULL,
            stderr=fh,
        )
    base = f"http://127.0.0.1:{port}"
    # Importing the application takes a couple of seconds, and every test in this
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

    def open_resource(self, path: str) -> None:
        """Open the resource route, where the URL path is the file path."""
        self._pg.goto(f"{self.base}/{path}")
        self._pg.wait_for_function("typeof path !== 'undefined' && path.length >= 1")
        self._pg.wait_for_timeout(400)

    def open(self, path: str = "") -> None:
        self._pg.goto(f"{self.base}/n/{path}")
        self._pg.wait_for_function("typeof path !== 'undefined' && path.length >= 1")
        self._pg.wait_for_timeout(400)


@pytest.fixture()
def page(server: str, playwright):
    browser = playwright.chromium.launch(headless=True)
    try:
        yield Harness(browser.new_page(viewport={"width": 1500, "height": 900}), server)
    finally:
        browser.close()


def test_the_root_column_lists_the_served_directory(page):
    page.open()
    names = page.eval_on_selector_all(
        '.col[data-i="0"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert {"notes", "code", "empty", "README.md", "sample.db"} <= set(names)
    assert ".hidden" not in names  # dotfiles off by default, as in filemill


def test_theme_follows_os_colour_scheme_and_keeps_manual_control(server, playwright):
    browser = playwright.chromium.launch(headless=True)
    try:
        for scheme, expected in (("dark", "dark"), ("light", "light")):
            context = browser.new_context(color_scheme=scheme)
            themed = Harness(context.new_page(), server)
            themed.open()
            assert themed.evaluate("root.dataset.theme") == expected
            assert (
                themed.locator("#s-theme").get_attribute("aria-checked")
                == str(expected == "dark").lower()
            )
            assert themed.evaluate(
                "getComputedStyle(document.documentElement).getPropertyValue('--chrome').trim()"
            ) == ("#1b1d21" if expected == "dark" else "#e7e7ec")
            themed.click("#gear")
            themed.click("#s-theme")
            manual = "light" if expected == "dark" else "dark"
            assert themed.evaluate("root.dataset.theme") == manual
            assert (
                themed.locator("#s-theme").get_attribute("aria-checked")
                == str(manual == "dark").lower()
            )
            context.close()
    finally:
        browser.close()


def test_long_names_truncate_before_the_extension(page):
    page.set_viewport_size({"width": 390, "height": 700})
    page.open()
    row = page.locator(
        '.row[title="this-is-a-very-long-file-name-that-must-stay-identifiable.txt"]'
    )
    assert row.inner_text().endswith(".txt")
    assert "identifiable" in row.inner_text()
    assert row.get_attribute("aria-label") == row.get_attribute("title")
    assert row.evaluate(
        "row => { const label = row.querySelector('.label'); "
        "const stem = label.querySelector('.stem'); "
        "return stem.scrollWidth > stem.clientWidth && "
        "label.getBoundingClientRect().right <= row.getBoundingClientRect().right; }"
    )


def test_short_and_extensionless_names_remain_readable(page):
    page.open()
    for name in ("short.txt", "README"):
        row = page.locator(f'.row[title="{name}"]')
        assert row.locator(".label").text_content() == name
        assert row.get_attribute("aria-label") == name


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
    scroll = page.evaluate("window.scrollX")
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(300)
    assert page.evaluate("focusCol") == 0
    assert page.evaluate("window.scrollX") == scroll


def test_an_empty_directory_says_so(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("empty")')
    page.wait_for_timeout(400)
    assert "Empty" in page.inner_text('.col[data-i="1"] .col-note')


def test_the_markdown_preview_is_rendered_in_the_browser(page):
    """Markdown goes through preview-rich.js and the modules the shell serves
    from /ui/vendor/; the output lands in the same pane preview-http.js fills
    for everything the server still renders."""
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert "Readme" in page.inner_text("#preview .pv-rich h1")


def test_mp4_preview_uses_a_video_control(page):
    page.open("clip.mp4")
    page.wait_for_selector("#preview video.pv-video")
    assert page.locator("#preview video[controls]").count() == 1


def test_preview_fullscreen_control_toggles_and_exits(page):
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    full = page.locator("#pv-fullscreen")

    full.click()
    page.wait_for_function("document.documentElement.classList.contains('pv-fullscreen')")
    assert full.get_attribute("aria-pressed") == "true"
    assert page.evaluate("getComputedStyle(document.getElementById('bar')).display") == "none"

    full.click()
    page.wait_for_function("!document.documentElement.classList.contains('pv-fullscreen')")
    assert full.get_attribute("aria-pressed") == "false"
    assert page.evaluate("getComputedStyle(document.getElementById('bar')).display") != "none"


def test_markdown_rendered_raw_toggle_preserves_navigation(page):
    source = "# Readme\n\nline one\nline two\n\n```python\n" + SOURCE + "```\n"
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    rendered = page.locator("#pv-md-rendered")
    raw = page.locator("#pv-md-raw")
    assert rendered.get_attribute("aria-pressed") == "true"
    assert raw.get_attribute("aria-pressed") == "false"
    assert page.evaluate("sel")[-1] == "README.md"

    raw.click()
    page.wait_for_function("document.querySelector('#preview .pv-text')?.textContent")
    assert page.locator("#preview .pv-rich h1").count() == 0
    assert page.text_content("#preview .pv-text") == source
    assert rendered.get_attribute("aria-pressed") == "false"
    assert raw.get_attribute("aria-pressed") == "true"
    assert page.evaluate("sel")[-1] == "README.md"

    rendered.press("Enter")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.evaluate("sel")[-1] == "README.md"


def test_vtt_transcript_and_raw_views_preserve_navigation(page):
    source = (
        "WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.500\n"
        "<v Alice>Hello <c.green>world</c>\n\n"
        "00:00:04.000 --> 00:00:05.000\nBye\n"
    )
    page.open("captions.vtt")
    page.wait_for_selector(".preview-transcript .preview-cue", timeout=15000)
    assert "00:00:01.000" in page.inner_text("#pv-content")
    assert "Hello world" in page.inner_text("#pv-content")
    assert page.locator("#pv-vtt-transcript").get_attribute("aria-pressed") == "true"
    assert page.evaluate("sel")[-1] == "captions.vtt"

    page.click("#pv-vtt-raw")
    page.wait_for_function("document.querySelector('#pv-content .preview-raw')")
    assert page.text_content("#pv-content .preview-raw") == source
    assert page.locator("#pv-vtt-raw").get_attribute("aria-pressed") == "true"
    assert page.evaluate("sel")[-1] == "captions.vtt"

    page.click("#pv-vtt-transcript")
    page.wait_for_selector(".preview-transcript .preview-cue", timeout=15000)
    assert page.locator("#pv-vtt-transcript").get_attribute("aria-pressed") == "true"


def test_vtt_empty_and_malformed_files_are_safe(page):
    page.open("empty.vtt")
    assert "no cues" in page.inner_text("#pv-content").lower()
    assert page.locator("#pv-vtt-views").is_visible()
    page.open("bad.vtt")
    assert "malformed webvtt" in page.inner_text("#pv-content").lower()


def test_vtt_highlight_view_keeps_the_source_fallback(page):
    page.open("captions.vtt?filemill=highlight")
    page.wait_for_selector("#preview .pv-rich .preview-raw", timeout=15000)
    assert "WEBVTT" in page.inner_text("#preview .pv-rich")
    assert page.locator("#pv-vtt-views").is_hidden()


def test_content_search_opens_a_matching_file(page):
    page.open()
    page.fill("#search-bar", "Leaf")
    page.wait_for_selector('.search-result[data-path="notes/deep/leaf.md"]')
    assert "# Leaf" in page.inner_text(".search-result")
    page.click('.search-result[data-path="notes/deep/leaf.md"]')
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert "Leaf" in page.inner_text("#preview .pv-rich h1")


def test_fenced_code_is_highlighted_in_the_browser(page):
    """The fence arrives as <pre><code class="language-python"> from Python and
    core/syntax.js colours it — the same classes as a source file, in both
    builds (static/test-rich.py checks the other one). Paragraphs are left as
    the renderer made them: a source newline is whitespace, not a <br>."""
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich pre code .hl-kw", timeout=15000)
    assert (
        page.eval_on_selector_all("#preview .pv-rich pre code span", TOKEN_CLASSES)
        == "hl-com,hl-kw,hl-num,hl-str"
    )
    assert page.text_content("#preview .pv-rich pre code") == SOURCE


def test_large_directory_pages_in_the_browser(page, ui_root):
    for i in range(501):
        (ui_root / f"large-{i:03d}.txt").write_text(str(i))
    page.open()
    page.wait_for_selector(".pager span")
    assert page.inner_text(".pager span") == "Page 1 of 2"
    assert page.locator('.col[data-i="0"] .row:has-text("large-000.txt")').count() == 1
    page.click('.pager button[aria-label="Next page"]')
    page.wait_for_function(
        "document.querySelector('.pager span')?.innerText === 'Page 2 of 2'"
    )
    assert page.locator('.col[data-i="0"] .row:has-text("large-500.txt")').count() == 1
    assert page.locator('.col[data-i="0"] .row:has-text("large-000.txt")').count() == 0


def test_markdown_soft_breaks_wrap_and_hard_breaks_remain(page):
    page.open("soft-breaks.md")
    page.wait_for_selector("#preview .pv-rich p", timeout=15000)
    assert page.locator("#preview .pv-rich p").count() == 2
    assert (
        page.eval_on_selector(
            "#preview .pv-rich p", "e=>getComputedStyle(e).whiteSpace"
        )
        == "normal"
    )
    assert page.evaluate(
        """() => {
          const p = document.querySelector('#preview .pv-rich p');
          const body = document.querySelector('#preview .pv-body');
          const style = getComputedStyle(body);
          return Math.round(p.getBoundingClientRect().width) === Math.round(
            body.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight)
          );
        }"""
    )
    assert page.eval_on_selector_all(
        "#preview .pv-rich p", "es=>es.map(e=>e.innerHTML)"
    ) == [
        "one\ntwo",
        "three<br>\nfour",
    ]


def test_markdown_code_wraps_within_portrait_preview(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.open("wide.md")
    page.wait_for_selector("#preview .pv-markdown pre", timeout=15000)
    assert page.evaluate(
        """() => {
          const body = document.querySelector('#preview .pv-body');
          return body.scrollWidth <= body.clientWidth;
        }"""
    )


def test_source_is_highlighted_in_the_browser(page):
    """core/syntax.js, not Pygments: the shared UI colours source itself so the
    static build and this one run one implementation. The server still renders
    what it is better at — see the markdown test above."""
    page.open("code/sample.py")
    page.wait_for_selector("#preview .pv-text .hl-kw", timeout=15000)
    assert (
        page.eval_on_selector_all("#preview .pv-text span", TOKEN_CLASSES)
        == "hl-com,hl-kw,hl-num,hl-str"
    )
    assert page.text_content("#preview .pv-text") == SOURCE


def test_saved_plaintext_preview_survives_reopen_and_reload(page):
    page.open("notes/plain.txt")
    page.wait_for_selector("#pv-edit")
    assert page.inner_text("#pv-content").strip() == "hello"
    page.click("#pv-edit")
    page.fill("#pv-editor", "saved")
    page.click("#pv-save")
    page.wait_for_function(
        "document.querySelector('#pv-content')?.innerText.trim() === 'saved'"
    )
    assert page.inner_text("#pv-content").strip() == "saved"
    assert page.is_hidden("#pv-modified")
    page.open("notes")
    page.click('.col[data-i="1"] .row:has-text("plain.txt")')
    page.wait_for_selector("#pv-edit")
    assert page.inner_text("#pv-content").strip() == "saved"
    assert page.is_hidden("#pv-modified")
    page.reload()
    page.wait_for_selector("#pv-edit")
    assert page.inner_text("#pv-content").strip() == "saved"
    assert page.is_hidden("#pv-modified")

    page.click("#pv-edit")
    page.wait_for_selector("#pv-editor")
    assert page.input_value("#pv-editor") == "saved"
    assert page.is_hidden("#pv-modified")


def test_a_long_source_file_is_highlighted_whole(page):
    """The served half of "no 8 000-character clip".

    app-http.js sends anything with a language core/syntax.js knows through
    PreviewLocal, so this file is fetched over /api/raw and coloured in the
    page — the same branch static/test-ui.py drives against a fake handle.
    Asserting the text alone would pass on a build that coloured the head and
    escaped the tail, so the keyword count is the half that matters: def and
    return is two per copy, 600 across the 300.
    """
    page.open("code/long.py")
    page.wait_for_selector("#preview .pv-text .hl-kw", timeout=15000)
    assert page.text_content("#preview .pv-text") == SOURCE * 300
    assert page.eval_on_selector_all("#preview .pv-text .hl-kw", "e=>e.length") == 600


def test_json_opens_as_a_hierarchical_view(page):
    """The server build exposes JSON containers as shared virtual columns."""
    page.open("code/nested.json")
    page.wait_for_selector('.col[data-i="2"] .row:has-text("tags")', timeout=15000)
    page.click('.col[data-i="2"] .row:has-text("tags")')
    page.wait_for_selector('.col[data-i="3"] .row:has-text("0")', timeout=15000)
    page.click('.col[data-i="3"] .row:has-text("0")')
    assert page.inner_text("#pv-content").strip() == "a"


def test_json_hierarchy_works_in_the_highlight_view(page):
    """?filemill=highlight keeps the shared JSON hierarchy."""
    page.open_resource("code/nested.json?filemill=highlight")
    page.wait_for_selector('.col[data-i="2"] .row:has-text("tags")', timeout=15000)
    assert page.evaluate("document.documentElement.dataset.filemill") == "highlight"
    page.click('.col[data-i="2"] .row:has-text("tags")')
    page.wait_for_selector('.col[data-i="3"] .row:has-text("1")', timeout=15000)


def test_an_oversized_text_file_is_declined_without_fetching_it(page):
    """The gate is before FS.blob, and this is the only way to see that.

    Both with and without it the pane says the same thing, because the size
    test used to happen after the bytes had arrived. What changes is whether
    they arrive at all: HTTP.blob does `await r.blob()`, so a 50 MB .sql was
    downloaded in full and then declined. Asserting the message would pass
    either way — asserting that /api/raw is never requested is what pins it.
    """
    seen: list[str] = []
    page.on("request", lambda r: seen.append(r.url))
    page.open("code/huge.py")
    page.wait_for_selector("#preview #pv-content p", timeout=15000)
    assert "No inline preview" in page.inner_text("#preview #pv-content")
    assert [u for u in seen if "/api/raw" in u] == []


def test_metadata_rides_along_with_the_listing(page):
    """No getFile() equivalent on this side: size and mtime arrive with the
    directory, so the pane is filled without a second round-trip."""
    page.open("notes/plain.txt")
    page.wait_for_timeout(400)
    assert "5 B" in page.inner_text("#pv-sub")
    assert "modified" in page.inner_text("#pv-sub")


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


def test_arrow_left_unfolds_each_focused_ancestor(page):
    page.set_viewport_size({"width": 760, "height": 700})
    page.open("notes/deep/leaf.md")
    url = page.url
    selected = page.evaluate("sel.slice()")

    assert page.evaluate("focusCol") == 2
    for expected in (1, 0):
        page.keyboard.press("ArrowLeft")
        _scroll_settled(page)
        state = page.evaluate(
            "({focusCol, folded, spine: document.querySelector('.col.focus').classList.contains('spine')})"
        )
        assert state == {"focusCol": expected, "folded": expected, "spine": False}
        assert page.url == url
        assert page.evaluate("sel") == selected


def test_preview_arrows_fold_all_then_restore_only_document_parent(page):
    page.set_viewport_size({"width": 760, "height": 700})
    page.open("notes/deep/leaf.md")
    page.keyboard.press("ArrowRight")
    _scroll_settled(page)
    assert page.evaluate("document.activeElement.id") == "preview"
    assert page.evaluate("folded") == page.evaluate("path.length")

    page.keyboard.press("ArrowLeft")
    _scroll_settled(page)
    state = page.evaluate("({focusCol, folded, spines: [...document.querySelectorAll('.col.spine')].map(c => +c.dataset.i)})")
    assert state == {"focusCol": 1, "folded": 1, "spines": [0]}


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


def _scroll_settled(page) -> None:
    """Wait until the smooth scroll of #finder has stopped moving."""
    prev = None
    for _ in range(40):  # 40 × 100 ms — a 4 s ceiling
        cur = page.evaluate("document.getElementById('finder').scrollLeft")
        if cur == prev:
            return
        prev = cur
        page.wait_for_timeout(100)
    raise AssertionError("#finder never stopped scrolling")


def test_arrow_navigation_folds_but_never_unfolds(page, ui_root):
    """Opening a wide chain folds the left columns; arrowing to a narrow entry
    must keep them folded. layout() may only raise the fold count on its own —
    unfolding is a user action (a scroll, a spine click, or ←).

    The widths are deterministic: the content width is capped at two-thirds of
    the live finder width, and the 1290 px viewport sits between "the wide
    chain overflows" and "the narrow chain fits"."""
    inner = ui_root / "w" / "inner"
    (inner / "a-wide").mkdir(parents=True)
    (
        inner / "a-wide" / ("a-name-long-enough-to-hit-the-column-cap" * 2 + ".txt")
    ).write_text("wide")
    (inner / "z-narrow").mkdir()
    (inner / "z-narrow" / "a.txt").write_text("narrow")

    page.set_viewport_size({"width": 1290, "height": 700})
    page.open()
    page.click('.col[data-i="0"] .row:has(.label:text-is("w"))')
    page.wait_for_timeout(300)
    page.click('.col[data-i="1"] .row:has(.label:text-is("inner"))')
    page.wait_for_timeout(300)
    page.click('.col[data-i="2"] .row:has(.label:text-is("a-wide"))')
    _scroll_settled(page)
    folded_before = page.evaluate("folded")
    assert folded_before >= 1, "the wide chain did not fold — the test proves nothing"
    assert page.evaluate("focusCol") == 2

    page.keyboard.press("ArrowDown")  # z-narrow: fits with no folds at all
    _scroll_settled(page)
    assert page.evaluate("sel[2]") == "z-narrow"
    # guard against a vacuous pass: the old minimal-fit layout would unfold here
    assert page.evaluate("stripSpan(0) + previewTarget() <= finder.clientWidth")
    assert page.evaluate("folded") == folded_before
    # the animation mechanism: layout()'s scrollLeft writes glide, in pure CSS
    assert page.evaluate("getComputedStyle(finder).scrollBehavior") == "smooth"


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
    F('local.py', 'def f():\n    # doc\n    return "s" + 42\n'),
  ]);
};
"""


def test_open_local_folder_is_offered(page):
    """The hybrid: the served page carries the FSA adapter too."""
    page.open()
    assert page.is_visible("#open")
    assert page.evaluate("typeof FSA === 'object'")
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


def _click_local(page, name: str, selector: str) -> None:
    """Click a local-folder entry and wait for the preview it draws.

    Markdown and .docx from a granted folder render in the page, from the
    modules the shell lists in FILEMILL_CDN; nothing is posted to the server
    for them. A timeout therefore says what did reach the DOM, which separates
    a renderer that threw (PreviewRich falls back to the source with a
    ``.pv-note``) from one that drew something without the selector in it.
    """
    page.click(f'.col[data-i="0"] .row:has-text("{name}")')
    try:
        page.wait_for_selector(selector, timeout=15000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(
            f"{selector} never appeared for {name}. #preview .pv-rich count is "
            f"{page.locator('#preview .pv-rich').count()}, .pv-note count is "
            f"{page.locator('#preview .pv-note').count()}. First 300 chars: "
            f"{page.inner_html('#preview')[:300]!r}"
        ) from exc


def test_local_markdown_is_rendered_in_the_browser(page):
    """Opening a local folder is not a downgrade: the same markdown-it that
    renders a served file renders bytes the server has never had a path to,
    and nothing is posted to it on the way."""
    page.open()
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    posts: list[str] = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    _click_local(page, "local.md", "#preview .pv-rich h1")
    assert "Local heading" in page.inner_text("#preview .pv-rich h1")
    assert page.locator("#preview .pv-rich strong").count() >= 1


def test_local_source_is_highlighted_without_asking_the_server(page):
    """The gain from moving highlighting into the page: a folder the server has
    no path to is coloured with no round-trip at all."""
    page.open()
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    posts: list[str] = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.click('.col[data-i="0"] .row:has-text("local.py")')
    page.wait_for_selector("#preview .pv-text .hl-kw", timeout=15000)
    assert (
        page.eval_on_selector_all("#preview .pv-text span", TOKEN_CLASSES)
        == "hl-com,hl-kw,hl-num,hl-str"
    )


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
    or 'open a folder and browse it' would depend on being online.

    Both halves matter, and this test used to check only the first. The served
    half goes through preview-http.js and `/api/preview`; the local-folder half
    goes through PreviewRich in the browser. Source files now go through neither — they are
    coloured in the page by core/syntax.js — so they are the easiest half to
    keep honest and are checked here too. Markdown goes through
    `ui/adapters/preview-rich.js` in both halves, which imports its renderer
    from the URL the shell's FILEMILL_CDN names: `/ui/vendor/markdown-it.js`,
    this origin. Only `.pptx` still asks a CDN for its viewer, and this test
    never opens one. Any other preview that started to would break this test,
    which is the point of the test.
    """
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

    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    _click_local(page, "local.md", "#preview .pv-rich")
    # local.py: core/syntax.js colours it in the page, so there is no response
    # to wait for — only the absence of a request.
    page.click('.col[data-i="0"] .row:has-text("local.py")')
    page.wait_for_selector("#preview .pv-text .hl-kw", timeout=15000)
    assert external == []


def test_the_server_edition_registers_core_and_browser_rich_renderers(page):
    """core/renderers.js: the same core table as the static build, plus the
    rich entries the browser draws here — Markdown and .docx from /ui/vendor/,
    .pptx from its viewer, and the offline fallback they name. reStructuredText
    is the one rich kind left to Python."""
    page.open("")
    assert page.evaluate("RENDERERS.map(e => e.kind)") == [
        "image",
        "video",
        "pdf",
        "html",
        "desktop",
        "vtt",
        "text",
        "md",
        "markdown",
        "docx",
        "pptx",
        "offline",
    ]


def test_no_console_errors(page):
    page.open("notes/deep/leaf.md")
    page.click('.col[data-i="0"] .row:has-text("code")')
    page.wait_for_timeout(400)
    assert page.errors == []


def test_missing_favicon_does_not_raise_in_the_browser(page):
    page.open()
    page.errors.clear()
    assert page.evaluate("fetch('/favicon.ico').then(r => r.status)") == 404
    assert not any("renderPage is not a function" in error for error in page.errors)


# ── virtual filesystems ──────────────────────────────────────────────────────
#
# The claim in ui/src/core/ports.js is that a node only needs name/dir/kids, so a
# SQLite table can be a directory with no change to core/. These are what make
# that a fact rather than an assertion.


def test_a_database_opens_as_a_column_of_tables(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    names = page.eval_on_selector_all(
        '.col[data-i="1"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert "users" in names


def test_a_table_opens_as_a_column_of_rows(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("users")')
    page.wait_for_selector('.col[data-i="2"] .row', timeout=15000)
    assert page.locator('.col[data-i="2"] .row').count() == 3


def test_a_row_previews_through_the_json_hierarchical_view(page):
    """The server sends the row's cells as JSON on the listing; the client
    browses the row like a JSONL record and never asks /api/preview."""
    seen: list[str] = []
    page.on("request", lambda r: seen.append(r.url))
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("users")')
    page.wait_for_selector('.col[data-i="2"] .row', timeout=15000)
    page.click('.col[data-i="2"] .row >> nth=0')
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert "User1" in page.inner_text("#preview .pv-json")
    assert [u for u in seen if "/api/preview" in u] == []


def test_virtual_nodes_keep_the_real_path_and_descend_by_vpath(page):
    """The rule the whole design rests on: one file on disk, many nodes."""
    page.open("sample.db/users")
    assert page.evaluate("path.map(p => p.rel)")[-1] == "sample.db"
    assert page.evaluate("path.map(p => p.vpath)")[-1] == "users"


def test_a_virtual_entry_uses_the_provider_glyph(page):
    page.open("sample.db")
    page.wait_for_selector('.col[data-i="1"] .row .ico.glyph', timeout=15000)
    assert page.locator('.col[data-i="1"] .row .ico.glyph').count() >= 1


def test_the_url_names_a_row_inside_a_database(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("users")')
    page.wait_for_timeout(400)
    assert page.url.endswith("/n/sample.db/users")


def test_a_row_shows_no_invented_size_or_date(page):
    """A row inside a database is not a file. Zeroed metadata would print
    "0 B · modified 1 Jan 1970", which is worse than nothing."""
    page.open("sample.db/users/1")
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert page.inner_text("#pv-sub").strip() == ""


def test_a_real_file_still_shows_its_size_and_date(page):
    page.open("notes/plain.txt")
    page.wait_for_timeout(400)
    assert "5 B" in page.inner_text("#pv-sub")
    assert "modified" in page.inner_text("#pv-sub")


# ── The resource route serves this UI (PLAN-19) ──────────────────────────────
#
# `/docs/topic.md?filemill=render` used to answer with the HTMX shell. These
# four are the only tests that prove the swap through a real browser: a
# TestClient sees an almost empty shell, because the chrome and the document
# both arrive after JavaScript runs.


def test_the_resource_route_opens_this_ui_at_the_file(page):
    page.open_resource("notes/deep/leaf.md?filemill=render")
    assert page.evaluate("sel") == ["notes", "deep", "leaf.md"]
    assert "Leaf" in page.inner_text("#preview .pv-rich h1")


def test_the_resource_route_keeps_the_query_while_you_browse(page):
    """router-path.js preserves the query, so the view survives a click."""
    page.open_resource("notes/deep/leaf.md?filemill=render")
    page.click('.col[data-i="0"] .row:has-text("code")')
    page.wait_for_timeout(400)
    assert page.url.endswith("/code?filemill=render")


def test_rendered_source_toggle_updates_the_url_and_history(page):
    page.open_resource("notes/deep/leaf.md?filemill=render")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    page.fill("#search-bar", "leaf")
    before = page.evaluate("performance.getEntriesByType('navigation')[0].type")
    page.click("#pv-view")
    page.wait_for_selector("#preview .pv-text", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=highlight")
    assert page.input_value("#search-bar") == "leaf"
    assert (
        page.evaluate("performance.getEntriesByType('navigation')[0].type")
        == before
        == "navigate"
    )
    assert page.locator("#preview .pv-rich h1").count() == 0
    assert page.inner_text("#pv-view") == "Rendered"

    page.go_back()
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=render")
    assert page.input_value("#search-bar") == "leaf"
    page.go_forward()
    page.wait_for_selector("#preview .pv-text", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=highlight")

    page.goto(page.url.replace("filemill=highlight", "filemill=render"))
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.inner_text("#pv-view") == "Source"


def test_raw_navigation_stays_in_the_file_manager(page):
    page.open("notes/plain.txt")
    page.click("#pv-raw")
    page.wait_for_selector("#preview .pv-content", timeout=15000)
    assert page.url.endswith("/notes/plain.txt?filemill=raw")
    assert page.evaluate("sel")[-1] == "plain.txt"
    page.click('.col[data-i="0"] .row:has-text("code")')
    page.wait_for_function("location.pathname === '/code'")
    assert page.url.endswith("/code?filemill=raw")


def test_back_from_raw_restores_the_previous_rendered_file(page):
    page.open("notes")
    page.click('.col[data-i="0"] .row:has-text("plain.txt")')
    page.click('.col[data-i="0"] .row:has-text("short.txt")')
    page.click("#pv-raw")
    page.go_back()
    page.wait_for_selector("#preview .pv-content", timeout=15000)
    assert page.url.endswith("/notes/short.txt?filemill=render")
    assert page.evaluate("sel")[-1] == "short.txt"


def test_back_and_forward_restore_folder_preview_and_raw_states(page):
    page.open("notes")
    page.click('.col[data-i="0"] .row:has-text("deep")')
    page.click('.col[data-i="1"] .row:has-text("leaf.md")')
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=render")

    page.click("#pv-raw")
    page.wait_for_selector("#preview .pv-content", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=raw")

    page.go_back()
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=render")
    page.go_back()
    assert page.url.endswith("/notes/deep")
    assert page.evaluate("sel")[-1] == "deep"

    page.go_forward()
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    page.go_forward()
    page.wait_for_selector("#preview .pv-content", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=raw")


def test_no_columns_shows_a_document_without_the_finder(page):
    """?layout=no-columns is the client's job now: the shell hides the chrome."""
    page.open_resource("notes/deep/leaf.md?filemill=render&layout=no-columns")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.evaluate("document.documentElement.dataset.layout") == "no-columns"
    assert page.locator("#strip > .col:visible").count() == 0
    assert not page.is_visible("#bar")
    assert not page.is_visible("#trail")
    assert page.is_visible("#preview .pv-rich")


def test_no_columns_shows_a_directory_as_one_listing(page):
    page.open_resource("notes?layout=no-columns")
    assert page.locator("#strip > .col:visible").count() == 1
    assert page.is_visible('#strip > .col:visible .row:has-text("deep")')
    assert not page.is_visible("#bar")


def test_highlight_shows_the_source_in_the_columns(page):
    """Markdown and HTML source use the shared browser highlighter."""
    page.open_resource("notes/deep/leaf.md?filemill=highlight")
    page.wait_for_selector("#preview .pv-text .hl-com", timeout=15000)
    assert page.text_content("#preview .pv-text") == "# Leaf\n**bold** text\n"
    assert page.locator("#preview .pv-rich").count() == 0
    page.open_resource("page.html?filemill=highlight")
    page.wait_for_selector("#preview .pv-text .hl-kw", timeout=15000)
    assert page.text_content("#preview .pv-text") == "<h1>Hi</h1>\n"
    assert page.locator("iframe.pv-html").count() == 0


def test_rst_renders_and_highlights_in_the_server_preview(page):
    page.open_resource("code/guide.rst?filemill=render")
    page.wait_for_selector("#preview .preview-rst h1", timeout=15000)
    assert "Some rst text." in page.text_content("#preview .preview-rst")
    page.open_resource("code/guide.rst?filemill=highlight")
    page.wait_for_selector("#preview .pv-text .hl-com", timeout=15000)
    assert ".. code-block:: python" in page.text_content("#preview .pv-text")


def test_hidden_show_starts_with_dotfiles_visible(page):
    """ui/core/state.js seeds state.dotfiles from the URL."""
    page.open_resource("README.md?filemill=render&hidden=show")
    names = page.eval_on_selector_all(
        '.col[data-i="0"] .row .label', "els => els.map(e => e.textContent)"
    )
    assert ".hidden" in names


def test_a_deep_link_into_a_database_restores_the_columns(page):
    page.open("sample.db/users/1")
    assert page.evaluate("sel")[-1] == "1"
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert "User1" in page.inner_text("#preview .pv-json")


def test_a_jsonl_file_opens_as_a_column_of_rows(page):
    page.open("")
    page.click('.col[data-i="0"] .row:has-text("log.jsonl")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    names = page.eval_on_selector_all(
        '.col[data-i="1"] .row', "els => els.map(e => e.title)"
    )
    assert names == ["Second", "First"]


def test_a_jsonl_row_previews_in_the_browser_without_asking_the_server(page):
    seen: list[str] = []
    page.on("request", lambda r: seen.append(r.url))
    page.open("log.jsonl/Second")
    assert page.evaluate("sel")[-1] == "Second"
    page.wait_for_selector("#preview .pv-kv", timeout=15000)
    cells = page.eval_on_selector_all(
        "#preview .pv-kv tr",
        "rs => rs.map(r => [r.children[0].textContent, r.children[1].textContent])",
    )
    assert cells == [["id", "2"], ["title", "Second"], ["ts", "2026-01-02"]]
    assert page.inner_text("#pv-sub") == ""
    assert [u for u in seen if "/api/preview" in u] == []


def test_a_csv_row_previews_headers_and_quoted_values(page):
    seen: list[str] = []
    page.on("request", lambda r: seen.append(r.url))
    page.open("data.csv/102")
    page.wait_for_selector("#preview .pv-kv", timeout=15000)
    assert page.inner_text("#preview .pv-kv") == "group\tA\nid\t102\nnote\tcomma, value"
    assert [u for u in seen if "/api/preview" in u] == []


def test_csv_without_unique_column_names_rows_individually(page):
    page.open("duplicate.csv")
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    assert page.eval_on_selector_all(
        '.col[data-i="1"] .row', "els => els.map(e => e.title)"
    ) == ["row 1", "row 2"]


def test_csv_unique_dot_labels_fall_back_to_visible_row_names(page):
    page.open("dot.csv")
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    assert page.eval_on_selector_all(
        '.col[data-i="1"] .row', "els => els.map(e => e.title)"
    ) == ["row 1", "row 2"]


def test_empty_and_malformed_csv_files_keep_safe_raw_fallback(page):
    page.open("empty.csv")
    assert "not yet" not in " ".join(page.errors)
    page.open("bad.csv")
    assert "not yet" not in " ".join(page.errors)


def test_editor_features_and_failed_save(page):
    pg = page
    pg.open("notes/plain.txt")
    pg.click("#pv-edit")
    pg.wait_for_selector("#pv-editor")
    original = pg.input_value("#pv-editor")
    assert pg.is_hidden("#pv-modified")
    pg.fill("#pv-editor", "alpha\nbeta alpha\n")
    assert pg.is_visible("#pv-modified")
    assert pg.inner_text("#pv-gutter") == "1\n2\n3"
    pg.press("#pv-editor", "Control+z")
    assert pg.input_value("#pv-editor") == original
    assert pg.is_hidden("#pv-modified")
    pg.press("#pv-editor", "Control+Shift+z")
    assert pg.input_value("#pv-editor") == "alpha\nbeta alpha\n"
    assert pg.is_visible("#pv-modified")
    pg.press("#pv-editor", "Control+f")
    pg.fill('input[aria-label="Find in file"]', "alpha")
    for start in (0, 11, 0):
        pg.keyboard.press("Enter")
        assert pg.eval_on_selector("#pv-editor", "e => e.selectionStart") == start
    pg.fill('input[aria-label="Find in file"]', "absent")
    pg.press('input[aria-label="Find in file"]', "Enter")
    assert pg.inner_text(".pv-find output") == "No matches"
    pg.fill('input[aria-label="Find in file"]', "")
    pg.press('input[aria-label="Find in file"]', "Enter")
    assert pg.inner_text(".pv-find output") == ""
    pg.press('input[aria-label="Find in file"]', "Escape")
    assert pg.is_hidden(".pv-find")
    assert pg.evaluate("document.activeElement.id") == "pv-editor"
    assert pg.input_value("#pv-editor") == "alpha\nbeta alpha\n"
    pg.evaluate("window.__editorBeforeResize = document.querySelector('#pv-editor')")
    pg.set_viewport_size({"width": 1100, "height": 700})
    pg.wait_for_function("finder.clientWidth < 1200")
    assert pg.evaluate("document.querySelector('#pv-editor') === __editorBeforeResize")
    assert pg.is_visible("#pv-modified")
    pg.press("#pv-editor", "Control+z")
    assert pg.input_value("#pv-editor") == original
    assert pg.is_hidden("#pv-modified")
    # A new edit after undo discards the old redo branch.
    pg.fill("#pv-editor", "new branch")
    pg.press("#pv-editor", "Control+Shift+z")
    assert pg.input_value("#pv-editor") == "new branch"
    pg.fill("#pv-editor", "")
    assert pg.inner_text("#pv-gutter") == "1"
    pg.fill("#pv-editor", "line\n" * 100)
    pg.eval_on_selector("#pv-editor", "e => { e.scrollTop = e.scrollHeight; }")
    pg.wait_for_function("""() => {
      const ta = document.querySelector('#pv-editor');
      return document.querySelector('#pv-gutter').style.transform === `translateY(${-ta.scrollTop}px)`;
    }""")
    assert (pg.inner_text("#pv-gutter")).splitlines()[-1] == "101"
    # A failed port write leaves the editable text and modified mark intact.
    pg.evaluate("""() => {
      window.__editorWrite = FS.write;
      FS.write = async () => { throw new Error('test write denied'); };
    }""")
    pg.click("#pv-save")
    pg.wait_for_function(
        "document.querySelector('#pv-edit-err').textContent === 'test write denied'"
    )
    assert pg.is_visible("#pv-modified")
    assert not pg.eval_on_selector("#pv-editor", "e => e.readOnly")
    pg.evaluate("() => { FS.write = window.__editorWrite; }")
    pg.fill("#pv-editor", original)
    assert pg.is_hidden("#pv-modified")
    pg.click("#pv-cancel")
    pg.wait_for_selector("#pv-edit", state="visible")
    assert pg.is_hidden("#pv-modified")
    pg.set_viewport_size({"width": 1500, "height": 900})


@pytest.mark.parametrize("fails", [False, True])
def test_editor_late_write_does_not_touch_next_file(page, fails):
    page.open("notes/plain.txt")
    page.click("#pv-edit")
    page.fill("#pv-editor", "saved asynchronously")
    page.evaluate("""() => {
      const write = FS.write;
      window.__writeCount = 0;
      FS.write = async (node, text) => {
        window.__writeCount++;
        try {
          await new Promise((resolve, reject) => {
            window.__finishWrite = fails => fails ? reject(new Error('late failure')) : resolve();
          });
          await write(node, text);
        } finally { window.__writeFinished = true; }
      };
    }""")
    page.click("#pv-save")
    page.wait_for_function("typeof window.__finishWrite === 'function'")
    assert page.eval_on_selector("#pv-editor", "e => e.readOnly")
    assert page.is_disabled("#pv-save")
    page.press("#pv-editor", "Control+z")
    assert page.input_value("#pv-editor") == "saved asynchronously"
    assert page.evaluate("window.__writeCount") == 1
    page.click('.col[data-i="1"] .row:has-text("short.txt")')
    page.wait_for_selector("#pv-edit", state="visible")
    page.click("#pv-edit")
    page.wait_for_selector("#pv-editor")
    page.evaluate("fails => window.__finishWrite(fails)", fails)
    page.wait_for_function("window.__writeFinished === true")
    assert page.input_value("#pv-editor") == "short"
    assert page.inner_text("#pv-edit-err") == ""
    assert page.is_hidden("#pv-modified")
    page.click('.col[data-i="1"] .row:has-text("plain.txt")')
    page.wait_for_selector("#pv-edit", state="visible")
    page.click("#pv-edit")
    page.wait_for_selector("#pv-editor")
    assert page.input_value("#pv-editor") == (
        "hello" if fails else "saved asynchronously"
    )
    assert page.is_hidden("#pv-modified")
    assert not page.errors


def test_editor_late_read_does_not_replace_next_editor(page):
    page.open("notes/plain.txt")
    page.wait_for_selector("#pv-edit", state="visible")
    page.evaluate("""() => {
      const blob = FS.blob;
      FS.blob = async node => {
        FS.blob = blob;
        await new Promise(resolve => { window.__finishRead = resolve; });
        const result = await blob(node);
        window.__readFinished = true;
        return result;
      };
    }""")
    page.click("#pv-edit")
    page.wait_for_function("typeof window.__finishRead === 'function'")
    page.click('.col[data-i="1"] .row:has-text("short.txt")')
    page.wait_for_selector("#pv-edit", state="visible")
    page.click("#pv-edit")
    page.wait_for_selector("#pv-editor")
    page.evaluate("() => { window.__finishRead(); }")
    page.wait_for_function("window.__readFinished === true")
    assert page.input_value("#pv-editor") == "short"
    assert page.is_hidden("#pv-modified")
    assert not page.errors


def test_editor_normalizes_newlines_and_undoes_replacements_and_composition(page):
    page.open("notes/plain.txt")
    page.wait_for_selector("#pv-edit", state="visible")
    page.evaluate("""() => {
      const blob = FS.blob;
      FS.blob = async () => {
        FS.blob = blob;
        return new Blob(['alpha\\r\\nbeta\\r\\n']);
      };
    }""")
    page.click("#pv-edit")
    page.wait_for_selector("#pv-editor")
    assert page.input_value("#pv-editor") == "alpha\nbeta\n"
    assert page.is_hidden("#pv-modified")
    page.eval_on_selector("#pv-editor", "e => e.setSelectionRange(0, 5)")
    page.keyboard.insert_text("replaced")
    assert page.input_value("#pv-editor") == "replaced\nbeta\n"
    page.press("#pv-editor", "Control+z")
    assert page.input_value("#pv-editor") == "alpha\nbeta\n"
    assert page.eval_on_selector(
        "#pv-editor", "e => [e.selectionStart, e.selectionEnd]"
    ) == [0, 5]
    assert page.is_hidden("#pv-modified")
    page.eval_on_selector(
        "#pv-editor",
        """e => {
      e.dispatchEvent(new CompositionEvent('compositionstart', {bubbles: true}));
      if (!e.dispatchEvent(new KeyboardEvent('keydown', {
        key: 'z', ctrlKey: true, bubbles: true, cancelable: true, isComposing: true
      }))) throw new Error('Editor intercepted composition undo');
      for (const text of ['a', 'あ']) {
        e.setRangeText(text, 0, e.selectionEnd, 'select');
        e.dispatchEvent(new InputEvent('input', {bubbles: true, isComposing: true}));
      }
      e.dispatchEvent(new CompositionEvent('compositionend', {bubbles: true}));
    }""",
    )
    assert page.is_visible("#pv-modified")
    page.press("#pv-editor", "Control+z")
    assert page.input_value("#pv-editor") == "alpha\nbeta\n"
    assert page.is_hidden("#pv-modified")


def test_editor_find_reveals_long_lines_and_keeps_composition_input(page):
    page.open("notes/plain.txt")
    page.click("#pv-edit")
    page.fill("#pv-editor", "needle" + "x" * 500 + "needle")
    page.eval_on_selector(
        "#pv-editor", "e => { e.setSelectionRange(0, 0); e.scrollLeft = 0; }"
    )
    page.press("#pv-editor", "Control+f")
    search = page.locator('input[aria-label="Find in file"]')
    search.fill("needle")
    # Enter belongs to the IME while it is composing a search query.
    assert search.evaluate("""e => e.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Enter', bubbles: true, cancelable: true, isComposing: true
    }))""")
    assert search.evaluate("e => document.activeElement === e")
    search.press("Enter")
    page.keyboard.press("Enter")
    assert page.eval_on_selector("#pv-editor", "e => e.selectionStart") == 506
    assert page.eval_on_selector("#pv-editor", "e => e.scrollLeft > 0")
    page.keyboard.press("Enter")
    assert page.eval_on_selector("#pv-editor", "e => e.selectionStart") == 0
    assert page.eval_on_selector("#pv-editor", "e => e.scrollLeft") == 0
    page.keyboard.press("Escape")
    assert page.is_hidden(".pv-find")
