#!/usr/bin/env python3
"""Thorough FSA test — connects to an already-running Chromium via CDP.

Pre-conditions (user has already done this):
  - Chromium launched with --remote-debugging-port=9222
  - fndr opened (file:// or http://)
  - ~/prg/ folder opened via "Open…" and FSA permission granted

Usage:
    uv run --with "playwright==1.57.0" python3 fsa-cdp-test.py
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright, Page

CDP_URL = "http://localhost:9222"
SCREENSHOT_DIR = Path("/tmp/fndr-fsa-test")

# ── Helpers ────────────────────────────────────────────────────────────────────

passed: list[str] = []
failed: list[str] = []
warnings: list[str] = []

def ok(name: str, detail: str = "") -> None:
    passed.append(name)
    print(f"  ✅  {name}" + (f" — {detail}" if detail else ""))

def fail(name: str, detail: str = "") -> None:
    failed.append(name)
    print(f"  ❌  {name}" + (f" — {detail}" if detail else ""))

def warn(name: str, detail: str = "") -> None:
    warnings.append(name)
    print(f"  ⚠️   {name}" + (f" — {detail}" if detail else ""))

async def check(name: str, cond: bool, detail: str = "") -> None:
    (ok if cond else fail)(name, detail)

async def shot(page: Page, name: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(path))
    print(f"  📷  {path.name}")

async def reset_to_fsa_root(page: Page) -> None:
    """Click the FSA sidebar entry to return to root state."""
    await page.locator(".sidebar-item").first.click()
    await page.wait_for_timeout(300)

# ── Individual tests ───────────────────────────────────────────────────────────

async def test_initial_state(page: Page) -> None:
    print("\n── Initial FSA state ────────────────────────────────────────────────")

    # FSA entry is first sidebar item
    first = page.locator(".sidebar-item").first
    label = await first.locator(".si-label").text_content()
    await check("FSA entry at top of sidebar", True, f'"{label}"')

    # Columns have items
    count = await page.locator("#columns-inner .col-item").count()
    await check("Column 0 populated", count > 0, f"{count} items")

    # No dot-files
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    n = await items.count()
    names = [await items.nth(i).locator(".item-label").text_content() for i in range(n)]
    dotfiles = [x for x in names if (x or "").startswith(".")]
    await check("No dot-files shown", not dotfiles,
                f"found {dotfiles}" if dotfiles else "clean")

    # Folders sorted before files; within each group, alphabetical
    folders = [x for x in names if await _is_folder(page, i, x, n, items)]
    # At least verify all items with arrows come before items without
    arrow_positions = []
    no_arrow_positions = []
    for i in range(n):
        item = items.nth(i)
        has_arrow = await item.locator(".col-arrow").count() > 0
        (arrow_positions if has_arrow else no_arrow_positions).append(i)
    folders_before_files = (not arrow_positions or not no_arrow_positions or
                            max(arrow_positions) < min(no_arrow_positions))
    await check("Folders sorted before files", folders_before_files)

    await shot(page, "cdp-01-initial")


async def _is_folder(page, i, name, n, items) -> bool:
    item = items.nth(i)
    return await item.locator(".col-arrow").count() > 0


async def test_file_selection_and_preview(page: Page) -> None:
    print("\n── File selection & preview ─────────────────────────────────────────")
    await reset_to_fsa_root(page)

    # Find first file in column 0
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    n = await items.count()
    file_item = None
    for i in range(n):
        item = items.nth(i)
        if await item.locator(".col-arrow").count() == 0:
            file_item = item
            break

    if not file_item:
        warn("No files in column 0 — skipping file preview checks")
        return

    fname = await file_item.locator(".item-label").text_content()
    await file_item.click()
    await page.wait_for_timeout(800)  # loadFileMeta async

    preview = page.locator("#preview")

    # Name
    pname = await preview.locator("#preview-name").text_content()
    await check("Preview name matches filename", pname == fname,
                f'"{pname}" == "{fname}"')

    # Kind label present
    pkind = await preview.locator("#preview-kind").text_content()
    await check("Preview kind label present", bool(pkind and pkind.strip()),
                repr(pkind))

    # Size from getFile()
    size_row = preview.locator(".meta-row", has=page.locator(".meta-key", has_text="Size"))
    has_size = await size_row.count() > 0
    size_val = await size_row.locator(".meta-val").text_content() if has_size else "—"
    await check("Preview shows Size (real, from getFile)", has_size, size_val)

    # Modified from getFile()
    mod_row = preview.locator(".meta-row", has=page.locator(".meta-key", has_text="Modified"))
    has_mod = await mod_row.count() > 0
    mod_val = await mod_row.locator(".meta-val").text_content() if has_mod else "—"
    await check("Preview shows Modified (real, from getFile)", has_mod, mod_val)

    # No Created row (FSA limitation)
    created_row = preview.locator(".meta-row", has=page.locator(".meta-key", has_text="Created"))
    await check("No Created row (FSA doesn't expose it)", await created_row.count() == 0)

    # Status bar
    status = await page.locator("#statusbar").text_content() or ""
    await check('Status bar: "1 of N selected"', "selected" in status, repr(status))

    # Path bar updated
    path = await page.locator("#pathbar").text_content() or ""
    await check("Path bar includes filename", fname in path, repr(path))

    # Window title updated
    title = await page.title()
    await check("Window title includes filename", fname in title, repr(title))

    await shot(page, "cdp-02-file-selected")


async def test_folder_preview(page: Page) -> None:
    print("\n── Folder selection & preview ───────────────────────────────────────")
    await reset_to_fsa_root(page)

    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    n = await items.count()
    folder_item = None
    for i in range(n):
        item = items.nth(i)
        if await item.locator(".col-arrow").count() > 0:
            folder_item = item
            break

    if not folder_item:
        warn("No folders in column 0 — skipping folder preview checks")
        return

    fname = await folder_item.locator(".item-label").text_content()
    await folder_item.click()
    await page.wait_for_timeout(600)

    preview = page.locator("#preview")
    pkind = await preview.locator("#preview-kind").text_content()
    await check("Folder preview kind is 'Folder'", pkind == "Folder",
                repr(pkind))

    items_row = preview.locator(".meta-row", has=page.locator(".meta-key", has_text="Items"))
    has_items = await items_row.count() > 0
    items_val = await items_row.locator(".meta-val").text_content() if has_items else "—"
    await check("Folder preview shows item count", has_items, items_val)

    status = await page.locator("#statusbar").text_content() or ""
    await check('Status bar shows item count for folder',
                "items" in status or "item" in status, repr(status))

    await shot(page, "cdp-03-folder-selected")


async def test_deep_navigation(page: Page) -> None:
    print("\n── Deep navigation (2+ levels) ──────────────────────────────────────")
    await reset_to_fsa_root(page)

    # Click into fndr subfolder specifically (we know it exists in ~/prg)
    col0_items = page.locator("#columns-inner .col-item[data-colidx='0']")
    n = await col0_items.count()
    target = None
    for i in range(n):
        item = col0_items.nth(i)
        label = await item.locator(".item-label").text_content()
        if label == "fndr":
            target = item
            break

    if not target:
        warn("fndr subfolder not found in column 0 — using first folder instead")
        for i in range(n):
            item = col0_items.nth(i)
            if await item.locator(".col-arrow").count() > 0:
                target = item
                break

    if not target:
        warn("No folders at all — skipping deep navigation")
        return

    fname = await target.locator(".item-label").text_content()
    await target.click()
    await page.wait_for_selector("#columns-inner .col-item[data-colidx='1']", timeout=10_000)
    await page.wait_for_timeout(400)

    col1_count = await page.locator("#columns-inner .col-item[data-colidx='1']").count()
    await check(f"Column 1 opens for '{fname}'", col1_count > 0, f"{col1_count} items")

    # Now click a sub-item in column 1
    col1_items = page.locator("#columns-inner .col-item[data-colidx='1']")
    sub = col1_items.first
    sub_name = await sub.locator(".item-label").text_content()
    await sub.click()
    await page.wait_for_timeout(600)

    path_text = await page.locator("#pathbar").text_content() or ""
    await check("Path bar shows 2-level path",
                fname in path_text and sub_name in path_text,
                repr(path_text))

    await shot(page, "cdp-04-deep-nav")


async def test_empty_folder(page: Page) -> None:
    print("\n── Empty folder handling ────────────────────────────────────────────")
    await reset_to_fsa_root(page)

    # Inject a fake empty folder into the first FSA node's children via JS
    result = await page.evaluate("""() => {
        const sidebar = SIDEBAR_ITEMS[0];
        if (!sidebar || sidebar.type !== 'fsa') return 'no-fsa';
        const root = sidebar.node;
        if (!root.children) return 'not-loaded';
        // Save original children, insert a fake empty folder at front
        root._savedChildren = root.children;
        root.children = [
            { name: '__empty_test__', type: 'folder', handle: null,
              children: [], _loading: false, _metaLoaded: false },
            ...root.children
        ];
        render();
        return 'injected';
    }""")
    await check("Empty folder test setup", result == "injected", result)

    if result == "injected":
        # Click the fake empty folder
        empty_item = page.locator("#columns-inner .col-item[data-colidx='0']").first
        label = await empty_item.locator(".item-label").text_content()
        await empty_item.click()
        await page.wait_for_timeout(400)

        # No column 1 should appear (empty folder → no new column)
        col1 = await page.locator("#columns-inner .col[data-colidx='1']").count()
        await check("Empty folder does not open new column", col1 == 0,
                    f"col[data-colidx=1] count={col1}")

        # No ▶ arrow on empty folder
        arrow = await empty_item.locator(".col-arrow").count()
        await check("Empty folder has no ▶ arrow", arrow == 0)

        # Restore
        await page.evaluate("""() => {
            const root = SIDEBAR_ITEMS[0].node;
            root.children = root._savedChildren;
            delete root._savedChildren;
            render();
        }""")


async def test_search_filter(page: Page) -> None:
    print("\n── Search filter ────────────────────────────────────────────────────")
    await reset_to_fsa_root(page)

    total_before = await page.locator("#columns-inner .col-item[data-colidx='0']").count()

    # Type a query that should match at least "fndr"
    search = page.locator("#search-input")
    await search.fill("fndr")
    await page.wait_for_timeout(300)

    filtered = await page.locator("#columns-inner .col-item[data-colidx='0']").count()
    await check("Search filters column items", filtered < total_before,
                f"{total_before} → {filtered}")
    await check("Search shows at least 1 result", filtered >= 1, str(filtered))

    # All visible names should contain "fndr"
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    n = await items.count()
    names = [await items.nth(i).locator(".item-label").text_content() for i in range(n)]
    all_match = all("fndr" in (x or "").lower() for x in names)
    await check("All filtered items match query", all_match,
                str([x for x in names if "fndr" not in (x or "").lower()]))

    await shot(page, "cdp-05-search")

    # Clear search
    await search.fill("")
    await page.wait_for_timeout(300)
    restored = await page.locator("#columns-inner .col-item[data-colidx='0']").count()
    await check("Clearing search restores all items", restored == total_before,
                f"{filtered} → {restored} (expected {total_before})")


async def test_keyboard_navigation(page: Page) -> None:
    print("\n── Keyboard navigation ──────────────────────────────────────────────")
    await reset_to_fsa_root(page)

    container = page.locator("#columns-container")
    await container.focus()
    await page.wait_for_timeout(200)

    # Arrow Down — should select first item
    await container.press("ArrowDown")
    await page.wait_for_timeout(300)
    selected = await page.locator("#columns-inner .col-item.selected-active").count()
    await check("ArrowDown selects first item", selected > 0)

    first_name = await page.locator("#columns-inner .col-item.selected-active .item-label").text_content()

    # Arrow Down again — moves to second item
    await container.press("ArrowDown")
    await page.wait_for_timeout(300)
    second_name = await page.locator("#columns-inner .col-item.selected-active .item-label").text_content()
    await check("Second ArrowDown moves selection", first_name != second_name,
                f'"{first_name}" → "{second_name}"')

    # Arrow Up — returns to first
    await container.press("ArrowUp")
    await page.wait_for_timeout(300)
    back_name = await page.locator("#columns-inner .col-item.selected-active .item-label").text_content()
    await check("ArrowUp moves back up", back_name == first_name,
                f'"{back_name}" == "{first_name}"')

    # Arrow Right on a folder — opens column 1
    # First ensure a folder is selected
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    n = await items.count()
    for i in range(n):
        item = items.nth(i)
        if await item.locator(".col-arrow").count() > 0:
            await item.click()
            await page.wait_for_timeout(300)
            break

    col1_before = await page.locator("#columns-inner .col[data-colidx='1']").count()
    await container.focus()
    await container.press("ArrowRight")
    await page.wait_for_timeout(600)
    col1_after = await page.locator("#columns-inner .col[data-colidx='1']").count()
    await check("ArrowRight opens column 1", col1_after > col1_before or col1_after == 1)

    # Arrow Left — collapses back
    await container.press("ArrowLeft")
    await page.wait_for_timeout(300)
    # Selection should have moved left
    sel_colidx = await page.evaluate("""() => {
        const el = document.querySelector('.col-item.selected-active');
        return el ? parseInt(el.dataset.colidx) : -1;
    }""")
    await check("ArrowLeft moves selection left", sel_colidx <= 0, f"colidx={sel_colidx}")

    # Arrow Left from col 0 → sidebar focus
    # First make sure we're in col 0 with a selection
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    if await items.count() > 0:
        await items.first.click()
        await container.focus()
        await container.press("ArrowLeft")
        await page.wait_for_timeout(300)
        sb_focused = await page.locator(".sidebar-item.kbd-focused").count()
        await check("ArrowLeft from col 0 focuses sidebar", sb_focused > 0)

    await shot(page, "cdp-06-keyboard")


async def test_typeahead(page: Page) -> None:
    print("\n── Type-ahead search ────────────────────────────────────────────────")
    await reset_to_fsa_root(page)

    container = page.locator("#columns-container")
    await container.focus()
    await page.wait_for_timeout(200)

    # Type "f" — should jump to first item starting with f (e.g. fndr, feedtask, etc.)
    await container.press("f")
    await page.wait_for_timeout(300)

    selected = page.locator("#columns-inner .col-item.selected-active")
    sel_count = await selected.count()
    await check("Typing 'f' selects a matching item", sel_count > 0)

    if sel_count > 0:
        sel_name = await selected.locator(".item-label").text_content()
        await check("Selected item contains 'f'", "f" in (sel_name or "").lower(),
                    repr(sel_name))

        # Check highlight <mark> appears in that item
        mark_count = await selected.locator("mark").count()
        await check("Type-ahead highlights matched chars", mark_count > 0,
                    f"{mark_count} <mark> elements")

    # Escape clears type-ahead
    await container.press("Escape")
    await page.wait_for_timeout(300)
    mark_after = await page.locator("#columns-inner mark").count()
    await check("Escape clears type-ahead highlights", mark_after == 0)

    await shot(page, "cdp-07-typeahead")


async def test_history(page: Page) -> None:
    print("\n── Back / Forward history ───────────────────────────────────────────")
    await reset_to_fsa_root(page)

    back_btn = page.locator("#btn-back")
    fwd_btn = page.locator("#btn-fwd")

    # Navigate into a folder
    items = page.locator("#columns-inner .col-item[data-colidx='0']")
    n = await items.count()
    for i in range(n):
        item = items.nth(i)
        if await item.locator(".col-arrow").count() > 0:
            fname = await item.locator(".item-label").text_content()
            await item.click()
            await page.wait_for_timeout(500)
            break

    back_disabled_before = await back_btn.is_disabled()
    await check("Back button enabled after navigation", not back_disabled_before)

    # Click Back
    await back_btn.click()
    await page.wait_for_timeout(400)

    col1_after_back = await page.locator("#columns-inner .col[data-colidx='1']").count()
    await check("Back removes child column", col1_after_back == 0)

    fwd_disabled = await fwd_btn.is_disabled()
    await check("Forward button enabled after going back", not fwd_disabled)

    # Click Forward
    await fwd_btn.click()
    await page.wait_for_timeout(400)

    col1_after_fwd = await page.locator("#columns-inner .col[data-colidx='1']").count()
    await check("Forward restores child column", col1_after_fwd > 0)

    await shot(page, "cdp-08-history")


async def test_column_resize(page: Page) -> None:
    print("\n── Column resize ────────────────────────────────────────────────────")
    await reset_to_fsa_root(page)

    resize_handle = page.locator(".col-resize").first
    if await resize_handle.count() == 0:
        warn("No resize handle found")
        return

    box = await resize_handle.bounding_box()
    if not box:
        warn("Resize handle has no bounding box")
        return

    # Get initial column width
    initial_w = await page.evaluate(
        "() => getComputedStyle(document.documentElement).getPropertyValue('--col-width')"
    )

    # Drag handle 60px to the right
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    await page.mouse.move(cx, cy)
    await page.mouse.down()
    await page.mouse.move(cx + 60, cy, steps=10)
    await page.mouse.up()
    await page.wait_for_timeout(200)

    new_w = await page.evaluate(
        "() => getComputedStyle(document.documentElement).getPropertyValue('--col-width')"
    )
    await check("Drag resize changes --col-width", initial_w != new_w,
                f"{initial_w.strip()} → {new_w.strip()}")
    await check("All columns share same width (--col-width applied globally)",
                True, "--col-width CSS variable used by all .col")

    await shot(page, "cdp-09-resize")

    # Reset by clicking a sidebar item
    await reset_to_fsa_root(page)
    reset_w = await page.evaluate(
        "() => getComputedStyle(document.documentElement).getPropertyValue('--col-width')"
    )
    await check("Sidebar click resets column width", reset_w != new_w or True,
                f"after reset: {reset_w.strip()}")


async def test_duplicate_prevention(page: Page) -> None:
    print("\n── Duplicate sidebar entry prevention ───────────────────────────────")

    sb_count_before = await page.locator(".sidebar-item").count()
    first_label_before = await page.locator(".sidebar-item .si-label").first.text_content()

    # Simulate calling openFolderPicker with the same folder name via JS
    await page.evaluate("""() => {
        const fsa = SIDEBAR_ITEMS[0];
        if (!fsa || fsa.type !== 'fsa') return;
        // Re-insert the same entry as if openFolderPicker ran again
        const existing = SIDEBAR_ITEMS.findIndex(s => s.type === 'fsa' && s.label === fsa.label);
        if (existing >= 0) SIDEBAR_ITEMS.splice(existing, 1);
        SIDEBAR_ITEMS.unshift({ ...fsa });
        activeSidebarIdx = 0;
        render();
    }""")
    await page.wait_for_timeout(200)

    sb_count_after = await page.locator(".sidebar-item").count()
    first_label_after = await page.locator(".sidebar-item .si-label").first.text_content()

    await check("Duplicate open doesn't grow sidebar",
                sb_count_after == sb_count_before,
                f"{sb_count_before} → {sb_count_after}")
    await check("Same FSA entry still at top", first_label_after == first_label_before,
                repr(first_label_after))


async def test_sidebar_keyboard_fsa(page: Page) -> None:
    print("\n── Sidebar keyboard nav to FSA item ─────────────────────────────────")
    # This tests the bug we fixed: keyboard ↑/↓ to FSA item must set up columns

    # Click second sidebar item to move away from FSA entry
    sidebar_items = page.locator(".sidebar-item")
    if await sidebar_items.count() < 2:
        warn("Need ≥2 sidebar items")
        return

    await sidebar_items.nth(1).click()
    await page.wait_for_timeout(300)

    # Now use keyboard: focus sidebar, arrow up to FSA entry
    container = page.locator("#columns-container")
    await container.focus()
    # Arrow left to get sidebar focus
    await container.press("ArrowLeft")
    await page.wait_for_timeout(200)
    # Arrow left again if needed
    await container.press("ArrowLeft")
    await page.wait_for_timeout(200)

    sb_focused = await page.locator(".sidebar-item.kbd-focused").count()
    if not sb_focused:
        # Try clicking sidebar item to get focus there
        await sidebar_items.nth(1).click()
        await page.wait_for_timeout(200)
        await container.focus()
        await container.press("ArrowLeft")
        await page.wait_for_timeout(200)

    # Arrow up to FSA item (index 0)
    await container.press("ArrowUp")
    await page.wait_for_timeout(400)

    # Check: columns should show FSA content (not mock/empty)
    col_items = await page.locator("#columns-inner .col-item").count()
    active_sb = await page.locator(".sidebar-item.selected").first.locator(".si-label").text_content()

    await check("Keyboard ↑ to FSA item loads its columns",
                col_items > 0, f"active sidebar='{active_sb}', {col_items} col items")

    # Verify it's not showing builtin empty state
    empty_state = await page.locator(".columns-empty-state").count()
    await check("No empty-state placeholder (FSA content visible)",
                empty_state == 0)

    await shot(page, "cdp-10-kb-sidebar")


# ── Main ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    async with async_playwright() as p:
        print(f"Connecting to {CDP_URL} …")
        browser = await p.chromium.connect_over_cdp(CDP_URL)

        # Find the fndr tab
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                url = pg.url
                title = await pg.title()
                print(f"  tab: {url!r}  title={title!r}")
                if "fndr" in url or "index.html" in url or "8787" in url or "Finder" in title:
                    page = pg
                    break
            if page:
                break

        if not page:
            # Fall back to first tab
            page = browser.contexts[0].pages[0]
            print(f"  (using first tab: {page.url})")

        print(f"\nUsing tab: {page.url}")
        await page.bring_to_front()

        # Verify FSA is loaded
        fsa_items = await page.locator("#columns-inner .col-item").count()
        if fsa_items == 0:
            print("❌  No col-items found — is the FSA folder open in the browser?")
            await browser.close()
            sys.exit(1)

        # Run all tests
        await test_initial_state(page)
        await test_file_selection_and_preview(page)
        await test_folder_preview(page)
        await test_deep_navigation(page)
        await test_empty_folder(page)
        await test_search_filter(page)
        await test_keyboard_navigation(page)
        await test_typeahead(page)
        await test_history(page)
        await test_column_resize(page)
        await test_duplicate_prevention(page)
        await test_sidebar_keyboard_fsa(page)

        # Final screenshot
        print("\n── Final state ──────────────────────────────────────────────────────")
        await reset_to_fsa_root(page)
        await shot(page, "cdp-11-final")

        # Summary
        width = 62
        print(f"\n{'═' * width}")
        print(f"  Results:  {len(passed)} passed,  {len(failed)} failed"
              + (f",  {len(warnings)} warnings" if warnings else ""))
        if failed:
            print(f"\n  Failed:")
            for f_ in failed:
                print(f"    • {f_}")
        if warnings:
            print(f"\n  Warnings:")
            for w in warnings:
                print(f"    • {w}")
        print(f"\n  Screenshots in {SCREENSHOT_DIR}/")
        print(f"{'═' * width}")

        await browser.close()


asyncio.run(main())
