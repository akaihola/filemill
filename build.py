#!/usr/bin/env python3
"""Build script: inlines src/ CSS and JS files into dist/index.html."""

import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC  = ROOT / "src"
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

template = (ROOT / "index.html").read_text(encoding="utf-8")

def inline_css(m: re.Match) -> str:
    href = m.group(1)
    path = ROOT / href
    css  = path.read_text(encoding="utf-8")
    return f"<style>\n{css}\n</style>"

def inline_js(m: re.Match) -> str:
    src  = m.group(1)
    path = ROOT / src
    js   = path.read_text(encoding="utf-8")
    return f"<script>\n{js}\n</script>"

result = template

# Inline <link rel="stylesheet" href="src/...css">
result = re.sub(
    r'<link\s+rel="stylesheet"\s+href="([^"]+\.css)">',
    inline_css,
    result,
)

# Inline <script src="src/...js"></script>
result = re.sub(
    r'<script\s+src="([^"]+\.js)"></script>',
    inline_js,
    result,
)

out = DIST / "index.html"
out.write_text(result, encoding="utf-8")
print(f"Built {out}  ({out.stat().st_size:,} bytes)")
