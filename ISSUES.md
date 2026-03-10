# Issues

Each issue has an explicit **Status** field: `open`, `in-progress`, or `closed`.

When closing an issue, set `**Status:** closed` and add a `**Closed:** YYYY-MM-DD` date.
**Closed issues are pruned from this file immediately upon closing** – their full text
lives in git history and can be retrieved with the commands below.

---

## Finding past issues in git

Closed issue blocks were removed from this file to keep the agent context lean.
The full text of every issue is preserved in git history.

```bash
# Show every commit that touched ISSUES.md (one line each)
git log --oneline -- ISSUES.md

# Search commit messages for an issue number or keyword
git log --oneline --all --grep="#24" -- ISSUES.md
git log --oneline --all --grep="keyboard" -- ISSUES.md

# Show the full diff for a specific commit (replace <hash> with the commit hash)
git show <hash> -- ISSUES.md

# Show the state of ISSUES.md as it was at a given commit
git show <hash>:ISSUES.md | less

# Grep across ALL historical versions of ISSUES.md for a keyword
git log -p -- ISSUES.md | grep -A 20 "ArrowLeft must update"

# Find the commit that removed a specific issue block
git log -p -- ISSUES.md | grep -B 5 "^-## #34"
```

---

## #43 – Mobile preview fills 100 % width; rightmost column peek needed as scroll hint

**Type:** UX
**Status:** open

After #42, `#preview` is given `min-width: 90vw` on narrow viewports, but in practice it expands to fill the full available width, leaving no visible edge of the directory column to signal that the user can scroll left. The peek – a few pixels of the rightmost column visible on the right – is the essential affordance that makes the swipe gesture discoverable.

**Planned fix / implementation sketch:**

- Change the mobile media-query rule in `styles.py` from `min-width: 90vw` to a fixed `width: 90vw` (with `flex-shrink: 0` and `max-width: 90vw`) so the preview cannot grow past 90 % of the viewport regardless of content width.
- Ensure `#finder` retains `overflow-x: auto` so the remaining 10 % column peek is reachable by scrolling.
- Update the corresponding tests in `tests/test_rendering.py` that assert the mobile CSS values.

---

## #44 – ripgrep-based full-text search bar in `<nav>`

**Type:** feature
**Status:** open

There is no way to search file contents from the UI; users must know where a file lives to navigate to it. A search bar in the `<nav>` breadcrumb area should run `rg` against the ROOT directory and display matches as a results column, letting the user click a hit to open its preview.

**Planned fix / implementation sketch:**

- Add an `<input id="search-bar">` element to the breadcrumb in `columns.py` (`make_breadcrumb`), positioned after the existing buttons.
- Add a `/search?q=<query>` route in `app.py` that shells out to `rg --json -l <query> <ROOT>` (list-only mode), parses the JSON output, and returns an HTMX-swappable column `<div>` containing one `<li>` per matching file path (relative to ROOT), reusing the existing column CSS.
- Clicking a result `<li>` should trigger the normal `/click` flow so the file is previewed and the breadcrumb updates.
- Wire the `<input>` with `hx-get="/search"` `hx-trigger="input changed delay:300ms"` `hx-target="#search-results"` and inject an empty `<div id="search-results">` into the page.
- Add CSS for the search bar in `styles.py` (fits flush with the existing nav buttons).
- Guard against `rg` being absent (fall back to `pathlib` `rglob` + `Path.read_text` substring match with a 256 KB cap per file).
- Tests in `tests/test_app.py`: assert the `/search` route returns matching filenames; assert it returns an empty column for a query with no matches; assert it is safe (no path escape via query string).

---

## Open issues

_No open issues at this time._
