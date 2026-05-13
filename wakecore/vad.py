"""Cheap voice-activity detection — useful as a pre-filter to skip silent
frames before they reach the main runtime. Two heuristics:

    EnergyVAD  : straightforward RMS threshold with a brief hangover
    ZeroCrossVAD : zero-crossing rate (useful for cheap whisper detection)

Both share the `vad.process(frame_bytes) -> bool` interface.

Neither is as accurate as a learned VAD (e.g. WebRTC, Silero). They are
intentionally tiny and dependency-free.
"""
from __future__ import annotations
import struct
from typing import Protocol


class VADProtocol(Protocol):
    sample_rate: int

    def process(self, frame_bytes: bytes) -> bool: ...
    def reset(self) -> None: ...


def _pcm16_to_float_squared_sum(frame: bytes) -> tuple[float, int]:
    """Sum of x^2 over the int16 frame, plus count. Used by RMS calculations."""
    n = len(frame) // 2
    if n == 0:
        return 0.0, 0
    samples = struct.unpack(f"<{n}h", frame)
    s = 0.0
    for x in samples:
        f = x / 32768.0
        s += f * f
    return s, n


class EnergyVAD:
    """RMS-threshold VAD with a tunable hangover (seconds of "still speaking"
    after the energy drops below the threshold).
    """

    def __init__(
        self,
        sample_rate:    int = 16000,
        frame_length:   int = 512,
        threshold:      float = 0.01,
        hangover_sec:   float = 0.4,
    ):
        self.sample_rate  = sample_rate
        self.frame_length = frame_length
        self.threshold    = threshold
        self._hangover_frames = max(1, int(hangover_sec * sample_rate / frame_length))
        self._remaining   = 0

    def process(self, frame_bytes: bytes) -> bool:
        ss, n = _pcm16_to_float_squared_sum(frame_bytes)
        rms = (ss / n) ** 0.5 if n else 0.0
        if rms >= self.threshold:
            self._remaining = self._hangover_frames
            return True
        if self._remaining > 0:
            self._remaining -= 1
            return True
        return False

    def reset(self) -> None:
        self._remaining = 0


class ZeroCrossVAD:
    """Counts zero crossings per frame; useful when energy alone is misleading
    (e.g. ambient hum vs. soft speech).
    """

    def __init__(
        self,
        sample_rate:  int = 16000,
        frame_length: int = 512,
        zcr_min:      int = 10,
        zcr_max:      int = 200,
        threshold:    float = 0.005,
    ):
        self.sample_rate  = sample_rate
        self.frame_length = frame_length
        self.zcr_min      = zcr_min
        self.zcr_max      = zcr_max
        self.threshold    = threshold

    def process(self, frame_bytes: bytes) -> bool:
        n = len(frame_bytes) // 2
        if n < 2:
            return False
        samples = struct.unpack(f"<{n}h", frame_bytes)
        crossings = 0
        for i in range(1, n):
            if (samples[i - 1] >= 0) != (samples[i] >= 0):
                crossings += 1
        if not (self.zcr_min <= crossings <= self.zcr_max):
            return False
        ss = sum((x / 32768.0) ** 2 for x in samples)
        rms = (ss / n) ** 0.5
        return rms >= self.threshold

    def reset(self) -> None:
        pass
