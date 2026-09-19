"""The browser renderer uses the model's live state and keyboard decisions."""

import pytest


def test_model_renderer_selection(bundle, playwright):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
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
        page.keyboard.press('ArrowDown')
        page.wait_for_function("sel[0] === 'folder' && path.length === 2")
        assert page.evaluate('focusCol') == 0
        page.keyboard.press('ArrowRight')
        page.wait_for_function("focusCol === 1 && sel[1] === 'note.txt'")
        page.wait_for_selector('#preview .pv-text')
        assert page.evaluate('path.map(n => n.name)') == ['model-test', 'folder']
        geometry = """() => [...document.querySelectorAll('.col, #preview')]
            .map(el => el.offsetWidth)"""
        widths = page.evaluate(geometry)
        page.keyboard.press('ArrowRight')
        page.wait_for_function("document.activeElement.id === 'preview'")
        assert page.evaluate(geometry) == widths
        page.keyboard.press('ArrowLeft')
        page.wait_for_function("!document.activeElement.closest('#preview')")
        assert page.evaluate("focusCol === 1 && sel[1] === 'note.txt'")
        if bundle.name == 'index-dev.html':
            assert page.evaluate("""async () => {
                const model = await import('../ui/core/model/state.js');
                const links = await import('../ui/core/model/deeplink.js');
                return model.path === path && model.sel === sel &&
                    links.currentPath().join('/') === 'folder/note.txt';
            }""")
        page.set_viewport_size({'width': 700, 'height': 700})
        page.wait_for_function("document.getElementById('finder').clientWidth <= 700")
        assert page.evaluate('sel[1]') == 'note.txt'
        # The static file entry already tries to register its HTTP-only worker.
        expected = "Failed to register a ServiceWorker: The URL protocol of the current origin ('file://') is not supported."
        assert all(error == expected for error in errors)
    finally:
        browser.close()


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
def test_responsive_column_widths(bundle, playwright, width, height, expected):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
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
        assert page.locator(".col").first.bounding_box()["width"] == pytest.approx(
            expected
        )
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
    finally:
        browser.close()


def test_loading_and_navigation_keep_columns_whole(bundle, playwright):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
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
        page.keyboard.press("ArrowRight")
        page.wait_for_function("focusCol === 1")
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
    finally:
        browser.close()


@pytest.mark.parametrize("width,folds", [(1154, 1), (1155, 0), (1156, 0)])
def test_preview_threshold_folds_only_below_one_third(bundle, playwright, width, folds):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
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
        for key in ["ArrowDown", "ArrowRight", "ArrowRight"]:
            page.keyboard.press(key)
        page.wait_for_function("focusCol === 2 && path.length === 3")
        assert page.evaluate("folded") == folds
        assert page.locator(".col.focus").bounding_box()["width"] == pytest.approx(240)
        box = page.locator("#preview").bounding_box()
        assert box["width"] >= width / 3 - 1
        assert box["x"] + box["width"] == pytest.approx(width - 10, abs=1)
    finally:
        browser.close()


@pytest.mark.parametrize("activation", ["keyboard", "mouse", "partial", "density"])
def test_geometry_changes_preserve_preview_rules(bundle, playwright, activation):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
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
            page.evaluate(
                "finder.scrollTo({left: 0.25 * foldUnit() * range(), behavior: 'instant'})"
            )
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
            "position => Math.abs(finder.scrollLeft / (foldUnit() * range()) - position) < 0.005",
            arg=position,
            timeout=2000,
        )
        assert page.locator(".col.focus").bounding_box()["width"] == pytest.approx(
            260 if activation == "density" else 240
        )
        if activation != "partial":
            box = page.locator("#preview").bounding_box()
            assert (
                min(box["x"] + box["width"], width) - max(box["x"], 0) >= width / 3 - 1
            )
    finally:
        browser.close()
