"""Sealed `.wake` container reader.

`.wake` files are sealed binary blobs produced by the WakeCore generator
service. This module verifies the outer frame and exposes the body as
opaque bytes; the runtime hands them to the inference backend.
"""
from __future__ import annotations
import dataclasses
import io
from pathlib import Path
from typing import Optional

_HEADER = b"WAKE"


class WakeFormatError(ValueError):
    pass


@dataclasses.dataclass
class WakeFile:
    body:           bytes
    format_version: int
    source_path:    Optional[Path] = None

    @property
    def size(self) -> int:
        return len(self.body)

    @property
    def filename(self) -> Optional[str]:
        return self.source_path.name if self.source_path else None


def is_wake_file(path: str | Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) == _HEADER
    except OSError:
        return False


def read_wake(path: str | Path) -> WakeFile:
    path = Path(path)
    with path.open("rb") as f:
        wf = _read(f)
    wf.source_path = path
    return wf


def read_wake_bytes(blob: bytes) -> WakeFile:
    return _read(io.BytesIO(blob))


def write_wake(path: str | Path, body: bytes, format_version: int = 1) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not body:
        raise WakeFormatError("body is empty")
    if format_version <= 0 or format_version > 0xFFFFFFFF:
        raise WakeFormatError("invalid format_version")
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as f:
        f.write(_HEADER)
        f.write(format_version.to_bytes(4, "little"))
        f.write(body)
    tmp.replace(path)
    return path


def _read(stream) -> WakeFile:
    head = stream.read(4)
    if head != _HEADER:
        raise WakeFormatError("not a WakeCore container")
    raw_ver = stream.read(4)
    if len(raw_ver) != 4:
        raise WakeFormatError("truncated frame")
    ver = int.from_bytes(raw_ver, "little")
    body = stream.read()
    if not body:
        raise WakeFormatError("empty body")
    return WakeFile(body=body, format_version=ver)
