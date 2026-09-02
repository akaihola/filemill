"""Browser tests for keyboard navigation, URL sync and the mobile layout.

Two shells are under test. `/` serves the shared Miller-columns UI
(server/src/filemill/ui, which the repo-root ui/ symlinks to); the tests that
drive it fetch nothing from a CDN and run offline. The legacy htmx shell still
serves `/f/`, and the tests that drive it load htmx from unpkg.com — that is
what the proxy plumbing below exists for.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from textwrap import dedent
from urllib.parse import urlsplit

import pytest

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _proxy_from_env() -> dict[str, str] | None:
    """Return Playwright's proxy settings from ``$HTTPS_PROXY``, or None.

    The htmx finder shell at /f/ loads htmx from unpkg.com and mermaid from
    cdn.jsdelivr.net. Chromium reads ``$HTTPS_PROXY`` but drops the credentials
    in it, so behind an authenticated proxy both scripts come back "407 Proxy
    Authentication Required", ``window.htmx`` stays undefined, and every click
    is ignored. The tests then fail on their navigation assertions, which reads
    like a routing regression and is not one. Passing the credentials here is
    what makes the /f/ tests run in a sandbox at all.
    """
    url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not url:
        return None
    parts = urlsplit(url)
    if not parts.hostname or not parts.username:
        return None
    return {
        "server": f"{parts.scheme}://{parts.hostname}:{parts.port}",
        "username": parts.username,
        "password": parts.password or "",
        # Without a bypass Chromium sends the test server's own 127.0.0.1 address
        # to the proxy, which answers 502 Bad Gateway and no page ever loads.
        "bypass": os.environ.get("NO_PROXY") or "localhost,127.0.0.1,::1",
    }


def _launch(p):
    """Headless Chromium, carrying the environment's proxy when there is one."""
    return p.chromium.launch(headless=True, proxy=_proxy_from_env())


@pytest.fixture()
def browser_root(tmp_path: Path) -> Path:
    kb = tmp_path / "my-knowledge"
    kb.mkdir()
    (kb / "AGENTS.md").write_text("# Agent notes\n")
    docs = kb / "docs"
    docs.mkdir()
    (docs / "topic.md").write_text("# Topic\n\n[Next](subdir/next.md)\n")
    subdir = docs / "subdir"
    subdir.mkdir()
    (subdir / "next.md").write_text("# Next\n")
    (tmp_path / "root-note.md").write_text("# Root\n")
    return tmp_path


# Long enough that measure() returns its 380 px ceiling for every column, which
# is the content browser_root deliberately does not have: its 271, 176 and 148 px
# columns are what makes the peek in
# test_mobile_folder_tap_keeps_the_touched_column_whole_and_peeks_the_new_one
# reachable at all, and widening them would delete a contract that is still
# right. Wide content therefore gets a fixture of its own. Six levels because
# landscape needs the depth: at 568 px the strip only reaches past the touched
# column once five ancestors have folded to spines.
_WIDE_NAMES = [f"level-{i}-" + "w" * 36 for i in range(6)]


@pytest.fixture()
def wide_root(tmp_path: Path) -> Path:
    """A chain of long-named folders, one file beside each."""
    current = tmp_path
    for name in _WIDE_NAMES:
        current = current / name
        current.mkdir()
        (current / f"note-{name}.md").write_text(f"# {name}\n")
    return tmp_path


@contextmanager
def _serve(root: Path):
    """Run `filemill <root>` on a free port for the duration of the block."""
    if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        pytest.skip("PLAYWRIGHT_BROWSERS_PATH is not set")

    port = _free_port()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    cmd = [
        "uv",
        "run",
        "filemill",
        str(root),
        "--bind",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 15
    ready = False
    while time.time() < deadline:
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=0.5)
            sock.close()
            ready = True
            break
        except OSError:
            time.sleep(0.2)

    if not ready:
        out = ""
        if proc.stdout is not None:
            try:
                out = proc.stdout.read()
            except Exception:
                out = ""
        proc.kill()
        raise RuntimeError(
            dedent(
                f"""\
                filemill test server did not start on {base_url}
                output:
                {out}
                """
            )
        )

    try:
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture()
def live_server(browser_root: Path):
    with _serve(browser_root) as base_url:
        yield base_url


@pytest.fixture()
def wide_live_server(wide_root: Path):
    with _serve(wide_root) as base_url:
        yield base_url


_FIND_LINK = """() => {
    const col = document.getElementById(%r);
    return col && Array.from(col.querySelectorAll('li a'))
        .find(a => a.textContent.includes(%r));
}"""


def _wait_for_htmx(page) -> None:
    """Wait until htmx has loaded and the document has finished parsing.

    Every column entry is ``<a href="#" hx-get="/click?...">``. Clicking one
    before htmx has loaded does nothing at all, and nothing retries it, so the
    caller then waits out its full timeout for a column that will never appear.
    htmx comes from unpkg.com, and `wait_until="networkidle"` does not guarantee
    it has executed: one probe run of six had ``typeof window.htmx ===
    'undefined'`` 800 ms after `goto` returned.
    """
    page.wait_for_function(
        "() => typeof window.htmx !== 'undefined'"
        " && document.readyState === 'complete'",
        timeout=30000,
    )


def _click_item(page, col_id: str, text: str) -> None:
    """Click the entry whose text contains *text* in column *col_id*.

    The waits are the point. The shell fills its columns after the page reports
    networkidle, so on a loaded machine a fixed sleep can expire while #col-0 is
    still empty. This helper used to guard the click with `if (link)` and return
    quietly when the entry was missing, which turned that race into an
    unexplained `assert 0 == 1` two lines later in the caller. Measured on a
    4-core host with 4 busy loops running: 2 of 6 attempts found no #col-0 at
    800 ms and the element was there by 5700 ms.
    """
    _wait_for_htmx(page)
    finder = _FIND_LINK % (col_id, text)
    page.wait_for_function(f"() => Boolean(({finder})())", timeout=20000)
    page.evaluate(f"() => {{ ({finder})().click(); }}")


def _expect_column(page, col_id: str) -> None:
    """Assert column *col_id* is present, waiting for it instead of guessing.

    The shell builds a column after the page reports networkidle, so a fixed
    `wait_for_timeout` is a bet on how loaded the machine is. Measured on this
    4-core host with four busy loops running, #col-0 was still absent 800 ms
    after `goto` in 2 of 6 attempts. Waiting keeps the assertion and drops the
    bet: a column that never arrives still fails, now with a TimeoutError that
    names the selector.
    """
    page.wait_for_selector(f"#{col_id}.column", timeout=20000)
    assert page.locator(f"#{col_id}.column").count() == 1


def _expect_preview(page) -> None:
    """Assert the preview pane holds text, waiting for the text to arrive."""
    page.wait_for_function(
        "() => { const p = document.querySelector('#preview');"
        " return Boolean(p && p.innerText.trim()); }",
        timeout=20000,
    )
    assert page.locator("#preview").inner_text().strip()


def _expect_url_ending(page, suffix: str) -> None:
    """Assert the address bar ends with *suffix*, waiting for the navigation."""
    page.wait_for_url(lambda url: url.endswith(suffix), timeout=20000)
    assert page.url.endswith(suffix)


def _wait_for_finder_scroll(page) -> None:
    """Wait until #finder exists, has scrolled right, and has stopped moving.

    Both shells move #finder.scrollLeft smoothly — `scrollFinderToReveal()` in
    styles.py for the htmx one, `scroll-behavior: smooth` plus layout() for the
    shared one — so the movement starts late and then takes time. A fixed sleep
    is a bet on how loaded the machine is, and one run of 29 lost it: it read
    `document.getElementById('finder')` as null 1100 ms after `goto` and failed
    on `assert scroll_left is not None`. Waiting for a settled position leaves
    every assertion that follows exactly as it was.
    """
    page.wait_for_function(
        "() => { const f = document.getElementById('finder');"
        " return Boolean(f && f.scrollLeft > 0); }",
        timeout=20000,
    )
    previous = None
    for _ in range(40):  # 40 x 100 ms, a 4 s ceiling on the smooth scroll
        current = page.evaluate("() => document.getElementById('finder').scrollLeft")
        if current == previous:
            return
        previous = current
        page.wait_for_timeout(100)
    raise AssertionError("#finder never stopped scrolling")


# ── The shared UI at / ───────────────────────────────────────────────────────
#
# `/` used to serve the htmx shell the helpers above drive; it now serves the
# shared Miller-columns UI (index() → resource() → _ui_shell), so the tests
# that drive `/` do it the way tests/test_browser_new_ui.py does: the UI's own
# selectors and globals, and no htmx.
#
# The mobile intent survives a model change. The htmx shell translated #finder
# horizontally and the tests measured that the newest column was scrolled into
# view, minimally. The shared UI condenses instead of panning: scrollLeft is a
# 0–100% dial that folds left columns to spines (ui/core/layout.js), so "the
# scroll fired" becomes "the dial engaged" (scrollLeft > 0), "minimal scroll"
# becomes layout()'s own least-folding target, and "nothing is flushed
# off-screen" becomes "every column starts inside the finder viewport, and the
# ones up to the focused column sit wholly inside it".

MOBILE_VIEWPORT = {"width": 390, "height": 844}
# Not the same device rotated (844x390): this fixture's columns are 271, 176
# and 148 px wide, so at 844 the strip never overflows past the focused column
# and a fold-cap check there would assert nothing. 568x320 is a small phone in
# landscape — where the fold actually reaches the column under the finger.
MOBILE_LANDSCAPE = {"width": 568, "height": 320}


@contextmanager
def _ui_page(base_url: str, mobile: bool = False, viewport: dict | None = None):
    """A page on the shared UI at `/`, mounted and painted.

    No proxy is handed to Chromium: the shared UI fetches nothing from a CDN
    (test_browser_new_ui.py pins that), and launching without one keeps these
    tests honest about it.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        if mobile:
            context = browser.new_context(
                viewport=viewport or MOBILE_VIEWPORT, is_mobile=True, has_touch=True
            )
            page = context.new_page()
        else:
            page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(base_url)
        page.wait_for_function("typeof path !== 'undefined' && path.length >= 1")
        page.wait_for_timeout(400)
        try:
            yield page
        finally:
            browser.close()


def _dial_settled(page) -> None:
    """Wait until #finder's smooth scroll has stopped moving, at any position."""
    previous = None
    for _ in range(40):  # 40 x 100 ms — a 4 s ceiling
        current = page.evaluate("document.getElementById('finder').scrollLeft")
        if current == previous:
            return
        previous = current
        page.wait_for_timeout(100)
    raise AssertionError("#finder never stopped scrolling")


def _ui_tap(page, col: int, name: str) -> None:
    """Tap the entry *name* in column *col*, unfolding the column first.

    Since layout() stopped folding past the focused column, nothing a test taps
    arrives folded — not even the root at first paint. The spine step stays
    because a folded column hides its rows and advertises "click to unfold", so
    it is the gesture a phone user makes after scrolling the dial by hand, and
    on an unfolded column it costs one `count()` and does nothing.
    """
    _dial_settled(page)
    sel = f'.col[data-i="{col}"]'
    if page.locator(sel + ".spine").count():
        page.click(sel + ".spine")
        page.wait_for_selector(sel + ":not(.spine)", timeout=20000)
    page.click(f'{sel} .row:has-text("{name}")')
    page.wait_for_timeout(600)


def _expect_ui_column(page, col: int) -> None:
    """Assert column *col* of the shared UI exists, waiting for it."""
    page.wait_for_selector(f'.col[data-i="{col}"]', timeout=20000)


# layout()'s contract, evaluated in the page: the dial rests at the least k
# where the k-folded strip plus the preview's target width fits the stage —
# but never past the focused column, so `expected` carries the same cap.
#
# Containment splits along that cap. Everything up to the focused column is
# what the layout still promises to fit, so it must sit wholly inside the
# finder; a column to the right of focus may run off the edge once the touched
# one holds its full width, and what it owes the reader is a left edge inside
# the viewport — the peek that says the strip scrolls.
_REVEAL_METRICS = """() => {
    const fr = finder.getBoundingClientRect();
    let k = 0;
    while (k < path.length && stripSpan(k) + previewTarget() > finder.clientWidth) k++;
    const expected = Math.round(Math.min(focusCol, k) * foldUnit() * range());
    const cols = [...document.querySelectorAll('.col')];
    const boxes = cols.map(c => c.getBoundingClientRect());
    const pv = document.getElementById('preview');
    const pr = pv && pv.getBoundingClientRect();
    return {
        scrollLeft: finder.scrollLeft,
        expected: expected,
        delta: Math.abs(finder.scrollLeft - expected),
        withinUpToFocus: cols.every((c, i) => +c.dataset.i > focusCol
            || (boxes[i].left >= fr.left - 2 && boxes[i].right <= fr.right + 2)),
        everyColStartsInside: boxes.every(r => r.left >= fr.left - 2
            && r.left <= fr.right - 2),
        firstColVisible: boxes.length > 0 && boxes[0].right > fr.left,
        previewStartVisible: Boolean(pr) && pr.left >= fr.left - 2
            && pr.left <= fr.right - 2,
    };
}"""


# The rule a tap has to obey: the dial may fold what the user has walked past,
# never the column under their finger nor the one that tap just opened.
# `uncapped` re-runs layout()'s raw while-loop, so a check can assert the case
# still has teeth — that the dial would have folded past focus if left alone.
_FOLD_METRICS = """() => {
    let uncapped = 0;
    while (uncapped < path.length &&
           stripSpan(uncapped) + previewTarget() > finder.clientWidth) uncapped++;
    const cols = [...document.querySelectorAll('.col')];
    const touched = cols.find(c => +c.dataset.i === focusCol);
    return {
        folded: folded,
        focusCol: focusCol,
        uncapped: uncapped,
        spinesAtOrRight: cols.filter(c => +c.dataset.i >= focusCol
            && c.classList.contains('spine')).map(c => +c.dataset.i),
        touchedWidth: Math.round(touched.getBoundingClientRect().width),
        naturalWidth: widths[focusCol],
    };
}"""

# The second half of the same rule, and the half the cap cannot deliver: the
# touched column has to be *on screen*, not merely unfolded. Each folded
# ancestor still costs a spine and a gutter, so with long names the column under
# the finger ran off the right edge and #stage clipped it — the row that had
# just been tapped, cut in half. applyScroll answers by sliding the strip left,
# and `unpannedOverflow` is where that column would sit without the slide, so a
# fixture whose columns happen to fit can never make these checks vacuous.
_TOUCHED_METRICS = """() => {
    const fr = finder.getBoundingClientRect();
    const col = document.querySelector(`.col[data-i="${focusCol}"]`);
    const r = col.getBoundingClientRect();
    const row = col.querySelector('.row.sel');
    const rr = row && row.getBoundingClientRect();
    const tf = getComputedStyle(strip).transform;
    const pan = tf && tf !== 'none' ? -new DOMMatrix(tf).m41 : 0;
    return {
        focusCol: focusCol,
        folded: folded,
        pan: Math.round(pan),
        spinesAtOrRight: [...document.querySelectorAll('.col.spine')]
            .map(c => +c.dataset.i).filter(i => i >= focusCol),
        touchedWhole: r.left >= fr.left - 2 && r.right <= fr.right + 2,
        rowWhole: Boolean(rr) && rr.left >= fr.left - 2 && rr.right <= fr.right + 2,
        unpannedOverflow: Math.round(r.right + pan - fr.right),
        stageScroll: stage.scrollLeft,
    };
}"""


@pytest.mark.integration
def test_arrow_left_keeps_browser_url_in_sync(live_server: str):
    """The URL names the selection chain, root-relative, through keyboard moves.

    In the shared UI ← moves *focus* out without closing anything, so it leaves
    the URL alone; re-committing a row in the parent column (↑ here) is the
    navigation that rewrites the URL back up the tree.
    """
    with _ui_page(live_server) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_url_ending(page, "/my-knowledge")
        folder_url = page.url

        _ui_tap(page, 1, "AGENTS.md")
        _expect_url_ending(page, "/my-knowledge/AGENTS.md")
        file_url = page.url

        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(300)
        assert page.evaluate("focusCol") == 0
        assert page.url == file_url  # focus is not navigation

        page.keyboard.press("ArrowUp")  # re-commits the my-knowledge row
        _expect_url_ending(page, "/my-knowledge")
        assert page.url == folder_url


@pytest.mark.integration
def test_nested_column_navigation_keeps_root_mount_in_url(live_server: str):
    """Nested navigation keeps the whole path in the URL.

    The mount prefix this test once asserted is gone by design: on `/` the URL
    path *is* the file path relative to the served root (router-path.js), so
    "the root mount stays in the URL" now means "no segment is ever dropped".
    """
    with _ui_page(live_server) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_url_ending(page, "/my-knowledge")

        _ui_tap(page, 1, "docs")
        _expect_url_ending(page, "/my-knowledge/docs")

        labels = page.eval_on_selector_all(
            '.col[data-i="2"] .row .label', "els => els.map(e => e.textContent)"
        )
        assert labels[0] == "subdir"  # directories still sort before files

        _ui_tap(page, 2, "topic.md")
        _expect_url_ending(page, "/my-knowledge/docs/topic.md")


@pytest.mark.integration
def test_legacy_query_url_canonicalizes_after_nested_navigation(
    live_server: str, browser_root: Path
):
    legacy_path = browser_root / "my-knowledge"

    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(
            f"{live_server}/f/?path={legacy_path}",
            wait_until="networkidle",
        )
        page.wait_for_timeout(800)

        _expect_url_ending(page, f"/f/{browser_root.name}/my-knowledge")

        _click_item(page, "col-1", "docs")
        page.wait_for_timeout(700)
        _expect_url_ending(page, f"/f/{browser_root.name}/my-knowledge/docs")

        _click_item(page, "col-2", "topic.md")
        page.wait_for_timeout(700)
        _expect_url_ending(page, f"/f/{browser_root.name}/my-knowledge/docs/topic.md")

        browser.close()


@pytest.mark.integration
def test_rendered_relative_markdown_link_uses_root_relative_url(
    live_server: str, browser_root: Path
):
    """A link inside rendered Markdown points at the target's own path.

    The browser-level counterpart of the unit tests in test_rendering.py. This
    asserted ``/f/{root}/my-knowledge/docs/subdir/next.md`` before the PLAN-19
    URL contract landed; generated links now use the path relative to the
    configured root. The legacy /f/ URL this test still *navigates to* keeps
    working, which is the other half of the story.
    """
    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/docs/topic.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(900)

        preview_link = page.locator(
            '#preview a[href="/my-knowledge/docs/subdir/next.md'
            '?filemill=render"]'
        ).first
        assert preview_link.count() == 1
        preview_link.click()
        page.wait_for_timeout(900)

        _expect_url_ending(
            page, "/my-knowledge/docs/subdir/next.md?filemill=render"
        )
        assert "Next" in page.locator("#preview").inner_text()

        browser.close()


@pytest.mark.integration
def test_parent_column_survives_preview_after_arrowleft_arrowright_cycle(
    live_server: str,
):
    """A ←/→ cycle around a file preview never loses the parent column.

    The shared UI cannot lose it the way the htmx shell once did (a stale
    sentinel deleted the column on the second preview), because ← moves focus
    without closing anything — which is exactly what this asserts.
    """
    with _ui_page(live_server) as page:
        page.keyboard.press("ArrowDown")  # commit the first row: my-knowledge
        page.wait_for_timeout(400)
        assert page.evaluate("sel[0]") == "my-knowledge"
        _expect_ui_column(page, 1)

        page.keyboard.press("ArrowRight")  # step in; the remembered row commits
        page.wait_for_timeout(500)
        assert page.evaluate("focusCol") == 1
        assert page.evaluate("sel[1]") == "docs"

        page.keyboard.press("ArrowDown")  # docs → AGENTS.md, previewed as a file
        page.wait_for_timeout(400)
        assert page.evaluate("sel[1]") == "AGENTS.md"
        _expect_ui_column(page, 1)
        _expect_preview(page)

        page.keyboard.press("ArrowLeft")  # focus out — the column must survive
        page.wait_for_timeout(300)
        assert page.evaluate("focusCol") == 0
        _expect_ui_column(page, 1)

        page.keyboard.press("ArrowRight")  # re-enter: the cursor row re-commits
        page.wait_for_timeout(500)
        assert page.evaluate("focusCol") == 1
        assert page.evaluate("sel[1]") == "AGENTS.md"
        _expect_ui_column(page, 1)
        _expect_preview(page)


@pytest.mark.integration
def test_mobile_folder_click_reveals_new_column_without_flushing_left(
    live_server: str,
):
    """Navigate two levels deep so three columns plus the preview pane cannot
    fit 390 px. The dial must engage, rest at layout()'s own least-folding
    target, and keep every column — spine or not — inside the viewport.
    """
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "docs")
        _expect_ui_column(page, 2)

        _wait_for_finder_scroll(page)
        metrics = page.evaluate(_REVEAL_METRICS)
        assert metrics["scrollLeft"] > 0, "the dial never engaged"
        assert metrics["delta"] <= 2, (
            f"dial at {metrics['scrollLeft']:.0f}px, layout()'s minimum is "
            f"{metrics['expected']:.0f}px"
        )
        assert metrics["withinUpToFocus"], (
            "a column up to the touched one is clipped outside the viewport"
        )
        assert metrics["everyColStartsInside"], "a column starts past the right edge"
        assert metrics["firstColVisible"], "the root column was flushed off-screen"


@pytest.mark.integration
def test_mobile_file_click_reveals_preview_without_flushing_left(
    live_server: str,
):
    """Tap a file after entering a folder: the preview pane must fill with
    text and start inside the viewport, with the dial at its minimum.

    The pane's own right edge may overflow: previewTarget() floors the reading
    width at 420 px and #preview cannot flex-shrink below it, so on a 390 px
    phone the dial shows the pane's left edge and the delta check stays the
    authoritative one — the same rule the htmx version of this test spelled
    out for its oversized previews.
    """
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")
        _expect_preview(page)

        _wait_for_finder_scroll(page)
        metrics = page.evaluate(_REVEAL_METRICS)
        assert metrics["scrollLeft"] > 0, "the dial never engaged"
        assert metrics["delta"] <= 2, (
            f"dial at {metrics['scrollLeft']:.0f}px, layout()'s minimum is "
            f"{metrics['expected']:.0f}px"
        )
        assert metrics["previewStartVisible"], "the preview starts off-screen"
        assert metrics["withinUpToFocus"], (
            "a column up to the touched one is clipped outside the viewport"
        )


@pytest.mark.integration
def test_mobile_portrait_folder_tap_never_folds_touched_or_right_columns(
    live_server: str,
):
    """Tapping a folder condenses only what is left of it — phone upright.

    layout() grew its fold count until the strip plus the preview fit, bounded
    by nothing but path.length, so on a 390 px screen this chain folded all
    three columns: the one under the finger, and the one that very tap had just
    opened. A tap is the user pointing at a column; answering it by hiding the
    column, or its result, is the bug.
    """
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "docs")
        _expect_ui_column(page, 2)
        _dial_settled(page)

        m = page.evaluate(_FOLD_METRICS)
        assert m["focusCol"] == 1
        assert m["uncapped"] > m["focusCol"], (
            "the dial had no reason to fold past focus here — the check is "
            f"vacuous (uncapped {m['uncapped']}, focus {m['focusCol']})"
        )
        assert m["folded"] <= m["focusCol"], (
            f"{m['folded']} columns folded with focus on {m['focusCol']}"
        )
        assert m["spinesAtOrRight"] == [], (
            f"columns {m['spinesAtOrRight']} folded at or right of the touched one"
        )
        # not ==: at rest the focused column is the one mid-fold, at t ~ 0.002,
        # so sub-pixel scroll rounding can paint it a pixel under its natural
        # width. A spine would be 34 px, which no tolerance hides.
        assert m["touchedWidth"] >= m["naturalWidth"] - 2, (
            f"touched column painted {m['touchedWidth']} of {m['naturalWidth']} px"
        )


@pytest.mark.integration
def test_mobile_landscape_folder_tap_never_folds_touched_column(live_server: str):
    """The same rule with the phone turned sideways.

    Here the fold reached the *parent* — the column holding the row that was
    tapped — rather than the one it opened, which is the second half of the
    same report. One tap is enough to show it: at 568 px the root column plus
    the preview already overflow.
    """
    with _ui_page(live_server, mobile=True, viewport=MOBILE_LANDSCAPE) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_ui_column(page, 1)
        _dial_settled(page)

        m = page.evaluate(_FOLD_METRICS)
        assert m["focusCol"] == 0
        assert m["uncapped"] > m["focusCol"], (
            "the dial had no reason to fold past focus here — the check is "
            f"vacuous (uncapped {m['uncapped']}, focus {m['focusCol']})"
        )
        assert m["folded"] == 0, (
            f"{m['folded']} columns folded with the root column touched"
        )
        assert m["spinesAtOrRight"] == [], (
            f"columns {m['spinesAtOrRight']} folded at or right of the touched one"
        )
        assert m["touchedWidth"] >= m["naturalWidth"] - 2, (
            f"touched column painted {m['touchedWidth']} of {m['naturalWidth']} px"
        )


def _tap_wide_chain(page, levels: int) -> None:
    """Walk `levels` folders down the long-named chain, tapping each in turn."""
    for col, name in enumerate(_WIDE_NAMES[:levels]):
        _ui_tap(page, col, name)
    _expect_ui_column(page, levels)
    _dial_settled(page)


@pytest.mark.integration
def test_mobile_portrait_wide_folder_tap_keeps_the_touched_row_on_screen(
    wide_live_server: str,
):
    """Long names, phone upright: the tapped row must still be readable.

    The fold cap kept the touched column out of the spines and stopped there,
    which is not the same as keeping it visible. Measured at 390 px before the
    pan: two levels in, 292 px of a 376 px column sat inside the viewport and
    #stage clipped the rest — the right-hand side of the row the finger had just
    hit. Every further level cost another 44 px to the ancestor it folded, down
    to 116 px of the column at six.
    """
    with _ui_page(wide_live_server, mobile=True) as page:
        _tap_wide_chain(page, 3)

        m = page.evaluate(_TOUCHED_METRICS)
        assert m["focusCol"] == 2
        assert m["unpannedOverflow"] > 0, (
            "the touched column fits here unaided — the check is vacuous "
            f"(overflow {m['unpannedOverflow']}px, pan {m['pan']}px)"
        )
        assert m["spinesAtOrRight"] == [], (
            f"columns {m['spinesAtOrRight']} folded at or right of the touched one"
        )
        assert m["touchedWhole"], (
            f"the touched column is clipped despite a {m['pan']}px pan"
        )
        assert m["rowWhole"], "the tapped row is cut off at the viewport edge"
        # The pan is the strip's own transform, never a scroll of #stage: that
        # one has no way back, which is what the pin in applyScroll is for.
        assert m["stageScroll"] == 0, "the pan scrolled #stage instead of moving the strip"


@pytest.mark.integration
def test_mobile_landscape_wide_folder_tap_keeps_the_touched_row_on_screen(
    wide_live_server: str,
):
    """The same rule with the phone turned sideways.

    568 px buys four more levels than 390 does before the strip reaches past the
    touched column, so this walks the chain to its end rather than stopping at
    three — the depth is what makes the case, not the orientation.
    """
    with _ui_page(
        wide_live_server, mobile=True, viewport=MOBILE_LANDSCAPE
    ) as page:
        _tap_wide_chain(page, len(_WIDE_NAMES))

        m = page.evaluate(_TOUCHED_METRICS)
        assert m["focusCol"] == len(_WIDE_NAMES) - 1
        assert m["unpannedOverflow"] > 0, (
            "the touched column fits here unaided — the check is vacuous "
            f"(overflow {m['unpannedOverflow']}px, pan {m['pan']}px)"
        )
        assert m["spinesAtOrRight"] == [], (
            f"columns {m['spinesAtOrRight']} folded at or right of the touched one"
        )
        assert m["touchedWhole"], (
            f"the touched column is clipped despite a {m['pan']}px pan"
        )
        assert m["rowWhole"], "the tapped row is cut off at the viewport edge"
        assert m["stageScroll"] == 0, "the pan scrolled #stage instead of moving the strip"


@pytest.mark.integration
def test_mobile_directory_restore_runtime_scroll_position_is_stable(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/docs",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)

        _expect_column(page, "col-2")

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_file_restore_runtime_scroll_position_is_stable(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/AGENTS.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)

        _expect_preview(page)

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_folder_tap_keeps_the_touched_column_whole_and_peeks_the_new_one(
    live_server: str,
):
    """What a tap owes the reader on a phone, now that focus cannot fold.

    This asserted the *opened* column was wholly visible, which the htmx shell
    delivered by panning. It is unreachable once the touched column keeps its
    full width: 271 px of root plus 176 of `my-knowledge` and their gutters
    come to 467 on a 390 px screen. Something has to overflow, and the choice
    the fold cap makes is that it will not be the column under the finger. What
    the new column gets instead is a left edge inside the viewport — the peek
    that says the strip scrolls, and the affordance ISSUES.md #43 asks for.
    """
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_ui_column(page, 1)

        _dial_settled(page)
        geometry = page.evaluate(
            """() => {
                const fr = finder.getBoundingClientRect();
                const box = i => {
                    const c = document.querySelector(`.col[data-i="${i}"]`);
                    return c && c.getBoundingClientRect();
                };
                const touched = box(focusCol), opened = box(focusCol + 1);
                if (!touched || !opened) return null;
                return {
                    touchedWhole: touched.left >= fr.left - 2
                        && touched.right <= fr.right + 2,
                    touchedFolded: document
                        .querySelector(`.col[data-i="${focusCol}"]`)
                        .classList.contains('spine'),
                    openedStartsInside: opened.left >= fr.left - 2
                        && opened.left <= fr.right - 2,
                };
            }"""
        )
        assert geometry is not None
        assert not geometry["touchedFolded"], "the touched column folded"
        assert geometry["touchedWhole"], "the touched column is clipped"
        assert geometry["openedStartsInside"], (
            "the opened column starts past the right edge — no peek to scroll to"
        )


@pytest.mark.integration
def test_mobile_preview_scroll_position_is_not_zero_after_navigation(
    live_server: str,
):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")
        _expect_preview(page)

        _wait_for_finder_scroll(page)
        assert page.evaluate("finder.scrollLeft") > 0


@pytest.mark.integration
def test_mobile_file_restore_scroll_position_is_not_zero(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/AGENTS.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)

        _wait_for_finder_scroll(page)
        scroll_left = page.evaluate(
            """() => {
                const finder = document.getElementById('finder');
                return finder ? finder.scrollLeft : null;
            }"""
        )

        assert scroll_left is not None
        assert scroll_left > 0

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_navigation_runtime_scroll_regression_is_covered(
    live_server: str,
):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_ui_column(page, 1)


@pytest.mark.integration
def test_mobile_preview_runtime_scroll_regression_is_covered(
    live_server: str,
):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")
        _expect_preview(page)


@pytest.mark.integration
def test_mobile_restore_runtime_scroll_regression_is_covered(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/docs",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)
        _expect_column(page, "col-2")

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_restore_preview_runtime_scroll_regression_is_covered(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/AGENTS.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)
        _expect_preview(page)

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_minimal_scroll_runtime_behavior_smoke(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")

        _expect_ui_column(page, 1)
        _expect_preview(page)


@pytest.mark.integration
def test_mobile_column_reveal_and_preview_reveal_both_work(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_ui_column(page, 1)

        _ui_tap(page, 1, "AGENTS.md")
        _expect_preview(page)


@pytest.mark.integration
def test_mobile_scroll_regression_end_to_end(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")

        _expect_ui_column(page, 1)
        _expect_preview(page)


@pytest.mark.integration
def test_mobile_scroll_regression_directory_only(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_ui_column(page, 1)


@pytest.mark.integration
def test_mobile_scroll_regression_preview_only(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")
        _expect_preview(page)


@pytest.mark.integration
def test_mobile_restore_regression_directory_only(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/docs",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)
        _expect_column(page, "col-2")

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_restore_regression_preview_only(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/AGENTS.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)
        _expect_preview(page)

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_behavior_runtime_assertions(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")

        _wait_for_finder_scroll(page)
        assert page.evaluate("finder.scrollLeft") > 0


@pytest.mark.integration
def test_mobile_restore_behavior_preview_assertions(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = _launch(p)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/AGENTS.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(1100)

        _wait_for_finder_scroll(page)
        assert page.evaluate("() => document.getElementById('finder').scrollLeft") > 0

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_behavior_preview_assertions(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")

        _wait_for_finder_scroll(page)
        assert page.evaluate("finder.scrollLeft") > 0


@pytest.mark.integration
def test_mobile_scroll_regression_user_case_is_covered(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_ui_column(page, 1)


@pytest.mark.integration
def test_mobile_scroll_regression_user_case_preview_is_covered(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _ui_tap(page, 1, "AGENTS.md")
        _expect_preview(page)


@pytest.mark.integration
def test_mobile_scroll_runtime_minimal_reveal_assertion(live_server: str):
    with _ui_page(live_server, mobile=True) as page:
        _ui_tap(page, 0, "my-knowledge")
        _expect_ui_column(page, 1)

        _dial_settled(page)
        metrics = page.evaluate(_REVEAL_METRICS)
        assert metrics["withinUpToFocus"], (
            "a column up to the touched one is clipped outside the viewport"
        )
        assert metrics["everyColStartsInside"], "a column starts past the right edge"
        assert metrics["firstColVisible"], "the root column was flushed off-screen"
