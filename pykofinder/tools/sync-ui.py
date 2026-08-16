#!/usr/bin/env python3
"""Copy the shared Miller-columns UI from a filemill checkout into the package.

`src/pykofinder/ui/` is a *vendored copy*, not a fork: it is overwritten
wholesale by this script and must never be hand-edited. The upstream is
filemill's `src/`, whose `core/` is source-agnostic and whose `adapters/` carry
both the File System Access API and the HTTP flavours — see
`src/adapters/README.md` there.

The copy keeps filemill's directory shape — `ui/src/{core,adapters}` beside
`ui/vendor` — so that relative references inside the files resolve unchanged.
`styles.css` reaches the icon font as `../../vendor/seti.woff`, and flattening
one level out of the tree is enough to 404 it. Byte-identical copies are also
what makes `--check` a meaningful test.

    tools/sync-ui.py [path/to/filemill]        # defaults to ../filemill
    tools/sync-ui.py --check                   # exit 1 if the copy is stale

The copy exists because the two projects are separate repositories today. Once
they share one, this whole script is replaced by the two of them pointing at the
same directory — which is the point of keeping the copy mechanical and the diff
empty.
"""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "src" / "pykofinder"
DEST = PKG / "ui"

# What the server build needs. app-fsa.js and index.html are the static build's
# entry points and are deliberately left behind.
WANTED = {
    "core": [
        "styles.css",
        "shell.js",
        "ports.js",
        "icons.js",
        "state.js",
        "render.js",
        "layout.js",
        "trail.js",
        "nav.js",
        "deeplink.js",
        "settings.js",
    ],
    "adapters": [
        "http.js",
        "preview-http.js",
        "preview-local.js",
        "preview-upload.js",
        "router-path.js",
        "storage.js",
        "fsa.js",
        "app-http.js",
        "README.md",
    ],
    "vendor": ["seti-map.js", "seti.woff", "SETI-LICENSE.md"],
}


def sources(src_root: Path) -> list[tuple[Path, Path]]:
    """Return (source, destination) pairs, erroring on anything missing."""
    pairs = []
    for sub, names in WANTED.items():
        rel = "vendor" if sub == "vendor" else f"src/{sub}"
        for name in names:
            f = src_root / rel / name
            if not f.is_file():
                raise SystemExit(f"missing upstream file: {f}")
            pairs.append((f, DEST / rel / name))
    return pairs


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--check"]
    check = "--check" in sys.argv
    src_root = Path(args[0]) if args else PKG.parent.parent.parent / "filemill"
    src_root = src_root.resolve()
    if not (src_root / "src" / "core" / "ports.js").is_file():
        raise SystemExit(f"not a filemill checkout: {src_root}")

    pairs = sources(src_root)

    if check:
        stale = [
            d
            for s, d in pairs
            if not d.is_file() or not filecmp.cmp(s, d, shallow=False)
        ]
        for d in stale:
            print(f"stale: {d.relative_to(PKG)}")
        if stale:
            print(
                f"\n{len(stale)} file(s) differ from {src_root} — run tools/sync-ui.py"
            )
            return 1
        print(f"ui/ is in sync with {src_root}")
        return 0

    if DEST.exists():
        shutil.rmtree(DEST)
    for s, d in pairs:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    print(
        f"Synced {len(pairs)} files from {src_root} → {DEST.relative_to(PKG.parent.parent)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
