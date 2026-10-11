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

import io
import json
import random
import shutil
import socket
import sqlite3
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

import pytest

from filemill.providers.archive import zstd_compress

pytest.importorskip("playwright")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

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
BIG_LINES = 20_000


def _minimal_docx(text: str) -> bytes:
    """The smallest .docx mammoth will read: one paragraph, no styles."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>",
        )
    return buf.getvalue()


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
    (tmp_path / "code" / "sample.py.j2").write_text(SOURCE)
    (tmp_path / "code" / "guide.rst").write_text(
        "Guide\n=====\n\nSome *rst* text.\n\n.. code-block:: python\n\n   return 1\n"
    )
    (tmp_path / "code" / "nested.json").write_text(
        '{"tags":["a","b"],"n":1,"meta":{"n":1}}'
    )
    (tmp_path / "code" / "folder.json").mkdir()
    # 11 700 chars: more than the 8 000 the preview used to clip at.
    (tmp_path / "code" / "long.py").write_text(SOURCE * 300)
    # One byte over the preview's 512 KB ceiling.
    (tmp_path / "code" / "huge.py").write_text("x" * (512 * 1024 + 1))
    (tmp_path / "empty").mkdir()
    (tmp_path / "README.md").write_text(
        "# Readme\n\nline one\nline two\n\n```python\n" + SOURCE + "```\n"
    )
    (tmp_path / "page.html").write_text("<h1>Hi</h1>\n")
    from pptx import Presentation
    from pptx.util import Inches

    deck = Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    for y, lines in ((1, ("Hello world", "Second line")), (3, ("Another block",))):
        box = slide.shapes.add_textbox(Inches(1), Inches(y), Inches(4), Inches(1))
        frame = box.text_frame
        paragraph = frame.paragraphs[0]
        paragraph.text = "Hello" if y == 1 else lines[0]
        if y == 1:
            paragraph.add_run().text = "world"
        for line in lines[1:]:
            frame.add_paragraph().text = line
    deck.save(str(tmp_path / "deck.pptx"))
    (tmp_path / "clip.mp4").write_bytes(b"not a playable video")
    # Noise does not compress: both photos are past the 512 KB text ceiling.
    from PIL import Image

    noise = Image.frombytes(
        "RGB", (960, 720), random.Random(65).randbytes(960 * 720 * 3)
    )
    noise.save(tmp_path / "photo.png")
    noise.save(tmp_path / "photo.jpg", quality=95)
    (tmp_path / "guide.md").write_text(
        "intro\n\n# Guide\n\ntext\n\n## Install\n\nsteps\n\n## Use\n\nrun\n"
    )
    (tmp_path / "code" / "manual.rst").write_text(
        "Manual\n======\n\nPart A\n------\n\nSome *alpha* text.\n\nPart B\n------\n\nbeta\n"
    )
    (tmp_path / "soft-breaks.md").write_text("one\ntwo\n\nthree  \nfour\n")
    (tmp_path / "bullets.md").write_text("para\n\n- one\n- two\n")
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
    # Past the 512 KB text ceiling: browsed by line index, not parsed whole.
    big = [f'{{"id": {n}, "title": "Row {n}"}}' for n in range(1, BIG_LINES + 1)]
    big[6] = "nope"
    (tmp_path / "big.jsonl").write_text("\n".join(big) + "\n")
    assert (tmp_path / "big.jsonl").stat().st_size > 512 * 1024
    (tmp_path / "data.csv").write_text(
        'group,id,note\nA,101,hello\nA,102,"comma, value"\n'
    )
    (tmp_path / "duplicate.csv").write_text("group,note\nA,hello\nA,hello\n")
    (tmp_path / "dot.csv").write_text("name,note\n.hidden,hello\n.visible,hello\n")
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
    archive_buf = io.BytesIO()
    with tarfile.open(fileobj=archive_buf, mode="w") as tf:
        info = tarfile.TarInfo("inside/hello.txt")
        info.size = len(b"hello from the archive\n")
        tf.addfile(info, io.BytesIO(b"hello from the archive\n"))
    (tmp_path / "bundle.tar.zst").write_bytes(zstd_compress(archive_buf.getvalue()))
    wide = io.BytesIO()
    Image.new("RGB", (1600, 200), "teal").save(wide, format="PNG")
    with zipfile.ZipFile(tmp_path / "bundle.zip", "w") as zf:
        zf.writestr("data.json", '{"tags":["a","b"],"n":1,"meta":{"n":1}}')
        zf.writestr("wide.png", wide.getvalue())
        zf.writestr(
            "rows.jsonl",
            '{"id": 1, "title": "First"}\n{"id": 2, "title": "Second"}\n',
        )
        zf.writestr(
            "readme.md",
            "# Inside\n\n**bold** member\n\n## Intro\n\nfirst part\n\n## Outro\n\nlast part\n",
        )
        zf.writestr("letter.docx", _minimal_docx("Dear member"))
    if shutil.which("git"):
        repo = tmp_path / ".bundle-source"
        repo.mkdir()
        git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
        (repo / "notes.txt").write_bytes(b"hello from the git bundle\n")
        for cmd in (["init", "-q", "-b", "main"], ["add", "."], ["commit", "-qm", "x"]):
            subprocess.run([*git, *cmd], check=True)
        subprocess.run(
            [*git, "bundle", "create", "-q", str(tmp_path / "repo.bundle"), "--all"],
            check=True,
        )
        shutil.rmtree(repo)
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


def test_search_label_is_read_aloud_but_not_shown(page):
    """The label names the search box for assistive tech and stays off screen.

    `sr-only` is the usual clip-to-a-pixel trick; a label with a real box would
    show "Search file contents" in the top bar on every screen.
    """
    page.open()
    label = page.locator('label[for="search-bar"]')
    assert label.inner_text() == "Search file contents"
    box = label.bounding_box()
    assert box is not None and box["width"] <= 1 and box["height"] <= 1
    expect(page.locator("#search-bar")).to_have_accessible_name("Search file contents")
    assert page.get_by_label("Search file contents").get_attribute("id") == "search-bar"


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
    assert set(names) == {"deep", "plain.txt", "short.txt"}
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


@pytest.mark.parametrize("name", ["photo.png", "photo.jpg"])
def test_an_image_past_the_text_ceiling_is_previewed(page, ui_root, name):
    """Issue 65: the 512 KB ceiling is for text. An image of any size is drawn."""
    assert (ui_root / name).stat().st_size > 512 * 1024
    page.open(name)
    page.wait_for_selector("#preview img.pv-img", timeout=15000)
    width = page.evaluate(
        "() => { const i = document.querySelector('#preview img.pv-img');"
        " return i.decode().then(() => i.naturalWidth) }"
    )
    assert width == 960


def test_preview_fullscreen_control_toggles_and_exits(page):
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    full = page.locator("#pv-fullscreen")

    url = page.url
    history_length = page.evaluate("history.length")
    full.click()
    page.wait_for_function("document.fullscreenElement !== null")
    page.evaluate("window.dispatchEvent(new Event('resize'))")
    assert page.evaluate("document.fullscreenElement !== null")
    assert page.url == url
    assert page.evaluate("history.length") == history_length
    page.wait_for_function(
        "document.documentElement.classList.contains('pv-fullscreen')"
    )
    assert full.get_attribute("aria-pressed") == "true"
    assert (
        page.evaluate("getComputedStyle(document.getElementById('bar')).display")
        == "none"
    )

    full.click()
    page.wait_for_function(
        "!document.documentElement.classList.contains('pv-fullscreen')"
    )
    assert full.get_attribute("aria-pressed") == "false"
    assert (
        page.evaluate("getComputedStyle(document.getElementById('bar')).display")
        != "none"
    )

    full.click()
    page.wait_for_function("document.fullscreenElement !== null")
    page.evaluate("document.exitFullscreen()")
    page.wait_for_function(
        "!document.documentElement.classList.contains('pv-fullscreen')"
    )
    assert full.get_attribute("aria-pressed") == "false"
    assert page.url == url
    assert page.evaluate("history.length") == history_length


def test_preview_fullscreen_falls_back_when_browser_denies_it(page):
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    page.evaluate("""() => {
        Element.prototype.requestFullscreen = async () => {
            throw new Error('Fullscreen unavailable');
        };
    }""")
    full = page.locator("#pv-fullscreen")
    full.click()
    assert full.get_attribute("aria-pressed") == "true"
    assert page.evaluate("document.fullscreenElement === null")
    full.click()
    assert full.get_attribute("aria-pressed") == "false"


TOOLBAR_LABELS = """() => [...document.querySelectorAll('.pv-actions .pv-action')]
    .filter(el => el.checkVisibility()).map(el => el.textContent.trim())"""


@pytest.mark.parametrize(
    "filename,ready",
    [("README.md", "#preview .pv-rich h1"), ("captions.vtt", ".preview-cue")],
)
def test_preview_toolbar_shows_one_raw_control(page, filename, ready):
    """One Raw link for every file type; the view toggle is the Source button."""
    page.open_resource(f"{filename}?filemill=render")
    page.wait_for_selector(ready, timeout=15000)
    assert page.evaluate(TOOLBAR_LABELS) == ["Raw", "Source", "Delete", "Fullscreen"]


def test_markdown_rendered_source_toggle_preserves_navigation(page):
    source = "# Readme\n\nline one\nline two\n\n```python\n" + SOURCE + "```\n"
    page.open_resource("README.md?filemill=render")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    toggle = page.locator("#pv-view")
    assert toggle.inner_text() == "Source"
    assert page.evaluate("sel")[-1] == "README.md"

    toggle.click()
    page.wait_for_function("document.querySelector('#preview .pv-text')?.textContent")
    assert page.locator("#preview .pv-rich h1").count() == 0
    assert page.text_content("#preview .pv-text") == source
    assert toggle.inner_text() == "Rendered"
    assert page.evaluate("sel")[-1] == "README.md"

    toggle.press("Enter")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert toggle.inner_text() == "Source"
    assert page.evaluate("sel")[-1] == "README.md"


def test_vtt_transcript_and_source_views_preserve_navigation(page):
    page.open_resource("captions.vtt?filemill=render")
    page.wait_for_selector(".preview-transcript .preview-cue", timeout=15000)
    assert "00:00:01.000" in page.inner_text("#pv-content")
    assert "Hello world" in page.inner_text("#pv-content")
    assert page.evaluate("sel")[-1] == "captions.vtt"

    page.click("#pv-view")
    page.wait_for_selector("#preview .pv-text", timeout=15000)
    assert "WEBVTT" in page.text_content("#preview .pv-text")
    assert page.locator(".preview-transcript").count() == 0
    assert page.evaluate("sel")[-1] == "captions.vtt"

    page.click("#pv-view")
    page.wait_for_selector(".preview-transcript .preview-cue", timeout=15000)
    assert page.evaluate("sel")[-1] == "captions.vtt"


def test_vtt_empty_and_malformed_files_are_safe(page):
    page.open("empty.vtt")
    assert "no cues" in page.inner_text("#pv-content").lower()
    page.open("bad.vtt")
    assert "malformed webvtt" in page.inner_text("#pv-content").lower()


def test_vtt_highlight_view_keeps_the_source_fallback(page):
    page.open("captions.vtt?filemill=highlight")
    page.wait_for_selector("#preview .pv-text", timeout=15000)
    assert "WEBVTT" in page.inner_text("#preview .pv-text")


@pytest.mark.parametrize("start", ["", "notes/plain.txt?filemill=highlight"])
@pytest.mark.parametrize("activation", ["click", "Enter"])
def test_content_search_opens_a_matching_file(page, start, activation):
    page.open_resource(start)
    previous_url = page.url
    page.evaluate("window.searchNavigationMarker = true")
    page.fill("#search-bar", "Leaf")
    result = page.locator('.search-result[data-path="notes/deep/leaf.md"]')
    result.wait_for()
    assert "# Leaf" in result.inner_text()
    if activation == "click":
        result.click()
    else:
        result.press("Enter")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=render")
    assert page.inner_text("#preview .pv-rich h1") == "Leaf"
    assert page.evaluate("window.searchNavigationMarker") is True
    assert page.locator("#search-results").is_hidden()
    assert page.evaluate("path.slice(1).map(n => n.name)") == ["notes", "deep"]
    assert page.evaluate("sel") == ["notes", "deep", "leaf.md"]
    assert page.evaluate("focusCol") == 2

    page.go_back()
    page.wait_for_url(previous_url)
    page.go_forward()
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    page.keyboard.press("ArrowRight")
    page.wait_for_function("document.activeElement.id === 'preview'")
    page.keyboard.press("ArrowLeft")
    assert page.evaluate("focusCol") == 2
    assert page.evaluate("sel[2]") == "leaf.md"

    raw = page.request.get(f"{page.base}/notes/deep/leaf.md")
    assert raw.text() == "# Leaf\n**bold** text\n"
    assert "text/markdown" in raw.headers["content-type"]
    raw_action = page.locator("#pv-raw").get_attribute("href")
    assert raw_action == "/notes/deep/leaf.md?filemill=raw"
    assert page.request.get(f"{page.base}{raw_action}").body() == raw.body()


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


def test_large_directory_scrolls_in_one_column(page, ui_root):
    """One column, one scrollbar: no pager, a viewport's worth of DOM rows,
    and Home/End reach both ends through the virtualized layer."""
    big = ui_root / "big"
    big.mkdir()
    for i in range(1200):
        (big / f"big-{i:04d}.txt").write_text(str(i))
    page.open("big")
    col = '.col[data-i="1"]'
    page.wait_for_selector(f"{col} .row")
    assert page.locator(".pager").count() == 0
    assert page.inner_text(f"{col} .col-head .count") == "1200"
    fits = page.evaluate(f"""() => {{
        const body = document.querySelector('{col} .col-body');
        return Math.floor(body.clientHeight / body.querySelector('.row').offsetHeight);
    }}""")
    assert fits <= page.locator(f"{col} .row").count() < 1200

    page.click(f'{col} .row:has-text("big-0000.txt")')
    page.keyboard.press("End")
    page.wait_for_function("sel[1] === 'big-1199.txt'")
    body = page.locator(f"{col} .col-body").bounding_box()
    row = page.locator(f"{col} .row.sel").bounding_box()
    assert body["y"] <= row["y"] <= body["y"] + body["height"] - row["height"]
    page.keyboard.press("Home")
    page.wait_for_function("sel[1] === 'big-0000.txt'")

    page.eval_on_selector(f"{col} .col-body", "b => b.scrollTop = b.scrollHeight")
    page.wait_for_selector(f'{col} .row:has-text("big-1199.txt")')
    assert page.locator(f"{col} .row").count() < 1200


def test_deep_link_restores_the_last_entry_of_a_large_directory(page, ui_root):
    """Every entry is addressable: a reload on the last of 1200 files
    restores the selection and scrolls its row into view."""
    big = ui_root / "big"
    big.mkdir()
    for i in range(1200):
        (big / f"big-{i:04d}.txt").write_text(str(i))
    page.open("big/big-1199.txt")
    page.wait_for_function("sel[1] === 'big-1199.txt'", timeout=15000)
    col = '.col[data-i="1"]'
    body = page.locator(f"{col} .col-body").bounding_box()
    row = page.locator(f"{col} .row.sel").bounding_box()
    assert body["y"] <= row["y"] <= body["y"] + body["height"] - row["height"]
    page.wait_for_selector("#preview .pv-text")


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


def test_markdown_list_items_share_paragraph_line_height(page):
    """Bullet lists are set as loosely as paragraphs ([77])."""
    page.open("bullets.md")
    page.wait_for_selector("#preview .pv-markdown li", timeout=15000)
    heights = page.evaluate(
        """() => {
          const lh = (sel) => getComputedStyle(
            document.querySelector('#preview .pv-markdown ' + sel)).lineHeight;
          return [lh('p'), lh('li')];
        }"""
    )
    assert heights[0] == heights[1]


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


def test_jinja_python_source_is_highlighted_in_the_browser(page):
    page.open("code/sample.py.j2")
    page.wait_for_selector("#preview .pv-text .hl-kw", timeout=15000)
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


@pytest.mark.parametrize("mode", ["render", "highlight"])
def test_large_json_previews_and_nested_links_reload(page, ui_root, mode):
    value = {"padding": "x" * (528 * 1024), "nested": {"leaf": "manifest leaf"}}
    (ui_root / "backup-manifest.json").write_text(json.dumps(value))
    page.open_resource(f"backup-manifest.json?filemill={mode}")
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert value["padding"] in page.text_content("#preview .pv-json")
    page.click('.col[data-i="1"] .row:has-text("nested")')
    page.click('.col[data-i="2"] .row:has-text("leaf")')
    page.wait_for_function(
        "document.querySelector('#preview .pv-json-value')?.textContent === 'manifest leaf'"
    )
    page.reload()
    page.wait_for_function(
        "document.querySelector('#preview .pv-json-value')?.textContent === 'manifest leaf'"
    )


def test_json_over_size_limit_is_declined_without_fetching(page, ui_root):
    (ui_root / "huge.json").write_text(" " * (8 * 1024 * 1024 + 1))
    seen = []
    page.on("request", lambda request: seen.append(request.url))
    page.open("huge.json")
    page.wait_for_selector("#preview .pv-err", timeout=15000)
    assert "Too large to browse (over 8 MiB)" in page.inner_text("#preview .pv-err")
    assert not [url for url in seen if "/api/raw" in url]


def test_json_hierarchy_icons(page):
    page.open("code/nested.json")
    page.wait_for_selector('.col[data-i="2"] .row:has-text("tags")', timeout=15000)
    file_icon = page.locator('.col[data-i="1"] .row:has-text("nested.json") .ico')
    assert file_icon.get_attribute("class") == "ico seti"
    assert file_icon.inner_text() == page.evaluate(
        "String.fromCodePoint(parseInt(SETI.ext.json[0], 16))"
    )
    assert (
        page.locator(
            '.col[data-i="1"] .row:has-text("folder.json") .ico.dir svg'
        ).count()
        == 1
    )
    assert page.locator('.col[data-i="2"] .ico.dir').count() == 0
    assert (
        page.locator('.col[data-i="2"] .row:has-text("tags") .ico.glyph').inner_text()
        == "[]"
    )
    assert (
        page.locator('.col[data-i="2"] .row:has-text("meta") .ico.glyph').inner_text()
        == "{}"
    )


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
    assert page.url.endswith("/n/notes/plain.txt?filemill=render")


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


@pytest.mark.parametrize("partial", [False, True])
def test_preview_arrow_folds_then_fullscreen(page, partial):
    page.open("notes/deep/leaf.md")
    page.wait_for_selector("#preview .pv-rich h1")
    page.evaluate("finder.scrollTo({left: 0, behavior: 'instant'})")
    page.wait_for_function("folded === 0")
    snapshot = page.evaluate(
        "({sel: [...sel], focusCol, url: location.href, history: history.length})"
    )
    page.keyboard.press("ArrowRight")
    assert page.evaluate("document.activeElement.id") == "preview"
    assert page.evaluate("finder.scrollLeft") == 0
    if partial:
        page.evaluate(
            "finder.scrollTo({left: .4 * foldUnit() * range(), behavior: 'instant'})"
        )
    for count in range(1, 4):
        page.keyboard.press("ArrowRight")
        page.wait_for_function(
            "n => document.querySelectorAll('.col.spine').length === n",
            arg=count,
            timeout=3000,
        )
        assert page.evaluate(
            "n => Math.abs(finder.scrollLeft - n * foldUnit() * range()) <= 1", count
        )
        assert page.evaluate("document.activeElement.id") == "preview"
        assert not page.evaluate(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "Math.abs(finder.scrollLeft - (finder.scrollWidth - finder.clientWidth)) <= 1"
    )
    assert page.evaluate(
        "[...document.querySelectorAll('.col')].every(c => c.getBoundingClientRect().right <= 1)"
    )
    assert not page.evaluate(
        "document.documentElement.classList.contains('pv-fullscreen')"
    )
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.documentElement.classList.contains('pv-fullscreen') && document.fullscreenElement !== null"
    )
    page.wait_for_function("document.activeElement.id === 'preview'")
    page.keyboard.press("ArrowRight")
    assert page.evaluate("document.documentElement.classList.contains('pv-fullscreen')")
    page.keyboard.press("ArrowLeft")
    page.wait_for_function(
        "!document.documentElement.classList.contains('pv-fullscreen') && !document.fullscreenElement"
    )
    page.wait_for_function("document.activeElement.id === 'preview'")
    assert (
        page.evaluate(
            "({sel: [...sel], focusCol, url: location.href, history: history.length})"
        )
        == snapshot
    )
    page.keyboard.press("ArrowLeft")
    assert page.evaluate("document.activeElement.id") != "preview"
    assert page.evaluate("focusCol") == 2
    assert not page.errors


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize("key", ["ArrowLeft", "Escape"])
def test_preview_arrow_exits_button_fullscreen(page, native, key):
    page.open("notes/deep/leaf.md")
    page.wait_for_selector("#preview .pv-rich h1")
    if not native:
        page.evaluate(
            "() => { document.documentElement.requestFullscreen = async () => { throw Error('denied'); }; }"
        )
    snapshot = page.evaluate(
        "({sel: [...sel], focusCol, url: location.href, history: history.length})"
    )
    page.locator("#pv-fullscreen").click()
    page.wait_for_function(
        "document.documentElement.classList.contains('pv-fullscreen')"
    )
    if native:
        page.wait_for_function("document.fullscreenElement !== null")
    page.locator("#preview").focus()
    page.keyboard.press(key)
    page.wait_for_function(
        "!document.documentElement.classList.contains('pv-fullscreen') && !document.fullscreenElement",
        timeout=3000,
    )
    page.wait_for_function("document.activeElement.id === 'preview'")
    assert (
        page.evaluate(
            "({sel: [...sel], focusCol, url: location.href, history: history.length})"
        )
        == snapshot
    )
    page.keyboard.press("ArrowLeft")
    assert page.evaluate("document.activeElement.id") != "preview"


def test_preview_arrow_focus_survives_resize(page):
    page.open("notes/plain.txt")
    page.keyboard.press("ArrowRight")
    assert page.evaluate("document.activeElement.id") == "preview"
    page.set_viewport_size({"width": 1400, "height": 850})
    page.wait_for_function(
        "parseFloat(document.documentElement.style.getPropertyValue('--stage-w')) === 1400"
    )
    page.wait_for_function("document.activeElement.id === 'preview'", timeout=3000)
    page.locator('.col[data-i="1"] .row[title="short.txt"]').click()
    page.keyboard.press("ArrowLeft")
    assert page.evaluate("focusCol") == 0


def test_preview_arrow_rapid_and_editable(page):
    page.open("notes/deep/leaf.md")
    page.wait_for_selector("#preview .pv-rich h1")
    page.evaluate("finder.scrollTo({left: 0, behavior: 'instant'})")
    page.wait_for_function("folded === 0")
    page.evaluate("""() => {
      const input = document.createElement('input');
      input.value = 'abc';
      document.querySelector('#preview').append(input);
      input.focus({preventScroll: true});
      input.setSelectionRange(1, 1);
    }""")
    page.keyboard.press("ArrowRight")
    assert page.evaluate("document.activeElement.selectionStart") == 2
    assert page.evaluate("finder.scrollLeft") == 0
    page.locator("#preview").focus()
    for _ in range(3):
        page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelectorAll('.col.spine').length === 3", timeout=3000
    )
    assert not page.evaluate(
        "document.documentElement.classList.contains('pv-fullscreen')"
    )


def test_preview_arrows_preserve_layout_then_restore_document_parent(page):
    page.set_viewport_size({"width": 760, "height": 700})
    page.open("notes/deep/leaf.md")
    _scroll_settled(page)
    folded_before = page.evaluate("folded")
    page.keyboard.press("ArrowRight")
    _scroll_settled(page)
    assert page.evaluate("document.activeElement.id") == "preview"
    assert page.evaluate("folded") == folded_before

    page.keyboard.press("ArrowLeft")
    _scroll_settled(page)
    state = page.evaluate(
        "({focusCol, folded, spines: [...document.querySelectorAll('.col.spine')].map(c => +c.dataset.i)})"
    )
    assert state == {"focusCol": 2, "folded": 2, "spines": [0, 1]}


def test_back_steps_out_of_the_folder_it_entered(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_timeout(300)
    page.click('.col[data-i="1"] .row:has-text("deep")')
    page.wait_for_timeout(300)
    page.wait_for_timeout(400)
    deep_url = page.url
    page.go_back()
    page.wait_for_timeout(500)
    assert page.url != deep_url
    assert page.evaluate("sel").count("deep") <= 1


def test_stepping_over_sibling_folders_rewrites_history(page):
    """ADR 0050: ↑/↓ over folders in one column opens them without stacking Back."""
    page.open()
    page.click('.col[data-i="0"] .row:has-text("README.md")')
    page.wait_for_timeout(300)
    before = page.evaluate("history.length")
    for key in ("ArrowUp", "ArrowUp", "ArrowDown", "End", "Home"):
        page.keyboard.press(key)
        page.wait_for_timeout(300)
    assert page.evaluate("path.length") == 2
    assert page.evaluate("history.length") == before


def test_clicking_across_folders_records_history(page):
    """Folder clicks are navigation: each opened folder is a Back step."""
    page.open_resource("?f=")
    before = page.evaluate("history.length")
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_timeout(300)
    page.click('.col[data-i="0"] .row:has-text("code")')
    page.wait_for_timeout(300)
    page.click('.col[data-i="1"] .row:has-text("sample.py")')
    page.wait_for_timeout(300)
    assert page.url.endswith("/code/sample.py?f=&filemill=render")
    assert page.evaluate("history.length") == before + 2
    page.go_back()
    page.wait_for_function("path.length === 2 && sel[0] === 'notes'")
    assert page.url.endswith("/notes?f=")
    page.go_back()
    page.wait_for_function("path.length === 1 && sel.length === 0")
    page.go_forward()
    page.wait_for_function("sel[0] === 'notes'")
    page.go_forward()
    page.wait_for_function("sel[1] === 'sample.py'")


def test_back_retraces_the_folders_that_were_opened(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_timeout(300)
    page.click('.col[data-i="1"] .row:has-text("deep")')
    page.wait_for_timeout(300)
    page.click('.col[data-i="2"] .row:has-text("leaf.md")')
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("plain.txt")')
    page.wait_for_selector("#preview .pv-text")
    page.click('.col[data-i="1"] .row:has-text("short.txt")')
    page.wait_for_timeout(300)
    assert page.url.endswith("/notes/short.txt?filemill=render")

    page.go_back()
    page.wait_for_function("sel[2] === 'leaf.md' && focusCol === 2")
    assert page.url.endswith("/notes/deep/leaf.md?filemill=render")
    page.go_back()
    page.wait_for_function("path.length === 2 && sel.length === 1 && focusCol === 0")
    assert page.url.endswith("/notes")
    page.go_forward()
    page.wait_for_function("sel[2] === 'leaf.md'")
    page.go_forward()
    page.wait_for_function("sel[1] === 'short.txt' && focusCol === 1")
    assert page.url.endswith("/notes/short.txt?filemill=render")


def test_alt_arrows_are_left_to_the_browser(page):
    """Alt+←/→ are the browser's Back and Forward; the finder must not eat them."""
    page.open()
    page.click('.col[data-i="0"] .row:has-text("notes")')
    page.wait_for_timeout(300)
    page.click('.col[data-i="1"] .row:has-text("deep")')
    page.wait_for_timeout(300)
    prevented = page.evaluate(
        """() => ["ArrowLeft", "ArrowRight"].map((key) => {
            const e = new KeyboardEvent("keydown",
                {key, altKey: true, bubbles: true, cancelable: true});
            document.activeElement.dispatchEvent(e);
            return e.defaultPrevented;
        })"""
    )
    assert prevented == [False, False]
    assert page.evaluate("focusCol") == 1
    page.focus("#preview")
    prevented = page.evaluate(
        """() => ["ArrowLeft", "ArrowRight"].map((key) => {
            const e = new KeyboardEvent("keydown",
                {key, altKey: true, bubbles: true, cancelable: true});
            document.activeElement.dispatchEvent(e);
            return e.defaultPrevented;
        })"""
    )
    assert prevented == [False, False]
    assert not page.evaluate("history.state?.filemillFullscreen")


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
    """Vertical navigation retains a deliberate fold with fixed-width columns."""
    inner = ui_root / "w" / "inner"
    (inner / "a-wide").mkdir(parents=True)
    (
        inner / "a-wide" / ("a-name-long-enough-to-hit-the-column-cap" * 2 + ".txt")
    ).write_text("wide")
    (inner / "z-narrow").mkdir()
    (inner / "z-narrow" / "a.txt").write_text("narrow")

    page.set_viewport_size({"width": 1290, "height": 700})
    page.open()
    page.click('.col[data-i="0"] .row[title="w"]')
    page.wait_for_timeout(300)
    page.click('.col[data-i="1"] .row[title="inner"]')
    page.wait_for_timeout(300)
    page.click('.col[data-i="2"] .row[title="a-wide"]')
    _scroll_settled(page)
    page.evaluate("finder.scrollLeft = 2 * foldUnit() * range()")
    _scroll_settled(page)
    folded_before = page.evaluate("folded")
    assert folded_before == 2
    assert page.evaluate("focusCol") == 2

    page.keyboard.press("ArrowDown")  # Select the sibling directory.
    _scroll_settled(page)
    assert page.evaluate("sel[2]") == "z-narrow"
    # Filename length must not change the fixed column widths.
    assert page.evaluate("new Set(widths).size") == 1
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


def test_an_archive_opens_as_columns_and_a_member_previews(page):
    """A .tar.zst is a folder of its members; a text member previews through
    the server, which is the only side that can read inside the archive."""
    page.open()
    page.click('.col[data-i="0"] .row:has-text("bundle.tar.zst")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("inside")')
    page.wait_for_selector('.col[data-i="2"] .row', timeout=15000)
    page.click('.col[data-i="2"] .row:has-text("hello.txt")')
    page.wait_for_function(
        "document.querySelector('#preview').innerText.includes('hello from the archive')",
        timeout=15000,
    )
    assert "/n/bundle.tar.zst/inside/hello.txt" in page.url


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_a_git_bundle_opens_as_refs_then_files_and_a_file_previews(page):
    """A .bundle is a folder of its refs; a ref is a folder of its tree."""
    page.open()
    page.click('.col[data-i="0"] .row:has-text("repo.bundle")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("heads")')
    page.wait_for_selector('.col[data-i="2"] .row', timeout=15000)
    page.click('.col[data-i="2"] .row:has-text("main")')
    page.wait_for_selector('.col[data-i="3"] .row', timeout=15000)
    page.click('.col[data-i="3"] .row:has-text("notes.txt")')
    page.wait_for_function(
        "document.querySelector('#preview').innerText.includes('hello from the git bundle')",
        timeout=15000,
    )
    assert "/n/repo.bundle/heads/main/notes.txt" in page.url


def test_a_json_member_opens_as_columns_of_its_keys_and_previews_foldable(page):
    """A .json inside an archive renders the way the same file does on disk:
    its keys are a column and the preview is the foldable JSON view, built
    from the member's bytes rather than the archive's."""
    page.open()
    page.click('.col[data-i="0"] .row:has-text("bundle.zip")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("data.json")')
    page.wait_for_selector('.col[data-i="2"] .row:has-text("tags")', timeout=15000)
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert json.loads(page.text_content("#preview .pv-json")) == {
        "tags": ["a", "b"],
        "n": 1,
        "meta": {"n": 1},
    }
    page.click('.col[data-i="2"] .row:has-text("tags")')
    page.wait_for_selector('.col[data-i="3"] .row:has-text("0")', timeout=15000)
    page.click('.col[data-i="3"] .row:has-text("0")')
    page.wait_for_function(
        "document.querySelector('#preview .pv-json-value')?.textContent === 'a'",
        timeout=15000,
    )
    assert "/n/bundle.zip/data.json/tags/0" in page.url


def test_a_deep_link_into_a_json_member_reloads(page):
    page.open("bundle.zip/data.json/meta/n")
    page.wait_for_function(
        "document.querySelector('#preview .pv-json-value')?.textContent === '1'",
        timeout=15000,
    )
    assert page.evaluate("sel") == ["bundle.zip", "data.json", "meta", "n"]


def test_a_jsonl_member_opens_as_a_column_of_rows(page):
    page.open()
    page.click('.col[data-i="0"] .row:has-text("bundle.zip")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("rows.jsonl")')
    page.wait_for_selector('.col[data-i="2"] .row:has-text("Second")', timeout=15000)
    page.click('.col[data-i="2"] .row:has-text("Second")')
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert json.loads(page.text_content("#preview .pv-json")) == {
        "id": 2,
        "title": "Second",
    }
    assert "/n/bundle.zip/rows.jsonl/Second" in page.url


def test_an_image_member_is_scaled_to_the_pane_like_a_file_on_disk(page):
    """Issue 85: a 1600 px member drew at its natural size and overflowed
    the pane. It must scale the way the same image on disk does."""
    page.open("bundle.zip/wide.png")
    page.wait_for_selector("#preview img.pv-img", timeout=15000)
    natural, shown, pane = page.evaluate(
        "() => { const i = document.querySelector('#preview img.pv-img');"
        " return i.decode().then(() => [i.naturalWidth, i.clientWidth,"
        " document.querySelector('#preview').clientWidth]) }"
    )
    assert natural == 1600
    assert 0 < shown <= pane < natural


def test_a_markdown_member_renders_like_the_same_file_on_disk(page):
    """Issue 86: a .md inside an archive came back from the server as
    highlighted source. It renders in the browser from the member's bytes,
    the way the same file on disk does, and opens as columns of its
    headings like one too."""
    page.open("bundle.zip/readme.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert "Inside" in page.inner_text("#preview .pv-rich h1")
    assert page.locator("#preview .pv-rich strong").count() == 1
    page.wait_for_selector('.col[data-i="2"] .row:has-text("Outro")', timeout=15000)
    page.click('.col[data-i="2"] .row:has-text("Outro")')
    page.wait_for_function(
        "document.querySelector('#preview .pv-rich')?.innerText.includes('last part')",
        timeout=15000,
    )
    assert "first part" not in page.inner_text("#preview .pv-rich")
    assert "/n/bundle.zip/readme.md/Outro" in page.url


def test_a_docx_member_renders_like_the_same_file_on_disk(page):
    page.open("bundle.zip/letter.docx")
    page.wait_for_selector("#preview .pv-rich p", timeout=15000)
    assert "Dear member" in page.inner_text("#preview .pv-rich p")


def test_a_deep_link_into_an_archive_previews_the_member(page):
    page.open("bundle.tar.zst/inside/hello.txt")
    page.wait_for_function(
        "document.querySelector('#preview').innerText.includes('hello from the archive')",
        timeout=15000,
    )
    assert page.evaluate("path.map(p => p.vpath)")[-1] == "inside"


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


@pytest.mark.parametrize("view", ["render", "highlight"])
def test_pptx_preview_preserves_slide_text_spacing_in_both_views(page, view):
    page.open_resource(f"deck.pptx?filemill={view}")
    page.wait_for_selector("#preview .pv-pptx .slide", timeout=15000)
    assert page.inner_text("#preview .pv-pptx .slide p") == (
        "Hello world\nSecond line\nAnother block"
    )


def test_the_resource_route_keeps_the_query_while_you_browse(page):
    """router-path.js preserves the query, so the view survives a click."""
    page.open_resource("notes/deep/leaf.md?filemill=render")
    page.click('.col[data-i="0"] .row:has-text("code")')
    page.wait_for_timeout(400)
    assert page.url.endswith("/code")


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


def test_raw_navigation_serves_bytes_and_back_restores_finder(page):
    page.open("notes/plain.txt")
    page.click("#pv-raw")
    page.wait_for_url("**/notes/plain.txt?filemill=raw")
    assert page.locator("body").inner_text() == "hello"
    assert page.locator("#preview").count() == 0
    page.go_back()
    page.wait_for_selector("#preview .pv-text")
    assert page.evaluate("sel")[-1] == "plain.txt"


def test_back_from_raw_restores_the_previous_rendered_file(page):
    page.open("notes")
    page.click('.col[data-i="1"] .row:has-text("plain.txt")')
    page.click('.col[data-i="1"] .row:has-text("short.txt")')
    page.click("#pv-raw")
    page.wait_for_url("**/notes/short.txt?filemill=raw")
    page.go_back()
    page.wait_for_selector("#preview .pv-text")
    assert page.url.endswith("/notes/short.txt?filemill=render")
    assert page.evaluate("sel")[-1] == "short.txt"


def test_back_and_forward_restore_folder_preview_and_raw_states(page):
    page.open("notes")
    page.click('.col[data-i="1"] .row:has-text("deep")')
    page.click('.col[data-i="2"] .row:has-text("leaf.md")')
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=render")
    page.click("#pv-raw")
    page.wait_for_url("**/notes/deep/leaf.md?filemill=raw")
    assert "# Leaf" in page.locator("body").inner_text()
    page.go_back()
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.url.endswith("/notes/deep/leaf.md?filemill=render")
    page.go_back()
    page.wait_for_function("path.length === 2 && sel[0] === 'notes'")
    assert page.url.endswith("/notes")
    page.go_forward()
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    page.go_forward()
    page.wait_for_url("**/notes/deep/leaf.md?filemill=raw")


def test_stale_no_columns_link_opens_the_normal_finder(page):
    """The retired ?layout=no-columns falls back to full columns (ADR 0067)."""
    page.open_resource("notes/deep/leaf.md?filemill=render&layout=no-columns")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.evaluate("document.documentElement.dataset.layout") == "full-columns"
    assert page.locator("#strip > .col:visible").count() >= 1
    assert page.is_visible("#bar")
    assert page.is_visible("#trail")


def test_highlight_shows_the_source_in_the_columns(page):
    """Markdown and HTML source use the shared browser highlighter."""
    page.open_resource("notes/deep/leaf.md?filemill=highlight")
    page.wait_for_selector("#preview .pv-text .hl-heading", timeout=15000)
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
    page.wait_for_selector("#preview .pv-text .hl-heading", timeout=15000)
    assert ".. code-block:: python" in page.text_content("#preview .pv-text")


def test_rst_source_and_rendered_modes_switch_without_losing_the_preview(page):
    page.open_resource("code/guide.rst?filemill=render")
    page.wait_for_selector("#preview .preview-rst h1", timeout=15000)
    page.click("#pv-view")
    page.wait_for_selector("#preview .pv-text", timeout=15000)
    assert "Guide" in page.text_content("#preview .pv-text")
    assert page.url.endswith("/code/guide.rst?filemill=highlight")
    page.click("#pv-view")
    page.wait_for_selector("#preview .preview-rst h1", timeout=15000)
    assert "Some rst text." in page.text_content("#preview .preview-rst")


def _rst_tokens(page, source: str) -> list[list[str]]:
    """The [class, text] pairs core/syntax.js wraps in `source`, after checking
    that the highlighted HTML still reads as exactly the source."""
    text, spans = page.evaluate(
        """async (source) => {
            const { hlHTML } = await import('/ui/core/syntax.js');
            const t = document.createElement('template');
            t.innerHTML = hlHTML(source, 'rst');
            const spans = [...t.content.querySelectorAll('span')]
                .map(s => [s.className, s.textContent]);
            return [t.content.textContent, spans];
        }""",
        source,
    )
    assert text == source
    return spans


def test_rst_apostrophes_in_words_are_not_markup(page):
    page.open()
    assert _rst_tokens(page, "Don't use it; it's the user's file.\n") == []
    assert _rst_tokens(page, "It's ``x`` and don't\n") == [["hl-str", "``x``"]]


def test_rst_roles_are_highlighted_like_pygments(page):
    page.open()
    source = "See :ref:`intro`, :func:`os.path` or `text`:role:.\n"
    assert _rst_tokens(page, source) == [
        ["hl-attr", ":ref:"],
        ["hl-var", "`intro`"],
        ["hl-attr", ":func:"],
        ["hl-var", "`os.path`"],
        ["hl-var", "`text`"],
        ["hl-attr", ":role:"],
    ]


def test_rst_syntax_is_highlighted(page):
    page.open()
    cases = {
        "Guide\n=====\n\ntext\n": [["hl-heading", "Guide\n=====\n"]],
        ".. note:: A note.\n": [["hl-kw", "note"]],
        ".. a comment\n   more\n": [["hl-com", ".. a comment\n   more\n"]],
        "Wait, etc.. more\n": [],
        "Some *emph* and **strong**.\n": [
            ["hl-emph", "*emph*"],
            ["hl-strong", "**strong**"],
        ],
        "A `link <http://x>`_ here.\n": [["hl-link", "`link <http://x>`_"]],
        ".. _name: http://example.com\n": [["hl-link", "_name:"]],
        ":field: value\n": [["hl-attr", ":field:"]],
        "Paragraph::\n\n   literal block\n": [["hl-str", "   literal block\n"]],
        "2*3*4 and snake_case_name.\n": [],
        ".. code-block::\n\n   *x* and :ref:`y`\n": [["hl-kw", "code-block"]],
    }
    for source, spans in cases.items():
        assert _rst_tokens(page, source) == spans, source
    code = _rst_tokens(page, ".. code-block:: python\n\n   return 1\n")
    assert ["hl-kw", "code-block"] in code
    assert ["hl-kw", "return"] in code
    assert ["hl-num", "1"] in code


def test_rst_unclosed_markup_is_highlighted_in_linear_time(page):
    """An opener that never closes must not rescan the rest of the paragraph:
    300 KB of them took 15 s when every start searched to the end."""
    page.open()
    elapsed = page.evaluate(
        """async () => {
            const { hlHTML } = await import('/ui/core/syntax.js');
            const t = performance.now();
            hlHTML('a **b '.repeat(50000) + 'a ``b '.repeat(50000), 'rst');
            return performance.now() - t;
        }"""
    )
    assert elapsed < 2000


def test_rst_highlight_view_marks_roles_and_leaves_apostrophes(page, ui_root):
    source = "Title\n=====\n\nIt's the user's :ref:`intro`, isn't it?\n"
    (ui_root / "notes" / "roles.rst").write_text(source)
    page.goto(f"{page.base}/notes/roles.rst?filemill=highlight")
    preview = page.locator("#preview .pv-text")
    preview.locator(".hl-attr").wait_for(timeout=15000)
    assert preview.text_content() == source
    assert preview.locator(".hl-attr").text_content() == ":ref:"
    assert preview.locator(".hl-var").text_content() == "`intro`"
    spans = preview.locator("span").all_text_contents()
    assert not any("'" in s for s in spans)


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
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert page.eval_on_selector_all(
        '.col[data-i="2"] .row', "rows => rows.map(row => row.title)"
    ) == ["id", "title", "ts"]
    assert json.loads(page.text_content("#preview .pv-json")) == {
        "id": 2,
        "title": "Second",
        "ts": "2026-01-02",
    }
    assert [u for u in seen if "/api/preview" in u] == []


def test_a_large_jsonl_file_opens_as_a_column_of_line_rows(page):
    page.open("")
    page.click('.col[data-i="0"] .row:has-text("big.jsonl")')
    page.wait_for_selector('.col[data-i="1"] .row', timeout=15000)
    names = page.eval_on_selector_all(
        '.col[data-i="1"] .row', "els => els.slice(0, 3).map(e => e.title)"
    )
    assert names == ["line 1", "line 2", "line 3"]
    assert page.evaluate("path[1].kids.length") == BIG_LINES
    assert page.locator('.col[data-i="1"] .col-note').count() == 0


def test_a_large_jsonl_row_previews_in_the_browser_without_asking_the_server(page):
    seen: list[str] = []
    page.on("request", lambda r: seen.append(r.url))
    page.open("big.jsonl/line 2")
    assert page.evaluate("sel")[-1] == "line 2"
    page.wait_for_selector("#preview .pv-json", timeout=15000)
    assert '"id": 2' in page.inner_text("#preview .pv-json")
    assert [u for u in seen if "/api/preview" in u] == []


def test_a_malformed_line_in_a_large_jsonl_file_fails_on_its_own_row(page):
    page.open("big.jsonl/line 7")
    page.wait_for_selector("#preview .pv-err", timeout=15000)
    assert "Not valid JSONL: line 7" in page.inner_text("#preview .pv-err")
    assert page.evaluate("sel")[-1] == "line 7"
    assert page.locator('.col[data-i="1"] .row[title="line 8"]').count() == 1


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


@pytest.mark.parametrize(
    "width,height,expected",
    [
        (1440, 900, 240),
        (1024, 768, 240),
        (390, 844, 195),
        (844, 390, 211),
    ],
)
def test_responsive_widths_survive_keyboard_and_mouse(page, width, height, expected):
    page.set_viewport_size({"width": width, "height": height})
    page.open()
    page.evaluate("finder.style.scrollBehavior = 'auto'")
    for name in ["notes", "empty", "README.md"]:
        page.locator('.col[data-i="0"] .row').filter(has_text=name).first.click()
        page.wait_for_function("name => sel[0] === name", arg=name)
        assert page.evaluate(
            "expected => widths.every(w => Math.abs(w - expected) < 0.1)", expected
        )
        assert page.locator(".col").first.bounding_box()["width"] == pytest.approx(
            expected
        )
    for key in ["ArrowDown", "ArrowUp", "Home", "End", "PageUp", "PageDown"]:
        page.keyboard.press(key)
        assert page.locator(".col").first.bounding_box()["width"] == pytest.approx(
            expected
        )
    page.locator('.col[data-i="0"] .row').filter(has_text="README.md").first.click()
    box = page.locator("#preview").bounding_box()
    assert min(box["x"] + box["width"], width) - max(box["x"], 0) >= width / 3 - 1
    assert page.evaluate("""() => {
        const pane = document.getElementById('preview').getBoundingClientRect();
        return [...document.querySelectorAll('.pv-actions button, .pv-actions a')]
            .filter(el => el.getClientRects().length)
            .every(el => {const box = el.getBoundingClientRect();
                return box.left >= pane.left && box.right <= pane.right;});
    }""")
    assert not page.errors


@pytest.fixture()
def scalar_files(ui_root):
    record = {
        "name": "Row",
        "text": "first\n<b>second</b>",
        "zero": 0,
        "empty": "",
        "none": None,
        "": "empty key",
    }
    (ui_root / "scalar.json").write_text(json.dumps(record))
    (ui_root / "scalar.jsonl").write_text(json.dumps(record) + "\n")
    with sqlite3.connect(ui_root / "scalar.db") as db:
        db.execute(
            "CREATE TABLE cells (name TEXT, text TEXT, zero INTEGER, "
            'empty TEXT, none TEXT, "" TEXT)'
        )
        db.execute(
            "INSERT INTO cells VALUES (?, ?, ?, ?, ?, ?)", tuple(record.values())
        )


@pytest.mark.parametrize("source", ["scalar.json", "scalar.jsonl", "scalar.db"])
def test_selected_scalar_preview(page, source, scalar_files):
    page.open(source)
    if source.endswith(".db"):
        page.locator(".row .label").filter(has_text="cells").click()
    if not source.endswith(".json"):
        column = 2 if source.endswith(".db") else 1
        page.locator(f'.col[data-i="{column}"] .row').first.click()
    page.wait_for_selector("#preview .pv-json")
    parent_url = page.url
    page.locator(".row .label").filter(has_text="text").click()
    page.wait_for_selector("#preview .pv-json-value", timeout=3000)
    value = page.locator("#preview .pv-json-value")
    assert value.text_content() == "first\n<b>second</b>"
    assert value.locator("b").count() == 0
    assert value.evaluate("e => getComputedStyle(e).whiteSpace") == "pre-wrap"
    page.keyboard.press("ArrowDown")
    page.wait_for_function(
        "document.querySelector('.pv-json-value')?.textContent === '0'"
    )
    scalar_url = page.url
    page.reload()
    page.wait_for_function(
        "document.querySelector('.pv-json-value')?.textContent === '0'"
    )
    assert page.url == scalar_url
    page.keyboard.press("ArrowRight")
    page.wait_for_function("document.activeElement.id === 'preview'")
    page.keyboard.press("ArrowLeft")
    page.wait_for_function("document.activeElement.id !== 'preview'")
    page.goto(parent_url)
    page.wait_for_selector("#preview .pv-json")
    assert page.url == parent_url
    page.reload()
    page.wait_for_selector("#preview .pv-json")
    assert page.url == parent_url
    page.locator('.row[title=""]').click()
    page.wait_for_function(
        "document.querySelector('.pv-json-value')?.textContent === 'empty key'"
    )


@pytest.mark.parametrize("extension", ["md", "markdown"])
def test_markdown_highlight_links_preserve_source_and_navigation(
    page, ui_root, extension
):
    source = (
        "# Heading [next](leaf.md?hidden=show#leaf)\n\n"
        "It's prose and here's more.\n"
        "https://example.org/path.\n"
        "[reference][ref]\n\n[ref]: leaf.md\n"
        "`[code](hidden.md)`\n\n```markdown\n[code](hidden.md)\n```\n"
    )
    name = f"notes/deep/source.{extension}"
    (ui_root / name).write_text(source)
    page.goto(f"{page.base}/{name}?filemill=highlight")
    preview = page.locator("#preview .pv-text")
    preview.wait_for()
    assert preview.text_content() == source
    assert preview.locator(".hl-heading").count() == 1
    assert preview.locator("a").count() == 3
    link = preview.locator("a").first
    assert (
        link.get_attribute("href")
        == "/notes/deep/leaf.md?hidden=show&filemill=render#leaf"
    )
    if extension == "md":
        link.click()
    else:
        link.focus()
        page.keyboard.press("Enter")
    page.wait_for_url("**/leaf.md?hidden=show&filemill=render#leaf")
    page.locator("#preview .pv-markdown h1").wait_for()
    assert page.locator("#preview .pv-markdown h1").inner_text() == "Leaf"


@pytest.mark.parametrize("view", ["render", "highlight"])
def test_markdown_link_paths_and_queries(page, ui_root, view):
    cases = [
        (
            "sibling",
            "leaf.md?x=1&filemill=highlight#leaf",
            "/notes/deep/leaf.md?x=1&filemill=highlight#leaf",
        ),
        (
            "parent",
            "../other%20file.markdown?x=1#top",
            "/notes/other%20file.markdown?x=1&filemill=render#top",
        ),
        ("spaces", "<space name.md>", "/notes/deep/space%20name.md?filemill=render"),
        ("balanced", "file(a).md", "/notes/deep/file(a).md?filemill=render"),
        ("empty", "", ""),
        ("angle", " <file(name.md> ", "/notes/deep/file(name.md?filemill=render"),
        ("quoted", r"next.md 'don\'t'", "/notes/deep/next.md?filemill=render"),
        ("titled", 'leaf.md "Title ("', "/notes/deep/leaf.md?filemill=render"),
        ("unicode", "note😀.md", "/notes/deep/note%F0%9F%98%80.md?filemill=render"),
        ("escaped", r"file\(b\).md", "/notes/deep/file(b).md?filemill=render"),
        ("root", "/README.md?filemill=render", "/README.md?filemill=render"),
        (
            "external",
            "https://example.org/a?x=1&y=2#top",
            "https://example.org/a?x=1&y=2#top",
        ),
        ("fragment", "#top", "#top"),
        ("query", "?filemill=raw", "?filemill=raw"),
        ("home", "~/note.md", "/note.md?f"),
        (
            "backlog",
            (
                "~/prg/pykoclaw-dev/pykoclaw-acp/backlog/004-tool-call-visibility.md"
                "#streaming-restore-plan-buffered-semantic-windows"
            ),
            (
                "/prg/pykoclaw-dev/pykoclaw-acp/backlog/004-tool-call-visibility.md"
                "?f#streaming-restore-plan-buffered-semantic-windows"
            ),
        ),
        ("keepview", "~/note.md?filemill=highlight", "/note.md?filemill=highlight"),
        ("textfile", "~/data.txt", "/data.txt"),
    ]
    source = "\n\n".join(f"[{label}]({href})" for label, href, _ in cases)
    (ui_root / "notes/deep/links.md").write_text(source)
    page.goto(f"{page.base}/notes/deep/links.md?filemill={view}")
    page.locator("#preview a", has_text="sibling").wait_for()
    for label, _, expected in cases:
        link = page.locator("#pv-content a", has_text=label)
        assert link.count() == 1
        assert link.get_attribute("href") == expected
    if view == "highlight":
        assert page.locator("#preview .pv-text").text_content() == source


@pytest.mark.parametrize("view", ["render", "highlight"])
def test_markdown_links_reject_unsafe_and_code_destinations(page, ui_root, view):
    source = (
        "[bad](javascript:alert(1))\n\n[bad](JaVaScRiPt:alert(1))\n\n"
        "[bad](javascript&#58;alert(1))\n\n[bad](java&#x09;script:alert(1))\n\n"
        "[bad](data:text/html,test)\n\n[bad](file:///etc/passwd)\n\n"
        "[bad](vbscript:alert(1))\n\n"
        "`[code](hidden.txt)`\n\n```markdown\n[code](hidden.txt)\n```\n\n"
        r"\[escaped](hidden.txt)"
        "\n\n[broken](missing.txt\n\n"
        "<img src=x onerror=alert(1)>\n"
    )
    (ui_root / "notes/deep/unsafe.md").write_text(source)
    page.goto(f"{page.base}/notes/deep/unsafe.md?filemill={view}")
    page.locator(
        "#preview .pv-text" if view == "highlight" else "#preview .pv-markdown"
    ).wait_for()
    assert page.locator("#pv-content a").count() == 0, page.locator(
        "#pv-content a"
    ).evaluate_all("es => es.map(e => e.outerHTML)")
    assert page.locator("#pv-content img").count() == 0
    if view == "highlight":
        assert page.locator("#preview .pv-text").text_content() == source


def test_markdown_render_keeps_safe_embedded_images(page, ui_root):
    (ui_root / "embedded.md").write_text("![pixel](data:image/png;base64,aGVsbG8=)")
    page.goto(f"{page.base}/embedded.md?filemill=render")
    image = page.locator("#pv-content img[alt=pixel]")
    image.wait_for(state="attached")
    assert image.get_attribute("src") == "data:image/png;base64,aGVsbG8="


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_context_menu_desktop_and_keyboard(page, scheme):
    page.emulate_media(color_scheme=scheme)
    page.open("notes/plain.txt")
    page.evaluate("""() => {
        Object.defineProperty(navigator, 'clipboard', {configurable: true,
          value: {writeText: async text => window.copied = text}});
    }""")
    before = page.url
    row = page.locator('.col[data-i="0"] .row[aria-label="code"]')
    row.click(button="right")
    menu = page.locator("#row-menu")
    menu.wait_for(state="visible")
    assert page.url == before
    colors = menu.evaluate("""el => {
        const s = getComputedStyle(el);
        return [s.backgroundColor, s.color];
    }""")
    assert colors == (
        ["rgb(255, 255, 255)", "rgb(22, 23, 26)"]
        if scheme == "light"
        else ["rgb(38, 41, 46)", "rgb(233, 234, 238)"]
    )
    menu.get_by_role("menuitem", name="Copy name", exact=True).click()
    page.wait_for_function("window.copied === 'code'")
    row.click(button="right")
    page.keyboard.press("Escape")
    assert menu.is_hidden()
    assert row.get_attribute("aria-expanded") == "false"
    file = page.locator('.col[data-i="1"] .row[aria-label="plain.txt"]')
    file.click()
    page.keyboard.press("Shift+F10")
    menu.wait_for(state="visible")
    assert menu.get_by_role("menuitem").first.evaluate(
        "e => e === document.activeElement"
    )
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    page.wait_for_function("window.copied === 'notes/plain.txt'")
    assert menu.is_hidden()
    page.keyboard.press("ContextMenu")
    menu.wait_for(state="visible")
    page.keyboard.press("Escape")
    page.keyboard.press("ArrowDown")
    page.wait_for_function("sel[1] === 'short.txt'")
    assert not page.errors


def test_preview_delete_cancel_confirm_and_keyboard(page, ui_root):
    page.open("notes/plain.txt")
    before = page.url
    requests = []
    page.on(
        "request", lambda r: requests.append(r.url) if r.method == "DELETE" else None
    )
    page.once("dialog", lambda d: d.dismiss())
    page.locator("#pv-delete").click()
    assert (ui_root / "notes/plain.txt").exists()
    assert requests == []
    assert page.url == before
    page.once("dialog", lambda d: d.accept())
    page.locator("#pv-delete").click()
    page.wait_for_function("sel[1] === undefined && focusCol === 1")
    assert not (ui_root / "notes/plain.txt").exists()
    assert len(requests) == 1
    assert page.locator('.col[data-i="1"] .row[aria-label="plain.txt"]').count() == 0
    assert "hello" not in page.locator("#preview").inner_text()
    assert "plain.txt" not in page.url
    assert "bad" not in (page.locator("#st-refresh").get_attribute("class") or "")
    page.keyboard.press("ArrowDown")
    page.wait_for_function("sel[1] === 'deep'")
    page.keyboard.press("ArrowDown")
    page.wait_for_function("sel[1] === 'short.txt'")
    assert not page.errors


def test_delete_key_deletes_selected_files_and_directories_but_not_editors(
    page, ui_root
):
    page.open()
    row = page.locator('.col[data-i="0"] .row[aria-label="short.txt"]')
    page.once("dialog", lambda d: d.accept())
    row.click()
    page.keyboard.press("Delete")
    row.wait_for(state="detached")
    assert not (ui_root / "short.txt").exists()

    folder = page.locator('.col[data-i="0"] .row[aria-label="notes"]')
    page.once("dialog", lambda d: d.accept())
    folder.click()
    page.keyboard.press("Delete")
    folder.wait_for(state="detached")
    assert not (ui_root / "notes").exists()

    page.open()
    page.evaluate(
        "() => { const input = document.createElement('input'); "
        "input.id = 'test-editor'; document.body.append(input); input.focus(); }"
    )
    page.keyboard.press("Delete")
    count = page.locator('.col[data-i="0"] .row').count()
    page.evaluate(
        "() => { document.querySelector('#test-editor').remove(); sel[0] = undefined; }"
    )
    page.keyboard.press("Delete")
    assert page.locator('.col[data-i="0"] .row').count() == count
    assert (ui_root / "README.md").exists()
    assert not page.errors


@pytest.mark.parametrize("failure", ["remove", "refresh"])
def test_preview_delete_reports_failure(page, ui_root, failure):
    page.open("notes/plain.txt")
    method = "remove" if failure == "remove" else "ensureLoaded"
    page.evaluate(
        "method => { FS[method] = async () => { throw new Error('test denied'); }; }",
        method,
    )
    page.once("dialog", lambda d: d.accept())
    page.locator("#pv-delete").click()
    message = "Delete failed" if failure == "remove" else "Deleted; refresh failed"
    page.wait_for_function(
        "message => document.querySelector('#st-refresh').textContent === message",
        arg=f"{message}: test denied",
    )
    assert (ui_root / "notes/plain.txt").exists() == (failure == "remove")
    assert "bad" in page.locator("#st-refresh").get_attribute("class")
    assert not page.locator("#pv-delete").is_disabled()
    assert not page.errors


@pytest.mark.parametrize("name", ["short.txt", "notes"])
def test_context_menu_delete_cancel_then_confirm(page, ui_root, name):
    page.open("notes/plain.txt")
    row = page.locator(f'.col[data-i="0"] .row[aria-label="{name}"]')
    before = page.url
    requests = []
    page.on(
        "request", lambda r: requests.append(r.url) if r.method == "DELETE" else None
    )
    row.click(button="right")
    page.once("dialog", lambda d: d.dismiss())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    assert (ui_root / name).exists()
    assert requests == []
    assert page.url == before
    row.click(button="right")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    row.wait_for(state="detached")
    assert not (ui_root / name).exists()
    assert len(requests) == 1
    if name == "notes":
        page.wait_for_function("path.length === 1")
        assert "/notes" not in page.url
        assert "hello" not in page.locator("#preview").inner_text()
    else:
        assert page.url == before
        assert page.locator("#pv-content").inner_text().strip() == "hello"
    assert not page.errors


def test_context_menu_delete_failure_and_virtual_entry(page, ui_root):
    page.open()
    row = page.locator('.col[data-i="0"] .row[aria-label="short.txt"]')
    page.route(
        "**/api/delete?*",
        lambda route: route.fulfill(
            status=403, content_type="application/json", body='{"error":"test denied"}'
        ),
    )
    row.click(button="right")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#st-refresh').textContent.includes('Delete failed: test denied')"
    )
    assert row.is_visible()
    assert (ui_root / "short.txt").exists()
    page.open("sample.db")
    virtual = page.locator('.col[data-i="1"] .row').first
    virtual.click(button="right")
    page.locator("#row-menu").wait_for(state="visible")
    assert page.get_by_role("menuitem", name="Delete", exact=True).count() == 0
    assert (ui_root / "sample.db").exists()


def test_context_menu_delete_during_navigation(page, ui_root):
    page.open("notes/plain.txt")
    page.evaluate("""() => {
        const remove = FS.remove;
        window.removeCalls = 0;
        FS.remove = node => { window.removeCalls++;
          return new Promise(resolve => window.finishDelete = async () => {
            await remove(node); resolve();
          });
        };
    }""")
    row = page.locator('.col[data-i="1"] .row[aria-label="plain.txt"]')
    row.click(button="right")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    page.wait_for_function("window.removeCalls === 1")
    row.click(button="right")
    assert page.get_by_role("menuitem", name="Delete", exact=True).is_disabled()
    page.keyboard.press("Escape")
    page.locator('.col[data-i="0"] .row[aria-label="code"]').click()
    page.wait_for_url("**/n/code")
    before = page.url
    page.evaluate("window.finishDelete()")
    assert page.url == before
    assert not (ui_root / "notes/plain.txt").exists()
    assert page.evaluate("window.removeCalls") == 1
    page.locator('.col[data-i="0"] .row[aria-label="notes"]').click()
    page.wait_for_function("path.length === 2 && path[1].name === 'notes'")
    assert page.locator('.col[data-i="1"] .row[aria-label="plain.txt"]').count() == 0
    assert not page.errors


def test_context_menu_delete_stays_disabled_until_refresh(page, ui_root):
    page.open()
    page.evaluate("""() => {
        const load = FS.ensureLoaded;
        FS.ensureLoaded = async node => {
          if (node === path[0] && node.kids === null) {
            await new Promise(resolve => window.finishRefresh = resolve);
          }
          return load(node);
        };
    }""")
    row = page.locator('.col[data-i="0"] .row[aria-label="short.txt"]')
    row.click(button="right")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    page.wait_for_function("typeof window.finishRefresh === 'function'")
    assert not (ui_root / "short.txt").exists()
    row.click(button="right")
    assert page.get_by_role("menuitem", name="Delete", exact=True).is_disabled()
    page.evaluate("window.finishRefresh()")
    row.wait_for(state="detached")
    assert page.locator("#row-menu").is_hidden()


def test_context_menu_delete_reports_refresh_failure(page, ui_root):
    page.open()
    page.evaluate(
        "() => { FS.ensureLoaded = async () => { throw new Error('test refresh denied'); }; }"
    )
    page.locator('.col[data-i="0"] .row[aria-label="short.txt"]').click(button="right")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    page.wait_for_function(
        "document.querySelector('#st-refresh').textContent.includes('Deleted; refresh failed: test refresh denied')"
    )
    assert not (ui_root / "short.txt").exists()
    assert not page.errors


def test_context_menu_delete_retry_after_reopening(page, ui_root):
    page.open("short.txt")
    page.evaluate("""() => {
        const remove = FS.remove;
        FS.remove = () => new Promise((resolve, reject) => {
          window.failDelete = () => {
            FS.remove = remove;
            reject(new Error('temporary failure'));
          };
        });
    }""")
    row = page.locator('.col[data-i="0"] .row[aria-label="short.txt"]')
    row.click(button="right")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    page.wait_for_function("typeof window.failDelete === 'function'")
    row.click(button="right")
    delete = page.get_by_role("menuitem", name="Delete", exact=True)
    assert delete.is_disabled()
    page.evaluate("render()")
    assert page.locator("#pv-delete").is_disabled()
    page.evaluate("window.failDelete()")
    page.wait_for_function(
        "document.querySelector('#st-refresh').textContent.includes('temporary failure')"
    )
    assert not delete.is_disabled()
    assert not page.locator("#pv-delete").is_disabled()
    page.once("dialog", lambda d: d.accept())
    delete.click()
    row.wait_for(state="detached")
    assert not (ui_root / "short.txt").exists()


@pytest.mark.parametrize("folder", ["", "notes/"])
def test_context_menu_delete_stays_disabled_after_reload(page, ui_root, folder):
    page.open(folder + "short.txt")
    page.evaluate("""() => {
        const remove = FS.remove;
        FS.remove = node => new Promise(resolve => {
          window.finishDelete = async () => { await remove(node); resolve(); };
        });
    }""")
    column = 1 if folder else 0
    row = page.locator(f'.col[data-i="{column}"] .row[aria-label="short.txt"]')
    row.click(button="right")
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("menuitem", name="Delete", exact=True).click()
    page.wait_for_function("typeof window.finishDelete === 'function'")
    page.evaluate("refreshColumn(0)")
    row.click(button="right")
    assert page.get_by_role("menuitem", name="Delete", exact=True).is_disabled()
    page.keyboard.press("Escape")
    page.evaluate("window.finishDelete()")
    row.wait_for(state="detached")
    assert not (ui_root / folder / "short.txt").exists()


def test_context_menu_preserves_keyboard_refresh(page, ui_root):
    page.open("notes/plain.txt")
    page.evaluate("window.contextMenuSentinel = 42")
    (ui_root / "notes" / "fresh.txt").write_text("new file")
    page.keyboard.press("Shift+F10")
    page.locator("#row-menu").wait_for(state="visible")
    page.keyboard.press("F5")
    page.locator("#row-menu").wait_for(state="hidden", timeout=5000)
    page.locator('.col[data-i="1"] .row[aria-label="fresh.txt"]').wait_for()
    assert page.evaluate("window.contextMenuSentinel") == 42
    assert page.evaluate("sel[1]") == "plain.txt"


@pytest.mark.parametrize("native", [False, True])
def test_mobile_fullscreen_back_preserves_preview(server, playwright, native):
    browser = playwright.chromium.launch()
    try:
        page = browser.new_page(
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        page.goto(server + "/notes/plain.txt?filemill=highlight")
        page.wait_for_selector("#pv-content .pv-text")
        if not native:
            page.evaluate("document.documentElement.requestFullscreen = undefined")
        url = page.url
        page.evaluate("window.savedPreview = document.querySelector('#pv-content')")
        full = page.locator("#pv-fullscreen")
        full.click()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        if native:
            page.wait_for_function("document.fullscreenElement !== null")
        page.go_back()
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen')"
        )
        page.wait_for_function("document.fullscreenElement === null")
        assert page.url == url
        assert page.evaluate("sel.at(-1)") == "plain.txt"
        assert page.evaluate("savedPreview === document.querySelector('#pv-content')")
        assert page.locator("#bar").is_visible()
        assert page.locator("#pv-content").inner_text() == "hello"
        page.go_forward()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        assert page.url == url
        full.click()
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen') && !history.state?.filemillFullscreen"
        )
        assert page.url == url
        assert page.evaluate("savedPreview === document.querySelector('#pv-content')")
        page.go_forward()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        if native:
            full.click()
            page.wait_for_function("!history.state?.filemillFullscreen")
            full.click()
            page.wait_for_function("document.fullscreenElement !== null")
            page.evaluate("document.exitFullscreen()")
            page.wait_for_function(
                "!document.documentElement.classList.contains('pv-fullscreen') && !history.state?.filemillFullscreen"
            )
            assert page.url == url
    finally:
        browser.close()


@pytest.mark.parametrize("change", ["reload", "view", "file"])
def test_mobile_fullscreen_history_after_preview_change(server, playwright, change):
    browser = playwright.chromium.launch()
    try:
        page = browser.new_page(
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        page.goto(server + "/notes/deep/leaf.md?filemill=highlight")
        page.wait_for_selector("#pv-content .pv-text")
        page.evaluate("document.documentElement.requestFullscreen = undefined")
        full = page.locator("#pv-fullscreen")
        full.click()
        if change == "reload":
            page.reload()
            page.wait_for_selector("#pv-content .pv-text")
        elif change == "file":
            page.evaluate("applyPath(['notes', 'plain.txt'])")
            page.wait_for_function("sel.at(-1) === 'plain.txt'")
            page.go_back()
            page.wait_for_function("sel.at(-1) === 'leaf.md'", timeout=3000)
        else:
            page.locator("#pv-view").click()
            page.wait_for_selector("#preview .pv-rich h1")
            page.go_back()
            page.wait_for_selector("#preview .pv-text", timeout=3000)
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')", timeout=3000
        )
        page.wait_for_function(
            "document.querySelector('#pv-content').textContent.includes('# Leaf')"
        )
        url = page.url
        content = page.locator("#pv-content").inner_text()
        page.go_back()
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen')",
            timeout=3000,
        )
        assert page.url == url
        assert page.locator("#pv-content").inner_text() == content
        page.go_forward()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')", timeout=3000
        )
        assert page.url == url
        full.click()
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen')",
            timeout=3000,
        )
    finally:
        browser.close()


TASKS_MD = "# Tasks\n\n- [ ] one\n- [x] two\n\ntext - [ ] kept\n"
TASK_BOX = "#preview .pv-rich input.task-list-item-checkbox"


def _open_tasks(page, ui_root: Path) -> Path:
    tasks = ui_root / "tasks.md"
    tasks.write_text(TASKS_MD)
    page.open("tasks.md")
    page.wait_for_selector(f"{TASK_BOX}:not([disabled])", timeout=15000)
    return tasks


def test_markdown_task_checkboxes_toggle_the_source(page, ui_root):
    tasks = _open_tasks(page, ui_root)
    boxes = page.locator(TASK_BOX)
    assert boxes.count() == 2
    assert page.locator("#pv-editor").count() == 0
    assert [boxes.nth(i).get_attribute("data-source-line") for i in (0, 1)] == [
        "2",
        "3",
    ]
    before = page.evaluate("({sel: [...sel], path: path.map(n => n.name)})")
    boxes.nth(0).check()
    page.wait_for_function(f"!document.querySelector('{TASK_BOX}').disabled")
    assert tasks.read_text() == TASKS_MD.replace("- [ ] one", "- [x] one")
    boxes.nth(1).uncheck()
    page.wait_for_function(
        f"[...document.querySelectorAll('{TASK_BOX}')].every(b => !b.disabled)"
    )
    assert tasks.read_text() == ("# Tasks\n\n- [x] one\n- [ ] two\n\ntext - [ ] kept\n")
    assert page.evaluate("({sel: [...sel], path: path.map(n => n.name)})") == before
    # The clicked box keeps focus, and preview keys still work from it.
    page.wait_for_function(
        "document.activeElement.matches('input.task-list-item-checkbox')"
    )
    page.keyboard.press("Space")
    page.wait_for_function(f"!document.querySelectorAll('{TASK_BOX}')[1].disabled")
    assert tasks.read_text() == TASKS_MD.replace("- [ ] one", "- [x] one")
    page.keyboard.press("ArrowLeft")
    page.wait_for_function("!document.activeElement.closest('#preview')")
    page.click('.col[data-i="0"] .row:has-text("tasks.md")')
    page.wait_for_selector("#pv-edit", state="visible")
    page.click("#pv-edit")
    page.wait_for_selector("#pv-editor")
    assert page.input_value("#pv-editor") == tasks.read_text()
    assert not page.errors


@pytest.mark.parametrize(
    "changed",
    [
        "# Tasks\n\n- [x] one\n",
        "# Tasks\n\none\n- [ ] two\n",
        "# Tasks\n\n- [ ] zero\n- [ ] one\n- [x] two\n",
    ],
)
def test_markdown_task_checkbox_rejects_changed_source(page, ui_root, changed):
    tasks = _open_tasks(page, ui_root)
    tasks.write_text(changed)
    page.locator(TASK_BOX).nth(0).click()
    page.wait_for_function(
        "document.querySelector('#st-refresh').textContent.includes('not saved')"
    )
    page.wait_for_function(f"!document.querySelector('{TASK_BOX}').disabled")
    assert not page.locator(TASK_BOX).nth(0).is_checked()
    assert "bad" in page.locator("#st-refresh").get_attribute("class")
    assert tasks.read_text() == changed
    assert not page.errors


def test_markdown_task_late_write_targets_its_own_file(page, ui_root):
    tasks = _open_tasks(page, ui_root)
    page.evaluate("""() => {
      const write = FS.write;
      window.__targets = [];
      FS.write = async (node, text) => {
        window.__targets.push(node.rel);
        await new Promise(resolve => { window.__finishWrite = resolve; });
        await write(node, text);
        window.__writeFinished = true;
      };
    }""")
    page.locator(TASK_BOX).nth(0).click()
    page.wait_for_function("typeof window.__finishWrite === 'function'")
    page.click('.col[data-i="0"] .row:has-text("short.txt")')
    page.wait_for_selector("#pv-edit", state="visible")
    page.evaluate("window.__finishWrite()")
    page.wait_for_function("window.__writeFinished === true")
    assert page.evaluate("window.__targets") == ["tasks.md"]
    assert tasks.read_text() == TASKS_MD.replace("- [ ] one", "- [x] one")
    assert (ui_root / "short.txt").read_text() == "short"
    assert not page.errors


def test_markdown_headings_open_as_columns_in_the_server_build(page):
    """A document's headings are columns, a section is a URL, and it reloads;
    a file whose only heading is its title stays a file."""
    page.open("guide.md")
    page.wait_for_selector('.col[data-i="1"] .row:has-text("Guide")', timeout=15000)
    assert page.evaluate("sel") == ["guide.md"]
    assert page.url.endswith("/guide.md?filemill=render")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    page.click('.col[data-i="1"] .row:has-text("Guide")')
    page.wait_for_url("**/guide.md/Guide?filemill=render")
    page.wait_for_selector('.col[data-i="2"] .row:has-text("Install")', timeout=15000)
    page.click('.col[data-i="2"] .row:has-text("Install")')
    page.wait_for_url("**/guide.md/Guide/Install?filemill=render")
    page.wait_for_function(
        "document.querySelector('#preview .pv-rich')?.textContent.includes('steps')"
    )
    assert "intro" not in page.text_content("#preview .pv-rich")
    page.open_resource("guide.md/Guide/Install?filemill=render")
    page.wait_for_function('JSON.stringify(sel) === \'["guide.md","Guide","Install"]\'')
    page.keyboard.press("ArrowLeft")
    page.wait_for_url("**/guide.md/Guide?filemill=render")
    page.keyboard.press("ArrowLeft")
    page.wait_for_url("**/guide.md?filemill=render")
    page.wait_for_function(
        "document.querySelector('#preview .pv-rich')?.textContent.includes('intro')"
    )
    assert page.evaluate("sel") == ["guide.md"]
    page.open("README.md")
    page.wait_for_selector("#preview .pv-rich h1", timeout=15000)
    assert page.evaluate("path.length") == 1
    assert page.evaluate("sel") == ["README.md"]


def test_rst_sections_render_through_the_server_in_the_server_build(page):
    page.open("code/manual.rst")
    page.wait_for_selector('.col[data-i="2"] .row:has-text("Part A")', timeout=15000)
    page.click('.col[data-i="2"] .row:has-text("Part A")')
    page.wait_for_url("**/code/manual.rst/Part%20A?filemill=render")
    page.wait_for_selector("#preview .preview-rst h1", timeout=15000)
    text = page.text_content("#preview .preview-rst")
    assert "Some alpha text." in text and "beta" not in text
    assert page.locator("#preview .preview-rst em").inner_text() == "alpha"

    page.keyboard.press("ArrowLeft")
    page.wait_for_url("**/code/manual.rst?filemill=render")
    page.wait_for_function(
        "document.querySelector('#preview .preview-rst')?.textContent.includes('beta')"
    )
    assert "Some alpha text." in page.text_content("#preview .preview-rst")
    assert page.evaluate("sel") == ["code", "manual.rst"]
