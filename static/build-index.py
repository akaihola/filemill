#!/usr/bin/env python3
"""Bundle the modular sources in src/ into the single-file index.html.

Dev entry point : index-dev.html  — plain <link>/<script src> references into
                  ../ui/, so it runs in the browser as-is with no build step.
Bundle          : index.html      — every reference inlined, including the Seti
                  icon font as a base64 data URI. No external requests at all
                  (the rich renderers are fetched later, on demand — see
                  ../ui/adapters/preview-rich.js).

Run ./build-index.py after editing anything in ../ui/, and
./build-index.py --check to verify the committed bundle matches the sources.
"""

import base64
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent          # filemill/
UI = HERE.parent / "ui"               # the shared frontend, one level up


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


html = (HERE / "index-dev.html").read_text(encoding="utf-8")
html, n_css = re.subn(r'<link rel="stylesheet" href="([^"]+)">', inline_css, html)
html, n_js = re.subn(r'<script src="([^"]+)"></script>', inline_js, html)
if not n_css:
    raise SystemExit("no stylesheet reference found in index-dev.html")

out = HERE / "index.html"

# The bundle is generated *and* committed, which is the arrangement that lets
# anyone download one file — and the arrangement that silently ships a stale
# one. CI runs --check so a src/ edit without a rebuild fails the build instead
# of quietly publishing last week's app.
if "--check" in sys.argv:
    current = out.read_text(encoding="utf-8") if out.is_file() else None
    if current == html:
        print(f"{out.name} is up to date ({len(html.encode()):,} bytes)")
        raise SystemExit(0)
    print(f"{out.name} is stale — run ./build-index.py", file=sys.stderr)
    raise SystemExit(1)

out.write_text(html, encoding="utf-8")
print(f"Built {out.name}  ({out.stat().st_size:,} bytes, {n_css} css + {n_js} js inlined)")
