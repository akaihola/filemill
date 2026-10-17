"""Deep links and filesystem performance on a loopback HTTP origin."""


# Serve the repository, not filemill/: the dev entry point references ../ui/,
# which is the whole point of the shared directory.

FAKE = r"""
window.__mk = () => {
  const F = (name, text) => ({kind:'file', name,
    getFile: async () => new File([text ?? 'x'], name, {lastModified: Date.parse('2026-08-01')})});
  const D = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  return D('workspace', [
    D('deep',  [D('alpha',[D('beta',[F('leaf.txt','leaf')])])]),
    D('mixed', [D('sub',[F('a.py','print(1)')]), F('.hidden','h'),
                F('note.md','# note'), F('sp ace & co.txt','x')]),
    F('README.md','# hi\n'),
  ]);
};
window.__state = () => ({path: path.map(p=>p.name), sel, focusCol});
"""

# A real directory, built inside the origin private file system. Sizes run
# 1…13 bytes and disagree with the names, so an order by size cannot be the
# order by name wearing a different label.
OPFS_BUILD = r"""
async (n) => {
  const root = await navigator.storage.getDirectory();
  try { await root.removeEntry('bench', {recursive: true}); } catch (e) {}
  const d = await root.getDirectoryHandle('bench', {create: true});
  /* 250 at a time. One at a time takes 25 s for 3 000 files, and this is
     fixture building, not the thing being measured. */
  const one = async i => {
    const fh = await d.getFileHandle(`file-${String(i).padStart(5,'0')}.txt`,
                                     {create: true});
    const w = await fh.createWritable();
    await w.write('x'.repeat((i % 13) + 1));
    await w.close();
  };
  for (let b = 0; b < n; b += 250)
    await Promise.all(Array.from({length: Math.min(250, n - b)}, (_, j) => one(b + j)));
  return n;
}
"""

# Three costs, separated, because only one of them is new. The listing is what
# opening any folder already costs; the sweep is what a size sort adds; the
# comparison is what people assume sorting *is*.
OPFS_SWEEP = r"""
async () => {
  const d = await (await navigator.storage.getDirectory()).getDirectoryHandle('bench');
  const node = FSA.node('bench', d);
  const t1 = performance.now();
  await FS.ensureLoaded(node);
  const listMs = performance.now() - t1;
  const t2 = performance.now();
  await ensureMeta(node);
  const sweepMs = performance.now() - t2;
  const was = state.sort;
  state.sort = {key: 'size', desc: true};
  const t3 = performance.now();
  const rows = visibleKids(node);
  const sortMs = performance.now() - t3;
  state.sort = was;
  return {rows: rows.length, listMs: +listMs.toFixed(0),
          sweepMs: +sweepMs.toFixed(0), sortMs: +sortMs.toFixed(1),
          unread: rows.filter(k => !k.meta || k.meta.error).length};
}
"""


async def open_at(pg, base, frag=""):
    """Load the app cold at a fragment and mount the fake tree.

    about:blank first: navigating between two URLs that differ only in their
    fragment does not reload the document, so the boot code that reads the link
    would never run again and the test would be measuring the previous page.
    """
    await pg.goto("about:blank")
    await pg.goto(base + frag)
    # Rich previews reach for a CDN and log two console errors when it is not
    # reachable; both sides of that are tests/test_rich.py's job, not this suite's.
    await pg.evaluate("localStorage.setItem('filemill.rich','off')")
    await pg.evaluate(FAKE)
    await pg.evaluate("mount(__mk())")
    await pg.wait_for_function(
        "path.length && !document.querySelector('.spinner') && location.hash.includes('r=workspace')"
    )


def test_fullscreen_survives_resize(bundle, playwright, static_origin):
    with playwright.chromium.launch() as browser:
        pg = browser.new_page()
        pg.goto(f"{static_origin}/static/{bundle.name}")
        pg.evaluate("localStorage.setItem('filemill.rich','off')")
        pg.evaluate(FAKE)
        pg.evaluate("mount(__mk())")
        pg.click('.col[data-i="0"] .row:has-text("README.md")')
        pg.wait_for_selector("#preview .pv-text")
        url = pg.url
        history_length = pg.evaluate("history.length")
        pg.focus("#pv-fullscreen")
        pg.keyboard.press("Enter")
        pg.wait_for_function("document.fullscreenElement !== null")
        pg.evaluate("window.dispatchEvent(new Event('resize'))")
        assert pg.evaluate("document.fullscreenElement !== null")
        assert pg.url == url
        assert pg.evaluate("history.length") == history_length
        assert pg.evaluate("document.activeElement.id") == "pv-fullscreen"
        pg.keyboard.press("Enter")
        pg.wait_for_function("document.fullscreenElement === null")
        assert pg.get_attribute("#pv-fullscreen", "aria-pressed") == "false"


async def test_selection_url(page, base):
    pg = page
    # ── the URL follows the selection ────────────────────────────────
    await open_at(pg, base)
    assert await pg.evaluate("location.hash") == "#r=workspace", await pg.evaluate(
        "location.hash"
    )

    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.wait_for_function("sel[0] === 'mixed' && path[1]?.kids")
    await pg.click('.col[data-i="1"] .row:has-text("note.md")')
    await pg.wait_for_function(
        "location.hash === '#r=workspace&p=mixed/note.md&v=render'"
    )
    assert (
        await pg.evaluate("location.hash") == "#r=workspace&p=mixed/note.md&v=render"
    ), await pg.evaluate("location.hash")

    await pg.click('.col[data-i="1"] .row:has-text("sp ace")')
    await pg.wait_for_function(
        "location.hash === '#r=workspace&p=mixed/sp%20ace%20%26%20co.txt&v=render'"
    )
    assert (
        await pg.evaluate("location.hash")
        == "#r=workspace&p=mixed/sp%20ace%20%26%20co.txt&v=render"
    ), await pg.evaluate("location.hash")


async def test_history_replacement(page, base):
    pg = page
    # ── walking a column must not flood history ──────────────────────
    await open_at(pg, base)
    await pg.click('.col[data-i="0"] .row:has-text("mixed")')
    await pg.click('.col[data-i="1"] .row:has-text("note.md")')
    # note.md opens as a column of headings; its own push must land first
    await pg.wait_for_function(
        "location.hash === '#r=workspace&p=mixed/note.md&v=render'"
    )
    before = await pg.evaluate("history.length")
    for key in ("ArrowDown", "ArrowUp", "ArrowDown"):
        await pg.keyboard.press(key)
        await pg.wait_for_function(
            "ROUTER.read().path.join('/') === sel.join('/') && !path.some(n => n.loading)"
        )
    after = await pg.evaluate("history.length")
    assert after == before, f"{before} → {after}"


async def test_deep_link(page, base):
    pg = page
    # ── a link restores the selection ────────────────────────────────
    await open_at(pg, base, "#r=workspace&p=deep/alpha/beta/leaf.txt")
    st = await pg.evaluate("__state()")
    assert st["path"] == ["workspace", "deep", "alpha", "beta"] and st["sel"] == [
        "deep",
        "alpha",
        "beta",
        "leaf.txt",
    ], str(st)
    assert "leaf" in await pg.inner_text("#preview .col-head"), (
        "The linked file is previewed, not just selected"
    )


async def test_dotfile_link(page, base):
    pg = page
    # ── a link into a dotfile reveals dotfiles ───────────────────────
    await open_at(pg, base, "#r=workspace&p=mixed/.hidden")
    assert await pg.evaluate("state.dotfiles") is True and (
        await pg.evaluate("__state()")
    )["sel"] == ["mixed", ".hidden"], str(await pg.evaluate("__state()"))


async def test_stale_link(page, base):
    pg = page
    # ── a stale link degrades, it does not fail ──────────────────────
    await open_at(pg, base, "#r=workspace&p=mixed/renamed-away.md")
    st = await pg.evaluate("__state()")
    assert st["path"] == ["workspace", "mixed"] and st["sel"] == ["mixed"], str(st)
    assert await pg.evaluate("location.hash") == "#r=workspace&p=mixed", (
        await pg.evaluate("location.hash")
    )


async def test_back_forward(page, base):
    pg = page
    # ── Back walks folders ───────────────────────────────────────────
    await open_at(pg, base)
    await pg.click('.col[data-i="0"] .row:has-text("deep")')
    await pg.wait_for_function("sel[0] === 'deep' && path[1]?.kids")
    await pg.click('.col[data-i="1"] .row:has-text("alpha")')
    await pg.wait_for_function("sel[1] === 'alpha' && path[2]?.kids")
    deep_hash = await pg.evaluate("location.hash")
    await pg.go_back()
    await pg.wait_for_function("path.length === 2 && sel[0] === 'deep'")
    st = await pg.evaluate("__state()")
    assert await pg.evaluate("location.hash") != deep_hash and st["sel"] == ["deep"], (
        str(st)
    )
    await pg.go_forward()
    await pg.wait_for_function("path.length === 3 && sel[1] === 'alpha'")
    assert (await pg.evaluate("__state()"))["sel"] == ["deep", "alpha"], str(
        await pg.evaluate("__state()")
    )


async def test_opfs_sort(page, base, opfs_root):
    pg = page
    # ── A real filesystem, through OPFS ──────────────────────────────
    # The origin private file system is a real FileSystemDirectoryHandle:
    # same entries(), same getFile(), same browser-side plumbing, and no
    # folder dialog. It is the only way this repo can run its own adapter
    # against real files without a person at the keyboard, and the only
    # place the true cost of a size sort is visible — the fake handle in
    # test_ui.py answers getFile() out of memory.
    N = 3000
    built = N
    r = await pg.evaluate(OPFS_SWEEP)
    assert (
        r["rows"] == N
        and r["unread"] == 0
        and r["sortMs"] < 200
        and r["sweepMs"] < 30_000
    ), f"built {built}, {r['unread']} rows without metadata"
    # Load moves the absolute figures by 3×, so the claim worth pinning is
    # the ratio: reading every file costs a small multiple of reading the
    # directory, not a multiple of the number of files. A sweep that waited
    # for each getFile() in turn would be tens of times the listing.
    assert r["sweepMs"] < r["listMs"] * 12, (
        f"sweep {r['sweepMs']} ms against listing {r['listMs']} ms"
    )

    # End to end, on real files: mount the folder, ask for biggest first.
    await pg.evaluate("setSort('size', true)")
    await pg.evaluate(
        "async root => mount(await root.getDirectoryHandle('bench'))", opfs_root
    )
    await pg.wait_for_function(
        "path.length && path[0].metaDone && colCache.get(path[0])", timeout=60_000
    )
    await pg.wait_for_function(
        "document.querySelector('.col[data-i=\"0\"] .row')?.title === visibleKids(path[0])[0]?.name"
    )
    top = await pg.eval_on_selector_all(
        '.col[data-i="0"] .row', "e => e.slice(0,3).map(x => x.title)"
    )
    biggest = await pg.evaluate(
        "path[0].kids.filter(k => k.meta.size === 13).map(k => k.name)"
    )
    assert len(top) == 3 and all(t in biggest for t in top), str(top)
    await pg.evaluate("setSort('name', false)")
