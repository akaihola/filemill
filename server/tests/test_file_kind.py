from pathlib import Path

import pytest

from filemill.vfs import classify_path

CASES = [
    ("folder", True, False, False, "folder", "none", False),
    ("data.db", False, False, True, "vfs", "virtual", False),
    ("link.desktop", False, False, False, "link", "desktop", False),
    ("photo.png", False, False, False, "file", "image", False),
    ("doc.pdf", False, False, False, "file", "pdf", False),
    ("note.md", False, False, False, "file", "md", False),
    ("captions.vtt", False, False, False, "file", "vtt", False),
    ("source.py", False, False, False, "file", "text", True),
]


@pytest.mark.parametrize(
    "name,is_dir,virtual,provider,kind,preview,editable", CASES
)
def test_file_kind_table(
    name, is_dir, virtual, provider, kind, preview, editable
):
    result = classify_path(
        Path(name), is_dir=is_dir, virtual=virtual, provider=provider
    )
    assert (result.kind, result.preview, result.editable) == (
        kind,
        preview,
        editable,
    )
