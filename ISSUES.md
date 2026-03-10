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

## #40 – Web-mode bar missing when opening an HTML file via direct `/f/` URL

**Type:** bug
**Status:** open

When an HTML file is opened via a direct `/f/` URL (e.g. `http://gogo:8334/f/menu/paivi/mdtest.html`), the preview renders the source correctly but the `<div class=preview-webmode-bar>` "🌐 View as web page" link is absent. The bar appears correctly when the same file is reached by clicking through the column UI, indicating the preview route handles the two entry-points differently.

**Planned fix / implementation sketch:**

- Trace `preview.py` – find where `preview-webmode-bar` is injected and identify the condition that suppresses it on the direct-URL code path.
- Ensure the web-mode bar is always emitted for `.html` files regardless of how the preview is invoked (direct `/f/` URL or column click).
- Add a test in `tests/test_preview.py` that asserts the bar is present in the rendered output for an HTML file preview.

---

## #42 – Mobile preview pane too narrow; should fill >90 % of viewport with a column peek

**Type:** UX
**Status:** open

On narrow mobile viewports, `#preview` receives only a fraction of the screen width (observed at less than 50 %) because the fixed-width directory columns (default 220 px each) consume most of the horizontal space before `flex: 1` stretches the preview into whatever remains. The desired behaviour is that whenever a preview is active on a narrow screen, the preview pane takes ≥ 90 % of viewport width with the rightmost directory column peeking in on the right, both when a document is reached by clicking through the column UI and when navigating directly to a `/f/` URL.

**Planned fix / implementation sketch:**

- Add a `@media (max-width: 700px)` (or similar breakpoint) block in `styles.py` (`CSS` constant) that overrides `#preview` with `min-width: 90vw` (or `width: 90vw; flex-shrink: 0`) so the pane dominates the horizontal scroll area.
- Ensure `#finder` keeps `overflow-x: auto` (already set) so the user can still scroll left to reach the directory columns.
- Consider adding `scroll-snap-type: x mandatory` on `#finder` with `scroll-snap-align: start` on `.column` and `scroll-snap-align: end` on `#preview` for a native swipe feel.
- Verify the fix covers both entry points: interactive click (`/click` HTMX route) and deep-link restore (`/restore` + direct `/f/` URL).
- Add tests in `tests/test_rendering.py` or `tests/test_app.py` asserting the mobile-override CSS rule is present in the rendered page.

## Open issues

_No open issues at this time._
