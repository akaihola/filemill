"""The browser renderer uses the model's live state and keyboard decisions."""

import pytest


def test_model_renderer_selection(bundle, sync_browser):
    browser = sync_browser
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate("""async () => {
        const dir = (name, kids) => ({kind: 'directory', name,
            async *entries() {for (const child of kids) yield [child.name, child];}});
        const file = name => ({kind: 'file', name,
            async getFile() {return new File(['hello'], name);}});
        await mount(dir('model-test', [dir('folder', [file('note.txt')]), file('z.txt')]));
    }""")
    page.wait_for_selector('.col[data-i="0"] .row')
    page.keyboard.press("ArrowDown")
    page.wait_for_function(
        "sel[0] === 'folder' && path[1]?.kids && colCache.get(path[1])?.rows.length"
    )
    assert page.evaluate("focusCol") == 0
    page.keyboard.press("ArrowRight")
    page.wait_for_function("focusCol === 1 && sel[1] === 'note.txt'")
    page.wait_for_selector("#preview .pv-text")
    assert page.evaluate("path.map(n => n.name)") == ["model-test", "folder"]
    geometry = """() => [...document.querySelectorAll('.col, #preview')]
        .map(el => el.offsetWidth)"""
    widths = page.evaluate(geometry)
    page.keyboard.press("ArrowRight")
    page.wait_for_function("document.activeElement.id === 'preview'")
    assert page.evaluate(geometry) == widths
    page.keyboard.press("ArrowLeft")
    page.wait_for_function("!document.activeElement.closest('#preview')")
    assert page.evaluate("focusCol === 1 && sel[1] === 'note.txt'")
    if bundle.name == "index-dev.html":
        assert page.evaluate("""async () => {
            const model = await import('../ui/core/model/state.js');
            const links = await import('../ui/core/model/deeplink.js');
            return model.path === path && model.sel === sel &&
                links.currentPath().join('/') === 'folder/note.txt';
        }""")
    page.set_viewport_size({"width": 700, "height": 700})
    page.wait_for_function("document.getElementById('finder').clientWidth <= 700")
    assert page.evaluate("sel[1]") == "note.txt"
    # The static file entry already tries to register its HTTP-only worker.
    expected = "Failed to register a ServiceWorker: The URL protocol of the current origin ('file://') is not supported."
    assert all(error == expected for error in errors)


def test_preview_left_preserves_ancestor_folds(bundle, sync_browser):
    browser = sync_browser
    page = browser.new_page(viewport={"width": 700, "height": 700})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate("""async () => {
        const file = name => ({kind: 'file', name,
            async getFile() {return new File(['hello'], name);}});
        const dir = (name, kids) => ({kind: 'directory', name,
            async *entries() {for (const child of kids) yield [child.name, child];}});
        let node = file('note.txt');
        for (const name of ['e', 'd', 'c', 'b', 'a']) node = dir(name, [node]);
        await mount(dir('root', [node]));
    }""")
    for depth in range(5):
        page.keyboard.press("ArrowDown")
        page.wait_for_function(
            "i => path[i]?.kids && colCache.get(path[i])?.rows.length",
            arg=depth + 1,
        )
        page.keyboard.press("ArrowRight")
        page.wait_for_function("length => sel.length === length", arg=depth + 2)
    page.keyboard.press("ArrowRight")
    page.wait_for_function("document.activeElement.id === 'preview'")
    # The finder scrolls smoothly (styles.css) and `folded` follows the
    # scroll, so wait for the layout's target: every ancestor folded.
    page.wait_for_function("folded === path.length - 1")
    before = page.evaluate("[folded, dial()]")
    page.keyboard.press("ArrowLeft")
    page.wait_for_function("document.activeElement.id !== 'preview'")
    assert page.evaluate("[folded, dial()]") == before


def test_preview_left_expands_parent_when_all_columns_are_folded(bundle, sync_browser):
    browser = sync_browser
    page = browser.new_page(viewport={"width": 700, "height": 700})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate("""async () => {
        const file = name => ({kind: 'file', name,
            async getFile() {return new File(['hello'], name);}});
        const dir = (name, kids) => ({kind: 'directory', name,
            async *entries() {for (const child of kids) yield [child.name, child];}});
        let node = file('note.txt');
        for (const name of ['e', 'd', 'c', 'b', 'a']) node = dir(name, [node]);
        await mount(dir('root', [node]));
    }""")
    for depth in range(5):
        page.keyboard.press("ArrowDown")
        page.wait_for_function(
            "i => path[i]?.kids && colCache.get(path[i])?.rows.length",
            arg=depth + 1,
        )
        page.keyboard.press("ArrowRight")
        page.wait_for_function("length => sel.length === length", arg=depth + 2)
    page.keyboard.press("ArrowRight")
    page.wait_for_function("document.activeElement.id === 'preview'")
    page.evaluate("dialTo(range())")
    page.wait_for_function("folded === path.length")
    page.keyboard.press("ArrowLeft")
    page.wait_for_function("document.activeElement.id !== 'preview'")
    page.wait_for_function("folded === path.length - 1")


@pytest.mark.parametrize(
    "width,height,expected",
    [
        (1440, 900, 240),
        (1024, 768, 240),
        (390, 844, 195),
        (844, 390, 211),
        (600, 800, 300),
        (601, 800, 240),
        (800, 600, 200),
        (800, 601, 240),
    ],
)
def test_responsive_column_widths(bundle, width, height, expected, sync_browser):
    browser = sync_browser
    page = browser.new_page(viewport={"width": width, "height": height})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate("""async () => {
        const file = name => ({kind: 'file', name,
            async getFile() {return new File(['hello'], name);}});
        const dir = (name, kids) => ({kind: 'directory', name,
            async *entries() {for (const child of kids) yield [child.name, child];}});
        await mount(dir('root', [dir('a', [file('short.txt')]),
            dir('b-' + 'long'.repeat(30), [file('long.txt')]), file('z.txt')]));
        finder.style.scrollBehavior = 'auto';
    }""")
    # The viewport policy applies before any content is selected.
    assert page.locator(".col").first.bounding_box()["width"] == pytest.approx(expected)
    for name in ["a", "b-" + "long" * 30, "z.txt"]:
        page.locator('.col[data-i="0"] .row').filter(has_text=name).first.click()
        page.wait_for_function("name => sel[0] === name", arg=name)
        assert page.evaluate(
            "expected => widths.every(w => Math.abs(w - expected) < 0.1)", expected
        )
        assert page.locator(".col").first.bounding_box()["width"] == pytest.approx(
            expected
        )
    # With one folder there is room for the preview, and it fills the rest.
    geometry = page.evaluate("""() => {
        const f = finder.getBoundingClientRect(), p = document.getElementById('preview').getBoundingClientRect();
        return {visible: Math.min(p.right, f.right) - Math.max(p.left, f.left),
            right: p.right, edge: f.right, gutter: parseFloat(getComputedStyle(strip).gap)};
    }""")
    assert geometry["visible"] >= width / 3 - 1
    assert geometry["right"] == pytest.approx(
        geometry["edge"] - geometry["gutter"], abs=1
    )
    assert page.evaluate("""() => {
        const pane = document.getElementById('preview').getBoundingClientRect();
        return [...document.querySelectorAll('.pv-actions button, .pv-actions a')]
            .filter(el => el.getClientRects().length)
            .every(el => {const box = el.getBoundingClientRect();
                return box.left >= pane.left && box.right <= pane.right;});
    }""")
    # Rotation and density use live measurements, not a cached node width.
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_function("widths[0] === 240")
    page.evaluate("root.dataset.density = 'comfortable'; render(true)")
    assert page.locator(".col").first.bounding_box()["width"] == pytest.approx(260)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_function("widths[0] === 195")
    assert page.locator(".col").first.bounding_box()["width"] == pytest.approx(195)


def test_loading_and_navigation_keep_columns_whole(bundle, sync_browser):
    browser = sync_browser
    page = browser.new_page(viewport={"width": 1024, "height": 768})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate("""async () => {
        const file = name => ({kind: 'file', name,
            async getFile() {return new File(['hello'], name);}});
        const dir = (name, kids, slow = false) => ({kind: 'directory', name,
            async *entries() {
                if (slow) await new Promise(resolve => window.finishRead = resolve);
                for (const child of kids) yield [child.name, child];
            }});
        await mount(dir('root', [dir('a', [dir('b', [
            dir('c', [file('long-' + 'name'.repeat(30))], true), file('z.txt')
        ])])]));
        window.badWidths = [];
        window.frames = 0;
        window.watchingWidths = true;
        const sample = () => {
            frames++;
            const col = document.querySelector('.col.focus');
            if (col && Math.abs(col.getBoundingClientRect().width - 240) > 0.1)
                badWidths.push(col.getBoundingClientRect().width);
            if (watchingWidths) requestAnimationFrame(sample);
        };
        requestAnimationFrame(sample);
    }""")
    page.locator('.row[title="a"]').click()
    page.wait_for_function("path[1]?.kids && colCache.get(path[1])?.rows.length")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "focusCol === 1 && path[2]?.kids && colCache.get(path[2])?.rows.length"
    )
    page.keyboard.press("ArrowRight")
    page.wait_for_selector('.col[data-i="3"] .spinner')
    page.evaluate("finishRead()")
    page.wait_for_selector('.col[data-i="3"] .row')
    for key in ["ArrowDown", "ArrowUp", "Home", "End", "PageUp", "PageDown"]:
        page.keyboard.press(key)
        page.wait_for_function("widths.every(w => w === 240)")
    page.evaluate("watchingWidths = false")
    assert page.evaluate("frames") > 2
    assert page.evaluate("badWidths") == []


@pytest.mark.parametrize("width,folds", [(1154, 1), (1155, 0), (1156, 0)])
def test_preview_threshold_folds_only_below_one_third(
    bundle, width, folds, sync_browser
):
    browser = sync_browser
    page = browser.new_page(viewport={"width": width, "height": 900})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate("""async () => {
        const dir = (name, kids) => ({kind: 'directory', name,
            async *entries() {for (const child of kids) yield [child.name, child];}});
        const file = {kind: 'file', name: 'note.txt',
            async getFile() {return new File(['hello'], this.name);}};
        await mount(dir('root', [dir('a', [dir('b', [file])])]));
        finder.style.scrollBehavior = 'auto';
    }""")
    page.keyboard.press("ArrowDown")
    for depth in (1, 2):
        page.wait_for_function(
            "i => path[i]?.kids && colCache.get(path[i])?.rows.length",
            arg=depth,
        )
        page.keyboard.press("ArrowRight")
    page.wait_for_function("focusCol === 2 && path.length === 3")
    # Navigation can finish before the layout's deferred scroll write.
    page.wait_for_function("expected => folded === expected", arg=folds)
    assert page.evaluate("folded") == folds
    assert page.locator(".col.focus").bounding_box()["width"] == pytest.approx(240)
    box = page.locator("#preview").bounding_box()
    assert box["width"] >= width / 3 - 1
    assert box["x"] + box["width"] == pytest.approx(width - 10, abs=1)


@pytest.mark.parametrize("activation", ["keyboard", "mouse", "partial", "density"])
def test_geometry_changes_preserve_preview_rules(bundle, activation, sync_browser):
    browser = sync_browser
    width = 1155 if activation == "density" else 1440
    page = browser.new_page(viewport={"width": width, "height": 900})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate("""async () => {
        const dir = (name, kids) => ({kind: 'directory', name,
            async *entries() {for (const child of kids) yield [child.name, child];}});
        const file = {kind: 'file', name: 'z.txt',
            async getFile() {return new File(['hello'], this.name);}};
        await mount(dir('root', [dir('a', [dir('b', [dir('c', [file]), file])])]));
        finder.style.scrollBehavior = 'auto';
        await applyPath(['a', 'b', 'z.txt'], 2);
    }""")
    page.wait_for_function("focusCol === 2 && path.length === 3")
    assert page.evaluate("folded") == 0
    if activation == "partial":
        page.evaluate("dialTo(0.25 * foldUnit() * range())")
    if activation in ["keyboard", "partial"]:
        page.keyboard.press("ArrowUp")
    elif activation == "density":
        page.evaluate("root.dataset.density = 'comfortable'; render(true)")
    else:
        page.locator('.col[data-i="2"] .row[title="c"]').click()
    count = 3 if activation == "density" else 4
    page.wait_for_function("count => path.length === count", arg=count)
    position = 0.25 if activation == "partial" else 1
    page.wait_for_function(
        "position => Math.abs(dial() / (foldUnit() * range()) - position) < 0.005",
        arg=position,
        timeout=2000,
    )
    if activation != "partial":
        # scrollLeft changes before its scroll event updates the columns.
        page.wait_for_function("folded === 1")
    assert page.locator(".col.focus").bounding_box()["width"] == pytest.approx(
        260 if activation == "density" else 240
    )
    if activation != "partial":
        box = page.locator("#preview").bounding_box()
        assert min(box["x"] + box["width"], width) - max(box["x"], 0) >= width / 3 - 1


@pytest.mark.parametrize("count", [80, 1000])
@pytest.mark.parametrize("last", [False, True])
@pytest.mark.parametrize("kind", ["directory", "file"])
def test_left_arrow_reveals_selection(bundle, count, last, kind, sync_browser):
    target = count - 1 if last else 0
    browser = sync_browser
    page = browser.new_page(viewport={"width": 1000, "height": 500})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate(
        """async ([kind, count]) => {
        const dir = (name, kids) => ({kind: 'directory', name,
            async *entries() {for (const child of kids) yield [child.name, child];}});
        const file = name => ({kind: 'file', name,
            async getFile() {return new File(['hello'], name);}});
        const kids = Array.from({length: count}, (_, i) => {
            const name = `item-${String(i).padStart(2, '0')}`;
            return kind === 'directory' ? dir(name, [file('note.txt')]) : file(name + '.txt');
        });
        await mount(dir('root', kids));
    }""",
        [kind, count],
    )
    name = f"item-{target:02}" + (".txt" if kind == "file" else "")
    page.keyboard.press("End" if last else "Home")
    page.wait_for_function("name => sel[0] === name", arg=name)
    if kind == "directory":
        page.wait_for_function("path[1]?.kids && colCache.get(path[1])?.rows.length")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.activeElement.id === 'preview'"
        if kind == "file"
        else "focusCol === 1 && sel[1] === 'note.txt'"
    )
    selection = page.evaluate("({path: path.map(n => n.name), sel: [...sel]})")
    page.locator('.col[data-i="0"] .col-body').evaluate(
        "(body, target) => {body.scrollTop = target === 0 ? body.scrollHeight : 0}",
        target,
    )
    visible = """() => {
        const row = document.querySelector('.col[data-i="0"] .row.sel');
        if (!row) return false;
        const r = row.getBoundingClientRect(), b = row.closest(".col-body").getBoundingClientRect();
        return r.top >= b.top - 1 && r.bottom <= b.bottom + 1;
    }"""
    assert not page.evaluate(visible)
    page.keyboard.press("ArrowLeft")
    page.wait_for_function(
        "focusCol === 0 && !document.activeElement.closest('#preview')"
    )
    assert page.evaluate("({path: path.map(n => n.name), sel: [...sel]})") == selection
    page.wait_for_function(visible, timeout=2000)
    assert page.evaluate("document.getElementById('stage').scrollLeft") == 0
    page.keyboard.press("ArrowDown" if target == 0 else "ArrowUp")
    next_name = f"item-{1 if target == 0 else target - 1:02}" + (
        ".txt" if kind == "file" else ""
    )
    page.wait_for_function("name => sel[0] === name", arg=next_name)


MOUNT_FILES = """async count => {
    const dir = (name, kids) => ({kind: 'directory', name,
        async *entries() {for (const child of kids) yield [child.name, child];}});
    const file = name => ({kind: 'file', name,
        async getFile() {return new File(['hello'], name);}});
    await mount(dir('root', Array.from({length: count},
        (_, i) => file(`item-${String(i).padStart(4, '0')}.txt`))));
}"""


@pytest.mark.parametrize("density", ["compact", "comfortable"])
def test_virtual_rows_follow_the_density_pitch(bundle, density, sync_browser):
    """A virtual row is placed by arithmetic, so its pitch must be the one the
    stylesheet draws; otherwise comfortable rows overlap their neighbours."""
    browser = sync_browser
    page = browser.new_page(viewport={"width": 1000, "height": 500})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate(MOUNT_FILES, 1000)
    page.evaluate("d => { root.dataset.density = d; render(true); }", density)
    page.wait_for_selector('.col[data-i="0"] .row-layer > .row:nth-child(2)')
    top, bottom, next_top = page.evaluate("""() => {
        const [a, b] = document.querySelectorAll('.col[data-i="0"] .row');
        const r = a.getBoundingClientRect();
        return [r.top, r.bottom, b.getBoundingClientRect().top];
    }""")
    assert next_top >= bottom
    assert next_top - top == page.evaluate("""() => {
        const css = getComputedStyle(document.documentElement);
        return parseFloat(css.getPropertyValue('--row-h'))
            + 2 * parseFloat(css.getPropertyValue('--row-gap'));
    }""")


def test_scrolled_virtual_rows_are_evicted(bundle, sync_browser):
    """Scrolling a large column end to end keeps about one viewport of rows in
    the DOM, and the selected row is highlighted again when it scrolls back."""
    browser = sync_browser
    page = browser.new_page(viewport={"width": 1000, "height": 500})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate(MOUNT_FILES, 3000)
    col = '.col[data-i="0"]'
    page.click(f'{col} .row:has-text("item-0000.txt")')
    page.wait_for_function("sel[0] === 'item-0000.txt'")
    page.locator(f"{col} .col-body").evaluate("""async body => {
        const frame = () => new Promise(r => requestAnimationFrame(r));
        for (const end of [body.scrollHeight, 0]) {
            const from = body.scrollTop;
            for (let step = 1; step <= 20; step++) {
                body.scrollTop = from + (end - from) * step / 20;
                await frame();
                await frame();
            }
        }
    }""")
    rows, fits = page.locator(f"{col} .col-body").evaluate("""body => [
        body.querySelectorAll('.row').length,
        Math.ceil(body.clientHeight / body.querySelector('.row').offsetHeight),
    ]""")
    assert rows <= fits + 2 * 10 + 2
    assert page.locator(f'{col} .row.sel:has-text("item-0000.txt")').count() == 1


@pytest.mark.parametrize("source", ["scalar.json", "scalar.jsonl"])
def test_selected_scalar_preview(bundle, source, sync_browser):
    browser = sync_browser
    page = browser.new_page()
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate(
        r"""async source => {
        const text = JSON.stringify({text: 'first\n<b>second</b>', zero: 0, '': 'empty key'});
        const file = {kind: 'file', name: source,
            async getFile() {return new File([text], source);}};
        await mount({kind: 'directory', name: 'scalars',
            async *entries() {yield [source, file];}});
    }""",
        source,
    )
    page.locator('.col[data-i="0"] .row').first.click()
    if source.endswith(".jsonl"):
        page.locator('.col[data-i="1"] .row').first.click()
    page.wait_for_selector("#preview .pv-json")
    page.locator(".row .label").filter(has_text="text").click()
    value = page.locator("#preview .pv-json-value")
    value.wait_for(timeout=3000)
    assert value.text_content() == "first\n<b>second</b>"
    assert value.locator("b").count() == 0
    assert value.evaluate("e => getComputedStyle(e).whiteSpace") == "pre-wrap"
    page.keyboard.press("ArrowDown")
    page.wait_for_function(
        "document.querySelector('.pv-json-value')?.textContent === '0'"
    )
    page.locator('.row[title=""]').click()
    page.wait_for_function(
        "document.querySelector('.pv-json-value')?.textContent === 'empty key'"
    )


@pytest.mark.parametrize("count", [20, 999, 1000])
def test_mounted_root_paints_visible_rows(bundle, count, sync_browser):
    browser = sync_browser
    page = browser.new_page(viewport={"width": 1000, "height": 900})
    page.goto(bundle.as_uri())
    page.wait_for_function("typeof mount === 'function'")
    page.evaluate(
        """async count => {
        await mount({kind: 'directory', name: 'root',
            async *entries() {
                for (let i = 0; i < count; i++) {
                    const name = `item-${String(i).padStart(4, '0')}.txt`;
                    yield [name, {kind: 'file', name,
                        async getFile() {return new File(['hello'], name);}}];
                }
            }});
    }""",
        count,
    )
    page.wait_for_function(
        """() => {
        const body = document.querySelector('.col[data-i="0"] .col-body');
        const rows = [...body.querySelectorAll('.row')];
        const last = rows.at(-1)?.getBoundingClientRect();
        return rows.length === path[0].kids.length ||
            last?.bottom >= body.getBoundingClientRect().bottom;
    }""",
        timeout=2000,
    )
    page.locator('.col[data-i="0"] .row').first.click()
    page.wait_for_function("sel[0] === 'item-0000.txt'")
    assert page.locator("#preview .pv-text").inner_text() == "hello"
