import html as html_lib
from pathlib import Path

from filemill.providers.vtt_provider import VTTProvider

VALID = """WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.500 align:start\n<v Alice>Hello <c.green>world</c>\nsecond line\n\n00:00:04.000 --> 00:00:05.000\nBye\n"""
YOUTUBE = """WEBVTT\nKind: captions\nLanguage: en\n\n00:00:00.000 --> 00:00:02.000\nHello from YouTube\n"""


def test_youtube_vtt_header_metadata_is_ignored(tmp_path: Path):
    path = tmp_path / "youtube.vtt"
    path.write_text(YOUTUBE, newline="")
    html = VTTProvider().render_preview(path, "", "transcript", 1, 1000)
    assert "Hello from YouTube" in html
    assert "missing a timestamp" not in html


def test_vtt_malformed_pre_cue_block_is_rejected(tmp_path: Path):
    path = tmp_path / "bad.vtt"
    path.write_text("WEBVTT\n\nnot metadata\n\n00:00:00.000 --> 00:00:01.000\ntext\n", newline="")
    assert "cue is missing a timestamp" in VTTProvider().render_preview(
        path, "", "transcript", 1, 1000
    )


def test_vtt_transcript_has_timing_text_tags_and_voice(tmp_path: Path):
    path = tmp_path / "captions.vtt"
    path.write_text(VALID, newline="")
    html = VTTProvider().render_preview(path, "", "transcript", 1, 1000)
    assert "00:00:01.000" in html
    assert "00:00:03.500" in html
    assert "Alice:" in html
    assert "Hello world" in html
    assert "second line" in html
    assert "<c.green>" not in html


def test_vtt_raw_preserves_source(tmp_path: Path):
    path = tmp_path / "captions.vtt"
    path.write_text(VALID, newline="")
    html = VTTProvider().render_preview(path, "", "raw", 1, 1000)
    assert html_lib.escape(VALID) in html


def test_vtt_empty_and_malformed_are_safe(tmp_path: Path):
    empty = tmp_path / "empty.vtt"
    empty.write_text("WEBVTT\n\n", newline="")
    assert "no cues" in VTTProvider().render_preview(empty, "", "transcript", 1, 1000)
    bad = tmp_path / "bad.vtt"
    bad.write_text("WEBVTT\n\n00:00:00.000 --> nope\ntext\n", newline="")
    assert "Malformed WebVTT" in VTTProvider().render_preview(bad, "", "transcript", 1, 1000)
    bad_header = tmp_path / "bad-header.vtt"
    bad_header.write_text("WEBVTTX\n", newline="")
    assert "Malformed WebVTT" in VTTProvider().render_preview(
        bad_header, "", "transcript", 1, 1000
    )


def test_vtt_provider_is_registered(tmp_path: Path):
    from filemill.vfs import REGISTRY
    assert REGISTRY.get(tmp_path / "captions.vtt") is not None
