#!/usr/bin/env python3
"""filemill rich-preview suite — the one feature that touches the network.

Rich rendering (Markdown, .docx, reStructuredText) is fetched from a CDN on first
use rather than bundled: the libraries are an order of magnitude larger than the
app, and the reStructuredText one is a Python runtime. That buys
parity with filemill's Python renderers at no cost to the single file, and it
costs the promise that nothing leaves the browser — so the behaviour that
matters is what happens when the download does not arrive, and whether the
switch that turns it off is honoured. Syntax highlighting is no longer on that
list: core/syntax.js colours source in the page, so it is checked here only to
the extent that it needs no download at all.

The offline path is forced here by a Playwright route that aborts `esm.sh` and
`cdn.jsdelivr.net` requests, so it is tested the same way on networked and
networkless hosts. The *loaded* path is exercised against stub modules served
from the same loopback server, which is the only way to reach it without the
real CDN.

    uv run --with "playwright==1.61.0" python3 test-rich.py [--bundle|--dev] [--rst]

The server edition serves the Markdown and .docx modules itself from ui/vendor/
and points FILEMILL_CDN at them; the last section here loads those real files
over the same loopback server, which is also where the renderers' output is
checked against what filemill's Python renderers used to produce.
"""
import asyncio
import base64
import io
import zipfile
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path


# Serve the repository, not filemill/: the dev entry point references ../ui/,
# which is the whole point of the shared directory.
ROOT = Path(__file__).parent.parent
TARGET = "static/" + ("index-dev.html" if "--dev" in sys.argv else "index.html")

# The smallest .docx mammoth accepts: the package relationship that names the
# document part, and one paragraph in it.
def _docx(text: str) -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
            'openxmlformats.org/package/2006/content-types"><Default Extension="xml" '
            'ContentType="application/xml"/><Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.'
            'wordprocessingml.document.main+xml"/></Types>'))
        z.writestr("_rels/.rels", (
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://'
            'schemas.openxmlformats.org/package/2006/relationships"><Relationship '
            'Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="word/document.xml"/></Relationships>'))
        z.writestr("word/document.xml", (
            '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://'
            'schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p>'
            f'<w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>'))
    return base64.b64encode(buf.getvalue()).decode()


FAKE = r"""
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
    B('doc.docx', '%(docx)s'),
    F('doc.rst', 'Heading\n=======\n\nSome *rst* text.\n'),
    F('code.py', 'def f():\n    return 1\n'),
    F('plain.txt', 'just text'),
    F('data.json', '{"items":["json value"],"count":2}'),
    F('deck.pptx', 'pptx bytes'),
    F('broken.pptx', 'bad'),
  ]);
};
""" % {"docx": _docx("Hello docx")}

# Enough of each library's shape to prove the plumbing: the loader, the plugin
# chaining, the highlight hook, and where the output lands. Faithfulness to the
# real renderers is the CDN's problem, not this suite's.
STUBS = {
    "pptx-viewer.js": """
export function createPptxViewer(host, options) {
  /* the real viewer reports a deck it cannot open through onError */
  if (options.source.size < 5) options.onError('bad deck');
  else host.innerHTML = '<div class="pptx-stub">PowerPoint loaded</div>';
  return { destroy() {} };
}
""",
    "markdown-it.js": """
export default class MarkdownIt {
  constructor(o) { this.options = o; this.renderer = { rules: {} }; this.core = { ruler: { push: (n, f) => { this._rule = f; } } }; }
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
      await new Promise(resolve => setTimeout(resolve, 10));
      if (window.__pyFail === 'render') throw Error('render failed');
      const text = options?.globals.src ?? src;
      const escaped = text.replaceAll('&', '&amp;').replaceAll('<', '&lt;');
      return '<section><h1>Heading</h1><p>Some <em>rst</em> text.</p>' +
        '<pre>' + escaped + '</pre></section>';
    },
  };
}
""",
}

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"  {'✅' if cond else '❌'}  {name}" + (f" — {detail}" if detail else ""))


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves the repo, plus the stub modules under /__stub/."""

    def log_message(self, format: str, *args) -> None:
        pass

    def do_GET(self) -> None:
        name = self.path.rsplit("/", 1)[-1]
        if self.path.startswith("/__stub/") and name in STUBS:
            body = STUBS[name].encode()
            kind = "text/css" if name.endswith(".css") else "application/javascript"
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


def serve():
    httpd = socketserver.TCPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=str(ROOT))
    )
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


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
        f"localStorage.setItem('filemill.rich', {'\"on\"' if rich else '\"off\"'})"
    )
    if stubs:
        await pg.evaluate(STUB_MAP % {"b": "/".join(base.split("/")[:3])})
    if vendored:
        await pg.evaluate(VENDOR_MAP)
    await pg.evaluate(FAKE)
    await pg.evaluate("mount(__mk())")
    await pg.wait_for_timeout(250)


async def preview(pg, name, timeout=4000, ready=None):
    await pg.click(f'.col[data-i="0"] .row:has-text("{name}")')
    await pg.wait_for_selector("#pv-content > *", timeout=timeout)
    if ready:
        await pg.wait_for_selector(ready, timeout=timeout)
    return await pg.inner_html("#pv-content")


async def rst_checks(pg, base):
    await boot(pg, base, rich=True)
    html = await preview(pg, "doc.rst", ready=".pv-note")
    check("RST offline fallback keeps readable source", "Heading" in html and "pv-text" in html)
    requests = []
    def record(request):
        if '/pyodide/' in request.url:
            requests.append(request.url)
    pg.on('request', record)
    await boot(pg, base, rich=False)
    html = await preview(pg, "doc.rst")
    check("RST consent off requests no runtime assets", not requests and "pv-note" not in html)
    pg.remove_listener('request', record)
    await pg.reload()
    check("RST consent survives reload", await pg.evaluate("localStorage.getItem('filemill.rich')") == "off")
    # RST registry failures and interpreter lifetime, without a real CDN.
    for failure in ('boot', 'package', 'render'):
        await boot(pg, base, rich=True, stubs=True)
        await pg.evaluate("failure => window.__pyFail = failure", failure)
        html = await preview(pg, "doc.rst", ready=".pv-note")
        check(f"RST {failure} failure falls back to source",
              "pv-text" in html and "Heading" in html)
        if failure == 'render':
            check("Failed RST conversion releases Python globals",
                  await pg.evaluate("window.__pyStats.destroyed") == 1)
        await pg.evaluate("window.__pyFail = null")
        await preview(pg, "plain.txt")
        html = await preview(pg, "doc.rst", ready=".pv-rich")
        check(f"RST retries after {failure} failure", "<em>rst</em>" in html)

    await boot(pg, base, rich=True, stubs=True)
    result = await pg.evaluate("""async () => {
      const outputs = await Promise.all(['first document', 'second document'].map(
        text => renderNode({name: 'doc.rst'}, new Blob([text]), 'rst')));
      return {outputs, stats: window.__pyStats};
    }""")
    check("Concurrent RST previews keep their own source",
          'first document' in result['outputs'][0]
          and 'second document' not in result['outputs'][0]
          and 'second document' in result['outputs'][1])
    check("Concurrent RST previews share initialization",
          result['stats']['boots'] == result['stats']['packages'] == 1)
    check("RST releases per-render Python globals",
          result['stats']['destroyed'] == 2)

    await boot(pg, base, rich=True, stubs=True)
    result = await pg.evaluate("""async () => ({
      html: await renderNode({name: 'large.rst'}, new Blob(['x'.repeat(512*1024+1)]), 'rst'),
      loaded: !!window.__pyStats
    })""")
    check("Oversize RST preserves the absent-preview limit without loading Python",
          result['html'] is None and not result['loaded'])

    await boot(pg, base, rich=False, stubs=True)
    await preview(pg, "doc.rst")
    check("RST consent off does not initialize the runtime",
          not await pg.evaluate("!!window.__pyStats"))
    await pg.click("#gear")
    await pg.click("#s-rich")
    await pg.wait_for_selector(".pv-rich em")
    check("Enabling RST consent renders the selected source",
          await pg.inner_text(".pv-rich em") == "rst")
    await pg.click("#s-rich")
    await pg.wait_for_selector(".pv-text")
    check("Disabling RST consent restores source", not await pg.locator(".pv-rich").count())


async def rst_main(bundle, fake_handle, playwright):
    global TARGET, FAKE
    TARGET, FAKE = f"static/{bundle.name}", fake_handle
    httpd, port = serve()
    try:
        async with playwright.async_playwright() as p:
            async with await p.chromium.launch() as browser:
                pg = await browser.new_page(viewport={"width": 1500, "height": 900})
                await pg.route("https://cdn.jsdelivr.net/**", lambda r: r.abort())
                await rst_checks(pg, f"http://127.0.0.1:{port}/{TARGET}")
    finally:
        httpd.shutdown()
        httpd.server_close()
    print(f"{len(passed)} passed, {len(failed)} failed")
    sys.exit(1 if failed else 0)


async def main(bundle, fake_handle, playwright):
    global TARGET, FAKE
    TARGET, FAKE = f"static/{bundle.name}", fake_handle
    httpd, port = serve()
    base = f"http://127.0.0.1:{port}/{TARGET}"

    async with playwright.async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        # Block the real CDN so the offline path is tested on every host.
        await pg.route("https://esm.sh/**", lambda r: r.abort())
        await pg.route("https://cdn.jsdelivr.net/**", lambda r: r.abort())
        requests = []
        pg.on("request", lambda r: requests.append(r.url))

        print(f"\n── {TARGET}: rich previews ──────────────────────────────────")

        # ── offline: the real CDN, no network ────────────────────────────
        await boot(pg, base, rich=True)
        await pg.click('.col[data-i="0"] .row:has-text("data.json")')
        await pg.wait_for_selector('.col[data-i="1"] .row:has-text("items")')
        await pg.click('.col[data-i="1"] .row:has-text("items")')
        await pg.wait_for_selector('.col[data-i="2"] .row:has-text("0")')
        await pg.click('.col[data-i="2"] .row:has-text("0")')
        check("Rich mode keeps JSON hierarchy client-side",
              "json value" in await pg.inner_text("#pv-content")
              and not [u for u in requests if "esm.sh" in u])
        html = await preview(pg, "note.md", ready=".pv-note")
        check("Offline, a Markdown file still shows its source",
              "Heading" in html and "pv-text" in html)
        check("…and says why it is not rendered", "pv-note" in html)

        html = await preview(pg, "plain.txt")
        check("A file needing no renderer is unaffected offline",
              "just text" in html and "pv-note" not in html)
        html = await preview(pg, "doc.rst", ready=".pv-note")
        check("Offline, reStructuredText shows its source and says why",
              "Heading" in html and "pv-text" in html and "pv-note" in html)
        html = await preview(pg, "deck.pptx", ready=".preview-error")
        check("Offline, a PowerPoint file says the viewer is unavailable",
              "PowerPoint preview unavailable" in html, html[:120])

        # ── the switch ───────────────────────────────────────────────────
        await boot(pg, base, rich=False)
        requests.clear()
        html = await preview(pg, "note.md")
        check("Switched off, Markdown shows source with no apology",
              "pv-text" in html and "pv-note" not in html)
        check("Switched off, nothing is requested from a CDN",
              not [u for u in requests if "esm.sh" in u],
              "; ".join(u for u in requests if "esm.sh" in u))
        await preview(pg, "doc.rst")
        check("Switched off, no Python runtime is requested either",
              not [u for u in requests if "jsdelivr" in u],
              "; ".join(u for u in requests if "jsdelivr" in u))
        await preview(pg, "deck.pptx")
        check("Switched off, no PowerPoint viewer is requested either",
              not [u for u in requests if "pptx" in u],
              "; ".join(u for u in requests if "pptx" in u))

        await pg.reload()
        await pg.wait_for_timeout(300)
        check("The choice survives a reload — consent is not re-asked",
              await pg.evaluate("localStorage.getItem('filemill.rich')") == "off")
        check("…and the toggle reads back off",
              await pg.get_attribute("#s-rich", "aria-checked") == "false")

        # ── loaded: stub modules over loopback ───────────────────────────
        await boot(pg, base, rich=True, stubs=True)
        html = await preview(pg, "note.md")
        check("With the renderer available, Markdown renders",
              "<h1>Heading</h1>" in html and "pv-note" not in html, html[:90])
        check("…into the shared rich-preview container", "pv-rich" in html)

        html = await preview(pg, "doc.rst")
        check("With the runtime available, reStructuredText renders",
              "<h1>Heading</h1>" in html and "pv-rich" in html
              and "pv-note" not in html, html[:120])

        requests.clear()
        html = await preview(pg, "deck.pptx", ready=".pptx-stub")
        check("With the viewer available, a PowerPoint file is mounted in it",
              "PowerPoint loaded" in html and "pv-pptx" in html, html[:120])
        check("…and the viewer module is the one requested",
              [u for u in requests if "pptx-viewer.js" in u],
              "; ".join(requests))
        html = await preview(
            pg, "broken.pptx", ready='.pv-pptx:has-text("PowerPoint preview failed")'
        )
        check("A deck the viewer rejects shows the viewer's message",
              "PowerPoint preview failed: bad deck" in html, html[:120])

        requests.clear()
        html = await preview(pg, "fence.md")
        check("A fenced block is coloured by core/syntax.js, not a download",
              'class="language-python"' in html and "hl-kw" in html, html[:200])
        check("…and no highlighter module is requested for it",
              not [u for u in requests if "highlight" in u],
              "; ".join(u for u in requests if "highlight" in u))
        check("A paragraph's source newline is not a rendered line break",
              "<br" not in html and "line one\nline two" in html, html[:200])

        requests.clear()
        html = await preview(pg, "code.py")
        check("Source is coloured in the page, not by a downloaded renderer",
              "hl-kw" in html and "pv-note" not in html, html[:90])
        check("…so previewing source asks for no module at all",
              not [u for u in requests if "__stub" in u],
              "; ".join(u for u in requests if "__stub" in u))

        html = await preview(pg, "plain.txt")
        check("A plain .txt still takes the cheap path",
              "pv-text" in html and "pv-rich" not in html)

        # ── wikilinks resolve in the folder, not on the web ──────────────
        await preview(pg, "note.md")
        before = await pg.evaluate("location.href")
        await pg.click("#pv-content a.wikilink")
        await pg.wait_for_timeout(400)
        check("A wikilink selects the file it names",
              await pg.evaluate("sel[0]") == "Other Note.md",
              str(await pg.evaluate("sel")))
        check("…without navigating the page away",
              (await pg.evaluate("location.href")).split("#")[0] == before.split("#")[0])

        # ── the vendored modules the server edition serves ───────────────
        # The switch is off: a module from this origin is not a download the
        # visitor has to agree to, so it must render anyway.
        await boot(pg, base, rich=False, vendored=True)
        requests.clear()
        html = await preview(pg, "rich.md", ready=".pv-rich")
        check("A vendored renderer is used even with the switch off",
              "<h1" in html and "pv-note" not in html, html[:120])
        check("…and nothing is asked of a CDN for it",
              not [u for u in requests if "esm.sh" in u or "jsdelivr" in u],
              "; ".join(requests))
        check("A task list renders as a checkbox",
              'class="task-list-item-checkbox"' in html and 'checked' in html)
        check("A footnote renders as a reference and a footnote list",
              'class="footnote-ref"' in html and 'class="footnotes"' in html)
        check("A fenced block is coloured by core/syntax.js",
              'class="language-python"' in html and "hl-kw" in html, html[:300])
        check("A wikilink renders as an in-app anchor",
              'class="wikilink" href="#" data-wiki="Other Note"' in html)
        check("A relative link in a browser-opened folder stays as written",
              'href="sib.md"' in html, html[:300])
        html = await preview(pg, "doc.docx", ready=".pv-rich")
        check("A .docx renders through the vendored mammoth",
              "<p>Hello docx</p>" in html and "pv-rich" in html, html[:120])

        await rst_checks(pg, base)

        # ── turning it back on retries ───────────────────────────────────
        await boot(pg, base, rich=False, stubs=True)
        await preview(pg, "note.md")
        await pg.click("#gear")
        await pg.click("#s-rich")
        await pg.wait_for_timeout(200)
        await preview(pg, "code.py")          # move the selection off note.md
        html = await preview(pg, "note.md")
        check("Turning it back on takes effect without a reload",
              "<h1>Heading</h1>" in html, html[:90])

        await b.close()

    httpd.shutdown()
    print(f"\n{'═' * 62}\n  {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("  Failed: " + ", ".join(failed))
    print("═" * 62)
    sys.exit(1 if failed else 0)


def test_rich(bundle, fake_handle, playwright):
    asyncio.run(rst_main(bundle, fake_handle, playwright) if "--rst" in sys.argv
                else main(bundle, fake_handle, playwright))
