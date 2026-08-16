#!/usr/bin/env python3
"""filemill UI test suite — headless, no folder dialog needed.

The app only ever talks to the FileSystemDirectoryHandle API, so a fake handle
exercises every code path except the OS picker itself (that one needs
test-e2e.py). Covers navigation, keyboard focus, folding, previews, the
settings toggles, and the render-cost budget.

    uv run --with "playwright==1.61.0" python3 test-ui.py [--bundle|--dev]

--bundle (default) tests the built index.html; --dev tests src/index.html, so
the same suite guards both the bundle and the modular sources.
"""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent
TARGET = ROOT / ("src/index.html" if "--dev" in sys.argv else "index.html")

# A fake FileSystemDirectoryHandle tree: async-iterable entries(), getFile().
FAKE = r"""
window.__mk = (nbig) => {
  const F = (name, text) => ({kind:'file', name,
    getFile: async () => new File([text ?? 'x'], name, {lastModified: Date.parse('2026-08-01')})});
  const D = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  const DENIED = (name) => ({kind:'directory', name,
    entries: async function*(){ throw Object.assign(new Error('no'), {name:'NotAllowedError'}); }});
  const SLOW = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ await new Promise(r=>setTimeout(r,500));
                                for (const k of kids) yield [k.name, k]; }});
  const big = [];
  for (let i=0;i<(nbig||0);i++) big.push(F(`file-${String(i).padStart(5,'0')}.txt`));
  return D('workspace', [
    D('deep',  [D('alpha',[D('beta',[D('gamma',[F('leaf.md','# leaf')])])])]),
    D('mixed', [D('sub',[F('a.py','print(1)')]), F('.dotfile','h'),
                F('note.md','# note'), F('data.json','{}')]),
    D('empty', []),
    DENIED('locked'),
    SLOW('slow', [F('one.txt','1'), F('two.txt','2')]),
    D('big', big),
    F('README.md','# hi\n'),
  ]);
};
window.__keybench = (n) => {
  const t0 = performance.now();
  for (let i=0;i<n;i++) document.dispatchEvent(new KeyboardEvent('keydown', {key:'ArrowDown'}));
  return +((performance.now()-t0)/n).toFixed(1);
};
window.__state = () => ({path: path.map(p=>p.name), sel, focusCol, folded});
"""

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"  {'✅' if cond else '❌'}  {name}" + (f" — {detail}" if detail else ""))


async def mount(pg, n=0):
    await pg.evaluate(f"mount(__mk({n}))")
    await pg.wait_for_function("path.length===1 && colCache.get(path[0])")
    await pg.wait_for_timeout(150)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        errs = []
        def on_console(m):
            if m.type == "error":
                errs.append(m.text)

        pg.on("console", on_console)
        pg.on("pageerror", lambda e: errs.append(str(e)))

        print(f"\n── {TARGET.relative_to(ROOT)} ───────────────────────────────")
        await pg.goto(TARGET.as_uri())
        await pg.wait_for_timeout(400)
        check("file:// shows the localhost hint, not a dead picker",
              "file://" in await pg.inner_text("#w-msg"))
        await pg.evaluate(FAKE)
        await mount(pg)
        check("Root folder mounts", await pg.evaluate("path[0].name") == "workspace")
        check("Welcome screen hidden after mount", await pg.evaluate("welcome.hidden"))

        print("\n── Directory states ─────────────────────────────────────────")
        for row, expect in (("empty", "Empty"), ("locked", "No permission")):
            await pg.click(f'.col[data-i="0"] .row:has-text("{row}")')
            await pg.wait_for_timeout(250)
            note = await pg.inner_text('.col[data-i="1"] .col-note')
            check(f"{row} directory shows “{expect}”", expect in note, note)
            # A column with no rows has nothing to highlight, so → must not move
            # focus into it — that read as a no-op while killing ↑/↓.
            await pg.keyboard.press("ArrowRight")
            await pg.wait_for_timeout(250)
            stayed = await pg.evaluate("focusCol") == 0
            await pg.keyboard.press("ArrowDown")
            await pg.wait_for_timeout(250)
            st = await pg.evaluate("__state()")
            check(f"→ does not enter the {row} column, ↑/↓ keep working",
                  stayed and st["focusCol"] == 0 and st["sel"][0] != row,
                  json.dumps(st))
        await pg.click('.col[data-i="0"] .row:has-text("slow")')
        try:      # the fake read takes 500 ms; don't race it with a fixed sleep
            await pg.wait_for_selector('.col[data-i="1"] .spinner', timeout=2000)
            check("Spinner while reading", True)
        except PlaywrightTimeoutError:
            check("Spinner while reading", False, "never appeared")
        await pg.wait_for_timeout(700)
        check("Entries appear when the read finishes",
              await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length") == 2)

        print("\n── Keyboard: ↑/↓ stay in the column ─────────────────────────")
        # sorted order is folders first, alphabetically:
        # big, deep, empty, locked, mixed, slow, then README.md
        await mount(pg)
        await pg.keyboard.press("ArrowDown")          # commits row 0 = "big" (a folder)
        await pg.wait_for_timeout(200)
        st = await pg.evaluate("__state()")
        check("↓ onto a folder opens its column but keeps focus",
              st["focusCol"] == 0 and st["path"] == ["workspace", "big"], json.dumps(st))
        names = []
        for _ in range(4):
            await pg.keyboard.press("ArrowDown")
            await pg.wait_for_timeout(120)
            s = await pg.evaluate("__state()")
            names.append(s["sel"][0])
        check("↓ walks down the same column, one row per press",
              names == ["deep", "empty", "locked", "mixed"] and
              (await pg.evaluate("focusCol")) == 0, str(names))
        await pg.keyboard.press("ArrowUp")
        await pg.wait_for_timeout(120)
        check("↑ walks back up the same column",
              (await pg.evaluate("sel[0]")) == "locked" and
              (await pg.evaluate("focusCol")) == 0)
        await pg.keyboard.press("End")
        await pg.wait_for_timeout(120)
        check("End jumps to the last row", (await pg.evaluate("sel[0]")) == "README.md")
        await pg.keyboard.press("Home")
        await pg.wait_for_timeout(120)
        check("Home jumps to the first row", (await pg.evaluate("sel[0]")) == "big")

        print("\n── Keyboard: → descends, ← comes back ───────────────────────")
        await pg.click('.col[data-i="0"] .row:has-text("deep")')
        await pg.wait_for_timeout(250)
        check("Clicking a folder also keeps focus in its own column",
              await pg.evaluate("focusCol") == 0)
        await pg.keyboard.press("ArrowRight")         # into "deep"
        await pg.wait_for_timeout(250)
        check("→ moves focus into the open column", await pg.evaluate("focusCol") == 1)
        for _ in range(3):
            await pg.keyboard.press("ArrowRight")
            await pg.wait_for_timeout(200)
        st = await pg.evaluate("__state()")
        check("→ walks all the way to the leaf",
              st["path"] == ["workspace", "deep", "alpha", "beta", "gamma"] and
              st["sel"][-1] == "leaf.md", json.dumps(st["path"]))
        await pg.keyboard.press("ArrowLeft")
        await pg.wait_for_timeout(200)
        check("← moves focus back out", await pg.evaluate("focusCol") == 3)
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_timeout(250)
        check("→ returns to the row the column was left on",
              await pg.evaluate("sel[4]") == "leaf.md" and
              await pg.evaluate("focusCol") == 4)

        print("\n── Folding dial ─────────────────────────────────────────────")
        await pg.evaluate("finder.scrollLeft = finder.scrollWidth")
        await pg.wait_for_timeout(300)
        spines = await pg.eval_on_selector_all(".col.spine", "e=>e.length")
        check("Scrolling right folds columns into spines", spines == 5, f"{spines} spines")
        await pg.evaluate("document.querySelector('.col.spine').click()")
        await pg.wait_for_timeout(700)
        check("Clicking a spine unfolds it",
              await pg.eval_on_selector_all(".col.spine", "e=>e.length") == 0)

        print("\n── Preview ──────────────────────────────────────────────────")
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(250)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        await pg.wait_for_timeout(400)
        check("Text file previews its contents",
              (await pg.inner_text(".pv-text")).strip() == "# note")
        check("Preview shows real size and mtime",
              "B ·" in await pg.inner_text("#pv-sub"), await pg.inner_text("#pv-sub"))
        await pg.click('.col[data-i="1"] .row:has-text("sub")')
        await pg.wait_for_timeout(250)
        check("Selecting a folder clears the preview",
              await pg.is_visible(".pv-empty"))

        print("\n── Settings ─────────────────────────────────────────────────")
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(200)
        before = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length")
        await pg.click("#gear")
        await pg.click("#s-dot")
        await pg.wait_for_timeout(200)
        after = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length")
        check("Dotfile toggle reveals hidden entries", after == before + 1, f"{before}→{after}")
        await pg.click("#s-density")
        await pg.wait_for_timeout(200)
        check("Density toggle changes row height",
              await pg.evaluate("getComputedStyle(document.querySelector('.row')).height") == "26px")
        await pg.click("#s-theme")
        await pg.wait_for_timeout(200)
        check("Dark theme re-colours the icons (cache invalidated)",
              await pg.evaluate("document.documentElement.dataset.theme") == "dark" and
              await pg.evaluate("!!document.querySelector('.ico.seti')"))
        for b_id in ("#s-theme", "#s-density", "#s-dot"):
            await pg.click(b_id)
        await pg.keyboard.press("Escape")

        print("\n── Render cost ──────────────────────────────────────────────")
        # Generous ceilings: they exist to catch the O(entries)-per-keystroke
        # regression (which cost 500–740 ms), not to benchmark a loaded machine.
        for n, budget in ((1000, 100), (3000, 100)):
            await mount(pg, n)
            await pg.click('.col[data-i="0"] .row:has-text("big")')
            await pg.wait_for_function(
                "colCache.get(path[1]) && colCache.get(path[1]).rows.length > 0", timeout=30_000)
            await pg.wait_for_timeout(300)
            ms = await pg.evaluate("(() => { const t=performance.now(); render(true);"
                                   "return +(performance.now()-t).toFixed(1); })()")
            key = await pg.evaluate("__keybench(20)")
            check(f"{n:,} entries: re-render {ms} ms, keystroke {key} ms (budget {budget} ms)",
                  ms < budget and key < budget)

        check("No console errors anywhere", not errs, "; ".join(errs[:3]))
        await b.close()

    print(f"\n{'═' * 62}\n  {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("  Failed: " + ", ".join(failed))
    print("═" * 62)
    sys.exit(1 if failed else 0)


asyncio.run(main())
