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

# The fixture's source file as Python sees it: __mk builds a.py from this
# string and long.py from 300 copies of it.
PY_SRC = 'def f():\n    # doc\n    return "s" + 42\n    # ' + 'x' * 82 + '\n'

# A fake FileSystemDirectoryHandle tree: async-iterable entries(), getFile().
FAKE = r"""
window.__mk = (nbig) => {
  /* Every getFile() is counted. A sort by size is the only feature here that
     reads a whole directory file by file, so "how many reads did that cost"
     is the number the sort checks are really about — an assertion on the
     order alone would pass just as well if the app swept on every render. */
  window.__gets = 0;
  /* The File is built once and handed back on every call. Constructing 3 000
     Blobs costs more than the sweep that asks for them, and a bench dominated
     by the fake measures the fake. The call is still counted, which is what the
     sort checks assert on. */
  const F = (name, text, mod) => { let f = null; return {kind:'file', name,
    getFile: async () => { window.__gets++;
      return f ||= new File([text ?? 'x'], name,
                            {lastModified: Date.parse(mod || '2026-08-01')}); },
    /* the write half of the seam — just enough for Edit → Save */
    createWritable: async () => { let buf = '';
      return {write: async d => { buf += d; },
              close: async () => { f = new File([buf], name,
                                                {lastModified: Date.now()}); }}; }}; };
  /* A file the port cannot stat: the permission case, which still has to sort
     somewhere and must never be dropped from the listing. */
  const FX = (name) => ({kind:'file', name,
    getFile: async () => { window.__gets++;
      throw Object.assign(new Error('no'), {name:'NotAllowedError'}); }});
  const D = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  /* long enough that measure() returns its 380 px ceiling for the column */
  const LONG = i => `level-${i}-` + 'w'.repeat(36);
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
  /* Sizes and mtimes that disagree with the name order in both directions, so a
     size or date sort cannot be mistaken for the name sort it replaced. */
  const big = [];
  for (let i=0;i<(nbig||0);i++)
    big.push(F(`file-${String(i).padStart(5,'0')}.txt`, 'x'.repeat((i % 13) + 1),
               `2026-0${(i % 9) + 1}-01`));
  /* rebuilt per mount(), so one test's added and removed files cannot leak
     into the next one */
  window.__F = F;
  window.__live = [D('sub',[F('deep.txt','d'), D('twig',[F('tip.txt','t')])]),
                   F('one.txt','1'), F('two.txt','2')];
  window.__race = [F('alpha.txt','a'), F('bravo.txt','b')];
  // one of every token class core/syntax.js knows, for the preview checks
  // …and an 88-column comment, for the "never wrap before column 88" checks
  const PY_SRC = 'def f():\n    # doc\n    return "s" + 42\n    # ' + 'x'.repeat(82) + '\n';
  return D('workspace', [
    D('deep',  [D('alpha',[D('beta',[D('gamma',[F('leaf.md','# leaf')])])])]),
    D('mixed', [D('sub',[F('a.py', PY_SRC),
                         // 11 700 chars, so the preview is asked for far
                         // more than the 8 000 it used to clip at.
                         F('long.py', PY_SRC.repeat(300)),
                         // One byte over TEXT_MAX: the ceiling that replaced
                         // the 8 000-char clip, so it needs a check of its own.
                         F('huge.py', 'x'.repeat(512 * 1024 + 1))]),
                F('.dotfile','h'), F('README','r'), F('short.txt','s'),
                F('this-is-a-very-long-file-name-that-must-stay-identifiable.txt'),
                // Auto-preview rungs: README beats README.* beats index.html.
                // Each folder also holds the losing names, so only the
                // priority order can explain what gets selected.
                D('docs', [F('README','plain'), F('README.md','# docs'),
                           F('index.html','<h1>idx</h1>')]),
                D('site', [F('README.md','# site'), F('index.html','<h1>s</h1>')]),
                D('web',  [F('index.html','<h1>w</h1>')]),
                F('note.md','# note'), F('data.json','{}'),
                F('nested.json', '{"name":"x","tags":["a","b"],"meta":{"n":1,"ok":true,"none":null}}'),
                F('bad.json', '{oops'),
                F('deep.json', '['.repeat(200000) + ']'.repeat(200000)),
                // Taller than any preview pane, so the pane has to say where a
                // long text scrolls: the column itself, not a box inside it.
                F('long.txt', 'a line of plain text\n'.repeat(400)),
                F('page.html','<h1>Hi</h1>'), F('doc.pdf','%PDF-1.4')]),
    D('empty', []),
    DENIED('locked'),
    SLOW('slow', [F('one.txt','1'), F('two.txt','2')]),
    D('big', big),
    // The chain inside holds names at measure()'s width ceiling, which is the
    // case the fold cap cannot answer alone: on a phone the column under the
    // finger is then wider than the stage has left once its ancestors have
    // folded to spines, and #stage clips what runs past the right edge.
    D('wide', [F('a-quite-long-file-name-1.txt'), F('a-quite-long-file-name-2.txt'),
               D(LONG(0), [D(LONG(1), [D(LONG(2), [F('leaf.md', '# leaf')])])])]),
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
    // Six orderings, all different, so no check can pass by accident. By name
    // the files read big, locked, medium, small; by size small(10) <
    // medium(100) < big(300); by date medium(Jan) < small(Feb) < big(Mar).
    // locked.txt has neither a size nor a date — getFile() refuses it.
    // Sorts after "slow", so the root row indices the keyboard checks use are
    // exactly where they were.
    D('sorting', [D('zeta', []), D('alpha', []),
                  F('big.bin',   'x'.repeat(300), '2026-03-02'),
                  F('small.txt', 'x'.repeat(10),  '2026-02-04'),
                  F('medium.md', 'x'.repeat(100), '2026-01-03'),
                  FX('locked.txt')]),
    // JSONL rows: a unique short `title` beats the unique `id`; when titles
    // repeat the id has to carry the column; a bad line or an oversized file
    // must land on the denied note, not a broken column.
    D('tables', [
      F('log.jsonl', '{"id":2,"title":"Second","ts":"2026-01-02","tags":[]}\n'
                   + '{"id":1,"title":"First","ts":"2026-01-01","tags":["a"]}\n'
                   + '{"id":3,"title":"Third","ts":"2026-01-03","tags":null}\n'),
      F('dup.jsonl', '{"id":10,"title":"Same"}\n{"id":11,"title":"Same"}\n'),
      F('bad.jsonl', '{"a":1}\nnope\n'),
      F('huge.jsonl', 'x'.repeat(512 * 1024 + 1)),
    ]),
    F('README.md','# hi\n'),
  ]);
};
/* Row names in a column, in the order the DOM has them. */
window.__rows = (i) =>
  [...document.querySelectorAll(`.col[data-i="${i}"] .row`)].map(r => r.title);
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
/* Make every metadata read take `ms`, so a sweep can be caught in flight and
   raced against a navigation. The real getFile() answers in microseconds on a
   fake handle, which is the one thing a race check cannot work with. */
window.__slowMeta = (ms) => {
  const real = window.__realMeta || (window.__realMeta = FS.loadMeta.bind(FS));
  FS.loadMeta = ms
    ? async n => { await new Promise(r => setTimeout(r, ms)); return real(n); }
    : real;
};
/* A port that rejects instead of recording the error on the row. FSA.loadMeta
   catches its own failures, but the port contract only promises to *fill*
   node.meta — and one rejection escaping the sweep would leave the column
   spinning until the tab closed. */
window.__brokenMeta = () => {
  window.__realMeta = window.__realMeta || FS.loadMeta.bind(FS);
  FS.loadMeta = async () => { throw new Error('boom'); };
};
/* The app's own share of a sweep: the fan-out, the awaits and the bookkeeping,
   with the port answering out of memory. Swept once first, so the fake's own
   File construction is behind us and the timed pass measures this app.
   The syscall the real port makes is measured in test-url.py, against a real
   filesystem, where it is the whole cost. */
window.__sweepbench = async () => {
  const node = path[focusCol];
  const clear = () => { node.metaDone = false;
                        for (const k of node.kids) delete k.meta; };
  clear(); await ensureMeta(node);          /* warm */
  clear();
  const before = window.__gets;
  const t0 = performance.now();
  await ensureMeta(node);
  return {ms: +(performance.now()-t0).toFixed(1), reads: window.__gets - before,
          rows: node.kids.length};
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


async def scroll_settled(pg, tries=40, step=100):
    """Wait until #finder has stopped moving, rather than guessing a duration.

    The dial is a CSS smooth scroll (styles.css: `scroll-behavior`), so a
    scrollLeft write glides for 400-500 ms instead of jumping — a fixed wait
    samples the animation rather than its result. Returns False if it never
    settles, so a check can say so instead of failing with no explanation.
    """
    prev = None
    for _ in range(tries):                       # 40 x 100 ms — a 4 s ceiling
        cur = await pg.evaluate("finder.scrollLeft")
        if cur == prev:
            return True
        prev = cur
        await pg.wait_for_timeout(step)
    return False


async def main():
    async with async_playwright() as p:
        # index-dev.html loads ../ui/entry-static.js as a module, which a file://
        # page may not fetch without this; the bundle needs nothing.
        b = await p.chromium.launch(args=["--allow-file-access-from-files"])
        for scheme, expected in (("dark", "dark"), ("light", "light")):
            ctx = await b.new_context(color_scheme=scheme)
            themed = await ctx.new_page()
            await themed.goto(TARGET.as_uri())
            check(f"OS {scheme} scheme selects {expected} theme",
                  await themed.evaluate("root.dataset.theme") == expected)
            check(f"OS {scheme} scheme updates theme accessibility state",
                  await themed.get_attribute("#s-theme", "aria-checked") ==
                  str(expected == "dark").lower())
            check(f"OS {scheme} scheme selects the matching palette",
                  await themed.evaluate(
                      "getComputedStyle(document.documentElement).getPropertyValue('--chrome').trim()"
                  ) == ("#1b1d21" if expected == "dark" else "#e7e7ec"))
            # No folder is mounted here, so #welcome covers the chrome and a
            # pointer click never reaches the toolbar; dispatch it directly.
            await themed.locator("#gear").dispatch_event("click")
            await themed.locator("#s-theme").dispatch_event("click")
            check(f"Manual toggle overrides {scheme} scheme",
                  await themed.evaluate("root.dataset.theme") != expected)
            check("Manual toggle updates theme accessibility state",
                  await themed.get_attribute("#s-theme", "aria-checked") ==
                  str(expected != "dark").lower())
            await ctx.close()
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
        cases = [
            ("folder", {"dir": True}, ("folder", "none", False)),
            ("data.db", {"provider": True}, ("vfs", "virtual", False)),
            ("link.desktop", {}, ("link", "desktop", False)),
            ("photo.png", {}, ("file", "image", False)),
            ("doc.pdf", {}, ("file", "pdf", False)),
            ("note.md", {}, ("file", "md", True)),
            ("captions.vtt", {}, ("file", "vtt", True)),
            ("source.py", {}, ("file", "text", True)),
        ]
        got = await pg.evaluate(
            "cases => cases.map(([name, opts]) => [name, classifyFile(name, opts)])",
            cases,
        )
        check(
            "File-kind table matches the shared UI contract",
            all(
                (row[1]["kind"], row[1]["preview"], row[1]["editable"]) == expected
                for row, (_, _, expected) in zip(got, cases)
            ),
        )
        check("file:// shows the localhost hint, not a dead picker",
              "file://" in await pg.inner_text("#w-msg"))
        await pg.evaluate(FAKE)
        await mount(pg)
        check("Root folder mounts", await pg.evaluate("path[0].name") == "workspace")
        check("Welcome screen hidden after mount", await pg.evaluate("welcome.hidden"))

        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(250)
        long = '.col[data-i="1"] .row[title^="this-is-a-very"]'
        visual = await pg.inner_text(long)
        check("Long names keep their extension", visual.endswith(".txt") and
              "identifiable" in visual)
        check("Long names keep their full accessible name",
              await pg.get_attribute(long, "aria-label") ==
              "this-is-a-very-long-file-name-that-must-stay-identifiable.txt")
        short = '.col[data-i="1"] .row[title="short.txt"]'
        check("Short names keep the existing label styling",
              await pg.eval_on_selector(short + " .label", "e=>e.textContent") == "short.txt" and
              await pg.query_selector(short + " .dim") is not None)
        no_ext = '.col[data-i="1"] .row[title="README"]'
        check("Names without extensions stay intact",
              await pg.eval_on_selector(no_ext + " .label", "e=>e.textContent") == "README")

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
        await pg.keyboard.press("ArrowRight")
        check("→ focuses the preview from the rightmost column",
              await pg.evaluate("document.activeElement?.id") == "preview")
        before = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
        await pg.keyboard.press("PageDown")
        after = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
        check("PageDown scrolls the focused preview", after > before,
              f"{before} -> {after}")
        await pg.keyboard.press("ArrowUp")
        restored = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
        check("ArrowUp scrolls the focused preview up", restored < after,
              f"{after} -> {restored}")
        await pg.keyboard.press("ArrowDown")
        down = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
        check("ArrowDown scrolls the focused preview down", down > restored,
              f"{restored} -> {down}")
        await pg.keyboard.press("PageUp")
        up = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
        check("PageUp scrolls the focused preview up", up < down,
              f"{down} -> {up}")

        print("\n── Folding dial ─────────────────────────────────────────────")
        # Both moves glide: the dial is a CSS smooth scroll either way round, so
        # wait for it to stop rather than for a clock. A flat 300 ms read the
        # fold mid-flight and counted 4 of the 5 spines.
        await pg.evaluate("finder.scrollLeft = finder.scrollWidth")
        settled = await scroll_settled(pg)
        spines = await pg.eval_on_selector_all(".col.spine", "e=>e.length")
        check("Scrolling right folds columns into spines", spines == 5,
              f"{spines} spines" + ("" if settled else ", scroll never settled"))
        await pg.evaluate("document.querySelector('.col.spine').click()")
        await scroll_settled(pg)
        check("Clicking a spine unfolds it",
              await pg.eval_on_selector_all(".col.spine", "e=>e.length") == 0)

        # Opening a folder is the user pointing at a column. The dial may fold
        # what they have walked past, never the column under the finger nor the
        # one that tap just opened — at 390 px the old arithmetic folded all of
        # it, preview first. Driving it here is what proves the *bundle* carries
        # the fold rule, not only the modular sources.
        await pg.set_viewport_size({"width": 390, "height": 700})
        await scroll_settled(pg)
        if await pg.eval_on_selector_all('.col[data-i="0"].spine', "e=>e.length"):
            await pg.click('.col[data-i="0"].spine')     # rows of a spine are hidden
            await scroll_settled(pg)
        await pg.click('.col[data-i="0"] .row:has-text("deep")')
        await scroll_settled(pg)
        fold = await pg.evaluate("""(() => {
          let uncapped = 0;
          while (uncapped < path.length &&
                 stripSpan(uncapped) + previewTarget() > finder.clientWidth) uncapped++;
          return {folded, focusCol, uncapped,
                  atOrRight: [...document.querySelectorAll('.col.spine')]
                      .map(c => +c.dataset.i).filter(i => i >= focusCol)};
        })()""")
        check("Opening a folder folds no column at or right of the touched one",
              fold["folded"] <= fold["focusCol"] and not fold["atOrRight"],
              json.dumps(fold))
        check("(the dial would have folded past it, so the check has teeth)",
              fold["uncapped"] > fold["focusCol"], json.dumps(fold))

        # Not folding the touched column is not the same as showing it. Each
        # ancestor the dial folds still costs a spine and a gutter, so with
        # names at the width ceiling the column under the finger ran off the
        # right edge and #stage clipped it — the row just tapped, cut in half.
        # Folding further is what the cap forbids, so the strip slides left by
        # exactly the overflow instead, and the ancestors leave from the left.
        await mount(pg)
        await pg.set_viewport_size({"width": 390, "height": 700})
        await scroll_settled(pg)
        await pg.click('.col[data-i="0"] .row:has-text("wide")')
        await pg.wait_for_timeout(250)
        for i in range(3):
            await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
            await pg.wait_for_timeout(250)
        await scroll_settled(pg)
        touched = await pg.evaluate("""(() => {
          const fr = finder.getBoundingClientRect();
          const col = document.querySelector(`.col[data-i="${focusCol}"]`);
          const r = col.getBoundingClientRect();
          const row = col.querySelector('.row.sel').getBoundingClientRect();
          const tf = getComputedStyle(strip).transform;
          const pan = tf && tf !== 'none' ? -new DOMMatrix(tf).m41 : 0;
          return {focusCol, pan: Math.round(pan), stage: stage.scrollLeft,
                  spine: col.classList.contains('spine'),
                  clipped: Math.round(r.right - fr.right),
                  rowClipped: Math.round(row.right - fr.right),
                  wouldClip: Math.round(r.right + pan - fr.right)};
        })()""")
        check("A tapped column too wide for what is left of the stage is slid "
              "into view, not clipped",
              touched["clipped"] <= 2 and touched["rowClipped"] <= 2
              and not touched["spine"] and touched["stage"] == 0,
              json.dumps(touched))
        check("(it really would have run past the edge, so the check has teeth)",
              touched["wouldClip"] > 0, json.dumps(touched))

        # Turning the phone is the case where the width clamp can lie. #stage's
        # width is --stage-w, which layout() writes *after* render() has chosen
        # the widths, so clamping against the stage measured the viewport the
        # user just rotated away from: 380 px columns on a 375 px screen, where
        # the pan can only choose which edge to lose. Measured before the fix,
        # from 568 px landscape to 375 px portrait: the tapped row sat 10 px
        # past the right edge until the next render healed it. #finder is the
        # live number and the one layout() reads.
        await mount(pg)
        await pg.set_viewport_size({"width": 568, "height": 320})
        await scroll_settled(pg)
        await pg.click('.col[data-i="0"] .row:has-text("wide")')
        await pg.wait_for_timeout(250)
        for i in range(3):
            await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
            await pg.wait_for_timeout(250)
        await scroll_settled(pg)
        await pg.set_viewport_size({"width": 375, "height": 812})   # rotate
        await pg.wait_for_timeout(400)
        await scroll_settled(pg)
        rotated = await pg.evaluate("""(() => {
          const fr = finder.getBoundingClientRect();
          const col = document.querySelector(`.col[data-i="${focusCol}"]`);
          const r = col.getBoundingClientRect();
          const row = col.querySelector('.row.sel').getBoundingClientRect();
          return {focusCol, widths: widths.map(Math.round),
                  cap: Math.floor(finder.clientWidth * 2 / 3),
                  clipped: Math.round(r.right - fr.right),
                  rowClipped: Math.round(row.right - fr.right)};
        })()""")
        check("Rotating to a narrower screen re-clamps the columns to it, so the "
              "tapped row is not left clipped",
              rotated["clipped"] <= 2 and rotated["rowClipped"] <= 2
              and max(rotated["widths"]) <= rotated["cap"], json.dumps(rotated))

        # Desktop is the other half of the contract: at a width where the strip
        # up to focus fits, nothing pans and nothing is clamped, so the dial
        # behaves exactly as it did before any of this.
        await mount(pg)
        await pg.set_viewport_size({"width": 1500, "height": 900})
        await scroll_settled(pg)
        await pg.click('.col[data-i="0"] .row:has-text("wide")')
        await pg.wait_for_timeout(250)
        for i in range(3):
            await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
            await pg.wait_for_timeout(250)
        await scroll_settled(pg)
        desktop = await pg.evaluate("""(() => {
          const fr = finder.getBoundingClientRect();
          const col = document.querySelector(`.col[data-i="${focusCol}"]`);
          const r = col.getBoundingClientRect();
          const tf = getComputedStyle(strip).transform;
          const pan = tf && tf !== 'none' ? -new DOMMatrix(tf).m41 : 0;
          return {focusCol, pan: Math.round(pan), widths: widths.map(Math.round),
                  natural: Math.max(...widths.map(Math.round)),
                  cap: Math.floor(finder.clientWidth * 2 / 3),
                  whole: r.left >= fr.left - 2 && r.right <= fr.right + 2};
        })()""")
        check("On a desktop-width screen the strip never pans and the columns "
              "keep their natural width",
              desktop["pan"] == 0 and desktop["whole"]
              and desktop["natural"] <= desktop["cap"], json.dumps(desktop))

        # The whole model, one check per device class (ADR 0062). Every
        # viewport walks the same four folders at the width ceiling and asserts
        # the same promises: the touched column and its row are whole, the
        # column that tap opened starts on screen unless the pan had to give
        # the touched column the whole width (ADR 0024), nothing right of focus
        # is a spine, no column is wider than two thirds of the finder, and the
        # strip moved by its own transform, never by scrolling #stage. Which
        # mechanism got there differs — the phones fold and pan, the tablet and
        # desktop fit — and the detail shows it.
        for label, w, h in (("phone portrait", 390, 844),
                            ("phone landscape", 844, 390),
                            ("tablet", 1024, 768),
                            ("desktop", 1440, 900)):
            await mount(pg)
            await pg.set_viewport_size({"width": w, "height": h})
            await scroll_settled(pg)
            await pg.click('.col[data-i="0"] .row:has-text("wide")')
            await pg.wait_for_timeout(250)
            for i in range(3):
                await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
                await pg.wait_for_timeout(250)
            await scroll_settled(pg)
            m = await pg.evaluate("""(() => {
              const fr = finder.getBoundingClientRect();
              const col = document.querySelector(`.col[data-i="${focusCol}"]`);
              const opened = document.querySelector(`.col[data-i="${focusCol + 1}"]`);
              const r = col.getBoundingClientRect();
              const row = col.querySelector('.row.sel').getBoundingClientRect();
              const o = opened.getBoundingClientRect();
              const tf = getComputedStyle(strip).transform;
              const pan = tf && tf !== 'none' ? -new DOMMatrix(tf).m41 : 0;
              return {focusCol, folded, pan: Math.round(pan), stage: stage.scrollLeft,
                      touchedWhole: r.left >= fr.left - 2 && r.right <= fr.right + 2,
                      rowWhole: row.left >= fr.left - 2 && row.right <= fr.right + 2,
                      openedStartsInside: o.left >= fr.left - 2 && o.left <= fr.right - 2,
                      spinesAtOrRight: [...document.querySelectorAll('.col.spine')]
                          .map(c => +c.dataset.i).filter(i => i >= focusCol),
                      maxWidth: Math.max(...widths.map(Math.round)),
                      cap: Math.floor(finder.clientWidth * 2 / 3)};
            })()""")
            check(f"{label} {w}x{h}: the touched column stays whole, the opened "
                  "column starts on screen unless the pan took its room, nothing "
                  "at or right of focus folds",
                  m["focusCol"] == 3 and m["touchedWhole"] and m["rowWhole"]
                  and (m["openedStartsInside"] or m["pan"] > 0)
                  and not m["spinesAtOrRight"]
                  and m["stage"] == 0 and m["maxWidth"] <= m["cap"],
                  json.dumps(m))

        # Walking in on a narrow screen leaves the focused column reaching past
        # the right edge — 4 spines and a 148 px column need 334 of 320 — so
        # applyScroll slides the strip left by that difference and the column
        # the keyboard is in stays whole. That pan is the *only* thing allowed
        # to move the strip: scrollIntoView() would scroll #stage instead,
        # dragging every column out through the left edge for good, because the
        # dial writes #finder and nothing ever scrolls #stage back. revealRow()
        # scrolls the column body, which is the only axis a row needs.
        await mount(pg)
        await pg.set_viewport_size({"width": 320, "height": 700})
        await scroll_settled(pg)
        await pg.click('.col[data-i="0"] .row:has-text("deep")')
        await pg.wait_for_timeout(250)
        for _ in range(4):                           # in to the leaf column
            await pg.keyboard.press("ArrowRight")
            await pg.wait_for_timeout(300)
        await scroll_settled(pg)
        strip_pos = await pg.evaluate("""(() => {
          const fr = finder.getBoundingClientRect();
          const focused = document.querySelector(`.col[data-i="${focusCol}"]`)
              .getBoundingClientRect();
          const tf = getComputedStyle(strip).transform;
          const pan = tf && tf !== 'none' ? -new DOMMatrix(tf).m41 : 0;
          return {stage: stage.scrollLeft, focusCol, pan: Math.round(pan),
                  clipped: Math.round(focused.right - fr.right),
                  wouldClip: Math.round(focused.right + pan - fr.right),
                  leftmost: Math.round(Math.min(...[...document.querySelectorAll('.col')]
                      .map(c => c.getBoundingClientRect().left)))};
        })()""")
        # The strip may sit left of the gutter by the pan and by nothing else:
        # a scrollIntoView() regression moved it 114 px further and scrolled
        # #stage to do it, which is the pair this check is watching for.
        check("Reaching a row never scrolls the strip out of the finder",
              strip_pos["stage"] == 0
              and strip_pos["leftmost"] >= -strip_pos["pan"] - 2,
              json.dumps(strip_pos))
        check("(the focused column really would reach past the edge, so it has teeth)",
              strip_pos["wouldClip"] > 0 and strip_pos["clipped"] <= 2,
              json.dumps(strip_pos))

        # The other half of revealRow: it replaced a browser primitive, so the
        # axis a row *does* need still has to work. A short viewport makes a
        # nine-row column overflow, and End has to bring the last row back.
        await mount(pg)
        await pg.set_viewport_size({"width": 320, "height": 260})
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(250)
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_timeout(250)
        await pg.keyboard.press("End")
        await pg.wait_for_timeout(250)
        seen = await pg.evaluate("""(() => {
          const row = document.querySelector('.col.focus .row.cursor');
          if (!row) return null;
          const body = row.closest('.col-body');
          const r = row.getBoundingClientRect(), b = body.getBoundingClientRect();
          return {above: Math.round(r.top - b.top),
                  below: Math.round(b.bottom - r.bottom),
                  scrolled: Math.round(body.scrollTop)};
        })()""")
        check("End scrolls the cursor row into view inside its own column",
              seen and seen["above"] >= -1 and seen["below"] >= -1, json.dumps(seen))
        check("(the column really had to scroll for it, so the check has teeth)",
              seen and seen["scrolled"] > 0, json.dumps(seen))
        end_scroll = seen["scrolled"]
        await pg.keyboard.press("Home")
        await pg.wait_for_timeout(250)
        seen = await pg.evaluate("""(() => {
          const row = document.querySelector('.col.focus .row.cursor');
          const body = row.closest('.col-body');
          const r = row.getBoundingClientRect(), b = body.getBoundingClientRect();
          return {above: Math.round(r.top - b.top),
                  below: Math.round(b.bottom - r.bottom),
                  scrolled: Math.round(body.scrollTop)};
        })()""")
        # Not scrollTop 0: `block: "nearest"` aligns the row with the scrollport,
        # which scrolls the body's own top padding away. Measured identical
        # against the scrollIntoView() this replaced — the point of the check is
        # that the arithmetic is the primitive's, not that it improves on it.
        check("Home brings it back the other way",
              seen["above"] >= -1 and seen["below"] >= -1
              and seen["scrolled"] < end_scroll, json.dumps(seen))

        await pg.keyboard.press("PageDown")
        await pg.wait_for_timeout(250)
        first_page = await pg.evaluate("""(() => {
          const col = document.querySelector('.col.focus');
          const body = col.querySelector('.col-body'), b = body.getBoundingClientRect();
          const rows = [...col.querySelectorAll('.row')].filter(r => {
            const x = r.getBoundingClientRect();
            return x.bottom > b.top && x.top < b.bottom;
          });
          return {selected: col.querySelector('.row.cursor')?.textContent,
                  edge: rows.at(-1)?.textContent, scroll: body.scrollTop};
        })()""")
        check("PageDown first moves to the visible bottom row",
              first_page and first_page["selected"] == first_page["edge"],
              json.dumps(first_page))
        await pg.keyboard.press("PageDown")
        await pg.wait_for_timeout(250)
        second_page = await pg.evaluate("""(() => {
          const col = document.querySelector('.col.focus');
          const body = col.querySelector('.col-body');
          return {selected: col.querySelector('.row.cursor')?.textContent,
                  scroll: body.scrollTop, max: body.scrollHeight - body.clientHeight};
        })()""")
        check("PageDown at the edge scrolls by a fitted page",
              second_page and second_page["scroll"] > first_page["scroll"]
              and second_page["scroll"] <= second_page["max"] + 1,
              json.dumps(second_page))
        await pg.keyboard.press("PageUp")
        await pg.wait_for_timeout(250)
        third_page = await pg.evaluate("""(() => {
          const col = document.querySelector('.col.focus');
          const body = col.querySelector('.col-body'), b = body.getBoundingClientRect();
          const rows = [...col.querySelectorAll('.row')].filter(r => {
            const x = r.getBoundingClientRect();
            return x.bottom > b.top && x.top < b.bottom;
          });
          return {selected: col.querySelector('.row.cursor')?.textContent,
                  edge: rows[0]?.textContent, scroll: body.scrollTop};
        })()""")
        check("PageUp returns to the visible top row",
              third_page and third_page["selected"] == third_page["edge"],
              json.dumps(third_page))
        await pg.set_viewport_size({"width": 1500, "height": 900})
        await pg.wait_for_timeout(200)

        print("\n── Preview ──────────────────────────────────────────────────")
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(250)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        await pg.wait_for_timeout(400)
        check("Text file previews its contents",
              (await pg.inner_text(".pv-text")).strip() == "# note")
        check("Preview offers fullscreen control",
              await pg.get_attribute("#pv-fullscreen", "aria-pressed") == "false")
        await pg.focus("#pv-fullscreen")
        await pg.keyboard.press("Enter")
        full = await pg.evaluate("""() => {
          const pv = document.querySelector('#preview').getBoundingClientRect();
          const cs = getComputedStyle(document.querySelector('#preview .pv-body'));
          return {bar: getComputedStyle(document.querySelector('#bar')).display,
                  status: getComputedStyle(document.querySelector('#status')).display,
                  padding: cs.padding,
                  preview: [Math.round(pv.left), Math.round(pv.top),
                            Math.round(pv.width), Math.round(pv.height)]};
        }""")
        check("Fullscreen hides chrome and removes preview padding",
              full["bar"] == full["status"] == "none" and full["padding"] == "0px",
              json.dumps(full))
        await pg.keyboard.press("Enter")
        check("Fullscreen control exits with keyboard",
              await pg.get_attribute("#pv-fullscreen", "aria-pressed") == "false")
        check("Preview shows real size and mtime",
              "B ·" in await pg.inner_text("#pv-sub"), await pg.inner_text("#pv-sub"))
        await pg.click('.col[data-i="1"] .row:has-text("long.txt")')
        await pg.wait_for_timeout(400)
        # A text box that stopped at part-height left the rest of the column
        # empty and scrolled on its own, so the column never used its height.
        fit = await pg.evaluate("""() => {
          const t = document.querySelector('.pv-text');
          const b = document.querySelector('#preview .pv-body');
          return {inner:  t.scrollHeight > t.clientHeight + 1,
                  column: b.scrollHeight > b.clientHeight + 1};
        }""")
        check("A long text preview grows no scrollbar of its own",
              not fit["inner"], json.dumps(fit))
        check("…the whole preview column scrolls instead",
              fit["column"], json.dumps(fit))
        await pg.click('.col[data-i="1"] .row:has-text("page.html")')
        await pg.wait_for_timeout(400)
        check("HTML file previews in an iframe",
              await pg.is_visible("iframe.pv-html"))
        # 100cqh/100%: the frame must fill one visible screen of .pv-body,
        # whatever width the fold dial has left the pane.
        fit = await pg.evaluate("""(() => {
          const f = document.querySelector('iframe.pv-html').getBoundingClientRect();
          const b = document.querySelector('.pv-body'), cs = getComputedStyle(b);
          return [f.width  - (b.clientWidth  - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)),
                  f.height - (b.clientHeight - parseFloat(cs.paddingTop)  - parseFloat(cs.paddingBottom))];
        })()""")
        check("…sized to one visible screen of the pane",
              all(abs(d) < 2 for d in fit), str(fit))
        await pg.click('.col[data-i="1"] .row:has-text("doc.pdf")')
        await pg.wait_for_timeout(400)
        check("PDF file previews in an iframe",
              await pg.is_visible("iframe.pv-pdf"))
        # The same rule as .pv-html: no half-height box inside the pane.
        fit = await pg.evaluate("""(() => {
          const f = document.querySelector('iframe.pv-pdf').getBoundingClientRect();
          const b = document.querySelector('.pv-body'), cs = getComputedStyle(b);
          return [f.width  - (b.clientWidth  - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)),
                  f.height - (b.clientHeight - parseFloat(cs.paddingTop)  - parseFloat(cs.paddingBottom))];
        })()""")
        check("…sized to one visible screen of the pane",
              all(abs(d) < 2 for d in fit), str(fit))
        await pg.click('.col[data-i="1"] .row:has-text("sub")')
        await pg.wait_for_timeout(250)
        check("Selecting a folder clears the preview",
              await pg.is_visible(".pv-empty"))

        # ── Syntax highlighting — core/syntax.js, the same file the server
        # build loads. Rich previews are off in this suite, so what runs here
        # is the offline path every build falls back to.
        await pg.click('.col[data-i="2"] .row:has-text("a.py")')
        await pg.wait_for_timeout(400)
        check("Source previews with every token class coloured",
              await pg.eval_on_selector_all(
                  ".pv-text span",
                  "e=>[...new Set(e.map(x=>x.className))].sort().join()")
              == "hl-com,hl-kw,hl-num,hl-str")
        check("…and the file still reads exactly as written",
              (await pg.text_content(".pv-text")) == PY_SRC)
        check("…and a coloured file is still editable",
              await pg.is_visible("#pv-edit"))
        # Column 88: the box never narrows below 88ch, and on a normal screen
        # the pane is wide enough that nothing scrolls sideways.
        WIDTH = """() => {
          const t = document.querySelector('.pv-text'), cs = getComputedStyle(t);
          const b = document.querySelector('#preview .pv-body');
          const probe = document.createElement('span');
          probe.textContent = '0'.repeat(88); probe.style.font = cs.font;
          probe.style.whiteSpace = 'pre'; probe.style.position = 'absolute';
          t.append(probe); const ch88 = probe.getBoundingClientRect().width; probe.remove();
          const lh = parseFloat(cs.lineHeight);
          return {code: t.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight),
                  ch88, lines: Math.round((t.clientHeight - parseFloat(cs.paddingTop)
                                           - parseFloat(cs.paddingBottom)) / lh),
                  sideways: b.scrollWidth > b.clientWidth + 1};
        }"""
        w = await pg.evaluate(WIDTH)
        check("A source preview is at least 88 columns wide",
              w["code"] >= w["ch88"] - 0.5, json.dumps(w))
        check("…without a sideways scrollbar on a normal screen",
              not w["sideways"], json.dumps(w))
        check("…and an 88-column line stays on one line",
              w["lines"] == 4, json.dumps(w))
        # Zoomed to ~170 %, the CSS viewport is 900 px wide. The pane must keep
        # its 88 columns rather than wrap the line; longer lines still wrap at
        # column 88 or later, and a pane narrower than that scrolls .pv-body.
        await pg.set_viewport_size({"width": 900, "height": 700})
        await pg.wait_for_timeout(300)
        w = await pg.evaluate(WIDTH)
        check("Zoomed in, the source preview still holds 88 columns",
              w["code"] >= w["ch88"] - 0.5, json.dumps(w))
        check("…and the 88-column line still stays on one line",
              w["lines"] == 4, json.dumps(w))
        # A phone cannot show 88 columns. With the dial at 100 % the pane is
        # alone and must fit the stage — what runs past the right edge is
        # clipped, not scrollable — and the code pans inside .pv-body instead.
        await pg.set_viewport_size({"width": 390, "height": 700})
        await pg.wait_for_timeout(300)
        await pg.evaluate("finder.scrollLeft = finder.scrollWidth")
        await pg.wait_for_timeout(400)
        w = await pg.evaluate(WIDTH)
        fits = await pg.evaluate("""(() => {
          const p = document.getElementById('preview').getBoundingClientRect();
          const s = stage.getBoundingClientRect();
          return {ok: p.left >= s.left - 1 && p.right <= s.right + 1,
                  preview: [Math.round(p.left), Math.round(p.right)],
                  stage: [Math.round(s.left), Math.round(s.right)],
                  target: previewTarget(), scroll: finder.scrollLeft,
                  max: finder.scrollWidth - finder.clientWidth};
        })()""")
        check("On a phone the preview pane fits the stage",
              fits["ok"] and w["code"] >= w["ch88"] - 0.5, json.dumps(w) + json.dumps(fits))
        check("…and the 88 columns pan inside the pane instead of clipping",
              w["sideways"] and w["lines"] == 4, json.dumps(w))
        await pg.set_viewport_size({"width": 1500, "height": 900})
        await pg.wait_for_timeout(300)
        # Both palettes are declared; that they are legible is a screenshot's
        # job, but a theme that never reaches the tokens is a bug this catches.
        colour = "e=>getComputedStyle(e).color"
        was = await pg.evaluate("root.dataset.theme")
        light = await pg.eval_on_selector(".pv-text .hl-kw", colour)
        await pg.evaluate("root.dataset.theme = 'dark'")
        dark = await pg.eval_on_selector(".pv-text .hl-kw", colour)
        check("Each theme colours the tokens its own way",
              light != dark, f"{light} vs {dark}")
        await pg.evaluate(f"root.dataset.theme = {was!r}")
        # Past the 8 000 characters the preview used to stop at. The text check
        # alone would pass on a build that coloured the head and escaped the
        # tail, so the span count is what proves colour reaches the last line:
        # def + return is two keywords per copy, 600 across the 300.
        await pg.click('.col[data-i="2"] .row:has-text("long.py")')
        await pg.wait_for_timeout(500)
        whole = await pg.text_content(".pv-text")
        kw = await pg.eval_on_selector_all(".pv-text .hl-kw", "e=>e.length")
        check("A source file past the old 8 000-character clip previews whole",
              whole == PY_SRC * 300,
              f"{len(whole)} chars, expected {len(PY_SRC) * 300}")
        check("…and is coloured to its last line, not just the first 8 000 chars",
              kw == 600, f"{kw} hl-kw spans, expected 600")
        # …and the ceiling that replaced the clip. Removing the 8 000-char cut
        # only made the 512 KB gate load-bearing, so one byte over it must still
        # decline rather than render — otherwise "whole or absent" has no second
        # half and a 50 MB .sql renders whole.
        await pg.click('.col[data-i="2"] .row:has-text("huge.py")')
        await pg.wait_for_timeout(500)
        body = await pg.inner_text("#pv-content")
        check("One byte over TEXT_MAX is declined, not rendered",
              not await pg.is_visible(".pv-text")
              and "No inline preview" in body, body[:80])
        # The phone pass above folded two columns, and a fold outlives the
        # resize back: unfolding is a user action, so make it one.
        if await pg.eval_on_selector_all('.col[data-i="1"].spine', "e=>e.length"):
            await pg.click('.col[data-i="1"].spine')
            await scroll_settled(pg)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        await pg.wait_for_timeout(300)
        check("A file with no language it knows stays plain",
              await pg.eval_on_selector_all(".pv-text span", "e=>e.length") == 0)

        print("\n── JSONL rows ───────────────────────────────────────────────")
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("tables")')
        await pg.wait_for_timeout(300)
        await pg.click('.col[data-i="1"] .row:has-text("log.jsonl")')
        await pg.wait_for_timeout(400)
        check("A .jsonl file opens as a column of rows named by the unique short text key",
              await pg.evaluate("__rows(2)") == ["Second", "First", "Third"],
              str(await pg.evaluate("__rows(2)")))
        await pg.click('.col[data-i="2"] .row:has-text("Second")')
        await pg.wait_for_timeout(400)
        kv = await pg.evaluate(
            "[...document.querySelectorAll('#pv-content .pv-kv tr')]"
            ".map(r => [r.children[0].textContent, r.children[1].textContent])")
        check("A row previews as a two-column key/value table",
              kv == [["id", "2"], ["title", "Second"], ["ts", "2026-01-02"], ["tags", "[]"]],
              str(kv))
        check("…with no invented size or date",
              await pg.inner_text("#pv-sub") == "")
        await pg.evaluate("applyPath(['tables', 'log.jsonl', 'Third'])")
        await pg.wait_for_timeout(400)
        check("A deep link names a row and restores it",
              (await pg.evaluate("sel"))[-1] == "Third"
              and "2026-01-03" in await pg.inner_text("#pv-content"))
        await pg.click('.col[data-i="1"] .row:has-text("dup.jsonl")')
        await pg.wait_for_timeout(400)
        check("Repeated titles fall back to the unique scalar key",
              await pg.evaluate("__rows(2)") == ["10", "11"], str(await pg.evaluate("__rows(2)")))
        await pg.click('.col[data-i="1"] .row:has-text("bad.jsonl")')
        await pg.wait_for_timeout(400)
        note = await pg.inner_text('.col[data-i="2"]')
        check("A malformed line lands on the denied note, not a column",
              "Not valid JSONL: line 2" in note and await pg.evaluate("__rows(2)") == [], note)
        await pg.click('.col[data-i="1"] .row:has-text("huge.jsonl")')
        await pg.wait_for_timeout(400)
        note = await pg.inner_text('.col[data-i="2"]')
        check("One byte over the ceiling is declined the same way",
              "Too large" in note and await pg.evaluate("__rows(2)") == [], note)
        # back where the sections below expect to find note.md
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(300)

        print("\n── Edit mode ────────────────────────────────────────────────")
        await pg.click('.col[data-i="1"] .row:has-text("long.txt")')
        await pg.wait_for_timeout(400)
        await pg.click("#pv-edit")
        await pg.wait_for_timeout(200)
        top = await pg.evaluate("""() => {
          const ta = document.querySelector('#pv-editor');
          return {start: ta.selectionStart, end: ta.selectionEnd,
                  scroll: ta.scrollTop, value: ta.value};
        }""")
        check("Plaintext edit starts at the top",
              top["start"] == top["end"] == top["scroll"] == 0
              and top["value"] == "a line of plain text\n" * 400,
              json.dumps({**top, "value": f"{len(top['value'])} chars"}))
        await pg.click("#pv-cancel")
        await pg.wait_for_timeout(300)
        await pg.click('.col[data-i="1"] .row:has-text("sub")')
        await pg.wait_for_timeout(300)
        await pg.click('.col[data-i="2"] .row:has-text("long.py")')
        await pg.wait_for_timeout(400)
        await pg.click("#pv-edit")
        await pg.wait_for_timeout(200)
        top = await pg.evaluate("""() => {
          const ta = document.querySelector('#pv-editor');
          return {start: ta.selectionStart, end: ta.selectionEnd,
                  scroll: ta.scrollTop, value: ta.value};
        }""")
        check("Highlighted edit starts at the top",
              top["start"] == top["end"] == top["scroll"] == 0
              and top["value"] == PY_SRC * 300,
              json.dumps({**top, "value": f"{len(top['value'])} chars"}))
        await pg.click("#pv-cancel")
        await pg.wait_for_timeout(300)
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(300)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        await pg.wait_for_timeout(400)
        check("Text preview offers an Edit button",
              await pg.is_visible("#pv-edit"))
        await pg.click("#pv-edit")
        await pg.wait_for_timeout(200)
        check("Edit opens a textarea with the full text",
              await pg.input_value("#pv-editor") == "# note")
        st = await pg.evaluate("__state()")
        await pg.type("#pv-editor", "x")
        await pg.keyboard.press("ArrowDown")
        check("Typing in the editor does not move the columns",
              await pg.evaluate("__state()") == st)
        await pg.click("#pv-cancel")
        await pg.wait_for_timeout(300)
        check("Cancel returns the unchanged read-only preview",
              (await pg.inner_text(".pv-text")).strip() == "# note")
        await pg.click("#pv-edit")
        await pg.wait_for_timeout(200)
        await pg.fill("#pv-editor", "# edited")
        await pg.click("#pv-save")
        await pg.wait_for_timeout(400)
        check("Save writes the file and returns to the preview",
              (await pg.inner_text(".pv-text")).strip() == "# edited")
        await pg.click('.col[data-i="1"] .row:has-text("data.json")')
        await pg.wait_for_timeout(300)
        await pg.click('.col[data-i="1"] .row:has-text("note.md")')
        await pg.wait_for_timeout(400)
        check("The change survives re-opening the file",
              (await pg.inner_text(".pv-text")).strip() == "# edited")
        await pg.click('.col[data-i="1"] .row:has-text("page.html")')
        await pg.wait_for_timeout(400)
        check("A non-text preview offers no Edit button",
              await pg.is_hidden("#pv-edit"))

        print("\n── JSON preview ─────────────────────────────────────────────")
        await pg.click('.col[data-i="1"] .row:has-text("nested.json")')
        await pg.wait_for_timeout(400)
        check("Valid JSON opens as an ordered key column",
              await pg.evaluate("__rows(2)") == ["name", "tags", "meta"])
        await pg.click('.col[data-i="2"] .row:has-text("tags")')
        await pg.wait_for_timeout(300)
        check("Nested arrays open as ordered index rows",
              await pg.evaluate("__rows(3)") == ["0", "1"])
        await pg.click('.col[data-i="3"] .row:has-text("0")')
        await pg.wait_for_timeout(300)
        check("Scalar JSON values preview in the pane",
              (await pg.inner_text(".pv-content")).strip() == "a")
        await pg.click('.col[data-i="2"] .row:has-text("meta")')
        await pg.wait_for_timeout(300)
        check("Nested objects remain navigable",
              await pg.evaluate("__rows(3)") == ["n", "ok", "none"])
        await pg.click('.col[data-i="1"] .row:has-text("bad.json")')
        await pg.wait_for_selector(".pv-text:not(.pv-json)")
        check("Invalid JSON keeps the coloured-source fallback",
              (await pg.inner_text(".pv-text")) == "{oops")
        await pg.click('.col[data-i="1"] .row:has-text("deep.json")')
        await pg.wait_for_selector(".pv-text:not(.pv-json)")
        check("JSON nested past the stack is shown as source, not an error",
              (await pg.inner_text(".pv-text")).startswith("[[[["))

        print("\n── Auto-preview ─────────────────────────────────────────────")
        await pg.click('.col[data-i="1"] .row:has-text("docs")')
        await pg.wait_for_timeout(250)
        st = await pg.evaluate("__state()")
        check("Folder with a README auto-previews it, focus unmoved",
              st["sel"] == ["mixed", "docs", "README"] and st["focusCol"] == 1,
              json.dumps(st))
        check("…dash-selected in the contents column",
              await pg.get_attribute('.col[data-i="2"].descendant .row.sel', "title")
              == "README")
        check("…and named in the preview header",
              "README" in await pg.inner_text("#preview .col-head .name"))
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_timeout(250)
        check("→ enters the column on the auto-previewed row",
              await pg.evaluate("focusCol") == 2 and
              await pg.evaluate("sel[2]") == "README")
        await pg.keyboard.press("ArrowLeft")
        await pg.wait_for_timeout(200)
        await pg.click('.col[data-i="1"] .row:has-text("site")')
        await pg.wait_for_timeout(250)
        check("README.* wins over index.html",
              await pg.evaluate("sel[2]") == "README.md")
        await pg.click('.col[data-i="1"] .row:has-text("web")')
        await pg.wait_for_timeout(400)
        check("index.html previews when no README exists",
              await pg.evaluate("sel[2]") == "index.html" and
              await pg.is_visible("iframe.pv-html"))

        print("\n── Settings ─────────────────────────────────────────────────")
        # An 88-column preview folds the walked-past root column here; open
        # its spine first, as a user would, before clicking a row in it.
        await pg.evaluate("document.querySelector('.col.spine')?.click()")
        await pg.wait_for_timeout(300)
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(200)
        before = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length")
        await pg.click("#gear")
        await pg.click("#s-dot")
        await pg.wait_for_timeout(200)
        after = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length")
        check("Dotfile toggle reveals hidden entries", after == before + 1, f"{before}→{after}")
        # The Previews group starts hidden and only preview-rich.js (loaded in
        # this build) reveals it — a build without the toggle shows no heading.
        check("Previews group is revealed with its rich toggle",
              await pg.evaluate("!document.getElementById('s-previews').hidden"
                                " && !document.getElementById('s-rich').hidden"))
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

        # The button has to be *painted* on the focused column, not merely
        # present. `folding` is not a transient state — layout.js puts it on
        # column `folded`, which at rest is the root — so a rule keyed on it hid
        # the button on the root for ever, and on whichever column the dial was
        # mid-fold on. Park the pointer first: `.col:hover` would otherwise show
        # the button and hide the bug, which is exactly why it read as a
        # keyboard-only fault.
        await mount(pg)
        await pg.mouse.move(1499, 899)
        await pg.wait_for_timeout(200)
        root_col = await pg.evaluate(
            "({cls: document.querySelector('.col[data-i=\"0\"]').className,"
            " w: document.querySelector('.col[data-i=\"0\"] .col-head .rf')"
            "     .getBoundingClientRect().width})")
        check("The focused root column shows ⟳, even though the dial calls it "
              "“folding”",
              root_col["w"] > 0 and "focus" in root_col["cls"],
              f"class={root_col['cls']!r}, painted width {root_col['w']}")
        check("(the root really is the folding column, so the check has teeth)",
              "folding" in root_col["cls"], root_col["cls"])

        # …and after ← lands focus on a column the dial is folding.
        await pg.set_viewport_size({"width": 760, "height": 700})
        await pg.keyboard.press("Home")
        await pg.wait_for_timeout(250)
        await pg.keyboard.press("ArrowDown")            # "deep"
        await pg.wait_for_timeout(250)
        for _ in range(4):                              # walk to the leaf
            await pg.keyboard.press("ArrowRight")
            await pg.wait_for_timeout(350)
        await pg.mouse.move(759, 699)
        painted = []
        landed = []
        for _ in range(4):                              # and back out again
            st = await pg.evaluate(
                "(() => { const el = document.querySelector('.col.focus');"
                " const rf = el && el.querySelector('.col-head .rf');"
                " return {cls: el && el.className,"
                "         w: rf ? rf.getBoundingClientRect().width : -1}; })()")
            painted.append((st["cls"], st["w"]))
            await pg.keyboard.press("ArrowLeft")
            await pg.wait_for_timeout(350)
            await scroll_settled(pg)
            landed.append(await pg.evaluate(
                "(() => { const el = document.querySelector('.col.focus');"
                " return {f: focusCol, d: folded, sp: SPINE(),"
                "         w: Math.round(el.getBoundingClientRect().width)}; })()"))
        check("Every column ← lands on shows ⟳, folding or not",
              all(w > 0 for _, w in painted),
              "; ".join(f"{c}→{w}" for c, w in painted))
        # The dial lands on round(k·unit·range), up to half a pixel short of the
        # boundary. Read with too small a slack that is one column *fewer*
        # folded, t ≈ 1: the column just reached paints as a spine, and since
        # folded === focusCol the next ← has nothing left to unfold. Measured
        # here, in this fixture at 760 px, on the second ← before the fix.
        check("← unfolds the column it lands on, at every depth",
              all(s["d"] == s["f"] and s["w"] > s["sp"] for s in landed),
              "; ".join(f"focus {s['f']} folded {s['d']} {s['w']}px" for s in landed))
        await pg.set_viewport_size({"width": 1500, "height": 900})
        await pg.wait_for_timeout(200)

        # A re-read replaces every node object in the column, including the one
        # whose preview is on screen. The guard is pvToken, the same counter a
        # slow file read already answers to: the re-render starts a new fill,
        # which retires the old one wherever it had got to.
        await in_refresh()
        await pg.keyboard.press("ArrowDown")           # one.txt, contents "1"
        await pg.wait_for_timeout(500)
        was = await pg.evaluate("pvToken")
        await pg.keyboard.press("F5")
        await pg.wait_for_timeout(700)
        now = await pg.evaluate("pvToken")
        body = (await pg.inner_text(".pv-text")).strip()
        check("A refresh retires the preview built for the node it replaced, "
              "and the new one shows the same file",
              now > was and body == "1" and await pg.evaluate("sel[1]") == "one.txt",
              f"pvToken {was}→{now}, preview {body!r}")

        # The entry you were on is gone. Selecting whatever slid into its place
        # would show a preview of a file nobody asked for, so nothing is
        # selected — and the unified name selection must not move to whatever
        # row slid into its place.
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
            "({...__state(),"
            " say: document.getElementById('st-refresh').textContent})")
        check("A selected file that vanished leaves nothing selected, and says so",
              snap["sel"] == ["refresh"] and snap["focusCol"] == 1
              and "two.txt is gone" in snap["say"], json.dumps(snap))
        await pg.keyboard.press("ArrowDown")
        await pg.wait_for_timeout(250)
        check("…so ↓ selects the first remaining row",
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
        # Both clicks inside one page call, so the 150 ms gap is 150 ms of app
        # time. Driven from here it was two Playwright round-trips wide, and on
        # a loaded machine that exceeds the 400 ms debounce and splits the write
        # this check exists to prove is single. It flaked twice in five runs.
        early = await pg.evaluate("""(async () => {
          document.querySelector('.col[data-i="0"] .row[title="mixed"]').click();
          await new Promise(r => setTimeout(r, 150));
          document.querySelector('.col[data-i="1"] .row[title="note.md"]').click();
          return __saved.length;
        })()""")
        await pg.wait_for_timeout(800)
        saved = await pg.evaluate("__saved")
        check("Mounting a folder does not overwrite the chain it just restored",
              start_saves == 0, f"{start_saves} writes during mount")
        check("Two navigations 150 ms apart collapse into one write",
              early == 0 and len(saved) == 1, f"{early} early, {len(saved)} total")
        check("What is stored is the folder and the chain inside it",
              saved == [["workspace", ["mixed", "note.md"]]], str(saved))

        print("\n── Sort options ─────────────────────────────────────────────")
        # The `sorting` folder is built so that every ordering below disagrees
        # with every other one. What the checks are really about is the *reads*:
        # sorting by name must cost none, and sorting by size must cost one
        # getFile() per row and then never ask again.
        NAME_ASC = ["alpha", "zeta", "big.bin", "locked.txt", "medium.md", "small.txt"]
        NAME_DESC = ["zeta", "alpha", "small.txt", "medium.md", "locked.txt", "big.bin"]
        SIZE_ASC = ["alpha", "zeta", "small.txt", "medium.md", "big.bin", "locked.txt"]
        SIZE_DESC = ["alpha", "zeta", "big.bin", "medium.md", "small.txt", "locked.txt"]
        MTIME_ASC = ["alpha", "zeta", "medium.md", "small.txt", "big.bin", "locked.txt"]

        async def in_sorting():
            """Mount fresh on the default sort and open the `sorting` folder."""
            await pg.evaluate("setSort('name', false)")
            await mount(pg)
            await pg.click('.col[data-i="0"] .row:has-text("sorting")')
            await pg.wait_for_timeout(300)

        await in_sorting()
        gets = await pg.evaluate("__gets")
        check("The default sort is by name, and it opens a folder without "
              "reading a single file",
              await pg.evaluate("__rows(1)") == NAME_ASC and gets == 0,
              f"{gets} getFile() calls — a name is already in the listing")

        await pg.evaluate("setSort('size', false)")
        await pg.wait_for_timeout(400)
        gets = await pg.evaluate("__gets")
        # 4 files in `sorting` and 1 (README.md) in the root column beside it.
        # The other nine directories in the tree are not on screen and are not
        # touched: the sweep covers what is displayed, not what exists.
        check("Sorting by size reorders the column, at one getFile() per row",
              await pg.evaluate("__rows(1)") == SIZE_ASC and gets == 5,
              f"{gets} reads: 4 files here, 1 in the root column, 0 elsewhere")

        await pg.evaluate("render(true)")
        await pg.wait_for_timeout(200)
        check("…and a re-render re-reads none of them",
              await pg.evaluate("__gets") == gets,
              f"{await pg.evaluate('__gets') - gets} extra reads")

        await pg.evaluate("setSort('size', true)")
        await pg.wait_for_timeout(300)
        desc = await pg.evaluate("__rows(1)")
        check("Descending reverses the order and sweeps nothing a second time",
              desc == SIZE_DESC and await pg.evaluate("__gets") == gets, str(desc))
        check("A file the port refused to stat sorts last in both directions, "
              "and is dropped from neither",
              SIZE_ASC[-1] == "locked.txt" and desc[-1] == "locked.txt"
              and len(desc) == 6,
              "biggest-first must not answer with a file nobody could open")

        await pg.evaluate("setSort('mtime', false)")
        await pg.wait_for_timeout(300)
        check("Modified orders by date, on the sweep the size sort already paid",
              await pg.evaluate("__rows(1)") == MTIME_ASC
              and await pg.evaluate("__gets") == gets,
              "getFile() hands back the size and the mtime together")

        await pg.evaluate("setSort('name', true)")
        await pg.wait_for_timeout(300)
        check("Folders stay above files under every key, and follow the direction",
              await pg.evaluate("__rows(1)") == NAME_DESC,
              "no port can give a directory a size or an mtime")

        await pg.evaluate("setSort('name', false)")
        await pg.click("#gear")
        await pg.click("#s-sort-size")
        await pg.wait_for_timeout(400)
        ticked = await pg.evaluate(
            "SORT_KEYS.map(k => document.getElementById('s-sort-'+k)"
            ".getAttribute('aria-checked'))")
        check("The ⚙ menu picks the key and shows which one is active",
              await pg.evaluate("__rows(1)") == SIZE_ASC
              and ticked == ["false", "true", "false"], str(ticked))
        await pg.click("#s-sort-desc")
        await pg.wait_for_timeout(300)
        check("…and the direction is a separate switch that applies to that key",
              await pg.evaluate("__rows(1)") == SIZE_DESC
              and await pg.evaluate(
                  "document.getElementById('s-sort-desc').getAttribute('aria-checked')")
              == "true")

        # Remembered in localStorage rather than in the per-folder record: the
        # sort is how a person reads a list, not a property of the folder.
        check("The choice is remembered, so the next session opens the same way",
              await pg.evaluate("localStorage.getItem('filemill.sort')") == "size:desc",
              await pg.evaluate("localStorage.getItem('filemill.sort')"))
        await pg.evaluate("state.sort = {key:'name', desc:false}; loadSort()")
        check("…and a reload reads it back",
              await pg.evaluate("JSON.stringify(state.sort)")
              == '{"key":"size","desc":true}',
              await pg.evaluate("JSON.stringify(state.sort)"))

        # The cursor is a row *index*, and a re-sort moves the row it named.
        # small.txt sits at row 2 ascending and row 4 descending, so a cursor
        # left behind would put ↓ on medium.md instead of locked.txt.
        await in_sorting()
        await pg.evaluate("setSort('size', false)")
        await pg.wait_for_timeout(400)
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_timeout(250)
        await pg.click('.col[data-i="1"] .row:has-text("small.txt")')
        await pg.wait_for_timeout(250)
        await pg.evaluate("setSort('size', true)")
        await pg.wait_for_timeout(400)
        await pg.keyboard.press("ArrowDown")
        await pg.wait_for_timeout(250)
        check("↓ after a re-sort steps off the row that is still selected, not "
              "off the row number it used to have",
              await pg.evaluate("sel[1]") == "locked.txt",
              await pg.evaluate("sel[1]"))

        # A refresh lands while the sweep is still reading. Those metadata reads
        # are about objects the new listing no longer contains, so the sweep
        # must not mark the new one done — and the app has to notice and ask
        # again rather than sit on a half-ordered column.
        await pg.evaluate("setSort('name', false)")
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("refresh")')
        await pg.wait_for_timeout(300)
        await pg.evaluate("__slowMeta(400)")
        await pg.evaluate("setSort('size', false)")
        await pg.wait_for_timeout(120)                  # the sweep is in flight
        await pg.evaluate("__add(__live, 'zero.txt')")  # 8 bytes; one/two are 1
        await pg.evaluate("refreshColumn(1)")
        await pg.wait_for_timeout(2500)
        rows = await pg.evaluate("__rows(1)")
        check("A refresh during a sweep re-reads and sweeps again, rather than "
              "trusting metadata about entries that are gone",
              rows == ["sub", "one.txt", "two.txt", "zero.txt"]
              and await pg.evaluate("path[1].metaDone") is True
              and await pg.eval_on_selector_all(".col.sorting", "e=>e.length") == 0,
              str(rows))
        await pg.evaluate("__slowMeta(0)")

        # A sweep is the one thing here that can take a visible moment, so the
        # column has to say it is working rather than sit there in name order.
        # 2 s per read, not 400 ms: three Playwright round-trips have to land
        # inside the window, and on a loaded machine each of those can take
        # hundreds of milliseconds. A window this wide fails only if the
        # spinner is genuinely absent.
        await in_sorting()
        await pg.evaluate("__slowMeta(2000)")
        await pg.evaluate("setSort('size', false)")
        await pg.wait_for_timeout(150)
        spinning = await pg.eval_on_selector_all(".col.sorting", "e=>e.length")
        say = (await pg.inner_text("#st-sort")).strip()
        # 5 files, which is exactly the getFile() count the check above pinned:
        # the strip counts calls outstanding, not entries in view.
        check("A column still reading its metadata says so, rather than freezing",
              spinning > 0 and "reading 5 files" in say,
              f"{spinning} columns spinning, strip says {say!r}")
        await pg.wait_for_function("!path.some(n => n.metaLoading)", timeout=30_000)
        await pg.wait_for_timeout(300)
        say = (await pg.inner_text("#st-sort")).strip()
        check("…and when the sweep lands the strip names the folder and what it "
              "cost to read",
              "size" in say and "sorting: 4 files read in" in say
              and await pg.eval_on_selector_all(".col.sorting", "e=>e.length") == 0,
              say)

        # The race the design has to survive: the sweep is slow, and the user
        # walks off before it lands.
        await in_sorting()
        await pg.evaluate("__slowMeta(500)")
        await pg.evaluate("setSort('size', false)")
        await pg.wait_for_timeout(120)                  # the sweep is in flight
        await pg.click('.col[data-i="0"] .row:has-text("mixed")')
        await pg.wait_for_timeout(1500)                 # long enough for it to land
        st = await pg.evaluate("__state()")
        coherent = all(st["sel"][i] == st["path"][i + 1]
                       for i in range(len(st["path"]) - 1))
        check("A sweep that lands after the user walked off does not repaint the "
              "column it no longer describes",
              st["path"] == ["workspace", "mixed"] and st["sel"] == ["mixed"]
              and coherent, json.dumps(st))

        await pg.evaluate("__slowMeta(0)")
        gets = await pg.evaluate("__gets")
        await pg.click('.col[data-i="0"] .row:has-text("sorting")')
        await pg.wait_for_timeout(500)
        again = await pg.evaluate("__gets") - gets
        check("…but what it read is kept, so stepping back in shows the sorted "
              "column and asks for nothing",
              await pg.evaluate("__rows(1)") == SIZE_ASC and again == 0,
              f"{again} further getFile() calls")

        # A port that rejects instead of recording the error would otherwise
        # leave metaLoading set for good, and the column would spin until the
        # tab closed.
        await in_sorting()
        await pg.evaluate("__brokenMeta()")
        await pg.evaluate("setSort('size', false)")
        await pg.wait_for_timeout(700)
        rows = await pg.evaluate("__rows(1)")
        check("A port that rejects every read finishes the sweep instead of "
              "spinning for ever, and keeps every row",
              await pg.eval_on_selector_all(".col.sorting", "e=>e.length") == 0
              and sorted(rows) == sorted(NAME_ASC)
              and await pg.evaluate("path[1].metaDone") is True,
              f"{len(rows)} rows, metaDone {await pg.evaluate('path[1].metaDone')}")
        await pg.evaluate("__slowMeta(0); setSort('name', false)")

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

            # The sweep a size or date sort has to finish before it can place
            # the first row. Against a fake handle getFile() returns without
            # touching a disk, so this is the app's own share of the cost — the
            # fan-out, the sort and the rebuild — and it is the part a
            # regression here would show up in. The syscall itself is measured
            # against a real filesystem in test-url.py, where it dominates.
            # Like refresh, this is a price paid once, when the user asks, and
            # the assertion is on the arrow key measured *after* it.
            sweep = await pg.evaluate("__sweepbench()")
            await pg.evaluate("setSort('size', false)")
            await pg.wait_for_timeout(300)
            swept_key = await pg.evaluate("__keybench(20)")
            # Two assertions, because a stopwatch alone cannot carry this one.
            #
            # `arrow` is the same key, same column, earlier in this same run.
            # A fixed ceiling would decide by machine load rather than by code:
            # an arrow key at 3 000 entries came in between 11.5 ms and 89.9 ms
            # over 12 runs here and 106 ms on a slower machine, against a 100 ms
            # budget. Sorting by size does not move it — a probe alternating the
            # keys on one column measured 19.4–40.4 ms by size against
            # 16.4–45.8 ms by name, less spread than either has on its own.
            #
            # But `arrow + budget` is loose enough to hide a re-sort per
            # keystroke, which costs 18–90 ms at this size. So the second
            # assertion is exact and has no clock in it: after 20 presses the
            # focused column must still be the *same cached entry*. Rebuilding
            # it per keystroke is the O(entries) regression the column cache
            # exists to prevent, and `metaDone` is a new way to trip it.
            # Verified by injecting exactly that (a buildCol whose metaRef never
            # matches): the keystroke went to 639.5 ms against a 109 ms
            # threshold, and the identity check went false.
            kept = await pg.evaluate(
                "(() => { const c = colCache.get(path[focusCol]);"
                " for (let i = 0; i < 20; i++)"
                "   document.dispatchEvent(new KeyboardEvent('keydown', {key:'ArrowDown'}));"
                " return colCache.get(path[focusCol]) === c; })()")
            check(f"{n:,} entries: a size sort sweeps the directory in "
                  f"{sweep['ms']} ms of app time ({sweep['reads']} getFile() "
                  f"calls); the keystroke after it costs {swept_key} ms against "
                  f"{arrow} ms for the same key before it, and rebuilds nothing",
                  swept_key < arrow + budget and kept and sweep["reads"] == n
                  and sweep["rows"] == n,
                  f"{sweep['reads']} reads for {sweep['rows']} rows, "
                  f"column {'kept' if kept else 'REBUILT'}")
            await pg.evaluate("setSort('name', false)")

        check("No console errors anywhere", not errs, "; ".join(errs[:3]))
        await b.close()

    print(f"\n{'═' * 62}\n  {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("  Failed: " + ", ".join(failed))
    print("═" * 62)
    sys.exit(1 if failed else 0)


asyncio.run(main())
