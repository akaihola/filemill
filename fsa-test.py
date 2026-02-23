#!/usr/bin/env python3
"""FSA end-to-end test — requires headed browser + one manual folder pick.

Usage:
    uv run --with "playwright==1.57.0" python3 fsa-test.py

Workflow:
  1. Starts HTTP server on localhost:8787
  2. Opens a persistent headed Chromium window (profile in /tmp/fndr-chrome-profile)
  3. Clicks "Open…" for you — OS file picker appears
  4. YOU pick any local folder and click Allow/Open (up to 2 min)
  5. Playwright detects content and runs all automated checks
  6. Saves screenshots to /tmp/fndr-fsa-test/

On subsequent runs with the same profile, Chrome skips the "Allow site to edit
files?" confirmation — only the OS picker appears.
"""
import asyncio
import sys
import threading
import http.server
import socketserver
from pathlib import Path
from playwright.async_api import async_playwright, Dialog

PORT = 8787
PROFILE_DIR = Path('/tmp/fndr-chrome-profile')
SCREENSHOT_DIR = Path('/tmp/fndr-fsa-test')

# ── HTTP server ────────────────────────────────────────────────────────────────

def start_server(directory: Path, port: int) -> None:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)
        def log_message(self, *_): pass  # silence access log

    with socketserver.TCPServer(("", port), Handler) as httpd:
        httpd.serve_forever()


# ── Pass/fail tracking ─────────────────────────────────────────────────────────

passed: list[str] = []
failed: list[str] = []


def ok(name: str, detail: str = "") -> None:
    passed.append(name)
    print(f"  ✅  {name}" + (f" — {detail}" if detail else ""))


def fail(name: str, detail: str = "") -> None:
    failed.append(name)
    print(f"  ❌  {name}" + (f" — {detail}" if detail else ""))


async def check(name: str, condition: bool, detail: str = "") -> None:
    (ok if condition else fail)(name, detail)


async def shot(page, name: str) -> None:
    path = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(path))
    print(f"  📷  {path.name}")


# ── Tests ──────────────────────────────────────────────────────────────────────

async def test_no_dotfiles(page) -> None:
    items = page.locator("#columns-inner .col-item")
    count = await items.count()
    names = [
        await items.nth(i).locator(".item-label").text_content()
        for i in range(min(count, 200))
    ]
    dotfiles = [n for n in names if (n or "").startswith(".")]
    await check("No dot-files shown", not dotfiles,
                f"found: {dotfiles}" if dotfiles else "clean")


async def test_file_selection(page) -> None:
    """Click the first file in column 0 and verify the preview panel."""
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    count = await items.count()
    file_item = None
    for i in range(count):
        item = items.nth(i)
        if await item.locator(".col-arrow").count() == 0:
            file_item = item
            break

    if not file_item:
        print("  ⚠️   No bare files in column 0 — skipping file-selection checks")
        return

    fname = await file_item.locator(".item-label").text_content()
    await file_item.click()
    await page.wait_for_timeout(800)  # loadFileMeta is async (getFile() call)
    await shot(page, "03-file-selected")

    preview = page.locator("#preview")

    pname = await preview.locator("#preview-name").text_content()
    await check("Preview name matches filename", pname == fname,
                f'preview="{pname}" item="{fname}"')

    size_row = preview.locator(".meta-row", has=page.locator(".meta-key", has_text="Size"))
    has_size = await size_row.count() > 0
    size_val = await size_row.locator(".meta-val").text_content() if has_size else "absent"
    await check("Preview shows file size (from getFile())", has_size, size_val)

    mod_row = preview.locator(".meta-row", has=page.locator(".meta-key", has_text="Modified"))
    has_mod = await mod_row.count() > 0
    mod_val = await mod_row.locator(".meta-val").text_content() if has_mod else "absent"
    await check("Preview shows modified date (from getFile())", has_mod, mod_val)

    # FSA doesn't expose 'created' time — the row should be absent, not blank
    created_row = preview.locator(".meta-row", has=page.locator(".meta-key", has_text="Created"))
    await check("No Created row (FSA limitation)", await created_row.count() == 0)

    status = await page.locator("#statusbar").text_content()
    await check('Status bar shows "1 of N selected"',
                "selected" in (status or ""), repr(status))


async def test_subfolder_navigation(page) -> None:
    """Click the first folder in column 0 and check column 1 appears."""
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    count = await items.count()
    folder_item = None
    for i in range(count):
        item = items.nth(i)
        if await item.locator(".col-arrow").count() > 0:
            folder_item = item
            break

    if not folder_item:
        print("  ⚠️   No folders with ▶ arrow in column 0 — skipping sub-folder check")
        return

    fname = await folder_item.locator(".item-label").text_content()
    await folder_item.click()

    # Spinner may appear briefly; wait for col-item in column 1 (or empty state)
    try:
        await page.wait_for_selector(
            "#columns-inner .col[data-colidx='1']", timeout=15_000
        )
        await page.wait_for_timeout(400)
        await shot(page, "04-subfolder")
        ok(f'Sub-folder "{fname}" opens column 1')

        col1_items = page.locator("#columns-inner .col-item[data-colidx='1']")
        col1_count = await col1_items.count()
        # Column may be empty (valid — empty dir), but column itself must exist
        ok("Column 1 present", f"{col1_count} items")
    except Exception:
        fail(f'Column 1 never appeared after clicking folder "{fname}"')


async def test_cancel_picker(page) -> None:
    """Simulate AbortError (user cancelled picker) — UI must remain intact."""
    items_before = await page.locator("#columns-inner .col-item").count()

    await page.evaluate("""() => {
        window._realPicker = window.showDirectoryPicker;
        window.showDirectoryPicker = () =>
            Promise.reject(Object.assign(new Error('cancelled'), { name: 'AbortError' }));
    }""")
    await page.locator("#btn-open-folder").click()
    await page.wait_for_timeout(400)

    items_after = await page.locator("#columns-inner .col-item").count()
    await check("Cancel leaves UI intact", items_after == items_before,
                f"{items_before} → {items_after} items")
    await page.evaluate("() => { window.showDirectoryPicker = window._realPicker; }")


async def test_unsupported_browser(page) -> None:
    """Delete showDirectoryPicker and click Open… — must show alert."""
    alert_msgs: list[str] = []

    async def handle_dialog(dialog: Dialog) -> None:
        alert_msgs.append(dialog.message)
        await dialog.accept()

    page.once("dialog", handle_dialog)
    await page.evaluate("""() => {
        window._realPicker2 = window.showDirectoryPicker;
        delete window.showDirectoryPicker;
    }""")
    await page.locator("#btn-open-folder").click()
    await page.wait_for_timeout(600)

    msg = alert_msgs[0] if alert_msgs else ""
    await check("Alert shown for unsupported browser",
                bool(msg) and "not supported" in msg.lower(), repr(msg))
    await page.evaluate("() => { window.showDirectoryPicker = window._realPicker2; }")


# ── Main ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Start HTTP server (daemon thread — dies with the process)
    project_root = Path(__file__).parent
    t = threading.Thread(target=start_server, args=(project_root, PORT), daemon=True)
    t.start()
    await asyncio.sleep(0.3)
    print(f"HTTP server: http://localhost:{PORT}/")

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        # ── Load app ───────────────────────────────────────────────────────────
        print("\n── Loading app ──────────────────────────────────────────────────────")
        await page.goto(f"http://localhost:{PORT}/")
        await page.wait_for_timeout(1200)
        await shot(page, "01-initial")
        ok("App loaded")

        btn = page.locator("#btn-open-folder")
        await check("Open… button present", await btn.count() > 0)

        # ── Wait for user to pick a folder ────────────────────────────────────
        print("\n── Pick a folder ────────────────────────────────────────────────────")
        print("  👆  The browser will now open the directory picker.")
        print("  👆  Select ANY local folder, then click Open / Allow.")
        print("  ⏳  Waiting up to 2 minutes…\n")

        # Record sidebar count BEFORE picking so we can detect the new FSA entry
        sb_count_before = await page.locator(".sidebar-item").count()

        await btn.click()

        try:
            # Wait for the FSA entry to be prepended to the sidebar.
            # (Waiting for .col-item is not reliable — mock items are already there.)
            await page.wait_for_function(
                f"document.querySelectorAll('.sidebar-item').length > {sb_count_before}",
                timeout=120_000,
            )
            # Then wait for ensureLoaded to finish (col-items appear)
            await page.wait_for_selector("#columns-inner .col-item", timeout=15_000)
            await page.wait_for_timeout(500)
            await shot(page, "02-after-open")
            ok("FSA folder loaded — sidebar entry added and columns populated")
        except Exception:
            fail("Timed out waiting for FSA content (folder not picked?)")
            await shot(page, "02-timeout")
            await ctx.close()
            sys.exit(1)

        # ── Sidebar ───────────────────────────────────────────────────────────
        print("\n── Sidebar ──────────────────────────────────────────────────────────")
        first_sb = page.locator(".sidebar-item").first
        first_label = await first_sb.locator(".si-label").text_content()
        await check("FSA entry prepended to sidebar", await first_sb.count() > 0,
                    f'label="{first_label}"')

        # ── Column content ────────────────────────────────────────────────────
        print("\n── Column content ───────────────────────────────────────────────────")
        count = await page.locator("#columns-inner .col-item").count()
        await check("Column 0 has items", count > 0, f"{count} items")
        await test_no_dotfiles(page)

        # ── Path bar ──────────────────────────────────────────────────────────
        print("\n── Path bar ─────────────────────────────────────────────────────────")
        path_text = (await page.locator("#pathbar").text_content() or "").strip()
        await check("Path bar shows folder name", bool(path_text), repr(path_text))

        # ── File selection ────────────────────────────────────────────────────
        print("\n── File selection ───────────────────────────────────────────────────")
        await test_file_selection(page)

        # ── Sub-folder navigation ─────────────────────────────────────────────
        print("\n── Sub-folder navigation ────────────────────────────────────────────")
        await test_subfolder_navigation(page)

        # ── Picker cancel ─────────────────────────────────────────────────────
        print("\n── Picker cancel ────────────────────────────────────────────────────")
        await test_cancel_picker(page)

        # ── Unsupported-browser alert ─────────────────────────────────────────
        print("\n── Unsupported browser simulation ───────────────────────────────────")
        await test_unsupported_browser(page)

        # ── Final screenshot ──────────────────────────────────────────────────
        print("\n── Final screenshot ─────────────────────────────────────────────────")
        await shot(page, "05-final")

        # ── Summary ───────────────────────────────────────────────────────────
        width = 60
        print(f"\n{'═' * width}")
        print(f"  Results:  {len(passed)} passed,  {len(failed)} failed")
        if failed:
            print(f"  Failed:   {', '.join(failed)}")
        print(f"  Screenshots in {SCREENSHOT_DIR}/")
        print(f"{'═' * width}")

        print("\nPress Enter to close the browser…")
        input()
        await ctx.close()


asyncio.run(main())
