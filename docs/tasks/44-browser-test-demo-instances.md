---
depends-on: []
---

# Document demo instances matching each browser test setup

## Original report and requirements

For user testing, document how to run instances of Filemill that are
as close as possible to the browser test setup you have in the test suite. Put each
different browser test setup in its own HTTP port, and link them in
the development dashboard. We will separately set up systemd user services for each
different browser test setup.

## Dashboard verification, 2026-10-21

[The verification task] confirmed the three links in the original host's
dashboard source. All three are absent from the current host's dashboard
source and installed [home page]. This is a gap in the current dashboard;
the earlier claim that the original integration was unverified can now be
narrowed to destination availability. This task remains unaccepted.

### Evidence and scope

- **Original target.** Filemill commit `a606ae0f` preserves the original
  request's account, host and home-page filename. Commit `bdaac0d6` replaced
  that filename with "the development dashboard". The original instructions
  in `df007a91` assigned ports 8452, 8453 and 8454 to the three fixture roots.
  Recover these records with:

  ```bash
  git show a606ae0f:docs/tasks/44-browser-test-demo-instances.md
  git show df007a91 -- server/README.md
  ```

- **Dashboard sources.** Checked the infrastructure checkout at
  `2a772aad0a854ebe09dbfce991de126869f3be02`. Its original-host dashboard
  contains three distinct anchor cards with the expected fixture labels and
  ports. [The current dashboard source], lines 137–168, has ordinary Filemill,
  public and workspace links, but no browser-test cards. The checked source
  files had no local changes.
- **Installation.** [The dashboard installation rule], lines 293–302,
  selects the dashboard source by host name and installs it as the home-page
  index. The installed [home page] is a symlink; its bytes match the current
  source exactly. The page's script only filters existing cards. It does not
  discover servers or read the Filemill instructions.
- **Isolated result.** Copied both source pages and the installed page to
  disposable HTML fixtures. Python's standard-library `HTMLParser` found
  all three demo cards in the original source and zero in each current copy.
  The discovery check exited **1**, reproducing the current omission. The
  original source supplied a positive control. No browser or destination
  request was needed.

| Fixture | Original dashboard port | Current example port | Current dashboard |
| --- | --- | --- | --- |
| Browser UI | 8452 | 8001 | Missing |
| Keyboard desktop | 8453 | 8002 | Missing |
| Keyboard mobile | 8454 | 8003 | Missing |

The current ports come from [the manual instance instructions] and are
explicitly examples. They are not dashboard registrations. The original
ports agree with the instructions at `df007a91`; the difference alone is
not a defect. [The current host's service inventory] assigns ports 8452–8454
to other applications, so a repair must check allocations before choosing
ports.

Snapshot SHA-256 values:

```text
original source: e1dd3bb85b70f61c4eb0fdf51816f23f4858c63a213b8362f7e03564e18755b1
current source:  3d5c34dfcc5695294653d2821dc56a3c9663cd49635229c8f5d9fcab993da921
installed page:  3d5c34dfcc5695294653d2821dc56a3c9663cd49635229c8f5d9fcab993da921
```

These are link-discovery results. They do not establish that the original
destinations still run, that the public demo serves these fixtures, or that
the manual fixtures match every current browser test. No running instance,
service, dashboard file or deployment was changed.

### Repeat the discovery check

Set `DASHBOARD_HTML` to a disposable copy of one dashboard, then run:

```bash
python3 - "$DASHBOARD_HTML" <<'PY'
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        keys = set(attrs.get("data-k", "").split())
        if (tag == "a" and "card" in attrs.get("class", "").split()
                and {"filemill", "browser", "tests"} <= keys):
            self.links.append((attrs.get("href", ""), keys))

cards = Cards()
cards.feed(Path(sys.argv[1]).read_text())
for keys in ({"shared", "ui"}, {"keyboard", "desktop"},
             {"keyboard", "mobile", "touch"}):
    links = [url for url, tags in cards.links if keys <= tags]
    print(sorted(keys), links)
    assert len(links) == 1, "Missing or ambiguous demo card"
ports = {urlsplit(url).port for url, _ in cards.links}
assert len(ports) == 3 and None not in ports, ports
PY
```

This checks the existing dashboard's card convention. A repair that changes
that convention must update the check and verify rendered discovery too.

### Draft repair issue

- **Title:** Restore browser-test demo discovery on the current dashboard.
- **Status:** Draft for the infrastructure tracker; not filed or implemented
  by this verification.
- **Problem:** The current dashboard omits the three fixture links that
  remain in the original host's source. Ordinary and public Filemill cards do
  not identify these setups.
- **File to change:** [The current dashboard source]. Keep its host-selected
  [installation rule] unless a test shows that rule needs a change.
- **Work:** Add clearly labelled Browser UI, Keyboard desktop and Keyboard
  mobile cards, with searchable keywords and distinct agreed endpoints.
  Record the endpoint-to-fixture mapping. Check port allocations; do not
  copy the original ports or the example ports without verification.
  Service provisioning stays separate, as the original request requires.
- **Acceptance:** Begin with a failing discovery check on the current page.
  Use isolated fixtures to verify the three links, service filtering and
  distinct destinations. Follow the links only to disposable test servers
  and confirm each fixture root. Keep ordinary and public links intact.
  Record unavailable services explicitly. Any deployment is separate work.

[the verification task]: 143-check-whether-the-demo-instances-show-up-in-the-development-dashboard.md
[home page]: http://hopeli/index.html?f
[the current dashboard source]: http://hopeli/repos/nixos-config/home-manager/dotfiles/hopeli-dashboard/index.html?f
[the dashboard installation rule]: http://hopeli/repos/nixos-config/home-manager/features/agent-workloads.nix?f
[installation rule]: http://hopeli/repos/nixos-config/home-manager/features/agent-workloads.nix?f
[the current host's service inventory]: http://hopeli/repos/nixos-config/docs/contributing/hopeli-agent-services.md?f
[the manual instance instructions]: ../../server/README.md#manual-browser-test-instances
