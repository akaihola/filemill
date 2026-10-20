# Separate internal requests from real file and folder paths

Source: [109](109-check-filemill-s-docs-and-adr-statuses-against-the-code-and-fix-what-d.md?f), question 6.
User review, 2026-10-20. Label: `steward`.

## Decision

Goal accepted by the user: internal web addresses must not hide real file or folder paths. The transport design remains proposed, not yet approved. This replaces the earlier comment-only correction.

## Work

1. Evaluate an explicit header, such as Filemill-Request: api, for fetch-based API calls. Dispatch marked requests before matching internal paths; unmarked requests must use normal file routing even when the path equals an endpoint. Do not use Accept: application/json or navigation mode as a complete identity test.

2. Cover all request types before choosing the design: /api/raw is also embedded in archive previews and returned as a Raw link; scripts, styles, fonts, icons, the manifest and worker load without arbitrary application headers. Give those requests an explicit representation/query contract or evaluate a separate application origin; do not leave /ui/, /icons/, /sw.js or /manifest.json collisions.

3. Compare a separate application/API host or port with the single-origin design. Separation can reserve no file paths, but adds origin, CORS, token, deployment and worker-scope requirements. A second API origin alone does not separate application assets left on the file origin.

4. For header dispatch, vary cacheable responses on the discriminator and update service-worker classification. Keep mutation authorization and containment checks; the routing header is not a credential.

5. Record the chosen design in an ADR with failing collision tests first. Coordinate with [129](129-remove-the-obsolete-w-and-n-url-routes.md?f); retain real w and n files after removing aliases.

## Acceptance

The design covers plain navigation, raw downloads, embedded resources, app assets, PWA startup and API calls for identically named filesystem fixtures. Browser and HTTP tests prove the chosen separation; no compatibility reservation silently hides a real path. Implementation waits for the design decision.

## Standards checked

- [Fetch request headers](https://fetch.spec.whatwg.org/#headers-class).
- [HTTP Vary](https://www.rfc-editor.org/rfc/rfc9110.html#name-vary).
- [HTML origins](https://html.spec.whatwg.org/multipage/browsers.html#origin) and [CORS](https://fetch.spec.whatwg.org/#cors-protocol).
