---
depends-on: [11, 12]
---

# Convert the shared UI to ES modules

## Goal

Every file in `ui/core/` and `ui/adapters/` uses `import` and `export`. Each
page loads one entry module. The bundle still works. Roadmap phase 3, steps
1 to 3.

## Steps

1. In each file in `ui/core/` and `ui/adapters/`, add `export` to each
   top-level function or constant that another file uses. Add `import`
   lines for each name the file uses from another file. Do not change logic.
2. Create `ui/entry-static.js` and `ui/entry-server.js`. Each one imports
   the adapters of its edition and calls the boot code that the old script
   list ran last.
3. In `static/index-dev.html`, replace the list of `<script>` tags with one
   `<script type="module" src="../ui/entry-static.js">`.
4. In `server/src/filemill/app.py`, replace the script list in the shell
   with one `<script type="module">` for `entry-server.js`.
5. In `static/build-index.py`, replace the concatenation with this: read the
   module graph from the entry file, order the files so each file comes after
   its imports, remove `import` and `export` keywords, and write the result
   in one `<script type="module">`. Keep the `--check` mode.
6. Run `cd static && ./build-index.py` and commit `index.html`.

## Done when

- `grep -L "^import\|^export" ui/core/*.js ui/adapters/*.js` prints nothing.
- `static/build-index.py --check` passes.
- `static/test-ui.py --dev`, `static/test-ui.py` and `cd server && uv run pytest` pass.

## Scope

`ui/`, `static/index-dev.html`, `static/build-index.py`, `app.py`.
