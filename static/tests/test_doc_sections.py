"""Markdown and reStructuredText documents browse by their headings."""

from urllib.parse import parse_qs, urlsplit

import pytest

MOUNT = """async () => {
    const file = (name, text) => [name, {kind: 'file', name,
        async getFile() { return new File([text], name); }}];
    const entries = [
        file('guide.md', 'intro\\n\\n# Guide\\n\\ntext\\n\\n## Install\\n\\nsteps\\n\\n'
            + '### Linux\\n\\napt\\n\\n## Use\\n\\nrun\\n'),
        file('plain.md', '# Title only\\n\\nno hierarchy here\\n'),
        file('doc.rst', 'Title\\n=====\\n\\nPart A\\n------\\n\\nalpha\\n\\n'
            + 'Part B\\n------\\n\\nbeta\\n'),
    ];
    await mount({kind: 'directory', name: 'root', async *entries() {
        for (const entry of entries) yield entry;
    }});
}"""


def rows(page, column):
    return page.eval_on_selector_all(
        f'.col[data-i="{column}"] .row .stem', "e => e.map(x => x.textContent)"
    )


def preview_has(page, *wanted, absent=()):
    page.wait_for_function(
        """([wanted, absent]) => {
            const text = document.querySelector('#pv-content')?.textContent || '';
            return wanted.every(w => text.includes(w)) && absent.every(a => !text.includes(a));
        }""",
        arg=[list(wanted), list(absent)],
    )


@pytest.mark.parametrize(
    "filename, heading, body",
    [
        ("guide.md", "Guide", "steps"),
        ("doc.rst", "Part B", "beta"),
    ],
)
@pytest.mark.parametrize("decoration", [".row .ico", "#preview .pv-hero"])
def test_section_previews_omit_decorations(
    bundle, playwright, filename, heading, body, decoration
):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page(viewport={"width": 1500, "height": 900})
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate("localStorage.setItem('filemill.rich', 'off')")
        page.evaluate(MOUNT)
        page.click(f'.col[data-i="0"] .row:has-text("{filename}")')
        preview_has(page, body)
        assert page.locator("#preview .pv-hero").count() == 1
        page.click(f'.col[data-i="1"] .row:has-text("{heading}")')
        preview_has(page, heading, body)
        selector = (
            f'.col[data-i="1"] {decoration}'
            if decoration.startswith(".row")
            else decoration
        )
        assert page.locator(selector).count() == 0
    finally:
        browser.close()


def test_markdown_headings_open_as_columns(bundle, playwright):
    browser = playwright.chromium.launch(args=["--allow-file-access-from-files"])
    try:
        page = browser.new_page(viewport={"width": 1500, "height": 900})
        page.goto(bundle.as_uri())
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate("localStorage.setItem('filemill.rich', 'off')")
        page.evaluate(MOUNT)
        page.wait_for_selector('.col[data-i="0"] .row')

        page.click('.col[data-i="0"] .row:has-text("guide.md")')
        page.wait_for_selector('.col[data-i="1"] .row:has-text("Guide")')
        assert rows(page, 1) == ["Guide"]
        # The whole document previews while its row is selected, and it edits.
        preview_has(page, "intro", "apt", "run")
        page.wait_for_selector("#pv-edit", state="visible")
        assert page.evaluate("sel") == ["guide.md"]

        page.click('.col[data-i="1"] .row:has-text("Guide")')
        page.wait_for_selector('.col[data-i="2"] .row:has-text("Install")')
        assert rows(page, 2) == ["Install", "Use"]
        preview_has(page, "text", "steps", "run", absent=["intro"])

        page.click('.col[data-i="2"] .row:has-text("Install")')
        page.wait_for_selector('.col[data-i="3"] .row:has-text("Linux")')
        preview_has(page, "steps", "apt", absent=["intro", "run"])
        page.wait_for_selector("#pv-edit", state="hidden")

        page.click('.col[data-i="2"] .row:has-text("Use")')
        preview_has(page, "run", absent=["steps", "apt"])
        assert page.evaluate("path.length") == 3

        page.evaluate('applyPath(["guide.md", "Guide", "Install", "Linux"], 3)')
        page.wait_for_function(
            """JSON.stringify(sel) === '["guide.md","Guide","Install","Linux"]'"""
        )
        preview_has(page, "apt", absent=["steps", "run"])

        # Left walks back through parent sections to the whole document.
        page.keyboard.press("ArrowLeft")
        preview_has(page, "steps", "apt", absent=["intro", "run"])
        page.keyboard.press("ArrowLeft")
        preview_has(page, "text", "steps", "run", absent=["intro"])
        page.keyboard.press("ArrowLeft")
        preview_has(page, "intro", "text", "steps", "apt", "run")
        assert page.evaluate("focusCol") == 0
        assert page.evaluate("sel") == ["guide.md"]
        assert rows(page, 1) == ["Guide"]
        page.keyboard.press("ArrowRight")
        preview_has(page, "text", "steps", "run", absent=["intro"])

        # A file whose only heading is its title stays a plain file: the deep
        # link ends at it, and no column opens.
        page.evaluate('applyPath(["plain.md"], 0)')
        preview_has(page, "no hierarchy here")
        page.wait_for_function("path.length === 1 && sel[0] === 'plain.md'")
        assert (
            page.evaluate("path[0].kids.find(k => k.name === 'plain.md').dir") is False
        )

        # The lone title at the top names the file; its parts are the column.
        page.click('.col[data-i="0"] .row:has-text("doc.rst")')
        page.wait_for_selector('.col[data-i="1"] .row:has-text("Part B")')
        assert rows(page, 1) == ["Part A", "Part B"]
        page.click('.col[data-i="1"] .row:has-text("Part B")')
        preview_has(page, "beta", absent=["alpha"])
        page.keyboard.press("ArrowLeft")
        preview_has(page, "Title", "alpha", "beta")
        assert page.evaluate("focusCol") == 0
        assert page.evaluate("sel") == ["doc.rst"]
        assert rows(page, 1) == ["Part A", "Part B"]
    finally:
        browser.close()


def test_left_return_ignores_preview_heading_names(
    bundle, playwright, static_origin, special_heading_document
):
    name, text, nested = special_heading_document
    browser = playwright.chromium.launch()
    try:
        page = browser.new_page(viewport={"width": 1500, "height": 900})
        page.goto(f"{static_origin}/static/{bundle.name}")
        page.wait_for_function("typeof mount === 'function'")
        page.evaluate("localStorage.setItem('filemill.rich', 'off')")
        page.evaluate(
            """async ([name, text]) => {
            const file = {kind: 'file', name,
                async getFile() { return new File([text], name); }};
            await mount({kind: 'directory', name: 'root', async *entries() {
                yield [name, file];
            }});
        }""",
            [name, text],
        )
        page.click('.col[data-i="0"] .row')
        if nested:
            page.click('.col[data-i="1"] .row:has-text("Group")')
        depth = 2 if nested else 1
        page.click(f'.col[data-i="{depth}"] .row:has-text("Other")')
        preview_has(page, "OTHER BODY", absent=["README BODY"])
        page.keyboard.press("ArrowLeft")
        preview_has(page, "README BODY")
        expected = [name, "Group"] if nested else [name]
        assert page.evaluate("sel") == expected
        assert page.evaluate("focusCol") == len(expected) - 1
        assert parse_qs(urlsplit(page.url).fragment)["p"] == ["/".join(expected)]
        preview_has(
            page,
            "README BODY",
            "OTHER BODY",
            "GROUP INTRO" if nested else "PREFACE",
            absent=["PREFACE"] if nested else [],
        )
    finally:
        browser.close()
