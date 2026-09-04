---
depends-on: []
---

# Hierarchical nested view for JSON

Implement a hierarchical nested view for `.json` files and variants like
`.jsonc` quite similarly to SQLite and JSONL files.

Lists of objects are actually rendered identically to a JSONL file. Lists of
long or multi-line strings are similar to folders of files/folders, truncating
long strings. The preview of a string is a highlighted render of the string
according to a "file type" detected based on the string content. Lists of mixed
types are rendered as truncated values with previewing available. If there are
no long/multiline strings or objects in the list, just a 1-column table preview
is shown.

Objects are rendered as a column of keys with previewing of values in the
preview area, except when no long/multiline strings nor objects exist as values,
a 2-column table is shown in the preview area.
