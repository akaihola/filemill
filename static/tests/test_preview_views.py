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
def browser_preview(request, bundle, sync_browser, static_origin):
    name, source, rendered = request.param
    browser = sync_browser
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


@pytest.mark.parametrize("extension", ["md", "markdown"])
def test_markdown_comments_are_hidden_only_in_rendered_view(
    bundle,
    static_origin,
    extension,
    sync_browser,
):
    source = (
        "# Comments\n\n"
        "Before <!-- inline **secret** [[Hidden]] -->after.\n\n"
        "Paragraph\n<!-- interrupt secret -->\nAfter block.\n\n"
        "> <!-- quote secret\n>\n> Hidden quote\n> -->\n> Visible quote.\n\n"
        "- item\n\n  <!-- list secret\n\n  Hidden list\n  -->\n\n  Visible item.\n\n"
        "<!-- block secret\n\n# Hidden heading\n\n- [ ] Hidden task\n-->\n\n"
        "Visible **text**.\n\n"
        "`<!-- inline code -->`\n\n"
        "```html\n<!-- fenced code -->\n```\n\n"
        "    <!-- indented code -->\n\n"
        "&lt;!-- escaped text --&gt;\n\n"
        "<b>literal HTML</b>\n\n"
        "<!-- unfinished secret\n\nHidden to end\n"
    )
    browser = sync_browser
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
        [f"comments.{extension}", source],
    )
    page.locator('.col[data-i="0"] .row').click()
    content = page.locator("#preview .pv-markdown")
    content.wait_for()
    text = content.inner_text()
    assert "secret" not in text
    assert "Hidden" not in text
    assert "Before after." in text
    assert "Visible quote." in text
    assert "Visible item." in text
    assert content.locator("strong").inner_text() == "text"
    assert content.locator("code").all_text_contents() == [
        "<!-- inline code -->",
        "<!-- fenced code -->\n",
        "<!-- indented code -->\n",
    ]
    assert "<!-- escaped text -->" in text
    assert "<b>literal HTML</b>" in text
    assert content.locator("b, input").count() == 0
    page.locator("#pv-view").click()
    page.locator("#preview .pv-text").wait_for()
    assert page.locator("#preview .pv-text").text_content() == source
    assert (
        page.locator("#pv-raw").evaluate("async a => (await fetch(a.href)).text()")
        == source
    )


def test_preview_mode_changes_render_once_and_survive_resize(browser_preview):
    page, source, rendered = browser_preview
    page.evaluate("""() => {
      window.__renders = 0;
      const render = PREVIEW.render.bind(PREVIEW);
      PREVIEW.render = n => { __renders++; return render(n); };
    }""")
    page.locator("#pv-view").click()
    page.wait_for_selector("#preview .pv-text")
    assert page.locator("#preview .pv-text").text_content() == source
    assert page.evaluate("__renders") == 1
    page.set_viewport_size({"width": 950, "height": 700})
    page.evaluate("render(true)")
    assert page.evaluate("__renders") == 1
    page.locator("#pv-view").click()
    page.wait_for_selector(rendered)
    assert page.evaluate("__renders") == 2
    page.evaluate("render(true)")
    assert page.evaluate("__renders") == 2
