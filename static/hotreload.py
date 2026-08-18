#!/usr/bin/env python3
"""
filemill hot-reloader — watches src/ and patches the live page via CDP.

Only useful against the DEV entry point, http://localhost:PORT/src/index.html,
which loads src/*.js and src/styles.css as separate files. The bundled
index.html has everything inlined and has to be rebuilt + reloaded instead.

JavaScript:  Debugger.setScriptSource  → function bodies updated in-place, all
             page state (open folder, FSA handles, scroll position) preserved.
CSS:         injects a <style id="filemill-hot-css"> after the original sheet.

Usage:
    python3 -m http.server 8000 -d .          # serve the repo
    # open http://localhost:8000/src/index.html in Chromium started with
    #   --remote-debugging-port=9222
    uv run --with "playwright==1.61.0" python3 hotreload.py

Reloading the page is cheap anyway — the last folder is restored from
IndexedDB — so reach for this only when a re-grant prompt would interrupt you.
"""

import asyncio
import json
import pathlib
import re
import sys
import time

SRC_DIR = pathlib.Path(__file__).parent / "src"
CHROME_ADDR = "http://localhost:9222"

# How often to poll for file changes (seconds)
POLL_INTERVAL = 0.25


_FN_START_RE = re.compile(r"^(?:async\s+)?function\s+\w+\s*\(")


def _extract_function_decls(source: str) -> str:
    """Return only the top-level (async) function declarations from *source*.

    Everything else — addEventListener calls, let/const/var declarations,
    top-level imperative statements — is dropped.  This makes the result safe
    to re-evaluate via Runtime.evaluate: it only re-defines function bodies with
    no side-effects (no duplicate event-listener registrations, etc.).

    New function declarations ARE included, so newly added helpers land in the
    global scope after eval() in sloppy-mode classic scripts.
    """
    lines = source.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if _FN_START_RE.match(lines[i].lstrip()):
            # Collect until brace depth returns to 0 (whole function body)
            fn: list[str] = []
            depth = 0
            while i < len(lines):
                fn.append(lines[i])
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
                if depth <= 0 and any("{" in l for l in fn):
                    break
            out.append("\n".join(fn))
        else:
            i += 1
    return "\n\n".join(out)


async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        sys.exit("Install playwright: uv run --with 'playwright==1.61.0' python3 hotreload.py")

    async with async_playwright() as pw:
        print(f"🔌 Connecting to Chromium at {CHROME_ADDR} …")
        try:
            browser = await pw.chromium.connect_over_cdp(CHROME_ADDR)
        except Exception as e:  # noqa: BLE001 — any connect failure is fatal here
            sys.exit(f"Cannot connect: {e}\nMake sure Chromium is running with --remote-debugging-port=9222")

        # Find the filemill page
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                url = pg.url
                if "localhost" in url or url.startswith("file://"):
                    page = pg
                    break
            if page:
                break
        if not page and browser.contexts:
            page = browser.contexts[0].pages[0]
        if not page:
            sys.exit("No open page found in the connected Chromium session.")

        print(f"📄 Page: {page.url}")

        # Open a CDP session for the Debugger domain
        cdp = await page.context.new_cdp_session(page)

        # Map file:// URL → scriptId
        script_map: dict[str, str] = {}

        def on_script_parsed(params):
            url = params.get("url", "")
            sid = params.get("scriptId", "")
            # Track only our src/ scripts
            if "/src/" in url and url.endswith(".js") and sid:
                fname = url.rsplit("/", 1)[-1]
                script_map[url] = sid
                print(f"  📝 tracked {fname} ({sid})")

        cdp.on("Debugger.scriptParsed", on_script_parsed)
        await cdp.send("Debugger.enable")

        # Give Chrome a moment to emit scriptParsed events for already-loaded scripts
        await asyncio.sleep(0.8)

        # Build initial mtime snapshot
        mtimes: dict[pathlib.Path, float] = {}
        for f in SRC_DIR.iterdir():
            if f.suffix in (".js", ".css"):
                mtimes[f] = f.stat().st_mtime

        print(f"\n👁  Watching {SRC_DIR}/  ({len(mtimes)} files)")
        print(f"   Scripts tracked by debugger: {len(script_map)}")
        for url in sorted(script_map):
            print(f"   • {url.rsplit('/', 1)[-1]}")
        print("\nPress Ctrl-C to stop.\n")

        while True:
            await asyncio.sleep(POLL_INTERVAL)
            for fpath in SRC_DIR.iterdir():
                if fpath.suffix not in (".js", ".css"):
                    continue
                try:
                    mtime = fpath.stat().st_mtime
                except FileNotFoundError:
                    continue
                if mtimes.get(fpath) == mtime:
                    continue
                old = mtimes.get(fpath, 0)
                mtimes[fpath] = mtime
                if old == 0:
                    continue  # first scan — don't reload on startup

                content = fpath.read_text()
                ts = time.strftime("%H:%M:%S")
                print(f"[{ts}] 🔄 {fpath.name}", end=" … ", flush=True)

                if fpath.suffix == ".css":
                    # Replace/create a <style id="filemill-hot-css"> with new content
                    js = (
                        "(()=>{"
                        "let el=document.getElementById('filemill-hot-css');"
                        "if(!el){el=document.createElement('style');"
                        "el.id='filemill-hot-css';document.head.appendChild(el);}"
                        f"el.textContent={json.dumps(content)};"
                        "})()"
                    )
                    try:
                        await cdp.send("Runtime.evaluate", {"expression": js})
                        print("✓ CSS injected")
                    except Exception as e:  # noqa: BLE001 — keep watching
                        print(f"✗ {e}")

                elif fpath.suffix == ".js":
                    url = f"file://{fpath.resolve()}"
                    sid = script_map.get(url)
                    if not sid:
                        print(f"✗ script ID not found (known: {list(script_map.keys())})")
                        continue
                    try:
                        result = await cdp.send(
                            "Debugger.setScriptSource",
                            {"scriptId": sid, "scriptSource": content},
                        )
                        status = result.get("status", "?")
                        if status == "Ok":
                            print("✓ setScriptSource ok", end="")
                        else:
                            print(f"⚠ setScriptSource status={status}", end="")
                    except Exception as e:  # noqa: BLE001 — keep watching
                        print(f"⚠ setScriptSource failed: {e}", end="")

                    # Also inject via Runtime.evaluate so NEW top-level function
                    # declarations land in the global scope.  We only inject
                    # function bodies (no addEventListener calls, no let/const),
                    # so this is idempotent and has no side-effects.
                    filtered = _extract_function_decls(content)
                    try:
                        r2 = await cdp.send("Runtime.evaluate", {
                            "expression": filtered,
                            "awaitPromise": False,
                        })
                        if r2.get("result", {}).get("subtype") == "error":
                            print(f" / eval ✗ {r2['result']['description']}")
                        else:
                            print(" / eval ✓ new fns surfaced")
                    except Exception as e2:  # noqa: BLE001 — keep watching
                        print(f" / eval ✗ {e2}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 hot-reload stopped")
