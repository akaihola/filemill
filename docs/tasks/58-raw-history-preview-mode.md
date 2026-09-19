---
depends-on: []
---

# Preserve preview mode in file URLs so Back from Raw restores the finder

## Original report and requirements

Bug: After navigating from a directory url without query parameters (e.g.
`/path/to/dir`) to a file (e.g. `file1.md`), and then another file (e.g. `file2.md`),
and then opening file2 using the `Raw` button, and navigating back using the browser's
back button, in some situations the file manager view isn't displayed. Instead, the
raw view of file1 is shown. Navigating to files needs to always include the
`?filemill=render` or `?filemill=highlight` query parameter (whichever mode was last
active) to prevent this behavior.
