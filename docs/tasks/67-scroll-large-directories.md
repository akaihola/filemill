---
depends-on: []
---

# Scroll large directories without pagination

## Original report and requirements

Large directories now partition their contents into multiple lists that the user
can browse using a `< Page N of NN >` control. This is not acceptable. The vertical
scrollbar should be used to navigate through the directory contents. Task
0b1a0f79-4a08-4b1e-a820-27242fdda812 tried to virtualize the directory contents but
failed (or was reverted with another task). Use Fable Medium to solve this. Make the
code elegant and efficient. Use a 3rd party library to virtualize the directory
contents if that helps.
