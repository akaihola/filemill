---
depends-on: []
---

# Fix the favicon 404 and `renderPage is not a function` error

## Original report and requirements

GET https://gogo.crane-boa.ts.net:8445/favicon.ico

  ```
  [HTTP/2 404  6ms]
  Uncaught (in promise) TypeError: renderPage is not a function
      applyPath https://gogo.crane-boa.ts.net:8445/ui/core/deeplink.js:123
      mountServer https://gogo.crane-boa.ts.net:8445/ui/adapters/app-http.js:117
      async* https://gogo.crane-boa.ts.net:8445/ui/adapters/app-http.js:201
  deeplink.js:123:5
  ```
