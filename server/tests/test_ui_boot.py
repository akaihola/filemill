"""Keep the ordered core boot contract in one place for all three hosts."""

import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
UI = ROOT / "ui"


def test_hosts_share_the_ordered_core_initializer():
    def compact(source):
        return re.sub(r"\s+", "", source).replace(",}", "}")

    boot = compact((UI / "core/boot.js").read_text())
    calls = [
        "initSort();",
        "setSortKids(sortKids);",
        "setActions({ choose, copyPath, refreshColumn, renderCrumbs, saySt, unfoldTo });",
        "setSortActions({ render });",
        "setDeepLinkActions({ render, colCache });",
        "initLayout(render);",
        "initSettings();",
    ]
    calls = [compact(call) for call in calls]
    positions = [boot.index(call) for call in calls]
    assert all(boot.count(call) == 1 for call in calls)
    assert positions == sorted(positions)
    for host in ("http", "fsa", "native"):
        app = (UI / f"adapters/app-{host}.js").read_text()
        assert 'import { initCore } from "../core/boot.js";' in app
        assert app.count("initCore();") == 1
        assert all(call not in compact(app) for call in calls)
        edition = {"http": "server", "fsa": "static", "native": "native"}[host]
        entry = (UI / f"entry-{edition}.js").read_text()
        assert entry.index('import "./core/shell.js";') < entry.index(
            f'import "./adapters/app-{host}.js";'
        )
