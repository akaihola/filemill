---
depends-on: []
---

# Return raw file bytes for URLs without query parameters

## Original report and requirements

Opening `https://filemill.example/<any path>` without query parameters
redirects to `https://filemill.example/` and spins `Reading...` for a very
long time (if not forever). It should instead return files raw with the correct
content type.
