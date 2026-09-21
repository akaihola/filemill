"""Build the prototype using the installed WebKitGTK development packages."""

import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent.parent
out = here / "build"
out.mkdir(exist_ok=True)
assets = out / "assets"
assets.mkdir(exist_ok=True)
subprocess.run(
    [
        sys.executable,
        str(root / "static/build-index.py"),
        "--native",
        str(assets / "index.html"),
    ],
    check=True,
)
data = (assets / "index.html").read_bytes()
(out / "resource.h").write_text(
    "static const unsigned char resource[] = {" + ",".join(map(str, data)) + "};\n"
)
flags = subprocess.check_output(
    ["pkg-config", "--cflags", "--libs", "webkit2gtk-4.1"], text=True
).split()
subprocess.run(
    [
        "cc",
        "-Os",
        "-s",
        "-Wall",
        "-Wextra",
        "-Wno-unused-parameter",
        str(here / "main.c"),
        "-o",
        str(out / "filemill"),
        *flags,
    ],
    check=True,
)
print(f"{out / 'filemill'}: {(out / 'filemill').stat().st_size} bytes")
