"""The URL contract: one path per file, query parameters pick the representation.

A file has one address. ``/docs/readme.md`` names the resource; the query says
which representation of it you want. That split is what lets the gogo dashboard
embed a document without minting a second URL for it — the dashboard asks the
same path for ``?pykofinder-view=rendered&layout=no-columns``, and a colleague
who pastes the link into chat opens the same document with the finder around it.

Three query groups, each with one documented default:

    pykofinder-view = raw | rendered | highlighted     (default: raw)
    layout          = full-columns | compressed-columns | no-columns
                                                       (default: full-columns)
    hidden          = hide | show                      (default: hide)

``raw`` is the default because the bare path has to serve the bytes: a stylesheet
at ``/site/main.css`` must arrive as ``text/css``, not as a preview of one.

Rules that hold for every value:

- A missing value uses the default.
- An unrecognised value uses the default and never changes the requested path.
- A repeated value uses the last occurrence, then the two rules above.
- No query value reaches the filesystem. ``_resolve_safe()`` sees the path and
  nothing else, so no combination of view and layout can widen what it allows.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from urllib.parse import quote as urlquote
from urllib.parse import urlencode

VIEW_PARAM = "pykofinder-view"
LAYOUT_PARAM = "layout"
HIDDEN_PARAM = "hidden"
VPATH_PARAM = "vpath"

VIEW_RAW = "raw"
VIEW_RENDERED = "rendered"
VIEW_HIGHLIGHTED = "highlighted"
VIEWS: tuple[str, ...] = (VIEW_RAW, VIEW_RENDERED, VIEW_HIGHLIGHTED)

LAYOUT_FULL = "full-columns"
LAYOUT_COMPRESSED = "compressed-columns"
LAYOUT_NONE = "no-columns"
LAYOUTS: tuple[str, ...] = (LAYOUT_FULL, LAYOUT_COMPRESSED, LAYOUT_NONE)

HIDDEN_HIDE = "hide"
HIDDEN_SHOW = "show"
HIDDEN_VALUES: tuple[str, ...] = (HIDDEN_HIDE, HIDDEN_SHOW)

DEFAULT_VIEW = VIEW_RAW
DEFAULT_LAYOUT = LAYOUT_FULL
DEFAULT_HIDDEN = HIDDEN_HIDE

# Human labels for the switch controls, in the order they are rendered.
VIEW_LABELS: tuple[tuple[str, str], ...] = (
    (VIEW_RENDERED, "Rendered"),
    (VIEW_HIGHLIGHTED, "Source"),
    (VIEW_RAW, "Raw"),
)


@dataclass(frozen=True)
class ViewState:
    """The three query groups, already validated, plus any virtual path."""

    view: str = DEFAULT_VIEW
    layout: str = DEFAULT_LAYOUT
    hidden: str = DEFAULT_HIDDEN
    vpath: str = ""

    @property
    def wants_columns(self) -> bool:
        """True when the response should carry the Miller-columns finder shell."""
        return self.layout != LAYOUT_NONE

    @property
    def show_hidden(self) -> bool:
        """True when dotfiles are visible."""
        return self.hidden == HIDDEN_SHOW

    def with_view(self, view: str) -> ViewState:
        """Return the same state pointed at another representation."""
        return replace(self, view=view if view in VIEWS else DEFAULT_VIEW)


def _last(params, key: str) -> str | None:
    """Return the last occurrence of *key*, or None.

    Starlette's ``QueryParams`` is a multidict, so ``?layout=a&layout=b`` has two
    values. Taking the last one makes a rewriting router's appended parameter
    win, which is the behaviour the gogo router needs when it forwards a request.
    """
    getlist = getattr(params, "getlist", None)
    if getlist is not None:
        values = getlist(key)
        return values[-1] if values else None
    value = params.get(key)
    return value if value is not None else None


def _one_of(value: str | None, allowed: tuple[str, ...], default: str) -> str:
    """Return *value* when it is allowed, else *default*."""
    if value is None:
        return default
    return value if value in allowed else default


def parse_state(params) -> ViewState:
    """Read the three query groups out of a query mapping.

    *params* is anything with ``.get()`` — a Starlette ``QueryParams`` or a plain
    dict. Every field comes back valid, so callers never re-check.
    """
    vpath = _last(params, VPATH_PARAM) or ""
    return ViewState(
        view=_one_of(_last(params, VIEW_PARAM), VIEWS, DEFAULT_VIEW),
        layout=_one_of(_last(params, LAYOUT_PARAM), LAYOUTS, DEFAULT_LAYOUT),
        hidden=_one_of(_last(params, HIDDEN_PARAM), HIDDEN_VALUES, DEFAULT_HIDDEN),
        vpath=vpath.strip("/"),
    )


def build_url(
    rel: str,
    *,
    view: str | None = None,
    layout: str | None = None,
    hidden: str | None = None,
    vpath: str | None = None,
) -> str:
    """Build a root-relative URL: ``/`` + *rel*, plus the parameters given.

    Only the parameters passed explicitly appear in the result, so
    ``build_url("docs/readme.md")`` is the canonical bare address of the file.
    An unrecognised value is dropped rather than emitted, which keeps the
    promise that every generated link carries valid query values.

    Each value is encoded exactly once: the path through ``quote`` with ``/``
    left intact, the query through ``urlencode``. HTML escaping belongs at the
    output boundary, not here.
    """
    path = "/" + urlquote(rel.strip("/"), safe="/@:")
    pairs: list[tuple[str, str]] = []
    if view is not None and view in VIEWS:
        pairs.append((VIEW_PARAM, view))
    if layout is not None and layout in LAYOUTS:
        pairs.append((LAYOUT_PARAM, layout))
    if hidden is not None and hidden in HIDDEN_VALUES:
        pairs.append((HIDDEN_PARAM, hidden))
    if vpath:
        pairs.append((VPATH_PARAM, vpath.strip("/")))
    return f"{path}?{urlencode(pairs)}" if pairs else path


def url_for_state(rel: str, state: ViewState, *, view: str | None = None) -> str:
    """Build the URL for *rel* in *state*, optionally switching representation.

    Non-default values are carried over so a switch link keeps the layout and
    dotfile choices the reader already made. The default values stay off the
    URL, which is what keeps the everyday address short.
    """
    chosen = view if view is not None else state.view
    return build_url(
        rel,
        view=chosen if chosen != DEFAULT_VIEW else None,
        layout=state.layout if state.layout != DEFAULT_LAYOUT else None,
        hidden=state.hidden if state.hidden != DEFAULT_HIDDEN else None,
        vpath=state.vpath or None,
    )
