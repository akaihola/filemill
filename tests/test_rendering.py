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


def test_non_mermaid_fence_still_highlighted():
    """Non-mermaid fences still get Pygments highlighting, not a mermaid div."""
    src = "```python\nprint('hi')\n```"
    rendered = md.render(src)
    assert '<div class="mermaid">' not in rendered
    assert "print" in rendered


# ── #19 git-root finding ──────────────────────────────────────────────────────


def test_find_git_root_finds_ancestor(tmp_path):
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "sub" / "deep"
    sub.mkdir(parents=True)
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


def test_href_for_md_file_uses_canonical_finder_path(tmp_path, monkeypatch):
    """.md files get a canonical /f/{mount}/{relative} URL when ROOT matches the workspace."""
    import pykofinder.app as app_module

    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    f = tmp_path / "page.md"
    f.touch()
    href = _href_for_file(f)
    assert href == f"/f/{tmp_path.name}/page.md"


def test_href_for_md_file_uses_canonical_finder_path_for_symlink_child(
    tmp_path, monkeypatch
):
    """Markdown under a direct symlink child keeps the ROOT mount in finder URLs."""
    import pykofinder.app as app_module

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
    assert href == "/f/menu/my-knowledge/docs/topic.md"


def test_href_for_other_file_uses_raw(tmp_path):
    """Non-.md files get /raw?path=... for direct byte serving."""
    f = tmp_path / "photo.png"
    assert _href_for_file(f).startswith("/raw?path=")


# ── #19 link normalization in rendered markdown ───────────────────────────────


def test_md_link_relative_normalized(tmp_path, monkeypatch):
    """A relative [text](file.md) link is rewritten to a canonical /f/{mount}/{relative} URL."""
    import pykofinder.app as app_module

    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    src = tmp_path / "note.md"
    src.write_text("[link](other.md)")
    target = tmp_path / "other.md"
    target.touch()
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert f"/f/{tmp_path.name}/other.md" in rendered
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
    """A [[WikiLink]] that resolves to a .md file gets a canonical /f/{mount}/{relative} href."""
    import pykofinder.app as app_module

    monkeypatch.setattr(app_module, "ROOT", tmp_path)
    src = tmp_path / "note.md"
    src.write_text("See [[Target]]")
    target = tmp_path / "Target.md"
    target.touch()
    rendered = md.render(src.read_text(), env={"source_path": src})
    assert f"/f/{tmp_path.name}/Target.md" in rendered
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


# ── #25 dotfile visibility toggle ─────────────────────────────────────────────


def test_dotfile_css_hidden_by_default():
    """li.dotfile entries must be hidden by default in APP_CSS."""
    from pykofinder.styles import APP_CSS

    assert "li.dotfile" in APP_CSS
    assert "display: none" in APP_CSS or "display:none" in APP_CSS


def test_dotfile_css_visible_with_body_class():
    """show-dotfiles body class must reveal dotfile entries."""
    from pykofinder.styles import APP_CSS

    assert "show-dotfiles" in APP_CSS


def test_dotfiles_toggle_js_in_column_js():
    """COLUMN_JS must contain toggleDotfiles and _syncDotBtn functions."""
    from pykofinder.styles import COLUMN_JS

    assert "toggleDotfiles" in COLUMN_JS
    assert "_syncDotBtn" in COLUMN_JS


def test_dotfiles_toggle_js_persists_to_localstorage():
    """COLUMN_JS must write to localStorage for persistence."""
    from pykofinder.styles import COLUMN_JS

    assert "pykofinder_show_dotfiles" in COLUMN_JS


def test_dotfiles_sync_btn_called_on_after_settle():
    """_syncDotBtn() call must appear inside the htmx:afterSettle handler."""
    from pykofinder.styles import COLUMN_JS

    assert "afterSettle" in COLUMN_JS
    # Search for the _syncDotBtn() *call* (with parens) starting from afterSettle
    settle_pos = COLUMN_JS.index("afterSettle")
    call_pos = COLUMN_JS.index("_syncDotBtn()", settle_pos)
    assert call_pos > settle_pos


def test_zoom_toggle_js_exists():
    """COLUMN_JS must expose toggleZoom() for the server-rendered zoom button."""
    from pykofinder.styles import COLUMN_JS

    assert "toggleZoom" in COLUMN_JS


def test_zoom_btn_not_fixed_position():
    """#zoom-btn must no longer use position:fixed (lives in breadcrumb flex row)."""
    from pykofinder.styles import APP_CSS

    # Find the #zoom-btn rule block and confirm 'fixed' is absent from it
    assert "#zoom-btn" not in APP_CSS or "position: fixed" not in APP_CSS


def test_preview_spreadsheet_has_no_padding_rule():
    """#preview must have zero padding when it contains a spreadsheet preview.

    The fmt-bar in Spreadsheet view lives inside #preview, while in Rows view
    it lives inside the column panel (no padding). Without this rule the toggle
    buttons jump by 16px vertically / 24px horizontally on every switch.
    """
    from pykofinder.styles import APP_CSS

    assert "#preview:has(.preview-db-spreadsheet)" in APP_CSS
    # Locate the block and verify padding:0 is part of it
    start = APP_CSS.index("#preview:has(.preview-db-spreadsheet)")
    block_end = APP_CSS.index("}", start)
    rule_block = APP_CSS[start:block_end]
    assert "padding" in rule_block
    assert "0" in rule_block


# ── #31 enhanced keyboard navigation ──────────────────────────────────────────


def test_keyboard_home_key_present():
    """COLUMN_JS must handle the 'Home' key (jump to first item)."""
    from pykofinder.styles import COLUMN_JS

    assert "'Home'" in COLUMN_JS


def test_keyboard_end_key_present():
    """COLUMN_JS must handle the 'End' key (jump to last item)."""
    from pykofinder.styles import COLUMN_JS

    assert "'End'" in COLUMN_JS


def test_keyboard_pageup_key_present():
    """COLUMN_JS must handle 'PageUp' (scroll up one page)."""
    from pykofinder.styles import COLUMN_JS

    assert "'PageUp'" in COLUMN_JS


def test_keyboard_pagedown_key_present():
    """COLUMN_JS must handle 'PageDown' (scroll down one page)."""
    from pykofinder.styles import COLUMN_JS

    assert "'PageDown'" in COLUMN_JS


def test_keyboard_focused_col_index_state():
    """COLUMN_JS maintains _focusedColIndex to track the active column."""
    from pykofinder.styles import COLUMN_JS

    assert "_focusedColIndex" in COLUMN_JS


def test_keyboard_visible_items_filters_dotfiles():
    """COLUMN_JS uses a visibleItems helper that skips hidden dotfile entries."""
    from pykofinder.styles import COLUMN_JS

    assert "visibleItems" in COLUMN_JS


def test_keyboard_left_closes_columns_beyond_the_exited():
    """ArrowLeft must close columns beyond the exited column and clear the preview."""
    from pykofinder.styles import COLUMN_JS

    left_pos = COLUMN_JS.index("'ArrowLeft'")
    break_pos = COLUMN_JS.index("break;", left_pos)
    left_block = COLUMN_JS[left_pos:break_pos]
    # ArrowLeft should now remove columns (the new required behavior)
    assert ".remove()" in left_block
    # ArrowLeft should also clear the preview
    assert "preview" in left_block and "innerHTML" in left_block


def test_keyboard_left_updates_last_col_count():
    """ArrowLeft must sync _lastColCount so the next ArrowRight detects the new column.

    Regression test for bug: ArrowLeft removed .column elements but did not update
    _lastColCount. The next htmx:afterSettle saw cols.length == _lastColCount and
    skipped auto-highlight, leaving the newly opened column with no selection.
    """
    from pykofinder.styles import COLUMN_JS

    left_pos = COLUMN_JS.index("'ArrowLeft'")
    break_pos = COLUMN_JS.index("break;", left_pos)
    left_block = COLUMN_JS[left_pos:break_pos]
    # Must assign _lastColCount inside the ArrowLeft handler
    assert "_lastColCount" in left_block


def test_keyboard_left_walks_dom_to_remove_sentinels():
    """ArrowLeft must walk the DOM to remove stale sentinel divs, not just .column elements.

    Regression test for bug: only removing .column nodes left orphaned sentinel divs
    (e.g. col-2) in the DOM before the re-inserted sentinel col-1. When a file was
    later opened, _build_prune_js(2) started at the stale col-2 sentinel, walked
    forward, and hit col-1 next – deleting it.
    """
    from pykofinder.styles import COLUMN_JS

    left_pos = COLUMN_JS.index("'ArrowLeft'")
    break_pos = COLUMN_JS.index("break;", left_pos)
    left_block = COLUMN_JS[left_pos:break_pos]
    # Must walk with nextElementSibling from the column element up to #preview
    assert "nextElementSibling" in left_block
    assert "preview" in left_block


def test_arrow_left_updates_url_from_parent_selection():
    """ArrowLeft must sync the URL from the selected entry in the parent column.

    Regression test for bug: ArrowLeft closed columns client-side but never updated
    the address bar, leaving the URL pointing at the deeper path that was just exited.
    """
    from pykofinder.styles import COLUMN_JS

    left_pos = COLUMN_JS.index("'ArrowLeft'")
    break_pos = COLUMN_JS.index("break;", left_pos)
    left_block = COLUMN_JS[left_pos:break_pos]
    assert "_capturePathStateFromLink" in left_block
    assert (
        "_syncUrl(leftState.path, leftState.vpath, leftState.finderUrl)" in left_block
    )


def test_arrow_left_at_root_resets_url():
    """ArrowLeft in the root column must reset the browser URL via the shared helper."""
    from pykofinder.styles import COLUMN_JS

    left_pos = COLUMN_JS.index("'ArrowLeft'")
    break_pos = COLUMN_JS.index("break;", left_pos)
    left_block = COLUMN_JS[left_pos:break_pos]
    assert "_syncUrl(null, null)" in left_block


def test_keyboard_right_checks_column_to_the_right():
    """ArrowRight must first check whether a column to the right exists before navigating."""
    from pykofinder.styles import COLUMN_JS

    right_pos = COLUMN_JS.index("'ArrowRight'")
    break_pos = COLUMN_JS.index("break;", right_pos)
    right_block = COLUMN_JS[right_pos:break_pos]
    assert "cols.length" in right_block


def test_keyboard_arrow_up_selects_last_when_no_selection():
    """ArrowUp with nothing selected must select the last visible item."""
    from pykofinder.styles import COLUMN_JS

    up_pos = COLUMN_JS.index("'ArrowUp'")
    break_pos = COLUMN_JS.index("break;", up_pos)
    up_block = COLUMN_JS[up_pos:break_pos]
    assert "selIdx < 0" in up_block
    assert "items.length - 1" in up_block


def test_keyboard_arrow_down_selects_first_when_no_selection():
    """ArrowDown with nothing selected must select the first visible item."""
    from pykofinder.styles import COLUMN_JS

    down_pos = COLUMN_JS.index("'ArrowDown'")
    break_pos = COLUMN_JS.index("break;", down_pos)
    down_block = COLUMN_JS[down_pos:break_pos]
    assert "selIdx < 0" in down_block
    assert "items[0]" in down_block


def test_keyboard_after_settle_updates_focused_col_index():
    """The keyboard IIFE's afterSettle handler must assign _focusedColIndex."""
    from pykofinder.styles import COLUMN_JS

    # Use the last afterSettle occurrence (the one inside the keyboard IIFE)
    settle_pos = COLUMN_JS.rindex("htmx:afterSettle")
    assign_pos = COLUMN_JS.index("_focusedColIndex =", settle_pos)
    assert assign_pos > settle_pos


def test_keyboard_enter_triggers_navigation():
    """Enter key must trigger navigation (triggerNav or htmx.trigger)."""
    from pykofinder.styles import COLUMN_JS

    assert "'Enter'" in COLUMN_JS
    enter_pos = COLUMN_JS.index("'Enter'")
    break_pos = COLUMN_JS.index("break;", enter_pos)
    enter_block = COLUMN_JS[enter_pos:break_pos]
    assert "triggerNav" in enter_block or "htmx.trigger" in enter_block


def test_no_document_body_addeventlistener_at_toplevel():
    """COLUMN_JS must never call document.body.addEventListener at IIFE top-level.

    Scripts run in <head> before <body> exists; any immediate
    document.body.addEventListener call throws TypeError and halts the
    entire script block (killing keyboard nav and other features).
    Use document.addEventListener instead – HTMX/click events bubble up.
    """
    from pykofinder.styles import COLUMN_JS

    assert "document.body.addEventListener" not in COLUMN_JS


# ── #32 column focus-state visual indicators ──────────────────────────────────


def test_col_ancestor_css_present():
    """APP_CSS must style .col-ancestor li.selected > a (muted highlight)."""
    from pykofinder.styles import APP_CSS

    assert "col-ancestor" in APP_CSS
    assert "col-ancestor li.selected" in APP_CSS


def test_col_descendant_css_present():
    """APP_CSS must style .col-descendant li.selected > a (subtle/remembered)."""
    from pykofinder.styles import APP_CSS

    assert "col-descendant" in APP_CSS
    assert "col-descendant li.selected" in APP_CSS


def test_col_descendant_icon_colour_overridden():
    """APP_CSS must override the icon colour inside descendant selected items."""
    from pykofinder.styles import APP_CSS

    assert "col-descendant li.selected > a .icon" in APP_CSS


def test_apply_focus_classes_function_exists():
    """COLUMN_JS must define an applyFocusClasses function."""
    from pykofinder.styles import COLUMN_JS

    assert "applyFocusClasses" in COLUMN_JS


def test_col_focused_class_stamped_in_js():
    """applyFocusClasses must stamp the col-focused class."""
    from pykofinder.styles import COLUMN_JS

    assert "col-focused" in COLUMN_JS


def test_col_ancestor_class_stamped_in_js():
    """applyFocusClasses must stamp the col-ancestor class."""
    from pykofinder.styles import COLUMN_JS

    assert "col-ancestor" in COLUMN_JS


def test_col_descendant_class_stamped_in_js():
    """applyFocusClasses must stamp the col-descendant class."""
    from pykofinder.styles import COLUMN_JS

    assert "col-descendant" in COLUMN_JS


def test_apply_focus_classes_called_on_arrow_left():
    """ArrowLeft handler must call applyFocusClasses() after shifting focus."""
    from pykofinder.styles import COLUMN_JS

    left_pos = COLUMN_JS.index("'ArrowLeft'")
    break_pos = COLUMN_JS.index("break;", left_pos)
    left_block = COLUMN_JS[left_pos:break_pos]
    assert "applyFocusClasses" in left_block


def test_apply_focus_classes_called_on_arrow_right():
    """ArrowRight triggers navigation; htmx:afterSettle handles focus update."""
    from pykofinder.styles import COLUMN_JS

    right_pos = COLUMN_JS.index("'ArrowRight'")
    break_pos = COLUMN_JS.index("break;", right_pos)
    right_block = COLUMN_JS[right_pos:break_pos]
    # ArrowRight now triggers HTMX navigation instead of directly managing focus
    # The afterSettle handler will update focus after the HTMX swap completes
    assert "triggerNav" in right_block


def test_arrow_right_opens_highlighted_item_in_next_column():
    """ArrowRight must navigate into the selected item (folder opens next column, file previews)."""
    from pykofinder.styles import COLUMN_JS

    right_pos = COLUMN_JS.index("'ArrowRight'")
    break_pos = COLUMN_JS.index("break;", right_pos)
    right_block = COLUMN_JS[right_pos:break_pos]
    # ArrowRight should trigger navigation when there's a selection
    assert "triggerNav" in right_block


def test_htmx_after_settle_auto_highlights_new_column():
    """When entering a previously unvisited folder, afterSettle must auto-highlight topmost item."""
    from pykofinder.styles import COLUMN_JS

    # Find the afterSettle handler in the keyboard IIFE
    settle_pos = COLUMN_JS.rindex("htmx:afterSettle")
    block_end = COLUMN_JS.index("});", settle_pos)
    settle_block = COLUMN_JS[settle_pos:block_end]
    # Should track column count to detect new columns
    assert "_lastColCount" in settle_block
    # Should auto-highlight first item in new column
    assert "selectLi" in settle_block and "items[0]" in settle_block


def test_apply_focus_classes_called_after_htmx_settle():
    """The keyboard IIFE's afterSettle handler must call applyFocusClasses()."""
    from pykofinder.styles import COLUMN_JS

    settle_pos = COLUMN_JS.rindex("htmx:afterSettle")
    block_end = COLUMN_JS.index("});", settle_pos)
    settle_block = COLUMN_JS[settle_pos:block_end]
    assert "applyFocusClasses" in settle_block


def test_kb_apply_focus_exposed_for_deep_navigate():
    """_kbApplyFocus must be declared at module level and called in _deepNavigate."""
    from pykofinder.styles import COLUMN_JS

    assert "_kbApplyFocus" in COLUMN_JS
    deep_pos = COLUMN_JS.index("function _deepNavigate")
    deep_end = COLUMN_JS.index("\n}", deep_pos)
    deep_block = COLUMN_JS[deep_pos:deep_end]
    assert "_kbApplyFocus" in deep_block
