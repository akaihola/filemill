#!/usr/bin/env python3
"""filemill rich-preview suite — the one feature that touches the network.

Rich rendering (Markdown, syntax highlighting, .docx) is fetched from a CDN on
first use rather than bundled: the libraries are an order of magnitude larger
than the app. That buys parity with pykofinder's Python renderers at no cost to
the 140 KB single file, and it costs the promise that nothing leaves the
browser — so the behaviour that matters is what happens when the download does
not arrive, and whether the switch that turns it off is honoured.

Both are tested here for real: this sandbox has no network, so the offline path
is not simulated. The *loaded* path is exercised against stub modules served
from the same loopback server, which is the only way to reach it offline.

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

ROOT = Path(__file__).parent
TARGET = "src/index.html" if "--dev" in sys.argv else "index.html"

FAKE = r"""
window.__mk = () => {
  const F = (name, text) => ({kind:'file', name,
    getFile: async () => new File([text], name, {lastModified: Date.parse('2026-08-01')})});
  const D = (name, kids) => ({kind:'directory', name,
    entries: async function*(){ for (const k of kids) yield [k.name, k]; }});
  return D('vault', [
    F('note.md', '# Heading\n\nSome **bold** text and a [[Other Note]] link.\n'),
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
    const body = src.replace(/\\[\\[([^\\]]+)\\]\\]/g,
      (_, t) => `<a class="wikilink" href="#" data-wiki="${t.trim()}">${t.trim()}</a>`);
    return `<h1>${first}</h1><p>${body.split('\\n').slice(2).join(' ')}</p>`;
  }
}
""",
    "plugin.js": "export default function noop() {}\n",
    "highlight.js": """
export default {
  getLanguage: (l) => l === 'py' || l === 'python',
  highlight: (t) => ({ value: '<span class="hljs-stub">' + t + '</span>' }),
  highlightAuto: (t) => ({ value: '<span class="hljs-auto">' + t + '</span>' }),
};
""",
    "hljs.css": ".hljs-stub { color: rebeccapurple }\n",
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
  "highlight.js":           "%(b)s/__stub/highlight.js",
  "hljs-css":               "%(b)s/__stub/hljs.css",
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

        html = await preview(pg, "code.py")
        check("Source is highlighted rather than escaped",
              "hljs-stub" in html and "pv-note" not in html, html[:90])

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
        html = await preview(pg, "code.py")
        check("Turning it back on takes effect without a reload",
              "hljs-stub" in html, html[:90])

        await b.close()

    httpd.shutdown()
    print(f"\n{'═' * 62}\n  {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("  Failed: " + ", ".join(failed))
    print("═" * 62)
    sys.exit(1 if failed else 0)


asyncio.run(main())
