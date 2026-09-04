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
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

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
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "sample.py").write_text(SOURCE)
    (tmp_path / "code" / "nested.json").write_text('{"tags":["a","b"],"n":1}')
    # 11 700 chars: more than the 8 000 the preview used to clip at.
    (tmp_path / "code" / "long.py").write_text(SOURCE * 300)
    # One byte over the preview's 512 KB ceiling.
    (tmp_path / "code" / "huge.py").write_text("x" * (512 * 1024 + 1))
    (tmp_path / "empty").mkdir()
    (tmp_path / "README.md").write_text(
        "# Readme\n\nline one\nline two\n\n```python\n" + SOURCE + "```\n"
    )
    (tmp_path / ".hidden").write_text("h")
    (tmp_path / "log.jsonl").write_text(
        '{"id": 2, "title": "Second", "ts": "2026-01-02"}\n'
        '{"id": 1, "title": "First", "ts": "2026-01-01"}\n'
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
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert "Readme" in page.inner_text("#preview .pv-rich h1")


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
    para = page.eval_on_selector("#preview .pv-rich p", "e=>e.innerHTML")
    assert para == "line one\nline two"


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
    page.open("notes")
    page.click('.col[data-i="1"] .row:has-text("plain.txt")')
    page.wait_for_selector("#pv-edit")
    assert page.inner_text("#pv-content").strip() == "saved"
    page.reload()
    page.wait_for_selector("#pv-edit")
    assert page.inner_text("#pv-content").strip() == "saved"


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
    (inner / "a-wide" / ("a-name-long-enough-to-hit-the-column-cap" * 2 + ".txt")
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


def _click_local(page, name: str, selector: str) -> None:
    """Click a local-folder entry, then hold the render it triggers to account.

    `preview-upload.js` posts the bytes to `POST /api/render`, because the server
    cannot read a file the browser granted through the File System Access API.
    Two of its branches are silent by design, and from the outside they look
    identical to each other and to a slow machine::

        if (!r.ok) return PreviewLocal.render(node);   /* draws no .pv-rich */
        return html.trim() ? `<div class="pv-rich">${html}</div>` : null;

    A non-2xx falls back to a renderer that emits no ``.pv-rich`` at all, and an
    empty body draws nothing. Either way the caller waits out its timeout for a
    selector that will never exist, which is a symptom rather than a cause. A
    peer agent hit exactly that on another host: the POST completed and
    ``#preview .pv-rich h1`` never appeared, and the timeout said nothing about
    why. So this reports the status, the first bytes, and whether ``.pv-rich``
    reached the DOM, which separates a bad response from an error card that
    simply has no heading in it.
    """
    with page.expect_response(
        lambda r: r.url.endswith("/api/render") and r.request.method == "POST",
        timeout=30000,
    ) as caught:
        page.click(f'.col[data-i="0"] .row:has-text("{name}")')
    response = caught.value
    body = response.text()
    assert response.ok, (
        f"POST /api/render answered {response.status} for {name}, so "
        f"preview-upload.js fell back silently and drew no .pv-rich. "
        f"First 300 bytes: {body[:300]!r}"
    )
    assert body.strip(), (
        f"POST /api/render answered 200 with an empty body for {name}, so "
        f"preview-upload.js returned null and drew nothing."
    )
    try:
        page.wait_for_selector(selector, timeout=15000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(
            f"{selector} never appeared for {name}. POST /api/render answered "
            f"{response.status} with {len(body)} bytes, and #preview .pv-rich "
            f"count is {page.locator('#preview .pv-rich').count()}. A count of 0 "
            f"means nothing was injected; a count of 1 means the server rendered "
            f"something without that element in it. "
            f"First 300 bytes: {body[:300]!r}"
        ) from exc


def test_local_files_are_still_rendered_by_python(page):
    """The point of POST /api/render: opening a local folder is not a downgrade.

    markdown-it-py renders bytes the server has never had a path to.
    """
    page.open()
    page.evaluate(FAKE_HANDLE)
    page.evaluate("mount(__local())")
    page.wait_for_timeout(300)
    _click_local(page, "local.md", "#preview .pv-rich h1")
    assert "Local heading" in page.inner_text("#preview .pv-rich h1")
    assert page.locator("#preview .pv-rich strong").count() >= 1


def test_local_source_is_highlighted_without_asking_the_server(page):
    """The gain from moving highlighting into the page: a folder the server has
    no path to is coloured with no round-trip at all, so POST /api/render is
    not reached for it the way local.md still reaches it."""
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
    assert [u for u in posts if u.endswith("/api/render")] == []


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
    goes through preview-upload.js and `POST /api/render`, which is the path the
    docstring is actually about. Source files now go through neither — they are
    coloured in the page by core/syntax.js — so they are the easiest half to
    keep honest and are checked here too. `ui/adapters/preview-rich.js` does lazy-load a
    renderer from a CDN, and it is the one adapter the server edition never
    loads: `_UI_ADAPTERS` omits it, and `wheel-exclude` in `pyproject.toml`
    keeps it out of the wheel. Loading it would break this test, which is the
    point of the test.
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
    # local.py takes neither path: core/syntax.js colours it in the page, so
    # there is no response to wait for — only the absence of a request.
    page.click('.col[data-i="0"] .row:has-text("local.py")')
    page.wait_for_selector("#preview .pv-text .hl-kw", timeout=15000)
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


def test_a_row_previews_through_the_provider(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("sample.db")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("users")')
    page.wait_for_selector('.col[data-i="2"] .row', timeout=15000)
    page.click('.col[data-i="2"] .row >> nth=0')
    page.wait_for_selector("#preview .pv-rich", timeout=15000)
    assert "User1" in page.inner_text("#preview .pv-rich")


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
    page.wait_for_selector("#preview .pv-rich", timeout=15000)
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


def test_highlight_shows_the_source_in_the_columns(page):
    """The view reaches /api/preview through preview-http.js."""
    page.open_resource("notes/deep/leaf.md?filemill=highlight")
    page.wait_for_selector("#preview .pv-rich .preview-code", timeout=15000)
    assert "# Leaf" in page.inner_text("#preview .pv-rich")
    assert page.locator("#preview .pv-rich h1").count() == 0


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
    page.wait_for_selector("#preview .pv-rich", timeout=15000)
    assert "User1" in page.inner_text("#preview .pv-rich")


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
