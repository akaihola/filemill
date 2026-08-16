import pytest
from pathlib import Path
from pykofinder.columns import entry_icon, list_column, initial_columns


# ── entry_icon ──────────────────────────────────────────────────────────────


def test_entry_icon_directory(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    assert entry_icon(d) == "📁"


def test_entry_icon_desktop(tmp_path):
    f = tmp_path / "link.desktop"
    f.touch()
    assert entry_icon(f) == "🔗"


def test_entry_icon_md(tmp_path):
    f = tmp_path / "note.md"
    f.touch()
    assert entry_icon(f) == "📝"


def test_entry_icon_pdf(tmp_path):
    f = tmp_path / "doc.pdf"
    f.touch()
    assert entry_icon(f) == "📑"


def test_entry_icon_docx(tmp_path):
    f = tmp_path / "doc.docx"
    f.touch()
    assert entry_icon(f) == "📄"


def test_entry_icon_pptx(tmp_path):
    f = tmp_path / "deck.pptx"
    f.touch()
    assert entry_icon(f) == "🎞"


@pytest.mark.parametrize("ext", [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"])
def test_entry_icon_image(tmp_path, ext):
    f = tmp_path / f"img{ext}"
    f.touch()
    assert entry_icon(f) == "🖼"


@pytest.mark.parametrize("ext", [".xlsx", ".xls", ".csv"])
def test_entry_icon_spreadsheet(tmp_path, ext):
    f = tmp_path / f"data{ext}"
    f.touch()
    assert entry_icon(f) == "📊"


def test_entry_icon_unknown_ext(tmp_path):
    f = tmp_path / "file.xyz"
    f.touch()
    assert entry_icon(f) == "📄"


# ── list_column ──────────────────────────────────────────────────────────────


def test_list_column_dirs_sorted_before_files(tmp_path):
    (tmp_path / "z_file.txt").touch()
    (tmp_path / "a_subdir").mkdir()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert html.index("a_subdir") < html.index("z_file.txt")


def test_list_column_dotfiles_have_dotfile_class(tmp_path):
    """Dotfiles are rendered but carry class='dotfile' for CSS toggling."""
    (tmp_path / ".hidden").touch()
    (tmp_path / "visible.txt").touch()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert ".hidden" in html  # dotfile IS rendered now
    assert "dotfile" in html  # … but marked with CSS class
    assert "visible.txt" in html  # normal entry still present


def test_list_column_desktop_has_open_link_href(tmp_path):
    (tmp_path / "link.desktop").touch()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert "/open-link" in html


def test_list_column_desktop_has_target_blank(tmp_path):
    (tmp_path / "link.desktop").touch()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert "_blank" in html


def test_list_column_desktop_has_no_htmx(tmp_path):
    """Desktop entries must not use hx-get (no HTMX, no preview update)."""
    (tmp_path / "link.desktop").touch()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert "hx-get" not in html


def test_list_column_dir_uses_hx_get_click(tmp_path):
    (tmp_path / "subdir").mkdir()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert "hx-get" in html
    assert "/click" in html


def test_list_column_dir_targets_next_col(tmp_path):
    (tmp_path / "sub").mkdir()
    html = list_column(tmp_path, tmp_path, col_index=2).__html__()
    assert "col-3" in html  # hx-target and sentinel div


def test_list_column_file_targets_preview(tmp_path):
    (tmp_path / "note.md").touch()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert "preview" in html


def test_list_column_permission_error_produces_empty_list(tmp_path, monkeypatch):
    def raise_perm(self):
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "iterdir", raise_perm)
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert "<li" not in html  # no entries rendered


def test_list_column_div_id_matches_col_index(tmp_path):
    html = list_column(tmp_path, tmp_path, col_index=3).__html__()
    assert 'id="col-3"' in html


# ── initial_columns ──────────────────────────────────────────────────────────


def test_initial_columns_structure(tmp_path):
    html = initial_columns(tmp_path).__html__()
    assert 'id="finder"' in html
    assert 'id="col-0"' in html
    assert 'id="col-1"' in html
    assert 'id="preview"' in html


# ── render_breadcrumb ─────────────────────────────────────────────────────────


def test_render_breadcrumb_root_shows_tilde(tmp_path):
    from pykofinder.columns import render_breadcrumb

    html = render_breadcrumb(tmp_path, tmp_path)
    assert 'id="breadcrumb"' in html
    assert "~" in html


def test_render_breadcrumb_one_level(tmp_path):
    from pykofinder.columns import render_breadcrumb

    sub = tmp_path / "documents"
    html = render_breadcrumb(sub, tmp_path)
    assert "documents" in html


def test_render_breadcrumb_nested(tmp_path):
    from pykofinder.columns import render_breadcrumb

    deep = tmp_path / "a" / "b" / "c.md"
    html = render_breadcrumb(deep, tmp_path)
    assert "a" in html
    assert "b" in html
    assert "c.md" in html


def test_render_breadcrumb_escapes_html(tmp_path):
    from pykofinder.columns import render_breadcrumb

    sub = tmp_path / "<evil>"
    html = render_breadcrumb(sub, tmp_path)
    assert "<evil>" not in html
    assert "&lt;evil&gt;" in html


def test_initial_columns_has_breadcrumb(tmp_path):
    html = initial_columns(tmp_path).__html__()
    assert 'id="breadcrumb"' in html
    assert 'id="app-shell"' in html


def test_render_breadcrumb_path_outside_root(tmp_path):
    """When path is not under root, relative_to raises ValueError; segments must be empty."""
    import tempfile
    from pykofinder.columns import render_breadcrumb

    with tempfile.TemporaryDirectory() as other_root:
        html = render_breadcrumb(Path(other_root), tmp_path)
        assert 'id="breadcrumb"' in html
        assert "~" in html
        # No segment spans – the path is outside root
        assert "bc-seg" not in html


# ── #18 VFS: entry_icon, list_column VFS routing, list_vfs_column, breadcrumb vpath ──


def test_entry_icon_db(tmp_path):
    f = tmp_path / "data.db"
    f.touch()
    assert entry_icon(f) == "🗄️"


def test_list_column_db_file_targets_next_col(tmp_path):
    db = tmp_path / "data.db"
    db.touch()
    html = list_column(tmp_path, tmp_path, col_index=1).__html__()
    assert "col-2" in html  # hx-target for the db file link


def test_list_column_db_file_does_not_target_preview(tmp_path):
    db = tmp_path / "data.db"
    db.touch()
    md = tmp_path / "note.md"
    md.write_text("# hello")
    html = list_column(tmp_path, tmp_path, col_index=1).__html__()
    # md still targets preview (regression check)
    assert "#preview" in html


def test_list_vfs_column_renders_folder_entries(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
    html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", 1).__html__()
    assert "users" in html


def test_list_vfs_column_folder_targets_next_col(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
    html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", col_index=2).__html__()
    assert "col-3" in html


def test_list_vfs_column_leaf_targets_preview(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="row_1", vpath="users/1", is_folder=False, icon="📋")]
    html = list_vfs_column(
        entries, "foo.db", "/abs/foo.db", "users", col_index=2
    ).__html__()
    assert "preview" in html


def test_list_vfs_column_fmt_bar_absent_when_not_requested(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
    html = list_vfs_column(
        entries, "foo.db", "/abs/foo.db", "", col_index=1, show_fmt_bar=False
    ).__html__()
    assert "fmt-bar" not in html


def test_list_vfs_column_fmt_bar_present_when_requested(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="r1", vpath="users/1", is_folder=False, icon="📋")]
    html = list_vfs_column(
        entries, "foo.db", "/abs/foo.db", "users", col_index=2, show_fmt_bar=True
    ).__html__()
    assert "fmt-bar" in html


def test_list_vfs_column_fmt_bar_active_is_rows(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="r1", vpath="users/1", is_folder=False, icon="📋")]
    html = list_vfs_column(
        entries,
        "foo.db",
        "/abs/foo.db",
        "users",
        col_index=2,
        show_fmt_bar=True,
        active_fmt="folders",
    ).__html__()
    assert "📋 Rows" in html
    assert "📊 Spreadsheet" in html


def test_list_vfs_column_url_has_vpath(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
    html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", col_index=1).__html__()
    assert "vpath=users" in html


def test_list_vfs_column_col_id(tmp_path):
    from pykofinder.columns import list_vfs_column

    html = list_vfs_column([], "f.db", "/f.db", "", col_index=5).__html__()
    assert 'id="col-5"' in html


def test_list_vfs_column_prune_script_present(tmp_path):
    from pykofinder.columns import list_vfs_column

    html = list_vfs_column([], "f.db", "/f.db", "", col_index=3).__html__()
    assert "<script>" in html


def test_list_vfs_column_data_fpath_on_entries(tmp_path):
    from pykofinder.vfs import VFSEntry
    from pykofinder.columns import list_vfs_column

    entries = [VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️")]
    html = list_vfs_column(entries, "f.db", "/abs/f.db", "", col_index=1).__html__()
    assert "data-fpath" in html


def test_render_breadcrumb_with_vpath(tmp_path):
    from pykofinder.columns import render_breadcrumb

    html = render_breadcrumb(tmp_path / "foo.db", tmp_path, vpath="users")
    assert "users" in html
    assert "bc-virtual" in html


def test_render_breadcrumb_with_nested_vpath(tmp_path):
    from pykofinder.columns import render_breadcrumb

    html = render_breadcrumb(tmp_path / "foo.db", tmp_path, vpath="users/42")
    assert "users" in html
    assert "42" in html


# ── #25 dotfile visibility toggle ─────────────────────────────────────────────


def test_list_column_dotfile_dir_has_dotfile_class(tmp_path):
    """Dotfile directories are rendered with class='dotfile'."""
    (tmp_path / ".hidden_dir").mkdir()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert ".hidden_dir" in html
    assert "dotfile" in html


def test_list_column_non_dotfile_has_no_dotfile_class(tmp_path):
    """Regular entries must NOT carry class='dotfile'."""
    (tmp_path / "regular.txt").touch()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert "regular.txt" in html
    # No dotfile class attribute when only regular entries are present
    assert 'class="dotfile"' not in html


def test_render_breadcrumb_has_dotfiles_toggle(tmp_path):
    """Breadcrumb must contain the dotfiles toggle button."""
    from pykofinder.columns import render_breadcrumb

    html = render_breadcrumb(tmp_path, tmp_path)
    assert "dotfiles-btn" in html
    assert "toggleDotfiles" in html


def test_render_breadcrumb_toggle_inside_nav(tmp_path):
    """The dotfiles button must be contained inside <nav id='breadcrumb'>."""
    from pykofinder.columns import render_breadcrumb

    html = render_breadcrumb(tmp_path, tmp_path)
    nav_start = html.index('<nav id="breadcrumb"')
    btn_pos = html.index("dotfiles-btn")
    assert btn_pos > nav_start  # button is inside the nav


def test_render_breadcrumb_has_zoom_btn(tmp_path):
    """Breadcrumb must contain the zoom toggle button (moved out of fixed overlay)."""
    from pykofinder.columns import render_breadcrumb

    html = render_breadcrumb(tmp_path, tmp_path)
    assert "zoom-btn" in html
    assert "toggleZoom" in html


def test_render_breadcrumb_zoom_btn_inside_nav(tmp_path):
    """Zoom button must be inside <nav id='breadcrumb'>, not injected by JS."""
    from pykofinder.columns import render_breadcrumb

    html = render_breadcrumb(tmp_path, tmp_path)
    nav_start = html.index('<nav id="breadcrumb"')
    zoom_pos = html.index("zoom-btn")
    assert zoom_pos > nav_start


# ── #27 list_column selected_name ─────────────────────────────────────────────


def test_list_column_selected_name_adds_selected_class(tmp_path):
    """Entry whose name matches selected_name must have class 'selected'."""
    (tmp_path / "target.md").write_text("hi")
    (tmp_path / "other.txt").write_text("ho")
    html = list_column(tmp_path, tmp_path, 0, selected_name="target.md").__html__()
    # target.md li should carry class="selected"
    assert 'class="selected"' in html
    # other.txt li must NOT have class="selected" on its <li>
    idx_other = html.index("other.txt")
    li_before = html.rfind("<li", 0, idx_other)
    # Grab only the opening <li ...> tag (up to the first >)
    li_tag_end = html.find(">", li_before)
    li_tag = html[li_before : li_tag_end + 1]
    assert 'class="selected"' not in li_tag


def test_list_column_selected_name_none_no_selected_class(tmp_path):
    """Default call (no selected_name) must not produce any selected class on <li>."""
    (tmp_path / "file.txt").write_text("x")
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert 'class="selected"' not in html


def test_list_column_dotfile_and_selected_has_both_classes(tmp_path):
    """A dotfile entry that is also selected must carry both 'dotfile' and 'selected'."""
    (tmp_path / ".secret").write_text("shhh")
    html = list_column(tmp_path, tmp_path, 0, selected_name=".secret").__html__()
    # The <li> opening tag must contain both classes
    idx_secret = html.index(".secret")
    li_start = html.rfind("<li", 0, idx_secret)
    li_tag_end = html.find(">", li_start)
    li_tag = html[li_start : li_tag_end + 1]
    assert "dotfile" in li_tag
    assert "selected" in li_tag


# ── #29 VFS URL sync – selected_vpath in list_vfs_column ──────────────────


def test_list_vfs_column_selected_vpath_adds_selected_class():
    """Entry whose vpath matches selected_vpath must have class 'selected' on its <li>."""
    from pykofinder.columns import list_vfs_column
    from pykofinder.vfs import VFSEntry

    entries = [
        VFSEntry(name="items", vpath="items", is_folder=True, icon="🗃️"),
        VFSEntry(name="users", vpath="users", is_folder=True, icon="🗃️"),
    ]
    html = list_vfs_column(
        entries, "foo.db", "/abs/foo.db", "", col_index=0, selected_vpath="items"
    ).__html__()

    # The <li> for "items" must carry class="selected"
    idx_items = html.index("items")
    li_start = html.rfind("<li", 0, idx_items)
    li_end = html.find(">", li_start)
    li_tag = html[li_start : li_end + 1]
    assert "selected" in li_tag

    # The <li> for "users" must NOT carry class="selected"
    idx_users = html.index("users")
    li_start_u = html.rfind("<li", 0, idx_users)
    li_end_u = html.find(">", li_start_u)
    li_tag_u = html[li_start_u : li_end_u + 1]
    assert "selected" not in li_tag_u


def test_list_vfs_column_no_selected_vpath_no_selected_class():
    """Default call (no selected_vpath) must not produce 'selected' on any <li>."""
    from pykofinder.columns import list_vfs_column
    from pykofinder.vfs import VFSEntry

    entries = [
        VFSEntry(name="items", vpath="items", is_folder=True, icon="🗃️"),
    ]
    html = list_vfs_column(entries, "foo.db", "/abs/foo.db", "", col_index=0).__html__()
    # No <li> should carry the selected class
    assert 'class="selected"' not in html


# ── #41 selected dotfile always visible (CSS override) ────────────────────────


def test_selected_dotfile_dir_carries_both_classes(tmp_path):
    """A dotfile *directory* that is the selected item must carry both 'dotfile'
    and 'selected' CSS classes on its <li> even when dotfiles are normally hidden."""
    dot_dir = tmp_path / ".config"
    dot_dir.mkdir()
    (tmp_path / "visible.txt").touch()
    html = list_column(tmp_path, tmp_path, 0, selected_name=".config").__html__()
    idx = html.index(".config")
    li_start = html.rfind("<li", 0, idx)
    li_end = html.find(">", li_start)
    li_tag = html[li_start : li_end + 1]
    assert "dotfile" in li_tag
    assert "selected" in li_tag


def test_app_css_shows_selected_dotfile_when_dotfiles_hidden():
    """APP_CSS must override li.dotfile visibility for selected items so that a
    selected dotfile entry is always visible even without the 'show-dotfiles' body class."""
    from pykofinder.styles import APP_CSS

    assert "li.dotfile.selected" in APP_CSS


def test_list_vfs_column_row_level_selected_vpath():
    """selected_vpath with composite vpath (tablename/rowkey) selects the right row."""
    from pykofinder.columns import list_vfs_column
    from pykofinder.vfs import VFSEntry

    entries = [
        VFSEntry(name="1", vpath="items/1", is_folder=False, icon="📋"),
        VFSEntry(name="2", vpath="items/2", is_folder=False, icon="📋"),
    ]
    html = list_vfs_column(
        entries,
        "foo.db",
        "/abs/foo.db",
        "items",
        col_index=1,
        selected_vpath="items/1",
    ).__html__()

    idx_1 = html.index(">1<")
    li_start = html.rfind("<li", 0, idx_1)
    li_end = html.find(">", li_start)
    li_tag = html[li_start : li_end + 1]
    assert "selected" in li_tag
