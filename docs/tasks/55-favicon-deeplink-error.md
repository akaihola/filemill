---
depends-on: []
---

# Fix the favicon 404 and `renderPage is not a function` error

## Original report and requirements

GET https://filemill.example/favicon.ico

  ```
  [HTTP/2 404  6ms]
  Uncaught (in promise) TypeError: renderPage is not a function
      applyPath https://filemill.example/ui/core/deeplink.js:123
      mountServer https://filemill.example/ui/adapters/app-http.js:117
      async* https://filemill.example/ui/adapters/app-http.js:201
  deeplink.js:123:5
  ```
