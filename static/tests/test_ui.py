"""UI sections with a fake directory handle and no folder picker."""

import json

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# The fixture's source file as Python sees it: __mk builds a.py from this
# string and long.py from 300 copies of it.
PY_SRC = 'def f():\n    # doc\n    return "s" + 42\n    # ' + "x" * 82 + "\n"

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
  const IMAGE = (name, type) => { let f = null; return {kind:'file', name,
    getFile: async () => { window.__gets++;
      if (!f) {
        const c = document.createElement('canvas'); c.width = c.height = 1;
        const bytes = Uint8Array.from(atob(c.toDataURL(type).split(',')[1]),
                                      x => x.charCodeAt(0));
        const padded = new Uint8Array(512 * 1024 + 1); padded.set(bytes);
        f = new File([padded], name, {type});
      }
      return f;
    }}; };
  /* A file the port cannot stat: the permission case, which still has to sort
     somewhere and must never be dropped from the listing. */
  const FX = (name) => ({kind:'file', name,
    getFile: async () => { window.__gets++;
      throw Object.assign(new Error('no'), {name:'NotAllowedError'}); }});
  const D = (name, kids) => ({kind:'directory', name,
    requestPermission: async () => 'granted',
    removeEntry: async (name, {recursive}) => {
      const i = kids.findIndex(k => k.name === name);
      if (i < 0) throw new Error('Entry not found');
      if (kids[i].kind === 'directory' && !recursive) throw new Error('Directory');
      window.removals?.push({name, recursive});
      kids.splice(i, 1);
    },
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  /* Long names must not affect the fixed column width. */
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
    D('deep',  [D('alpha',[D('beta',[D('gamma',[F('leaf.txt','leaf\n' + 'scrollable line\n'.repeat(200))])])])]),
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
                F('nested.json', '{"name":"x","tags":["a","b"],"items":[{"id":1,"name":"first"}],"meta":{"n":1,"ok":true,"none":null}}'),
                F('bad.json', '{oops'),
                F('deep.json', '['.repeat(200000) + ']'.repeat(200000)),
                // Taller than any preview pane, so the pane has to say where a
                // long text scrolls: the column itself, not a box inside it.
                F('long.txt', 'a line of plain text\n'.repeat(400)),
                F('page.html','<h1>Hi</h1>'), F('doc.pdf','%PDF-1.4'),
                IMAGE('large.png', 'image/png'),
                IMAGE('large.jpeg', 'image/jpeg')]),
    D('empty', []),
    DENIED('locked'),
    SLOW('slow', [F('one.txt','1'), F('two.txt','2')]),
    D('big', big),
    // The chain inside holds names at measure()'s width ceiling, which is the
    // case the fold cap cannot answer alone: on a phone the column under the
    // finger is then wider than the stage has left once its ancestors have
    // folded to spines, and #stage clips what runs past the right edge.
    D('wide', [F('a-quite-long-file-name-1.txt'), F('a-quite-long-file-name-2.txt'),
               D(LONG(0), [D(LONG(1), [D(LONG(2), [D(LONG(3), [D(LONG(4), [F('leaf.txt', 'leaf')])])])])])]),
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
    // repeat the id has to carry the column; a bad line must land on the
    // denied note, not a broken column; a large file is browsed by line.
    D('tables', [
      F('log.jsonl', '{"id":2,"title":"Second","ts":"2026-01-02","tags":["a",{"ok":true}]}\n'
                   + '{"id":1,"title":"First","ts":"2026-01-01","tags":["a"]}\n'
                   + '{"id":3,"title":"Third","ts":"2026-01-03","tags":null}\n'),
      F('dup.jsonl', '{"id":10,"title":"Same"}\n{"id":11,"title":"Same"}\n'),
      F('bad.jsonl', '{"a":1}\nnope\n'),
      // past the 512 KB text ceiling, with one bad line: browsed by line index
      F('huge.jsonl', Array.from({length: 20000}, (_, i) =>
        i === 6 ? 'nope' : `{"id":${i + 1},"title":"Row ${i + 1}"}`).join('\n') + '\n'),
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
   The syscall the real port makes is measured in tests/test_url.py, against a real
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
/* Real structured-cloneable handles exercise storage across module boundaries. */
window.__remember = async (chain) => {
  const fs = await navigator.storage.getDirectory();
  const root = await fs.getDirectoryHandle('workspace', {create:true});
  const mixed = await root.getDirectoryHandle('mixed', {create:true});
  const sub = await mixed.getDirectoryHandle('sub', {create:true});
  await sub.getFileHandle('a.py', {create:true});
  await mixed.getFileHandle('note.md', {create:true});
  const deep = await root.getDirectoryHandle('deep', {create:true});
  await deep.getDirectoryHandle('alpha', {create:true});
  window.__storedRoot = root;
  await __seed([{handle:root, path:chain}]);
};
/* Observe real writes without replacing the storage module's bindings. */
window.__spySaves = async () => {
  await __seed([]);
  window.__saved = [];
  const put = IDBObjectStore.prototype.put;
  IDBObjectStore.prototype.put = function(value, key) {
    if (key === 'recent') __saved.push([value[0].handle.name, value[0].path]);
    return put.call(this, value, key);
  };
  window.__restoreSaves = () => { IDBObjectStore.prototype.put = put; };
};
/* Playwright invokes a function-valued evaluation result. End on a string. */
"fake handle ready";
"""


async def mount(pg, n=0):
    await pg.evaluate(f"mount(__mk({n}))")
    await pg.wait_for_function("path.length===1 && colCache.get(path[0])")
    await pg.wait_for_function(
        "document.querySelector('.col .row') && !document.querySelector('.spinner')"
    )
    await scroll_settled(pg)


SCROLL_SETTLED = """() => {
  const value = JSON.stringify([dial(), finder.scrollLeft,
    finder.scrollWidth, finder.clientWidth, folded]);
  const now = performance.now();
  if (value !== window.__scrollProbe.value) {
    window.__scrollProbe = {value, since: now};
  }
  return now - window.__scrollProbe.since >= 300;
}"""


async def scroll_settled(pg):
    """Wait for smooth scrolling and the dial range rebase to settle."""
    await pg.evaluate("window.__scrollProbe = {value: null, since: 0}")
    await pg.wait_for_function(SCROLL_SETTLED, timeout=6000)
    return True


def sync_scroll_settled(page):
    page.evaluate("window.__scrollProbe = {value: null, since: 0}")
    page.wait_for_function(SCROLL_SETTLED, timeout=6000)


async def editor_feature_checks(pg):
    await pg.click("#pv-edit")
    await pg.wait_for_selector("#pv-editor")
    original = await pg.input_value("#pv-editor")
    assert await pg.is_hidden("#pv-modified")
    await pg.fill("#pv-editor", "alpha\nbeta alpha\n")
    assert await pg.is_visible("#pv-modified")
    assert await pg.inner_text("#pv-gutter") == "1\n2\n3"
    await pg.press("#pv-editor", "Control+z")
    assert await pg.input_value("#pv-editor") == original
    assert await pg.is_hidden("#pv-modified")
    await pg.press("#pv-editor", "Control+Shift+z")
    assert await pg.input_value("#pv-editor") == "alpha\nbeta alpha\n"
    assert await pg.is_visible("#pv-modified")
    await pg.press("#pv-editor", "Control+f")
    await pg.fill('input[aria-label="Find in file"]', "alpha")
    for start in (0, 11, 0):
        await pg.keyboard.press("Enter")
        assert await pg.eval_on_selector("#pv-editor", "e => e.selectionStart") == start
    await pg.fill('input[aria-label="Find in file"]', "absent")
    await pg.press('input[aria-label="Find in file"]', "Enter")
    assert await pg.inner_text(".pv-find output") == "No matches"
    await pg.fill('input[aria-label="Find in file"]', "")
    await pg.press('input[aria-label="Find in file"]', "Enter")
    assert await pg.inner_text(".pv-find output") == ""
    await pg.press('input[aria-label="Find in file"]', "Escape")
    assert await pg.is_hidden(".pv-find")
    assert await pg.evaluate("document.activeElement.id") == "pv-editor"
    assert await pg.input_value("#pv-editor") == "alpha\nbeta alpha\n"
    await pg.fill("#pv-editor", "needle" + "x" * 500 + "needle")
    await pg.eval_on_selector(
        "#pv-editor", "e => { e.setSelectionRange(0, 0); e.scrollLeft = 0; }"
    )
    await pg.press("#pv-editor", "Control+f")
    search = pg.locator('input[aria-label="Find in file"]')
    await search.fill("needle")
    assert await search.evaluate("""e => e.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Enter', bubbles: true, cancelable: true, isComposing: true
    }))""")
    assert await search.evaluate("e => document.activeElement === e")
    await search.press("Enter")
    await pg.keyboard.press("Enter")
    assert await pg.eval_on_selector("#pv-editor", "e => e.selectionStart") == 506
    assert await pg.eval_on_selector("#pv-editor", "e => e.scrollLeft > 0")
    await pg.keyboard.press("Enter")
    assert await pg.eval_on_selector("#pv-editor", "e => e.scrollLeft") == 0
    await pg.keyboard.press("Escape")
    await pg.press("#pv-editor", "Control+z")
    assert await pg.input_value("#pv-editor") == "alpha\nbeta alpha\n"
    await pg.evaluate(
        "window.__editorBeforeResize = document.querySelector('#pv-editor')"
    )
    await pg.set_viewport_size({"width": 1100, "height": 700})
    await pg.wait_for_function("finder.clientWidth < 1200")
    assert await pg.evaluate(
        "document.querySelector('#pv-editor') === __editorBeforeResize"
    )
    assert await pg.is_visible("#pv-modified")
    await pg.press("#pv-editor", "Control+z")
    assert await pg.input_value("#pv-editor") == original
    assert await pg.is_hidden("#pv-modified")
    # A new edit after undo discards the old redo branch.
    await pg.fill("#pv-editor", "new branch")
    await pg.press("#pv-editor", "Control+Shift+z")
    assert await pg.input_value("#pv-editor") == "new branch"
    await pg.fill("#pv-editor", "")
    assert await pg.inner_text("#pv-gutter") == "1"
    await pg.fill("#pv-editor", "line\n" * 100)
    await pg.eval_on_selector("#pv-editor", "e => { e.scrollTop = e.scrollHeight; }")
    await pg.wait_for_function("""() => {
      const ta = document.querySelector('#pv-editor');
      return document.querySelector('#pv-gutter').style.transform === `translateY(${-ta.scrollTop}px)`;
    }""")
    assert (await pg.inner_text("#pv-gutter")).splitlines()[-1] == "101"
    # A failed port write leaves the editable text and modified mark intact.
    await pg.evaluate("""() => {
      window.__editorWrite = FS.write;
      FS.write = async () => { throw new Error('test write denied'); };
    }""")
    await pg.click("#pv-save")
    await pg.wait_for_function(
        "document.querySelector('#pv-edit-err').textContent === 'test write denied'"
    )
    assert await pg.is_visible("#pv-modified")
    assert not await pg.eval_on_selector("#pv-editor", "e => e.readOnly")
    await pg.evaluate("() => { FS.write = window.__editorWrite; }")
    await pg.fill("#pv-editor", original)
    assert await pg.is_hidden("#pv-modified")
    await pg.click("#pv-cancel")
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.is_hidden("#pv-modified")
    await pg.set_viewport_size({"width": 1500, "height": 900})


async def click_row(pg, column, name):
    await scroll_settled(pg)
    spine = pg.locator(f'.col[data-i="{column}"].spine')
    if await spine.count():
        await spine.click()
        await scroll_settled(pg)
    await pg.click(f'.col[data-i="{column}"] .row[title="{name}"]')


def test_markdown_source_tokens(bundle, playwright):
    source = (
        "# Heading [link](next.md)\n\nSetext\n======\n\n"
        "It's prose, and here's another apostrophe.\n"
        "https://example.org/path?q=1&x=2.\n"
        "[reference][target]\n[target]: next.md\n"
        "`[code](hidden.md)`\n\n```md\n[code](hidden.md)\n```\n"
        "<img src=x onerror=alert(1)>\n"
    )
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof renderNode === 'function'")
        page.evaluate(
            """async text => {
          const host = document.createElement('div');
          host.id = 'markdown-test';
          host.innerHTML = await renderNode({name: 'test.md'}, new Blob([text]), 'text');
          document.body.append(host);
        }""",
            source,
        )
        host = page.locator("#markdown-test")
        assert host.text_content() == source
        assert host.locator(".hl-heading").count() == 2
        assert host.locator(".hl-str").all_text_contents() == [
            "`[code](hidden.md)`",
            "```md\n[code](hidden.md)\n```\n",
        ]
        assert host.locator("a").evaluate_all(
            "es => es.map(e => e.getAttribute('href'))"
        ) == ["next.md", "https://example.org/path?q=1&x=2", "next.md"]
        assert host.locator("img").count() == 0
    finally:
        browser.close()


def test_markdown_source_link_boundaries(bundle, playwright):
    cases = [
        (
            "paragraph code",
            "`open\n\n[visible](next.md)\n\nclose`",
            ["/notes/next.md?filemill=render"],
        ),
        (
            "paragraph label",
            "[broken\n\nlabel](hidden.txt)\n\n[visible](next.md)",
            ["/notes/next.md?filemill=render"],
        ),
        (
            "code in label",
            "[caption `]` text](next.md)",
            ["/notes/next.md?filemill=render"],
        ),
        (
            "uppercase URLs",
            "HTTPS://example.org/page WWW.example.org",
            ["HTTPS://example.org/page", "http://WWW.example.org"],
        ),
        (
            "autolinks",
            "<person@example.org> <ftp://example.org/file>",
            ["mailto:person@example.org", "ftp://example.org/file"],
        ),
        ("empty destination", "[empty]()", [""]),
        (
            "angle destination",
            "[angle]( <file(name.md> )",
            ["/notes/file(name.md?filemill=render"],
        ),
        (
            "escaped title",
            r"[title](next.md 'don\'t')",
            ["/notes/next.md?filemill=render"],
        ),
        ("multiline code", "`code\n[not a link](hidden.txt)`", []),
    ]
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof renderNode === 'function'")
        failures = []
        for label, source, expected in cases:
            actual = page.evaluate(
                """async text => {
              const host = document.createElement('div');
              host.innerHTML = await renderNode(
                {name: 'test.md', rel: 'notes/test.md'}, new Blob([text]), 'text');
              return {text: host.textContent,
                links: [...host.querySelectorAll('a')].map(a => a.getAttribute('href'))};
            }""",
                source,
            )
            if actual != {"text": source, "links": expected}:
                failures.append({"case": label, "actual": actual, "expected": expected})
        assert failures == [], json.dumps(failures, indent=2)
    finally:
        browser.close()


async def test_storage(bundle, async_playwright, static_origin, tmp_path):
    playwright, profile = async_playwright, tmp_path
    async with playwright.async_playwright() as p:
        # Chromium 153 (Playwright 1.63) aborts the whole browser when an
        # off-the-record context reads a stored FileSystemHandle back from
        # IndexedDB, and launch() + new_page() is off-the-record. A persistent
        # profile reads it back fine.
        b = await p.chromium.launch_persistent_context(
            profile, viewport={"width": 1500, "height": 900}
        )
        print("\n── Remember view state per folder ───────────────────────────")
        # OPFS requires an HTTP origin.
        pg = await b.new_page()
        await pg.goto(f"{static_origin}/static/{bundle.name}")
        await pg.evaluate(FAKE)
        # Exercise migration with plain records, then restoration and debounced
        # writes with real OPFS handles that survive IndexedDB cloning.
        await pg.evaluate("__seed([{kind:'directory', name:'legacy'}])")
        got = await pg.evaluate("recallRoots()")
        assert got == [
            {"handle": {"kind": "directory", "name": "legacy"}, "path": []}
        ], str(got)
        await pg.evaluate(
            "__seed([{handle:{kind:'directory',name:'w'}, path:['mixed','sub']}])"
        )
        got = await pg.evaluate("recallRoots()")
        assert len(got) == 1 and got[0]["path"] == ["mixed", "sub"], str(got)

        await pg.evaluate("__remember([])")
        assert await pg.evaluate("recallView(__storedRoot)") is None, (
            "A folder last left on its own root asks for no restore"
        )

        await pg.evaluate("__remember(['mixed','sub','a.py'])")
        await pg.evaluate("mount(__storedRoot)")
        await pg.wait_for_function("sel[2] === 'a.py' && path.length === 3")
        st = await pg.evaluate("__state()")
        assert st["path"] == ["workspace", "mixed", "sub"] and st["sel"] == [
            "mixed",
            "sub",
            "a.py",
        ], json.dumps(st)

        # The case that matters: the folder is still there, the chain is not.
        await pg.evaluate("__remember(['mixed','gone','x.py'])")
        await pg.evaluate("mount(__storedRoot)")
        await pg.wait_for_function("path.length === 2 && sel.length === 1")
        st = await pg.evaluate("__state()")
        assert st["path"] == ["workspace", "mixed"] and st["sel"] == ["mixed"], (
            json.dumps(st)
        )
        assert len(st["sel"]) == 1 and st["focusCol"] == 0, json.dumps(st)

        await pg.evaluate("__remember(['mixed','sub'])")
        await pg.evaluate("pendingLoc = {root:'workspace', path:['deep','alpha']}")
        await pg.evaluate("mount(__storedRoot)")
        await pg.wait_for_function("path[2]?.name === 'alpha'")
        st = await pg.evaluate("__state()")
        assert st["path"] == ["workspace", "deep", "alpha"], json.dumps(st)

        # The write side. Walking a column is one location change per keystroke,
        # so the saves are debounced — a write per keystroke would be the
        # per-entry cost this app spent a rewrite deleting, in another costume.
        await pg.evaluate("__spySaves()")
        await pg.evaluate("mount(__storedRoot)")
        await pg.wait_for_function("!document.querySelector('.spinner')")
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
        await pg.wait_for_function("__saved.length === 1")
        saved = await pg.evaluate("__saved")
        assert start_saves == 0, f"{start_saves} writes during mount"
        assert early == 0 and len(saved) == 1, f"{early} early, {len(saved)} total"
        assert saved == [["workspace", ["mixed", "note.md"]]], str(saved)

        await pg.evaluate("__restoreSaves(); __seed([])")
        await b.close()


def test_context_menu_delete_fsa(bundle, fake_handle, playwright):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page(viewport={"width": 1500, "height": 900})
        page.goto(bundle.as_uri())
        page.evaluate("localStorage.setItem('filemill.rich','off')")
        page.evaluate(fake_handle)
        page.evaluate("""async () => {
          window.localRoot = __mk(0);
          await mount(localRoot);
          window.removals = [];
        }""")
        row = page.locator('.col[data-i="0"] .row[aria-label="mixed"]')
        row.click()
        page.wait_for_function("path.length === 2")
        # Native handles have no parent property. The adapter owns the parent link.
        assert page.evaluate("!path[1].handle.parent && path[1].parent === localRoot")
        page.evaluate("localRoot.requestPermission = async () => 'denied'")
        row.click(button="right")
        page.once("dialog", lambda d: d.accept())
        page.get_by_role("menuitem", name="Delete", exact=True).click()
        page.wait_for_function(
            "document.querySelector('#st-refresh').textContent.includes('No permission to delete')"
        )
        assert page.evaluate("window.removals.length") == 0
        page.evaluate("localRoot.requestPermission = async () => 'granted'")
        row.click(button="right")
        page.once("dialog", lambda d: d.accept())
        page.get_by_role("menuitem", name="Delete", exact=True).click()
        row.wait_for(state="detached")
        assert page.evaluate("window.removals") == [
            {"name": "mixed", "recursive": True}
        ]
        page.wait_for_function("path.length === 1")
        page.locator('.col[data-i="0"] .row[aria-label="refresh"]').click()
        file = page.locator('.col[data-i="1"] .row[aria-label="one.txt"]')
        file.click()
        page.once("dialog", lambda d: d.accept())
        page.locator("#pv-delete").click()
        file.wait_for(state="detached")
        assert page.evaluate("window.removals[1]") == {
            "name": "one.txt",
            "recursive": False,
        }
        page.wait_for_function(
            "document.querySelector('#st-refresh').textContent === 'Deleted “one.txt”'"
        )
        assert "bad" not in (page.locator("#st-refresh").get_attribute("class") or "")
        assert page.evaluate("sel[1] === undefined && focusCol === 1")
        page.keyboard.press("ArrowDown")
        page.wait_for_function("sel[1] === 'sub'")
        page.evaluate("""() => {
          const remove = FS.remove;
          FS.remove = node => new Promise(resolve => {
            window.finishDelete = async () => { await remove(node); resolve(); };
          });
        }""")
        second = page.locator('.col[data-i="1"] .row[aria-label="two.txt"]')
        second.click(button="right")
        page.once("dialog", lambda d: d.accept())
        page.get_by_role("menuitem", name="Delete", exact=True).click()
        page.wait_for_function("typeof window.finishDelete === 'function'")
        page.evaluate("refreshColumn(0)")
        second.click(button="right")
        assert page.get_by_role("menuitem", name="Delete", exact=True).is_disabled()
        page.keyboard.press("Escape")
        page.evaluate("window.finishDelete()")
        second.wait_for(state="detached")
        assert page.evaluate("window.removals[2]") == {
            "name": "two.txt",
            "recursive": False,
        }
        page.evaluate("FS.remove = undefined")
        page.locator('.col[data-i="1"] .row[aria-label="sub"]').click(button="right")
        page.locator("#row-menu").wait_for(state="visible")
        assert page.get_by_role("menuitem", name="Delete", exact=True).count() == 0
    finally:
        browser.close()


def test_delete_fsa_uses_parent_directory(bundle, fake_handle, playwright):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.evaluate(fake_handle)
        result = page.evaluate("""async () => {
          const handle = __mk(0);
          const root = FSA.node(handle.name, handle);
          await FSA.ensureLoaded(root);
          const child = root.kids.find(n => n.name === 'mixed');
          window.removals = [];
          try { await FSA.remove(child); }
          catch (error) { return error.message; }
          return window.removals;
        }""")
        assert result == [{"name": "mixed", "recursive": True}]
    finally:
        browser.close()


def test_mobile_fullscreen_back(bundle, fake_handle, playwright, static_origin):
    browser = playwright.chromium.launch()
    try:
        page = browser.new_page(
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        page.goto(f"{static_origin}/static/{bundle.name}")
        page.evaluate(fake_handle)
        page.evaluate(
            "async () => { await mount(__mk(0)); await applyPath(['mixed', 'short.txt']); }"
        )
        page.wait_for_selector("#pv-content .pv-text")
        page.evaluate("document.documentElement.requestFullscreen = undefined")
        url = page.url
        page.evaluate("window.savedPreview = document.querySelector('#pv-content')")
        full = page.locator("#pv-fullscreen")
        full.click()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        page.go_back()
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen')"
        )
        assert page.url == url
        assert page.evaluate("sel.at(-1)") == "short.txt"
        assert page.evaluate("savedPreview === document.querySelector('#pv-content')")
        assert page.locator("#bar").is_visible()
        page.go_forward()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        full.click()
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen') && !history.state?.filemillFullscreen"
        )
        assert page.url == url
        page.go_forward()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        page.go_back()
        page.wait_for_function("!history.state?.filemillFullscreen")
        page.go_back()
        page.wait_for_function("path.length === 1")
        assert page.locator("#bar").is_visible()
        page.go_forward()
        page.wait_for_function("sel.at(-1) === 'short.txt'")
        page.go_forward()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
    finally:
        browser.close()


def test_preview_arrow_sequence(bundle, fake_handle, playwright, static_origin):
    browser = playwright.chromium.launch()
    try:
        page = browser.new_page(viewport={"width": 1500, "height": 900}, has_touch=True)
        page.goto(f"{static_origin}/static/{bundle.name}")
        page.evaluate(fake_handle)
        page.evaluate(
            "async () => { await mount(__mk(0)); await applyPath(['mixed', 'short.txt']); }"
        )
        page.wait_for_selector("#pv-content .pv-text")
        page.evaluate("document.documentElement.requestFullscreen = undefined")
        page.evaluate("dialTo(0)")
        page.wait_for_function("folded === 0")
        page.locator("#preview").focus()
        url = page.url
        for count in (1, 2):
            page.keyboard.press("ArrowRight")
            page.wait_for_function(
                "n => document.querySelectorAll('.col.spine').length === n",
                arg=count,
                timeout=3000,
            )
        page.keyboard.press("ArrowRight")
        page.wait_for_function("Math.abs(dial() - range()) <= 1")
        assert not page.evaluate(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        page.keyboard.press("ArrowRight")
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen') && history.state?.filemillFullscreen"
        )
        page.keyboard.press("ArrowLeft")
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen') && !history.state?.filemillFullscreen"
        )
        assert page.evaluate("document.activeElement.id") == "preview"
        assert page.url == url
        assert page.evaluate("sel.at(-1)") == "short.txt"
        page.go_forward()
        page.wait_for_function(
            "document.documentElement.classList.contains('pv-fullscreen')"
        )
        page.keyboard.press("Escape")
        page.wait_for_function(
            "!document.documentElement.classList.contains('pv-fullscreen') && !history.state?.filemillFullscreen"
        )
        assert page.url == url
    finally:
        browser.close()


# iOS Safari sends a tap as a hover first. If that hover makes hidden content
# visible, Safari keeps the hover and drops the click, so the user must tap
# again. A folder opens its column unfocused, so its rows meet this on the
# first tap. On a touch-only screen, hover must reveal nothing.
def test_touch_tap_opens_folder_first_time(
    bundle, fake_handle, playwright, static_origin
):
    browser = playwright.chromium.launch()
    try:
        page = browser.new_page(
            viewport={"width": 1024, "height": 768}, is_mobile=True, has_touch=True
        )
        page.goto(f"{static_origin}/static/{bundle.name}")
        page.evaluate("localStorage.setItem('filemill.rich','off')")
        page.evaluate(fake_handle)
        page.evaluate("async () => { await mount(__mk(0)); }")
        assert page.evaluate("matchMedia('(hover: none)').matches")
        shown = """i => [...document.querySelectorAll(`.col[data-i="${i}"] *`)]
          .filter(e => getComputedStyle(e).visibility === 'visible').length"""
        for depth, name in enumerate(["deep", "alpha", "beta"]):
            sync_scroll_settled(page)
            row = page.locator(f'.col[data-i="{depth}"] .row[aria-label="{name}"]')
            row.wait_for()
            before = page.evaluate(shown, depth)
            row.hover()
            assert page.evaluate(shown, depth) == before, (
                f"hover on {name} reveals content"
            )
            sync_scroll_settled(page)
            row.tap()
            page.wait_for_function(
                "n => path.length === n", arg=depth + 2, timeout=3000
            )
            assert page.evaluate(f"sel[{depth}]") == name
        # A long press opens the menu and leaves the folder closed.
        sync_scroll_settled(page)
        box = page.locator('.col[data-i="3"] .row[aria-label="gamma"]').bounding_box()
        point = [{"x": box["x"] + 20, "y": box["y"] + box["height"] / 2}]
        cdp = page.context.new_cdp_session(page)
        cdp.send(
            "Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": point}
        )
        page.locator("#row-menu").wait_for(state="visible", timeout=3000)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_function("document.querySelector('#row-menu')?.checkVisibility()")
        assert page.locator("#row-menu").is_visible()
        assert page.evaluate("path.length") == 4
        assert page.evaluate("sel[3]") is None
    finally:
        browser.close()


@pytest.fixture
def copy_page(bundle, fake_handle, playwright, request):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    touch = getattr(request.node, "callspec", None)
    touch = bool(touch and touch.params.get("width") == 390)
    page = browser.new_page(viewport={"width": 1000, "height": 700}, has_touch=touch)
    page.goto(bundle.as_uri())
    page.evaluate("localStorage.setItem('filemill.rich','off')")
    page.evaluate(fake_handle)
    page.evaluate("async () => { await mount(__mk(0)); __clip(false); }")
    page.locator('.col[data-i="0"] .row[title="mixed"]').click()
    page.locator('.col[data-i="1"] .row[title="note.md"]').click()
    # The preview's late render rewrites the status path and drops a fallback
    # selection made before it; CI once read that selection empty.
    page.wait_for_selector("#preview .pv-text")
    # pause_at installs the clock itself, avoiding a running interval between calls.
    page.clock.pause_at(1000000)
    try:
        yield page
    finally:
        browser.close()


def copied(page, expected, key="Control+c"):
    count = page.evaluate("__clipped.length")
    page.keyboard.press(key)
    page.wait_for_function(
        "([count, value]) => __clipped.length === count + 1 && __clipped.at(-1) === value",
        arg=[count, expected],
        timeout=3000,
    )
    assert page.locator("#st-copy").inner_text() == f"Copied {expected}"


@pytest.mark.parametrize("directory", [False, True])
def test_copy_rotation_fsa(copy_page, directory):
    page = copy_page
    relative = "mixed/note.md"
    if directory:
        page.locator('.col[data-i="1"] .row[title="docs"]').click()
        page.wait_for_function("sel[2] === 'README'")
        relative = "mixed/docs"
    for value in [relative, "/" + relative, relative.split("/")[-1], relative]:
        copied(page, value)
    page.locator("#st-path").click()
    assert page.evaluate("__clipped.at(-1)") == page.locator("#st-path").inner_text()


@pytest.mark.parametrize(
    "elapsed, expected",
    [(4999, "/mixed/note.md"), (5000, "mixed/note.md"), (5001, "mixed/note.md")],
)
def test_copy_timeout(copy_page, elapsed, expected):
    copied(copy_page, "mixed/note.md")
    copy_page.clock.run_for(elapsed)
    copied(copy_page, expected)
    copy_page.clock.run_for(4999)
    copied(copy_page, "note.md" if elapsed < 5000 else "/mixed/note.md")


@pytest.mark.parametrize(
    "interaction",
    [
        "key",
        "pointer",
        "wheel",
        "blur",
        "input",
        "preview",
        "selection",
        "root",
        "stopped-input",
        "input-event",
    ],
)
def test_copy_interaction_reset(copy_page, interaction):
    page = copy_page
    copied(page, "mixed/note.md")
    if interaction == "key":
        page.keyboard.press("Escape")
    elif interaction == "pointer":
        page.locator("#status").click(position={"x": 1, "y": 1})
    elif interaction == "wheel":
        page.mouse.wheel(0, 20)
    elif interaction == "blur":
        page.evaluate("window.dispatchEvent(new Event('blur'))")
    elif interaction == "input-event":
        page.evaluate(
            "document.body.dispatchEvent(new Event('input', {bubbles: true}))"
        )
    elif interaction in ("input", "preview", "stopped-input"):
        page.evaluate(
            """kind => {
          const el = kind !== 'preview' ? document.body.appendChild(document.createElement('input')) : document.querySelector('#preview');
          if (kind === 'stopped-input') el.addEventListener('keydown', e => e.stopPropagation());
          el.dispatchEvent(new KeyboardEvent('keydown', {key: 'x', bubbles: true}));
        }""",
            interaction,
        )
    elif interaction == "selection":
        page.evaluate("sel[1] = 'short.txt'; render()")
    else:
        page.clock.resume()
        page.evaluate("async () => { await mount(__mk(0)); }")
        spine = page.locator('.col[data-i="0"].spine')
        if spine.count():
            spine.click()
        page.locator('.col[data-i="0"] .row[title="mixed"]').click()
        page.locator('.col[data-i="1"] .row[title="note.md"]').click()
    copied(page, "mixed/short.txt" if interaction == "selection" else "mixed/note.md")


@pytest.mark.parametrize("touch", [False, True])
def test_copy_menu_unselected_target(copy_page, touch):
    page = copy_page
    target = page.locator('.col[data-i="1"] .row[title="short.txt"]')
    if touch:
        page.evaluate("Object.defineProperty(navigator, 'maxTouchPoints', {value: 1})")
        target.dispatch_event(
            "pointerdown", {"pointerType": "touch", "clientX": 30, "clientY": 30}
        )
        page.clock.run_for(501)
    else:
        target.click(button="right")
    page.get_by_role("menuitem", name="Copy relative path", exact=True).click()
    assert page.locator("#st-copy").inner_text() == "Copied mixed/short.txt"
    assert page.evaluate("sel[1]") == "note.md"
    copied(page, "/mixed/short.txt")
    copied(page, "short.txt")
    copied(page, "mixed/short.txt")
    for label, value in [
        ("Copy name", "short.txt"),
        ("Copy absolute path", "/mixed/short.txt"),
    ]:
        target.click(button="right")
        page.get_by_role("menuitem", name=label, exact=True).click()
        assert page.locator("#st-copy").inner_text() == f"Copied {value}"
        copied(page, "mixed/note.md")


@pytest.mark.parametrize("variant", [0, 1, 2])
def test_copy_refusal_fallback(copy_page, variant):
    page = copy_page
    values = ["mixed/note.md", "/mixed/note.md", "note.md"]
    for value in values[:variant]:
        copied(page, value)
    page.locator("#gear").focus()
    page.evaluate("__clip(true)")
    page.keyboard.press("Control+c")
    page.wait_for_function(
        "document.querySelector('#st-copy').textContent.includes('refused')"
    )
    assert (
        page.get_by_label("Text to copy", exact=True).input_value() == values[variant]
    )
    page.keyboard.press("Control+c")
    assert page.evaluate("__clipped.length") == 1
    if variant == 0:
        page.get_by_role("button", name="Close", exact=True).click()
    else:
        page.keyboard.press("Escape")
    assert page.locator("#copy-dialog").is_hidden()
    assert page.locator("#gear").evaluate("el => document.activeElement === el")


def test_copy_pending_reset_and_missing_clipboard(copy_page):
    page = copy_page
    page.evaluate(
        "() => { navigator.clipboard.writeText = () => new Promise(resolve => { window.finishCopy = resolve; }); }"
    )
    page.keyboard.press("Control+c")
    page.keyboard.press("Escape")
    page.evaluate("finishCopy(); __clip(false)")
    assert not page.locator("#st-copy").inner_text()
    copied(page, "mixed/note.md", key="Meta+c")
    page.evaluate(
        "Object.defineProperty(navigator, 'clipboard', {value: undefined, configurable: true})"
    )
    page.keyboard.press("Control+c")
    page.wait_for_function(
        "document.querySelector('#st-copy').textContent.includes('refused')"
    )
    assert (
        page.get_by_label("Text to copy", exact=True).input_value() == "/mixed/note.md"
    )


def test_copy_status_truncates(copy_page):
    page = copy_page
    name = "long-" * 35 + ".txt"
    page.evaluate(
        "name => { const n = path[1].kids.find(n => n.name === 'note.md'); n.name = name; sel[1] = name; render(); }",
        name,
    )
    page.set_viewport_size({"width": 390, "height": 700})
    copied(page, "mixed/" + name)
    assert page.locator("#st-copy").evaluate(
        "el => el.clientWidth > 0 && el.scrollWidth > el.clientWidth && getComputedStyle(el).textOverflow === 'ellipsis'"
    )


def test_copy_preserves_native_text_copy(copy_page):
    page = copy_page
    copied(page, "mixed/note.md")
    page.evaluate("""() => {
      const input = document.body.appendChild(document.createElement('textarea'));
      input.id = 'native-copy-test';
      input.value = 'selected text'; input.focus(); input.select();
    }""")
    page.keyboard.press("Control+c")
    assert page.evaluate("__clipped") == ["mixed/note.md"]
    page.evaluate(
        "document.activeElement.blur(); document.querySelector('#native-copy-test').remove()"
    )
    page.evaluate("""() => {
      const range = document.createRange();
      range.selectNodeContents(document.querySelector('#st-path'));
      getSelection().removeAllRanges(); getSelection().addRange(range);
    }""")
    page.keyboard.press("Control+c")
    assert page.evaluate("__clipped") == ["mixed/note.md"]
    page.evaluate("getSelection().removeAllRanges()")
    copied(page, "mixed/note.md")


def test_copy_late_completion_does_not_replace_new_cycle(copy_page):
    page = copy_page
    page.evaluate(
        "() => { navigator.clipboard.writeText = () => new Promise(resolve => { window.finishCopy = resolve; }); }"
    )
    page.keyboard.press("Control+c")
    page.evaluate("__clip(false)")
    copied(page, "mixed/note.md")
    copied(page, "/mixed/note.md")
    page.evaluate("finishCopy()")
    assert page.locator("#st-copy").inner_text() == "Copied /mixed/note.md"
    copied(page, "note.md")


@pytest.mark.parametrize("width", [1000, 390])
@pytest.mark.parametrize(
    "label,mode",
    [("Copy name", 2), ("Copy relative path", 0), ("Copy absolute path", 1)],
)
def test_copy_menu_refusal_dialog(copy_page, width, label, mode):
    page = copy_page
    page.set_viewport_size({"width": width, "height": 700})
    absolute = "/" + "long directory/" * 100 + "short.txt"
    reason = "Clipboard permission denied. " * 100
    page.evaluate(
        "([absolute, reason]) => { path[1].kids.find(n => n.name === 'short.txt').abs = absolute; __clip(false); navigator.clipboard.writeText = async t => { __clipped.push(t); throw new DOMException(reason, 'NotAllowedError'); }; }",
        [absolute, reason],
    )
    target = page.locator('.col[data-i="1"] .row[title="short.txt"]')
    if width == 390:
        box = target.bounding_box()
        cdp = page.context.new_cdp_session(page)
        cdp.send(
            "Input.dispatchTouchEvent",
            {
                "type": "touchStart",
                "touchPoints": [
                    {"x": box["x"] + 20, "y": box["y"] + box["height"] / 2}
                ],
            },
        )
        page.clock.run_for(501)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.get_by_role("menuitem", name=label, exact=True).tap()
    else:
        target.click(button="right")
        page.get_by_role("menuitem", name=label, exact=True).click()
    dialog = page.get_by_role("dialog", name="Copy manually")
    dialog.wait_for(timeout=3000)
    assert page.locator("#row-menu").is_hidden()
    field = page.get_by_label("Text to copy", exact=True)
    value = ["mixed/short.txt", absolute, "short.txt"][mode]
    assert field.input_value() == value
    assert field.evaluate(
        "el => document.activeElement === el && el.selectionStart === 0 && el.selectionEnd === el.value.length"
    )
    assert dialog.locator("#copy-reason").inner_text() == "NotAllowedError: " + reason
    assert "Ctrl+C" in dialog.inner_text()
    assert dialog.evaluate(
        "el => { const r = el.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight && el.scrollHeight > el.clientHeight; }"
    )
    count = page.evaluate("__clipped.length")
    page.keyboard.press("Control+c")
    assert page.evaluate("__clipped.length") == count
    assert dialog.is_visible()
    assert page.evaluate("sel[1]") == "note.md"
    page.keyboard.press("Escape")
    assert not dialog.is_visible()
    assert page.evaluate("document.activeElement === document.body")


def test_copy_current_folder_after_breadcrumb(copy_page):
    page = copy_page
    page.locator("#crumbs .crumb").filter(has_text="mixed").click()
    assert page.locator("#st-path").inner_text() == "mixed"
    assert page.evaluate("sel[1] === undefined")
    for value in ["mixed", "/mixed", "mixed", "mixed"]:
        copied(page, value)


@pytest.mark.parametrize("variant", [1, 2])
@pytest.mark.parametrize("directory", [False, True])
def test_copy_status_click_after_refused_rotation(copy_page, variant, directory):
    page = copy_page
    relative = "mixed/note.md"
    if directory:
        page.locator('.col[data-i="1"] .row[title="docs"]').click()
        page.wait_for_function("sel[2] === 'README'")
        relative = "mixed/docs"
    for value in [relative, "/" + relative][:variant]:
        copied(page, value)
    page.evaluate("__clip(true)")
    page.keyboard.press("Control+c")
    page.wait_for_function(
        "document.querySelector('#st-copy').textContent.includes('refused')"
    )
    assert (
        page.get_by_label("Text to copy", exact=True).input_value()
        == ([relative, "/" + relative, relative.split("/")[-1]][variant])
    )
    page.keyboard.press("Escape")
    displayed = page.locator("#st-path").inner_text()
    page.evaluate("__clip(false)")
    page.locator("#st-path").click()
    assert page.evaluate("__clipped") == [displayed]
    copied(page, "/" + displayed)


async def test_file_kinds(page):
    pg = page
    cases = [
        ("folder", {"dir": True}, ("folder", "none", False)),
        ("data.db", {"vpath": "table"}, ("vfs", "virtual", False)),
        ("link.desktop", {}, ("link", "desktop", False)),
        ("photo.png", {}, ("file", "image", False)),
        ("photo.jpg", {}, ("file", "image", False)),
        ("photo.jpeg", {}, ("file", "image", False)),
        ("doc.pdf", {}, ("file", "pdf", False)),
        ("note.md", {}, ("file", "md", True)),
        ("captions.vtt", {}, ("file", "vtt", True)),
        ("rows.jsonl", {}, ("file", "jsonl", True)),
        ("rows.csv", {}, ("file", "csv", True)),
        ("source.py", {}, ("file", "text", True)),
    ]
    got = await pg.evaluate(
        "cases => cases.map(([name, opts]) => [name, classifyFile(name, opts)])",
        cases,
    )
    assert all(
        (row[1]["kind"], row[1]["preview"], row[1]["editable"]) == expected
        for row, (_, _, expected) in zip(got, cases)
    ), "File-kind table matches the shared UI contract"
    # ── Renderer registry — core/renderers.js. One check per core entry,
    # driven straight through renderNode so the table is tested as a table:
    # a new kind is one entry here and one line below.


async def test_renderer_registry(page, driver):
    pg = page
    await pg.wait_for_function(
        "typeof renderNode === 'function' && RENDERERS.length > 0"
    )
    assert await pg.evaluate("RENDERERS.map(e => e.kind)") == [
        "image",
        "video",
        "pdf",
        "html",
        "desktop",
        "vtt",
        "text",
        "md",
        "markdown",
        "rst",
        "docx",
        "pptx",
        "offline",
    ], "Registry holds the core kinds plus this edition's rich ones"
    RENDER = """([name, kind, body, extra]) =>
        renderNode({name, ...(extra || {})}, new Blob([body]), kind)"""
    entries = [
        ("image", ["a.png", "image", "\x89PNG"], 'class="pv-img"'),
        ("image", ["a.jpg", "image", "\xff\xd8\xff"], 'class="pv-img"'),
        ("pdf", ["a.pdf", "pdf", "%PDF-1.4"], 'class="pv-pdf"'),
        ("html", ["a.html", "html", "<p>hi</p>"], 'class="pv-html"'),
        (
            "desktop",
            [
                "a.desktop",
                "desktop",
                "[Desktop Entry]\nType=Link\nName=Home\nURL=https://x.y/",
            ],
            'class="pv-link"',
        ),
        (
            "vtt",
            ["a.vtt", "vtt", "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello"],
            'class="preview-transcript"',
        ),
        ("text", ["a.txt", "text", "plain"], 'class="pv-text"'),
    ]
    for kind, args, marker in entries:
        html = await pg.evaluate(RENDER, args) or ""
        assert marker in html, html[:80]
    html = await pg.evaluate(RENDER, ["a.json", "text", '{"a": 1}']) or ""
    assert "pv-json" in html, "Entry 'text' shows parsed JSON foldable"
    # The fold limit, rather than the engine stack, bounds recursion.
    deep = "[" * 1001 + "]" * 1001
    html = await pg.evaluate(RENDER, ["a.json", "text", deep]) or ""
    assert "pv-json" not in html and "pv-text" in html, html[:80]
    html = (
        await pg.evaluate(RENDER, ["a.vtt", "vtt", "WEBVTT", {"previewFormat": "raw"}])
        or ""
    )
    assert "preview-raw" in html, "Entry 'vtt' honours the raw view"
    html = await pg.evaluate(RENDER, ["a.xyz", "no-such-kind", "plain"]) or ""
    assert 'class="pv-text"' in html, "An unknown kind renders as text"
    await pg.evaluate("""addRenderers([
        {kind: "boom", render() { throw new Error("boom"); }, fallback: "text"},
        {kind: "dead", render() { throw new Error("dead"); }}])""")
    html = await pg.evaluate(RENDER, ["a.txt", "boom", "plain"]) or ""
    assert 'class="pv-text"' in html, "A throwing entry falls back to the kind it names"
    err = await pg.evaluate(
        RENDER + ".catch(e => e.message)", ["a.txt", "dead", "plain"]
    )
    assert err == "dead", err

    if getattr(driver, "native", False):
        assert await pg.evaluate(
            "path.length > 0 && typeof nativeCall === 'function'"
        ), "Native root opens without a browser picker"
    else:
        assert "file://" in await pg.inner_text("#w-msg"), (
            "file:// shows the localhost hint, not a dead picker"
        )
    await pg.evaluate(FAKE)
    await mount(pg)
    assert await pg.evaluate("path[0].name") == "workspace", "Root folder mounts"
    assert await pg.evaluate(
        "!welcome || welcome.hidden"
        if getattr(driver, "native", False)
        else "welcome.hidden"
    ), "Welcome screen hidden after mount"

    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("sel[0] === 'mixed' && path[1]?.kids")
    long = '.col[data-i="1"] .row[title^="this-is-a-very"]'
    visual = await pg.inner_text(long)
    assert visual.rstrip().endswith(".txt") and "identifiable" in visual, repr(visual)
    assert (
        await pg.get_attribute(long, "aria-label")
        == "this-is-a-very-long-file-name-that-must-stay-identifiable.txt"
    ), "Long names keep their full accessible name"
    short = '.col[data-i="1"] .row[title="short.txt"]'
    assert (
        await pg.eval_on_selector(short + " .label", "e=>e.textContent") == "short.txt"
        and await pg.query_selector(short + " .dim") is not None
    ), "Short names keep the existing label styling"
    no_ext = '.col[data-i="1"] .row[title="README"]'
    assert (
        await pg.eval_on_selector(no_ext + " .label", "e=>e.textContent") == "README"
    ), "Names without extensions stay intact"


async def test_directory_states(page):
    pg = page
    await mount(pg)
    for row, expect in (("empty", "Empty"), ("locked", "No permission")):
        await pg.click(f'.col[data-i="0"] .row:has-text("{row}")')
        await pg.wait_for_function(
            "text => document.querySelector('.col[data-i=\"1\"] .col-note')?.textContent.includes(text)",
            arg=expect,
        )
        note = await pg.inner_text('.col[data-i="1"] .col-note')
        assert expect in note, note
        # A column with no rows has nothing to highlight, so → must not move
        # focus into it — that read as a no-op while killing ↑/↓.
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_function("focusCol === 0")
        stayed = await pg.evaluate("focusCol") == 0
        await pg.keyboard.press("ArrowDown")
        await pg.wait_for_function("sel[0] !== " + json.dumps(row))
        st = await pg.evaluate("__state()")
        assert stayed and st["focusCol"] == 0 and st["sel"][0] != row, json.dumps(st)
    await pg.click('.col[data-i="0"] .row:has-text("slow")')
    try:  # the fake read takes 500 ms; don't race it with a fixed sleep
        await pg.wait_for_selector('.col[data-i="1"] .spinner', timeout=2000)
    except PlaywrightTimeoutError:
        assert False, "never appeared"
    await pg.wait_for_function(
        "document.querySelectorAll('.col[data-i=\"1\"] .row').length === 2"
    )
    assert await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length") == 2, (
        "Entries appear when the read finishes"
    )


async def test_column_width(page):
    pg = page
    await mount(pg)
    await pg.evaluate("__watchWidths()")
    await pg.click('.col[data-i="0"] .row:has-text("wide")')
    await pg.wait_for_function("__w.some(w => w.startsWith('wide:'))")
    widths = [
        w.split(":")[1] for w in await pg.evaluate("__w") if w.startswith("wide:")
    ]
    assert set(widths) == {"240px"}, (
        ", ".join(widths) or f"never sized: {await pg.evaluate('__w')}"
    )


async def test_keyboard_vertical(page):
    pg = page
    # sorted order is folders first, alphabetically:
    # big, deep, empty, locked, mixed, slow, then README.md
    await mount(pg)
    await pg.keyboard.press("ArrowDown")  # commits row 0 = "big" (a folder)
    await pg.wait_for_function("sel[0] === 'big' && path[1]?.kids")
    st = await pg.evaluate("__state()")
    assert st["focusCol"] == 0 and st["path"] == ["workspace", "big"], json.dumps(st)
    stable = await pg.evaluate(
        "[...document.querySelectorAll('.col')].map(c=>Math.round(c.getBoundingClientRect().width))"
    )
    names = []
    for name in ("deep", "empty", "locked", "mixed"):
        await pg.keyboard.press("ArrowDown")
        await pg.wait_for_function("name => sel[0] === name && path[1]?.kids", arg=name)
        s = await pg.evaluate("__state()")
        names.append(s["sel"][0])
    assert (
        names == ["deep", "empty", "locked", "mixed"]
        and (await pg.evaluate("focusCol")) == 0
    ), str(names)
    await pg.keyboard.press("ArrowUp")
    await pg.wait_for_function("sel[0] === 'locked'")
    assert (await pg.evaluate("sel[0]")) == "locked" and (
        await pg.evaluate("focusCol")
    ) == 0, "↑ walks back up the same column"
    assert (
        await pg.evaluate(
            "[...document.querySelectorAll('.col')].map(c=>Math.round(c.getBoundingClientRect().width))"
        )
        == stable
    ), json.dumps(
        {
            "before": stable,
            "after": await pg.evaluate(
                "[...document.querySelectorAll('.col')].map(c=>Math.round(c.getBoundingClientRect().width))"
            ),
        }
    )
    await pg.keyboard.press("End")
    await pg.wait_for_function("sel[0] === 'README.md'")
    assert (await pg.evaluate("sel[0]")) == "README.md", "End jumps to the last row"
    await pg.keyboard.press("Home")
    await pg.wait_for_function("sel[0] === 'big'")
    assert (await pg.evaluate("sel[0]")) == "big", "Home jumps to the first row"


@pytest.mark.parametrize("deferred", ["none", "scroll", "preview"])
async def test_keyboard_horizontal(page, deferred):
    pg = page
    if deferred == "preview":
        await pg.evaluate("""() => {
          const blob = FS.blob.bind(FS);
          FS.blob = async node => {
            if (node.name === 'leaf.txt') {
              for (let i = 0; i < 12; i++) {
                await new Promise(requestAnimationFrame);
              }
            }
            return blob(node);
          };
        }""")
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("deep")')
    await pg.wait_for_function("sel[0] === 'deep' && path[1]?.kids")
    assert await pg.evaluate("focusCol") == 0, (
        "Clicking a folder also keeps focus in its own column"
    )
    await pg.keyboard.press("ArrowRight")  # into "deep"
    await pg.wait_for_function("focusCol === 1")
    assert await pg.evaluate("focusCol") == 1, "→ moves focus into the open column"
    for depth in range(2, 5):
        await pg.wait_for_function(
            "i => path[i]?.kids && colCache.get(path[i])?.rows.length",
            arg=depth,
        )
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_function(
            "depth => focusCol === depth && colCache.get(path[depth])?.rows.length",
            arg=depth,
        )
    st = await pg.evaluate("__state()")
    assert (
        st["path"] == ["workspace", "deep", "alpha", "beta", "gamma"]
        and st["sel"][-1] == "leaf.txt"
    ), json.dumps(st["path"])
    await pg.keyboard.press("ArrowLeft")
    await pg.wait_for_function("focusCol === 3")
    assert await pg.evaluate("focusCol") == 3, "← moves focus back out"
    await pg.keyboard.press("ArrowRight")
    await pg.wait_for_function("focusCol === 4")
    assert (
        await pg.evaluate("sel[4]") == "leaf.txt" and await pg.evaluate("focusCol") == 4
    ), "→ returns to the row the column was left on"
    await pg.keyboard.press("ArrowRight")
    assert await pg.evaluate("document.activeElement?.id") == "preview", (
        "→ focuses the preview from the rightmost column"
    )
    await pg.keyboard.press("ArrowLeft")
    await pg.wait_for_function("focusCol === 4")
    st = await pg.evaluate("__state()")
    assert (
        st["focusCol"] == 4
        and st["sel"][-1] == "leaf.txt"
        and await pg.evaluate("document.querySelector('.col.focus .row.cursor')?.title")
        == "leaf.txt"
    ), json.dumps(st)
    await pg.keyboard.press("ArrowRight")
    await pg.wait_for_function("document.activeElement?.id === 'preview'")
    # ← from the preview re-rendered it (A9), and its text arrives after an
    # asynchronous read. A scroll key pressed before then has nothing to
    # scroll, and the wait for movement below can only time out.
    await pg.wait_for_function(
        """() => { const body = document.querySelector('#preview .pv-body');
          return body?.querySelector('.pv-text')?.textContent.startsWith('leaf')
            && body.scrollHeight > body.clientHeight; }"""
    )
    if deferred == "scroll":
        # Model a scroll write that lands after the keyboard round trip.
        await pg.evaluate("""() => {
          const body = document.querySelector('#preview .pv-body');
          const scrollBy = body.scrollBy.bind(body);
          body.scrollBy = options => requestAnimationFrame(() =>
            requestAnimationFrame(() => requestAnimationFrame(() => scrollBy(options))));
        }""")
    before = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
    await pg.keyboard.press("PageDown")
    await pg.wait_for_function(
        "before => document.querySelector('#preview .pv-body').scrollTop > before",
        arg=before,
    )
    after = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
    assert after > before, f"{before} -> {after}"
    await pg.keyboard.press("ArrowUp")
    await pg.wait_for_function(
        "after => document.querySelector('#preview .pv-body').scrollTop < after",
        arg=after,
    )
    restored = await pg.evaluate(
        "document.querySelector('#preview .pv-body').scrollTop"
    )
    assert restored < after, f"{after} -> {restored}"
    await pg.keyboard.press("ArrowDown")
    await pg.wait_for_function(
        "restored => document.querySelector('#preview .pv-body').scrollTop > restored",
        arg=restored,
    )
    down = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
    assert down > restored, f"{restored} -> {down}"
    await pg.keyboard.press("PageUp")
    await pg.wait_for_function(
        "down => document.querySelector('#preview .pv-body').scrollTop < down",
        arg=down,
    )
    up = await pg.evaluate("document.querySelector('#preview .pv-body').scrollTop")
    assert up < down, f"{down} -> {up}"


async def test_mount_stops_previous_fold(page):
    await mount(page)
    await page.evaluate("""async () => {
      dialTo(range(), true);
      await mount(__mk(0));
    }""")
    await scroll_settled(page)
    assert await page.evaluate("folded") == 0
    assert await page.locator('.col[data-i="0"] .row[title="refresh"]').is_visible()


async def test_new_root_has_its_widening_range_immediately(page):
    await page.set_viewport_size({"width": 390, "height": 844})
    position = await page.evaluate("""async () => {
      await mount(__mk(0));
      finder.scrollTo({left: 0, behavior: 'instant'});
      return dial();
    }""")
    assert position < 0


async def test_new_root_releases_previous_wheel_axis(page):
    await mount(page)
    await page.clock.install()
    await page.evaluate("""async () => {
      finder.dispatchEvent(new WheelEvent('wheel', {
        deltaX: 3, deltaY: 40, bubbles: true, cancelable: true,
      }));
      await mount(__mk(0));
    }""")
    # A mount cancels the old settle timer. Its axis must still expire.
    await page.clock.run_for(250)
    position = await page.evaluate("""() => {
      const before = dial();
      finder.dispatchEvent(new WheelEvent('wheel', {
        deltaX: 40, deltaY: 3, bubbles: true, cancelable: true,
      }));
      return {before, after: dial()};
    }""")
    assert position["after"] > position["before"], position


async def test_instant_dial_move_supersedes_deferred_glide(page):
    await mount(page)
    await page.evaluate("""() => {
      dialTo(range(), false);
      dialTo(range() / 2, true);
      dialTo(0, false);
    }""")
    await scroll_settled(page)
    assert await page.evaluate("dial()") == 0
    assert await page.evaluate("folded") == 0


async def test_folding_dial(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("deep")')
    await pg.wait_for_function("path[1]?.name === 'deep' && path[1]?.kids")
    for col in range(1, 5):
        await pg.wait_for_function(
            "i => path[i]?.kids && colCache.get(path[i])?.rows.length",
            arg=col,
        )
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_function("focusCol === " + str(col))
    await pg.keyboard.press("ArrowRight")  # focus the leaf preview
    await scroll_settled(pg)
    # Both moves glide: the dial is a CSS smooth scroll either way round, so
    # wait for it to stop rather than for a clock. A flat 300 ms read the
    # fold mid-flight and counted 4 of the 5 spines.
    # A fling runs to the end of the scrollbar, which is one stop away
    # (ADR 0075): first the rightmost column alone, then every column.
    n = await pg.evaluate("path.length")
    await pg.evaluate("finder.scrollLeft = finder.scrollWidth")
    settled = await scroll_settled(pg)
    await pg.wait_for_function(
        "document.querySelectorAll('.col.spine').length === path.length - 1 && finder.scrollLeft < finder.scrollWidth - finder.clientWidth - 1"
    )
    spines = await pg.eval_on_selector_all(".col.spine", "e=>e.length")
    assert spines == n - 1, f"{spines} spines of {n}" + (
        "" if settled else ", scroll never settled"
    )
    await pg.evaluate("finder.scrollLeft = finder.scrollWidth")
    settled = await scroll_settled(pg)
    await pg.wait_for_function(
        "document.querySelectorAll('.col.spine').length === path.length"
    )
    spines = await pg.eval_on_selector_all(".col.spine", "e=>e.length")
    assert spines == n, f"{spines} spines of {n}" + (
        "" if settled else ", scroll never settled"
    )
    await pg.evaluate("document.querySelector('.col.spine').click()")
    await scroll_settled(pg)
    assert await pg.eval_on_selector_all(".col.spine", "e=>e.length") == 0, (
        "Clicking a spine unfolds it"
    )

    # Opening a folder is the user pointing at a column. The dial may fold
    # what they have walked past, never the column under the finger nor the
    # one that tap just opened — at 390 px the old arithmetic folded all of
    # it, preview first. Driving it here is what proves the *bundle* carries
    # the fold rule, not only the modular sources.
    await pg.set_viewport_size({"width": 390, "height": 700})
    await scroll_settled(pg)
    if await pg.eval_on_selector_all('.col[data-i="0"].spine', "e=>e.length"):
        await pg.click('.col[data-i="0"].spine')  # rows of a spine are hidden
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
    assert fold["folded"] <= fold["focusCol"] and not fold["atOrRight"], json.dumps(
        fold
    )
    assert fold["uncapped"] > fold["focusCol"], json.dumps(fold)

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
    await pg.wait_for_function("sel[0] === 'wide' && path[1]?.kids")
    for i in range(5):
        await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
        await pg.wait_for_function(
            "n => path.length === n && path.at(-1)?.kids", arg=i + 3
        )
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
    assert (
        touched["clipped"] <= 2
        and touched["rowClipped"] <= 2
        and not touched["spine"]
        and touched["stage"] == 0
    ), json.dumps(touched)
    assert touched["wouldClip"] > 0, json.dumps(touched)

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
    await pg.wait_for_function("sel[0] === 'wide' && path[1]?.kids")
    for i in range(3):
        await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
        await pg.wait_for_function(
            "n => path.length === n && path.at(-1)?.kids", arg=i + 3
        )
    await scroll_settled(pg)
    await pg.set_viewport_size({"width": 375, "height": 812})  # rotate
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
    assert (
        rotated["clipped"] <= 2
        and rotated["rowClipped"] <= 2
        and max(rotated["widths"]) <= rotated["cap"]
    ), json.dumps(rotated)

    # Desktop is the other half of the contract: at a width where the strip
    # up to focus fits, nothing pans and nothing is clamped, so the dial
    # behaves exactly as it did before any of this.
    await mount(pg)
    await pg.set_viewport_size({"width": 1500, "height": 900})
    await scroll_settled(pg)
    await pg.click('.col[data-i="0"] .row:has-text("wide")')
    await pg.wait_for_function("sel[0] === 'wide' && path[1]?.kids")
    for i in range(3):
        await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
        await pg.wait_for_function(
            "n => path.length === n && path.at(-1)?.kids", arg=i + 3
        )
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
    assert (
        desktop["pan"] == 0
        and desktop["whole"]
        and desktop["natural"] <= desktop["cap"]
    ), json.dumps(desktop)

    # The whole model, one check per device class (ADR 0062). Every
    # viewport walks the same four folders at the width ceiling and asserts
    # the same promises: the touched column and its row are whole, the
    # column that tap opened starts on screen unless the pan had to give
    # the touched column the whole width (ADR 0024), nothing right of focus
    # is a spine, no column is wider than two thirds of the finder, and the
    # strip moved by its own transform, never by scrolling #stage. Which
    # mechanism got there differs — the phones fold and pan, the tablet and
    # desktop fit — and the detail shows it.
    for label, w, h in (
        ("phone portrait", 390, 844),
        ("phone landscape", 844, 390),
        ("tablet", 1024, 768),
        ("desktop", 1440, 900),
    ):
        await mount(pg)
        await pg.set_viewport_size({"width": w, "height": h})
        await scroll_settled(pg)
        await pg.click('.col[data-i="0"] .row:has-text("wide")')
        await pg.wait_for_function("sel[0] === 'wide' && path[1]?.kids")
        for i in range(3):
            await pg.click(f'.col[data-i="{i + 1}"] .row:has-text("level-{i}-")')
            await pg.wait_for_function(
                "n => path.length === n && path.at(-1)?.kids", arg=i + 3
            )
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
        assert (
            m["focusCol"] == 3
            and m["touchedWhole"]
            and m["rowWhole"]
            and (m["openedStartsInside"] or m["pan"] > 0)
            and not m["spinesAtOrRight"]
            and m["stage"] == 0
            and m["maxWidth"] <= m["cap"]
        ), json.dumps(m)

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
    await pg.wait_for_function("sel[0] === 'deep' && path[1]?.kids")
    for depth in range(1, 5):  # in to the leaf column
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_function(
            "depth => focusCol === depth && colCache.get(path[depth])?.rows.length",
            arg=depth,
        )
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
    assert strip_pos["stage"] == 0 and strip_pos["leftmost"] >= -strip_pos["pan"] - 2, (
        json.dumps(strip_pos)
    )
    assert strip_pos["wouldClip"] > 0 and strip_pos["clipped"] <= 2, json.dumps(
        strip_pos
    )

    # The other half of revealRow: it replaced a browser primitive, so the
    # axis a row *does* need still has to work. A short viewport makes a
    # nine-row column overflow, and End has to bring the last row back.
    await mount(pg)
    await pg.set_viewport_size({"width": 320, "height": 260})
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("sel[0] === 'mixed' && path[1]?.kids")
    await pg.keyboard.press("ArrowRight")
    await pg.wait_for_function("focusCol === 1")
    await pg.keyboard.press("End")
    await pg.wait_for_function(
        "document.querySelector('.col.focus .row.cursor')?.title === visibleKids(path[focusCol]).at(-1)?.name"
    )
    seen = await pg.evaluate("""(() => {
      const row = document.querySelector('.col.focus .row.cursor');
      if (!row) return null;
      const body = row.closest('.col-body');
      const r = row.getBoundingClientRect(), b = body.getBoundingClientRect();
      return {above: Math.round(r.top - b.top),
              below: Math.round(b.bottom - r.bottom),
              scrolled: Math.round(body.scrollTop)};
    })()""")
    assert seen and seen["above"] >= -1 and seen["below"] >= -1, json.dumps(seen)
    assert seen and seen["scrolled"] > 0, json.dumps(seen)
    end_scroll = seen["scrolled"]
    await pg.keyboard.press("Home")
    await pg.wait_for_function(
        "document.querySelector('.col.focus .row.cursor')?.title === visibleKids(path[focusCol])[0]?.name"
    )
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
    assert (
        seen["above"] >= -1 and seen["below"] >= -1 and seen["scrolled"] < end_scroll
    ), json.dumps(seen)

    await pg.keyboard.press("PageDown")
    await pg.wait_for_function("""() => {
      const col = document.querySelector('.col.focus'), body = col.querySelector('.col-body');
      const bounds = body.getBoundingClientRect();
      const rows = [...col.querySelectorAll('.row')].filter(row => {
        const r = row.getBoundingClientRect(); return r.bottom > bounds.top && r.top < bounds.bottom;
      });
      return col.querySelector('.row.cursor') === rows.at(-1);
    }""")
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
    assert first_page and first_page["selected"] == first_page["edge"], json.dumps(
        first_page
    )
    await pg.keyboard.press("PageDown")
    await pg.wait_for_function(
        "before => document.querySelector('.col.focus .col-body').scrollTop > before",
        arg=first_page["scroll"],
    )
    second_page = await pg.evaluate("""(() => {
      const col = document.querySelector('.col.focus');
      const body = col.querySelector('.col-body');
      return {selected: col.querySelector('.row.cursor')?.textContent,
              scroll: body.scrollTop, max: body.scrollHeight - body.clientHeight};
    })()""")
    assert (
        second_page
        and second_page["scroll"] > first_page["scroll"]
        and second_page["scroll"] <= second_page["max"] + 1
    ), json.dumps(second_page)
    await pg.keyboard.press("PageUp")
    await pg.wait_for_function("""() => {
      const col = document.querySelector('.col.focus'), body = col.querySelector('.col-body');
      const bounds = body.getBoundingClientRect();
      const first = [...col.querySelectorAll('.row')].find(row => {
        const r = row.getBoundingClientRect(); return r.bottom > bounds.top && r.top < bounds.bottom;
      });
      return col.querySelector('.row.cursor') === first;
    }""")
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
    assert third_page and third_page["selected"] == third_page["edge"], json.dumps(
        third_page
    )
    await pg.set_viewport_size({"width": 1500, "height": 900})
    await scroll_settled(pg)


async def test_preview(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("sel[0] === 'mixed' && path[1]?.kids")
    await pg.click('.col[data-i="1"] .row:has-text("note.md")')
    await pg.wait_for_function(
        "document.querySelector('.pv-text')?.textContent.trim() === '# note'"
    )
    assert (await pg.inner_text(".pv-text")).strip() == "# note", (
        "Text file previews its contents"
    )
    assert await pg.get_attribute("#pv-fullscreen", "aria-pressed") == "false", (
        "Preview offers fullscreen control"
    )
    await pg.focus("#pv-fullscreen")
    await pg.keyboard.press("Enter")
    await pg.wait_for_function("document.fullscreenElement !== null")
    full = await pg.evaluate("""() => {
      const pv = document.querySelector('#preview').getBoundingClientRect();
      const cs = getComputedStyle(document.querySelector('#preview .pv-body'));
      return {bar: getComputedStyle(document.querySelector('#bar')).display,
              status: getComputedStyle(document.querySelector('#status')).display,
              padding: cs.padding,
              preview: [Math.round(pv.left), Math.round(pv.top),
                        Math.round(pv.width), Math.round(pv.height)]};
    }""")
    assert full["bar"] == full["status"] == "none" and full["padding"] == "0px", (
        json.dumps(full)
    )
    await pg.keyboard.press("Enter")
    await pg.wait_for_function("document.fullscreenElement === null")
    assert await pg.get_attribute("#pv-fullscreen", "aria-pressed") == "false", (
        "Fullscreen control exits with keyboard"
    )
    assert "B ·" in await pg.inner_text("#pv-sub"), await pg.inner_text("#pv-sub")
    await pg.click('.col[data-i="1"] .row:has-text("long.txt")')
    await pg.wait_for_function(
        "document.querySelector('.pv-text')?.textContent.length > 4000"
    )
    # A text box that stopped at part-height left the rest of the column
    # empty and scrolled on its own, so the column never used its height.
    fit = await pg.evaluate("""() => {
      const t = document.querySelector('.pv-text');
      const b = document.querySelector('#preview .pv-body');
      return {inner:  t.scrollHeight > t.clientHeight + 1,
              column: b.scrollHeight > b.clientHeight + 1};
    }""")
    assert not fit["inner"], json.dumps(fit)
    assert fit["column"], json.dumps(fit)
    await pg.click('.col[data-i="1"] .row:has-text("page.html")')
    await pg.wait_for_function("document.querySelector('iframe.pv-html')")
    assert await pg.is_visible("iframe.pv-html"), "HTML file previews in an iframe"
    # 100cqh/100%: the frame must fill one visible screen of .pv-body,
    # whatever width the fold dial has left the pane.
    fit = await pg.evaluate("""(() => {
      const f = document.querySelector('iframe.pv-html').getBoundingClientRect();
      const b = document.querySelector('.pv-body'), cs = getComputedStyle(b);
      return [f.width  - (b.clientWidth  - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)),
              f.height - (b.clientHeight - parseFloat(cs.paddingTop)  - parseFloat(cs.paddingBottom))];
    })()""")
    assert all(abs(d) < 2 for d in fit), str(fit)
    await pg.click('.col[data-i="1"] .row:has-text("doc.pdf")')
    await pg.wait_for_function("document.querySelector('iframe.pv-pdf')")
    assert await pg.is_visible("iframe.pv-pdf"), "PDF file previews in an iframe"
    # The same rule as .pv-html: no half-height box inside the pane.
    fit = await pg.evaluate("""(() => {
      const f = document.querySelector('iframe.pv-pdf').getBoundingClientRect();
      const b = document.querySelector('.pv-body'), cs = getComputedStyle(b);
      return [f.width  - (b.clientWidth  - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)),
              f.height - (b.clientHeight - parseFloat(cs.paddingTop)  - parseFloat(cs.paddingBottom))];
    })()""")
    assert all(abs(d) < 2 for d in fit), str(fit)
    await pg.click('.col[data-i="1"] .row:has-text("sub")')
    await pg.wait_for_function(
        "document.querySelector('.pv-empty') && path[2]?.name === 'sub'"
    )
    assert await pg.is_visible(".pv-empty"), "Selecting a folder clears the preview"

    # ── Syntax highlighting — core/syntax.js, the same file the server
    # build loads. Rich previews are off in this suite, so what runs here
    # is the offline path every build falls back to.
    await pg.click('.col[data-i="2"] .row:has-text("a.py")')
    await pg.wait_for_function(
        "document.querySelectorAll('.pv-text .hl-kw').length > 0"
    )
    assert (
        await pg.eval_on_selector_all(
            ".pv-text span", "e=>[...new Set(e.map(x=>x.className))].sort().join()"
        )
        == "hl-com,hl-kw,hl-num,hl-str"
    ), "Source previews with every token class coloured"
    assert (await pg.text_content(".pv-text")) == PY_SRC, (
        "…and the file still reads exactly as written"
    )
    assert await pg.is_visible("#pv-edit"), "…and a coloured file is still editable"
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
    assert w["code"] >= w["ch88"] - 0.5, json.dumps(w)
    assert not w["sideways"], json.dumps(w)
    assert w["lines"] == 4, json.dumps(w)
    # Zoomed to ~170 %, the CSS viewport is 900 px wide. The pane must keep
    # its 88 columns rather than wrap the line; longer lines still wrap at
    # column 88 or later, and a pane narrower than that scrolls .pv-body.
    await pg.set_viewport_size({"width": 900, "height": 700})
    await scroll_settled(pg)
    w = await pg.evaluate(WIDTH)
    assert w["code"] >= w["ch88"] - 0.5, json.dumps(w)
    assert w["lines"] == 4, json.dumps(w)
    # A phone cannot show 88 columns. With the dial at 100 % the pane is
    # alone and must fit the stage — what runs past the right edge is
    # clipped, not scrollable — and the code pans inside .pv-body instead.
    await pg.set_viewport_size({"width": 390, "height": 700})
    await scroll_settled(pg)
    await pg.evaluate("dialTo(range() * 0.99, true)")
    await scroll_settled(pg)
    w = await pg.evaluate(WIDTH)
    fits = await pg.evaluate("""(() => {
      const p = document.getElementById('preview').getBoundingClientRect();
      const s = stage.getBoundingClientRect();
      return {ok: p.left >= s.left - 1 && p.right <= s.right + 1,
              preview: [Math.round(p.left), Math.round(p.right)],
              stage: [Math.round(s.left), Math.round(s.right)],
              target: previewTarget(), scroll: dial(), max: range()};
    })()""")
    assert fits["ok"] and w["code"] >= w["ch88"] - 0.5, json.dumps(w) + json.dumps(fits)
    assert w["sideways"] and w["lines"] == 4, json.dumps(w)
    await pg.set_viewport_size({"width": 1500, "height": 900})
    await scroll_settled(pg)
    # Both palettes are declared; that they are legible is a screenshot's
    # job, but a theme that never reaches the tokens is a bug this catches.
    colour = "e=>getComputedStyle(e).color"
    was = await pg.evaluate("root.dataset.theme")
    light = await pg.eval_on_selector(".pv-text .hl-kw", colour)
    await pg.evaluate("root.dataset.theme = 'dark'")
    dark = await pg.eval_on_selector(".pv-text .hl-kw", colour)
    assert light != dark, f"{light} vs {dark}"
    await pg.evaluate(f"root.dataset.theme = {was!r}")
    # Past the 8 000 characters the preview used to stop at. The text check
    # alone would pass on a build that coloured the head and escaped the
    # tail, so the span count is what proves colour reaches the last line:
    # def + return is two keywords per copy, 600 across the 300.
    await pg.click('.col[data-i="2"] .row:has-text("long.py")')
    await pg.wait_for_function(
        "document.querySelectorAll('.pv-text .hl-kw').length === 600"
    )
    whole = await pg.text_content(".pv-text")
    kw = await pg.eval_on_selector_all(".pv-text .hl-kw", "e=>e.length")
    assert whole == PY_SRC * 300, f"{len(whole)} chars, expected {len(PY_SRC) * 300}"
    assert kw == 600, f"{kw} hl-kw spans, expected 600"
    # …and the ceiling that replaced the clip. Removing the 8 000-char cut
    # only made the 512 KB gate load-bearing, so one byte over it must still
    # decline rather than render — otherwise "whole or absent" has no second
    # half and a 50 MB .sql renders whole.
    await pg.click('.col[data-i="2"] .row:has-text("huge.py")')
    await pg.wait_for_function(
        "document.querySelector('#pv-content')?.textContent.includes('No inline preview')"
    )
    body = await pg.inner_text("#pv-content")
    assert not await pg.is_visible(".pv-text") and "No inline preview" in body, body[
        :80
    ]
    # The phone pass above folded two columns, and a fold outlives the
    # resize back: unfolding is a user action, so make it one.
    if await pg.eval_on_selector_all('.col[data-i="1"].spine', "e=>e.length"):
        await pg.click('.col[data-i="1"].spine')
        await scroll_settled(pg)
    await pg.click('.col[data-i="1"] .row:has-text("large.png")')
    await pg.wait_for_function("document.querySelector('.pv-img')?.naturalWidth > 0")
    assert await pg.evaluate(
        "() => document.querySelector('.pv-img')?.naturalWidth > 0"
    ), await pg.inner_text("#pv-content")
    await pg.click('.col[data-i="1"] .row:has-text("large.jpeg")')
    await pg.wait_for_function("document.querySelector('.pv-img')?.naturalWidth > 0")
    assert await pg.evaluate(
        "() => document.querySelector('.pv-img')?.naturalWidth > 0"
    ), await pg.inner_text("#pv-content")
    await pg.click('.col[data-i="1"] .row:has-text("short.txt")')
    await pg.wait_for_function(
        "sel[1] === 'short.txt' && document.querySelector('.pv-text')?.textContent === 's'"
    )
    assert await pg.eval_on_selector_all(".pv-text span", "e=>e.length") == 0, (
        "A file with no language it knows stays plain"
    )


async def test_jsonl_rows(page):
    pg = page
    await mount(pg)
    await click_row(pg, 0, "tables")
    await pg.wait_for_function("path[1]?.name === 'tables' && path[1]?.kids")
    await click_row(pg, 1, "log.jsonl")
    await pg.wait_for_function("path[2]?.name === 'log.jsonl' && path[2]?.kids")
    assert await pg.evaluate("__rows(2)") == ["Second", "First", "Third"], str(
        await pg.evaluate("__rows(2)")
    )
    await click_row(pg, 2, "Second")
    await pg.wait_for_function(
        "path[3]?.name === 'Second' && document.querySelector('.pv-json details')"
    )
    assert (
        await pg.evaluate("__rows(3)") == ["id", "title", "ts", "tags"]
        and await pg.locator("#preview .pv-json details").count() > 0
    ), "A row opens as the JSON hierarchical view"
    await click_row(pg, 3, "tags")
    await pg.wait_for_function("path[4]?.name === 'tags' && path[4]?.kids")
    assert await pg.evaluate("__rows(4)") == ["0", "1"], (
        "A JSONL row's nested array remains navigable"
    )
    await click_row(pg, 4, "1")
    await pg.wait_for_function("path[5]?.name === '1' && path[5]?.kids")
    assert await pg.evaluate("__rows(5)") == ["ok"], (
        "A JSONL array object remains navigable"
    )
    await pg.evaluate("applyPath(['tables', 'log.jsonl', 'Second'])")
    await pg.wait_for_function("sel[2] === 'Second' && path[3]?.kids")
    await click_row(pg, 3, "title")
    await pg.wait_for_function(
        "document.querySelector('.pv-content')?.textContent.trim() === 'Second'"
    )
    assert (await pg.inner_text(".pv-content")).strip() == "Second", (
        "A JSONL scalar keeps the JSON scalar preview"
    )
    assert await pg.inner_text("#pv-sub") == "", "…with no invented size or date"
    await pg.evaluate("applyPath(['tables', 'log.jsonl', 'Third'])")
    await pg.wait_for_function(
        "document.querySelector('#pv-content')?.textContent.includes('2026-01-03')"
    )
    assert (await pg.evaluate("sel"))[
        -1
    ] == "Third" and "2026-01-03" in await pg.inner_text("#pv-content"), (
        "A deep link names a row and restores it"
    )
    await click_row(pg, 1, "dup.jsonl")
    await pg.wait_for_function("path[2]?.name === 'dup.jsonl' && path[2]?.kids")
    assert await pg.evaluate("__rows(2)") == ["10", "11"], str(
        await pg.evaluate("__rows(2)")
    )
    await click_row(pg, 1, "bad.jsonl")
    await pg.wait_for_function(
        "document.querySelector('#preview .pv-err')?.textContent.includes('Not valid JSONL: line 2')"
    )
    note = await pg.inner_text("#preview .pv-err")
    assert (
        "Not valid JSONL: line 2" in note
        and await pg.locator('.col[data-i="2"]').count() == 0
        and await pg.locator('.row[title="bad.jsonl"] .chev').count() == 0
    ), note
    await click_row(pg, 1, "huge.jsonl")
    await pg.wait_for_selector('.col[data-i="2"] .row', timeout=15000)
    rows = await pg.evaluate("__rows(2)")
    assert (
        rows[:2] == ["line 1", "line 2"]
        and await pg.evaluate("path[2].kids.length") == 20000
    ), str(rows[:3])
    await pg.evaluate("applyPath(['tables', 'huge.jsonl', 'line 3'])")
    await pg.wait_for_selector("#preview .pv-json", timeout=15000)
    assert (await pg.evaluate("sel"))[-1] == "line 3" and '"id":3' in (
        await pg.inner_text("#pv-content")
    ).replace(" ", ""), await pg.inner_text("#pv-content")
    await pg.evaluate("applyPath(['tables', 'huge.jsonl', 'line 7'])")
    await pg.wait_for_selector("#preview .pv-err", timeout=15000)
    err = await pg.inner_text("#preview .pv-err")
    assert (
        "Not valid JSONL: line 7" in err
        and (await pg.evaluate("sel"))[-1] == "line 7"
        and "line 8" in await pg.evaluate("__rows(2)")
    ), err
    # back where the sections below expect to find note.md
    await click_row(pg, 0, "mixed")
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")


async def test_edit_mode(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    await click_row(pg, 1, "long.txt")
    await pg.wait_for_function(
        "document.querySelector('.pv-text')?.textContent.length > 4000"
    )
    await pg.click("#pv-edit")
    await pg.wait_for_function("document.querySelector('#pv-editor')")
    top = await pg.evaluate("""() => {
      const ta = document.querySelector('#pv-editor');
      return {start: ta.selectionStart, end: ta.selectionEnd,
              scroll: ta.scrollTop, value: ta.value};
    }""")
    assert (
        top["start"] == top["end"] == top["scroll"] == 0
        and top["value"] == "a line of plain text\n" * 400
    ), json.dumps({**top, "value": f"{len(top['value'])} chars"})
    await pg.click("#pv-cancel")
    await pg.wait_for_function(
        "!document.querySelector('#pv-editor') && document.querySelector('.pv-text')"
    )
    await click_row(pg, 1, "sub")
    await pg.wait_for_function("path[2]?.name === 'sub' && path[2]?.kids")
    await click_row(pg, 2, "long.py")
    await pg.wait_for_function(
        "document.querySelectorAll('.pv-text .hl-kw').length === 600"
    )
    await pg.click("#pv-edit")
    await pg.wait_for_function("document.querySelector('#pv-editor')")
    top = await pg.evaluate("""() => {
      const ta = document.querySelector('#pv-editor');
      return {start: ta.selectionStart, end: ta.selectionEnd,
              scroll: ta.scrollTop, value: ta.value};
    }""")
    assert (
        top["start"] == top["end"] == top["scroll"] == 0
        and top["value"] == PY_SRC * 300
    ), json.dumps({**top, "value": f"{len(top['value'])} chars"})
    await pg.click("#pv-cancel")
    await pg.wait_for_function(
        "!document.querySelector('#pv-editor') && document.querySelector('.pv-text')"
    )
    await click_row(pg, 0, "mixed")
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    await click_row(pg, 1, "note.md")
    await pg.wait_for_function(
        "document.querySelector('.pv-text')?.textContent.trim() === '# note'"
    )
    assert await pg.is_visible("#pv-edit"), "Text preview offers an Edit button"
    await pg.click("#pv-edit")
    await pg.wait_for_function("document.querySelector('#pv-editor')")
    assert await pg.input_value("#pv-editor") == "# note", (
        "Edit opens a textarea with the full text"
    )
    st = await pg.evaluate("__state()")
    await pg.type("#pv-editor", "x")
    await pg.keyboard.press("ArrowDown")
    assert await pg.evaluate("__state()") == st, (
        "Typing in the editor does not move the columns"
    )
    await pg.click("#pv-cancel")
    await pg.wait_for_function(
        "!document.querySelector('#pv-editor') && document.querySelector('.pv-text')"
    )
    assert (await pg.inner_text(".pv-text")).strip() == "# note", (
        "Cancel returns the unchanged read-only preview"
    )
    await pg.click("#pv-edit")
    await pg.wait_for_function("document.querySelector('#pv-editor')")
    await pg.fill("#pv-editor", "# edited")
    await pg.click("#pv-save")
    await pg.wait_for_function(
        "document.querySelector('.pv-text')?.textContent.trim() === '# edited'"
    )
    assert (await pg.inner_text(".pv-text")).strip() == "# edited", (
        "Save writes the file and returns to the preview"
    )
    await click_row(pg, 1, "data.json")
    await pg.wait_for_function(
        "sel[1] === 'data.json' && document.querySelector('.pv-json')"
    )
    await click_row(pg, 1, "note.md")
    await pg.wait_for_function(
        "sel[1] === 'note.md' && document.querySelector('.pv-text')?.textContent.trim() === '# edited'"
    )
    assert await pg.is_hidden("#pv-modified"), "Saved and reopened text is not modified"
    assert (await pg.inner_text(".pv-text")).strip() == "# edited", (
        "The change survives re-opening the file"
    )
    await editor_feature_checks(pg)
    await click_row(pg, 1, "page.html")
    await pg.wait_for_function("document.querySelector('iframe.pv-html')")
    assert await pg.is_hidden("#pv-edit"), "A non-text preview offers no Edit button"


async def test_json_preview(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    await click_row(pg, 1, "nested.json")
    await pg.wait_for_function(
        "path[2]?.name === 'nested.json' && document.querySelector('.pv-json')"
    )
    assert (
        await pg.locator('.col[data-i="1"] .row:has-text("docs") .ico.dir').count() == 1
    ), "Ordinary directories keep the folder icon"
    assert await pg.evaluate("__rows(2)") == ["name", "tags", "items", "meta"], (
        "Valid JSON opens as an ordered key column"
    )
    assert (
        await pg.locator(
            '.col[data-i="1"] .row:has-text("nested.json") .ico.seti'
        ).count()
        == 1
    ), "JSON files use the JSON icon"
    assert (
        await pg.locator("#preview .pv-json").count() == 1
        and await pg.locator("#preview details").count() > 0
    ), "Selected JSON object keeps its preview beside its children"
    await click_row(pg, 2, "tags")
    await pg.wait_for_function("path[3]?.name === 'tags' && path[3]?.kids")
    assert await pg.evaluate("__rows(3)") == ["0", "1"], (
        "Nested arrays open as ordered index rows"
    )
    assert (
        await pg.locator('.col[data-i="2"] .row:has-text("tags") .ico.glyph').count()
        == 1
        and await pg.locator(
            '.col[data-i="2"] .row:has-text("tags") .ico.glyph'
        ).inner_text()
        == "[]"
    ), "JSON arrays use the [] icon"
    await click_row(pg, 3, "0")
    await pg.wait_for_function(
        "document.querySelector('.pv-content')?.textContent.trim() === 'a'"
    )
    assert (await pg.inner_text(".pv-content")).strip() == "a", (
        "Scalar JSON values preview in the pane"
    )
    await click_row(pg, 2, "meta")
    await pg.wait_for_function("path[3]?.name === 'meta' && path[3]?.kids")
    assert await pg.evaluate("__rows(3)") == ["n", "ok", "none"], (
        "Nested objects remain navigable"
    )
    assert (
        await pg.locator('.col[data-i="2"] .row:has-text("meta") .ico.glyph').count()
        == 1
        and await pg.locator(
            '.col[data-i="2"] .row:has-text("meta") .ico.glyph'
        ).inner_text()
        == "{}"
    ), "JSON objects use the {} icon"
    await click_row(pg, 2, "items")
    await pg.wait_for_function(
        "path[3]?.name === 'items' && document.querySelector('.pv-json')"
    )
    assert (
        await pg.evaluate("__rows(3)") == ["0"]
        and await pg.locator("#preview .pv-json").count() == 1
    ), "Arrays expose object child nodes"
    await click_row(pg, 3, "0")
    await pg.wait_for_function("path[4]?.name === '0' && path[4]?.kids")
    assert await pg.evaluate("__rows(4)") == ["id", "name"], (
        "Array object children remain navigable"
    )
    await click_row(pg, 1, "bad.json")
    await pg.wait_for_selector(".pv-text:not(.pv-json)")
    assert (await pg.inner_text(".pv-text")) == "{oops" and await pg.locator(
        '.row[title="bad.json"] .chev'
    ).count() == 0, "Invalid JSON keeps the coloured-source fallback"
    await click_row(pg, 1, "deep.json")
    await pg.wait_for_selector(".pv-text:not(.pv-json)")
    assert (await pg.inner_text(".pv-text")).startswith("[[[["), (
        "JSON nested past the stack is shown as source, not an error"
    )


async def test_auto_preview(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    await pg.click('.col[data-i="1"] .row:has-text("docs")')
    await pg.wait_for_function(
        "sel[2] === 'README' && document.querySelector('#preview .col-head .name')?.textContent.includes('README')"
    )
    st = await pg.evaluate("__state()")
    assert st["sel"] == ["mixed", "docs", "README"] and st["focusCol"] == 1, json.dumps(
        st
    )
    assert (
        await pg.get_attribute('.col[data-i="2"].descendant .row.sel', "title")
        == "README"
    ), "…dash-selected in the contents column"
    assert "README" in await pg.inner_text("#preview .col-head .name"), (
        "…and named in the preview header"
    )
    await pg.keyboard.press("ArrowRight")
    await pg.wait_for_function("focusCol === 2")
    assert (
        await pg.evaluate("focusCol") == 2 and await pg.evaluate("sel[2]") == "README"
    ), "→ enters the column on the auto-previewed row"
    await pg.keyboard.press("ArrowLeft")
    await pg.wait_for_function("focusCol === 1")
    await pg.click('.col[data-i="1"] .row:has-text("site")')
    await pg.wait_for_function("sel[2] === 'README.md'")
    assert await pg.evaluate("sel[2]") == "README.md", "README.* wins over index.html"
    await pg.click('.col[data-i="1"] .row:has-text("web")')
    await pg.wait_for_function(
        "sel[2] === 'index.html' && document.querySelector('iframe.pv-html')"
    )
    assert await pg.evaluate("sel[2]") == "index.html" and await pg.is_visible(
        "iframe.pv-html"
    ), "index.html previews when no README exists"


async def test_settings(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    # An 88-column preview folds the walked-past root column here; open
    # its spine first, as a user would, before clicking a row in it.
    await pg.evaluate("document.querySelector('.col.spine')?.click()")
    await scroll_settled(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    before = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length")
    await pg.click("#gear")
    await pg.click("#s-dot")
    await pg.wait_for_function(
        "state.dotfiles && document.querySelector('.row[title=\".dotfile\"]')"
    )
    after = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length")
    assert after == before + 1, f"{before}→{after}"
    # The Previews group starts hidden and only preview-rich.js (loaded in
    # this build) reveals it — a build without the toggle shows no heading.
    assert await pg.evaluate(
        "!document.getElementById('s-previews').hidden"
        " && !document.getElementById('s-rich').hidden"
    ), "Previews group is revealed with its rich toggle"
    await pg.click("#s-density")
    await pg.wait_for_function(
        "getComputedStyle(document.querySelector('.row')).height === '26px'"
    )
    assert (
        await pg.evaluate("getComputedStyle(document.querySelector('.row')).height")
        == "26px"
    ), "Density toggle changes row height"
    await pg.click("#s-theme")
    await pg.wait_for_function("root.dataset.theme === 'dark'")
    assert await pg.evaluate(
        "document.documentElement.dataset.theme"
    ) == "dark" and await pg.evaluate("!!document.querySelector('.ico.seti')"), (
        "Dark theme re-colours the icons (cache invalidated)"
    )
    for b_id in ("#s-theme", "#s-density", "#s-dot"):
        await pg.click(b_id)
    await pg.keyboard.press("Escape")


async def test_remount_discards_pending_document_choice(page):
    await mount(page)
    await page.click('.col[data-i="0"] .row:has-text("search")')
    await page.wait_for_function("path[1]?.name === 'search' && path[1]?.kids")
    await page.evaluate("""() => {
        const node = path[1].kids.find(n => n.name === 'release-notes.md');
        window.__oldDocument = node;
        const load = FS.ensureLoaded;
        FS.ensureLoaded = n => n === node
            ? new Promise(resolve => { window.__decline = () => {
                node.dir = false;
                node.kids = undefined;
                resolve();
            }; }) : load(n);
        // Control the grace boundary, rather than racing a real-time delay.
        const timer = window.setTimeout;
        window.setTimeout = (callback, ms, ...args) => {
            if (ms === 50) {
                window.__openGrace = callback;
                return 0;
            }
            return timer(callback, ms, ...args);
        };
        window.__pendingChoice = choose(1, node);
        window.setTimeout = timer;
    }""")
    await page.evaluate("mount(__mk(0))")
    await page.evaluate("__openGrace()")
    # The grace continuation runs before the next browser round-trip.
    await page.evaluate("async () => { __decline(); await __pendingChoice; }")
    assert await page.evaluate("path.map(n => n.name)") == ["workspace"]
    assert await page.evaluate("sel") == []
    assert await page.evaluate("focusCol") == 0
    assert not await page.evaluate("__oldDocument.dir")


async def test_remount_stops_pending_path_walk(page):
    await mount(page)
    # The old root's URL names a folder, so a stale one is told from the new.
    await page.evaluate("applyPath(['deep'])")
    assert "p=deep" in await page.evaluate("location.hash")
    await page.evaluate("""() => {
        const node = path[0].kids.find(n => n.name === 'mixed');
        const load = FS.ensureLoaded;
        window.__reached = new Promise(reached => {
            FS.ensureLoaded = n => n === node
                ? new Promise(resolve => {
                    window.__release = () => load(n).then(resolve);
                    reached();
                }) : load(n);
        });
        window.__walk = applyPath(['mixed', 'sub', 'a.py'], 2);
    }""")
    await page.evaluate("__reached")
    await page.evaluate("mount(__mk(0))")
    snapshot = """() => ({path: path.map(n => n.name), sel: [...sel],
                         focusCol, url: location.href})"""
    mounted = await page.evaluate(snapshot)
    # Every read from here on goes through the port the new root uses.
    await page.evaluate("""() => {
        window.__reads = [];
        const load = FS.ensureLoaded;
        FS.ensureLoaded = n => { __reads.push(n.name); return load(n); };
    }""")
    walked = await page.evaluate("async () => { __release(); return await __walk; }")
    after = await page.evaluate(snapshot)
    reads = await page.evaluate("__reads")
    assert (walked, after, reads) == (False, mounted, [])
    assert after["url"].endswith("#r=workspace"), "the URL names the new root"


async def test_typeahead(page):
    pg = page
    marks = (
        "[...document.querySelectorAll('.col[data-i=\"1\"] .row mark')]"
        ".map(m => m.textContent)"
    )

    async def in_search():
        """Focus the `search` column — type-ahead runs on the focused one."""
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("search")')
        await pg.wait_for_function("path[1]?.name === 'search' && path[1]?.kids")
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_function("focusCol === 1")

    await in_search()
    await pg.keyboard.type("re")
    await pg.wait_for_function("sel[1] === 'readme.md'")
    # One round-trip, not three: every assertion made between the two typed
    # groups below is time the 1.2 s buffer is running down, and a suite
    # that spends it fails on a feature that works.
    snap = await pg.evaluate(
        f"({{sel: sel[1], marks: {marks},"
        " find: document.getElementById('st-find').textContent})"
    )
    assert snap["sel"] == "readme.md", snap["sel"]
    assert snap["marks"] == ["re"], str(snap["marks"])
    assert snap["find"].strip() == "⌕ re", snap["find"]

    # Within the idle window the buffer keeps growing: "re" + "l" is one
    # search for "rel", not a fresh search for "l".
    await pg.keyboard.type("l")
    await pg.wait_for_function("sel[1] === 'release-notes.md'")
    assert await pg.evaluate("sel[1]") == "release-notes.md", await pg.evaluate(
        "sel[1]"
    )
    await pg.wait_for_function("!document.querySelector('#st-find').textContent.trim()")
    await pg.keyboard.type("c")
    await pg.wait_for_function("sel[1] === 'changelog.md'")
    assert await pg.evaluate("sel[1]") == "changelog.md", await pg.evaluate("sel[1]")

    await in_search()
    await pg.keyboard.type("notes")
    await pg.wait_for_function("sel[1] === 'notes.txt'")
    assert await pg.evaluate("sel[1]") == "notes.txt", await pg.evaluate("sel[1]")

    await in_search()
    await pg.keyboard.type("log")
    await pg.wait_for_function("sel[1] === 'changelog.md'")
    assert await pg.evaluate("sel[1]") == "changelog.md", await pg.evaluate("sel[1]")

    await in_search()
    await pg.keyboard.type("arp")
    await pg.wait_for_function("sel[1] === 'Alpha Report.txt'")
    assert await pg.evaluate("sel[1]") == "Alpha Report.txt", await pg.evaluate(
        "sel[1]"
    )
    assert await pg.evaluate(marks) == ["A", "R", "p"], str(await pg.evaluate(marks))

    await in_search()
    await pg.keyboard.type("zz")
    await pg.wait_for_function(
        "document.querySelector('#st-find').textContent.includes('no match')"
    )
    assert await pg.evaluate(
        "sel[1]"
    ) == "Alpha Report.txt" and "no match" in await pg.inner_text("#st-find"), (
        await pg.inner_text("#st-find")
    )
    # Backspace has to undo a typo, so a failed search keeps its buffer.
    await pg.keyboard.press("Backspace")
    await pg.keyboard.press("Backspace")
    await pg.keyboard.type("re")
    await pg.wait_for_function("sel[1] === 'readme.md'")
    assert await pg.evaluate("sel[1]") == "readme.md", await pg.evaluate("sel[1]")

    await in_search()
    await pg.keyboard.type("re")
    await pg.wait_for_function("sel[1] === 'readme.md'")
    await pg.keyboard.press("Escape")
    await pg.wait_for_function(
        "!document.querySelector('mark') && !document.querySelector('#st-find').textContent.trim()"
    )
    assert (
        not await pg.evaluate(marks) and not (await pg.inner_text("#st-find")).strip()
    ), "Escape abandons the search and clears the marks"

    await in_search()
    await pg.keyboard.type("re")
    await pg.wait_for_function("sel[1] === 'readme.md'")
    await pg.keyboard.press("ArrowDown")
    await pg.wait_for_function(
        "sel[1] === 'release-notes.md' && !document.querySelector('mark')"
    )
    assert await pg.evaluate("sel[1]") == "release-notes.md" and not await pg.evaluate(
        marks
    ), await pg.evaluate("sel[1]")

    await in_search()
    await pg.keyboard.press("Control+r")  # a browser shortcut, not a search
    await pg.wait_for_function("!document.querySelector('#st-find').textContent.trim()")
    assert (
        await pg.evaluate("sel[1]") == "Alpha Report.txt"
        and not (await pg.inner_text("#st-find")).strip()
    ), await pg.evaluate("sel[1]")


async def test_copy_path(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    await mount(pg)
    await pg.evaluate("__clip(false)")
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("path[1]?.name === 'mixed' && path[1]?.kids")
    await pg.click('.col[data-i="1"] .row:has-text("note.md")')
    await pg.wait_for_function(
        "document.querySelector('#st-path').textContent === 'mixed/note.md'"
    )
    assert await pg.inner_text("#st-path") == "mixed/note.md", await pg.inner_text(
        "#st-path"
    )
    await pg.keyboard.press("Control+c")
    await pg.wait_for_function(
        "__clipped.length === 1 && document.querySelector('#st-copy').textContent.includes('Copied')"
    )
    assert await pg.evaluate("__clipped") == ["mixed/note.md"], str(
        await pg.evaluate("__clipped")
    )
    assert (await pg.inner_text("#st-copy")).strip() == "Copied mixed/note.md", (
        "A copy that worked says so"
    )

    await pg.evaluate("__clip(false)")
    await pg.click("#st-path")
    await pg.wait_for_function("__clipped.length === 1")
    assert await pg.evaluate("__clipped") == ["mixed/note.md"], str(
        await pg.evaluate("__clipped")
    )

    # The clipboard API can be refused, and a refusal that says nothing is
    # worse than no button: the next paste hands over something else.
    await pg.evaluate("__clip(true)")
    await pg.click("#st-path")
    await pg.wait_for_function(
        "document.querySelector('#st-copy').textContent.includes('refused')"
    )
    note = await pg.inner_text("#st-copy")
    assert "refused" in note, note
    assert (
        await pg.get_by_label("Text to copy", exact=True).input_value()
        == "mixed/note.md"
    )


async def test_refresh(page):
    pg = page
    # Nothing here touches a real folder: what changes is the fake handle's
    # entry list. test-e2e.py runs the real-disk version, against a
    # temporary directory it creates and deletes itself.
    rows1 = '.col[data-i="1"] .row'

    async def in_refresh():
        """Mount fresh and focus the `refresh` column (row 0 = the `sub` folder)."""
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("refresh")')
        await pg.wait_for_function("path[1]?.name === 'refresh' && path[1]?.kids")
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_function("focusCol === 1 && sel[1] === 'sub'")

    await in_refresh()
    before = await pg.eval_on_selector_all(rows1, "e=>e.length")
    await pg.evaluate("__add(__live, 'three.txt')")

    assert await pg.eval_on_selector_all(rows1, "e=>e.length") == before, (
        "no watch API exists — which is the whole reason refresh is manual"
    )
    await pg.evaluate("window.__sentinel = 42")
    await pg.keyboard.press("F5")
    await pg.wait_for_function(
        "document.querySelector('#st-refresh').textContent.includes('1 new')"
    )
    snap = await pg.evaluate(
        "({...__state(), rows: colCache.get(path[1]).rows.length,"
        " sentinel: window.__sentinel,"
        " say: document.getElementById('st-refresh').textContent})"
    )
    assert snap["rows"] == before + 1, f"{before}→{snap['rows']}"
    assert snap["sentinel"] == 42, (
        f"page marker {snap['sentinel']}, 42 means the page survived"
    )
    assert (
        snap["sel"] == ["refresh", "sub"]
        and snap["focusCol"] == 1
        and snap["path"] == ["workspace", "refresh", "sub"]
    ), json.dumps(snap)
    assert snap["say"].strip() == "⟳ 1 new, 0 gone", snap["say"]

    await in_refresh()
    before = await pg.eval_on_selector_all(rows1, "e=>e.length")
    await pg.evaluate("__add(__live, 'four.txt')")
    await pg.click('.col[data-i="1"] .col-head .rf')
    await pg.wait_for_function(
        "document.querySelector('#st-refresh').textContent.includes('1 new')"
    )
    assert await pg.eval_on_selector_all(rows1, "e=>e.length") == before + 1, (
        "The ⟳ button on the column header does the same job as F5"
    )

    # The button has to be *painted* on the focused column, not merely
    # present. `folding` is not a transient state — layout.js puts it on
    # column `folded`, which at rest is the root — so a rule keyed on it hid
    # the button on the root for ever, and on whichever column the dial was
    # mid-fold on. Park the pointer first: `.col:hover` would otherwise show
    # the button and hide the bug, which is exactly why it read as a
    # keyboard-only fault.
    await mount(pg)
    await pg.mouse.move(1499, 899)
    await pg.wait_for_function(
        "document.querySelector('.col[data-i=\"0\"].focus .rf').getBoundingClientRect().width > 0"
    )
    root_col = await pg.evaluate(
        "({cls: document.querySelector('.col[data-i=\"0\"]').className,"
        " w: document.querySelector('.col[data-i=\"0\"] .col-head .rf')"
        "     .getBoundingClientRect().width})"
    )
    assert root_col["w"] > 0 and "focus" in root_col["cls"], (
        f"class={root_col['cls']!r}, painted width {root_col['w']}"
    )
    assert "folding" in root_col["cls"], root_col["cls"]

    # …and after ← lands focus on a column the dial is folding.
    await pg.set_viewport_size({"width": 760, "height": 700})
    await pg.keyboard.press("Home")
    await pg.wait_for_function("sel[0] === 'big'")
    await pg.keyboard.press("ArrowDown")  # "deep"
    await pg.wait_for_function("sel[0] === 'deep' && path[1]?.kids")
    for depth in range(1, 5):  # walk to the leaf
        await pg.keyboard.press("ArrowRight")
        await pg.wait_for_function(
            "depth => focusCol === depth && colCache.get(path[depth])?.rows.length",
            arg=depth,
        )
    await pg.mouse.move(759, 699)
    painted = []
    landed = []
    for _ in range(4):  # and back out again
        st = await pg.evaluate(
            "(() => { const el = document.querySelector('.col.focus');"
            " const rf = el && el.querySelector('.col-head .rf');"
            " return {cls: el && el.className,"
            "         w: rf ? rf.getBoundingClientRect().width : -1}; })()"
        )
        painted.append((st["cls"], st["w"]))
        await pg.keyboard.press("ArrowLeft")
        await scroll_settled(pg)
        landed.append(
            await pg.evaluate(
                "(() => { const el = document.querySelector('.col.focus');"
                " return {f: focusCol, d: folded, sp: parseInt(getComputedStyle(document.documentElement).getPropertyValue('--spine-w')),"
                "         w: Math.round(el.getBoundingClientRect().width)}; })()"
            )
        )
    assert all(w > 0 for _, w in painted), "; ".join(f"{c}→{w}" for c, w in painted)
    # The dial lands on round(k·unit·range), up to half a pixel short of the
    # boundary. Read with too small a slack that is one column *fewer*
    # folded, t ≈ 1: the column just reached paints as a spine, and since
    # folded === focusCol the next ← has nothing left to unfold. Measured
    # here, in this fixture at 760 px, on the second ← before the fix.
    assert all(s["d"] == s["f"] and s["w"] > s["sp"] for s in landed), "; ".join(
        f"focus {s['f']} folded {s['d']} {s['w']}px" for s in landed
    )
    await pg.set_viewport_size({"width": 1500, "height": 900})
    await scroll_settled(pg)

    # A re-read replaces every node object in the column, including the one
    # whose preview is on screen. The guard is pvToken, the same counter a
    # slow file read already answers to: the re-render starts a new fill,
    # which retires the old one wherever it had got to.
    await in_refresh()
    await pg.keyboard.press("ArrowDown")  # one.txt, contents "1"
    await pg.wait_for_function(
        "sel[1] === 'one.txt' && document.querySelector('.pv-text')?.textContent.trim() === '1'"
    )
    was = await pg.evaluate("pvToken")
    await pg.keyboard.press("F5")
    await pg.wait_for_function(
        "old => pvToken > old && document.querySelector('.pv-text')?.textContent.trim() === '1' && document.querySelector('#st-refresh').textContent.includes('no change')",
        arg=was,
    )
    now = await pg.evaluate("pvToken")
    body = (await pg.inner_text(".pv-text")).strip()
    assert now > was and body == "1" and await pg.evaluate("sel[1]") == "one.txt", (
        f"pvToken {was}→{now}, preview {body!r}"
    )

    # The entry you were on is gone. Selecting whatever slid into its place
    # would show a preview of a file nobody asked for, so nothing is
    # selected — and the unified name selection must not move to whatever
    # row slid into its place.
    await in_refresh()
    for _ in range(2):
        await pg.keyboard.press("ArrowDown")
        await pg.wait_for_function(
            "!document.querySelector('.spinner') && document.querySelector('.pv-text')"
        )
    assert await pg.evaluate("sel[1]") == "two.txt", await pg.evaluate("sel[1]")
    await pg.evaluate("__rm(__live, 'two.txt')")
    await pg.keyboard.press("F5")
    await pg.wait_for_function(
        "sel.length === 1 && document.querySelector('#st-refresh').textContent.includes('two.txt is gone')"
    )
    snap = await pg.evaluate(
        "({...__state(), say: document.getElementById('st-refresh').textContent})"
    )
    assert (
        snap["sel"] == ["refresh"]
        and snap["focusCol"] == 1
        and "two.txt is gone" in snap["say"]
    ), json.dumps(snap)
    await pg.keyboard.press("ArrowDown")
    await pg.wait_for_function("sel[1] === 'sub' && path[2]?.kids")
    assert await pg.evaluate("sel[1]") == "sub", await pg.evaluate("sel[1]")

    # Refreshing a parent must not quietly throw away the columns to its
    # right. A re-read hands back new node objects, so the chain is walked
    # again by name rather than kept by identity.
    async def deep_chain():
        await mount(pg)
        await pg.click('.col[data-i="0"] .row:has-text("refresh")')
        await pg.wait_for_function("path[1]?.name === 'refresh' && path[1]?.kids")
        for depth in range(1, 4):  # → sub → twig → tip.txt
            await pg.keyboard.press("ArrowRight")
            await pg.wait_for_function(
                "depth => focusCol === depth && colCache.get(path[depth])?.rows.length",
                arg=depth,
            )
        for depth in (2, 1):  # ← back out to the `refresh` column
            await pg.keyboard.press("ArrowLeft")
            await pg.wait_for_function("depth => focusCol === depth", arg=depth)

    await deep_chain()
    await pg.keyboard.press("F5")
    await pg.wait_for_function(
        "document.querySelector('#st-refresh').textContent.includes('no change')"
    )
    st = await pg.evaluate("__state()")
    assert st["path"] == ["workspace", "refresh", "sub", "twig"] and st["sel"] == [
        "refresh",
        "sub",
        "twig",
        "tip.txt",
    ], json.dumps(st)
    assert st["focusCol"] == 1, str(st["focusCol"])

    await deep_chain()
    await pg.evaluate("__rm(__live, 'sub')")
    await pg.keyboard.press("F5")
    await pg.wait_for_function(
        "path.length === 2 && document.querySelector('#st-refresh').textContent.includes('sub is gone')"
    )
    snap = await pg.evaluate(
        "({...__state(), say: document.getElementById('st-refresh').textContent})"
    )
    assert (
        snap["path"] == ["workspace", "refresh"]
        and snap["sel"] == ["refresh"]
        and snap["focusCol"] == 1
        and "sub is gone" in snap["say"]
    ), json.dumps(snap)

    # The race the pvToken/ensureLoaded reuse exists for. `racing` snapshots
    # its entries before a 400 ms wait, so a refresh that simply re-entered
    # ensureLoaded would be handed the in-flight promise and win the *old*
    # listing — two reads, one field, and the wrong one landing last.
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("racing")')
    await pg.wait_for_function("path[1]?.loading")
    await pg.evaluate("__add(__race, 'charlie.txt')")
    await pg.evaluate("refreshColumn(1)")
    await pg.wait_for_function("!path[1]?.loading && path[1]?.kids.length === 3")
    got = await pg.eval_on_selector_all(rows1, "e=>e.map(x=>x.title)")
    head = (await pg.inner_text('.col[data-i="1"] .count')).strip()
    assert (
        got == ["alpha.txt", "bravo.txt", "charlie.txt"]
        and head == "3"
        and await pg.evaluate("path[1].loading") is None
    ), f"{got}, header says {head}"

    # Refreshing the root replaces its nodes and restores the open chain.
    # A subsequent click must replace that chain completely, leaving every
    # open column as the child selected by the level above it. evaluate()
    # awaits refreshColumn's promise; this checks navigation after refresh.
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("slow")')
    await pg.wait_for_function("path[1]?.name === 'slow' && path[1]?.kids")
    await pg.keyboard.press("ArrowRight")
    await pg.wait_for_function("focusCol === 1")
    await pg.evaluate("refreshColumn(0)")
    await pg.wait_for_function(
        "path[1]?.name === 'slow' && path[1]?.kids && !document.querySelector('.col.busy')"
    )
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function(
        "path.length === 2 && path[1]?.name === 'mixed' && sel[1] === 'README'"
    )
    st = await pg.evaluate("__state()")
    coherent = all(
        st["sel"][i] == st["path"][i + 1] for i in range(len(st["path"]) - 1)
    )
    assert (
        st["path"] == ["workspace", "mixed"]
        and st["sel"] == ["mixed", "README"]
        and coherent
    ), json.dumps(st)


# A refresh can end on an instant dial write and a glide towards the resting
# place it computed, the glide queued for the next frame or started but not yet
# moved. The new root's resting place is where the dial already sits, so a
# mount in that window issued no scroll of its own, the old glide landed, and
# the focused root folded into a spine: test_refresh's next click then waited
# 30 s on a hidden row (CI run 39292689552).
GLIDES = {
    "queued": "dialTo(0, false); dialTo(fold, true); return mount(__mk(0));",
    "started": """dialTo(0, false);
      return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => {
        dialTo(fold, true); r(mount(__mk(0))); })));""",
}


@pytest.mark.parametrize("glide", list(GLIDES))
async def test_mount_stops_a_glide_that_would_fold_the_root(page, glide):
    pg = page
    await mount(pg)
    await pg.evaluate(
        "body => new Function('fold', body)(Math.round(foldUnit() * range()))",
        GLIDES[glide],
    )
    await pg.wait_for_function("path.length === 1 && colCache.get(path[0])")
    await scroll_settled(pg)
    st = await pg.evaluate(
        "({folded, dial: dial(), cls: document.querySelector('.col[data-i=\"0\"]').className})"
    )
    assert st["folded"] == 0 and "spine" not in st["cls"], json.dumps(st)
    await pg.click('.col[data-i="0"] .row:has-text("refresh")')
    await pg.wait_for_function("path[1]?.name === 'refresh'")


async def test_sort_options(page):
    pg = page
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
        await pg.wait_for_function("path[1]?.name === 'sorting' && path[1]?.kids")

    await in_sorting()
    gets = await pg.evaluate("__gets")
    assert await pg.evaluate("__rows(1)") == NAME_ASC and gets == 0, (
        f"{gets} getFile() calls — a name is already in the listing"
    )

    await pg.evaluate("setSort('size', false)")
    await pg.wait_for_function(
        "path.every(n => n.metaDone) && !document.querySelector('.col.sorting')"
    )
    gets = await pg.evaluate("__gets")
    # 4 files in `sorting` and 1 (README.md) in the root column beside it.
    # The other nine directories in the tree are not on screen and are not
    # touched: the sweep covers what is displayed, not what exists.
    assert await pg.evaluate("__rows(1)") == SIZE_ASC and gets == 5, (
        f"{gets} reads: 4 files here, 1 in the root column, 0 elsewhere"
    )

    await pg.evaluate("render(true)")
    await pg.wait_for_function("!path.some(n => n.metaLoading)")
    assert await pg.evaluate("__gets") == gets, (
        f"{await pg.evaluate('__gets') - gets} extra reads"
    )

    await pg.evaluate("setSort('size', true)")
    await pg.wait_for_function("__rows(1)[2] === 'big.bin'")
    desc = await pg.evaluate("__rows(1)")
    assert desc == SIZE_DESC and await pg.evaluate("__gets") == gets, str(desc)
    assert (
        SIZE_ASC[-1] == "locked.txt" and desc[-1] == "locked.txt" and len(desc) == 6
    ), "biggest-first must not answer with a file nobody could open"

    await pg.evaluate("setSort('mtime', false)")
    await pg.wait_for_function("__rows(1)[2] === 'medium.md'")
    assert (
        await pg.evaluate("__rows(1)") == MTIME_ASC
        and await pg.evaluate("__gets") == gets
    ), "getFile() hands back the size and the mtime together"

    await pg.evaluate("setSort('name', true)")
    await pg.wait_for_function("__rows(1)[0] === 'zeta'")
    assert await pg.evaluate("__rows(1)") == NAME_DESC, (
        "no port can give a directory a size or an mtime"
    )

    await pg.evaluate("setSort('name', false)")
    await pg.click("#gear")
    await pg.click("#s-sort-size")
    await pg.wait_for_function("__rows(1)[2] === 'small.txt'")
    ticked = await pg.evaluate(
        "['name', 'size', 'mtime'].map(k => document.getElementById('s-sort-'+k)"
        ".getAttribute('aria-checked'))"
    )
    assert await pg.evaluate("__rows(1)") == SIZE_ASC and ticked == [
        "false",
        "true",
        "false",
    ], str(ticked)
    await pg.click("#s-sort-desc")
    await pg.wait_for_function("__rows(1)[2] === 'big.bin'")
    assert (
        await pg.evaluate("__rows(1)") == SIZE_DESC
        and await pg.evaluate(
            "document.getElementById('s-sort-desc').getAttribute('aria-checked')"
        )
        == "true"
    ), "…and the direction is a separate switch that applies to that key"

    # Remembered in localStorage rather than in the per-folder record: the
    # sort is how a person reads a list, not a property of the folder.
    assert await pg.evaluate("localStorage.getItem('filemill.sort')") == "size:desc", (
        await pg.evaluate("localStorage.getItem('filemill.sort')")
    )
    await pg.evaluate("state.sort = {key:'name', desc:false}; loadSort()")
    assert (
        await pg.evaluate("JSON.stringify(state.sort)") == '{"key":"size","desc":true}'
    ), await pg.evaluate("JSON.stringify(state.sort)")

    # The cursor is a row *index*, and a re-sort moves the row it named.
    # small.txt sits at row 2 ascending and row 4 descending, so a cursor
    # left behind would put ↓ on medium.md instead of locked.txt.
    await in_sorting()
    await pg.evaluate("setSort('size', false)")
    await pg.wait_for_function(
        "path.every(n => n.metaDone) && !document.querySelector('.col.sorting')"
    )
    await pg.keyboard.press("ArrowRight")
    await pg.wait_for_function("focusCol === 1")
    await pg.click('.col[data-i="1"] .row:has-text("small.txt")')
    await pg.wait_for_function("sel[1] === 'small.txt'")
    await pg.evaluate("setSort('size', true)")
    await pg.wait_for_function("__rows(1)[2] === 'big.bin'")
    await pg.keyboard.press("ArrowDown")
    await pg.wait_for_function("sel[1] === 'locked.txt'")
    assert await pg.evaluate("sel[1]") == "locked.txt", await pg.evaluate("sel[1]")

    # A refresh lands while the sweep is still reading. Those metadata reads
    # are about objects the new listing no longer contains, so the sweep
    # must not mark the new one done — and the app has to notice and ask
    # again rather than sit on a half-ordered column.
    await pg.evaluate("setSort('name', false)")
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("refresh")')
    await pg.wait_for_function("path[1]?.name === 'refresh' && path[1]?.kids")
    await pg.evaluate("__slowMeta(400)")
    await pg.evaluate("setSort('size', false)")
    await pg.wait_for_function("path.some(n => n.metaLoading)")
    await pg.evaluate("__add(__live, 'zero.txt')")  # 8 bytes; one/two are 1
    await pg.evaluate("refreshColumn(1)")
    await pg.wait_for_function(
        "path[1]?.metaDone && !document.querySelector('.col.sorting')"
    )
    rows = await pg.evaluate("__rows(1)")
    assert (
        rows == ["sub", "one.txt", "two.txt", "zero.txt"]
        and await pg.evaluate("path[1].metaDone") is True
        and await pg.eval_on_selector_all(".col.sorting", "e=>e.length") == 0
    ), str(rows)
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
    await pg.wait_for_function("document.querySelector('.col.sorting')")
    spinning = await pg.eval_on_selector_all(".col.sorting", "e=>e.length")
    say = (await pg.inner_text("#st-sort")).strip()
    # 5 files, which is exactly the getFile() count the check above pinned:
    # the strip counts calls outstanding, not entries in view.
    assert spinning > 0 and "reading 5 files" in say, (
        f"{spinning} columns spinning, strip says {say!r}"
    )
    await pg.wait_for_function("!path.some(n => n.metaLoading)", timeout=30_000)
    await pg.wait_for_function(
        "!document.querySelector('.col.sorting') && document.querySelector('#st-sort').textContent.includes('sorting: 4 files read in')"
    )
    say = (await pg.inner_text("#st-sort")).strip()
    assert (
        "size" in say
        and "sorting: 4 files read in" in say
        and await pg.eval_on_selector_all(".col.sorting", "e=>e.length") == 0
    ), say

    # The race the design has to survive: the sweep is slow, and the user
    # walks off before it lands.
    await in_sorting()
    await pg.evaluate("__slowMeta(500)")
    await pg.evaluate("setSort('size', false)")
    await pg.wait_for_function("path.some(n => n.metaLoading)")
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function(
        "!path.some(n => n.metaLoading) && path[0].kids.find(n => n.name === 'sorting').metaDone && sel[1] === 'README'"
    )
    st = await pg.evaluate("__state()")
    coherent = all(
        st["sel"][i] == st["path"][i + 1] for i in range(len(st["path"]) - 1)
    )
    assert (
        st["path"] == ["workspace", "mixed"]
        and st["sel"] == ["mixed", "README"]
        and coherent
    ), json.dumps(st)

    await pg.evaluate("__slowMeta(0)")
    gets = await pg.evaluate("__gets")
    await pg.click('.col[data-i="0"] .row:has-text("sorting")')
    await pg.wait_for_function("path[1]?.name === 'sorting' && path[1]?.metaDone")
    again = await pg.evaluate("__gets") - gets
    assert await pg.evaluate("__rows(1)") == SIZE_ASC and again == 0, (
        f"{again} further getFile() calls"
    )

    # A port that rejects instead of recording the error would otherwise
    # leave metaLoading set for good, and the column would spin until the
    # tab closed.
    await in_sorting()
    await pg.evaluate("__brokenMeta()")
    await pg.evaluate("setSort('size', false)")
    await pg.wait_for_function(
        "path[1]?.metaDone && !document.querySelector('.col.sorting')"
    )
    rows = await pg.evaluate("__rows(1)")
    assert (
        await pg.eval_on_selector_all(".col.sorting", "e=>e.length") == 0
        and sorted(rows) == sorted(NAME_ASC)
        and await pg.evaluate("path[1].metaDone") is True
    ), f"{len(rows)} rows, metaDone {await pg.evaluate('path[1].metaDone')}"
    await pg.evaluate("__slowMeta(0); setSort('name', false)")


async def test_render_cost(page):
    pg = page
    # Generous ceilings: they exist to catch the O(entries)-per-keystroke
    # regression (which cost 500–740 ms), not to benchmark a loaded machine.
    for n, budget in ((1000, 100), (3000, 100)):
        await mount(pg, n)
        await pg.click('.col[data-i="0"] .row:has-text("big")')
        await pg.wait_for_function(
            "colCache.get(path[1]) && colCache.get(path[1]).rows.length > 0",
            timeout=30_000,
        )
        await pg.wait_for_function("!document.querySelector('.spinner')")
        dom_rows = await pg.eval_on_selector_all('.col[data-i="1"] .row', "e=>e.length")
        assert dom_rows < n if n >= 1000 else dom_rows == n, f"{dom_rows} DOM rows"
        ms = await pg.evaluate(
            "(() => { const t=performance.now(); render(true);"
            "return +(performance.now()-t).toFixed(1); })()"
        )
        key = await pg.evaluate("__keybench(20)")
        assert ms < budget and key < budget, (
            f"{n:,} entries: re-render {ms} ms, keystroke {key} ms (budget {budget} ms)"
        )
        # Type-ahead runs on every letter, so it needs its own ceiling. What
        # to bound is the cost of the *search*, not the cost of the row it
        # lands on: picking a file out of a 3 000-entry directory builds a
        # preview and re-renders, ~60 ms here, whether an arrow key or a
        # letter asked for it. Measuring both in the same column separates
        # the two — __keybench walked 20 rows down the root column, so the
        # big directory has to be re-opened before stepping in.
        await pg.click('.col[data-i="0"] .row:has-text("big")')
        await pg.wait_for_function(
            "colCache.get(path[1]) && colCache.get(path[1]).rows.length > 0",
            timeout=30_000,
        )
        await pg.wait_for_function(
            "sel[0] !== null && !document.querySelector('.spinner')"
        )
        await pg.keyboard.press("ArrowRight")  # focus the big column
        await pg.wait_for_function(
            "focusCol === 1 && colCache.get(path[1])?.rows.length > 0"
        )
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
            " return +((performance.now()-t)/20).toFixed(2); })()"
        )
        assert (
            find < 25
            and miss["ms"] < budget
            and hit["ms"] < arrow + budget
            and hit["rows"] == n
            and miss["rows"] == n
        ), f"searched {hit['rows']} rows, expected {n}"

        # Refresh is the one action that throws a cached column away on
        # purpose: the entry list really did change, so the DOM has to be
        # rebuilt. Its price is therefore the build price the cache exists
        # to avoid paying per keystroke — once, when the user asks. What
        # matters is that it is not on the keystroke path, so the assertion
        # is on the arrow key measured *after* it, not on the refresh.
        rf = await pg.evaluate(
            "(async () => { const t = performance.now();"
            " await refreshColumn(focusCol);"
            " return +(performance.now()-t).toFixed(1); })()"
        )
        after = await pg.evaluate("__keybench(20)")
        assert (
            after < budget
            and await pg.evaluate("colCache.get(path[focusCol]).rows.length") == n
        ), f"keystroke {after} ms after a {rf} ms refresh"

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
        await pg.wait_for_function("!path.some(n => n.metaLoading)")
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
            " return colCache.get(path[focusCol]) === c; })()"
        )
        assert (
            swept_key < arrow + budget
            and kept
            and sweep["reads"] == n
            and sweep["rows"] == n
        ), (
            f"{sweep['reads']} reads for {sweep['rows']} rows, "
            f"column {'kept' if kept else 'REBUILT'}"
        )
        await pg.evaluate("setSort('name', false)")


async def test_theme(browser, bundle):
    for scheme, expected in (("dark", "dark"), ("light", "light")):
        ctx = await browser.new_context(color_scheme=scheme)
        themed = await ctx.new_page()
        await themed.goto(bundle.as_uri())
        assert await themed.evaluate("root.dataset.theme") == expected, (
            f"OS {scheme} scheme selects {expected} theme"
        )
        assert (
            await themed.get_attribute("#s-theme", "aria-checked")
            == str(expected == "dark").lower()
        ), f"OS {scheme} scheme updates theme accessibility state"
        assert await themed.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--chrome').trim()"
        ) == ("#1b1d21" if expected == "dark" else "#e7e7ec"), (
            f"OS {scheme} scheme selects the matching palette"
        )
        # No folder is mounted here, so #welcome covers the chrome and a
        # pointer click never reaches the toolbar; dispatch it directly.
        await themed.locator("#gear").dispatch_event("click")
        await themed.locator("#s-theme").dispatch_event("click")
        assert await themed.evaluate("root.dataset.theme") != expected, (
            f"Manual toggle overrides {scheme} scheme"
        )
        assert (
            await themed.get_attribute("#s-theme", "aria-checked")
            == str(expected != "dark").lower()
        ), "Manual toggle updates theme accessibility state"
        await ctx.close()


async def test_editor_features(page):
    pg = page
    await pg.evaluate("localStorage.setItem('filemill.rich','off')")
    await pg.evaluate(FAKE)
    await pg.evaluate("mount(__mk(0))")
    await pg.wait_for_function("path.length === 1 && colCache.get(path[0])")
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.click('.col[data-i="1"] .row:has-text("note.md")')
    await pg.wait_for_selector("#pv-edit", state="visible")
    await editor_feature_checks(pg)
    await pg.click("#pv-edit")
    await pg.fill("#pv-editor", "saved editor text")
    assert await pg.is_visible("#pv-modified")
    await pg.click("#pv-save")
    await pg.wait_for_function(
        "document.querySelector('#pv-content').textContent.trim() === 'saved editor text'"
    )
    assert await pg.is_hidden("#pv-modified")
    await pg.click("#pv-edit")
    await pg.wait_for_selector("#pv-editor")
    assert await pg.input_value("#pv-editor") == "saved editor text"
    assert await pg.is_hidden("#pv-modified")


async def preview_spy(pg):
    await pg.evaluate("""() => {
      window.__previewRenders = 0;
      const render = PREVIEW.render.bind(PREVIEW);
      PREVIEW.render = n => { __previewRenders++; return render(n); };
    }""")


async def test_preview_reuse_and_invalidation(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_selector("#pv-edit", state="visible")
    await preview_spy(pg)
    await pg.click('.col[data-i="1"] .row[title="short.txt"]')
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.evaluate("__previewRenders") == 1
    await pg.evaluate("""() => {
      window.__previewPane = document.getElementById('preview');
      window.__previewContent = document.getElementById('pv-content').firstChild;
      window.__previewRaw = document.getElementById('pv-raw').href;
    }""")
    await pg.set_viewport_size({"width": 950, "height": 700})
    await scroll_settled(pg)
    await pg.evaluate("dialTo(range(), false)")
    await scroll_settled(pg)
    assert await pg.evaluate("folded") > 0
    await pg.evaluate("render(true)")
    await scroll_settled(pg)
    assert await pg.evaluate("__previewRenders") == 1
    assert await pg.evaluate("""document.getElementById('preview') === __previewPane &&
      document.getElementById('pv-content').firstChild === __previewContent &&
      document.getElementById('pv-raw').href === __previewRaw""")

    # A save refreshes the retained pane once, then the new metadata is reusable.
    await pg.click("#pv-edit")
    await pg.fill("#pv-editor", "saved preview")
    await pg.click("#pv-save")
    await pg.wait_for_function(
        "document.querySelector('#pv-content').textContent.trim() === 'saved preview'"
    )
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.evaluate("__previewRenders") == 2
    await pg.evaluate("render(true)")
    assert await pg.evaluate("__previewRenders") == 2

    # Both in-place metadata updates and replacement must invalidate.
    for change in ("n.meta.mod++", "n.meta = {...n.meta, size: n.meta.size + 1}"):
        before = await pg.evaluate("__previewRenders")
        await pg.evaluate(
            f"() => {{ const n = path[1].kids.find(n => n.name === 'short.txt'); {change}; render(true); }}"
        )
        await pg.wait_for_selector("#pv-edit", state="visible")
        assert await pg.evaluate("__previewRenders") == before + 1
        await pg.evaluate("render(true)")
        assert await pg.evaluate("__previewRenders") == before + 1

    before = await pg.evaluate("__previewRenders")
    await pg.evaluate("choose(1, path[1].kids.find(n => n.name === 'README'))")
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.evaluate("__previewRenders") == before + 1
    await pg.evaluate("choose(1, path[1].kids.find(n => n.name === 'short.txt'))")
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.evaluate("__previewRenders") == before + 2


async def test_preview_reuses_pending_fill_and_discards_departed_result(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_selector("#pv-edit", state="visible")
    await preview_spy(pg)
    await pg.evaluate("""() => {
      const load = FS.loadMeta.bind(FS);
      FS.loadMeta = async n => {
        if (n.name === 'short.txt') await new Promise(r => { window.__releaseMeta = r; });
        return load(n);
      };
      choose(1, path[1].kids.find(n => n.name === 'short.txt'));
      window.__pendingPane = document.getElementById('preview');
      render(true);
      render(true);
    }""")
    assert await pg.evaluate("document.getElementById('preview') === __pendingPane")
    await pg.evaluate("__releaseMeta()")
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.evaluate("__previewRenders") == 1

    # A read finishing after selection moves to an empty folder must be ignored.
    await pg.evaluate("""() => {
      const render = PREVIEW.render.bind(PREVIEW);
      PREVIEW.render = async n => {
        await new Promise(r => { window.__releasePreview = r; });
        return render(n);
      };
      choose(1, path[1].kids.find(n => n.name === 'README'));
    }""")
    await pg.wait_for_function('typeof __releasePreview === "function"')
    await pg.evaluate("choose(0, path[0].kids.find(n => n.name === 'empty'))")
    await pg.evaluate("__releasePreview()")
    # Await the old provider's completion before checking that it did not paint.
    await pg.wait_for_function("__previewRenders === 2")
    await pg.evaluate("new Promise(requestAnimationFrame)")
    assert await pg.locator("#pv-content").count() == 0
    assert "Select a file to preview" in await pg.locator("#preview").inner_text()


async def test_preview_reuses_pending_editor_save(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.click('.col[data-i="1"] .row[title="short.txt"]')
    await pg.wait_for_selector("#pv-edit", state="visible")
    await preview_spy(pg)
    await pg.click("#pv-edit")
    await pg.fill("#pv-editor", "saved during resize")
    await pg.evaluate("""() => {
      const load = FS.loadMeta.bind(FS);
      FS.loadMeta = async n => {
        await new Promise(r => { window.__releaseSavedMeta = r; });
        return load(n);
      };
      window.__savedPane = document.getElementById('preview');
    }""")
    await pg.click("#pv-save")
    await pg.wait_for_function('typeof __releaseSavedMeta === "function"')
    await pg.evaluate("render(true)")
    assert await pg.evaluate("document.getElementById('preview') === __savedPane")
    await pg.evaluate("__releaseSavedMeta()")
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.locator("#pv-content").inner_text() == "saved during resize"
    assert await pg.evaluate("__previewRenders") == 1


async def test_preview_reuses_document_when_delayed_outline_declines(page):
    pg = page
    await pg.evaluate("""async () => {
      let reads = 0;
      await mount({kind: 'directory', name: 'delayed-document', async *entries() {
        yield ['plain.md', {kind: 'file', name: 'plain.md', async getFile() {
          const file = new File(['# Title only\\n\\nbody'], 'plain.md', {lastModified: 1});
          const text = file.text.bind(file);
          file.text = async () => {
            if (++reads === 1) await new Promise(r => { window.__releaseOutline = r; });
            return text();
          };
          return file;
        }}];
      }});
    }""")
    await preview_spy(pg)
    await pg.click('.row[title="plain.md"]')
    await pg.wait_for_selector("#preview .pv-text")
    assert await pg.evaluate("__previewRenders") == 1
    await pg.evaluate("window.__documentPane = document.getElementById('preview')")
    await pg.evaluate("__releaseOutline()")
    await pg.wait_for_function("!path[0].kids[0].loading && !path[0].kids[0].dir")
    await pg.wait_for_selector("#pv-edit", state="visible")
    assert await pg.evaluate("__previewRenders") == 1
    assert await pg.evaluate("document.getElementById('preview') === __documentPane")


async def test_preview_reuses_pending_provider_that_populates_revision(page):
    pg = page
    await mount(pg)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_selector("#pv-edit", state="visible")
    await pg.evaluate("""() => {
      window.__providerStarts = 0;
      const render = PREVIEW.render.bind(PREVIEW);
      PREVIEW.render = async n => {
        __providerStarts++;
        n.revision = 'read-revision';
        await new Promise(r => { window.__releaseProvider = r; });
        return render(n);
      };
      choose(1, path[1].kids.find(n => n.name === 'short.txt'));
      window.__providerPane = document.getElementById('preview');
    }""")
    await pg.wait_for_function('typeof __releaseProvider === "function"')
    await pg.evaluate("render(true)")
    assert await pg.evaluate("document.getElementById('preview') === __providerPane")
    assert await pg.evaluate("__providerStarts") == 1
    await pg.evaluate("__releaseProvider()")
    await pg.wait_for_selector("#pv-edit", state="visible")
    await pg.evaluate("render(true)")
    assert await pg.evaluate("__providerStarts") == 1


async def test_content_search_uses_granted_folder(page, driver):
    await mount(page)
    search = page.locator("#search-bar")
    if getattr(driver, "native", False):
        assert not await search.is_visible()
        return
    assert await search.is_visible()
    await page.evaluate("applyPath(['mixed', 'sub', 'a.py'])")
    await search.fill("def f():")
    result = page.locator('.search-result[data-path="mixed/sub/a.py"]')
    await result.wait_for()
    await result.press("Enter")
    await page.wait_for_function("sel.join('/') === 'mixed/sub/a.py'")
    assert await page.locator("#search-results").is_hidden()
