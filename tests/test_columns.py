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


def test_list_column_skips_dotfiles(tmp_path):
    (tmp_path / ".hidden").touch()
    (tmp_path / "visible.txt").touch()
    html = list_column(tmp_path, tmp_path, 0).__html__()
    assert ".hidden" not in html
    assert "visible.txt" in html


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
