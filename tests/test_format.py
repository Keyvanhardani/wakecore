"""Round-trip tests for the sealed `.wake` container."""
from __future__ import annotations
import pytest

from wakecore.format import (
    WakeFormatError, write_wake, read_wake, read_wake_bytes, is_wake_file,
)


def test_roundtrip(tmp_path):
    body = bytes(range(256)) * 2
    p = write_wake(tmp_path / "x.wake", body)
    wf = read_wake(p)
    assert wf.body == body
    assert wf.format_version == 1
    assert wf.size == len(body)
    assert wf.filename == "x.wake"


def test_is_wake_file(tmp_path):
    good = tmp_path / "good.wake"
    bad  = tmp_path / "bad.wake"
    write_wake(good, b"x" * 16)
    bad.write_bytes(b"NOPE" + b"\x00" * 32)
    assert is_wake_file(good) is True
    assert is_wake_file(bad)  is False
    assert is_wake_file(tmp_path / "missing") is False


def test_bad_magic_rejected():
    with pytest.raises(WakeFormatError):
        read_wake_bytes(b"NOPE" + b"\x00" * 32)


def test_empty_body_rejected(tmp_path):
    with pytest.raises(WakeFormatError):
        write_wake(tmp_path / "z.wake", b"")
