"""JSON folds follow structural paths across previews."""

import pytest


def test_invalid_json_keeps_source_fallback(bundle, playwright):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate("""async () => {
            const file = new File(['{"broken":}'], 'broken.json');
            await mount({kind: 'directory', name: 'root', async *entries() {
                yield [file.name, {kind: 'file', name: file.name, async getFile() {return file;}}];
            }});
            await applyPath([file.name], 0);
        }""")
        page.wait_for_selector("#preview .pv-text .hl-str", timeout=3000)
        assert page.inner_text("#preview .pv-text") == '{"broken":}'
    finally:
        browser.close()


def test_json_size_guard_checks_blob_before_reading_text(bundle, playwright):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate("""async () => {
            window.textReads = 0;
            const file = new File([' '.repeat(8 * 1024 * 1024 + 1)], 'huge.json');
            file.text = async () => {textReads++; throw new Error('Must not read text');};
            await mount({kind: 'directory', name: 'root', async *entries() {
                yield [file.name, {kind: 'file', name: file.name, async getFile() {return file;}}];
            }});
            await applyPath([file.name], 0);
        }""")
        page.wait_for_selector("#preview .pv-err")
        assert "Too large to browse (over 8 MiB)" in page.inner_text("#preview .pv-err")
        assert page.evaluate("textReads") == 0
    finally:
        browser.close()


@pytest.mark.parametrize(
    "shape,padding_size",
    [
        ("object", 528 * 1024),
        ("array", 528 * 1024),
        ("scalar", 528 * 1024),
        ("scalar", 8 * 1024 * 1024 - 2),
    ],
)
def test_json_over_text_limit_previews_and_browses(
    bundle, playwright, shape, padding_size
):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate(
            """async ([shape, paddingSize]) => {
            const padding = 'x'.repeat(paddingSize);
            const record = {padding, nested: {leaf: 'manifest leaf'}};
            const value = shape === 'array' ? [record] : shape === 'scalar' ? padding : record;
            const file = new File([JSON.stringify(value)], 'backup-manifest.json');
            if (file.size <= 512 * 1024) throw new Error('Fixture is too small');
            await mount({kind: 'directory', name: 'root', async *entries() {
                yield [file.name, {kind: 'file', name: file.name, async getFile() {return file;}}];
            }});
            await applyPath([file.name], 0);
        }""",
            [shape, padding_size],
        )
        preview = page.locator("#preview .pv-text")
        preview.wait_for()
        assert "x" * padding_size in preview.text_content()
        if shape != "scalar":
            parts = ["backup-manifest.json"]
            if shape == "array":
                parts.append("0")
            parts.extend(["nested", "leaf"])
            page.evaluate(
                "async parts => await applyPath(parts, parts.length - 1)", parts
            )
            page.wait_for_function(
                "document.querySelector('#preview .pv-json-value')?.textContent === 'manifest leaf'"
            )
    finally:
        browser.close()


@pytest.mark.parametrize("activation", ["mouse", "keyboard", "immediate"])
def test_json_collapse_paths(bundle, playwright, activation):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate("""async () => {
            const value = () => ({c: {bar: {leaf: 1}}, other: {bar: {leaf: 2}}});
            const data = {a: {b: {foo: value()}}, x: {y: {z: value()}},
                short: value()};
            window.reads = 0;
            await mount({kind: 'directory', name: 'root', async *entries() {
                yield ['data.json', {kind: 'file', name: 'data.json',
                    async getFile() { reads++; return new File([JSON.stringify(data)], 'data.json'); }}];
            }});
        }""")

        def view(parts):
            page.evaluate(
                'async parts => await applyPath(["data.json", ...parts], parts.length)',
                parts,
            )
            page.wait_for_selector("#preview details")

        def bar():
            return (
                page.locator("#preview summary")
                .filter(has_text='"bar":')
                .first.locator("..")
            )

        view(["a", "b", "foo"])
        page.evaluate(
            'window.savedPreview = document.querySelector("#pv-content"); window.savedDetails = savedPreview.querySelector("details"); window.savedReads = reads; window.savedSelection = JSON.stringify(sel)'
        )
        summary = bar().locator(":scope > summary")
        if activation == "keyboard":
            summary.focus()
            summary.press("Enter")
        elif activation == "immediate":
            summary.evaluate(
                'el => { el.click(); window.navigation = applyPath(["data.json", "x", "y", "z"], 3); }'
            )
            page.evaluate("navigation")
        else:
            summary.click()
        if activation != "immediate":
            assert not bar().evaluate("el => el.open")
            assert page.evaluate(
                'savedPreview === document.querySelector("#pv-content") && savedDetails === savedPreview.querySelector("details") && reads === savedReads && JSON.stringify(sel) === savedSelection'
            )
        view(["x", "y", "z"])
        assert not bar().evaluate("el => el.open")
        assert (
            page.locator("#preview summary")
            .filter(has_text='"bar":')
            .nth(1)
            .locator("..")
            .evaluate("el => el.open")
        )
        view(["x", "y", "z", "c"])
        assert not bar().evaluate("el => el.open")
        bar().locator(":scope > summary").click()
        view(["a", "b", "foo"])
        assert not bar().evaluate("el => el.open")
        view(["x", "y", "z"])
        assert bar().evaluate("el => el.open")
        bar().locator(":scope > summary").click()
        view(["x", "y", "z", "c"])
        assert not bar().evaluate("el => el.open")
        view(["short"])
        assert bar().evaluate("el => el.open")
    finally:
        browser.close()


@pytest.mark.parametrize("extension", ["json", "jsonl"])
def test_json_array_paths_and_root_fold(bundle, playwright, extension):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page()
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate(
            """async extension => {
            const records = Array.from({length: 2}, () => ({'a.b': {'/"*': {value: 1}}}));
            const text = extension === 'json' ? JSON.stringify(records) : records.map(v => JSON.stringify(v)).join('\\n');
            const name = 'data.' + extension;
            await mount({kind: 'directory', name: 'root', async *entries() {
                yield [name, {kind: 'file', name, async getFile() {return new File([text], name);}}];
            }});
        }""",
            extension,
        )

        def view(index):
            row = str(index) if extension == "json" else f"line {index + 1}"
            page.evaluate(
                "async parts => await applyPath(parts, 1)", [f"data.{extension}", row]
            )
            page.wait_for_selector("#preview details")

        view(0)
        page.locator("#preview details").nth(2).locator(":scope > summary").click()
        view(1)
        assert not page.locator("#preview details").nth(2).evaluate("el => el.open")
        assert page.locator("#preview details").nth(2).evaluate(
            "el => JSON.parse(el.dataset.jsonPath)"
        ) == ["1", "a.b", '/"*']
        root = page.locator("#preview details").first
        root.locator(":scope > summary").click()
        view(0)
        assert not root.evaluate("el => el.open")
        root.locator(":scope > summary").focus()
        root.locator(":scope > summary").press("Space")
        assert root.evaluate("el => el.open")
        view(1)
        assert not root.evaluate("el => el.open")
        view(0)
        assert root.evaluate("el => el.open")
        assert not page.locator("#preview details").nth(2).evaluate("el => el.open")
    finally:
        browser.close()
