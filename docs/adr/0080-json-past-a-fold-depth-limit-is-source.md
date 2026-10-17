# ADR 0080: JSON past a fold depth limit is source

Date: 2026-10-17. Issue: [30].

## Context

The JSON preview folds arrays and objects with a recursive renderer. Deep
JSON was shown as source only after the recursion exhausted the engine's
stack, and the browsing preview first re-serialised the value with
`JSON.stringify`, which recursed the same way. V8 gives up quickly.
JavaScriptCore, in the native shell and Safari, recursed far deeper. A
200,000-deep document cost 3.4 s per preview render in WebKit against
0.16 s in Chromium, and every render rebuilt the preview (finding A9).

## Decision

`JSON_FOLD_DEPTH` in `ui/core/limits.js` is 1,000 levels. An iterative walk,
which stops at the limit, decides before folding or re-serialising. JSON
deeper than the limit is shown as source in every engine.

## Consequences

The 200,000-deep fixture renders in under 50 ms in both engines. JSON nested
between 1,001 levels and an engine's stack limit, which used to fold, now
shows as source. Browsing such a document as columns is unchanged.

[30]: ../tasks/30-webview-shell.md
