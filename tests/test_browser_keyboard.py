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
    (tmp_path / "my-knowledge").mkdir()
    (tmp_path / "my-knowledge" / "AGENTS.md").write_text("# Agent notes\n")
    (tmp_path / "my-knowledge" / "docs").mkdir()
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


@pytest.mark.integration
def test_arrow_left_keeps_browser_url_in_sync(live_server: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(live_server, wait_until="networkidle")
        page.wait_for_timeout(800)

        page.evaluate(
            """() => {
                const col = document.getElementById('col-0');
                const link = Array.from(col.querySelectorAll('li a'))
                    .find(a => a.textContent.includes('my-knowledge'));
                if (link) link.click();
            }"""
        )
        page.wait_for_timeout(700)
        folder_url = page.url
        assert "path=" in folder_url
        assert "my-knowledge" in folder_url

        page.evaluate(
            """() => {
                const col = document.getElementById('col-1');
                const link = Array.from(col.querySelectorAll('li a'))
                    .find(a => a.textContent.includes('AGENTS.md'));
                if (link) link.click();
            }"""
        )
        page.wait_for_timeout(700)
        file_url = page.url
        assert "path=" in file_url
        assert "AGENTS.md" in file_url

        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(400)
        assert page.url == folder_url

        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(300)
        assert page.url.rstrip("/") == live_server.rstrip("/") + "/f"

        browser.close()
