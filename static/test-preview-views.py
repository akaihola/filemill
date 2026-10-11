"""Local preview representations in the static bundle and module build."""

import pytest

VENDOR_MAP = """
window.FILEMILL_CDN = Object.fromEntries(
  ["markdown-it", "markdown-it-footnote", "markdown-it-deflist",
   "markdown-it-task-lists", "markdown-it-anchor"]
    .map((n) => [n, `/ui/vendor/${n}.js`]));
"""


@pytest.fixture(
    params=[
        ("note.md", "# Heading\n\nSome **bold** text.\n", ".pv-rich h1"),
        (
            "captions.vtt",
            "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello world\n",
            ".preview-cue",
        ),
    ]
)
def browser_preview(request, bundle, playwright, static_origin):
    name, source, rendered = request.param
    with playwright.chromium.launch() as browser:
        page = browser.new_page()
        page.goto(f"{static_origin}/static/{bundle.name}")
        page.evaluate(VENDOR_MAP)
        page.evaluate(
            """async ([name, source]) => {
          document.documentElement.dataset.filemill = 'render';
          await mount({kind: 'directory', name: 'vault', async *entries() {
            yield [name, {kind: 'file', name,
              async getFile() { return new File([source], name); }}];
          }});
        }""",
            [name, source],
        )
        page.locator('.col[data-i="0"] .row').click()
        page.wait_for_selector(rendered)
        yield page, source, rendered


def test_static_rendered_source_round_trip(browser_preview):
    page, source, rendered = browser_preview
    before = page.evaluate("sel.slice()")
    toggle = page.locator("#pv-view")
    assert toggle.inner_text() == "Source"
    toggle.click()
    page.wait_for_selector("#preview .pv-text", timeout=3000)
    assert page.locator("#preview .pv-text").text_content() == source
    assert page.locator(rendered).count() == 0
    assert toggle.inner_text() == "Rendered"
    assert page.evaluate("sel") == before
    assert "#r=vault" in page.url and "&v=highlight" in page.url

    toggle.press("Enter")
    page.wait_for_selector(rendered)
    assert toggle.inner_text() == "Source"
    assert page.evaluate("sel") == before
    assert "#r=vault" in page.url and "&v=render" in page.url


def test_static_raw_link_reads_local_bytes(browser_preview):
    page, source, _rendered = browser_preview
    raw = page.locator("#pv-raw")
    assert raw.count() == 1
    assert raw.get_attribute("href").startswith("blob:")
    assert raw.evaluate("async a => (await fetch(a.href)).text()") == source
    assert page.locator(".pv-actions").inner_text().split().count("Raw") == 1
    before = page.url
    with page.expect_popup() as opened:
        raw.click()
    popup = opened.value
    popup.wait_for_load_state()
    assert popup.locator("pre").text_content() == source
    assert page.url == before
    popup.close()


def test_static_raw_link_releases_previous_bytes(browser_preview):
    page, source, _rendered = browser_preview
    old_url = page.locator("#pv-raw").get_attribute("href")
    page.locator("#pv-view").click()
    page.wait_for_selector("#preview .pv-text")
    raw = page.locator("#pv-raw")
    assert raw.evaluate("async a => (await fetch(a.href)).text()") == source
    assert page.evaluate(
        "async url => { try { await fetch(url); return false; } catch { return true; } }",
        old_url,
    )
