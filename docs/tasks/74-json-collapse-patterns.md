---
depends-on: []
---

# Remember collapse patterns across JSON previews

## Original report and requirements

When object hierarchies are collapsed by the user in a JSON object preview,
remember the paths of collapsed objects (built all the way from the root), and also
collapse the same objects when viewing similar objects anywhere at the same depth. For
example, if I'm viewing `a.b.foo` and collapse `a.b.foo.c.bar`, then when I view any
`*.*.*` or `*.*.*.c` path, `*.*.*.c.bar` should be collapsed.
