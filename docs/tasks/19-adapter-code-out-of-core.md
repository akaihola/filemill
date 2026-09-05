---
depends-on: [17]
---

# Move adapter code out of ui/core/

## Goal

`ui/core/` has no code that only one edition uses. Roadmap phase 3, step 5.

## Steps

1. Move `ui/core/jsonl.js` to `ui/adapters/vfs-json.js`. Fix the imports.
2. Move the welcome screen and the "Open Folder" markup from
   `ui/core/shell.js` to `ui/adapters/app-fsa.js`.
3. Move the local badge and the "leave local" control from `shell.js` to
   `ui/adapters/app-http.js`.
4. Move `offerRichToggle` from `ui/core/settings.js` to
   `ui/adapters/preview-rich.js`.
5. Run the grep in "Done when". For each hit, move the code to the adapter
   that needs it.

## Done when

- `grep -n "vpath\|showDirectoryPicker\|PreviewLocal\|API\b" ui/core/` prints
  nothing.
- `static/build-index.py --check` passes.
- All static tests and server tests pass.

## Scope

`ui/core/{jsonl.js,shell.js,settings.js}` and `ui/adapters/`.
