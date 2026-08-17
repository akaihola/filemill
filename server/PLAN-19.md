# Gogo dashboard integration — the URL and view contract

**Status:** implemented on `feature/proactive-pykofinder-tkz`. This document was
a plan; it is now a record. The plan text is preserved under "What the plan
said" so the differences stay readable, because the differences are the useful
part.

## What changes for the person using the dashboard

Today Filemill and the gogo dashboard are two places. You read a note in one
and you look at your services in the other, and moving between them means
switching tabs and losing your position.

After this change, a document can be *in* the dashboard. The dashboard asks
Filemill for `/docs/readme.md?pykofinder-view=rendered&layout=no-columns` and
gets back the rendered note with no column rail and no breadcrumb, so it drops
into a dashboard pane without two sets of navigation fighting each other.

The link you paste to a colleague is the useful part. It is the file's own path:

    https://gogo.example/docs/readme.md

They open it and get the file. If they want to read it rather than download it,
they add one parameter, and if they want the finder around it they change one
more. Same address, three different things:

| What you want | What you type |
| --- | --- |
| the file itself | `/docs/readme.md` |
| it rendered, in the finder | `/docs/readme.md?pykofinder-view=rendered` |
| it rendered, alone, for embedding | `/docs/readme.md?pykofinder-view=rendered&layout=no-columns` |
| its source, coloured | `/docs/readme.md?pykofinder-view=highlighted` |

There is one address to remember and one thing to add to it. Nobody has to know
that `/f/` means the finder and `/w/` means the web view.

## What changes technically, and why one path beats one path per view

A **resource** is the thing. A **representation** is one way of sending it. A
Markdown file is one resource; its bytes, its rendered HTML, and its
syntax-highlighted source are three representations of that one thing.

The old design gave each representation its own path:

    /w/menu/docs/readme.md      the bytes
    /f/menu/docs/readme.md      the finder, deep-linked
    /raw?path=/home/antti/menu/docs/readme.md   the bytes again

Three costs came with that, and all three are gone now.

**One: the mount name.** `/w/menu/…` and `/f/menu/…` both carry a `menu` segment
that names the configured root. A reader has to know it, and it changes when the
root changes. In the new form the root is implied, because the path is *relative*
to it. `/docs/readme.md` says what it means.

**Two: relative links inside documents broke.** This is the concrete one. A note
at `/f/menu/docs/note.md` containing `![](photo.png)` made the browser request
`/f/menu/docs/photo.png` — which served the finder shell, not the image. Under
the new contract the note is at `/docs/note.md`, the browser asks for
`/docs/photo.png`, and that is the image. The contract fixed a real bug by
*removing* a special case. That is usually the sign a design is right.

**Three: switching views meant rewriting the path.** With a path per view, a
"show me the source" button has to know how to translate `/w/menu/x` into
`/f/menu/x`. With one path it appends a parameter and leaves the path alone, so
the switch controls are one loop over three view names rather than three
hand-written translations. That is why they are reciprocal by construction here.

For embedding specifically, the win is that **the dashboard does not have to
understand Filemill's URL scheme.** It has a path and it adds parameters. A
router that forwards or rewrites a request forwards the path and preserves three
query values; it never has to reconstruct an address.

Absolute filesystem paths never appear in the route. `_resolve_safe()` still sees
every path, and the query never takes part in that decision — see "The safety
boundary" below.

## The contract

| Parameter | Values | Default |
| --- | --- | --- |
| `pykofinder-view` | `raw`, `rendered`, `highlighted` | `raw` |
| `layout` | `full-columns`, `compressed-columns`, `no-columns` | `full-columns` |
| `hidden` | `hide`, `show` | `hide` |
| `vpath` | a path inside a virtual filesystem | empty |

`raw` is the default because the bare path has to serve bytes: `/site/main.css`
must arrive as `text/css`, not as a preview of itself.

Rules, all tested in `tests/test_urls.py`:

- Missing → the default.
- Unrecognised → the default, and the requested file path never changes.
- Repeated → the last occurrence wins, so a router that appends a parameter wins.
- Values are encoded exactly once; HTML escaping happens at the output boundary.

## What landed

**`src/filemill/urls.py`** (new). The vocabulary, `parse_state()`,
`build_url()`, `url_for_state()`. One parser and one builder, so the query
grammar is stated in one file. 49 tests.

**`src/filemill/app.py`.** The `/{path:path}` resource route; `_rel_url_path()`;
`_resource_target()`; `_view_switch_html()`; `_representation_html()`;
`_document_page()`. `_finder_fragment()` lifted out of `restore()` with a preview
override, and `_head_tags()` lifted out of `_shell_html()`, so the deep link, the
standalone page, and the embedded page build from the same two functions.
`_reorder_routes()` rewritten to state route precedence in four bands.

**`src/filemill/preview.py`.** `render_source()` beside `render_preview()`,
sharing `_highlight_source()` and `_raw_text()`. `render_preview(path, state=None)`
threads the request state to the Markdown renderer only.

**`src/filemill/rendering.py`.** `_href_for_file()` emits root-relative URLs;
Markdown and wikilink hrefs carry the reader's `layout` and `hidden`.

**`src/filemill/styles.py`.** `initDotfilesToggle()` reads `data-hidden`, so an
explicit `?hidden=` outranks the stored preference.

**Tests.** `test_urls.py` (49), `test_resource_routes.py` (47),
`test_resource_safety.py` (229).

### Standalone and embedded share one code path

They differ by two attributes on `<body>` and nothing else. `compressed-columns`
sets the `zoomed` class the ⛶ button already toggles; `hidden=show` sets the
`show-dotfiles` class the `.*` button already toggles. There is no second
template and no embedded-mode branch in a handler.

One divergence, commented at the branch that causes it: a node inside a virtual
filesystem (`/sample.db/users/42`) has no bytes of its own, so `raw` has nothing
to serve there and `rendered` becomes the default. It diverges because there are
no bytes, not because embedding is different.

## The safety boundary

`_resolve_safe()` is unchanged. The new query dimension does not reach it.

`tests/test_resource_safety.py` drives 10 escape paths through 4 view cases and
4 layout cases and asserts, for every one, on **what `_resolve_safe` returned** —
either `None` or a path inside an allowed zone — rather than on the request
string. A spy wrapping the module attribute records every call, including those
made through `api.split_vfs`.

That distinction earned its keep. httpx collapses a literal `..` before sending,
so `/../outside/secret.txt` arrives at the server as `/outside/secret.txt`; a
test that checked only what it sent would have been testing the client. The
percent-encoded forms (`%2e%2e`, `..%2F`) survive and are what actually reaches
the handler.

The strongest test compares the recorded `(argument, result)` sequences across
all 20 view/layout combinations for the same path. They are identical, which
means the query *cannot* participate in containment rather than merely not
having done so.

Covered: percent-encoded and double-encoded traversal, a nested symlink escaping
ROOT, a directory symlink escaping ROOT, a symlink escaping a bookmark zone, the
ROOT-prefix sibling (`menu` vs `menuEVIL`), an absolute path offered as a
relative one, backslashes, `....//`. Zone 2 is intact: a direct symlink child of
ROOT is still browsable. A denied path and a missing one return byte-identical
responses.

**Validated by mutation, not by assertion alone.** Deleting the zone-1
containment check from `_resolve_safe` fails 169 of the 229. The 60 that still
pass are the absolute-path cases, which `api.rel_to_abs` rejects before
`_resolve_safe` is reached — defence in depth, now on the record.

## The old URLs still work

Every route the plan listed still answers, and every existing test for them still
passes untouched: mount URLs, legacy absolute-path query URLs (`/f/?path=…`),
safety zones and symlinks, Markdown, syntax highlighting, the raw fallback, the
preview routes, HTMX fragments, and deep-link restoration.

**Four test assertions changed, and no user-visible URL broke.** The four were
`test_href_for_md_file_uses_canonical_finder_path`, its symlink-child variant,
`test_md_link_relative_normalized`, and `test_wikilink_resolved_gets_proper_href`.
All four assert on links Filemill *generates*, not on URLs it *accepts*:

    was  /f/menu/docs/guide.md
    now  /docs/guide.md?pykofinder-view=rendered

A reader with an old bookmark sees exactly what they saw before, because `/f/`
and `/w/` are still routed. Only newly rendered documents link differently.

One behaviour change worth naming: `/notes/todo.txt` used to be served by
FastHTML's static catch-all from the **working directory**; it now serves
`ROOT/notes/todo.txt`. That is the point of the change, and it is the safer of
the two.

## What the plan got wrong

**It contradicted itself about `raw`.** §1 lists a default static representation
*and* a `pykofinder-view=raw` one. §5 then says both "the raw view has a
reciprocal link to the matching rendered or highlighted view" and "direct raw
responses remain bytes with correct Content-Type" — a bytes response cannot carry
a link. Resolved by making `raw` the default and the bare path identical to it,
so there are three views rather than four, and the reciprocal links live on the
rendered and highlighted views, which are HTML and can hold them.

**It did not say what `layout` does to a representation.** Reading §1 and §3
together, `layout` selects how much chrome wraps the representation, which is
what makes the contract useful for embedding. That reading is now the
implementation and should have been in the plan explicitly.

**It said "if they are still needed by existing callers" about `/w/` and `/f/`.**
They are, and the answer was knowable in advance by reading the tests.

**It asked for switch controls "emitted with rendered Markdown and
syntax-highlighted source" without saying where.** They are emitted by the new
resource route. The HTMX preview pane reached through `/click` keeps its existing
markup, because changing it would alter fragments that existing tests pin for
reasons unrelated to this contract.

**It listed `README.md`, `CONTRIBUTING.md`, `ISSUES.md`, `TASKS.md` as planned
changes.** Not done — see below.

## What remains

1. **Raw HTML in Markdown reaches the browser.** `MarkdownIt("commonmark")` sets
   `html: True`, so a `<script>` written into a Markdown file under ROOT runs.
   This predates PLAN-19 and no test covered it;
   `test_rendered_view_passes_raw_html_through_unescaped` now pins the current
   behaviour. **This change raises the stakes**: a rendered page is served
   same-origin with the dashboard that embeds it, so a Markdown file in the
   served tree can run script in the dashboard's origin. Fixing it means either
   `html: False` or a sanitiser, and either alters rendering for every existing
   document. That is Antti's call, not a side effect of a routing change.
2. **`/` still redirects to `/f/`.** ROOT's own root-relative address should be
   `/`, but `test_root_redirects_to_finder` pins the redirect and the `/n/`
   cutover described in `PLAN-20-shared-frontend.md` will move it anyway.
3. **`_resolve_safe()` decodes a path that is already decoded.** Starlette
   decodes path and query before the handler, and `_resolve_safe` calls
   `urlunquote` again. A file literally named `a%20b.txt` is therefore reachable
   as `a b.txt`. Containment is unaffected — it is checked on the resolved path,
   and `tests/test_resource_safety.py` covers the double-encoded case — so this
   picks the wrong file rather than escaping. `test_url_encoded_path_is_decoded`
   pins the current behaviour, so fixing it is its own change.
4. **`layout` and `hidden` are not honoured on `/f/` and `/w/`.** The legacy
   routes ignore them. Low value while `/f/` is legacy.
5. **Documentation.** `README.md`, `CONTRIBUTING.md`, `ISSUES.md` and `TASKS.md`
   do not yet describe the contract.
6. **The gogo router contract is implemented but not written down** anywhere the
   dashboard's authors would find it. §3 of the old plan is the nearest thing.

## What I would design differently

`compressed-columns` is the weakest of the three layout values. It reuses the
`zoomed` class, which hides the columns entirely rather than folding them to
spines — the shared UI in `ui/core/layout.js` has a real fold dial with exactly
that behaviour, and the HTMX shell has nothing like it. The name promises
something the HTMX UI cannot yet deliver. I would either rename it to match what
it does today or hold it back until the `/n/` cutover makes the fold dial
available. It is honest about being a placeholder in the code comment, but a URL
contract is a promise to users, and this part of it over-promises.

I would also drop `hidden` from the contract. It is a display preference, it is
already persisted in `localStorage`, and it is the one parameter that does not
change what the URL *identifies* — unlike `pykofinder-view` and `layout`, which
select a representation and a presentation of it. Three parameters where two
would do makes the contract harder to teach for no gain.

---

## What the plan said

The original plan text, preserved for comparison.

### Scope

Adapt Filemill's FastHTML/ASGI app for embedding in the gogo dashboard while
preserving standalone behavior. The URL path is always the file path relative to
the configured root. Query parameters select the representation and layout; they
do not carry an absolute filesystem path.

### Current integration points

- `src/filemill/app.py`: `/click`, `/raw`, `/w/{path:path}`, `/f/`,
  `/f/{path:path}`, `_resolve_safe()`, mount URL helpers, shell/deep-navigation
  JavaScript.
- `src/filemill/columns.py`: Finder links, HTMX targets, `data-finder-url`,
  breadcrumb.
- `src/filemill/preview.py`: Markdown dispatch, Pygments code dispatch, UTF-8
  raw fallback, PDF/image `/raw` URLs.
- `src/filemill/rendering.py`: Markdown links/wikilinks and current `/f/`,
  `/w/`, or `/raw?path=` URL generation.
- Existing tests cover mount URLs, legacy absolute-path query URLs,
  safety zones/symlinks, Markdown, syntax highlighting, raw fallback, preview
  routes, HTMX fragments, and deep-link restoration.

### Required behavior

1. **URL and query contract.** Use the same path for all representations.
   `/docs/readme.md` serves the static file by default;
   `?pykofinder-view=rendered|highlighted|raw` selects the others; `layout=` and
   `hidden=` select the Finder layout and dotfile visibility. Missing or invalid
   query values use documented defaults and never change the requested file path.
   Use one shared query parser and URL builder. Encode query values once and
   apply HTML escaping at output boundaries.
2. **Relative file paths.** Serve paths relative to the configured root without
   requiring `/w/<mount>/` or `/f/<mount>/` prefixes. Keep named-mount routes
   only as legacy compatibility routes, if they are still needed by existing
   callers. Never accept an absolute filesystem path from the client as the
   canonical route format.
3. **Raw-file/router integration.** Router-facing static/raw requests are
   GET-only and return a file response with detected media type. Rendered
   endpoints return HTML fragments or the full shell as specified; raw bytes must
   not fall through FastHTML's catch-all. Preserve `pykofinder-view`, `layout`,
   and `hidden` when the dashboard router forwards or rewrites requests. Keep
   route ordering explicit. Preserve existing `/w/` CORS behavior only for
   web-static requests.
4. **Rendered Markdown and syntax-highlighted views.** Markdown uses
   `pykofinder-view=rendered`; source/code uses `highlighted`; `raw` returns the
   source. Keep relative links, wikilinks, linkify, Mermaid, escaping, size
   limits, and encoding fallbacks. Reuse existing Markdown/Pygments pipelines.
5. **Raw-file switch link contract.** A visible switch link has a stable class or
   data attribute and links to the same path with each view value. It preserves
   `layout`, `hidden`, and applicable `vpath`. Tests assert exact path/query
   semantics, not merely that an href contains `/raw`.

### Safety and query rules

All filesystem inputs pass `_resolve_safe()` after URL decoding and
normalization; containment is checked on resolved paths. Preserve the existing
allowed zones. Deny traversal, unknown mounts, outside paths, broken links,
directories on file-only endpoints, and missing paths. Define deterministic
behavior for absent, empty, repeated, malformed, and encoded values, and test it.
Escape path-derived HTML values and encode each URL query value exactly once.
Return 404 for denied paths without revealing whether an outside target exists.
