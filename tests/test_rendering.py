from unittest.mock import patch
from pykofinder.rendering import highlighter, md


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
