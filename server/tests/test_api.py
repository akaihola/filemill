"""The JSON/fragment API behind the shared Miller-columns UI.

The contract these tests pin down is the one in `src/filemill/api.py`: every
request names a path *relative to ROOT*, and nothing may name an absolute one.
"""

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


def test_dir_lists_dotfiles(client, tmp_root: Path):
    """Hiding them is the client's job — a deep link to one must still resolve."""
    names = {e["name"] for e in client.get("/api/dir?p=").json()["entries"]}
    assert ".hidden" in names


def test_dir_descends_a_relative_path(client, tmp_root: Path):
    (tmp_root / "subdir" / "inner.txt").write_text("x")
    j = client.get("/api/dir?p=subdir").json()
    assert [e["name"] for e in j["entries"]] == ["inner.txt"]


def test_dir_on_a_file_is_404(client, tmp_root: Path):
    assert client.get("/api/dir?p=readme.md").status_code == 404


def test_dir_on_a_missing_path_is_404(client, tmp_root: Path):
    assert client.get("/api/dir?p=nope/nope").status_code == 404


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


def test_raw_on_a_directory_is_404(client, tmp_root: Path):
    assert client.get("/api/raw?p=subdir").status_code == 404


# ── /api/preview ─────────────────────────────────────────────────────────────


def test_preview_uses_the_python_markdown_pipeline(client, tmp_root: Path):
    """The whole reason the renderers were not ported to JavaScript."""
    html = client.get("/api/preview?p=readme.md").text
    assert "<h1" in html
    assert "<strong>world</strong>" in html


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
    coloured source that ?layout=no-columns renders on the server.
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
    assert "/ui/core/shell.js" in html
    assert "/ui/adapters/app-http.js" in html


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


def test_the_vendored_ui_is_whole(client, tmp_root: Path):
    """Every script the shell references must actually be there — a missing one
    is a blank page, and nothing else in the suite would notice."""
    for name in app_module._UI_CORE:
        assert client.get(f"/ui/core/{name}").status_code == 200, name
    for name in app_module._UI_ADAPTERS:
        assert client.get(f"/ui/adapters/{name}").status_code == 200, name


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
    loaded = {f"ui/core/{n}" for n in app_module._UI_CORE}
    loaded |= {f"ui/adapters/{n}" for n in app_module._UI_ADAPTERS}
    loaded |= {"ui/core/styles.css", "ui/vendor/seti-map.js", "ui/vendor/seti.woff"}
    assert not excluded & loaded, f"the wheel would omit: {sorted(excluded & loaded)}"

    # A typo would exclude nothing and pass the check above in silence.
    for rel in excluded:
        assert (pkg / rel).is_file(), rel


# ── the old UI is untouched ──────────────────────────────────────────────────


def test_the_htmx_ui_still_serves(client, tmp_root: Path):
    """The migration is additive until the cutover; /f/ must not have moved."""
    assert client.get("/f/").status_code == 200


# ── virtual filesystems through the new API ──────────────────────────────────


def test_a_database_lists_as_a_folder(db_client, db_root: Path):
    """A .db has to open a column, not a preview — so the listing calls it a
    directory even though it is a file on disk."""
    by_name = {e["name"]: e for e in db_client.get("/api/dir?p=").json()["entries"]}
    assert by_name["sample.db"]["dir"] is True


def test_a_provider_with_no_entries_stays_a_file(client, tmp_root: Path):
    """The CSV provider is a stub that yields nothing; calling it a folder would
    make it an always-empty column with no preview."""
    (tmp_root / "data.csv").write_text("a,b\n1,2\n")
    by_name = {e["name"]: e for e in client.get("/api/dir?p=").json()["entries"]}
    assert by_name["data.csv"]["dir"] is False


def test_dir_inside_a_database_lists_its_tables(db_client, db_root: Path):
    j = db_client.get("/api/dir?p=sample.db").json()
    names = {e["name"] for e in j["entries"]}
    assert "users" in names
    users = next(e for e in j["entries"] if e["name"] == "users")
    assert users["dir"] is True
    assert users["vpath"] == "users"
    assert users["icon"]


def test_dir_inside_a_table_lists_its_rows(db_client, db_root: Path):
    j = db_client.get("/api/dir?p=sample.db&v=users").json()
    assert len(j["entries"]) == 5
    row = j["entries"][0]
    assert row["dir"] is False
    assert row["vpath"].startswith("users/")


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
        client.post("/api/save?p=readme.md", content=b"x" * (RENDER_MAX + 1)).status_code
        == 413
    )
    assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"
