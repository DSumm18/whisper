import logging
import tempfile
from pathlib import Path

import pytest

from app import output


def test_send_transcript_success(tmp_path):
    destination = tmp_path / "transcript.txt"
    result = output.send_transcript("hello", destination)

    assert result == destination
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "hello"


def test_send_transcript_unwritable_cache(monkeypatch, tmp_path, caplog):
    destination = tmp_path / "cache" / "transcript.txt"

    original_mkdir = Path.mkdir
    original_write_text = Path.write_text

    def failing_mkdir(self, *args, **kwargs):
        if self == destination.parent:
            raise PermissionError("cannot create directory")
        return original_mkdir(self, *args, **kwargs)

    def failing_write(self, *args, **kwargs):
        if self == destination:
            raise PermissionError("cannot write file")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)
    monkeypatch.setattr(Path, "write_text", failing_write)

    copied = []

    def clipboard_success(text: str) -> bool:
        copied.append(text)
        return True

    caplog.set_level(logging.WARNING)
    result = output.send_transcript(
        "fallback text", destination, clipboard_copier=clipboard_success
    )

    assert copied == ["fallback text"]
    assert result is not None
    assert result != destination
    assert result.name == destination.name
    assert result.parent == Path(tempfile.gettempdir())

    messages = "\n".join(record.message for record in caplog.records)
    assert "fallback location" in messages
    assert str(result) in messages


def test_fallback_logs_when_disk_and_clipboard_fail(monkeypatch, tmp_path, caplog):
    destination = tmp_path / "transcript.txt"

    def always_fail_write(self, *args, **kwargs):
        raise PermissionError("no disk access")

    def noop_mkdir(self, *args, **kwargs):
        return None

    monkeypatch.setattr(Path, "write_text", always_fail_write)
    monkeypatch.setattr(Path, "mkdir", noop_mkdir)

    def clipboard_failure(_: str) -> bool:
        raise RuntimeError("clipboard offline")

    caplog.set_level(logging.WARNING)
    result = output.send_transcript(
        "content", destination, clipboard_copier=clipboard_failure
    )

    assert result is None
    messages = "\n".join(record.message for record in caplog.records)
    assert "Failed to store transcript on disk and copy it to the clipboard" in messages
    assert "fallback location" in messages


@pytest.mark.parametrize("clipboard_returns", [True, False])
def test_default_fallback_handler_attempts_clipboard(monkeypatch, clipboard_returns):
    destination = Path("/unwritable/transcript.txt")

    def always_fail_write(self, *args, **kwargs):
        raise PermissionError("no disk access")

    def noop_mkdir(self, *args, **kwargs):
        return None

    monkeypatch.setattr(Path, "write_text", always_fail_write)
    monkeypatch.setattr(Path, "mkdir", noop_mkdir)

    called = {}

    def clipboard_mock(text: str) -> bool:
        called.setdefault("count", 0)
        called["count"] += 1
        return clipboard_returns

    output.default_fallback_handler(
        "transcript", destination, clipboard_copier=clipboard_mock
    )

    assert called["count"] == 1
