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
        "pykofinder",
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
                pykofinder test server did not start on {base_url}
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

        _click_item(page, "col-2", "topic.md")
        page.wait_for_timeout(700)
        assert page.url.endswith(f"/f/{browser_root.name}/my-knowledge/docs/topic.md")

        browser.close()


@pytest.mark.integration
def test_rendered_relative_markdown_link_uses_canonical_url(
    live_server: str, browser_root: Path
):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(
            f"{live_server}/f/{browser_root.name}/my-knowledge/docs/topic.md",
            wait_until="networkidle",
        )
        page.wait_for_timeout(900)

        preview_link = page.locator(
            '#preview a[href$="/f/'
            + browser_root.name
            + '/my-knowledge/docs/subdir/next.md"]'
        ).first
        assert preview_link.count() == 1
        preview_link.click()
        page.wait_for_timeout(900)

        assert page.url.endswith(
            f"/f/{browser_root.name}/my-knowledge/docs/subdir/next.md"
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
