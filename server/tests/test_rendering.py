from pathlib import Path

from filemill.rendering import (
    _find_file_for_href,
    _find_git_root,
    _href_for_file,
    md,
)


def test_md_renders_bold():
    assert "<strong>bold</strong>" in md.render("**bold**")


def test_md_renders_table():
    assert "<table>" in md.render("| a | b |\n|---|---|\n| 1 | 2 |\n")


def test_md_renders_strikethrough():
    html = md.render("~~deleted~~")
    assert "<del>deleted</del>" in html or "<s>" in html


# ── #22 plain URL linkification ───────────────────────────────────────────────


def test_linkify_plain_https_url():
    """A bare HTTPS URL in markdown text becomes a clickable anchor."""
    rendered = md.render("Visit https://example.com today")
    assert '<a href="https://example.com">' in rendered


def test_linkify_plain_http_url():
    rendered = md.render("See http://foo.bar/path for details")
    assert '<a href="http://foo.bar/path">' in rendered


def test_linkify_markdown_link_not_double_processed():
    """Explicit [text](url) links are not processed twice."""
    rendered = md.render("[click](https://example.com)")
    assert rendered.count("<a ") == 1
    assert 'href="https://example.com"' in rendered


# ── #21 mermaid diagram rendering ────────────────────────────────────────────


def test_mermaid_fence_produces_div():
    """A ```mermaid fence becomes <div class="mermaid">."""
    src = "```mermaid\ngraph TD\n  A-->B\n```"
    rendered = md.render(src)
    assert '<div class="mermaid">' in rendered
    assert "<pre>" not in rendered


def test_mermaid_content_html_escaped():
    """Mermaid content with special chars is HTML-escaped inside the div."""
    src = "```mermaid\ngraph TD\n  A-->B & C<D>\n```"
    rendered = md.render(src)
    assert "&amp;" in rendered or "&lt;" in rendered


def test_mermaid_div_contains_diagram_source():
    src = "```mermaid\nsequenceDiagram\n  Alice->>Bob: Hello\n```"
    rendered = md.render(src)
    assert "sequenceDiagram" in rendered
    assert "Alice" in rendered


def test_non_mermaid_fence_is_plain_for_the_browser_to_colour():
    """A fence is <pre><code class="language-x"> with the source escaped and no
    server-side spans: ui/core/syntax.js colours it, in both builds."""
    src = "```python\nprint('<hi>')\n```"
    rendered = md.render(src)
    assert '<div class="mermaid">' not in rendered
    assert '<pre><code class="language-python">' in rendered
    assert "&lt;hi&gt;" in rendered
    assert "<span" not in rendered


def test_paragraph_newlines_are_not_line_breaks():
    """A soft line break inside a paragraph stays whitespace, never a <br>."""
    rendered = md.render("line one\nline two\n")
    assert "<p>line one\nline two</p>" in rendered
    assert "<br" not in rendered


def test_markdown_paragraph_boundaries_and_hard_breaks():
    rendered = md.render("one\ntwo\n\nthree  \nfour")
    assert rendered.count("<p>") == 2
    assert "<p>one\ntwo</p>" in rendered
    assert "<p>three<br />\nfour</p>" in rendered


# ── #19 git-root finding ──────────────────────────────────────────────────────


def test_find_git_root_finds_ancestor(tmp_path):
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "sub" / "deep"
    sub.mkdir(parents=True)
    assert _find_git_root(sub) == tmp_path


def test_find_git_root_returns_none_when_no_git(tmp_path, monkeypatch):
    """The walk returns None when no directory it visits holds a ``.git``.

    The start path is relative on purpose, so the walk pins its own root. An
    absolute ``tmp_path / "a" / "b"`` walks all the way to ``/`` and so depends on
    every directory above the temp directory: this host has a real ``/tmp/.git``
    and pytest puts ``tmp_path`` under ``/tmp``, which made the assertion read
    ``assert Path('/tmp') is None``. ``Path("a/b").parents`` is ``a`` and ``.``
    and stops, so after chdir the three directories the walk visits are the three
    this test created.
    """
    (tmp_path / "a" / "b").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert _find_git_root(Path("a/b")) is None


def test_find_git_root_on_git_dir_itself(tmp_path):
    (tmp_path / ".git").mkdir()
    assert _find_git_root(tmp_path) == tmp_path


# ── #19 href file-finding ─────────────────────────────────────────────────────


def test_find_file_for_href_relative_sibling(tmp_path):
    """Resolves a sibling-file relative href from the source directory."""
    src = tmp_path / "docs" / "note.md"
    src.parent.mkdir()
    src.touch()
    target = tmp_path / "docs" / "other.md"
    target.touch()
    assert _find_file_for_href("other.md", src) == target.resolve()


def test_find_file_for_href_relative_subdir(tmp_path):
    """Resolves a subdirectory-relative href."""
    src = tmp_path / "note.md"
    src.touch()
    sub = tmp_path / "images" / "photo.png"
    sub.parent.mkdir()
    sub.touch()
    assert _find_file_for_href("images/photo.png", src) == sub.resolve()


def test_find_file_for_href_absolute_url_skipped(tmp_path):
    src = tmp_path / "note.md"
    src.touch()
    assert _find_file_for_href("https://example.com/page", src) is None


def test_find_file_for_href_anchor_skipped(tmp_path):
    src = tmp_path / "note.md"
    src.touch()
    assert _find_file_for_href("#section", src) is None


def test_find_file_for_href_slash_skipped(tmp_path):
    src = tmp_path / "note.md"
    src.touch()
    assert _find_file_for_href("/absolute/path.md", src) is None


def test_find_file_for_href_not_found(tmp_path):
    """Returns None when no file matches anywhere."""
    (tmp_path / ".git").mkdir()
    src = tmp_path / "note.md"
    src.touch()
    assert _find_file_for_href("nonexistent_xyz_abc.md", src) is None


def test_find_file_for_href_walks_up_to_git_root(tmp_path):
    """Finds a file in a sibling directory by walking up to the git root."""
    (tmp_path / ".git").mkdir()
    src_dir = tmp_path / "docs"
    src_dir.mkdir()
    src = src_dir / "note.md"
    src.touch()
    target = tmp_path / "assets" / "image.png"
    target.parent.mkdir()
    target.touch()
    assert _find_file_for_href("assets/image.png", src) == target.resolve()


def test_find_file_for_href_recursive_search(tmp_path):
    """Finds a file by basename rglob when direct relative lookup fails."""
    (tmp_path / ".git").mkdir()
    src = tmp_path / "note.md"
    src.touch()
    target = tmp_path / "deep" / "nested" / "diagram.png"
    target.parent.mkdir(parents=True)
    target.touch()
    assert _find_file_for_href("diagram.png", src) == target.resolve()


def test_find_file_for_href_strips_fragment(tmp_path):
    """Fragment (#anchor) in href is stripped before file lookup."""
    src = tmp_path / "note.md"
    src.touch()
    target = tmp_path / "other.md"
    target.touch()
    assert _find_file_for_href("other.md#heading-1", src) == target.resolve()


def test_find_file_for_href_no_git_still_finds_relative(tmp_path):
    """With no .git root, still finds files relative to source dir (step 1)."""
    src = tmp_path / "note.md"
    src.touch()
    target = tmp_path / "sibling.md"
    target.touch()
    assert _find_file_for_href("sibling.md", src) == target.resolve()


# ── #19 href URL generation ───────────────────────────────────────────────────


def test_href_for_md_file_uses_root_relative_rendered_url(tmp_path, monkeypatch):
    """.md files get their own path plus filemill=render (PLAN-19 §4).

    Was ``/f/{mount}/page.md`` before the URL contract landed. The old form is
    still routed and still answers, so an existing bookmark is unaffected; only
    newly generated links moved.
    """
    import filemill.app as app_module

    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    f = tmp_path / "page.md"
    f.touch()
    assert _href_for_file(f) == "/page.md?filemill=render"


def test_href_for_md_file_uses_canonical_finder_path_for_symlink_child(
    tmp_path, monkeypatch
):
    """Markdown under a direct symlink child keeps the *visible* path, not the target's.

    The reader sees ``/my-knowledge/docs/topic.md``, the path they navigated, not
    the workspace directory the symlink resolves to.
    """
    import filemill.app as app_module

    workspace = tmp_path / "workspace"
    docs = workspace / "docs"
    docs.mkdir(parents=True)
    root = tmp_path / "menu"
    root.mkdir()
    (root / "my-knowledge").symlink_to(workspace, target_is_directory=True)
    monkeypatch.setattr(app_module, "ROOT", root)

    f = docs / "topic.md"
    f.touch()
    href = _href_for_file(f.resolve())
    assert href == "/my-knowledge/docs/topic.md?filemill=render"


def test_href_for_other_file_uses_raw(tmp_path):
    """Non-.md files get /raw?path=... for direct byte serving."""
    f = tmp_path / "photo.png"
    assert _href_for_file(f).startswith("/raw?path=")


# ── #19 link normalization in rendered markdown ───────────────────────────────


def test_md_link_relative_normalized(tmp_path, monkeypatch):
    """A relative [text](file.md) link is rewritten to the target's own path."""
    import filemill.app as app_module

    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    src = tmp_path / "note.md"
    src.write_text("[link](other.md)")
    target = tmp_path / "other.md"
    target.touch()
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert 'href="/other.md?filemill=render"' in rendered
    assert "/?path=" not in rendered


def test_md_link_absolute_url_unchanged(tmp_path):
    """Absolute URLs are never rewritten."""
    src = tmp_path / "note.md"
    src.write_text("[link](https://example.com/page)")
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert 'href="https://example.com/page"' in rendered


def test_md_link_not_found_unchanged(tmp_path):
    """A relative link with no matching file is left as-is."""
    (tmp_path / ".git").mkdir()
    src = tmp_path / "note.md"
    src.write_text("[link](ghost.md)")
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert 'href="ghost.md"' in rendered


def test_md_link_no_env_unchanged():
    """Without source_path env, all links are left untouched."""
    rendered = md.render("[link](other.md)")
    assert 'href="other.md"' in rendered


# ── #20 wikilink rendering ────────────────────────────────────────────────────


def test_wikilink_basic_renders_anchor():
    """[[WikiLink]] renders as <a class="wikilink">."""
    rendered = md.render("See [[MyNote]] for details")
    assert 'class="wikilink"' in rendered
    assert ">MyNote</a>" in rendered


def test_wikilink_with_display_text():
    """[[Target|Display]] uses the display text for the link label."""
    rendered = md.render("See [[OtherPage|click here]]")
    assert ">click here</a>" in rendered


def test_wikilink_unresolved_gets_hash_href():
    """An unresolved [[WikiLink]] gets href='#wikilink-{name}'."""
    rendered = md.render("[[NonExistentFile]]")
    assert "#wikilink-" in rendered


def test_wikilink_resolved_gets_proper_href(tmp_path, monkeypatch):
    """A [[WikiLink]] resolving to a .md file gets that file's own path."""
    import filemill.app as app_module

    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    src = tmp_path / "note.md"
    src.write_text("See [[Target]]")
    target = tmp_path / "Target.md"
    target.touch()
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert "/Target.md?filemill=render" in rendered
    assert "/?path=" not in rendered


def test_wikilink_does_not_break_normal_links():
    """Normal [text](url) links still render correctly alongside wikilinks."""
    rendered = md.render("[normal](https://ex.com) and [[Wiki]]")
    assert 'href="https://ex.com"' in rendered
    assert 'class="wikilink"' in rendered


def test_wikilink_empty_brackets_not_matched():
    """[[]] (empty) is not treated as a wikilink."""
    rendered = md.render("This is [[]] empty")
    assert 'class="wikilink"' not in rendered


def test_find_file_for_href_empty_string(tmp_path):
    """An empty href returns None immediately."""
    src = tmp_path / "note.md"
    src.touch()
    assert _find_file_for_href("", src) is None


def test_find_file_for_href_query_only(tmp_path):
    """An href that is only a query string (e.g. '?q=1') returns None."""
    src = tmp_path / "note.md"
    src.touch()
    assert _find_file_for_href("?q=1", src) is None


def test_find_file_for_href_ftp_skipped(tmp_path):
    """ftp:// URLs are not resolved."""
    src = tmp_path / "note.md"
    src.touch()
    assert _find_file_for_href("ftp://example.com/file.txt", src) is None


def test_find_file_for_href_skips_hidden_dir_in_rglob(tmp_path):
    """Files inside hidden directories are skipped in the recursive search."""
    (tmp_path / ".git").mkdir()
    src = tmp_path / "note.md"
    src.touch()
    # Place target inside a hidden directory — should be skipped
    hidden = tmp_path / ".hidden_dir" / "secret.md"
    hidden.parent.mkdir()
    hidden.touch()
    # The file should NOT be found because it's inside a hidden directory
    assert _find_file_for_href("secret.md", src) is None


def test_find_file_for_href_step2_fails_step3_succeeds(tmp_path):
    """Step 2 walks up to git_root without finding file; step 3 finds it by rglob."""
    (tmp_path / ".git").mkdir()
    src_dir = tmp_path / "docs"
    src_dir.mkdir()
    src = src_dir / "note.md"
    src.touch()
    # File is NOT findable by href "x/target.md" from any ancestor of docs
    # (there's no docs/x/target.md, nor tmp_path/x/target.md)
    # but rglob from git_root finds it
    target = tmp_path / "data" / "archive" / "target.md"
    target.parent.mkdir(parents=True)
    target.touch()
    found = _find_file_for_href("x/target.md", src)
    # rglob by basename "target.md" finds it
    assert found == target.resolve()
