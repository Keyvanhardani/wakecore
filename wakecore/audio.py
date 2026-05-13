"""Microphone capture — thin convenience layer on top of `sounddevice`.

Supports two patterns:

    # Iterator: yields fixed-size int16 frames
    with AudioCapture(sample_rate=16000, frame_length=512) as cap:
        for frame in cap:
            ...

    # Callback: invoked from the audio thread for each frame
    cap = AudioCapture(sample_rate=16000, frame_length=512, on_frame=fn)
    cap.start(); ...; cap.stop()

Frames are yielded as `bytes` in 16-bit little-endian PCM (mono),
matching the format the inference runtime expects.

If `sounddevice` is not installed, importing this module still works,
but constructing `AudioCapture` raises `AudioError` with a helpful
message. Useful for development on systems without audio (CI, headless
servers).
"""
from __future__ import annotations
import queue
import threading
from typing import Callable, Iterator, Optional

try:
    import sounddevice as _sd  # type: ignore
    _SD_AVAILABLE = True
except Exception:  # pragma: no cover  (covers Linux-no-portaudio scenarios)
    _sd = None
    _SD_AVAILABLE = False


class AudioError(RuntimeError):
    """Anything wrong with audio capture (device, format, …)."""


class AudioCapture:
    """A pull-based or push-based 16-bit-PCM mono microphone stream."""

    def __init__(
        self,
        sample_rate:  int = 16000,
        frame_length: int = 512,
        device:       Optional[int | str] = None,
        on_frame:     Optional[Callable[[bytes], None]] = None,
        queue_depth:  int = 32,
    ):
        if not _SD_AVAILABLE:
            raise AudioError(
                "sounddevice is not installed. Install with `pip install sounddevice` "
                "or pass audio frames manually via Runtime.process()."
            )
        if frame_length <= 0:
            raise AudioError("frame_length must be positive")
        if sample_rate <= 0:
            raise AudioError("sample_rate must be positive")

        self._sample_rate  = sample_rate
        self._frame_length = frame_length
        self._device       = device
        self._on_frame     = on_frame
        self._queue:       queue.Queue[bytes] = queue.Queue(maxsize=queue_depth)
        self._stream:      Optional["_sd.InputStream"] = None  # type: ignore[name-defined]
        self._closed       = threading.Event()

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def frame_length(self) -> int:
        return self._frame_length

    @property
    def bytes_per_frame(self) -> int:
        return self._frame_length * 2

    def _on_audio(self, indata, frames, time_info, status):  # noqa: ARG002
        if status:
            # Non-fatal; drop frame
            return
        # indata is float32 [-1, 1]; convert to int16 LE bytes
        import numpy as np
        i16 = (np.clip(indata[:, 0], -1.0, 1.0) * 32767.0).astype(np.int16)
        buf = i16.tobytes()
        if self._on_frame is not None:
            try:
                self._on_frame(buf)
            except Exception:
                pass
        else:
            try:
                self._queue.put_nowait(buf)
            except queue.Full:
                # drop the oldest to make space (latency over backlog)
                try: self._queue.get_nowait()
                except queue.Empty: pass
                try: self._queue.put_nowait(buf)
                except queue.Full: pass

    def start(self) -> None:
        if self._stream is not None:
            return
        if not _SD_AVAILABLE:
            raise AudioError("sounddevice unavailable")
        self._stream = _sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self._frame_length,
            device=self._device,
            callback=self._on_audio,
        )
        self._stream.start()

    def stop(self) -> None:
        s = self._stream
        if s is None:
            return
        try:
            s.stop(); s.close()
        finally:
            self._stream = None
            self._closed.set()

    def read(self, timeout: Optional[float] = None) -> bytes:
        """Block until the next frame is available; returns its bytes."""
        return self._queue.get(timeout=timeout)

    def __iter__(self) -> Iterator[bytes]:
        return self

    def __next__(self) -> bytes:
        if self._closed.is_set():
            raise StopIteration
        return self.read()

    def __enter__(self) -> "AudioCapture":
        self.start()
        return self

    def __exit__(self, *_exc) -> None:
        self.stop()


def list_devices() -> list[dict]:
    """Return all input-capable audio devices as dicts."""
    if not _SD_AVAILABLE:
        raise AudioError("sounddevice unavailable")
    devices = _sd.query_devices()
    return [
        {"index": i, "name": d["name"], "channels": d["max_input_channels"],
         "default_sample_rate": d["default_samplerate"]}
        for i, d in enumerate(devices) if d["max_input_channels"] > 0
    ]
