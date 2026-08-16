#!/usr/bin/env python3
"""Copy the repository's shared UI into the Python package.

The source of truth is `../ui/` at the repository root: the same directory
filemill builds its single-file bundle from, and the reason the two frontends
cannot drift — one repository, one commit, both projects.

`src/pykofinder/ui/` is a copy of it and must never be hand-edited. The copy is
about packaging, not drift: a wheel cannot reach outside its own package
directory, so what `pip install pykofinder` needs at runtime has to live inside
it. Keeping the copy mechanical and byte-identical is what makes `--check` a
real test rather than a ritual.

    tools/sync-ui.py [path/to/ui]      # defaults to ../ui
    tools/sync-ui.py --check           # exit 1 if the copy is stale
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


def sources(ui_root: Path) -> list[tuple[Path, Path]]:
    """Return (source, destination) pairs, erroring on anything missing."""
    pairs = []
    for sub, names in WANTED.items():
        for name in names:
            f = ui_root / sub / name
            if not f.is_file():
                raise SystemExit(f"missing upstream file: {f}")
            pairs.append((f, DEST / sub / name))
    return pairs


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--check"]
    check = "--check" in sys.argv
    ui_root = Path(args[0]) if args else PKG.parent.parent.parent / "ui"
    ui_root = ui_root.resolve()
    if not (ui_root / "core" / "ports.js").is_file():
        raise SystemExit(f"not a shared-UI directory: {ui_root}")

    pairs = sources(ui_root)

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
                f"\n{len(stale)} file(s) differ from {ui_root} — run tools/sync-ui.py"
            )
            return 1
        print(f"ui/ is in sync with {ui_root}")
        return 0

    if DEST.exists():
        shutil.rmtree(DEST)
    for s, d in pairs:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    print(
        f"Synced {len(pairs)} files from {ui_root} → {DEST.relative_to(PKG.parent.parent)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
