"""Focused checks for the static PWA package."""
import json
from pathlib import Path

ROOT = Path(__file__).parent


def test_manifest():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "./"
    assert manifest["scope"] == "./"
    for icon in manifest["icons"]:
        assert (ROOT / icon["src"][2:]).is_file()


def test_shell():
    html = (ROOT / "index.html").read_text()
    assert '<link rel="manifest" href="./manifest.json">' in html
    assert "navigator.serviceWorker.register('./sw.js', {scope: './'})" in html


def test_worker():
    worker = (ROOT / "sw.js").read_text()
    assert '"./manifest.json"' in worker
    assert '"./icon-192.png"' in worker
    assert '"./icon-512.png"' in worker


if __name__ == "__main__":
    for check in (test_manifest, test_shell, test_worker):
        check()
    print("static PWA checks passed")
