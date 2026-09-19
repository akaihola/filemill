---
depends-on: []
---

# Fix content searches failing with `Search timed out`

## Original report and requirements

Using the `Search file contents` input always causes the error
`Search error: Search timed out` to display. JavaScript console:
`XHR GET https://gogo.crane-boa.ts.net:8445/api/search?q=development [HTTP/2 503  2020ms]`.
Originally implemented in task 456736f9-7242-40d0-894d-d5e1db50c0de.
