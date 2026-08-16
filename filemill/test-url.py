#!/usr/bin/env python3
"""filemill deep-link suite — the address bar, over a real origin.

Separate from test-ui.py because history.pushState throws on a file:// page's
opaque origin, which is exactly the case test-ui.py covers. Here the bundle is
served over localhost, so the router is live.

    uv run --with "playwright==1.61.0" python3 test-url.py [--bundle|--dev]
"""
import asyncio
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.async_api import async_playwright

# Serve the repository, not filemill/: the dev entry point references ../ui/,
# which is the whole point of the shared directory.
ROOT = Path(__file__).parent.parent
TARGET = "filemill/" + ("index-dev.html" if "--dev" in sys.argv else "index.html")

FAKE = r"""
window.__mk = () => {
  const F = (name, text) => ({kind:'file', name,
    getFile: async () => new File([text ?? 'x'], name, {lastModified: Date.parse('2026-08-01')})});
  const D = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  return D('workspace', [
    D('deep',  [D('alpha',[D('beta',[F('leaf.md','# leaf')])])]),
    D('mixed', [D('sub',[F('a.py','print(1)')]), F('.hidden','h'),
                F('note.md','# note'), F('sp ace & co.txt','x')]),
    F('README.md','# hi\n'),
  ]);
};
window.__state = () => ({path: path.map(p=>p.name), sel, focusCol});
"""

passed, failed = [], []


async def open_at(pg, base, frag=""):
    """Load the app cold at a fragment and mount the fake tree.

    about:blank first: navigating between two URLs that differ only in their
    fragment does not reload the document, so the boot code that reads the link
    would never run again and the test would be measuring the previous page.
    """
    await pg.goto("about:blank")
    await pg.goto(base + frag)
    # Rich previews reach for a CDN and log two console errors when it is not
    # reachable; both sides of that are test-rich.py's job, not this suite's.
    await pg.evaluate("localStorage.setItem('filemill.rich','off')")
    await pg.evaluate(FAKE)
    await pg.evaluate("mount(__mk())")
    await pg.wait_for_timeout(250)


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"  {'✅' if cond else '❌'}  {name}" + (f" — {detail}" if detail else ""))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass


def serve():
    handler = functools.partial(Quiet, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


async def main():
    httpd, port = serve()
    base = f"http://127.0.0.1:{port}/{TARGET}"

    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        print(f"\n── {TARGET} over http ───────────────────────────────────────")

        # ── the URL follows the selection ────────────────────────────────
        await open_at(pg, base)
        check("A mounted root names itself in the URL",
              await pg.evaluate("location.hash") == "#r=workspace",
              await pg.evaluate("location.hash"))

        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(250)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        await pg.wait_for_timeout(250)
        check("Selecting a file writes its path to the URL",
              await pg.evaluate("location.hash") == "#r=workspace&p=mixed/note.md",
              await pg.evaluate("location.hash"))

        await pg.click('.col[data-i="1"] .row:has-text("sp ace")')
        await pg.wait_for_timeout(250)
        check("Names with spaces and & are encoded once",
              await pg.evaluate("location.hash")
              == "#r=workspace&p=mixed/sp%20ace%20%26%20co.txt",
              await pg.evaluate("location.hash"))

        # ── walking a column must not flood history ──────────────────────
        await open_at(pg, base)
        before = await pg.evaluate("history.length")
        await pg.click('.col[data-i="0"] .row:has-text("README.md")')
        await pg.wait_for_timeout(200)
        for _ in range(3):
            await pg.keyboard.press("ArrowUp")
            await pg.wait_for_timeout(120)
        after = await pg.evaluate("history.length")
        check("↑/↓ inside one column rewrite the URL, they do not stack history",
              after == before, f"{before} → {after}")

        # ── a link restores the selection ────────────────────────────────
        await open_at(pg, base, "#r=workspace&p=deep/alpha/beta/leaf.md")
        st = await pg.evaluate("__state()")
        check("A deep link opens every column down to the file",
              st["path"] == ["workspace", "deep", "alpha", "beta"]
              and st["sel"] == ["deep", "alpha", "beta", "leaf.md"],
              str(st))
        check("The linked file is previewed, not just selected",
              "leaf" in await pg.inner_text("#preview .col-head"))

        # ── a link into a dotfile reveals dotfiles ───────────────────────
        await open_at(pg, base, "#r=workspace&p=mixed/.hidden")
        check("A link to a dotfile turns dotfiles on rather than showing nothing",
              await pg.evaluate("state.dotfiles") is True
              and (await pg.evaluate("__state()"))["sel"] == ["mixed", ".hidden"],
              str(await pg.evaluate("__state()")))

        # ── a stale link degrades, it does not fail ──────────────────────
        await open_at(pg, base, "#r=workspace&p=mixed/renamed-away.md")
        st = await pg.evaluate("__state()")
        check("A link to a file that is gone still opens the folder it was in",
              st["path"] == ["workspace", "mixed"] and st["sel"] == ["mixed"], str(st))
        check("…and the URL is rewritten to what was actually reached",
              await pg.evaluate("location.hash") == "#r=workspace&p=mixed",
              await pg.evaluate("location.hash"))

        # ── Back walks folders ───────────────────────────────────────────
        await open_at(pg, base)
        await pg.click('.col[data-i="0"] .row:has-text("deep")')
        await pg.wait_for_timeout(250)
        await pg.click('.col[data-i="1"] .row:has-text("alpha")')
        await pg.wait_for_timeout(250)
        deep_hash = await pg.evaluate("location.hash")
        await pg.go_back()
        await pg.wait_for_timeout(400)
        st = await pg.evaluate("__state()")
        check("Back steps out of the folder it stepped into",
              await pg.evaluate("location.hash") != deep_hash
              and st["sel"] == ["deep"], str(st))
        await pg.go_forward()
        await pg.wait_for_timeout(400)
        check("Forward returns to it",
              (await pg.evaluate("__state()"))["sel"] == ["deep", "alpha"],
              str(await pg.evaluate("__state()")))

        check("No console errors anywhere", not errs, "; ".join(errs[:3]))
        await b.close()

    httpd.shutdown()
    print(f"\n{'═' * 62}\n  {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("  Failed: " + ", ".join(failed))
    print("═" * 62)
    sys.exit(1 if failed else 0)


asyncio.run(main())
