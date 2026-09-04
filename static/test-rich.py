#!/usr/bin/env python3
"""filemill rich-preview suite — the one feature that touches the network.

Rich rendering (Markdown, .docx) is fetched from a CDN on first use rather than
bundled: the libraries are an order of magnitude larger than the app. That buys
parity with filemill's Python renderers at no cost to the single file, and it
costs the promise that nothing leaves the browser — so the behaviour that
matters is what happens when the download does not arrive, and whether the
switch that turns it off is honoured. Syntax highlighting is no longer on that
list: core/syntax.js colours source in the page, so it is checked here only to
the extent that it needs no download at all.

The offline path is forced here by a Playwright route that aborts `esm.sh`
requests, so it is tested the same way on networked and networkless hosts. The
*loaded* path is exercised against stub modules served from the same loopback
server, which is the only way to reach it without the real CDN.

    uv run --with "playwright==1.61.0" python3 test-rich.py [--bundle|--dev]
"""
import asyncio
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.async_api import async_playwright

# Serve the repository, not filemill/: the dev entry point references ../ui/,
# which is the whole point of the shared directory.
ROOT = Path(__file__).parent.parent
TARGET = "static/" + ("index-dev.html" if "--dev" in sys.argv else "index.html")

FAKE = r"""
window.__mk = () => {
  const F = (name, text) => ({kind:'file', name,
    getFile: async () => new File([text], name, {lastModified: Date.parse('2026-08-01')})});
  const D = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  return D('vault', [
    F('note.md', '# Heading\n\nSome **bold** text and a [[Other Note]] link.\n'),
    F('fence.md', '# Code\n\nline one\nline two\n\n```python\ndef f():\n    return 1\n```\n'),
    F('Other Note.md', '# Other\n'),
    F('code.py', 'def f():\n    return 1\n'),
    F('plain.txt', 'just text'),
  ]);
};
"""

# Enough of each library's shape to prove the plumbing: the loader, the plugin
# chaining, the highlight hook, and where the output lands. Faithfulness to the
# real renderers is the CDN's problem, not this suite's.
STUBS = {
    "markdown-it.js": """
export default class MarkdownIt {
  constructor(o) { this.options = o; this.core = { ruler: { push: (n, f) => { this._rule = f; } } }; }
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
};
"""


async def boot(pg, base, *, rich=True, stubs=False):
    """Load the app cold with the switch in a known state."""
    await pg.goto("about:blank")
    await pg.goto(base)
    await pg.evaluate(
        f"localStorage.setItem('filemill.rich', {'\"on\"' if rich else '\"off\"'})"
    )
    if stubs:
        await pg.evaluate(STUB_MAP % {"b": "/".join(base.split("/")[:3])})
    await pg.evaluate(FAKE)
    await pg.evaluate("mount(__mk())")
    await pg.wait_for_timeout(250)


async def preview(pg, name, timeout=4000):
    await pg.click(f'.col[data-i="0"] .row:has-text("{name}")')
    await pg.wait_for_selector("#pv-content > *", timeout=timeout)
    await pg.wait_for_timeout(250)
    return await pg.inner_html("#pv-content")


async def main():
    httpd, port = serve()
    base = f"http://127.0.0.1:{port}/{TARGET}"

    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1500, "height": 900})
        # Block the real CDN so the offline path is tested on every host.
        await pg.route("https://esm.sh/**", lambda r: r.abort())
        requests = []
        pg.on("request", lambda r: requests.append(r.url))

        print(f"\n── {TARGET}: rich previews ──────────────────────────────────")

        # ── offline: the real CDN, no network ────────────────────────────
        await boot(pg, base, rich=True)
        html = await preview(pg, "note.md")
        check("Offline, a Markdown file still shows its source",
              "Heading" in html and "pv-text" in html)
        check("…and says why it is not rendered", "pv-note" in html)

        html = await preview(pg, "plain.txt")
        check("A file needing no renderer is unaffected offline",
              "just text" in html and "pv-note" not in html)

        # ── the switch ───────────────────────────────────────────────────
        await boot(pg, base, rich=False)
        requests.clear()
        html = await preview(pg, "note.md")
        check("Switched off, Markdown shows source with no apology",
              "pv-text" in html and "pv-note" not in html)
        check("Switched off, nothing is requested from a CDN",
              not [u for u in requests if "esm.sh" in u],
              "; ".join(u for u in requests if "esm.sh" in u))

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


asyncio.run(main())
