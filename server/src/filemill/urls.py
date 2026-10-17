"""The URL contract: one path per file, query parameters pick the representation.

A file has one address. ``/docs/readme.md`` names the resource; the query says
which representation of it you want, so a link pasted into chat opens the same
document with the finder around it.

Two query groups, each with one documented default:

    filemill = raw | render | highlight            (default: raw)
    layout   = full-columns | compressed-columns   (default: full-columns)

``raw`` is the default because the bare path has to serve the bytes: a stylesheet
at ``/site/main.css`` must arrive as ``text/css``, not as a preview of one.

Rules that hold for every value:

- A missing value uses the default.
- ``?filemill``, ``?filemill=``, and ``?f`` mean ``?filemill=render``.
- An unrecognised value uses the default and never changes the requested path.
- A repeated value uses the last occurrence, then the two rules above.
- No query value reaches the filesystem. ``_resolve_safe()`` sees the path and
  nothing else, so no combination of view and layout can widen what it allows.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from urllib.parse import quote as urlquote
from urllib.parse import urlencode

VIEW_PARAM = "filemill"
VIEW_SHORT_PARAM = "f"
LAYOUT_PARAM = "layout"
VPATH_PARAM = "vpath"

VIEW_RAW = "raw"
VIEW_RENDER = "render"
VIEW_HIGHLIGHT = "highlight"
VIEWS: tuple[str, ...] = (VIEW_RAW, VIEW_RENDER, VIEW_HIGHLIGHT)

LAYOUT_FULL = "full-columns"
LAYOUT_COMPRESSED = "compressed-columns"
LAYOUTS: tuple[str, ...] = (LAYOUT_FULL, LAYOUT_COMPRESSED)

DEFAULT_VIEW = VIEW_RAW
DEFAULT_LAYOUT = LAYOUT_FULL

# Human labels for the switch controls, in the order they are rendered.
VIEW_LABELS: tuple[tuple[str, str], ...] = (
    (VIEW_RENDER, "Rendered"),
    (VIEW_HIGHLIGHT, "Source"),
    (VIEW_RAW, "Raw"),
)


@dataclass(frozen=True)
class ViewState:
    """The two query groups, already validated, plus any virtual path."""

    view: str = DEFAULT_VIEW
    layout: str = DEFAULT_LAYOUT
    vpath: str = ""

    def with_view(self, view: str) -> ViewState:
        """Return the same state pointed at another representation."""
        return replace(self, view=view if view in VIEWS else DEFAULT_VIEW)


def _last(params, key: str) -> str | None:
    """Return the last occurrence of *key*, or None.

    Starlette's ``QueryParams`` is a multidict, so ``?layout=a&layout=b`` has two
    values. Taking the last one makes a rewriting router's appended parameter
    win when a reverse proxy forwards a request.
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
    """Read the two query groups and the virtual path out of a query mapping.

    *params* is anything with ``.get()`` — a Starlette ``QueryParams`` or a plain
    dict. Every field comes back valid, so callers never re-check.
    """
    vpath = _last(params, VPATH_PARAM) or ""
    view = _last(params, VIEW_PARAM)
    if view is None and _last(params, VIEW_SHORT_PARAM) == "":
        view = VIEW_RENDER
    return ViewState(
        view=VIEW_RENDER if view == "" else _one_of(view, VIEWS, DEFAULT_VIEW),
        layout=_one_of(_last(params, LAYOUT_PARAM), LAYOUTS, DEFAULT_LAYOUT),
        vpath=vpath.strip("/"),
    )


def build_url(
    rel: str,
    *,
    view: str | None = None,
    layout: str | None = None,
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
    if vpath:
        pairs.append((VPATH_PARAM, vpath.strip("/")))
    return f"{path}?{urlencode(pairs)}" if pairs else path
