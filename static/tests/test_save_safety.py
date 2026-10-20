"""Exercise the real browser filesystem port with an externally changed handle."""

import pytest


@pytest.mark.parametrize("failure", ["external", "write", "close"])
async def test_browser_save_conflicts_and_aborts(browser, base, failure):
    page = await browser.new_page()
    await page.goto(base)
    result = await page.evaluate('''async failure => {
      const {FSA} = await import('/ui/adapters/fsa.js');
      let content = 'old', aborted = false, opened = false;
      const node = FSA.node('test.txt', {kind:'file',
        getFile: async () => new File([content], 'test.txt', {lastModified:1}),
        createWritable: async () => { opened = true; return {
          write: async () => { if (failure === 'write') throw Error('disk'); },
          close: async () => { if (failure === 'close') throw Error('disk'); },
          abort: async () => { aborted = true; }
        }; }
      });
      const blob = await FSA.blob(node);
      if (failure === 'external') content = 'new'; // same size and timestamp
      try { await FSA.write(node, 'draft', blob.revision); }
      catch (error) { return {error:String(error), aborted, opened}; }
      return {};
    }''', failure)
    assert result.get("error")
    if failure == "external":
        assert "Conflict" in result["error"]
        assert not result["opened"]
    else:
        assert result["aborted"]
    await page.close()


async def test_editor_pins_document_revision_and_keeps_draft(browser, base):
    page = await browser.new_page()
    await page.goto(base)
    await page.evaluate('''async () => {
      const {FSA} = await import('/ui/adapters/fsa.js');
      const {withDocuments} = await import('/ui/adapters/vfs-doc.js');
      const {useFilesystem} = await import('/ui/core/ports.js');
      const {openEditor} = await import('/ui/editor/editor.js');
      window.content = '# old';
      window.node = {...FSA.node('test.md', {kind:'file',
        getFile: async () => new File([window.content], 'test.md', {lastModified:1}),
        createWritable: async () => { throw Error('must detect conflict first'); }
      }), doc:true};
      window.fs = withDocuments(FSA);
      useFilesystem(fs);
      document.body.innerHTML = '<div id="preview"><button id="pv-edit"></button><span id="pv-modified"></span><div id="pv-content"></div></div>';
      await openEditor(node, () => true, () => { throw Error('unexpected refresh'); });
    }''')
    await page.fill("#pv-editor", "my draft")
    # A later preview read must not advance the editor's expected revision.
    await page.evaluate('''async () => {
      content = '# new'; node.file = node.meta = null;
      await fs.blob(node);
    }''')
    await page.click("#pv-save")
    await page.wait_for_function("document.querySelector('#pv-edit-err').textContent.includes('Conflict')")
    assert await page.input_value("#pv-editor") == "my draft"
    assert not await page.eval_on_selector("#pv-editor", "e => e.readOnly")
    await page.close()
