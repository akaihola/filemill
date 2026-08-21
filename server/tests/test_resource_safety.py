"""The safety boundary holds for every view and layout (PLAN-19 §"Safety").

``_resolve_safe()`` exists because a path that arrived in a URL must not escape
the configured root. PLAN-19 adds a query-parameter dimension on top of that
path, so the question this module answers is narrow and specific: does any
combination of ``filemill`` and ``layout`` open a way past it?

Every test here asserts on the **resolved path**, not on the request string. A
request string can be normalised by the client before it reaches the server —
httpx collapses a literal ``..`` segment, so ``/../outside/secret.txt`` arrives
as ``/outside/secret.txt`` — and a test that only inspected the string it sent
would be testing the client. The percent-encoded forms below survive that
normalisation and are the ones that actually reach the handler.

Directory layout built by the ``escape_tree`` fixture:

    tmp/
        outside/
            secret.txt                  "TOP-SECRET-CANARY"
            dirA/
                file_in_A.txt
                cross_link -> ../dirB/file_in_B.txt   (escapes dirA)
            dirB/file_in_B.txt          "CANARY-IN-B"
        menuEVIL/evil.txt               "EVIL-CANARY"   (ROOT-prefix sibling)
        menu/                           <- ROOT
            real_file.txt
            docs/
                guide.md
                escape     -> ../../outside/secret.txt (nested, escapes ROOT)
                escape_dir -> ../../outside            (nested, escapes ROOT)
            bookmark -> ../outside/dirA (direct child: an allowed zone-2 mount)
"""

from pathlib import Path
from urllib.parse import urlencode

import pytest
from starlette.testclient import TestClient

import filemill.app as app_module
from filemill.urls import LAYOUTS, VIEWS

CANARY = "TOP-SECRET-CANARY"

# "" means "send no such parameter at all", which is a distinct case from
# sending the default: it is the URL a person actually types.
VIEW_CASES = ("", *VIEWS)
LAYOUT_CASES = ("", *LAYOUTS)

# Paths that must never resolve. The percent-encoded forms are the ones that
# survive client-side normalisation; the plain ones are kept because
# _resource_target() is also called directly, where nothing normalises them.
ESCAPE_PATHS = (
    "/%2e%2e/outside/secret.txt",
    "/..%2F..%2Foutside/secret.txt",
    "/docs/%2e%2e/%2e%2e/outside/secret.txt",
    "/%252e%252e/outside/secret.txt",
    "/docs/escape",
    "/docs/escape_dir/secret.txt",
    "/bookmark/cross_link",
    "/%2e%2e/menuEVIL/evil.txt",
    "/etc/passwd",
    "/....//outside/secret.txt",
)


@pytest.fixture()
def escape_tree(tmp_path, monkeypatch):
    """Build the tree in the module docstring and point ROOT at ``menu/``."""
    outside = tmp_path / "outside"
    dir_a, dir_b = outside / "dirA", outside / "dirB"
    dir_a.mkdir(parents=True)
    dir_b.mkdir(parents=True)
    (outside / "secret.txt").write_text(CANARY)
    (dir_a / "file_in_A.txt").write_text("A")
    (dir_b / "file_in_B.txt").write_text("CANARY-IN-B")
    (dir_a / "cross_link").symlink_to(dir_b / "file_in_B.txt")

    evil = tmp_path / "menuEVIL"
    evil.mkdir()
    (evil / "evil.txt").write_text("EVIL-CANARY")

    root = tmp_path / "menu"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (root / "real_file.txt").write_text("real")
    (docs / "guide.md").write_text("# Guide\n\nBody text.\n")
    (docs / "escape").symlink_to(outside / "secret.txt")
    (docs / "escape_dir").symlink_to(outside, target_is_directory=True)
    (root / "bookmark").symlink_to(dir_a, target_is_directory=True)

    monkeypatch.setattr(app_module, "ROOT", root)
    return {"root": root, "outside": outside, "dir_a": dir_a, "evil": evil}


@pytest.fixture()
def recorder(escape_tree, monkeypatch):
    """Wrap ``_resolve_safe`` so tests can assert on what it was asked and returned.

    The wrapper records ``(path_str, result)`` for every call. ``_resource_target``
    looks the name up on the module at call time, so patching the attribute
    catches the calls made through ``api.split_vfs`` too.
    """
    calls: list[tuple[str, Path | None]] = []
    original = app_module._resolve_safe

    def spy(path_str: str, root: Path | None = None):
        result = original(path_str, root=root)
        calls.append((path_str, result))
        return result

    monkeypatch.setattr(app_module, "_resolve_safe", spy)
    return calls


def _client():
    return TestClient(app_module.app, raise_server_exceptions=False)


def _query(view: str, layout: str) -> str:
    pairs = []
    if view:
        pairs.append(("filemill", view))
    if layout:
        pairs.append(("layout", layout))
    return f"?{urlencode(pairs)}" if pairs else ""


def _allowed_zones(root: Path) -> list[Path]:
    """ROOT plus each direct-symlink-child target — the zones ``_resolve_safe`` permits."""
    zones = [root.resolve()]
    zones.extend(c.resolve() for c in root.iterdir() if c.is_symlink())
    return zones


def _inside_allowed_zone(resolved: Path, root: Path) -> bool:
    return any(resolved == z or z in resolved.parents for z in _allowed_zones(root))


# ── The boundary holds for every view × layout ───────────────────────────────


@pytest.mark.parametrize("path", ESCAPE_PATHS)
@pytest.mark.parametrize("view", VIEW_CASES)
@pytest.mark.parametrize("layout", LAYOUT_CASES)
def test_escape_is_denied_for_every_view_and_layout(
    recorder, escape_tree, path, view, layout
):
    """No view/layout pair turns a traversal or an escaping symlink into a hit.

    The assertion is on what ``_resolve_safe`` returned: every resolution during
    the request either failed outright or landed inside an allowed zone. That is
    the property, and it does not depend on how the client spelled the request.
    """
    root = escape_tree["root"]
    resp = _client().get(f"{path}{_query(view, layout)}")

    assert resp.status_code == 404
    assert CANARY not in resp.text
    assert "EVIL-CANARY" not in resp.text
    assert "CANARY-IN-B" not in resp.text

    assert recorder, "the request never reached _resolve_safe"
    for path_str, resolved in recorder:
        assert resolved is None or _inside_allowed_zone(resolved, root), (
            f"_resolve_safe({path_str!r}) returned {resolved}, "
            f"outside every allowed zone of {root}"
        )


@pytest.mark.parametrize("view", VIEW_CASES)
@pytest.mark.parametrize("layout", LAYOUT_CASES)
def test_legitimate_file_still_resolves_for_every_view_and_layout(
    recorder, escape_tree, view, layout
):
    """The positive control: the matrix above is not passing because all of it 404s."""
    resp = _client().get(f"/docs/guide.md{_query(view, layout)}")
    assert resp.status_code == 200
    assert recorder
    assert any(r is not None for _, r in recorder)


# ── The query cannot take part in the decision ───────────────────────────────


@pytest.mark.parametrize("path", ["/docs/guide.md", "/%2e%2e/outside/secret.txt"])
def test_resolution_is_identical_across_every_view_and_layout(escape_tree, path):
    """The strongest form of the property: the query changes nothing that resolves.

    Each view/layout pair is driven through the same path and the arguments and
    results of every ``_resolve_safe`` call are compared. Identical across all 20
    combinations means the new query dimension cannot participate in containment,
    rather than merely happening not to this time.
    """
    original = app_module._resolve_safe
    seen: dict[tuple[str, str], list[tuple[str, str | None]]] = {}

    for view in VIEW_CASES:
        for layout in LAYOUT_CASES:
            calls: list[tuple[str, str | None]] = []

            def spy(path_str, root=None, _calls=calls):
                result = original(path_str, root=root)
                _calls.append((path_str, None if result is None else str(result)))
                return result

            app_module._resolve_safe = spy
            try:
                _client().get(f"{path}{_query(view, layout)}")
            finally:
                app_module._resolve_safe = original
            seen[(view, layout)] = calls

    baseline = seen[("", "")]
    for key, calls in seen.items():
        assert calls == baseline, f"{key} resolved differently from the bare URL"


# ── The same denials at the unit level, with nothing normalising the string ──


@pytest.mark.parametrize("path", ESCAPE_PATHS)
def test_resource_target_denies_escape_without_a_client_in_the_way(escape_tree, path):
    """``_resource_target`` refuses the raw string, including the literal ``..`` forms.

    httpx collapses a literal ``..`` before sending, so the HTTP tests above can
    only prove the encoded cases. This one hands the handler the string directly.
    """
    assert app_module._resource_target(path.lstrip("/")) is None


@pytest.mark.parametrize(
    "path",
    [
        "../outside/secret.txt",
        "docs/../../outside/secret.txt",
        "/outside/secret.txt",
        "//outside/secret.txt",
        "/etc/passwd",
        "\\\\outside\\secret.txt",
    ],
)
def test_resource_target_denies_absolute_and_literal_traversal(escape_tree, path):
    """An absolute path is rejected before it is joined, not normalised into ROOT."""
    assert app_module._resource_target(path) is None


def test_resource_target_allows_a_file_under_root(escape_tree):
    found = app_module._resource_target("docs/guide.md")
    assert found is not None
    target, rel, vpath = found
    assert target == (escape_tree["root"] / "docs" / "guide.md").resolve()
    assert (rel, vpath) == ("docs/guide.md", "")


def test_resource_target_allows_a_bookmark_target(escape_tree):
    """A direct symlink child of ROOT stays browsable — zone 2 is unchanged."""
    found = app_module._resource_target("bookmark/file_in_A.txt")
    assert found is not None
    assert found[0] == (escape_tree["dir_a"] / "file_in_A.txt").resolve()


# ── A denial says nothing about what is on the other side ────────────────────


def test_denied_and_missing_are_indistinguishable(escape_tree):
    """An existing outside file and an absent one give the identical response."""
    exists_outside = _client().get("/%2e%2e/outside/secret.txt")
    absent_outside = _client().get("/%2e%2e/outside/no_such_file.txt")
    assert exists_outside.status_code == absent_outside.status_code == 404
    assert exists_outside.text == absent_outside.text


# ── The bookmark zone is not widened by a view or a layout ───────────────────


@pytest.mark.parametrize("view", VIEW_CASES)
@pytest.mark.parametrize("layout", LAYOUT_CASES)
def test_symlink_escaping_a_bookmark_is_denied_for_every_view_and_layout(
    escape_tree, view, layout
):
    """``bookmark/cross_link`` points out of dirA into dirB and must stay denied."""
    resp = _client().get(f"/bookmark/cross_link{_query(view, layout)}")
    assert resp.status_code == 404
    assert "CANARY-IN-B" not in resp.text


@pytest.mark.parametrize("view", VIEW_CASES)
@pytest.mark.parametrize("layout", LAYOUT_CASES)
def test_root_prefix_sibling_is_denied_for_every_view_and_layout(
    escape_tree, view, layout
):
    """ROOT is ``…/menu``; ``…/menuEVIL`` must not pass a startswith-style check."""
    resp = _client().get(f"/%2e%2e/menuEVIL/evil.txt{_query(view, layout)}")
    assert resp.status_code == 404
    assert "EVIL-CANARY" not in resp.text
