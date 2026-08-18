#!/usr/bin/env python3
"""filemill end-to-end test — the parts a fake handle cannot cover.

Needs a real browser window and one manual folder pick, because the OS picker
is not scriptable. Verifies that a *real* directory reads correctly and, on the
second run, that the remembered folder opens with no dialog at all.

    uv run --with "playwright==1.61.0" python3 test-e2e.py

Run it twice: the persistent profile in /tmp/filemill-profile keeps both the
IndexedDB entry and Chrome's permission grant, so the second run should mount
straight into the same folder (or offer it as a one-click "Recently opened").
"""
import asyncio
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

PORT = 8787
ROOT = Path(__file__).parent
PROFILE = Path("/tmp/filemill-profile")
SHOTS = Path("/tmp/filemill-e2e")

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"  {'✅' if cond else '❌'}  {name}" + (f" — {detail}" if detail else ""))


def serve():
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(ROOT), **kw)

        def log_message(self, format: str, *args) -> None:
            pass

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), H) as httpd:
        httpd.serve_forever()


async def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=serve, daemon=True).start()
    await asyncio.sleep(0.3)

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE), headless=False, viewport={"width": 1400, "height": 880},
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))

        await pg.goto(f"http://localhost:{PORT}/index.html")
        await pg.wait_for_timeout(1200)

        print("\n── Startup ──────────────────────────────────────────────────")
        mounted = await pg.evaluate("welcome.hidden")
        recents = await pg.eval_on_selector_all("#w-recent .rec", "e=>e.map(x=>x.textContent)")
        if mounted:
            check("Remembered folder mounted with no dialog (2nd+ run)", True,
                  await pg.evaluate("path[0].name"))
        elif recents:
            check("Remembered folders offered on the welcome screen", True, str(recents))
            print("  👆  Click one of them, or pick a new folder.")
        else:
            check("First run: picker offered", await pg.is_visible("#w-pick"))
            print("  👆  Click “Choose Folder…” and pick any local folder.")

        if not mounted:
            print("  ⏳  Waiting up to 2 minutes for the folder…")
            try:
                await pg.wait_for_function("welcome.hidden && path.length", timeout=120_000)
            except PlaywrightTimeoutError:
                check("Folder opened", False, "timed out")
                await ctx.close()
                sys.exit(1)

        await pg.wait_for_function("colCache.get(path[0]) && colCache.get(path[0]).rows.length")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(SHOTS / "01-mounted.png"))

        print("\n── Real directory contents ──────────────────────────────────")
        kids = await pg.evaluate("path[0].kids.map(k => [k.name, k.dir])")
        check("Root directory read", len(kids) > 0, f"{len(kids)} entries")
        shown = await pg.eval_on_selector_all('.col[data-i="0"] .row', "e=>e.map(x=>x.title)")
        check("Dotfiles hidden by default",
              not [n for n in shown if n.startswith(".")],
              f"{len(kids) - len(shown)} hidden")
        dirs = [i for i, n in enumerate(shown) if dict(kids).get(n)]
        files = [i for i, n in enumerate(shown) if not dict(kids).get(n)]
        check("Folders sorted before files",
              not dirs or not files or max(dirs) < min(files))

        print("\n── Real file metadata ───────────────────────────────────────")
        file_row = None
        for i, n in enumerate(shown):
            if not dict(kids).get(n):
                file_row = i
                break
        if file_row is None:
            print("  ⚠️   No files in the root folder — skipping metadata checks")
        else:
            await pg.eval_on_selector_all(
                '.col[data-i="0"] .row', f"e => e[{file_row}].click()")
            await pg.wait_for_timeout(900)
            sub = await pg.inner_text("#pv-sub")
            check("Preview shows real size + mtime from getFile()",
                  "modified" in sub and "reading" not in sub, sub)
            await pg.screenshot(path=str(SHOTS / "02-file.png"))

        print("\n── Type-ahead over real names ───────────────────────────────")
        # Whatever the folder holds, typing the first three letters of an entry
        # has to land on an entry starting with those letters. The row it picks
        # is the first such row in the column, which need not be this one.
        target = next((n for n in shown if len(n) >= 3 and n[:3].isalpha()), None)
        if target is None:
            print("  ⚠️   No entry starts with three letters — skipping type-ahead")
        else:
            q = target[:3]
            await pg.keyboard.type(q)
            await pg.wait_for_timeout(400)
            landed = await pg.evaluate("sel[0]") or ""
            check(f"Typing “{q}” jumps to a matching row",
                  landed.lower().startswith(q.lower()), f"landed on “{landed}”")
            check("The matched characters are marked on the row it landed on",
                  await pg.eval_on_selector_all('.col[data-i="0"] .row mark',
                                                "e => e.length") > 0)
            await pg.screenshot(path=str(SHOTS / "03-typeahead.png"))
            await pg.keyboard.press("Escape")
            await pg.wait_for_timeout(200)

        print("\n── Copy path, real clipboard ────────────────────────────────")
        # test-ui.py stubs navigator.clipboard, so this is the only place the
        # real permission-gated API is exercised. A granted clipboard is the
        # good path; the refusal path is the stubbed one over there.
        await ctx.grant_permissions(["clipboard-read", "clipboard-write"],
                                    origin=f"http://localhost:{PORT}")
        await pg.evaluate("getSelection().removeAllRanges()")
        await pg.click('.col[data-i="0"] .row')
        await pg.wait_for_timeout(400)
        shown_path = await pg.inner_text("#st-path")
        await pg.keyboard.press("Control+c")
        await pg.wait_for_timeout(500)
        try:
            pasted = await pg.evaluate("navigator.clipboard.readText()")
        except PlaywrightError as exc:                # a refusal is a result too
            pasted = f"<unreadable: {exc}>"
        check("Ctrl+C puts the real path on the real clipboard",
              pasted == shown_path, f"clipboard {pasted!r}, status bar {shown_path!r}")
        check("A copy that worked says so in the status strip",
              (await pg.inner_text("#st-copy")).strip() == "copied",
              await pg.inner_text("#st-copy"))

        print("\n── Persistence ──────────────────────────────────────────────")
        stored = await pg.evaluate("recallRoots().then(h => h.map(x => x.name))")
        check("Folder recorded in IndexedDB for next session", bool(stored), str(stored))
        check("No page errors", not errs, "; ".join(errs[:2]))

        print(f"\n{'═' * 62}\n  {len(passed)} passed, {len(failed)} failed")
        print(f"  Screenshots in {SHOTS}/")
        print("  Re-run this script to verify the no-dialog restore path.")
        print("═" * 62)
        print("\nPress Enter to close the browser…")
        input()
        await ctx.close()
    sys.exit(1 if failed else 0)


asyncio.run(main())
