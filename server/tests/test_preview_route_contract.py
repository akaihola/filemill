"""The shared shell owns presentation; only RST retains a server renderer."""

import re
import zipfile
from pathlib import Path

import pytest

import filemill.app as app_module

# Cover every classifier branch, plus source, video and unknown binary files.
SUFFIXES = [
    "md",
    "markdown",
    "rst",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "svg",
    "pdf",
    "html",
    "htm",
    "desktop",
    "vtt",
    "jsonl",
    "csv",
    "docx",
    "pptx",
    "py",
    "txt",
    "mp4",
    "bin",
]
SOURCE = b"Route sentinel\n==============\n\nUnrendered *source*.\n"


@pytest.mark.parametrize("suffix", SUFFIXES)
@pytest.mark.parametrize("member", [False, True], ids=["file", "member"])
def test_document_route_contract(client, tmp_root, suffix, member):
    name = f"note.{suffix}"
    if member:
        with zipfile.ZipFile(tmp_root / "documents.zip", "w") as archive:
            archive.writestr(f"docs/{name}", SOURCE)
        params = {"p": "documents.zip", "v": f"docs/{name}"}
        resource = f"/documents.zip/docs/{name}"
    else:
        (tmp_root / name).write_bytes(SOURCE)
        params = {"p": name}
        resource = f"/{name}"

    for view in ("render", "highlight"):
        shell = client.get(resource, params={"filemill": view})
        assert shell.status_code == 200
        assert shell.headers["content-type"].startswith("text/html")
        assert f'data-filemill="{view}"' in shell.text
        assert "/ui/entry-server.js" in shell.text
        assert "Route sentinel" not in shell.text

    raw = client.get("/api/raw", params=params)
    assert raw.status_code == 200
    assert raw.content == SOURCE
    assert raw.headers["cache-control"] == "no-store"
    if not member:
        for query in ({}, {"filemill": "raw"}):
            response = client.get(
                resource, params=query, headers={"accept": "text/html"}
            )
            assert response.status_code == 200
            assert response.content == SOURCE

    preview = client.get("/api/preview", params=params)
    assert preview.headers["content-type"].startswith("text/html")
    if suffix == "rst":
        assert preview.status_code == 200
        assert "Unrendered <em>source</em>." in preview.text
        assert preview.headers["cache-control"] == "no-store"
    else:
        assert preview.status_code == 404
        assert preview.text == "Not found"


def test_stylesheet_cleanup_request_probe(client):
    package = Path(app_module.__file__).parent
    assert not (package / "styles.py").exists()
    for source in package.glob("*.py"):
        assert "APP_CSS" not in source.read_text(), source.name
    shell = client.get("/")
    styles = re.findall(r'<link rel="stylesheet" href="([^"]+)"', shell.text)
    assert len(styles) == 1
    assert styles[0].startswith("/ui/core/styles.css")
    assert "<style" not in shell.text.lower()
    response = client.get(styles[0])
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert response.content == (package / "ui/core/styles.css").read_bytes()


@pytest.mark.parametrize(
    ("url", "params", "status", "body"),
    [
        ("/missing.md", {}, 404, "Not found"),
        ("/api/raw", {"p": "missing.md"}, 404, "Not found"),
        ("/api/preview", {"p": "missing.rst"}, 404, "Not found"),
        ("/api/raw", {"p": "documents.zip", "v": "missing.rst"}, 404, "Not found"),
        ("/api/preview", {"p": "documents.zip", "v": "missing.rst"}, 404, "Not found"),
        ("/api/preview", {"p": "note.rst", "lines": "bad"}, 400, "Bad lines"),
    ],
)
def test_route_errors_remain_html(client, tmp_root, url, params, status, body):
    (tmp_root / "note.rst").write_bytes(SOURCE)
    with zipfile.ZipFile(tmp_root / "documents.zip", "w") as archive:
        archive.writestr("note.rst", SOURCE)
    response = client.get(url, params=params)
    assert response.status_code == status
    assert response.headers["content-type"].startswith("text/html")
    assert response.text == body
