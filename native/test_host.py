"""Native contract checks through the application's actual WebView."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from webdriver import application


def test_native_ports(tmp_path):
    (tmp_path / "hello.txt").write_text("native bytes")
    (tmp_path / "sub").mkdir()
    (tmp_path / "escape").symlink_to("/etc")
    with application(tmp_path) as page:
        assert page.evaluate("typeof FS.ensureLoaded") == "function"
        assert page.evaluate('path[0].kids.map(n => n.name).includes("hello.txt")')
        assert (
            page.evaluate(
                'async () => { const n = path[0].kids.find(n => n.name === "hello.txt"); return await (await FS.blob(n)).text(); }'
            )
            == "native bytes"
        )
        page.evaluate(
            'async () => { const n = path[0].kids.find(n => n.name === "hello.txt"); await FS.write(n, "changed"); }'
        )
        assert (tmp_path / "hello.txt").read_text() == "changed"
        (tmp_path / "new.txt").write_text("new")
        page.evaluate("refreshColumn(0)")
        page.wait('path[0].kids?.some(n => n.name === "new.txt")')
        assert page.evaluate(
            'async () => { try { await nativeCall("read", {path:"escape/passwd"}); return false; } catch { return true; } }'
        )
        assert page.evaluate(
            'async () => { try { await nativeCall("read", {path:"../outside"}); return false; } catch { return true; } }'
        )


def test_html_preview_cannot_reach_bridge(tmp_path):
    (tmp_path / "secret.txt").write_text("secret")
    (tmp_path / "attack.html").write_text("""<h1>Preview content</h1><script>
parent.__previewAttack = true;
parent.nativeCall('read', {path: 'secret.txt'}).then(x => parent.__stolen = x);
</script>""")
    with application(tmp_path) as page:
        page.evaluate('applyPath(["attack.html"])')
        page.wait('document.querySelector("iframe.pv-html")')
        page.wait('document.querySelector("iframe.pv-html").contentWindow !== null')
        assert page.evaluate(
            'document.querySelector("iframe.pv-html").hasAttribute("sandbox")'
        )
        assert page.evaluate("typeof window.__previewAttack") == "undefined"
        assert page.evaluate("typeof window.__stolen") == "undefined"


def test_failed_write_preserves_contents(tmp_path):
    file = tmp_path / "read-only.txt"
    file.write_text("keep these bytes")
    file.chmod(0o400)
    with application(tmp_path) as page:
        assert page.evaluate(
            'async () => { try { await nativeCall("write", {path:"read-only.txt", text:"lost"}); return false; } catch { return true; } }'
        )
    assert file.read_text() == "keep these bytes"


def test_router_preserves_view_and_root(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    with application(tmp_path) as page:
        page.evaluate(
            'async () => { ROUTER.write({path:["a.txt"]}, false); ROUTER.write({path:["b.txt"],view:"highlight"}, false); await nativeCall("root"); }'
        )
        page.wait('ROUTER.read().view === "highlight"')
        assert page.evaluate("ROUTER.read().root") == tmp_path.name


def test_untrusted_top_level_navigation_is_blocked(tmp_path):
    with application(tmp_path) as page:
        page.evaluate(
            "() => { const link = document.createElement('a'); link.href = 'data:text/html,<script>window.attacker=true</script>'; document.body.append(link); link.click(); return new Promise(resolve => setTimeout(resolve, 100)); }"
        )
        assert page.evaluate("typeof window.attacker") == "undefined"
        assert page.evaluate("location.protocol") == "filemill:"


def test_native_keyboard_reaches_renderer(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    with application(tmp_path) as page:
        page.evaluate(
            'window.__keys = []; addEventListener("keydown", e => __keys.push(e.key))'
        )
        page.call(
            "/actions",
            {
                "actions": [
                    {
                        "type": "key",
                        "id": "keyboard",
                        "actions": [
                            {"type": "keyDown", "value": "\ue015"},
                            {"type": "keyUp", "value": "\ue015"},
                        ],
                    }
                ]
            },
        )
        assert page.evaluate("__keys") == ["ArrowDown"]
        assert page.evaluate("sel[0]") == "a.txt"


def test_native_pointer_selects_target(tmp_path):
    for name in ["alpha", "beta", "gamma", "omega"]:
        (tmp_path / name).mkdir()
    with application(tmp_path) as page:
        element = page.call(
            "/execute/sync",
            {
                "script": "return document.querySelector('.row[title=\"omega\"]')",
                "args": [],
            },
        )
        page.call(
            "/element/" + element["element-6066-11e4-a52e-4f735466cecf"] + "/click", {}
        )
        assert page.evaluate("sel[0]") == "omega"


def test_back_exits_fullscreen_before_navigating(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    with application(tmp_path) as page:
        page.evaluate('applyPath(["a.txt"])')
        page.wait('document.querySelector("#pv-fullscreen")')
        page.evaluate('applyPath(["b.txt"])')
        page.wait('sel[0] === "b.txt"')
        page.evaluate(
            'document.documentElement.requestFullscreen = undefined; document.querySelector("#pv-fullscreen").click()'
        )
        page.evaluate(
            '[...document.querySelectorAll("#bar button")].find(b => b.textContent === "Back").click()'
        )
        page.wait('!document.documentElement.classList.contains("pv-fullscreen")')
        assert page.evaluate("sel[0]") == "b.txt"


def test_scrolled_row_remains_clickable(tmp_path):
    """Acceptance blocker: WebKitGTK reports a visible row as the scroll container."""
    for name in [
        "big",
        "deep",
        "empty",
        "locked",
        "mixed",
        "racing",
        "refresh",
        "search",
        "slow",
        "sorting",
        "tables",
        "wide",
    ]:
        (tmp_path / name).mkdir()
    (tmp_path / "README.md").write_text("# fixture")
    with application(tmp_path) as page:
        page.call("/window/rect", {"width": 568, "height": 320})
        result = page.evaluate("""async () => {
const row = document.querySelector('.row[title="wide"]');
row.scrollIntoView({block:'nearest',inline:'nearest'});
await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
const r = row.getBoundingClientRect();
const hit = document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
return {clickable: row.contains(hit), hit: hit?.id || hit?.className,
        row: r.toJSON(), viewport: {width:innerWidth,height:innerHeight}};
}""")
        assert result["clickable"], result


def test_row_edge_beside_column_scrollbar_is_clickable(tmp_path):
    """A scrolling column's scrollbar must not cover its rows' chevrons."""
    for index in range(40):
        (tmp_path / f"folder-{index:02}").mkdir()
    with application(tmp_path) as page:
        page.call("/window/rect", {"width": 568, "height": 320})
        result = page.evaluate("""async () => {
await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
const body = document.querySelector('.col[data-i="0"] .col-body');
const row = body.querySelector('.row');
const r = row.getBoundingClientRect();
const hit = document.elementFromPoint(r.right - 3, r.y + r.height / 2);
return {clickable: row.contains(hit), hit: hit?.id || hit?.className,
        scrolls: body.scrollHeight > body.clientHeight, row: r.toJSON()};
}""")
        assert result["scrolls"], result
        assert result["clickable"], result


def test_write_preserves_embedded_nul(tmp_path):
    file = tmp_path / "text.txt"
    file.write_text("before")
    with application(tmp_path) as page:
        page.evaluate(
            'async () => { await FS.write(path[0].kids[0], "before\\u0000after é"); }'
        )
    assert file.read_bytes() == "before\0after é".encode()


def test_ui_driver_reports_console_errors(tmp_path):
    import asyncio

    from ui_driver import NativePage

    with application(tmp_path) as raw:
        page = NativePage(raw, tmp_path)
        errors = []
        page.on("console", lambda message: errors.append((message.type, message.text)))
        asyncio.run(page.evaluate('console.error("native", "failure")'))
        assert errors == [("error", "native failure")]
        asyncio.run(page.evaluate("true"))
        assert len(errors) == 1


def test_ui_driver_waits_with_argument(tmp_path):
    import asyncio

    from ui_driver import NativePage

    (tmp_path / "a.txt").write_text("a")
    with application(tmp_path) as raw:
        page = NativePage(raw, tmp_path)
        asyncio.run(
            page.wait_for_function(
                "name => path[0].kids.some(n => n.name === name)", arg="a.txt"
            )
        )


def test_ui_driver_waits_for_javascript_truthiness(tmp_path):
    import asyncio

    from ui_driver import NativePage

    with application(tmp_path) as raw:
        page = NativePage(raw, tmp_path)
        asyncio.run(page.wait_for_function("[]", timeout=1000))
        # A pending promise is a truthy object, not a value to wait for.
        asyncio.run(
            page.wait_for_function(
                "new Promise(resolve => setTimeout(resolve, 2000))", timeout=1000
            )
        )


def test_denied_folder_is_recognized_in_any_locale(tmp_path):
    (tmp_path / "locked").mkdir()
    (tmp_path / "locked").chmod(0)
    try:
        with application(tmp_path, LC_ALL="fi_FI.UTF-8", LANGUAGE="fi") as page:
            denied = page.evaluate(
                "async () => { const n = path[0].kids[0]; await FS.ensureLoaded(n); return n.denied; }"
            )
    finally:
        (tmp_path / "locked").chmod(0o700)
    assert denied == "No permission to read"


def test_ui_driver_clicks_through_folding_columns(tmp_path):
    """Like Playwright, wait until a sliding row settles and receives the point."""
    import asyncio

    from ui_driver import NativePage

    folder = tmp_path / "wide"
    for level in range(5):
        folder = folder / f"level-{level}-{'w' * 36}"
    folder.mkdir(parents=True)
    (folder / "leaf.txt").write_text("leaf")
    for index in (1, 2):
        (tmp_path / "wide" / f"a-quite-long-file-name-{index}.txt").write_text("")
    with application(tmp_path) as raw:
        page = NativePage(raw, tmp_path)

        async def drill():
            await page.set_viewport_size({"width": 390, "height": 700})
            await page.click('.col[data-i="0"] .row[title="wide"]')
            await page.wait_for_function("path[1]?.kids")
            for level in range(5):
                await page.click(
                    f'.col[data-i="{level + 1}"] .row[title^="level-{level}-"]'
                )
                await page.wait_for_function(
                    "n => path.length === n && path.at(-1)?.kids", arg=level + 3
                )

        asyncio.run(drill())
        assert raw.evaluate("path.at(-1).name").startswith("level-4-")


def test_ui_driver_counts_native_file_reads(tmp_path):
    """__gets mirrors the fake handle's getFile() count through the real port."""
    import asyncio

    from ui_driver import NativePage

    (tmp_path / "a.txt").write_text("a")
    with application(tmp_path) as raw:
        page = NativePage(raw, tmp_path)
        asyncio.run(page.evaluate("window.__mk = () => null; window.__gets = 0"))
        raw.evaluate(
            "async () => { const n = path[0].kids[0]; n.meta = null; await FS.loadMeta(n); await FS.blob(n); }"
        )
        assert raw.evaluate("__gets") == 2


def test_automation_keeps_no_profile(tmp_path):
    """Like a new Playwright context: test launches share no stored settings."""
    root, data, cache = tmp_path / "root", tmp_path / "data", tmp_path / "cache"
    root.mkdir()
    with application(root, XDG_DATA_HOME=str(data), XDG_CACHE_HOME=str(cache)) as page:
        page.evaluate("localStorage.setItem('filemill.sort', 'size')")
    assert not (data / "filemill").exists()
    assert not (cache / "filemill").exists()
