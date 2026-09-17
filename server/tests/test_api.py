"""The JSON/fragment API behind the shared Miller-columns UI.

The contract these tests pin down is the one in `src/filemill/api.py`: every
request names a path *relative to ROOT*, and nothing may name an absolute one.
"""

import re
from pathlib import Path

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
        "alpha", "subdir", "Zoo", ".hidden", "10.txt", "2.txt", "readme.md"
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


def test_large_directory_is_paginated_in_stable_order(client, tmp_root: Path):
    for i in range(501):
        (tmp_root / f"item-{i:03d}").write_text(str(i))

    first = client.get("/api/dir?p=&page=1").json()
    second = client.get("/api/dir?p=&page=2").json()

    assert len(first["entries"]) == 500
    assert len(second["entries"]) == 7
    assert first["total"] == 507
    assert first["pages"] == second["pages"] == 2
    assert first["page"] == 1
    assert second["page"] == 2
    assert first["entries"][-1]["name"] == "item-495"
    assert second["entries"][0]["name"] == "item-496"


def test_directory_at_page_limit_keeps_small_response(client, tmp_root: Path):
    for i in range(494):
        (tmp_root / f"item-{i:03d}").write_text(str(i))

    data = client.get("/api/dir?p=&page=1").json()

    assert len(data["entries"]) == 500
    assert "pages" not in data


def test_directory_rejects_invalid_page(client, tmp_root: Path):
    assert client.get("/api/dir?p=&page=0").status_code == 400


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


def test_preview_uses_the_python_markdown_pipeline(client, tmp_root: Path):
    """The whole reason the renderers were not ported to JavaScript."""
    r = client.get("/api/preview?p=readme.md")
    html = r.text
    assert "<h1" in html
    assert "<strong>world</strong>" in html
    assert r.headers["cache-control"] == "no-store"


def test_html_preview_iframe_uses_the_canonical_file_path(client, tmp_root: Path):
    page = tmp_root / "docs" / "page.html"
    page.parent.mkdir()
    page.write_text("<h1>Hi</h1>")
    html = client.get("/api/preview?p=docs/page.html").text
    assert 'src="/docs/page.html"' in html
    assert "/raw?path=" not in html


def test_preview_highlights_source_with_pygments(client, tmp_root: Path):
    (tmp_root / "code.py").write_text("def f():\n    return 1\n")
    html = client.get("/api/preview?p=code.py").text
    assert "preview-code" in html
    assert "highlight" in html


def test_preview_serves_the_source_when_the_page_asked_for_highlight(
    client, tmp_root: Path
):
    """?filemill=highlight reaches here from the page's own URL.

    ui/adapters/preview-http.js forwards it, so the columns show the same
    coloured source that the shared shell renders for ?layout=no-columns.
    """
    html = client.get("/api/preview?p=readme.md&filemill=highlight").text
    assert "preview-code" in html
    assert "<h1" not in html


def test_preview_renders_the_document_for_every_other_view(client, tmp_root: Path):
    """render and raw both mean "the document" once a preview pane is asking."""
    for query in ("", "&filemill=render", "&filemill=raw", "&filemill=nonsense"):
        html = client.get(f"/api/preview?p=readme.md{query}").text
        assert "<h1" in html, query


def test_preview_renders_a_desktop_link(client, tmp_root: Path):
    html = client.get("/api/preview?p=link.desktop").text
    assert "https://example.com" in html


def test_preview_of_a_missing_file_is_404(client, tmp_root: Path):
    assert client.get("/api/preview?p=gone.md").status_code == 404


# ── /api/render — the local-folder case ──────────────────────────────────────


def test_render_renders_posted_bytes(client, tmp_root: Path):
    """A file the server has never seen still gets the Python renderers."""
    r = client.post(
        "/api/render",
        files={"file": ("note.md", b"# Posted\n**bold**\n", "text/markdown")},
    )
    assert r.status_code == 200
    assert "<h1" in r.text
    assert "<strong>bold</strong>" in r.text


def test_render_dispatches_on_the_uploaded_name(client, tmp_root: Path):
    r = client.post(
        "/api/render", files={"file": ("snippet.py", b"def f():\n    return 1\n")}
    )
    assert "preview-code" in r.text


def test_render_leaves_no_temp_file_behind(client, tmp_root: Path, tmp_path: Path):
    import tempfile

    before = set(Path(tempfile.gettempdir()).glob("*"))
    client.post("/api/render", files={"file": ("note.md", b"# hi\n")})
    assert not set(Path(tempfile.gettempdir()).glob("*")) - before


def test_render_refuses_an_oversized_upload(client, tmp_root: Path):
    from filemill import api

    big = b"x" * (api.RENDER_MAX + 1)
    r = client.post("/api/render", files={"file": ("big.md", big)})
    assert "Too large" in r.text


def test_render_without_a_file_is_400(client, tmp_root: Path):
    assert client.post("/api/render", data={"nope": "1"}).status_code == 400


# ── the shell and its assets ─────────────────────────────────────────────────


def test_ui_root_serves_the_shell(client, tmp_root: Path):
    html = client.get("/n/").text
    assert '<script src="/ui/entry-server.js" type="module">' in html
    assert "/ui/adapters/" not in html  # one entry module, no script list


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
    assert f'data-root="{app_module.ROOT.name}"' in html


def test_ui_path_mirrors_the_file_path(client, tmp_root: Path):
    """The URL under the base is the path relative to ROOT, nothing else."""
    assert client.get("/n/readme.md").status_code == 200
    assert client.get("/n/subdir").status_code == 200


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


def test_dir_inside_a_table_lists_its_rows(db_client, db_root: Path):
    j = db_client.get("/api/dir?p=sample.db&v=users").json()
    assert len(j["entries"]) == 5
    row = j["entries"][0]
    assert row["dir"] is False
    assert row["vpath"].startswith("users/")
    assert row["ordered"] is True


def test_a_virtual_entry_carries_a_vpath_and_a_real_one_does_not(client, tmp_root):
    """That distinction is the client's entire rule: an entry with a vpath keeps
    its parent's real path, one without joins its name onto it."""
    assert all("vpath" not in e for e in client.get("/api/dir?p=").json()["entries"])


def test_preview_of_a_virtual_row_uses_the_provider(db_client, db_root: Path):
    html = db_client.get("/api/preview?p=sample.db&v=users/1").text
    assert "User1" in html


def test_preview_of_a_table_uses_the_provider(db_client, db_root: Path):
    html = db_client.get("/api/preview?p=sample.db&v=users&fmt=spreadsheet").text
    assert "User1" in html


def test_vfs_paths_are_not_a_way_around_resolve_safe(db_client, db_root: Path):
    for p in ("../outside.db", "/etc/passwd"):
        assert db_client.get(f"/api/dir?p={p}&v=users").status_code == 404


# ── deep links into a virtual filesystem ─────────────────────────────────────


def test_split_vfs_separates_the_real_path_from_the_virtual_one(db_root: Path):
    from filemill.api import split_vfs

    resolve = app_module._resolve_safe
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

    assert split_vfs("readme.md/nope", tmp_root, app_module._resolve_safe) is None
    assert split_vfs("nope/at/all", tmp_root, app_module._resolve_safe) is None


def test_a_url_can_name_a_row_inside_a_database(db_client, db_root: Path):
    """/n/sample.db/users/1 is one URL but two things — a file and a key in it."""
    assert db_client.get("/n/sample.db/users/1").status_code == 200
    assert db_client.get("/n/sample.db").status_code == 200


def test_a_url_into_a_non_virtual_file_is_404(client, tmp_root: Path):
    assert client.get("/n/readme.md/nope").status_code == 404


# ── /api/save ────────────────────────────────────────────────────────────────


def test_save_overwrites_and_returns_a_fresh_stat(client, tmp_root: Path):
    r = client.post("/api/save?p=readme.md", content=b"# changed\n")
    assert r.status_code == 200
    assert (tmp_root / "readme.md").read_bytes() == b"# changed\n"
    j = r.json()
    assert j["size"] == len("# changed\n")
    assert j["mod"] > 0


def test_save_allows_unknown_extension_utf8_and_rejects_binary(client, tmp_root: Path):
    (tmp_root / ".gitconfig").write_text("name = old\n")
    assert (
        client.post(
            "/api/save?p=.gitconfig", content="name = Åsa\n".encode()
        ).status_code
        == 200
    )
    (tmp_root / "binary").write_bytes(b"x\0y")
    assert client.post("/api/save?p=binary", content=b"z").status_code == 415
    assert client.post("/api/save?p=.gitconfig", content=b"x\0y").status_code == 415


def test_save_rejects_insanely_wide_text(client, tmp_root: Path):
    (tmp_root / "wide").write_text("x" * 10_001)
    assert client.post("/api/save?p=wide", content=b"short").status_code == 415


def test_save_refuses_paths_outside_root(client, tmp_root: Path):
    (tmp_root.parent / "outside.txt").write_text("secret")
    assert client.post("/api/save?p=../outside.txt", content=b"x").status_code == 404
    assert client.post("/api/save?p=/etc/passwd", content=b"x").status_code == 404
    assert (tmp_root.parent / "outside.txt").read_text() == "secret"


def test_save_only_overwrites_existing_files(client, tmp_root: Path):
    """Edit mode edits what it previews — no create, and no directories."""
    assert client.post("/api/save?p=new.txt", content=b"x").status_code == 404
    assert not (tmp_root / "new.txt").exists()
    assert client.post("/api/save?p=subdir", content=b"x").status_code == 404


def test_save_caps_the_body_size(client, tmp_root: Path):
    from filemill.api import RENDER_MAX

    assert (
        client.post(
            "/api/save?p=readme.md", content=b"x" * (RENDER_MAX + 1)
        ).status_code
        == 413
    )
    assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"


def test_delete_removes_files_and_directories(client, tmp_root: Path):
    (tmp_root / "gone.txt").write_text("bye")
    (tmp_root / "gone-dir").mkdir()
    (tmp_root / "gone-dir" / "nested.txt").write_text("bye")
    assert client.delete("/api/delete?p=gone.txt").json() == {"deleted": True}
    assert client.delete("/api/delete?p=gone-dir").json() == {"deleted": True}
    assert not (tmp_root / "gone.txt").exists()
    assert not (tmp_root / "gone-dir").exists()


def test_delete_rejects_missing_and_root(client, tmp_root: Path):
    assert client.delete("/api/delete?p=missing").status_code == 404
    assert client.delete("/api/delete?p=").status_code == 404


def test_delete_removes_a_symlink_without_following_it(client, tmp_root: Path):
    outside = tmp_root.parent / "outside-delete-target"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    (tmp_root / "linked").symlink_to(outside, target_is_directory=True)
    assert client.delete("/api/delete?p=linked").json() == {"deleted": True}
    assert not (tmp_root / "linked").exists()
    assert (outside / "keep.txt").exists()


def test_delete_removes_a_broken_symlink(client, tmp_root: Path):
    (tmp_root / "broken").symlink_to(tmp_root / "missing")
    assert client.delete("/api/delete?p=broken").json() == {"deleted": True}
    assert not (tmp_root / "broken").is_symlink()
