"""The JSON/fragment API behind the shared Miller-columns UI.

The contract these tests pin down is the one in `src/filemill/api.py`: every
request names a path *relative to ROOT*, and nothing may name an absolute one.
"""

import json
import re
import zipfile
from pathlib import Path

import pytest

import filemill.app as app_module

# ── /api/dir ─────────────────────────────────────────────────────────────────


def test_dir_lists_the_root(client, tmp_root: Path):
    j = client.get("/api/dir?p=").json()
    names = {e["name"] for e in j["entries"]}
    assert {"subdir", "readme.md", ".hidden"} <= names
    assert j["denied"] is None


def test_dir_marks_directories_and_carries_metadata(client, tmp_root: Path):
    """The listing has to be self-sufficient: the UI never asks twice."""
    by_name = {e["name"]: e for e in client.get("/api/dir?p=").json()["entries"]}
    assert by_name["subdir"]["dir"] is True
    assert by_name["readme.md"]["dir"] is False
    assert by_name["readme.md"]["size"] == len("# Hello\n**world**\n")
    assert by_name["readme.md"]["mod"] > 0


def test_dir_owns_stable_entry_order(client, tmp_root: Path):
    (tmp_root / "Zoo").mkdir()
    (tmp_root / "alpha").mkdir()
    (tmp_root / "10.txt").touch()
    (tmp_root / "2.txt").touch()

    entries = client.get("/api/dir?p=").json()["entries"]

    assert [e["name"] for e in entries] == [
        "alpha",
        "subdir",
        "Zoo",
        ".hidden",
        "10.txt",
        "2.txt",
        "doc.pdf",
        "image.jpg",
        "image.png",
        "link.desktop",
        "readme.md",
    ]
    assert all(e["ordered"] for e in entries)


def test_dir_lists_dotfiles(client, tmp_root: Path):
    """Hiding them is the client's job — a deep link to one must still resolve."""
    names = {e["name"] for e in client.get("/api/dir?p=").json()["entries"]}
    assert ".hidden" in names


def test_dir_descends_a_relative_path(client, tmp_root: Path):
    (tmp_root / "subdir" / "inner.txt").write_text("x")
    j = client.get("/api/dir?p=subdir").json()
    assert [e["name"] for e in j["entries"]] == ["inner.txt"]


def test_large_directory_lists_every_entry_in_one_response(client, tmp_root: Path):
    """The column scrolls; the server never splits a listing into pages."""
    folder = tmp_root / "subdir"
    for i in range(501):
        (folder / f"item-{i:03d}").write_text(str(i))

    data = client.get("/api/dir?p=subdir").json()

    assert [e["name"] for e in data["entries"]] == [f"item-{i:03d}" for i in range(501)]
    assert not {"page", "pages", "total"} & data.keys()


def test_dir_on_a_file_is_404(client, tmp_root: Path):
    assert client.get("/api/dir?p=readme.md").status_code == 404


def test_dir_on_a_missing_path_is_404(client, tmp_root: Path):
    assert client.get("/api/dir?p=nope/nope").status_code == 404


def test_search_returns_relative_matches_and_context(client, tmp_root: Path):
    (tmp_root / "subdir" / "needle.txt").write_text("before\nneedle here\nafter\n")
    r = client.get("/api/search?q=needle")
    assert r.status_code == 200
    assert r.json()["matches"] == [
        {"path": "subdir/needle.txt", "line": 2, "column": 1, "context": "needle here"}
    ]


def test_search_reports_empty_and_invalid_queries(client, tmp_root: Path):
    assert client.get("/api/search?q=missing").json() == {"matches": []}
    assert client.get("/api/search?q=").status_code == 400
    assert client.get("/api/search?q=" + "x" * 201).status_code == 400


def test_search_query_cannot_become_a_path_or_option(client, tmp_root: Path):
    r = client.get("/api/search?q=--glob=*")
    assert r.status_code == 200
    assert all(not e["path"].startswith("/") for e in r.json()["matches"])


def test_search_stays_inside_focused_directory(client, tmp_root: Path):
    (tmp_root / "subdir" / "inside.txt").write_text("needle\n")
    (tmp_root / "outside.txt").write_text("needle\n")
    r = client.get("/api/search?q=needle&p=subdir")
    assert r.json()["matches"] == [
        {"path": "subdir/inside.txt", "line": 1, "column": 1, "context": "needle"}
    ]


def test_search_limits_large_result_sets(client, tmp_root: Path):
    for i in range(200):
        (tmp_root / "subdir" / f"{i}.txt").write_text("needle\n" * 20)
    r = client.get("/api/search?q=needle&p=subdir")
    assert r.status_code == 200
    assert len(r.json()["matches"]) == 100


def test_search_timeout_is_reported_as_a_backend_error(
    client, tmp_root: Path, monkeypatch
):
    import subprocess

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            kwargs["args"] if "args" in kwargs else args[0], 10
        )

    monkeypatch.setattr("filemill.api.subprocess.run", timeout)
    r = client.get("/api/search?q=needle")
    assert r.status_code == 503
    assert r.json() == {"error": "Search timed out"}


# ── the path contract ────────────────────────────────────────────────────────


def test_absolute_paths_are_refused(client, tmp_root: Path):
    """`ROOT / "/etc"` is `/etc` — treating an absolute p as relative would
    hand out the whole disk, so it is rejected before any join happens."""
    for p in ("/etc", "/etc/passwd", "//etc/passwd"):
        assert client.get(f"/api/dir?p={p}").status_code == 404, p
        assert client.get(f"/api/raw?p={p}").status_code == 404, p


def test_traversal_out_of_root_is_refused(client, tmp_root: Path):
    (tmp_root.parent / "outside.txt").write_text("secret")
    assert client.get("/api/raw?p=../outside.txt").status_code == 404
    assert client.get("/api/dir?p=../..").status_code == 404


def test_encoded_traversal_is_refused(client, tmp_root: Path):
    assert client.get("/api/raw?p=%2e%2e%2foutside.txt").status_code == 404


def test_rel_to_abs_rejects_absolute_and_drive_paths(tmp_path: Path):
    from filemill.api import rel_to_abs

    assert rel_to_abs("", tmp_path) == tmp_path
    assert rel_to_abs("a/b", tmp_path) == tmp_path / "a/b"
    assert rel_to_abs("/etc/passwd", tmp_path) is None
    assert rel_to_abs("\\windows", tmp_path) is None
    assert rel_to_abs("C:/windows", tmp_path) is None


# ── /api/raw ─────────────────────────────────────────────────────────────────


def test_raw_serves_bytes_with_a_media_type(client, tmp_root: Path):
    r = client.get("/api/raw?p=readme.md")
    assert r.status_code == 200
    assert r.content == b"# Hello\n**world**\n"
    assert "markdown" in r.headers["content-type"]
    assert r.headers["cache-control"] == "no-store"


def test_raw_on_a_directory_is_404(client, tmp_root: Path):
    assert client.get("/api/raw?p=subdir").status_code == 404


# ── /api/preview ─────────────────────────────────────────────────────────────


def test_preview_of_markdown_is_its_source(client, tmp_root: Path):
    """Markdown renders in the browser; the server only ever shows the source."""
    r = client.get("/api/preview?p=readme.md")
    html = r.text
    assert "preview-code" in html
    assert "<strong>world</strong>" not in html
    assert r.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("suffix", ["html", "pdf", "png"])
def test_media_preview_uses_the_canonical_file_path(client, tmp_root: Path, suffix):
    page = tmp_root / "docs" / f"page & copy.{suffix}"
    page.parent.mkdir()
    page.write_text("<h1>Hi</h1>")
    html = client.get("/api/preview", params={"p": f"docs/{page.name}"}).text
    assert f'src="/docs/page%20%26%20copy.{suffix}"' in html
    assert "/api/raw?" not in html
    assert client.get(f"/docs/page%20%26%20copy.{suffix}").content == page.read_bytes()


def test_preview_highlights_source_with_pygments(client, tmp_root: Path):
    (tmp_root / "code.py").write_text("def f():\n    return 1\n")
    html = client.get("/api/preview?p=code.py").text
    assert "preview-code" in html
    assert "highlight" in html


def test_preview_serves_the_source_when_the_page_asked_for_highlight(
    client, tmp_root: Path
):
    """?filemill=highlight reaches here from the page's own URL.

    ui/adapters/preview-http.js forwards it, so the columns show the coloured
    source the page's URL asked for.
    """
    html = client.get("/api/preview?p=readme.md&filemill=highlight").text
    assert "preview-code" in html
    assert "<h1" not in html


def test_preview_renders_the_document_for_every_other_view(client, tmp_root: Path):
    """render and raw both mean "the document" once a preview pane is asking."""
    (tmp_root / "page.html").write_text("<h1>Hi</h1>")
    for query in ("", "&filemill=render", "&filemill=raw", "&filemill=nonsense"):
        html = client.get(f"/api/preview?p=page.html{query}").text
        assert "<iframe" in html, query


def test_preview_renders_a_desktop_link(client, tmp_root: Path):
    html = client.get("/api/preview?p=link.desktop").text
    assert "https://example.com" in html


def test_preview_of_a_missing_file_is_404(client, tmp_root: Path):
    assert client.get("/api/preview?p=gone.md").status_code == 404


# ── the shell and its assets ─────────────────────────────────────────────────


def test_ui_root_serves_the_shell(client, tmp_root: Path):
    html = client.get("/n/").text
    scripts = re.findall(r'<script src="([^"]+)" type="module">', html)
    assert len(scripts) == 1
    importmap = re.search(r'<script type="importmap">(.*?)</script>', html)
    assert importmap is not None
    imports = json.loads(importmap[1])["imports"]
    assert scripts == [imports["/ui/entry-server.js"]]
    for path in ("/ui/entry-server.js", "/ui/core/render.js", "/ui/editor/editor.js"):
        assert imports[path].startswith(path + "?v=")
        assert client.get(imports[path]).content == client.get(path).content
    assert re.search(r'href="/ui/core/styles.css\?v=[a-f0-9]+"', html)


def test_shell_carries_no_chrome_markup(client, tmp_root: Path):
    """core/shell.js builds the page, so this template and filemill's
    index.html have nothing to drift apart on."""
    html = client.get("/n/").text
    for marker in ('id="strip"', 'id="crumbs"', 'id="settings"'):
        assert marker not in html


def test_shell_configures_the_adapters(client, tmp_root: Path):
    html = client.get("/n/").text
    assert 'data-api="/api"' in html
    assert f'data-base="{app_module.UI_BASE}"' in html
    assert f'data-root="{tmp_root.name}"' in html


def test_ui_path_mirrors_the_file_path(client, tmp_root: Path):
    """The URL under the base is the path relative to ROOT, nothing else."""
    assert client.get("/n/readme.md").status_code == 200
    assert client.get("/n/subdir").status_code == 200


@pytest.mark.parametrize("view", ["render", "highlight"])
def test_ui_path_preserves_requested_view(client, view):
    response = client.get("/n/readme.md", params={"filemill": view})
    assert response.status_code == 200
    assert f'data-filemill="{view}"' in response.text


@pytest.mark.parametrize("query", [{}, {"filemill": "raw"}])
def test_ui_path_never_tells_the_shell_it_is_raw(client, query):
    """The shell always renders, so `raw` there is `render`.

    The client's Source/Rendered toggle trusts data-filemill. Told "raw", it
    labelled a rendered section "Rendered" and clicking it changed nothing.
    """
    response = client.get("/n/readme.md", params=query)
    assert response.status_code == 200
    assert 'data-filemill="render"' in response.text


def test_ui_path_that_does_not_exist_is_404(client, tmp_root: Path):
    assert client.get("/n/nope.md").status_code == 404


def test_missing_favicon_is_404(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 404
    assert response.text == "Not found"


def test_ui_path_cannot_escape_root(client, tmp_root: Path):
    (tmp_root.parent / "outside.txt").write_text("secret")
    assert client.get("/n/../outside.txt").status_code == 404


def test_ui_assets_are_served(client, tmp_root: Path):
    for asset, kind in (
        ("/ui/core/ports.js", "javascript"),
        ("/ui/core/styles.css", "text/css"),
        ("/ui/adapters/http.js", "javascript"),
        ("/ui/vendor/seti-map.js", "javascript"),
        # styles.css reaches the font as ../../vendor/seti.woff, which only
        # resolves because the copy keeps filemill's directory shape.
        ("/ui/vendor/seti.woff", "font/woff"),
    ):
        r = client.get(asset)
        assert r.status_code == 200, asset
        assert kind in r.headers["content-type"], asset


def test_ui_assets_cannot_escape_the_ui_directory(client, tmp_root: Path):
    for bad in ("/ui/../app.py", "/ui/core/../../app.py", "/ui/app.py"):
        assert client.get(bad).status_code == 404, bad


def _module_graph(entry: Path) -> set[str]:
    """Every module reachable from *entry*, as ui/-relative paths — the same
    walk static/build-index.py does, and the only definition of "loaded" now
    that the shell names one file."""
    ui = entry.parent
    seen: set[Path] = set()

    def visit(path: Path) -> None:
        if path in seen:
            return
        seen.add(path)
        for m in re.finditer(
            r'^import\s*(?:\{[^}]*\}\s*from\s*)?"(\.[^"]+)";',
            path.read_text(),
            re.MULTILINE,
        ):
            visit((path.parent / m.group(1)).resolve())

    visit(entry.resolve())
    return {f"ui/{p.relative_to(ui).as_posix()}" for p in seen}


def test_the_vendored_ui_is_whole(client, tmp_root: Path):
    """Every module the entry reaches must actually be served — one missing
    import fails the whole graph, and nothing else in the suite would notice."""
    loaded = _module_graph(app_module._UI_DIR / app_module._UI_ENTRY)
    assert len(loaded) > 20, loaded
    for rel in sorted(loaded):
        assert client.get(f"/{rel}").status_code == 200, rel


def test_the_wheel_excludes_only_what_the_shell_never_loads():
    """`wheel-exclude` is the only thing standing between the shell and a broken
    wheel, now that `ui/` is the package's own directory rather than a copy of
    it. The test above cannot see this: it runs against the source tree, where
    an over-excluded file is present either way — the omission would only show
    up in an installed wheel, as a blank page.
    """
    import tomllib

    pkg = Path(app_module.__file__).parent
    cfg = tomllib.loads((pkg.parent.parent / "pyproject.toml").read_text())
    excluded = set(cfg["tool"]["uv"]["build-backend"]["wheel-exclude"])

    # Everything _ui_shell() asks the browser for, plus the font styles.css names.
    loaded = _module_graph(app_module._UI_DIR / app_module._UI_ENTRY)
    loaded |= {"ui/core/styles.css", "ui/vendor/seti-map.js", "ui/vendor/seti.woff"}
    assert not excluded & loaded, f"the wheel would omit: {sorted(excluded & loaded)}"

    # A typo would exclude nothing and pass the check above in silence.
    for rel in excluded:
        assert (pkg / rel).is_file(), rel


# ── the old UI is untouched ──────────────────────────────────────────────────


# ── virtual filesystems through the new API ──────────────────────────────────


def test_a_database_lists_as_a_folder(db_client, db_root: Path):
    """A .db has to open a column, not a preview — so the listing calls it a
    directory even though it is a file on disk."""
    by_name = {e["name"]: e for e in db_client.get("/api/dir?p=").json()["entries"]}
    assert by_name["sample.db"]["dir"] is True


def test_csv_stays_a_plain_file_for_server_api(client, tmp_root: Path):
    """CSV is browsed by the shared browser adapter and remains raw on the API."""
    (tmp_root / "data.csv").write_text("a,b\n1,2\n")
    by_name = {e["name"]: e for e in client.get("/api/dir?p=").json()["entries"]}
    assert by_name["data.csv"]["dir"] is False
    assert client.get("/api/raw?p=data.csv").text == "a,b\n1,2\n"


def test_empty_and_malformed_csv_remain_raw_files(client, tmp_root: Path):
    (tmp_root / "empty.csv").write_text("")
    (tmp_root / "bad.csv").write_text('a,b\n1,"oops\n')
    assert client.get("/api/raw?p=empty.csv").text == ""
    assert client.get("/api/raw?p=bad.csv").text == 'a,b\n1,"oops\n'


def test_dir_inside_a_database_lists_its_tables(db_client, db_root: Path):
    j = db_client.get("/api/dir?p=sample.db").json()
    names = {e["name"] for e in j["entries"]}
    assert "users" in names
    users = next(e for e in j["entries"] if e["name"] == "users")
    assert users["dir"] is True
    assert users["vpath"] == "users"
    assert users["icon"]
    assert users["ordered"] is True
    assert "record" not in users


def test_dir_inside_a_table_lists_its_rows(db_client, db_root: Path):
    j = db_client.get("/api/dir?p=sample.db&v=users").json()
    assert len(j["entries"]) == 5
    row = j["entries"][0]
    assert row["dir"] is False
    assert row["vpath"].startswith("users/")
    assert row["ordered"] is True
    assert row["record"] == {"id": 1, "name": "User1", "bio": "Bio1"}


def test_a_virtual_entry_carries_a_vpath_and_a_real_one_does_not(client, tmp_root):
    """That distinction is the client's entire rule: an entry with a vpath keeps
    its parent's real path, one without joins its name onto it."""
    assert all("vpath" not in e for e in client.get("/api/dir?p=").json()["entries"])


def test_the_server_renders_no_database_html(db_client, db_root: Path):
    """The row's cells travel as JSON on their /api/dir entry and the client
    draws them, so no preview response carries a row or a table — whatever
    shape the preview route itself has."""
    assert db_client.get("/api/dir?p=sample.db&v=users").json()["entries"][0][
        "record"
    ] == {"id": 1, "name": "User1", "bio": "Bio1"}
    for url in ("/api/preview?p=sample.db&v=users/1", "/api/preview?p=sample.db"):
        body = db_client.get(url).text
        assert "User1" not in body
        assert "db-table" not in body
        assert "db-kv-table" not in body


def test_vfs_paths_are_not_a_way_around_resolve_safe(db_client, db_root: Path):
    for p in ("../outside.db", "/etc/passwd"):
        assert db_client.get(f"/api/dir?p={p}&v=users").status_code == 404


# ── deep links into a virtual filesystem ─────────────────────────────────────


def test_split_vfs_separates_the_real_path_from_the_virtual_one(db_root: Path):
    from filemill.api import split_vfs

    resolve = app_module._resolve
    assert split_vfs("sample.db/users/1", db_root, resolve) == ("sample.db", "users/1")
    assert split_vfs("sample.db", db_root, resolve) == ("sample.db", "")
    # browsed on the client, so the server only has to let the row URL through
    (db_root / "log.jsonl").write_text('{"id": 1}\n')
    assert split_vfs("log.jsonl/x", db_root, resolve) == ("log.jsonl", "x")
    assert split_vfs("subdir", db_root, resolve) == ("subdir", "")
    assert split_vfs("", db_root, resolve) == ("", "")


def test_split_vfs_refuses_a_path_that_is_not_virtual(tmp_root: Path):
    """readme.md has no provider, so readme.md/anything is simply not a path."""
    from filemill.api import split_vfs

    assert split_vfs("image.png/nope", tmp_root, app_module._resolve) is None
    assert split_vfs("nope/at/all", tmp_root, app_module._resolve) is None


def test_a_url_can_name_a_row_inside_a_database(db_client, db_root: Path):
    """/n/sample.db/users/1 is one URL but two things — a file and a key in it."""
    assert db_client.get("/n/sample.db/users/1").status_code == 200
    assert db_client.get("/n/sample.db").status_code == 200


def test_a_url_into_a_non_virtual_file_is_404(client, tmp_root: Path):
    assert client.get("/n/image.png/nope").status_code == 404


# ── archives through the new API ─────────────────────────────────────────────


def test_an_archive_lists_as_a_folder_and_an_empty_one_as_a_file(
    archive_client, archive_root: Path
):
    by_name = {
        e["name"]: e for e in archive_client.get("/api/dir?p=").json()["entries"]
    }
    assert by_name["demo.tar.zst"]["dir"] is True
    assert by_name["demo.zip"]["dir"] is True
    assert by_name["empty.tar"]["dir"] is False


def test_dir_inside_an_archive_lists_one_level(archive_client, archive_root: Path):
    for name in ("demo.tar.zst", "demo.zip"):
        j = archive_client.get(f"/api/dir?p={name}").json()
        assert [(e["name"], e["dir"], e["vpath"]) for e in j["entries"]] == [
            ("docs", True, "docs"),
            ("src", True, "src"),
            ("top.txt", False, "top.txt"),
        ]
        j = archive_client.get(f"/api/dir?p={name}&v=docs").json()
        assert [e["vpath"] for e in j["entries"]] == ["docs/pic.png", "docs/readme.md"]


def test_a_member_previews_as_the_file_it_is(archive_client, archive_root: Path):
    r = archive_client.get("/api/preview?p=demo.tar.zst&v=docs/readme.md")
    assert r.status_code == 200
    assert r.headers["cache-control"] == "no-store"
    assert "Hello from the archive" in r.text
    assert (
        'class="highlight"'
        in archive_client.get("/api/preview?p=demo.zip&v=src/app.py").text
    )


def test_an_image_member_is_served_through_raw_with_its_vpath(
    archive_client, archive_root: Path
):
    html = archive_client.get("/api/preview?p=demo.tar.zst&v=docs/pic.png").text
    assert (
        '<img class="pv-img" src="/api/raw?p=demo.tar.zst&amp;v=docs%2Fpic.png"' in html
    )
    r = archive_client.get("/api/raw?p=demo.tar.zst&v=docs/pic.png")
    assert r.status_code == 200
    assert r.content == b"\x89PNG\r\n"
    assert r.headers["content-type"].startswith("image/png")
    assert r.headers["cache-control"] == "no-store"


def test_an_html_member_previews_in_a_sandboxed_iframe(
    archive_client, archive_root: Path
):
    """Issue 114: the member's page comes from /api/raw, filemill's own
    origin, so without the sandbox a file on disk gets (ui/core/renderers.js)
    its script would run as filemill. `sandbox=""` allows neither scripts nor
    the same origin."""
    with zipfile.ZipFile(archive_root / "site.zip", "w") as zf:
        zf.writestr("page.html", "<script>parent.alert(1)</script>")
    html = archive_client.get("/api/preview?p=site.zip&v=page.html").text
    iframe = re.search(r"<iframe\b[^>]*>", html)
    assert iframe is not None
    assert re.search(r'\ssandbox=""[\s>]', iframe[0])


def test_raw_without_a_vpath_still_serves_the_archive_itself(
    archive_client, archive_root: Path
):
    r = archive_client.get("/api/raw?p=demo.zip")
    assert r.status_code == 200
    assert r.content == (archive_root / "demo.zip").read_bytes()


def test_a_folder_or_missing_member_is_404(archive_client, archive_root: Path):
    for v in ("docs", "nope.txt", "../top.txt"):
        assert (
            archive_client.get(f"/api/preview?p=demo.tar.zst&v={v}").status_code == 404
        )
        assert archive_client.get(f"/api/raw?p=demo.tar.zst&v={v}").status_code == 404
    assert archive_client.get("/api/preview?p=top.txt&v=x").status_code == 404


def test_an_oversized_member_says_so_instead_of_rendering(
    archive_client, archive_root: Path, monkeypatch
):
    monkeypatch.setattr("filemill.providers.archive.MEMBER_MAX", 4)
    r = archive_client.get("/api/preview?p=demo.tar.zst&v=docs/readme.md")
    assert r.status_code == 200
    assert "Too large to preview" in r.text
    assert (
        archive_client.get("/api/raw?p=demo.tar.zst&v=docs/readme.md").status_code
        == 413
    )


def test_a_url_can_name_a_member_inside_an_archive(archive_client, archive_root: Path):
    assert archive_client.get("/n/demo.tar.zst/docs/readme.md").status_code == 200
    assert archive_client.get("/n/demo.tar.zst").status_code == 200
    assert archive_client.get("/demo.tar.zst/docs/readme.md?f").status_code == 200


# ── /api/save ────────────────────────────────────────────────────────────────


@pytest.fixture()
def mutation_client(client, monkeypatch):
    monkeypatch.setenv("FILEMILL_ORIGINS", "http://testserver")
    from filemill.app import app

    client.headers.update(
        {
            "Origin": "http://testserver",
            "X-Filemill-Token": app.state.mutation_token,
        }
    )
    return client


def test_save_overwrites_and_returns_a_fresh_stat(mutation_client, tmp_root: Path):
    r = mutation_client.post("/api/save?p=readme.md", content=b"# changed\n")
    assert r.status_code == 200
    assert (tmp_root / "readme.md").read_bytes() == b"# changed\n"
    j = r.json()
    assert j["size"] == len("# changed\n")
    assert j["mod"] > 0


def test_save_allows_unknown_extension_utf8_and_rejects_binary(
    mutation_client, tmp_root: Path
):
    (tmp_root / ".gitconfig").write_text("name = old\n")
    assert (
        mutation_client.post(
            "/api/save?p=.gitconfig", content="name = Åsa\n".encode()
        ).status_code
        == 200
    )
    (tmp_root / "binary").write_bytes(b"x\0y")
    assert mutation_client.post("/api/save?p=binary", content=b"z").status_code == 415
    assert (
        mutation_client.post("/api/save?p=.gitconfig", content=b"x\0y").status_code
        == 415
    )


def test_save_rejects_insanely_wide_text(mutation_client, tmp_root: Path):
    (tmp_root / "wide").write_text("x" * 10_001)
    assert mutation_client.post("/api/save?p=wide", content=b"short").status_code == 415


def test_save_refuses_paths_outside_root(mutation_client, tmp_root: Path):
    (tmp_root.parent / "outside.txt").write_text("secret")
    assert (
        mutation_client.post("/api/save?p=../outside.txt", content=b"x").status_code
        == 404
    )
    assert (
        mutation_client.post("/api/save?p=/etc/passwd", content=b"x").status_code == 404
    )
    assert (tmp_root.parent / "outside.txt").read_text() == "secret"


def test_save_only_overwrites_existing_files(mutation_client, tmp_root: Path):
    """Edit mode edits what it previews — no create, and no directories."""
    assert mutation_client.post("/api/save?p=new.txt", content=b"x").status_code == 404
    assert not (tmp_root / "new.txt").exists()
    assert mutation_client.post("/api/save?p=subdir", content=b"x").status_code == 404


def test_save_caps_the_body_size(mutation_client, tmp_root: Path):
    from filemill.api import RENDER_MAX

    assert (
        mutation_client.post(
            "/api/save?p=readme.md", content=b"x" * (RENDER_MAX + 1)
        ).status_code
        == 413
    )
    assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"


def test_delete_removes_files_and_directories(mutation_client, tmp_root: Path):
    (tmp_root / "gone.txt").write_text("bye")
    (tmp_root / "gone-dir").mkdir()
    (tmp_root / "gone-dir" / "nested.txt").write_text("bye")
    assert mutation_client.delete("/api/delete?p=gone.txt").json() == {"deleted": True}
    assert mutation_client.delete("/api/delete?p=gone-dir").json() == {"deleted": True}
    assert not (tmp_root / "gone.txt").exists()
    assert not (tmp_root / "gone-dir").exists()


def test_delete_rejects_missing_and_root(mutation_client, tmp_root: Path):
    assert mutation_client.delete("/api/delete?p=missing").status_code == 404
    assert mutation_client.delete("/api/delete?p=").status_code == 404


def test_delete_removes_a_symlink_without_following_it(mutation_client, tmp_root: Path):
    outside = tmp_root.parent / "outside-delete-target"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    (tmp_root / "linked").symlink_to(outside, target_is_directory=True)
    assert mutation_client.delete("/api/delete?p=linked").json() == {"deleted": True}
    assert not (tmp_root / "linked").exists()
    assert (outside / "keep.txt").exists()


def test_delete_removes_a_broken_symlink(mutation_client, tmp_root: Path):
    (tmp_root / "broken").symlink_to(tmp_root / "missing")
    assert mutation_client.delete("/api/delete?p=broken").json() == {"deleted": True}
    assert not (tmp_root / "broken").is_symlink()


def test_split_vfs_keeps_document_headings_virtual(tmp_root: Path):
    """The browser browses Markdown and reStructuredText by headings; their
    section URLs reload like a SQLite row's."""
    from filemill import app as app_module
    from filemill.api import split_vfs

    (tmp_root / "guide.rst").write_text("Guide\n=====\n")
    assert split_vfs("readme.md/Hello", tmp_root, app_module._resolve) == (
        "readme.md",
        "Hello",
    )
    assert split_vfs("guide.rst/Guide/Sub", tmp_root, app_module._resolve) == (
        "guide.rst",
        "Guide/Sub",
    )


def test_document_heading_urls_serve_the_shell(client):
    for url in (
        "/readme.md/Hello?filemill=render",
        "/readme.md/Hello",
        "/readme.md/Hello?filemill=raw",
    ):
        r = client.get(url)
        assert r.status_code == 200, url
        assert 'data-filemill="render"' in r.text, url


def test_rst_preview_renders_a_line_range(client, tmp_root: Path):
    (tmp_root / "guide.rst").write_text(
        "Title\n=====\n\nPart A\n------\n\nalpha\n\nPart B\n------\n\nbeta\n"
    )
    html = client.get("/api/preview", params={"p": "guide.rst", "lines": "8-12"}).text
    assert "Part B" in html and "beta" in html
    assert "alpha" not in html and "Part A" not in html
    whole = client.get("/api/preview", params={"p": "guide.rst"}).text
    assert "alpha" in whole and "beta" in whole
    assert (
        client.get("/api/preview", params={"p": "guide.rst", "lines": "x"}).status_code
        == 400
    )


# ── Git bundles through the new API ──────────────────────────────────────────


def test_a_bundle_lists_as_a_folder_and_a_broken_one_as_a_file(
    bundle_client, bundle_root: Path
):
    by_name = {e["name"]: e for e in bundle_client.get("/api/dir?p=").json()["entries"]}
    assert by_name["demo.bundle"]["dir"] is True
    assert by_name["broken.bundle"]["dir"] is False


def test_dir_inside_a_bundle_lists_refs_then_trees(bundle_client, bundle_root: Path):
    j = bundle_client.get("/api/dir?p=demo.bundle").json()
    assert [(e["name"], e["dir"], e["vpath"]) for e in j["entries"]] == [
        ("HEAD", True, "HEAD"),
        ("heads", True, "heads"),
        ("tags", True, "tags"),
    ]
    j = bundle_client.get("/api/dir?p=demo.bundle&v=heads/main").json()
    assert [(e["name"], e["dir"]) for e in j["entries"]] == [
        ("docs", True),
        ("src", True),
        ("top.txt", False),
    ]
    j = bundle_client.get("/api/dir?p=demo.bundle&v=heads/main/docs").json()
    assert [e["vpath"] for e in j["entries"]] == [
        "heads/main/docs/pic.png",
        "heads/main/docs/readme.md",
    ]


def test_a_bundle_member_previews_as_the_file_it_is(bundle_client, bundle_root: Path):
    r = bundle_client.get("/api/preview?p=demo.bundle&v=heads/main/docs/readme.md")
    assert r.status_code == 200
    assert "Hello from the bundle" in r.text
    assert (
        'class="highlight"'
        in bundle_client.get("/api/preview?p=demo.bundle&v=tags/v1/src/app.py").text
    )
    r = bundle_client.get("/api/raw?p=demo.bundle&v=HEAD/docs/pic.png")
    assert r.status_code == 200
    assert r.content == b"\x89PNG\r\n"
    assert r.headers["content-type"].startswith("image/png")


def test_a_bundle_folder_ref_or_missing_member_is_404(bundle_client, bundle_root: Path):
    for v in ("heads", "heads/main", "heads/main/docs", "heads/main/nope.txt"):
        assert bundle_client.get(f"/api/preview?p=demo.bundle&v={v}").status_code == 404
        assert bundle_client.get(f"/api/raw?p=demo.bundle&v={v}").status_code == 404


def test_a_url_can_name_a_file_inside_a_bundle(bundle_client, bundle_root: Path):
    assert (
        bundle_client.get("/n/demo.bundle/heads/main/docs/readme.md").status_code == 200
    )
    assert (
        bundle_client.get("/demo.bundle/heads/main/docs/readme.md?f").status_code == 200
    )
