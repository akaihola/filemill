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
TARGET = ROOT / ("index-dev.html" if "--dev" in sys.argv else "index.html")

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
  /* Snapshots its entry list *before* the wait, the way a real read does: the
     directory the port hands back is the one that existed when the call
     started. Without that, a read in flight would silently pick up a change
     made while it slept, and the refresh-versus-load race would have nothing
     to catch it out on. */
  const RACE = (name, ref) => ({kind:'directory', name,
    entries: async function*(){ const snap = ref.slice();
                                await new Promise(r=>setTimeout(r,400));
                                for (const k of snap) yield [k.name, k]; }});
  const big = [];
  for (let i=0;i<(nbig||0);i++) big.push(F(`file-${String(i).padStart(5,'0')}.txt`));
  /* rebuilt per mount(), so one test's added and removed files cannot leak
     into the next one */
  window.__F = F;
  window.__live = [D('sub',[F('deep.txt','d'), D('twig',[F('tip.txt','t')])]),
                   F('one.txt','1'), F('two.txt','2')];
  window.__race = [F('alpha.txt','a'), F('bravo.txt','b')];
  return D('workspace', [
    D('deep',  [D('alpha',[D('beta',[D('gamma',[F('leaf.md','# leaf')])])])]),
    D('mixed', [D('sub',[F('a.py','print(1)')]), F('.dotfile','h'),
                F('note.md','# note'), F('data.json','{}')]),
    D('empty', []),
    DENIED('locked'),
    SLOW('slow', [F('one.txt','1'), F('two.txt','2')]),
    D('big', big),
    D('wide', [F('a-quite-long-file-name-1.txt'), F('a-quite-long-file-name-2.txt')]),
    // Names chosen so each type-ahead rung is the *only* one that can explain
    // the answer. Sorted: Alpha Report.txt, beta-notes.md, changelog.md,
    // notes.txt, readme.md, release-notes.md.
    //   "notes" → notes.txt      prefix beats beta-notes.md's earlier substring
    //   "log"   → changelog.md   substring; nothing starts with it
    //   "arp"   → Alpha Report   fuzzy; no other name has a, r, p in order
    D('search', [F('readme.md'), F('release-notes.md'), F('beta-notes.md'),
                 F('changelog.md'), F('notes.txt'), F('Alpha Report.txt')]),
    // Two directories whose entry lists the test edits, which is how "the disk
    // moved under the app" is rehearsed without writing to a real folder.
    // Both sort after "mixed", so the row indices the keyboard checks above
    // rely on do not move.
    D('refresh', window.__live),
    RACE('racing', window.__race),
    F('README.md','# hi\n'),
  ]);
};
/* Live entry lists, and the two edits a test makes to them. The node factories
   live inside __mk, so the helpers are bound here rather than re-derived. */
window.__live = [];
window.__race = [];
window.__F = null;
window.__add = (into, name) => into.push(window.__F(name, name));
window.__rm  = (from, name) =>
  from.splice(from.findIndex(k => k.name === name), 1);
/* The clipboard is a permission away in a real browser and refused outright in
   some contexts, so the suite drives both branches itself rather than asking
   Chromium for a grant it may not give. */
window.__clip = (fail) => {
  window.__clipped = [];
  Object.defineProperty(navigator, 'clipboard', {configurable: true, value: {
    writeText: async t => {
      window.__clipped.push(t);
      if (fail) throw Object.assign(new Error('denied'), {name: 'NotAllowedError'});
    }}});
};
/* Mean cost of one letter. `reset` sends Escape first, so every iteration is a
   fresh single-letter search that finds a row and re-renders — the realistic
   case. Without it the buffer grows and stops matching, which is the worst
   case: three full passes over every name in the column. */
window.__typebench = (n, key, reset) => {
  const hit = k => document.dispatchEvent(new KeyboardEvent('keydown', {key: k}));
  /* Report the column actually searched. A bench pointed at the wrong column
     reads as a wonderful result instead of as a broken measurement — the first
     version of this measured the 8-row root and reported 0 ms. */
  const rows = colCache.get(path[focusCol]).rows.length;
  const t0 = performance.now();
  for (let i=0;i<n;i++) { if (reset) hit('Escape'); hit(key); }
  const ms = +((performance.now()-t0)/n).toFixed(1);
  hit('Escape');
  return {ms, rows};
};
/* every width a column is ever painted at, to catch one that opens narrow and
   then jumps once its names arrive */
window.__watchWidths = () => {
  window.__w = [];
  new MutationObserver(ms => { for (const m of ms) { const el = m.target;
    if (el.classList && el.classList.contains('col'))
      window.__w.push(el.querySelector('.col-head .name span').textContent + ':' + el.style.width);
  }}).observe(document.getElementById('finder'),
              {subtree: true, attributes: true, attributeFilter: ['style']});
};
window.__keybench = (n) => {
  const t0 = performance.now();
  for (let i=0;i<n;i++) document.dispatchEvent(new KeyboardEvent('keydown', {key:'ArrowDown'}));
  return +((performance.now()-t0)/n).toFixed(1);
};
window.__state = () => ({path: path.map(p=>p.name), sel, focusCol, folded});
/* Put a `recent` list straight into the real database, to prove the record
   format and its migration rather than a stub of them. Only plain objects go in
   — a fake handle carries an async generator, which structuredClone refuses.
   test-e2e.py stores a real FileSystemDirectoryHandle in a real profile. */
window.__seed = (recent) => new Promise((res, rej) => {
  const r = indexedDB.open('filemill', 1);
  r.onupgradeneeded = e => e.target.result.createObjectStore('kv');
  r.onsuccess = e => { const tx = e.target.result.transaction('kv', 'readwrite');
                       tx.objectStore('kv').put(recent, 'recent');
                       tx.oncomplete = () => res(true);
                       tx.onerror = () => rej(tx.error); };
  r.onerror = e => rej(e.target.error);
});
/* Stand in for one remembered folder. isSameEntry is what recallView matches
   on, and the real one is the only correct answer — two folders can share a
   basename — so the stub answers by name and nothing in the app has to. */
window.__remember = (chain) => {
  window.recallRoots = async () => [{
    handle: {name: 'workspace', isSameEntry: async h => h.name === 'workspace'},
    path: chain}];
};
/* Watch what the app decides to store, without storing it. */
window.__spySaves = () => {
  window.__saved = [];
  window.recallRoots = async () => [];
  window.rememberRoot = async (h, p) => window.__saved.push([h.name, p]);
};
/* End on a value, never on an assignment. Playwright evaluates this string and
   *calls the result if it is a function* — and the result is the completion
   value of the last statement. Ending on `window.__spySaves = () => {…}` handed
   Playwright that arrow, which it duly invoked, stubbing recallRoots before a
   single check ran. The two storage checks then read an empty list from a
   database that visibly had a record in it. */
"fake handle ready";
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
        # This suite is about the UI, not the one feature that reaches the
        # network. Left on, every .md preview would try a CDN import, fail (no
        # network in CI), and log two console errors — see test-rich.py, which
        # covers both sides of that switch deliberately.
        await pg.evaluate("localStorage.setItem('filemill.rich','off')")
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

        print("\n── Column width ─────────────────────────────────────────────")
        await mount(pg)
        await pg.evaluate("__watchWidths()")
        await pg.click('.col[data-i="0"] .row:has-text("wide")')
        await pg.wait_for_timeout(400)
        widths = [w.split(":")[1] for w in await pg.evaluate("__w") if w.startswith("wide:")]
        check("A column opens at its content width, without a narrow first frame",
              len(set(widths)) == 1 and widths[0] != "148px", ", ".join(widths) or "never sized")

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

        print("\n── Type-ahead ───────────────────────────────────────────────")
        marks = ('[...document.querySelectorAll(\'.col[data-i="1"] .row mark\')]'
                 ".map(m => m.textContent)")

        async def in_search():
            """Focus the `search` column — type-ahead runs on the focused one."""
            await mount(pg)
            await pg.click('.col[data-i="0"] .row:has-text("search")')
            await pg.wait_for_timeout(250)
            await pg.keyboard.press("ArrowRight")
            await pg.wait_for_timeout(250)

        await in_search()
        await pg.keyboard.type("re")
        await pg.wait_for_timeout(150)
        # One round-trip, not three: every assertion made between the two typed
        # groups below is time the 1.2 s buffer is running down, and a suite
        # that spends it fails on a feature that works.
        snap = await pg.evaluate(
            f"({{sel: sel[1], marks: {marks},"
            " find: document.getElementById('st-find').textContent})")
        check("Prefix: “re” jumps to readme.md", snap["sel"] == "readme.md", snap["sel"])
        check("The matched characters are marked", snap["marks"] == ["re"], str(snap["marks"]))
        check("The buffer is shown, so a search in progress is visible",
              snap["find"].strip() == "⌕ re", snap["find"])

        # Within the idle window the buffer keeps growing: "re" + "l" is one
        # search for "rel", not a fresh search for "l".
        await pg.keyboard.type("l")
        await pg.wait_for_timeout(150)
        check("A letter typed straight after extends the buffer (“rel”)",
              await pg.evaluate("sel[1]") == "release-notes.md",
              await pg.evaluate("sel[1]"))
        await pg.wait_for_timeout(1400)          # longer than TA_IDLE = 1200 ms
        await pg.keyboard.type("c")
        await pg.wait_for_timeout(150)
        check("A pause starts a new search (“c”, not “relc”)",
              await pg.evaluate("sel[1]") == "changelog.md", await pg.evaluate("sel[1]"))

        await in_search()
        await pg.keyboard.type("notes")
        await pg.wait_for_timeout(150)
        check("Prefix outranks substring: “notes” → notes.txt, not beta-notes.md",
              await pg.evaluate("sel[1]") == "notes.txt", await pg.evaluate("sel[1]"))

        await in_search()
        await pg.keyboard.type("log")
        await pg.wait_for_timeout(150)
        check("Substring: “log” → changelog.md, which nothing starts with",
              await pg.evaluate("sel[1]") == "changelog.md", await pg.evaluate("sel[1]"))

        await in_search()
        await pg.keyboard.type("arp")
        await pg.wait_for_timeout(150)
        check("Fuzzy: “arp” → Alpha Report.txt",
              await pg.evaluate("sel[1]") == "Alpha Report.txt", await pg.evaluate("sel[1]"))
        check("Fuzzy marks the scattered characters, not a run",
              await pg.evaluate(marks) == ["A", "R", "p"], str(await pg.evaluate(marks)))

        await in_search()
        await pg.keyboard.type("zz")
        await pg.wait_for_timeout(150)
        check("No match says so and moves nothing",
              await pg.evaluate("sel[1]") == "Alpha Report.txt"
              and "no match" in await pg.inner_text("#st-find"),
              await pg.inner_text("#st-find"))
        # Backspace has to undo a typo, so a failed search keeps its buffer.
        await pg.keyboard.press("Backspace")
        await pg.keyboard.press("Backspace")
        await pg.keyboard.type("re")
        await pg.wait_for_timeout(150)
        check("Backspace undoes a typo instead of dropping the search",
              await pg.evaluate("sel[1]") == "readme.md", await pg.evaluate("sel[1]"))

        await in_search()
        await pg.keyboard.type("re")
        await pg.wait_for_timeout(120)
        await pg.keyboard.press("Escape")
        await pg.wait_for_timeout(120)
        check("Escape abandons the search and clears the marks",
              not await pg.evaluate(marks)
              and not (await pg.inner_text("#st-find")).strip())

        await in_search()
        await pg.keyboard.type("re")
        await pg.wait_for_timeout(120)
        await pg.keyboard.press("ArrowDown")
        await pg.wait_for_timeout(150)
        check("↑/↓ still walk the column, and end the search",
              await pg.evaluate("sel[1]") == "release-notes.md"
              and not await pg.evaluate(marks), await pg.evaluate("sel[1]"))

        await in_search()
        await pg.keyboard.press("Control+r")     # a browser shortcut, not a search
        await pg.wait_for_timeout(150)
        check("A letter with a modifier held is not type-ahead",
              await pg.evaluate("sel[1]") == "Alpha Report.txt"
              and not (await pg.inner_text("#st-find")).strip(),
              await pg.evaluate("sel[1]"))

        print("\n── Copy path ────────────────────────────────────────────────")
        await mount(pg)
        await pg.evaluate("__clip(false)")
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(250)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        await pg.wait_for_timeout(250)
        check("The status strip shows the path in the form it copies",
              await pg.inner_text("#st-path") == "workspace/mixed/note.md",
              await pg.inner_text("#st-path"))
        await pg.keyboard.press("Control+c")
        await pg.wait_for_timeout(250)
        check("⌘C / Ctrl+C copies the selected item's path",
              await pg.evaluate("__clipped") == ["workspace/mixed/note.md"],
              str(await pg.evaluate("__clipped")))
        check("A copy that worked says so",
              (await pg.inner_text("#st-copy")).strip() == "copied")

        await pg.evaluate("__clip(false)")
        await pg.click("#st-path")
        await pg.wait_for_timeout(250)
        check("Clicking the status path copies it too",
              await pg.evaluate("__clipped") == ["workspace/mixed/note.md"],
              str(await pg.evaluate("__clipped")))

        # The clipboard API can be refused, and a refusal that says nothing is
        # worse than no button: the next paste hands over something else.
        await pg.evaluate("__clip(true)")
        await pg.click("#st-path")
        await pg.wait_for_timeout(250)
        note = await pg.inner_text("#st-copy")
        check("A refused clipboard is visible, not silent", "refused" in note, note)
        check("…and the path is left selected, so the browser's own copy works",
              await pg.evaluate("getSelection().toString()") == "workspace/mixed/note.md",
              await pg.evaluate("getSelection().toString()"))

        print("\n── Refresh a directory ──────────────────────────────────────")
        # Nothing here touches a real folder: what changes is the fake handle's
        # entry list. test-e2e.py runs the real-disk version, against a
        # temporary directory it creates and deletes itself.
        rows1 = '.col[data-i="1"] .row'

        async def in_refresh():
            """Mount fresh and focus the `refresh` column (row 0 = the `sub` folder)."""
            await mount(pg)
            await pg.click('.col[data-i="0"] .row:has-text("refresh")')
            await pg.wait_for_timeout(250)
            await pg.keyboard.press("ArrowRight")
            await pg.wait_for_timeout(250)

        await in_refresh()
        before = await pg.eval_on_selector_all(rows1, "e=>e.length")
        await pg.evaluate("__add(__live, 'three.txt')")
        await pg.wait_for_timeout(120)
        check("A file another program wrote stays invisible until asked",
              await pg.eval_on_selector_all(rows1, "e=>e.length") == before,
              "no watch API exists — which is the whole reason refresh is manual")
        await pg.evaluate("window.__sentinel = 42")
        await pg.keyboard.press("F5")
        await pg.wait_for_timeout(600)
        snap = await pg.evaluate(
            "({...__state(), rows: colCache.get(path[1]).rows.length,"
            " sentinel: window.__sentinel,"
            " say: document.getElementById('st-refresh').textContent})")
        check("F5 re-reads the focused column and the new file appears",
              snap["rows"] == before + 1, f"{before}→{snap['rows']}")
        check("F5 refreshes the folder instead of reloading the page",
              snap["sentinel"] == 42,
              f"page marker {snap['sentinel']}, 42 means the page survived")
        check("The selection survives the re-read, and so does the column it opened",
              snap["sel"] == ["refresh", "sub"] and snap["focusCol"] == 1
              and snap["path"] == ["workspace", "refresh", "sub"], json.dumps(snap))
        check("The strip says what changed, in entries rather than adjectives",
              snap["say"].strip() == "⟳ 1 new, 0 gone", snap["say"])

        await in_refresh()
        before = await pg.eval_on_selector_all(rows1, "e=>e.length")
        await pg.evaluate("__add(__live, 'four.txt')")
        await pg.click('.col[data-i="1"] .col-head .rf')
        await pg.wait_for_timeout(600)
        check("The ⟳ button on the column header does the same job as F5",
              await pg.eval_on_selector_all(rows1, "e=>e.length") == before + 1)

        # The entry you were on is gone. Selecting whatever slid into its place
        # would show a preview of a file nobody asked for, so nothing is
        # selected — but the cursor stays, because ↑/↓ should resume where you
        # were rather than at the top of a 3 000-row list.
        await in_refresh()
        for _ in range(2):
            await pg.keyboard.press("ArrowDown")
            await pg.wait_for_timeout(150)
        check("(a file two rows down is selected)",
              await pg.evaluate("sel[1]") == "two.txt", await pg.evaluate("sel[1]"))
        await pg.evaluate("__rm(__live, 'two.txt')")
        await pg.keyboard.press("F5")
        await pg.wait_for_timeout(600)
        snap = await pg.evaluate(
            "({...__state(), cursor1: cursor[1],"
            " say: document.getElementById('st-refresh').textContent})")
        check("A selected file that vanished leaves nothing selected, and says so",
              snap["sel"] == ["refresh"] and snap["focusCol"] == 1
              and "two.txt is gone" in snap["say"], json.dumps(snap))
        check("…and the cursor stays on that row index, clamped to what is left",
              snap["cursor1"] == 1, str(snap["cursor1"]))
        await pg.keyboard.press("ArrowDown")
        await pg.wait_for_timeout(250)
        check("…so ↓ resumes next to the missing file, not at the top",
              await pg.evaluate("sel[1]") == "one.txt", await pg.evaluate("sel[1]"))

        # Refreshing a parent must not quietly throw away the columns to its
        # right. A re-read hands back new node objects, so the chain is walked
        # again by name rather than kept by identity.
        async def deep_chain():
            await mount(pg)
            await pg.click('.col[data-i="0"] .row:has-text("refresh")')
            await pg.wait_for_timeout(250)
            for _ in range(3):                    # → sub → twig → tip.txt
                await pg.keyboard.press("ArrowRight")
                await pg.wait_for_timeout(250)
            for _ in range(2):                    # ← back out to the `refresh` column
                await pg.keyboard.press("ArrowLeft")
                await pg.wait_for_timeout(150)

        await deep_chain()
        await pg.keyboard.press("F5")
        await pg.wait_for_timeout(900)
        st = await pg.evaluate("__state()")
        check("Refreshing a parent keeps the whole chain open below it",
              st["path"] == ["workspace", "refresh", "sub", "twig"]
              and st["sel"] == ["refresh", "sub", "twig", "tip.txt"], json.dumps(st))
        check("…and leaves focus on the column the user was actually in",
              st["focusCol"] == 1, str(st["focusCol"]))

        await deep_chain()
        await pg.evaluate("__rm(__live, 'sub')")
        await pg.keyboard.press("F5")
        await pg.wait_for_timeout(900)
        snap = await pg.evaluate(
            "({...__state(), say: document.getElementById('st-refresh').textContent})")
        check("A chain that stopped existing is restored as far as it is real, "
              "and no further",
              snap["path"] == ["workspace", "refresh"] and snap["sel"] == ["refresh"]
              and snap["focusCol"] == 1 and "sub is gone" in snap["say"],
              json.dumps(snap))

        # The race the pvToken/ensureLoaded reuse exists for. `racing` snapshots
        # its entries before a 400 ms wait, so a refresh that simply re-entered
        # ensureLoaded would be handed the in-flight promise and win the *old*
        # listing — two reads, one field, and the wrong one landing last.
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("racing")')
        await pg.wait_for_timeout(150)                 # the 400 ms read is in flight
        await pg.evaluate("__add(__race, 'charlie.txt')")
        await pg.evaluate("refreshColumn(1)")
        await pg.wait_for_timeout(1600)
        got = await pg.eval_on_selector_all(rows1, "e=>e.map(x=>x.title)")
        head = (await pg.inner_text('.col[data-i="1"] .count')).strip()
        check("A refresh that lands on a read already in flight waits for it, then "
              "re-reads once — one listing wins",
              got == ["alpha.txt", "bravo.txt", "charlie.txt"] and head == "3"
              and await pg.evaluate("path[1].loading") is None,
              f"{got}, header says {head}")

        # The other way round: the user clicks somewhere else while a refresh is
        # still walking the chain back down. Refreshing the root re-reads `slow`
        # (500 ms), which is a wide enough window to land a click in. Whoever
        # the user asked for last has to win, and the columns must still agree
        # with each other — every open column is the child the level above
        # selected. A half-applied walk shows up here as a chain that does not.
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("slow")')
        await pg.wait_for_timeout(900)
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_timeout(300)
        await pg.evaluate("refreshColumn(0)")       # deliberately not awaited
        await pg.wait_for_timeout(120)
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(2500)
        st = await pg.evaluate("__state()")
        coherent = all(st["sel"][i] == st["path"][i + 1]
                       for i in range(len(st["path"]) - 1))
        check("A click during a refresh wins, and leaves the columns agreeing "
              "with each other",
              st["path"] == ["workspace", "mixed"] and st["sel"] == ["mixed"]
              and coherent, json.dumps(st))

        print("\n── Remember view state per folder ───────────────────────────")
        # The record and its migration go through the real database. The restore
        # itself is driven by stubbing recallRoots, because a fake handle is not
        # structured-cloneable — test-e2e.py does the real-handle round trip.
        await pg.evaluate("__seed([{kind:'directory', name:'legacy'}])")
        got = await pg.evaluate("recallRoots()")
        check("A database written before view state keeps its folders",
              got == [{"handle": {"kind": "directory", "name": "legacy"}, "path": []}],
              str(got))
        await pg.evaluate(
            "__seed([{handle:{kind:'directory',name:'w'}, path:['mixed','sub']}])")
        got = await pg.evaluate("recallRoots()")
        check("A stored chain comes back attached to the folder it belongs to",
              len(got) == 1 and got[0]["path"] == ["mixed", "sub"], str(got))

        await pg.evaluate("__remember([])")
        check("A folder last left on its own root asks for no restore",
              await pg.evaluate("recallView({name:'workspace'})") is None)

        await pg.evaluate("__remember(['mixed','sub','a.py'])")
        await pg.evaluate("mount(__mk(0))")
        await pg.wait_for_timeout(350)
        st = await pg.evaluate("__state()")
        check("Re-mounting a remembered folder puts the user back on the chain",
              st["path"] == ["workspace", "mixed", "sub"]
              and st["sel"] == ["mixed", "sub", "a.py"], json.dumps(st))

        # The case that matters: the folder is still there, the chain is not.
        await pg.evaluate("__remember(['mixed','gone','x.py'])")
        await pg.evaluate("mount(__mk(0))")
        await pg.wait_for_timeout(350)
        st = await pg.evaluate("__state()")
        check("A remembered chain that no longer exists restores as far as it is "
              "real, and stops",
              st["path"] == ["workspace", "mixed"] and st["sel"] == ["mixed"],
              json.dumps(st))
        check("…and shows no selection inside the folder it stopped at, because "
              "there is none to show",
              len(st["sel"]) == 1 and st["focusCol"] == 0, json.dumps(st))

        await pg.evaluate("__remember(['mixed','sub'])")
        await pg.evaluate("pendingLoc = {root:'workspace', path:['deep','alpha']}")
        await pg.evaluate("mount(__mk(0))")
        await pg.wait_for_timeout(350)
        st = await pg.evaluate("__state()")
        check("A link in the address bar beats the remembered chain",
              st["path"] == ["workspace", "deep", "alpha"], json.dumps(st))

        # The write side. Walking a column is one location change per keystroke,
        # so the saves are debounced — a write per keystroke would be the
        # per-entry cost this app spent a rewrite deleting, in another costume.
        await pg.evaluate("__spySaves()")
        await pg.evaluate("mount(__mk(0))")
        await pg.wait_for_timeout(350)
        start_saves = await pg.evaluate("__saved.length")
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(150)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        early = await pg.evaluate("__saved.length")
        await pg.wait_for_timeout(800)
        saved = await pg.evaluate("__saved")
        check("Mounting a folder does not overwrite the chain it just restored",
              start_saves == 0, f"{start_saves} writes during mount")
        check("Two navigations 150 ms apart collapse into one write",
              early == 0 and len(saved) == 1, f"{early} early, {len(saved)} total")
        check("What is stored is the folder and the chain inside it",
              saved == [["workspace", ["mixed", "note.md"]]], str(saved))

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
            # Type-ahead runs on every letter, so it needs its own ceiling. What
            # to bound is the cost of the *search*, not the cost of the row it
            # lands on: picking a file out of a 3 000-entry directory builds a
            # preview and re-renders, ~60 ms here, whether an arrow key or a
            # letter asked for it. Measuring both in the same column separates
            # the two — __keybench walked 20 rows down the root column, so the
            # big directory has to be re-opened before stepping in.
            await pg.click('.col[data-i="0"] .row:has-text("big")')
            await pg.wait_for_function(
                "colCache.get(path[1]) && colCache.get(path[1]).rows.length > 0", timeout=30_000)
            await pg.wait_for_timeout(200)
            await pg.keyboard.press("ArrowRight")     # focus the big column
            await pg.wait_for_timeout(200)
            arrow = await pg.evaluate("__keybench(20)")
            hit = await pg.evaluate("__typebench(20, 'f', true)")
            miss = await pg.evaluate("__typebench(20, 'q', false)")
            # The matcher alone: three complete passes, no row clicked and
            # nothing re-rendered. This is the number that moves if someone
            # drops the c.lower cache or makes matching quadratic, and it is
            # the only one here that does not ride on the preview.
            find = await pg.evaluate(
                "(() => { const c = colCache.get(path[focusCol]);"
                " const t = performance.now();"
                " for (let i=0;i<20;i++) taSearch(c.lower, 'qqq');"
                " return +((performance.now()-t)/20).toFixed(2); })()")
            check(f"{n:,} entries: matching {find} ms; a whole keystroke is "
                  f"{miss['ms']} ms with no match and {hit['ms']} ms with one, "
                  f"against {arrow} ms for an arrow key in the same column",
                  find < 25 and miss["ms"] < budget and hit["ms"] < arrow + budget
                  and hit["rows"] == n and miss["rows"] == n,
                  f"searched {hit['rows']} rows, expected {n}")

            # Refresh is the one action that throws a cached column away on
            # purpose: the entry list really did change, so the DOM has to be
            # rebuilt. Its price is therefore the build price the cache exists
            # to avoid paying per keystroke — once, when the user asks. What
            # matters is that it is not on the keystroke path, so the assertion
            # is on the arrow key measured *after* it, not on the refresh.
            rf = await pg.evaluate(
                "(async () => { const t = performance.now();"
                " await refreshColumn(focusCol);"
                " return +(performance.now()-t).toFixed(1); })()")
            after = await pg.evaluate("__keybench(20)")
            check(f"{n:,} entries: a refresh rebuilds the column in {rf} ms, and the "
                  f"next keystroke still costs {after} ms (budget {budget} ms)",
                  after < budget and await pg.evaluate("colCache.get(path[focusCol])"
                                                       ".rows.length") == n,
                  f"keystroke {after} ms after a {rf} ms refresh")

        check("No console errors anywhere", not errs, "; ".join(errs[:3]))
        await b.close()

    print(f"\n{'═' * 62}\n  {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("  Failed: " + ", ".join(failed))
    print("═" * 62)
    sys.exit(1 if failed else 0)


asyncio.run(main())
