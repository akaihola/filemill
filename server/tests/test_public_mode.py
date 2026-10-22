"""A public instance never lists or serves a hidden path (ADR 0087, issue [128]).

Directory layout built by the ``public_tree`` fixture:

    tmp/
        outside/
            secret.txt                  "OUTSIDE-CANARY"
            .config/x.txt               "CONFIG-CANARY"
        root/                           <- ROOT
            README.md
            .secret.html                "INDEX-CANARY"
            .git/config                 "GIT-CANARY"
            .claude/settings.json       "CLAUDE-CANARY"
            a/visible.txt
            a/.b/c                      "NESTED-CANARY"
            docs/git-link    -> ../.git          (visible name, hidden target)
            docs/config-link -> ../.git/config
            site/index.html  -> ../.secret.html
            .alias           -> a                (hidden name, visible target)
            .bookmark        -> ../outside       (hidden-named mount)
            cfg              -> ../outside/.config  (mount on a hidden target)
            bundle.zip                  members .env and ok.txt
"""

import re
import zipfile
from urllib.parse import unquote

import pytest
from starlette.testclient import TestClient

import filemill.app as app_module
from filemill import api, paths

CANARIES = (
    "OUTSIDE-CANARY",
    "CONFIG-CANARY",
    "INDEX-CANARY",
    "GIT-CANARY",
    "CLAUDE-CANARY",
    "NESTED-CANARY",
    "ENV-CANARY",
)
HIDDEN_FILES = (".git/config", ".claude/settings.json", "a/.b/c")
HIDDEN_DIRS = (".git", ".claude", "a/.b")
# Visible names that lead to a hidden path, and hidden names that lead to a
# visible one. Both are 404, so a probe learns nothing about either.
HIDDEN_ROUTES = (
    *HIDDEN_FILES,
    "docs/config-link",
    "docs/git-link/config",
    ".alias/visible.txt",
    ".bookmark/secret.txt",
    "cfg/x.txt",
    "%252egit/config",
    # The API strips a path before resolving it, so a leading space must not
    # hide the dot from the check.
    "%20.alias/visible.txt",
    # httpx collapses a literal ``..`` in a URL path; the encoded one arrives.
    ".git/%2e%2e/README.md",
)


@pytest.fixture()
def public_tree(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    (outside / ".config").mkdir(parents=True)
    (outside / "secret.txt").write_text("OUTSIDE-CANARY")
    (outside / ".config" / "x.txt").write_text("CONFIG-CANARY")

    root = tmp_path / "root"
    for folder in (".git", ".claude", "a/.b", "docs", "site"):
        (root / folder).mkdir(parents=True)
    (root / "README.md").write_text("# Readme\n")
    (root / ".secret.html").write_text("INDEX-CANARY")
    (root / ".git" / "config").write_text("GIT-CANARY")
    (root / ".claude" / "settings.json").write_text('{"k": "CLAUDE-CANARY"}')
    (root / "a" / "visible.txt").write_text("visible")
    (root / "a" / ".b" / "c").write_text("NESTED-CANARY")
    (root / "docs" / "git-link").symlink_to("../.git", target_is_directory=True)
    (root / "docs" / "config-link").symlink_to("../.git/config")
    (root / "site" / "index.html").symlink_to("../.secret.html")
    (root / ".alias").symlink_to("a", target_is_directory=True)
    (root / ".bookmark").symlink_to(outside, target_is_directory=True)
    (root / "cfg").symlink_to(outside / ".config", target_is_directory=True)
    with zipfile.ZipFile(root / "bundle.zip", "w") as archive:
        archive.writestr(".env", "ENV-CANARY")
        archive.writestr("ok.txt", "ok")

    monkeypatch.setattr(app_module.app.state, "root", root)
    monkeypatch.setattr(app_module.app.state, "public", True)
    return root


@pytest.fixture()
def client(public_tree):
    return TestClient(
        app_module.app, base_url="http://localhost", raise_server_exceptions=False
    )


def _names(client, p, **params):
    response = client.get("/api/dir", params={"p": p, **params})
    assert response.status_code == 200
    return {entry["name"] for entry in response.json()["entries"]}


def _assert_not_found(response):
    assert response.status_code == 404, response.text[:200]
    assert not any(canary in response.text for canary in CANARIES)


# ── Listings ─────────────────────────────────────────────────────────────────


def test_listing_with_hidden_show_has_no_hidden_entries(client):
    names = _names(client, "", hidden="show")
    assert names == {"README.md", "a", "bundle.zip", "docs", "site"}
    assert _names(client, "a", hidden="show") == {"visible.txt"}


def test_listing_drops_symlinks_into_hidden_paths(client):
    assert _names(client, "docs") == set()


def test_listing_leaks_no_hidden_target_path(client):
    """``abs`` would print where a dropped symlink points."""
    for p in ("", "docs"):
        assert "/." not in client.get("/api/dir", params={"p": p}).text


def test_archive_listing_drops_hidden_members(client):
    response = client.get("/api/dir", params={"p": "bundle.zip", "v": ""})
    assert {e["name"] for e in response.json()["entries"]} == {"ok.txt"}


# ── Every file route answers 404 ─────────────────────────────────────────────


@pytest.mark.parametrize("rel", HIDDEN_ROUTES)
@pytest.mark.parametrize(
    "query",
    [
        "",
        "?filemill=raw",
        "?filemill=render",
        "?filemill=highlight",
        "?f",
        "?hidden=show",
    ],
)
def test_resource_route_is_404(client, rel, query):
    _assert_not_found(client.get(f"/{rel}{query}"))


@pytest.mark.parametrize("route", ["raw", "preview"])
@pytest.mark.parametrize("rel", HIDDEN_ROUTES)
def test_api_file_routes_are_404(client, route, rel):
    """A query value is decoded once, where a path is decoded twice."""
    _assert_not_found(
        client.get(f"/api/{route}", params={"p": unquote(rel), "hidden": "show"})
    )


@pytest.mark.parametrize("rel", (*HIDDEN_DIRS, "docs/git-link", ".alias", "cfg"))
def test_api_dir_is_404(client, rel):
    _assert_not_found(client.get("/api/dir", params={"p": rel, "hidden": "show"}))


@pytest.mark.parametrize("rel", [".git", "docs/git-link", "a/.b", " .alias"])
def test_search_in_hidden_folder_is_404(client, rel):
    _assert_not_found(client.get("/api/search", params={"q": "CANARY", "p": rel}))


def test_search_drops_hidden_matches(client, monkeypatch):
    """Even a ripgrep configured with ``--hidden`` cannot surface them."""

    def matches(root, query, focused=""):
        return {
            "matches": [
                {"path": path, "line": 1, "column": 1, "context": "x"}
                for path in (".git/config", "docs/config-link", "a/visible.txt")
            ]
        }

    monkeypatch.setattr(api, "search_root", matches)
    response = client.get("/api/search", params={"q": "x"})
    assert [m["path"] for m in response.json()["matches"]] == ["a/visible.txt"]


@pytest.mark.parametrize(
    "url",
    [
        "/api/raw?p=bundle.zip&v=.env",
        "/api/preview?p=bundle.zip&v=.env",
        "/api/dir?p=bundle.zip&v=.env",
        "/bundle.zip/.env",
        "/bundle.zip?filemill=render&vpath=.env",
        "/bundle.zip?vpath=.env",
    ],
)
def test_hidden_archive_member_is_404(client, url):
    _assert_not_found(client.get(url))


def test_index_symlink_into_hidden_path_is_absent(client, public_tree):
    """The folder answers alike whether or not the hidden target exists."""
    present = client.get("/site/")
    (public_tree / "site" / "index.html").unlink()
    (public_tree / "site" / "index.html").symlink_to("../.missing.html")
    missing = client.get("/site/")
    assert (present.status_code, missing.status_code) == (200, 200)
    assert "INDEX-CANARY" not in present.text
    assert "data-mutation-token" not in present.text
    assert app_module.app.state.mutation_token not in present.text


@pytest.mark.parametrize("rel", (*HIDDEN_FILES, "README.md", "a", "missing"))
def test_public_mutations_are_forbidden(public_tree, rel):
    headers = {
        "origin": "http://localhost",
        "x-filemill-token": app_module.app.state.mutation_token,
    }
    target = public_tree / rel
    before = target.read_bytes() if target.is_file() else None
    with TestClient(app_module.app, base_url="http://localhost") as client:
        save = client.post(
            "/api/save", params={"p": rel}, content="changed", headers=headers
        )
        delete = client.delete("/api/delete", params={"p": rel}, headers=headers)
    assert (save.status_code, delete.status_code) == (403, 403)
    if before is not None:
        assert target.read_bytes() == before
    assert (public_tree / "a" / "visible.txt").read_text() == "visible"


def test_shell_ignores_hidden_show(client):
    html = client.get("/?hidden=show").text
    assert "data-hidden" not in html


# ── Visible paths still work ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/README.md",
        "/a/visible.txt",
        "/a/visible.txt?filemill=render",
        "/api/raw?p=a/visible.txt",
        "/api/dir?p=a",
        "/api/raw?p=bundle.zip&v=ok.txt",
    ],
)
def test_visible_paths_are_served(client, url):
    assert client.get(url).status_code == 200


def test_resource_serves_visible_file(client, public_tree):
    response = client.get("/a/visible.txt")
    assert response.text == "visible"


# ── Private mode is unchanged ────────────────────────────────────────────────


def test_private_mode_lists_and_serves_hidden_paths(client, monkeypatch):
    monkeypatch.setattr(app_module.app.state, "public", False)
    assert {".git", ".claude", ".alias", ".bookmark", "cfg"} <= _names(client, "")
    assert _names(client, "docs") == {"git-link", "config-link"}
    for rel in HIDDEN_FILES:
        assert client.get(f"/{rel}").status_code == 200
    assert client.get("/.bookmark/secret.txt").text == "OUTSIDE-CANARY"
    assert client.get("/api/raw?p=bundle.zip&v=.env").text == "ENV-CANARY"
    assert re.search(r'data-hidden="show"', client.get("/?hidden=show").text)


# ── The rule itself ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "rel,expected",
    [
        ("", False),
        ("a/b.txt", False),
        ("a.b/c", False),
        (".git", True),
        ("a/.b/c", True),
        ("%2egit/config", True),
        (" .git", True),
        ("a/ .b", False),
        ("a/../b", True),
        ("./a", True),
    ],
)
def test_hidden(rel, expected):
    assert paths.hidden(rel) is expected


def test_public_zones_keep_root_and_visible_bookmarks(public_tree):
    zones = paths.public_zones(public_tree, paths.symlink_zones(public_tree))
    assert set(zones) == {public_tree.name}


def test_bookmark_named_like_the_root_cannot_open_a_hidden_folder(
    tmp_path, monkeypatch
):
    """``symlink_zones`` lets such a bookmark replace the root's own zone."""
    ssh = tmp_path / "home" / ".ssh"
    ssh.mkdir(parents=True)
    (ssh / "id_rsa").write_text("SSH-CANARY")
    root = tmp_path / "site"
    root.mkdir()
    (root / "site").symlink_to(ssh, target_is_directory=True)
    monkeypatch.setattr(app_module.app.state, "root", root)
    monkeypatch.setattr(app_module.app.state, "public", True)
    client = TestClient(
        app_module.app, base_url="http://localhost", raise_server_exceptions=False
    )
    for url in ("/site/id_rsa", "/api/dir?p=site"):
        response = client.get(url)
        assert response.status_code == 404
        assert "id_rsa" not in response.text and "SSH-CANARY" not in response.text


def test_root_under_a_hidden_folder_is_served_beside_an_ancestor_bookmark(
    tmp_path, monkeypatch
):
    """The root is the operator's choice, even below a bookmark's hidden folder."""
    root = tmp_path / "home" / ".srv" / "root"
    root.mkdir(parents=True)
    (root / "f.txt").write_text("f")
    (root / "home").symlink_to(tmp_path / "home", target_is_directory=True)
    monkeypatch.setattr(app_module.app.state, "root", root)
    monkeypatch.setattr(app_module.app.state, "public", True)
    client = TestClient(
        app_module.app, base_url="http://localhost", raise_server_exceptions=False
    )
    assert client.get("/f.txt").text == "f"
    assert "f.txt" in _names(client, "")
    assert client.get("/home/.srv/root/f.txt").status_code == 404


def test_public_zones_keep_a_root_under_a_hidden_folder(tmp_path):
    root = tmp_path / ".srv" / "root"
    root.mkdir(parents=True)
    (root / "f.txt").write_text("f")
    zones = paths.public_zones(root, paths.symlink_zones(root))
    assert paths.resolve_safe(str(root / "f.txt"), root, zones, public=True)


def test_visible(public_tree):
    zones = paths.public_zones(public_tree, paths.symlink_zones(public_tree))
    assert paths.visible(public_tree / "a" / "visible.txt", zones)
    assert not paths.visible(public_tree / "a" / ".b" / "c", zones)
    assert not paths.visible(public_tree.parent / "outside" / "secret.txt", zones)


@pytest.mark.parametrize("value,expected", [("1", "True"), ("", "False")])
def test_direct_asgi_app_reads_public_mode_from_env(monkeypatch, value, expected):
    """Uvicorn's reload and direct ASGI loading import the app afresh."""
    import subprocess
    import sys

    monkeypatch.setenv("FILEMILL_PUBLIC", value)
    out = subprocess.run(
        [sys.executable, "-c", "import filemill.app as a; print(a.app.state.public)"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert out == expected


async def test_public_save_refused_before_body(public_tree):
    from starlette.requests import Request

    async def receive():
        pytest.fail("public save consumed request bytes")

    request = Request(
        {
            "type": "http",
            "app": app_module.app,
            "method": "POST",
            "scheme": "http",
            "path": "/api/save",
            "query_string": b"",
            "headers": [
                (b"host", b"localhost"),
                (b"origin", b"http://localhost"),
                (b"x-filemill-token", app_module.app.state.mutation_token.encode()),
            ],
        },
        receive,
    )
    assert (await app_module.api_save(request, p="README.md")).status_code == 403
