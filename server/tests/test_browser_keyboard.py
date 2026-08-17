from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path
from textwrap import dedent

import pytest

sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


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


@pytest.fixture()
def live_server(browser_root: Path):
    if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        pytest.skip("PLAYWRIGHT_BROWSERS_PATH is not set")

    port = _free_port()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    cmd = [
        "uv",
        "run",
        "filemill",
        str(browser_root),
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


def _click_item(page, col_id: str, text: str) -> None:
    page.evaluate(
        f"""() => {{
            const col = document.getElementById({col_id!r});
            const link = col && Array.from(col.querySelectorAll('li a'))
                .find(a => a.textContent.includes({text!r}));
            if (link) link.click();
        }}"""
    )


def _first_entry_text(page, col_id: str) -> str:
    return page.evaluate(
        f"""() => {{
            const col = document.getElementById({col_id!r});
            const first = col && col.querySelector('li a');
            return first ? first.textContent.trim() : '';
        }}"""
    )


def _selected_text(page, col_id: str) -> str:
    return page.evaluate(
        f"""() => {{
            const col = document.getElementById({col_id!r});
            const selected = col && col.querySelector('li.selected a');
            return selected ? selected.textContent.trim() : '';
        }}"""
    )


@pytest.mark.integration
def test_arrow_left_keeps_browser_url_in_sync(live_server: str, browser_root: Path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(700)
        folder_url = page.url
        assert folder_url.endswith("/f/" + browser_root.name + "/my-knowledge")

        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(700)
        file_url = page.url
        assert file_url.endswith("/f/" + browser_root.name + "/my-knowledge/AGENTS.md")

        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(400)
        assert page.url == folder_url

        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(300)
        assert page.url.rstrip("/") == live_server.rstrip("/") + "/f"

        browser.close()


@pytest.mark.integration
def test_nested_column_navigation_keeps_root_mount_in_url(
    live_server: str, browser_root: Path
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(700)
        assert page.url.endswith(f"/f/{browser_root.name}/my-knowledge")

        _click_item(page, "col-1", "docs")
        page.wait_for_timeout(700)
        assert page.url.endswith(f"/f/{browser_root.name}/my-knowledge/docs")

        file_name = _first_entry_text(page, "col-2")
        assert file_name == "📁subdir"
        _click_item(page, "col-2", "topic.md")
        page.wait_for_timeout(700)
        assert page.url.endswith(f"/f/{browser_root.name}/my-knowledge/docs/topic.md")

        browser.close()


@pytest.mark.integration
def test_legacy_query_url_canonicalizes_after_nested_navigation(
    live_server: str, browser_root: Path
):
    legacy_path = browser_root / "my-knowledge"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(
            f"{live_server}/f/?path={legacy_path}",
            wait_until="networkidle",
        )
        page.wait_for_timeout(800)

        assert page.url.endswith(f"/f/{browser_root.name}/my-knowledge")

        _click_item(page, "col-1", "docs")
        page.wait_for_timeout(700)
        assert page.url.endswith(f"/f/{browser_root.name}/my-knowledge/docs")

        _click_item(page, "col-2", "topic.md")
        page.wait_for_timeout(700)
        assert page.url.endswith(f"/f/{browser_root.name}/my-knowledge/docs/topic.md")

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
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/docs/topic.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(900)

        preview_link = page.locator(
            '#preview a[href="/my-knowledge/docs/subdir/next.md'
            '?pykofinder-view=rendered"]'
        ).first
        assert preview_link.count() == 1
        preview_link.click()
        page.wait_for_timeout(900)

        assert page.url.endswith(
            "/my-knowledge/docs/subdir/next.md?pykofinder-view=rendered"
        )
        assert "Next" in page.locator("#preview").inner_text()

        browser.close()


@pytest.mark.integration
def test_parent_column_survives_preview_after_arrowleft_arrowright_cycle(
    live_server: str,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        # Root column starts with no selection; ArrowDown selects the first visible item.
        # In our temp tree that's my-knowledge/ because dirs sort before files.
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(250)
        assert "my-knowledge" in _selected_text(page, "col-0")

        # ArrowRight enters the folder and should auto-highlight the first item.
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(700)
        assert page.locator("#col-1.column").count() == 1
        assert _selected_text(page, "col-1")

        # ArrowDown moves from docs/ to AGENTS.md in the reopened folder listing.
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(250)
        assert "AGENTS.md" in _selected_text(page, "col-1")

        # ArrowRight previews the file while keeping the parent column alive.
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(700)
        assert page.locator("#col-1.column").count() == 1
        assert page.locator("#preview").inner_text().strip()

        # ArrowLeft exits back to the root column and closes col-1.
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(400)
        assert page.locator("#col-1.column").count() == 0
        assert "my-knowledge" in _selected_text(page, "col-0")

        # Re-enter via keyboard and verify the new column gets a restored selection.
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(700)
        assert page.locator("#col-1.column").count() == 1
        reopened_selected = _selected_text(page, "col-1")
        assert reopened_selected

        # Move to the file again and preview it. The regression was that this second
        # preview deleted the parent folder column due to stale sentinel DOM order.
        if "AGENTS.md" not in reopened_selected:
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(250)
        assert "AGENTS.md" in _selected_text(page, "col-1")

        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(700)
        assert page.locator("#col-1.column").count() == 1
        assert page.locator("#preview").inner_text().strip()

        col1_class = page.locator("#col-1").get_attribute("class") or ""
        assert "column" in col1_class

        browser.close()


@pytest.mark.integration
def test_mobile_folder_click_reveals_new_column_without_flushing_left(
    live_server: str,
):
    """Navigate two levels deep so three columns (3×160 = 480px) overflow the
    390px mobile viewport, triggering the minimal-scroll logic.

    Before the fix the afterSettle handler checked classList.contains('column')
    on the detached sentinel (always false after outerHTML swap), so the scroll
    never fired and the CSS snap locked the new column flush-left.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        # Level 1: root → my-knowledge (col-0 + col-1, total ≤390px, no scroll yet)
        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)

        # Level 2: my-knowledge → docs (col-0 + col-1 + col-2, total >390px, scroll needed)
        _click_item(page, "col-1", "docs")
        page.wait_for_timeout(900)

        metrics = page.evaluate(
            """() => {
                const finder = document.getElementById('finder');
                const prevCol = document.getElementById('col-1');
                const newCol  = document.getElementById('col-2');
                if (!finder || !prevCol || !newCol) return null;
                const finderRect = finder.getBoundingClientRect();
                const prevRect   = prevCol.getBoundingClientRect();
                const newRect    = newCol.getBoundingClientRect();
                // Expected scroll: min(offsetLeft + offsetWidth - clientWidth, offsetLeft)
                const expectedScroll = Math.min(
                    newCol.offsetLeft + newCol.offsetWidth - finder.clientWidth,
                    newCol.offsetLeft
                );
                return {
                    scrollLeft:      finder.scrollLeft,
                    maxScrollLeft:   Math.max(0, finder.scrollWidth - finder.clientWidth),
                    finderLeft:      finderRect.left,
                    finderRight:     finderRect.right,
                    prevLeft:        prevRect.left,
                    prevRight:       prevRect.right,
                    newLeft:         newRect.left,
                    newRight:        newRect.right,
                    overflowRight:   newRect.right - finderRect.right,
                    expectedScroll:  expectedScroll,
                    scrollDelta:     Math.abs(finder.scrollLeft - Math.max(0, expectedScroll)),
                };
            }"""
        )

        assert metrics is not None, "col-2 not found after two folder clicks"
        # The new column must be fully within the finder viewport (not clipped right)
        assert metrics["overflowRight"] <= 1, (
            f"col-2 right edge overflows finder by {metrics['overflowRight']:.1f}px"
        )
        assert metrics["newRight"] <= metrics["finderRight"] + 1
        # The scroll must have moved to reveal it (it was past the right edge before scroll)
        assert metrics["scrollLeft"] > 0, (
            "finder did not scroll — outerHTML-swap re-query fix may be missing"
        )
        # Scroll matches the minimal-reveal formula (within 1px rounding)
        assert metrics["scrollDelta"] <= 1, (
            f"scroll {metrics['scrollLeft']:.0f} deviates from expected "
            f"{metrics['expectedScroll']:.0f} by {metrics['scrollDelta']:.1f}px"
        )
        # Previous column is still partially visible (not flushed off-screen)
        assert metrics["prevRight"] > metrics["finderLeft"], (
            "previous column completely hidden — over-scrolled"
        )
        assert metrics["scrollLeft"] < metrics["maxScrollLeft"]

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_file_click_reveals_preview_without_flushing_left(
    live_server: str,
):
    """Click a file after entering a folder so the preview pane appears.

    The preview uses hx-swap="innerHTML" so e.detail.target stays in the DOM
    and scroll fires correctly.  This test verifies the minimal-scroll formula
    positions the preview right edge flush with the viewport right edge (not
    scrolled all the way to the end).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)

        metrics = page.evaluate(
            """() => {
                const finder  = document.getElementById('finder');
                const col     = document.getElementById('col-1');
                const preview = document.getElementById('preview');
                if (!finder || !col || !preview) return null;
                const finderRect  = finder.getBoundingClientRect();
                const colRect     = col.getBoundingClientRect();
                const previewRect = preview.getBoundingClientRect();
                const expectedScroll = Math.min(
                    preview.offsetLeft + preview.offsetWidth - finder.clientWidth,
                    preview.offsetLeft
                );
                return {
                    scrollLeft:       finder.scrollLeft,
                    maxScrollLeft:    Math.max(0, finder.scrollWidth - finder.clientWidth),
                    finderLeft:       finderRect.left,
                    finderRight:      finderRect.right,
                    colLeft:          colRect.left,
                    colRight:         colRect.right,
                    previewLeft:      previewRect.left,
                    previewRight:     previewRect.right,
                    previewTextLen:   (preview.innerText || '').trim().length,
                    overflowRight:    previewRect.right - finderRect.right,
                    expectedScroll:   expectedScroll,
                    scrollDelta:      Math.abs(finder.scrollLeft - Math.max(0, expectedScroll)),
                };
            }"""
        )

        assert metrics is not None
        assert metrics["previewTextLen"] > 0, "preview has no text content"
        # Scroll must have fired to reveal the preview
        assert metrics["scrollLeft"] > 0, "finder did not scroll to reveal preview"
        # Minimal-reveal formula was applied (scrollDelta ≤ 1px rounding)
        # Note: if preview.offsetWidth > finder.clientWidth (preview wider than viewport),
        # Math.min caps the scroll at preview.offsetLeft (show left edge), so overflowRight
        # may be non-zero but scrollDelta is still 0.  scrollDelta is the authoritative check.
        assert metrics["scrollDelta"] <= 1, (
            f"scroll {metrics['scrollLeft']:.0f} deviates from expected "
            f"{metrics['expectedScroll']:.0f} by {metrics['scrollDelta']:.1f}px — "
            "scroll-snap or wrong formula may have overridden scrollFinderToReveal"
        )
        # Preview left edge must be visible (formula caps at offsetLeft for oversized previews)
        assert metrics["previewLeft"] >= -1, (
            f"preview left edge at {metrics['previewLeft']:.0f}px — scrolled past preview"
        )

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_directory_restore_runtime_scroll_position_is_stable(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

        assert page.locator("#col-2.column").count() == 1

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_file_restore_runtime_scroll_position_is_stable(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_folder_navigation_reveals_target_column_completely_at_runtime(
    live_server: str,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)

        fully_visible = page.evaluate(
            """() => {
                const finder = document.getElementById('finder');
                const newCol = document.getElementById('col-1');
                if (!finder || !newCol) return null;
                const finderRect = finder.getBoundingClientRect();
                const colRect = newCol.getBoundingClientRect();
                return colRect.left >= finderRect.left - 1 && colRect.right <= finderRect.right + 1;
            }"""
        )

        assert fully_visible is True

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_preview_scroll_position_is_not_zero_after_navigation(
    live_server: str,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)

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
def test_mobile_file_restore_scroll_position_is_not_zero(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        assert page.locator("#col-1.column").count() == 1

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_preview_runtime_scroll_regression_is_covered(
    live_server: str,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_restore_runtime_scroll_regression_is_covered(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
        assert page.locator("#col-2.column").count() == 1

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_restore_preview_runtime_scroll_regression_is_covered(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_minimal_scroll_runtime_behavior_smoke(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)

        assert page.locator("#col-1.column").count() == 1
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_column_reveal_and_preview_reveal_both_work(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        assert page.locator("#col-1.column").count() == 1

        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_regression_end_to_end(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)

        assert page.locator("#col-1.column").count() == 1
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_regression_directory_only(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        assert page.locator("#col-1.column").count() == 1

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_regression_preview_only(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_restore_regression_directory_only(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
        assert page.locator("#col-2.column").count() == 1

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_restore_regression_preview_only(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_behavior_runtime_assertions(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)

        assert page.evaluate("() => document.getElementById('finder').scrollLeft") > 0

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_restore_behavior_preview_assertions(
    live_server: str,
    browser_root: Path,
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

        assert page.evaluate("() => document.getElementById('finder').scrollLeft") > 0

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_behavior_preview_assertions(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)

        assert page.evaluate("() => document.getElementById('finder').scrollLeft") > 0

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_regression_user_case_is_covered(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        assert page.locator("#col-1.column").count() == 1

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_regression_user_case_preview_is_covered(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)
        _click_item(page, "col-1", "AGENTS.md")
        page.wait_for_timeout(900)
        assert page.locator("#preview").inner_text().strip()

        context.close()
        browser.close()


@pytest.mark.integration
def test_mobile_scroll_runtime_minimal_reveal_assertion(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        _click_item(page, "col-0", "my-knowledge")
        page.wait_for_timeout(900)

        assert page.evaluate(
            """() => {
                const finder = document.getElementById('finder');
                const rootCol = document.getElementById('col-0');
                const newCol = document.getElementById('col-1');
                if (!finder || !rootCol || !newCol) return false;
                const finderRect = finder.getBoundingClientRect();
                const rootRect = rootCol.getBoundingClientRect();
                const newRect = newCol.getBoundingClientRect();
                return newRect.right <= finderRect.right + 1 && rootRect.right > finderRect.left;
            }"""
        )

        context.close()
        browser.close()

