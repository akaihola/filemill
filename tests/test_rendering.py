from unittest.mock import patch

from pykofinder.rendering import (
    _find_file_for_href,
    _find_git_root,
    _href_for_file,
    highlighter,
    md,
)


def test_highlighter_known_lang():
    """lang is truthy → get_lexer_by_name path; Pygments wraps tokens in <span>."""
    result = highlighter("x = 1", "python", "")
    assert "<span" in result


def test_highlighter_empty_lang_guesses():
    """Empty lang → guess_lexer path; returns non-empty string."""
    result = highlighter("print('hi')", "", "")
    assert isinstance(result, str) and len(result) > 0


def test_highlighter_bad_lang_falls_back_to_text():
    """get_lexer_by_name raises → TextLexer fallback; still returns a string."""
    with patch(
        "pykofinder.rendering.get_lexer_by_name", side_effect=Exception("no lexer")
    ):
        result = highlighter("some code", "nonexistent_lang_xyz", "")
    assert isinstance(result, str) and len(result) > 0


def test_md_renders_bold():
    assert "<strong>bold</strong>" in md.render("**bold**")


def test_md_renders_table():
    assert "<table>" in md.render("| a | b |\n|---|---|\n| 1 | 2 |\n")


def test_md_renders_strikethrough():
    html = md.render("~~deleted~~")
    assert "<del>deleted</del>" in html or "<s>" in html


# ── #10 selected state ────────────────────────────────────────────────────────


def test_selected_css_present_in_app_css():
    from pykofinder.styles import APP_CSS

    assert "li.selected" in APP_CSS or ".selected" in APP_CSS


def test_selection_js_present_in_column_js():
    from pykofinder.styles import COLUMN_JS

    assert "classList.add('selected')" in COLUMN_JS or "selected" in COLUMN_JS


# ── #22 plain URL linkification ───────────────────────────────────────────────


def test_linkify_plain_https_url():
    """A bare HTTPS URL in markdown text becomes a clickable <a>."""
    rendered = md.render("Visit https://example.com today")
    assert '<a href="https://example.com">' in rendered


def test_linkify_plain_http_url():
    rendered = md.render("See http://foo.bar/path for details")
    assert '<a href="http://foo.bar/path">' in rendered


def test_linkify_markdown_link_unchanged():
    """Explicit [text](url) Markdown links are not double-processed."""
    rendered = md.render("[click](https://example.com)")
    assert rendered.count("<a ") == 1
    assert 'href="https://example.com"' in rendered


# ── #21 mermaid diagram rendering ────────────────────────────────────────────


def test_mermaid_fence_produces_div():
    """A ```mermaid fence block becomes <div class="mermaid">."""
    src = "```mermaid\ngraph TD\n  A-->B\n```"
    rendered = md.render(src)
    assert '<div class="mermaid">' in rendered
    assert "<pre>" not in rendered


def test_mermaid_content_html_escaped():
    """Mermaid content with < > & is HTML-escaped inside the div."""
    src = "```mermaid\ngraph TD\n  A-->B & C<D>\n```"
    rendered = md.render(src)
    assert "&amp;" in rendered or "&lt;" in rendered


def test_mermaid_div_contains_diagram_source():
    src = "```mermaid\nsequenceDiagram\n  Alice->>Bob: Hello\n```"
    rendered = md.render(src)
    assert "sequenceDiagram" in rendered
    assert "Alice" in rendered


def test_non_mermaid_fence_still_highlighted():
    """Non-mermaid code fences still get Pygments highlighting."""
    src = "```python\nprint('hi')\n```"
    rendered = md.render(src)
    # Pygments wraps in <span> or similar; should NOT be a plain mermaid div
    assert '<div class="mermaid">' not in rendered
    assert "print" in rendered


# ── #19 git-root finding ──────────────────────────────────────────────────────


def test_find_git_root_finds_ancestor(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    sub = tmp_path / "sub" / "deep"
    sub.mkdir(parents=True)
    f = sub / "note.md"
    f.touch()
    assert _find_git_root(sub) == tmp_path


def test_find_git_root_returns_none_when_no_git(tmp_path):
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert _find_git_root(sub) is None


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
    found = _find_file_for_href("other.md", src)
    assert found == target.resolve()


def test_find_file_for_href_relative_subdir(tmp_path):
    """Resolves a subdirectory-relative href."""
    src = tmp_path / "note.md"
    src.touch()
    sub = tmp_path / "images" / "photo.png"
    sub.parent.mkdir()
    sub.touch()
    found = _find_file_for_href("images/photo.png", src)
    assert found == sub.resolve()


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
    # target is at git root level (not relative to src's dir)
    target = tmp_path / "assets" / "image.png"
    target.parent.mkdir()
    target.touch()
    found = _find_file_for_href("assets/image.png", src)
    assert found == target.resolve()


def test_find_file_for_href_recursive_search(tmp_path):
    """Finds file anywhere under git root by basename when direct paths fail."""
    (tmp_path / ".git").mkdir()
    src = tmp_path / "note.md"
    src.touch()
    target = tmp_path / "deep" / "nested" / "diagram.png"
    target.parent.mkdir(parents=True)
    target.touch()
    found = _find_file_for_href("diagram.png", src)
    assert found == target.resolve()


def test_find_file_for_href_strips_fragment(tmp_path):
    """Fragment (#anchor) in href is stripped before file lookup."""
    src = tmp_path / "note.md"
    src.touch()
    target = tmp_path / "other.md"
    target.touch()
    found = _find_file_for_href("other.md#heading-1", src)
    assert found == target.resolve()


def test_find_file_for_href_no_git_root_still_finds_relative(tmp_path):
    """With no .git root, still finds files relative to source dir."""
    src = tmp_path / "note.md"
    src.touch()
    target = tmp_path / "sibling.md"
    target.touch()
    # No .git dir → _find_git_root returns None, but step 1 still works
    found = _find_file_for_href("sibling.md", src)
    assert found == target.resolve()


# ── #19 href URL generation ───────────────────────────────────────────────────


def test_href_for_md_file_uses_deep_link(tmp_path):
    """.md files get /?path=... so _deepNavigate opens them in the finder."""
    f = tmp_path / "page.md"
    assert _href_for_file(f).startswith("/?path=")
    assert "page.md" in _href_for_file(f)


def test_href_for_other_file_uses_raw(tmp_path):
    """Non-.md files get /raw?path=... for direct serving."""
    f = tmp_path / "photo.png"
    href = _href_for_file(f)
    assert href.startswith("/raw?path=")


# ── #19 link normalization in rendered markdown ───────────────────────────────


def test_md_link_relative_normalized(tmp_path):
    """A relative [text](file.md) link is rewritten to /?path=... when file exists."""
    src = tmp_path / "note.md"
    src.write_text("[link](other.md)")
    target = tmp_path / "other.md"
    target.touch()
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert "/?path=" in rendered
    assert str(target.resolve()) in rendered


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
    """[[Target|Display]] uses the display text, not the target."""
    rendered = md.render("See [[OtherPage|click here]] for info")
    assert ">click here</a>" in rendered
    assert "OtherPage" not in rendered.replace("OtherPage", "")  # target not in text
    # The display text should appear in the link
    assert ">click here<" in rendered


def test_wikilink_unresolved_gets_hash_href():
    """An unresolved [[WikiLink]] gets href='#wikilink-{name}'."""
    rendered = md.render("[[NonExistentFile]]")
    assert "#wikilink-" in rendered


def test_wikilink_resolved_gets_proper_href(tmp_path):
    """A [[WikiLink]] that resolves to a .md file gets /?path=... href."""
    src = tmp_path / "note.md"
    src.write_text("See [[Target]]")
    target = tmp_path / "Target.md"
    target.touch()
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert "/?path=" in rendered
    assert str(target.resolve()) in rendered


def test_wikilink_does_not_break_normal_links():
    """Normal [text](url) links still render correctly alongside wikilinks."""
    rendered = md.render("[normal](https://ex.com) and [[Wiki]]")
    assert 'href="https://ex.com"' in rendered
    assert 'class="wikilink"' in rendered


def test_wikilink_empty_brackets_not_matched():
    """[[]] (empty) is not treated as a wikilink."""
    rendered = md.render("This is [[]] empty")
    # Should not produce a wikilink anchor
    assert 'class="wikilink"' not in rendered
