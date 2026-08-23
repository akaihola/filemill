"""Tests for the shared query parser and URL builder (PLAN-19 §1)."""

import pytest
from starlette.datastructures import QueryParams

from filemill.urls import (
    DEFAULT_LAYOUT,
    DEFAULT_VIEW,
    LAYOUT_COMPRESSED,
    LAYOUT_NONE,
    VIEW_HIGHLIGHT,
    VIEW_RAW,
    VIEW_RENDER,
    ViewState,
    build_url,
    parse_state,
    url_for_state,
)

# ── Defaults ─────────────────────────────────────────────────────────────────


def test_empty_query_gives_documented_defaults():
    """No query at all means raw bytes, full columns, dotfiles hidden."""
    state = parse_state(QueryParams(""))
    assert (state.view, state.layout) == (
        DEFAULT_VIEW,
        DEFAULT_LAYOUT,
    )
    assert (DEFAULT_VIEW, DEFAULT_LAYOUT) == (
        "raw",
        "full-columns",
    )


@pytest.mark.parametrize("view", ["render", "highlight", "raw"])
def test_each_view_value_parses(view):
    assert parse_state(QueryParams(f"filemill={view}")).view == view


@pytest.mark.parametrize("query", ["filemill", "filemill=", "f", "f="])
def test_render_shorthands(query):
    assert parse_state(QueryParams(query)).view == VIEW_RENDER


def test_full_view_parameter_takes_priority_over_shortcut():
    assert parse_state(QueryParams("f&filemill=raw")).view == VIEW_RAW


@pytest.mark.parametrize("layout", ["full-columns", "compressed-columns", "no-columns"])
def test_each_layout_value_parses(layout):
    assert parse_state(QueryParams(f"layout={layout}")).layout == layout


# ── Malformed, empty, repeated, encoded ──────────────────────────────────────


@pytest.mark.parametrize(
    "query",
    [
        "filemill=nonsense",
        "filemill=RENDER",
        "filemill=render%00",
        "filemill=../../etc/passwd",
    ],
)
def test_invalid_view_falls_back_to_default(query):
    assert parse_state(QueryParams(query)).view == DEFAULT_VIEW


@pytest.mark.parametrize("query", ["layout=wide", "layout=", "layout=no-columns2"])
def test_invalid_layout_falls_back_to_default(query):
    assert parse_state(QueryParams(query)).layout == DEFAULT_LAYOUT


def test_repeated_value_takes_the_last_occurrence():
    """A rewriting router appends; the appended value has to win."""
    state = parse_state(QueryParams("filemill=raw&filemill=render"))
    assert state.view == VIEW_RENDER


def test_repeated_value_with_invalid_last_falls_back_to_default():
    state = parse_state(QueryParams("layout=no-columns&layout=nonsense"))
    assert state.layout == DEFAULT_LAYOUT


def test_unknown_parameters_are_ignored():
    state = parse_state(QueryParams("view=rendered&mode=raw&filemill=render"))
    assert state.view == VIEW_RENDER


def test_vpath_is_stripped_of_surrounding_slashes():
    assert parse_state(QueryParams("vpath=/users/42/")).vpath == "users/42"


def test_plain_dict_parses_like_query_params():
    """The parser accepts a plain mapping, which keeps unit tests cheap."""
    assert parse_state({"filemill": "highlight"}).view == VIEW_HIGHLIGHT


# ── Derived flags ────────────────────────────────────────────────────────────


def test_no_columns_layout_reports_no_columns():
    assert parse_state(QueryParams("layout=no-columns")).wants_columns is False


@pytest.mark.parametrize("layout", ["full-columns", "compressed-columns"])
def test_column_layouts_report_columns(layout):
    assert parse_state(QueryParams(f"layout={layout}")).wants_columns is True


# ── build_url ────────────────────────────────────────────────────────────────


def test_bare_path_is_the_canonical_url():
    assert build_url("docs/readme.md") == "/docs/readme.md"


def test_leading_slash_is_not_doubled():
    assert build_url("/docs/readme.md") == "/docs/readme.md"


def test_root_is_a_single_slash():
    assert build_url("") == "/"


def test_view_parameter_is_named_filemill():
    assert build_url("a.md", view=VIEW_RENDER) == "/a.md?filemill=render"


def test_view_and_layout_appear_in_a_stable_order():
    url = build_url("a.md", view=VIEW_RENDER, layout=LAYOUT_NONE)
    assert url == "/a.md?filemill=render&layout=no-columns"


def test_invalid_values_are_dropped_not_emitted():
    """Every generated link carries valid values, by construction."""
    assert build_url("a.md", view="nonsense", layout="wide") == "/a.md"


def test_path_separators_survive_encoding():
    assert build_url("a/b/c.md") == "/a/b/c.md"


def test_space_in_a_filename_is_encoded_once():
    assert build_url("my notes/a b.md") == "/my%20notes/a%20b.md"


def test_percent_in_a_filename_is_encoded_once():
    """A literal %20 in a name encodes to %2520 and stays distinct from a space."""
    assert build_url("a%20b.md") == "/a%2520b.md"


def test_hash_in_a_filename_cannot_start_a_fragment():
    assert build_url("a#b.md") == "/a%23b.md"


def test_question_mark_in_a_filename_cannot_start_a_query():
    assert build_url("a?b.md") == "/a%3Fb.md"


def test_ampersand_in_a_query_value_is_encoded():
    assert build_url("a.db", vpath="users/a&b") == "/a.db?vpath=users%2Fa%26b"


def test_vpath_rides_along():
    assert build_url("sample.db", vpath="users/42") == "/sample.db?vpath=users%2F42"


# ── url_for_state ────────────────────────────────────────────────────────────


def test_url_for_state_keeps_non_default_layout_when_switching_view():
    """Switching to raw drops the view parameter: the bare path *is* the raw file.

    Clicking "Raw" therefore lands the reader on the canonical short URL, which
    is the contract's own best explanation of itself. The layout and dotfile
    choices they already made ride along.
    """
    state = ViewState(view=VIEW_RENDER, layout=LAYOUT_NONE)
    assert url_for_state("a.md", state, view=VIEW_RAW) == (
        "/a.md?layout=no-columns"
    )


def test_build_url_can_still_pin_the_raw_view_explicitly():
    """A router that must not rely on the default spells the value out."""
    assert build_url("a.md", view=VIEW_RAW) == "/a.md?filemill=raw"


def test_url_for_state_omits_defaults():
    state = ViewState()
    assert url_for_state("a.md", state) == "/a.md"


def test_url_for_state_keeps_vpath():
    state = ViewState(view=VIEW_RENDER, vpath="users/42")
    assert url_for_state("sample.db", state) == (
        "/sample.db?filemill=render&vpath=users%2F42"
    )


def test_with_view_replaces_only_the_view():
    state = ViewState(view=VIEW_RAW, layout=LAYOUT_COMPRESSED)
    switched = state.with_view(VIEW_HIGHLIGHT)
    assert switched.view == VIEW_HIGHLIGHT
    assert switched.layout == LAYOUT_COMPRESSED


def test_with_view_rejects_an_unknown_value():
    assert ViewState().with_view("nonsense").view == DEFAULT_VIEW
