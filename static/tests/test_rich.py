"""Rich previews with blocked CDNs, local stubs and vendored renderers."""

import base64
import io
import re
import zipfile
from textwrap import dedent

from docutils.core import publish_parts

# Serve the repository, not filemill/: the dev entry point references ../ui/,
# which is the whole point of the shared directory.


# The smallest .docx mammoth accepts: the package relationship that names the
# document part, and one paragraph in it.
def _docx(text: str) -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                'openxmlformats.org/package/2006/content-types"><Default Extension="xml" '
                'ContentType="application/xml"/><Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document.main+xml"/></Types>'
            ),
        )
        z.writestr(
            "_rels/.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://'
                'schemas.openxmlformats.org/package/2006/relationships"><Relationship '
                'Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                'relationships/officeDocument" Target="word/document.xml"/></Relationships>'
            ),
        )
        z.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://'
                'schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p>'
                f"<w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
            ),
        )
    return base64.b64encode(buf.getvalue()).decode()


# A .docx whose hyperlinks point where the document says, and one picture:
# mammoth passes a link's target through as written (A2).
DOCX_LINKS = [
    ("run", "javascript:window.__xss=6"),
    ("page", "data:text/html,x"),
    ("web", "https://example.com/"),
    ("mail", "mailto:a@example.com"),
]
PIXEL = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def _docx_links() -> str:
    ns = (
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
    )
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    links = "".join(
        f'<w:p><w:hyperlink r:id="rL{i}"><w:r><w:t>{label}</w:t></w:r>'
        "</w:hyperlink></w:p>"
        for i, (label, _) in enumerate(DOCX_LINKS)
    )
    picture = (
        '<w:p><w:r><w:drawing><wp:inline><wp:docPr id="1" name="Picture" '
        'descr="a pixel"/><a:graphic><a:graphicData uri="http://schemas.'
        'openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:blipFill>'
        '<a:blip r:embed="rImg"/></pic:blipFill></pic:pic></a:graphicData>'
        "</a:graphic></wp:inline></w:drawing></w:r></w:p>"
    )
    rels = (
        "".join(
            f'<Relationship Id="rL{i}" Type="{rel}/hyperlink" Target="{target}" '
            'TargetMode="External"/>'
            for i, (_, target) in enumerate(DOCX_LINKS)
        )
        + f'<Relationship Id="rImg" Type="{rel}/image" Target="media/pixel.png"/>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                'openxmlformats.org/package/2006/content-types"><Default Extension="xml" '
                'ContentType="application/xml"/><Default Extension="png" '
                'ContentType="image/png"/><Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document.main+xml"/></Types>'
            ),
        )
        z.writestr(
            "_rels/.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://'
                'schemas.openxmlformats.org/package/2006/relationships"><Relationship '
                f'Id="rId1" Type="{rel}/officeDocument" Target="word/document.xml"/>'
                "</Relationships>"
            ),
        )
        z.writestr(
            "word/_rels/document.xml.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://'
                f'schemas.openxmlformats.org/package/2006/relationships">{rels}'
                "</Relationships>"
            ),
        )
        z.writestr("word/media/pixel.png", base64.b64decode(PIXEL))
        z.writestr(
            "word/document.xml",
            (
                f'<?xml version="1.0" encoding="UTF-8"?><w:document {ns}><w:body>'
                f"{links}{picture}</w:body></w:document>"
            ),
        )
    return base64.b64encode(buf.getvalue()).decode()


def _pptx():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "ppt/slides/slide1.xml", "<slide><p><t>PowerPoint loaded</t></p></slide>"
        )
    return base64.b64encode(buf.getvalue()).decode()


FAKE = (
    r"""
window.__mk = () => {
  const F = (name, text) => ({kind:'file', name,
    getFile: async () => new File([text], name, {lastModified: Date.parse('2026-08-01')})});
  const B = (name, b64) => F(name, Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)));
  const D = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  return D('vault', [
    F('note.md', '# Heading\n\nSome **bold** text and a [[Other Note]] link.\n'),
    F('fence.md', '# Code\n\nline one\nline two\n\n```python\ndef f():\n    return 1\n```\n'),
    F('Other Note.md', '# Other\n'),
    F('rich.md', '# Rich\n\n- [x] done\n\nText[^1] and [sib](sib.md) and [[Other Note]]\n\n' +
      '```python\ndef f():\n    return 1\n```\n\n[^1]: a note\n'),
    B('doc.docx', '__DOCX__'),
    F('doc.rst', 'Heading\n=======\n\nSome *rst* text.\n'),
    F('code.py', 'def f():\n    return 1\n'),
    F('plain.txt', 'just text'),
    F('data.json', '{"items":["json value"],"count":2}'),
    B('deck.pptx', '__PPTX__'),
    F('broken.pptx', 'bad'),
    // A2: markup that must stay text, with and without a wikilink beside it.
    F('inert.md', 'Text <img src=x onerror="window.__xss=1"> beside [[Other Note|the note]], ' +
      '`<b>code</b>`, [sib](sib.md) and a note[^1].\n\n' +
      'No wikilink: <img src=x onerror="window.__xss=2">\n\n' +
      'Malformed: [[ <img src=x onerror="window.__xss=3"> and [[x]\n\n' +
      '[^1]: a <i>note</i>\n'),
    B('links.docx', '__DOCX_LINKS__'),
    F('script.desktop', '[Desktop Entry]\nType=Link\nName=Bad\nURL=javascript:window.__xss=4\n'),
    F('web.desktop', '[Desktop Entry]\nType=Link\nName=Web\nURL=https://example.com/\n'),
  ]);
};
""".replace("__DOCX__", _docx("Hello docx"))
    .replace("__PPTX__", _pptx())
    .replace("__DOCX_LINKS__", _docx_links())
)

# Enough of each library's shape to prove the plumbing: the loader, the plugin
# chaining, the highlight hook, and where the output lands. Faithfulness to the
# real renderers is the CDN's problem, not this suite's.
STUBS = {
    "markdown-it.js": """
export default class MarkdownIt {
  constructor(o) { this.options = o; this.renderer = { rules: {} }; this.core = { ruler: { push: (n, f) => { this._rule = f; } } }; }
  inline = { ruler: { before() {} } };
  block = { ruler: { before() {} } };
  use() { return this; }
  render(src) {
    const first = src.split('\\n')[0].replace(/^#\\s*/, '');
    const [prose, code] = src.split(/```python\\n|```\\n?$/);
    const body = prose.replace(/\\[\\[([^\\]]+)\\]\\]/g,
      (_, t) => `<a class="wikilink" href="#" data-wiki="${t.trim()}">${t.trim()}</a>`);
    /* the real renderer's shapes: a paragraph keeps its newline, a fence is
       <pre><code class="language-x"> with the source escaped */
    return `<h1>${first}</h1><p>${body.split('\\n').slice(2).join('\\n').trim()}</p>` +
      (code ? `<pre><code class="language-python">${code.replace(/</g, '&lt;')}</code></pre>` : '');
  }
}
""",
    "plugin.js": "export default function noop() {}\n",
    # pyodide.mjs has no default export: the adapter calls m.loadPyodide and
    # then the interpreter methods used by the adapter.
    "pyodide.js": """
export async function loadPyodide() {
  const stats = window.__pyStats ||= {boots: 0, packages: 0, destroyed: 0};
  stats.boots++;
  if (window.__pyFail === 'boot') throw Error('boot failed');
  let src;
  return {
    loadPackage: async () => {
      stats.packages++;
      if (window.__pyFail === 'package') throw Error('package failed');
    },
    globals: { set(_key, value) { src = value; } },
    toPy: (values) => ({...values, destroy() { stats.destroyed++; }}),
    runPythonAsync: async (_code, options) => {
      stats.renders = (stats.renders || 0) + 1;
      if (window.__pyRenderGate) await window.__pyRenderGate;
      await new Promise(resolve => setTimeout(resolve, 10));
      if (window.__pyFail === 'render') throw Error('render failed');
      if (window.__pyHTML) return window.__pyHTML;
      const text = options?.globals.src ?? src;
      const escaped = text.replaceAll('&', '&amp;').replaceAll('<', '&lt;');
      return '<section><h1>Heading</h1><p>Some <em>rst</em> text.</p>' +
        '<pre>' + escaped + '</pre></section>';
    },
  };
}
""",
}


STUB_MAP = """
window.FILEMILL_CDN = {
  "markdown-it":            "%(b)s/__stub/markdown-it.js",
  "markdown-it-footnote":   "%(b)s/__stub/plugin.js",
  "markdown-it-deflist":    "%(b)s/__stub/plugin.js",
  "markdown-it-task-lists": "%(b)s/__stub/plugin.js",
  "markdown-it-anchor":     "%(b)s/__stub/plugin.js",
  "pyodide":                "%(b)s/__stub/pyodide.js",
  "pptx-vanilla-viewer":    "%(b)s/__stub/pptx-viewer.js",
};
"""


# What server/src/filemill/app.py emits in its shell: the same names, served
# from this origin. Files, not stubs — this is the renderer the server edition
# ships, so its output is what gets checked.
VENDOR_MAP = """
window.FILEMILL_CDN = Object.fromEntries(
  ["markdown-it", "markdown-it-footnote", "markdown-it-deflist",
   "markdown-it-task-lists", "markdown-it-anchor", "mammoth"]
    .map((n) => [n, `/ui/vendor/${n}.js`]));
"""


async def boot(pg, base, *, rich=True, stubs=False, vendored=False):
    """Load the app cold with the switch in a known state."""
    await pg.goto("about:blank")
    await pg.goto(base)
    await pg.evaluate(
        f"localStorage.setItem('filemill.rich', {'"on"' if rich else '"off"'})"
    )
    if stubs:
        await pg.evaluate(STUB_MAP % {"b": "/".join(base.split("/")[:3])})
    if vendored:
        await pg.evaluate(VENDOR_MAP)
    await pg.evaluate(FAKE)
    await pg.evaluate("mount(__mk())")
    await pg.wait_for_function("path[0]?.kids && document.querySelector('.col .row')")


async def preview(pg, name, timeout=4000, ready=None):
    # The pane is rebuilt per preview, and a Markdown file is read for its
    # headings before it renders: wait for the new pane, not the old one.
    await pg.evaluate("window.__pvOld = document.querySelector('#pv-content')")
    await pg.click(f'.col[data-i="0"] .row:has-text("{name}")')
    await pg.wait_for_function(
        "document.querySelector('#pv-content') !== window.__pvOld"
        " && document.querySelector('#pv-content > *')",
        timeout=timeout,
    )
    if ready:
        await pg.wait_for_selector(ready, timeout=timeout)
    return await pg.inner_html("#pv-content")


async def test_rst_failure_releases_one_scope_during_layout(page, base):
    await boot(page, base, rich=True, stubs=True)
    await page.evaluate("""() => {
      window.__pyFail = 'render';
      window.__pyRenderGate = new Promise(resolve => { window.__releasePython = resolve; });
    }""")
    await page.click('.col[data-i="0"] .row[title="doc.rst"]')
    await page.wait_for_function("window.__pyStats?.renders === 1")
    await page.evaluate("window.__rstPane = document.getElementById('preview')")
    await page.set_viewport_size({"width": 950, "height": 700})
    await page.evaluate("render(true)")
    assert await page.evaluate("window.__pyStats.destroyed") == 0
    await page.evaluate("window.__releasePython()")
    await page.wait_for_selector("#pv-content .pv-note")
    stats = await page.evaluate("window.__pyStats")
    assert stats["renders"] == stats["destroyed"] == 1, stats
    assert await page.evaluate("document.getElementById('preview') === __rstPane")
    assert "Heading" in await page.inner_text("#pv-content .pv-text")


async def test_rst(page, base):
    pg = page
    await boot(pg, base, rich=True)
    html = await preview(pg, "doc.rst", ready=".pv-note")
    assert "Heading" in html and "pv-text" in html, (
        "RST offline fallback keeps readable source"
    )
    requests = []

    def record(request):
        if "/pyodide/" in request.url:
            requests.append(request.url)

    pg.on("request", record)
    await boot(pg, base, rich=False)
    html = await preview(pg, "doc.rst")
    assert not requests and "pv-note" not in html, (
        "RST consent off requests no runtime assets"
    )
    pg.remove_listener("request", record)
    await pg.reload()
    assert await pg.evaluate("localStorage.getItem('filemill.rich')") == "off", (
        "RST consent survives reload"
    )
    # RST registry failures and interpreter lifetime, without a real CDN.
    for failure in ("boot", "package", "render"):
        await boot(pg, base, rich=True, stubs=True)
        await pg.evaluate("failure => window.__pyFail = failure", failure)
        html = await preview(pg, "doc.rst", ready=".pv-note")
        assert "pv-text" in html and "Heading" in html, (
            f"RST {failure} failure falls back to source"
        )
        if failure == "render":
            assert await pg.evaluate("window.__pyStats.destroyed") == 1, (
                "Failed RST conversion releases Python globals"
            )
        await pg.evaluate("window.__pyFail = null")
        await preview(pg, "plain.txt")
        html = await preview(pg, "doc.rst", ready=".pv-rich")
        assert "<em>rst</em>" in html, f"RST retries after {failure} failure"

    await boot(pg, base, rich=True, stubs=True)
    result = await pg.evaluate("""async () => {
      const outputs = await Promise.all(['first document', 'second document'].map(
        text => renderNode({name: 'doc.rst'}, new Blob([text]), 'rst')));
      return {outputs, stats: window.__pyStats};
    }""")
    assert (
        "first document" in result["outputs"][0]
        and "second document" not in result["outputs"][0]
        and "second document" in result["outputs"][1]
    ), "Concurrent RST previews keep their own source"
    assert result["stats"]["boots"] == result["stats"]["packages"] == 1, (
        "Concurrent RST previews share initialization"
    )
    assert result["stats"]["destroyed"] == 2, "RST releases per-render Python globals"

    await boot(pg, base, rich=True, stubs=True)
    result = await pg.evaluate("""async () => ({
      html: await renderNode({name: 'large.rst'}, new Blob(['x'.repeat(512*1024+1)]), 'rst'),
      loaded: !!window.__pyStats
    })""")
    assert result["html"] is None and not result["loaded"], (
        "Oversize RST preserves the absent-preview limit without loading Python"
    )

    await boot(pg, base, rich=False, stubs=True)
    await preview(pg, "doc.rst")
    assert not await pg.evaluate("!!window.__pyStats"), (
        "RST consent off does not initialize the runtime"
    )
    await pg.click("#gear")
    await pg.click("#s-rich")
    await pg.wait_for_selector(".pv-rich em")
    assert await pg.inner_text(".pv-rich em") == "rst", (
        "Enabling RST consent renders the selected source"
    )
    await pg.click("#s-rich")
    await pg.wait_for_selector(".pv-text")
    assert not await pg.locator(".pv-rich").count(), (
        "Disabling RST consent restores source"
    )


def test_markdown_viewport(bundle, playwright, static_origin):
    """Wide Markdown stays reachable in normal and fullscreen previews."""
    from playwright.sync_api import expect

    with playwright.chromium.launch() as browser:
        page = browser.new_page()
        page.goto(f"{static_origin}/static/{bundle.name}")
        page.evaluate(VENDOR_MAP)
        # A slow initial fill must become one retained preview across resizes.
        page.evaluate("""() => {
          window.__viewportRenders = 0;
          const kind = classifyFile('wide.md').preview;
          const entry = RENDERERS.find((e) => e.kind === kind);
          RENDERERS.unshift({...entry, render: async (...args) => {
            __viewportRenders++;
            await new Promise((done) => setTimeout(done, 300));
            return entry.render(...args);
          }});
        }""")
        page.evaluate(r"""async () => {
          const text = '# Heading' + 'Long'.repeat(30) + '\n\n' +
            '**bold** and *italic* [https://example.com/' + 'path'.repeat(40) +
            '](https://example.com/)\n\n```python\n' +
            'print("' + 'code '.repeat(60) + '")\n```\n\n' +
            '| ' + Array(20).fill('Column').join(' | ') + ' |\n' +
            '| ' + Array(20).fill('---').join(' | ') + ' |\n' +
            '| ' + Array(20).fill('value').join(' | ') + ' |\n';
          await mount({kind: 'directory', name: 'vault',
            async *entries() { yield ['wide.md', {kind: 'file', name: 'wide.md',
              async getFile() { return new File([text], 'wide.md'); }}]; }});
        }""")
        page.locator('.row:has-text("wide.md")').click()
        page.wait_for_selector(".pv-markdown table")
        page.evaluate("window.__viewportPane = document.querySelector('#preview')")
        page.keyboard.press("ArrowRight")
        for width, height in ((390, 844), (320, 568), (844, 390), (1500, 900)):
            page.set_viewport_size({"width": width, "height": height})
            for fullscreen in (False, True):
                if fullscreen:
                    page.locator("#pv-fullscreen").click()
                # Wait for the retained pane to reach the new geometry.
                page.wait_for_function("""() => {
                  const pv = document.querySelector('#preview');
                  const pane = pv.getBoundingClientRect();
                  return pv === __viewportPane &&
                    pane.left >= -1 && pane.right <= innerWidth + 1 &&
                    pv.querySelectorAll('.pv-markdown td').length === 20;
                }""")
                sizes = page.evaluate("""() => {
                  const body = document.querySelector('.pv-body');
                  const doc = document.documentElement;
                  return {width: body.clientWidth, scroll: body.scrollWidth,
                    pageWidth: doc.clientWidth, pageScroll: doc.scrollWidth,
                    cells: body.querySelectorAll('.pv-markdown td').length};
                }""")
                assert sizes["cells"] == 20, (width, fullscreen, sizes)
                assert sizes["scroll"] <= sizes["width"] + 1, (width, fullscreen, sizes)
                assert sizes["pageScroll"] <= sizes["pageWidth"], sizes
                assert page.locator(".pv-markdown strong").inner_text() == "bold"
                assert page.locator(".pv-markdown em").inner_text() == "italic"
                assert (
                    page.locator(".pv-markdown a").get_attribute("href")
                    == "https://example.com/"
                )
                assert "code " * 60 in page.locator(".pv-markdown pre").text_content()
                table = page.locator(".pv-markdown table")
                expect(table.locator("td")).to_have_count(20)
                assert page.evaluate("__viewportRenders") == 1
                assert table.evaluate("""e => {
                  e.scrollLeft = e.scrollWidth;
                  return e.scrollWidth <= e.clientWidth + e.scrollLeft + 1;
                }""")
                if fullscreen:
                    page.locator("#pv-fullscreen").click()


def test_rst_viewport(bundle, playwright, static_origin, tmp_path):
    """Both RST containers fill the pane without changing document content."""
    from filemill.preview import _preview_rst

    source = tmp_path / "guide.rst"
    source.write_text("""Guide
=====

A command-line tool to capture stdin and command output for AI tools
(like `Roo Code`_, an AI-powered coding assistant for VSCode).

.. _Roo Code: https://example.com/

Some *emphasis*, **strong text**, and ``inline code``.

- First item
- Second item

.. code-block:: python

   def example():
       return 1
""")
    html = _preview_rst(source)
    with playwright.chromium.launch() as browser:
        page = browser.new_page(viewport={"width": 1500, "height": 900})
        page.goto(f"{static_origin}/static/{bundle.name}")
        page.evaluate(
            """async html => {
          RENDERERS.unshift({kind: 'rst', render: async () => html});
          await mount({kind: 'directory', name: 'vault',
            async *entries() { yield ['guide.rst', {kind: 'file', name: 'guide.rst',
              async getFile() { return new File(['source'], 'guide.rst'); }}]; }});
        }""",
            html,
        )
        page.locator('.row:has-text("guide.rst")').click()
        page.wait_for_selector(".preview-rst p")
        page.keyboard.press("ArrowRight")
        for container in ("preview-rst", "pv-rich"):
            page.locator("#pv-content > div").evaluate(
                "(e, name) => e.className = name", container
            )
            for width, height in ((1500, 900), (390, 844), (320, 568)):
                page.set_viewport_size({"width": width, "height": height})
                for fullscreen in (False, True):
                    if fullscreen:
                        page.locator("#pv-fullscreen").click()
                    page.wait_for_function("""() => {
                      const pane = document.querySelector('#preview').getBoundingClientRect();
                      return pane.left >= -1 && pane.right <= innerWidth + 1;
                    }""")
                    document = page.locator("#pv-content > div")
                    sizes = document.locator("p").first.evaluate("""p => ({
                      paragraph: p.getBoundingClientRect().width,
                      available: p.parentElement.getBoundingClientRect().width,
                      height: p.getBoundingClientRect().height,
                      line: parseFloat(getComputedStyle(p).lineHeight)
                    })""")
                    assert abs(sizes["paragraph"] - sizes["available"]) <= 1, (
                        container,
                        width,
                        sizes,
                    )
                    if width == 1500 and fullscreen:
                        assert sizes["height"] <= sizes["line"] + 1, sizes
                    assert document.locator("h1").inner_text() == "Guide"
                    assert document.locator("em").inner_text() == "emphasis"
                    assert document.locator("strong").inner_text() == "strong text"
                    assert (
                        document.locator("a").get_attribute("href")
                        == "https://example.com/"
                    )
                    assert document.locator("p .literal").inner_text() == "inline code"
                    assert document.locator("li").all_text_contents() == [
                        "First item",
                        "Second item",
                    ]
                    assert (
                        document.locator("pre").text_content()
                        == "def example():\n    return 1"
                    )
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                    if fullscreen:
                        page.locator("#pv-fullscreen").click()


async def test_offline(page, base, requests):
    pg = page
    # ── offline: the real CDN, no network ────────────────────────────
    await boot(pg, base, rich=True)
    await pg.click('.col[data-i="0"] .row:has-text("data.json")')
    await pg.wait_for_selector('.col[data-i="1"] .row:has-text("items")')
    await pg.click('.col[data-i="1"] .row:has-text("items")')
    await pg.wait_for_selector('.col[data-i="2"] .row:has-text("0")')
    await pg.click('.col[data-i="2"] .row:has-text("0")')
    assert "json value" in await pg.inner_text("#pv-content") and not [
        u for u in requests if "esm.sh" in u
    ], "Rich mode keeps JSON hierarchy client-side"
    html = await preview(pg, "note.md", ready=".pv-note")
    assert "Heading" in html and "pv-text" in html, (
        "Offline, a Markdown file still shows its source"
    )
    assert "pv-note" in html, "…and says why it is not rendered"

    html = await preview(pg, "plain.txt")
    assert "just text" in html and "pv-note" not in html, (
        "A file needing no renderer is unaffected offline"
    )
    html = await preview(pg, "doc.rst", ready=".pv-note")
    assert "Heading" in html and "pv-text" in html and "pv-note" in html, (
        "Offline, reStructuredText shows its source and says why"
    )
    html = await preview(pg, "deck.pptx", ready=".pv-pptx")
    assert "PowerPoint loaded" in html, html[:120]


async def test_consent_switch(page, base, requests):
    pg = page
    # ── the switch ───────────────────────────────────────────────────
    await boot(pg, base, rich=False)
    requests.clear()
    html = await preview(pg, "note.md")
    assert "pv-text" in html and "pv-note" not in html, (
        "Switched off, Markdown shows source with no apology"
    )
    assert not [u for u in requests if "esm.sh" in u], "; ".join(
        u for u in requests if "esm.sh" in u
    )
    await preview(pg, "doc.rst")
    assert not [u for u in requests if "jsdelivr" in u], "; ".join(
        u for u in requests if "jsdelivr" in u
    )
    await preview(pg, "deck.pptx")
    assert not [u for u in requests if "pptx" in u], "; ".join(
        u for u in requests if "pptx" in u
    )

    await pg.reload()
    await pg.wait_for_function(
        "document.querySelector('#s-rich')?.getAttribute('aria-checked') === 'false'"
    )
    assert await pg.evaluate("localStorage.getItem('filemill.rich')") == "off", (
        "The choice survives a reload — consent is not re-asked"
    )
    assert await pg.get_attribute("#s-rich", "aria-checked") == "false", (
        "…and the toggle reads back off"
    )


async def test_loaded_renderers(page, base, requests):
    pg = page
    # ── loaded: stub modules over loopback ───────────────────────────
    await boot(pg, base, rich=True, stubs=True)
    html = await preview(pg, "note.md")
    assert "<h1>Heading</h1>" in html and "pv-note" not in html, html[:90]
    assert "pv-rich" in html, "…into the shared rich-preview container"

    html = await preview(pg, "doc.rst")
    assert "<h1>Heading</h1>" in html and "pv-rich" in html and "pv-note" not in html, (
        html[:120]
    )

    requests.clear()
    html = await preview(pg, "deck.pptx", ready=".pv-pptx")
    assert "PowerPoint loaded" in html and not any(
        "pptx-viewer" in u for u in requests
    ), "PowerPoint renders slide text without a CDN viewer"
    html = await preview(pg, "broken.pptx", ready=".preview-error")
    assert "PowerPoint preview failed" in html, html[:120]

    requests.clear()
    html = await preview(pg, "fence.md")
    assert 'class="language-python"' in html and "hl-kw" in html, html[:200]
    assert not [u for u in requests if "highlight" in u], "; ".join(
        u for u in requests if "highlight" in u
    )
    assert "<br" not in html and "line one\nline two" in html, html[:200]

    requests.clear()
    html = await preview(pg, "code.py")
    assert "hl-kw" in html and "pv-note" not in html, html[:90]
    assert not [u for u in requests if "__stub" in u], "; ".join(
        u for u in requests if "__stub" in u
    )

    html = await preview(pg, "plain.txt")
    assert "pv-text" in html and "pv-rich" not in html, (
        "A plain .txt still takes the cheap path"
    )


async def test_wikilinks(page, base, requests):
    pg = page
    await boot(pg, base, rich=True, stubs=True)
    # ── wikilinks resolve in the folder, not on the web ──────────────
    await preview(pg, "note.md")
    before = await pg.evaluate("location.href")
    await pg.click("#pv-content a.wikilink")
    await pg.wait_for_function(
        "sel[0] === 'Other Note.md' && document.querySelector('#pv-content .pv-rich')"
    )
    assert await pg.evaluate("sel[0]") == "Other Note.md", str(await pg.evaluate("sel"))
    assert (await pg.evaluate("location.href")).split("#")[0] == before.split("#")[0], (
        "…without navigating the page away"
    )


async def test_vendored_renderers(page, base, requests):
    pg = page
    # ── the vendored modules the server edition serves ───────────────
    # The switch is off: a module from this origin is not a download the
    # visitor has to agree to, so it must render anyway.
    await boot(pg, base, rich=False, vendored=True)
    requests.clear()
    html = await preview(pg, "rich.md", ready=".pv-rich")
    assert "<h1" in html and "pv-note" not in html, html[:120]
    assert not [u for u in requests if "esm.sh" in u or "jsdelivr" in u], "; ".join(
        requests
    )
    assert 'class="task-list-item-checkbox"' in html and "checked" in html, (
        "A task list renders as a checkbox"
    )
    assert 'class="footnote-ref"' in html and 'class="footnotes"' in html, (
        "A footnote renders as a reference and a footnote list"
    )
    assert 'class="language-python"' in html and "hl-kw" in html, html[:300]
    assert 'class="wikilink" href="#" data-wiki="Other Note"' in html, (
        "A wikilink renders as an in-app anchor"
    )
    assert 'href="sib.md"' in html, html[:300]
    html = await preview(pg, "doc.docx", ready=".pv-rich")
    assert "<p>Hello docx</p>" in html and "pv-rich" in html, html[:120]


INERT = """(() => {
  const c = document.querySelector('#pv-content');
  return {
    markup: c.querySelectorAll('img, i, b, [onerror]').length,
    xss: window.__xss ?? null,
    text: c.innerText,
    wiki: [...c.querySelectorAll('a.wikilink')]
      .map((a) => [a.dataset.wiki, a.textContent, a.getAttribute('href')]),
    code: c.querySelector('code')?.textContent,
    sib: !!c.querySelector('a[href="sib.md"]'),
    footnote: !!c.querySelector('.footnote-ref') && !!c.querySelector('.footnotes'),
  };
})()"""

LINKS = """[...document.querySelectorAll('#pv-content a')]
  .map((a) => [a.textContent.trim(), a.getAttribute('href')])"""


async def test_markdown_stays_inert(page, base, requests):
    pg = page
    # ── crafted Markdown is text, beside a wikilink or not (A2) ──────
    await boot(pg, base, rich=False, vendored=True)
    html = await preview(pg, "inert.md", ready=".pv-rich")
    found = await pg.evaluate(INERT)
    assert found["markup"] == 0 and found["xss"] is None, html
    assert found["text"].count('<img src=x onerror="window.__xss=') == 3, found
    assert "[[x]" in found["text"], "A malformed wikilink stays as typed"
    assert found["wiki"] == [["Other Note", "the note", "#"]], found
    assert found["code"] == "<b>code</b>", found
    assert found["sib"] and found["footnote"], found


async def test_unsafe_urls_are_not_links(page, base, requests):
    pg = page
    # ── a link keeps its target only on the safe-protocol list (A2) ──
    await boot(pg, base, rich=False, vendored=True)
    html = await preview(pg, "links.docx", ready=".pv-rich a")
    assert await pg.evaluate(LINKS) == [
        ["run", None],
        ["page", None],
        ["web", "https://example.com/"],
        ["mail", "mailto:a@example.com"],
    ], html
    assert await pg.get_attribute("#pv-content img", "src") == (
        f"data:image/png;base64,{PIXEL}"
    ), "A picture in the document still shows"
    assert await pg.get_attribute("#pv-content img", "alt") == "a pixel", html

    html = await preview(pg, "script.desktop", ready=".pv-link")
    assert await pg.evaluate(LINKS) == [], html
    assert "javascript:window.__xss=4" in await pg.inner_text("#pv-content"), html
    html = await preview(pg, "web.desktop", ready=".pv-link")
    assert await pg.evaluate(LINKS) == [
        ["https://example.com/", "https://example.com/"]
    ], html
    assert await pg.evaluate("window.__xss ?? null") is None


async def test_rst_links_keep_only_safe_urls(page, base, requests):
    pg = page
    # ── docutils writes a target as given; the page drops unsafe ones ─
    await boot(pg, base, rich=True, stubs=True)
    await pg.evaluate(
        """window.__pyHTML = '<p><a class="reference external"'
          + ' href="javascript:window.__xss=5">run</a> <a class="reference'
          + ' external" href="https://example.com/">web</a> <a class="reference'
          + ' internal" href="#heading">up</a></p>'"""
    )
    html = await preview(pg, "doc.rst", ready=".pv-rich a")
    assert await pg.evaluate(LINKS) == [
        ["run", None],
        ["web", "https://example.com/"],
        ["up", "#heading"],
    ], html


async def test_rst_output_keeps_no_live_attribute(page, base, requests):
    pg = page
    # ── an SVG or object keeps no handler, xlink:href or data (S2) ───
    await boot(pg, base, rich=True, stubs=True)
    await pg.evaluate(
        """window.__pyHTML = '<p>picture</p><svg onload="window.__xss=7">'
          + '<a xlink:href="javascript:window.__xss=8"><text>x</text></a>'
          + '</svg><object data="javascript:window.__xss=9"></object>'"""
    )
    html = await preview(pg, "doc.rst", ready=".pv-rich p")
    assert (
        await pg.evaluate(
            """[...document.querySelectorAll('#pv-content *')]
          .flatMap((el) => [...el.attributes].map((a) => a.name))
          .filter((n) => n.startsWith('on') || n === 'data' || n === 'xlink:href')"""
        )
        == []
    ), html


def _docutils(source: str) -> str:
    """The HTML the browser's interpreter gets from docutils for *source*,
    with the settings of RST_PY in ui/adapters/preview-rich.js."""
    return publish_parts(
        source,
        writer_name="html5",
        settings_overrides={
            "raw_enabled": False,
            "file_insertion_enabled": False,
            "report_level": 5,
            "doctitle_xform": False,
            "initial_header_level": 1,
            "syntax_highlight": "none",
            "embed_stylesheet": False,
        },
    )["body"]


# Elements docutils never writes, which a document's text can still bring in.
FOREIGN = "<iframe></iframe><embed><form></form><base><svg><animate></animate></svg>"


async def test_rst_output_keeps_only_elements_docutils_writes(page, base, requests):
    pg = page
    # ── a video's alternative text and address are written unescaped ─
    await boot(pg, base, rich=True, stubs=True)
    await pg.evaluate(
        "html => window.__pyHTML = html",
        _docutils(
            f".. image:: clip.mp4\n   :alt: {FOREIGN}\n\n.. image:: {FOREIGN}.mp4\n"
        ),
    )
    html = await preview(pg, "doc.rst", ready=".pv-rich video")
    assert (
        await pg.evaluate(
            """[...document.querySelectorAll(
              '#pv-content :is(iframe, embed, form, base, svg, animate)')]
              .map((el) => el.localName)"""
        )
        == []
    ), html
    assert await pg.locator("#pv-content video").count() == 2, html


ORDINARY_RST = dedent(
    """\
    Heading
    =======

    Some *emphasis*, **strong**, ``literal``, :sub:`2`, :sup:`3`,
    :math:`a^2 + b^2`, a `link <https://example.com/>`_, a footnote [#]_
    and `Heading`_.

    .. [#] A footnote.

    - one
    - two

    3. three

    term
      definition

    +-----+-----+
    | A   | B   |
    +=====+=====+
    | spans both|
    +-----+-----+

    .. list-table::
       :widths: 30 70

       * - a
         - b

    .. code-block:: python
       :number-lines:

       return 1

    .. code-block:: python

       return 2

    .. image:: pics/cat.png
       :width: 50%
       :align: center

    .. figure:: pics/cat.png

       A caption.

    .. note:: A note.

    .. contents::
    """
)


async def test_ordinary_rst_keeps_everything_docutils_writes(page, base, requests):
    pg = page
    # ── the check drops nothing from an ordinary document ───────────
    await boot(pg, base, rich=True, stubs=True)
    written = _docutils(ORDINARY_RST)
    # rst() renames a highlighted block's classes before the check.
    expected = re.sub(
        r'<pre class="code (\S+) literal-block"><code>',
        r'<pre><code class="language-\1">',
        written,
    )
    shapes = await pg.evaluate(
        """async ([written, expected]) => {
          window.__pyHTML = written;
          const shape = (html) => [...new DOMParser()
            .parseFromString(html, 'text/html').body.querySelectorAll('*')]
            .map((el) => [el.localName, ...[...el.attributes]
              .map((a) => `${a.name}=${a.value}`).sort()].join(' '));
          const out = await renderNode({name: 'doc.rst'}, new Blob(['x']), 'rst');
          return {expected: shape(expected), got: shape(out).slice(1)};
        }""",
        [written, expected],
    )
    for tag in ("table", "pre", "img", "aside", "math"):
        assert any(s.split(" ")[0] == tag for s in shapes["expected"]), tag
    assert shapes["got"] == shapes["expected"]


async def test_consent_retry(page, base, requests):
    pg = page
    # ── turning it back on retries ───────────────────────────────────
    await boot(pg, base, rich=False, stubs=True)
    await preview(pg, "note.md")
    await pg.click("#gear")
    await pg.click("#s-rich")
    await pg.wait_for_function(
        "document.querySelector('#s-rich')?.getAttribute('aria-checked') === 'true'"
    )
    await preview(pg, "code.py")  # move the selection off note.md
    html = await preview(pg, "note.md")
    assert "<h1>Heading</h1>" in html, html[:90]
