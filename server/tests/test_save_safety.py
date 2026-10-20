"""Replacement failures and optimistic writes must preserve existing bytes."""

import os
import threading

import pytest
from starlette.requests import Request

from filemill import api
from filemill import app as app_module


def revision(path):
    return api.raw_response(path, snapshot=True).headers.get("etag", "missing")


@pytest.mark.parametrize("failure", ["fsync", "replace"])
def test_failed_replacement_keeps_old_bytes(tmp_path, monkeypatch, failure):
    target = tmp_path / "file.txt"
    target.write_text("old bytes")
    expected = revision(target)

    def fail(*args):
        raise OSError("injected disk failure")

    monkeypatch.setattr(os, failure, fail)
    response = api.save_file(target, b"draft", expected)
    assert response.status_code == 500
    assert target.read_text() == "old bytes"
    assert list(tmp_path.iterdir()) == [target]


def test_stale_and_missing_revisions_are_refused(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("old")
    expected = revision(target)
    target.write_text("external")
    assert api.save_file(target, b"draft", expected).status_code == 409
    assert api.save_file(target, b"draft").status_code == 428
    assert target.read_text() == "external"


def test_replacement_link_and_metadata_policy(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("old")
    target.chmod(0o640)
    hard = tmp_path / "hard.txt"
    hard.hardlink_to(target)
    link = tmp_path / "sym.txt"
    link.symlink_to(target)
    before = target.stat()
    response = api.save_file(link, b"new", revision(link))
    assert response.status_code == 200
    assert link.is_symlink()
    assert link.read_text() == "new"
    assert hard.read_text() == "old"
    after = target.stat()
    assert (after.st_uid, after.st_gid, after.st_mode) == (
        before.st_uid,
        before.st_gid,
        before.st_mode,
    )
    assert response.headers["etag"] == revision(target)


async def test_body_limit_stops_receiving_and_save_runs_off_loop(tmp_root, monkeypatch):
    monkeypatch.setattr(app_module.mutations, "authorized", lambda request: True)
    monkeypatch.setattr(api, "RENDER_MAX", 4)
    chunks = iter([b"1234", b"5"])

    async def receive():
        try:
            chunk = next(chunks)
        except StopIteration:
            pytest.fail("oversized body kept reading")
        return {"type": "http.request", "body": chunk, "more_body": True}

    scope = {
        "type": "http",
        "app": app_module.app,
        "method": "POST",
        "path": "/api/save",
        "headers": [],
    }
    response = await app_module.api_save(Request(scope, receive), p="readme.md")
    assert response.status_code == 413
    assert (tmp_root / "readme.md").read_text() == "# Hello\n**world**\n"

    owner = threading.get_ident()

    def save(*args):
        assert threading.get_ident() != owner
        return api.JSONResponse({})

    monkeypatch.setattr(api, "save_file", save)

    async def small():
        return {"type": "http.request", "body": b"ok", "more_body": False}

    assert (
        await app_module.api_save(Request(scope, small), p="readme.md")
    ).status_code == 200


def test_partial_temporary_write_keeps_old_bytes(tmp_path, monkeypatch):
    target = tmp_path / "file.txt"
    target.write_text("old bytes")
    expected = revision(target)
    create = api.tempfile.NamedTemporaryFile

    def partial_write(**kwargs):
        output = create(**kwargs)
        write = output.write

        def fail(data):
            write(data[:2])
            raise OSError("disk full after partial write")

        output.write = fail
        return output

    monkeypatch.setattr(api.tempfile, "NamedTemporaryFile", partial_write)
    assert api.save_file(target, b"draft", expected).status_code == 500
    assert target.read_text() == "old bytes"
    assert list(tmp_path.iterdir()) == [target]


def test_external_change_during_flush_is_not_overwritten(tmp_path, monkeypatch):
    target = tmp_path / "file.txt"
    target.write_text("old")
    expected = revision(target)
    monkeypatch.setattr(os, "fsync", lambda fd: target.write_text("external"))
    assert api.save_file(target, b"draft", expected).status_code == 409
    assert target.read_text() == "external"
    assert list(tmp_path.iterdir()) == [target]


def test_concurrent_saves_cannot_both_use_one_revision(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    target = tmp_path / "file.txt"
    target.write_text("old")
    expected = revision(target)
    with ThreadPoolExecutor(2) as pool:
        responses = list(
            pool.map(
                lambda data: api.save_file(target, data, expected), [b"one", b"two"]
            )
        )
    assert sorted(r.status_code for r in responses) == [200, 409]


def test_failed_ownership_preservation_keeps_old_bytes(tmp_path, monkeypatch):
    from types import SimpleNamespace

    target = tmp_path / "file.txt"
    target.write_text("old")
    expected = revision(target)
    monkeypatch.setattr(os, "fstat", lambda fd: SimpleNamespace(st_uid=-1, st_gid=-1))

    def denied(*args):
        raise PermissionError("cannot preserve ownership")

    monkeypatch.setattr(os, "fchown", denied)
    assert api.save_file(target, b"draft", expected).status_code == 500
    assert target.read_text() == "old"
    assert list(tmp_path.iterdir()) == [target]


def test_read_only_target_cannot_be_replaced(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("old")
    target.chmod(0o400)
    try:
        assert api.save_file(target, b"draft", revision(target)).status_code == 500
        assert target.read_text() == "old"
    finally:
        target.chmod(0o600)


def test_save_does_not_report_failure_from_metadata_after_commit(tmp_path, monkeypatch):
    target = tmp_path / "file.txt"
    target.write_text("old")
    expected = revision(target)
    replace, stat = os.replace, type(target).stat
    committed = False

    def commit(*args):
        nonlocal committed
        replace(*args)
        committed = True

    def fail_after_commit(path, **kwargs):
        if path == target and committed:
            raise OSError("metadata unavailable after commit")
        return stat(path, **kwargs)

    monkeypatch.setattr(os, "replace", commit)
    monkeypatch.setattr(type(target), "stat", fail_after_commit)
    response = api.save_file(target, b"draft", expected)
    assert response.status_code == 200
    assert target.read_bytes() == b"draft"


def test_raw_download_keeps_range_support(client):
    response = client.get("/api/raw?p=readme.md", headers={"Range": "bytes=0-2"})
    assert response.status_code == 206
    assert response.content == b"# H"
