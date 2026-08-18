#!/usr/bin/env python3
"""filemill end-to-end test — the parts a fake handle cannot cover.

Needs a real browser window and one manual folder pick, because the OS picker
is not scriptable. Verifies that a *real* directory reads correctly and, on the
second run, that the remembered folder opens with no dialog at all.

    uv run --with "playwright==1.61.0" python3 test-e2e.py

Run it twice: the persistent profile in /tmp/filemill-profile keeps both the
IndexedDB entry and Chrome's permission grant, so the second run should mount
straight into the same folder (or offer it as a one-click "Recently opened").

The refresh and view-state checks need the directory to change under the app,
so they run against a throwaway folder this script creates, fills, edits and
deletes. Nothing here ever writes to a folder you picked: `fixture()` builds it
under the system temp directory and `owned()` refuses any path outside it.
"""
import asyncio
import http.server
import os
import shutil
import socketserver
import sys
import tempfile
import threading
from datetime import datetime
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


# Three real files whose names, sizes and dates each give a different order, so
# a sort by size or date on a real disk cannot be the sort by name in disguise.
#   name:     a-large, b-small, c-medium
#   size:     b-small(10) < c-medium(300) < a-large(3000)
#   modified: c-medium(Jan) < a-large(Feb) < b-small(Mar)
SIZED = [("a-large.txt", 3000, "2026-02-03"),
         ("b-small.txt", 10, "2026-03-04"),
         ("c-medium.txt", 300, "2026-01-02")]


def fixture() -> Path:
    """A folder this script owns, so no check ever edits a folder you picked."""
    d = Path(tempfile.mkdtemp(prefix="filemill-e2e-"))
    (d / "notes").mkdir()
    (d / "notes" / "one.txt").write_text("one\n")
    (d / "notes" / "two.txt").write_text("two\n")
    (d / "readme.md").write_text("# fixture\n")
    (d / "sized").mkdir()
    for name, size, when in SIZED:
        f = d / "sized" / name
        f.write_text("x" * size)
        ts = datetime.fromisoformat(when).timestamp()
        os.utime(f, (ts, ts))
    return d


def owned(root: Path, target: Path) -> Path:
    """Refuse to touch anything outside the throwaway folder.

    The app is read-only and the suite has to stay that way about real data. A
    guard on the path is cheap; a test that deleted the wrong file once is not.
    """
    tmp = Path(tempfile.gettempdir()).resolve()
    t, r = target.resolve(), root.resolve()
    if not (r.is_relative_to(tmp) and t.is_relative_to(r)):
        raise SystemExit(f"refusing to touch {t}: outside the test folder {r}")
    return t


STATE = "({path: path.map(p => p.name), sel, focusCol})"

# Count the real getFile() calls. The claim under test is not only that a size
# sort puts the right file first — it is that the name sort put it there for
# nothing, and that flipping to a date sort asks for nothing more.
COUNT_META = """
window.__countMeta = () => {
  const real = FS.loadMeta.bind(FS);
  window.__metas = 0;
  FS.loadMeta = async n => { window.__metas++; return real(n); };
};
"metadata counter ready";
"""


async def refresh_and_restore(pg):
    """Drive refresh and view-state restore against a folder this script owns.

    The other checks read whatever folder you picked. These two cannot: refresh
    only means something once the directory changes, and a restore only means
    something once you have navigated somewhere and come back. So this builds
    its own folder, asks for one more pick, edits it, and deletes it after.
    """
    root = fixture()
    print(f"\n  👆  Click “Open Folder…” and pick this folder:\n      {root}")
    try:
        try:
            await pg.wait_for_function(
                "name => path.length && path[0].name === name",
                arg=root.name, timeout=120_000)
        except PlaywrightTimeoutError:
            check("Test folder opened", False, f"timed out waiting for {root.name}")
            return
        await pg.wait_for_timeout(600)

        print("\n── Sort a real folder by size and by date ───────────────────")
        # test-url.py measures the sweep against the origin private file system,
        # which is real but is the browser's own store. This is the user's disk,
        # reached through the picker they clicked, which is the only thing the
        # OPFS run cannot claim to be.
        await pg.evaluate("setSort('name', false)")
        await pg.evaluate(COUNT_META)
        await pg.evaluate("__countMeta()")
        await pg.click('.col[data-i="0"] .row:has-text("sized")')
        await pg.wait_for_timeout(600)
        rows1 = '.col[data-i="1"] .row'
        names = await pg.eval_on_selector_all(rows1, "e => e.map(x => x.title)")
        check("A real folder opens in name order without reading one file",
              names == [n for n, _, _ in SIZED] and await pg.evaluate("__metas") == 0,
              f"{names}, {await pg.evaluate('__metas')} getFile() calls")

        await pg.evaluate("setSort('size', true)")
        await pg.wait_for_function("path[1] && path[1].metaDone", timeout=30_000)
        await pg.wait_for_timeout(400)
        names = await pg.eval_on_selector_all(rows1, "e => e.map(x => x.title)")
        swept = await pg.evaluate("path[1].metaSwept")
        paid = await pg.evaluate("__metas")
        check(f"Biggest first puts the 3 000-byte file at the top, after "
              f"{swept['n']} real getFile() calls in {swept['ms']} ms",
              names == ["a-large.txt", "c-medium.txt", "b-small.txt"], str(names))

        await pg.evaluate("setSort('mtime', false)")
        await pg.wait_for_timeout(500)
        names = await pg.eval_on_selector_all(rows1, "e => e.map(x => x.title)")
        again = await pg.evaluate("__metas") - paid
        check("Oldest first orders by the real mtime and reads nothing more",
              names == ["c-medium.txt", "a-large.txt", "b-small.txt"] and again == 0,
              f"{names}, {again} further getFile() calls")
        await pg.evaluate("setSort('name', false)")

        print("\n── Refresh against a real folder ────────────────────────────")
        await pg.click('.col[data-i="0"] .row:has-text("notes")')
        await pg.wait_for_timeout(400)
        await pg.keyboard.press("ArrowRight")          # focus the notes column
        await pg.wait_for_timeout(400)
        before = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e => e.length")

        owned(root, root / "notes" / "three.txt").write_text("three\n")
        await pg.wait_for_timeout(300)
        check("A file written on disk is invisible until the app is asked",
              await pg.eval_on_selector_all('.col[data-i="1"] .row',
                                            "e => e.length") == before,
              "no watch API — the read already happened")
        await pg.keyboard.press("F5")
        await pg.wait_for_timeout(900)
        shown = await pg.eval_on_selector_all('.col[data-i="1"] .row',
                                              "e => e.map(x => x.title)")
        check("F5 re-reads the real directory and the new file appears",
              "three.txt" in shown, str(shown))

        # Select a file, delete it on disk, refresh: the app must not keep
        # showing a selection that no longer exists anywhere.
        await pg.click('.col[data-i="1"] .row:has-text("two.txt")')
        await pg.wait_for_timeout(500)
        owned(root, root / "notes" / "two.txt").unlink()
        await pg.keyboard.press("F5")
        await pg.wait_for_timeout(900)
        st = await pg.evaluate(STATE)
        say = await pg.inner_text("#st-refresh")
        check("A selected file deleted on disk leaves no selection behind",
              len(st["sel"]) == 1 and "two.txt is gone" in say,
              f"{st['sel']}, strip says {say!r}")

        print("\n── The chain comes back after a reload ──────────────────────")
        await pg.click('.col[data-i="1"] .row:has-text("one.txt")')
        await pg.wait_for_timeout(1000)                # longer than the 400 ms debounce
        want = await pg.evaluate(STATE)
        await pg.reload()
        try:
            await pg.wait_for_function("welcome.hidden && path.length", timeout=20_000)
        except PlaywrightTimeoutError:
            check("Remembered folder re-mounted after a reload", False,
                  "landed on the welcome screen — the grant was dropped")
            return
        await pg.wait_for_timeout(1200)
        got = await pg.evaluate(STATE)
        check("A reload puts the user back on the chain they left",
              got == want, f"left {want}, came back to {got}")

        # The case that matters: the folder is still granted, the chain is not
        # all there any more.
        owned(root, root / "notes" / "one.txt").unlink()
        await pg.reload()
        await pg.wait_for_function("welcome.hidden && path.length", timeout=20_000)
        await pg.wait_for_timeout(1200)
        got = await pg.evaluate(STATE)
        check("A chain whose file was deleted restores as far as it is real",
              got["path"] == [root.name, "notes"] and got["sel"] == ["notes"],
              str(got))
        check("…and offers no selection inside the folder it stopped at",
              len(got["sel"]) == 1, str(got["sel"]))
        await pg.screenshot(path=str(SHOTS / "04-restored.png"))
    finally:
        shutil.rmtree(root, ignore_errors=True)
        print(f"  🧹  Removed {root}")


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
        # The profile is persistent, so a run that stopped halfway through the
        # sort section would leave its key in localStorage and re-order every
        # column the checks below read.
        await pg.evaluate("setSort('name', false)")

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
        stored = await pg.evaluate("recallRoots().then(r => r.map(x => x.handle.name))")
        check("Folder recorded in IndexedDB for next session", bool(stored), str(stored))

        await refresh_and_restore(pg)
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
