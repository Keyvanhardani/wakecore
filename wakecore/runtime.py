"""WakeCore detection runtime.

`Runtime.load(path)` constructs a runtime from a sealed `.wake` file. The
runtime hands the file body to the configured inference backend and exposes
a small high-level API for processing audio frames.
"""
from __future__ import annotations
import dataclasses
import time
from pathlib import Path
from typing import Callable, Optional, Protocol

from .format import WakeFile, read_wake


# Audio constants for the current engine version. These are fixed for the
# current generation of the inference engine and are not negotiable from
# the `.wake` file.
SAMPLE_RATE  = 16_000
FRAME_LENGTH = 512


class RuntimeError(Exception):
    pass


@dataclasses.dataclass
class Detection:
    timestamp:   float
    confidence:  float = 1.0
    frame_index: int = -1


class Backend(Protocol):
    @property
    def sample_rate(self)  -> int: ...
    @property
    def frame_length(self) -> int: ...
    def process(self, frame_bytes: bytes) -> bool: ...
    def close(self) -> None: ...


# ── stub backend (no inference; used by tests / dev environments) ───────

class _StubBackend:
    """Always returns False. Useful when the native binary is unavailable."""

    def __init__(self, _wake_file: WakeFile, _options: dict):
        pass

    @property
    def sample_rate(self)  -> int: return SAMPLE_RATE
    @property
    def frame_length(self) -> int: return FRAME_LENGTH

    def process(self, frame_bytes: bytes) -> bool:
        if len(frame_bytes) != FRAME_LENGTH * 2:
            raise RuntimeError(f"frame must be {FRAME_LENGTH*2} bytes")
        return False

    def close(self) -> None:
        pass


# ── backend registry ────────────────────────────────────────────────────

_BackendFactory = Callable[[WakeFile, dict], Backend]
_BACKENDS: dict[str, _BackendFactory] = {
    "stub": _StubBackend,
}


def register_backend(name: str, factory: _BackendFactory) -> None:
    _BACKENDS[name] = factory


def _native_factory(wf: WakeFile, options: dict) -> Backend:
    from ._native import NativeBackend
    return NativeBackend(wf, options)


_BACKENDS["native"] = _native_factory


# ── runtime ────────────────────────────────────────────────────────────

class Runtime:
    def __init__(self, backend: Backend, wake_file: WakeFile):
        self._backend     = backend
        self._wake        = wake_file
        self._frame_index = 0
        self._last_t      = 0.0
        self._cooldown_s  = 0.4

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        backend: str = "native",
        sensitivity: Optional[float] = None,
        **options,
    ) -> "Runtime":
        wf = read_wake(path)
        return cls.from_wake_file(wf, backend=backend,
                                  sensitivity=sensitivity, **options)

    @classmethod
    def from_wake_file(
        cls,
        wake_file: WakeFile,
        *,
        backend: str = "native",
        sensitivity: Optional[float] = None,
        **options,
    ) -> "Runtime":
        factory = _BACKENDS.get(backend)
        if factory is None:
            raise RuntimeError(
                f"unknown backend {backend!r}. Available: {sorted(_BACKENDS)}"
            )
        opts = dict(options)
        if sensitivity is not None:
            opts["sensitivity"] = float(sensitivity)
        return cls(factory(wake_file, opts), wake_file)

    @property
    def sample_rate(self)     -> int: return self._backend.sample_rate
    @property
    def frame_length(self)    -> int: return self._backend.frame_length
    @property
    def bytes_per_frame(self) -> int: return self.frame_length * 2

    def process(self, frame_bytes: bytes) -> Optional[Detection]:
        if len(frame_bytes) != self.bytes_per_frame:
            raise RuntimeError(
                f"frame must be {self.bytes_per_frame} bytes "
                f"(got {len(frame_bytes)})"
            )
        hit = self._backend.process(frame_bytes)
        self._frame_index += 1
        if not hit:
            return None
        now = time.monotonic()
        if now - self._last_t < self._cooldown_s:
            return None
        self._last_t = now
        return Detection(timestamp=time.time(), frame_index=self._frame_index - 1)

    def close(self) -> None:
        try:
            self._backend.close()
        except Exception:
            pass

    def __enter__(self) -> "Runtime":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
