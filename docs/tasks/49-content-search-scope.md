---
depends-on: []
---

# Fix content search errors and restrict search to the focused directory tree

## Original report and requirements

Task e02c3b0b-21a0-4be0-bcdd-bce0d99206f4 didn't fix file content search. It
either returns `Search error: search result too large` or `No matches`. Make sure
search only covers the current focused directory and its subdirectories recursively.
Do red-green testing: first reproduce, then investigate, plan, implement, and test.
Iterate until fixed.
