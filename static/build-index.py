#!/usr/bin/env python3
"""Bundle the modular sources in ../ui/ into the single-file index.html.

Dev entry point : index-dev.html  — a stylesheet <link>, the icon-map <script>
                  and one <script type="module"> for ../ui/entry-static.js, so
                  it runs in the browser as-is with no build step.
Bundle          : index.html      — every reference inlined, including the Seti
                  icon font as a base64 data URI and the whole module graph as
                  one inline module. No external requests at all (the rich
                  renderers are fetched later, on demand — see
                  ../ui/adapters/preview-rich.js).

The module graph is walked from the entry the way a browser evaluates it:
depth-first, each module after its imports, each module once. The bodies are
concatenated in that order with the import lines and the `export` keywords
removed, so the bundle and the dev page evaluate identically — cycles included.
Only relative imports and `export` on declarations are understood; anything
else is refused at build time rather than shipped broken.

Run ./build-index.py after editing anything in ../ui/, and
./build-index.py --check to verify the committed bundle matches the sources.
"""

import base64
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent          # filemill/
UI = HERE.parent / "ui"               # the shared frontend, one level up

IMPORT = re.compile(r'^import\s*(?:\{[^}]*\}\s*from\s*)?"(\.[^"]+)";\n?', re.M)
EXPORT = re.compile(r"^export (?=(?:async |function|const|let|var|class))", re.M)
EMPTY_EXPORT = re.compile(r"^export \{\};\n?", re.M)
DECLARATION = re.compile(r"^(?:async\s+)?(?:function|const|let|var|class)\s+(\w+)", re.M)


def read(ref: str) -> str:
    """Resolve an href the way the browser would, from index-dev.html."""
    return (HERE / ref).resolve().read_text(encoding="utf-8")


def inline_css(m: re.Match) -> str:
    css = read(m.group(1))
    # the one asset a stylesheet can't carry itself: the icon font
    font = (UI / "vendor/seti.woff").read_bytes()
    data = base64.b64encode(font).decode("ascii")
    css = re.sub(
        r'src: url\("[^"]*seti\.woff"\) format\("woff"\);[^\n]*',
        f'src: url("data:font/woff;base64,{data}") format("woff");',
        css,
    )
    return f"<style>\n{css.strip()}\n</style>"


def inline_js(m: re.Match) -> str:
    return f"<script>\n{read(m.group(1)).strip()}\n</script>"


def module_graph(entry: Path) -> list[Path]:
    """Every module reachable from *entry*, in browser evaluation order."""
    order: list[Path] = []
    seen: set[Path] = set()

    def visit(path: Path) -> None:
        if path in seen:
            return
        seen.add(path)
        text = path.read_text(encoding="utf-8")
        for m in IMPORT.finditer(text):
            visit((path.parent / m.group(1)).resolve())
        order.append(path)

    visit(entry.resolve())
    return order


def module_body(path: Path) -> str:
    """The module with its import lines and `export` keywords removed."""
    name = path.relative_to(UI.resolve()).as_posix()
    text = path.read_text(encoding="utf-8")
    for bad, why in (
        (r"^import\s+(?!\{|\")", "default and namespace imports"),
        (r"^import\s*\{[^}]*\bas\b", "renaming imports"),
        (r"^import\s*(?:\{[^}]*\}\s*from\s*)?\"[^.]", "non-relative imports"),
        (r"^export\s+(?:default\b|\{[^}]*\w)", "export lists and default exports"),
    ):
        if re.search(bad, text, re.M):
            raise SystemExit(f"{name}: {why} cannot be inlined")
    text = EMPTY_EXPORT.sub("", IMPORT.sub("", text))
    return f"/* ═══ {name} ═══ */\n{EXPORT.sub('', text).strip()}\n"


def inline_module(m: re.Match) -> str:
    modules = module_graph(HERE / m.group(1))
    bodies = [module_body(p) for p in modules]
    seen: dict[str, str] = {}
    for path, body in zip(modules, bodies):
        for name in DECLARATION.findall(body):
            if name in seen:
                raise SystemExit(
                    f"{path.name} and {seen[name]} both declare {name}; "
                    "one module scope cannot hold both"
                )
            seen[name] = path.name
    inline_module.count = len(modules)
    return '<script type="module">\n' + "\n".join(bodies) + "</script>"


html = (HERE / "index-dev.html").read_text(encoding="utf-8")
html, n_css = re.subn(r'<link rel="stylesheet" href="([^"]+)">', inline_css, html)
html, n_mod = re.subn(
    r'<script type="module" src="([^"]+)"></script>', inline_module, html
)
html, n_js = re.subn(r'<script src="([^"]+)"></script>', inline_js, html)
if not n_css:
    raise SystemExit("no stylesheet reference found in index-dev.html")
if n_mod != 1:
    raise SystemExit("index-dev.html must load exactly one entry module")

out = HERE / "index.html"

# The bundle is generated *and* committed, which is the arrangement that lets
# anyone download one file — and the arrangement that silently ships a stale
# one. CI runs --check so a ui/ edit without a rebuild fails the build instead
# of quietly publishing last week's app.
if "--check" in sys.argv:
    current = out.read_text(encoding="utf-8") if out.is_file() else None
    if current == html:
        print(f"{out.name} is up to date ({len(html.encode()):,} bytes)")
        raise SystemExit(0)
    print(f"{out.name} is stale — run ./build-index.py", file=sys.stderr)
    raise SystemExit(1)

out.write_text(html, encoding="utf-8")
print(
    f"Built {out.name}  ({out.stat().st_size:,} bytes, {n_css} css + {n_js} js "
    f"+ {inline_module.count} modules inlined)"
)
