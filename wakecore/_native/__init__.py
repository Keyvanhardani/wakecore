"""Bridge to the bundled inference engine.

The native binary is distributed separately and is not part of this
repository. See `INSTALL.md` for setup.
"""
from __future__ import annotations
import ctypes
import os
import sys
from ctypes import c_int, c_short, c_uint8, byref, POINTER, Structure
from pathlib import Path
from typing import Optional

from ..format    import WakeFile
from ..runtime  import RuntimeError as _RuntimeError


_LIB_NAMES = {
    "linux":   "libwakecore_engine.so",
    "darwin":  "libwakecore_engine.dylib",
    "win32":   "wakecore_engine.dll",
}


def _resolve_lib_path() -> Path:
    name = _LIB_NAMES.get(sys.platform)
    if name is None:
        raise _RuntimeError(f"no native engine for {sys.platform!r}")

    env = os.environ.get("WAKECORE_NATIVE_DIR")
    candidates = []
    if env:
        candidates.append(Path(env) / name)
    candidates.append(Path(__file__).resolve().parent / name)
    for p in candidates:
        if p.exists():
            return p
    raise _RuntimeError(
        f"native engine not found. Set WAKECORE_NATIVE_DIR or place {name} "
        f"next to wakecore/_native/. See INSTALL.md."
    )


class _CHandle(Structure):
    pass


class _NativeBindings:
    def __init__(self, lib_path: Path):
        self._lib = ctypes.cdll.LoadLibrary(str(lib_path))
        self.open = self._bind("open",
                               [POINTER(c_uint8), c_int, POINTER(POINTER(_CHandle))],
                               c_int)
        self.feed = self._bind("feed",
                               [POINTER(_CHandle), POINTER(c_short), POINTER(c_int)],
                               c_int)
        self.shut = self._bind("close", [POINTER(_CHandle)], None)

    def _bind(self, suffix, argtypes, restype):
        for prefix in ("wakecore_", "wc_engine_", "wc_"):
            try:
                fn = getattr(self._lib, prefix + suffix)
                fn.argtypes = argtypes
                fn.restype  = restype
                return fn
            except AttributeError:
                continue
        raise _RuntimeError(f"native bridge: required symbol {suffix!r} missing")


_bindings: Optional[_NativeBindings] = None


def _get_bindings() -> _NativeBindings:
    global _bindings
    if _bindings is None:
        _bindings = _NativeBindings(_resolve_lib_path())
    return _bindings


class NativeBackend:
    def __init__(self, wake_file: WakeFile, options: dict):
        from ..runtime import SAMPLE_RATE, FRAME_LENGTH
        b = _get_bindings()

        body = wake_file.body
        body_arr = (c_uint8 * len(body))(*body)
        self._handle = POINTER(_CHandle)()
        rc = b.open(body_arr, len(body), byref(self._handle))
        if rc != 0:
            raise _RuntimeError(f"native engine open failed (rc={rc})")

        self._bindings        = b
        self._sample_rate     = SAMPLE_RATE
        self._frame_length    = FRAME_LENGTH
        self._bytes_per_frame = FRAME_LENGTH * 2
        self._pcm_buf         = (c_short * FRAME_LENGTH)()
        from ctypes import addressof
        self._pcm_addr        = addressof(self._pcm_buf)
        self._result          = c_int()

    @property
    def sample_rate(self)  -> int: return self._sample_rate
    @property
    def frame_length(self) -> int: return self._frame_length

    def process(self, frame_bytes: bytes) -> bool:
        if len(frame_bytes) != self._bytes_per_frame:
            raise _RuntimeError(
                f"frame must be {self._bytes_per_frame} bytes "
                f"(got {len(frame_bytes)})"
            )
        from ctypes import memmove
        memmove(self._pcm_addr, bytes(frame_bytes), self._bytes_per_frame)
        rc = self._bindings.feed(self._handle, self._pcm_buf, byref(self._result))
        if rc != 0:
            raise _RuntimeError(f"native engine feed failed (rc={rc})")
        return self._result.value != 0

    def close(self) -> None:
        h = getattr(self, "_handle", None)
        if h is not None:
            try: self._bindings.shut(h)
            except Exception: pass
            self._handle = None
