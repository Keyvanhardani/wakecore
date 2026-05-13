"""WakeCore — open hotword detection for private voice systems."""
from __future__ import annotations

from .format    import WakeFile, read_wake, write_wake, is_wake_file
from .runtime   import Runtime, Detection, RuntimeError as WakeRuntimeError
from .audio     import AudioCapture, AudioError

__all__ = [
    "Runtime", "Detection", "WakeRuntimeError",
    "AudioCapture", "AudioError",
    "WakeFile", "read_wake", "write_wake", "is_wake_file",
    "VERSION",
]

VERSION = "0.1.0"
