"""The browser renderer uses the model's live state and keyboard decisions."""


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
