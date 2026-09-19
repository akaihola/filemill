---
depends-on: []
---

# Choose unique CSV row keys and keep duplicate values independently selectable

## Original report and requirements

In the CSV hierarchical preview, there are two problems. The first column is
always selected as the key. Instead, a unique column should be selected similar to how
it's done in JSON. Also, currently if the first column is not unique, all identical
values are selected together. This should be fixed for the case when no unique column
is available. Original implementation in task 8038a32c-570b-45ed-b3ca-5834b3b8dc18.
