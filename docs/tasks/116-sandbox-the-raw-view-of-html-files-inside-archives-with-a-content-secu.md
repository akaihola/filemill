Follow-up from [114], whose worker left this as a decision.

Since [114], the preview of an `.html` file inside an archive runs in a sandboxed iframe. Its Raw link still opens the file as an ordinary page on Filemill's own origin, so a script in it can reach the Filemill session. `SECURITY.md` now documents this as the same trust boundary as an HTML file at the server root.

Proposal: send `Content-Security-Policy: sandbox` on `/api/raw` responses for HTML members of archives (and decide whether HTML files on disk get the same). Scripts in such pages would stop working in the Raw view.

Decision needed: whether Raw should stay a faithful, scriptable view or become inert like the preview.
