"""Feature-extraction front-end utilities.

The backend inference engine (loaded by `runtime.py`) computes its own
features internally; the helpers here are for *user-facing* analysis tools,
demos, and tests. They are deliberately small and depend only on numpy.

  - `rms_db(frame)`         : level meter in dB-FS
  - `pre_emphasis(samples)`  : classical first-order high-pass
  - `mel_filterbank(n, sr)`  : N-band mel filterbank matrix
"""
from __future__ import annotations
import math

import numpy as np


def rms_db(frame_bytes: bytes, ref: float = 1.0, floor_db: float = -90.0) -> float:
    """Return the dB-FS level of an int16-LE PCM frame."""
    n = len(frame_bytes) // 2
    if n == 0:
        return floor_db
    s = np.frombuffer(frame_bytes, dtype="<i2").astype(np.float32) / 32768.0
    rms = float(np.sqrt(np.mean(s * s)))
    if rms <= 1e-9:
        return floor_db
    return max(floor_db, 20.0 * math.log10(rms / ref))


def pre_emphasis(samples: np.ndarray, coef: float = 0.97) -> np.ndarray:
    """First-order high-pass that boosts higher frequencies, used by many
    classical speech pipelines."""
    if samples.size == 0:
        return samples
    out = np.empty_like(samples)
    out[0]  = samples[0]
    out[1:] = samples[1:] - coef * samples[:-1]
    return out


def _hz_to_mel(hz: float) -> float:
    return 2595.0 * math.log10(1.0 + hz / 700.0)


def _mel_to_hz(mel: float) -> float:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def mel_filterbank(
    n_filters:   int = 40,
    sample_rate: int = 16000,
    n_fft:       int = 512,
    f_min:       float = 0.0,
    f_max:       float | None = None,
) -> np.ndarray:
    """Return a (n_filters, n_fft//2 + 1) triangular mel filterbank matrix."""
    f_max = f_max or sample_rate / 2.0
    mel_min = _hz_to_mel(f_min)
    mel_max = _hz_to_mel(f_max)
    mel_pts = np.linspace(mel_min, mel_max, n_filters + 2)
    hz_pts  = np.array([_mel_to_hz(m) for m in mel_pts])
    bin_pts = np.floor((n_fft + 1) * hz_pts / sample_rate).astype(int)

    n_bins = n_fft // 2 + 1
    fb = np.zeros((n_filters, n_bins), dtype=np.float32)
    for k in range(n_filters):
        left   = bin_pts[k]
        center = bin_pts[k + 1]
        right  = bin_pts[k + 2]
        if center > left:
            fb[k, left:center] = (np.arange(left, center) - left) / max(1, center - left)
        if right > center:
            fb[k, center:right] = (right - np.arange(center, right)) / max(1, right - center)
    return fb


def short_time_fft(
    samples:      np.ndarray,
    frame_length: int = 512,
    hop_length:   int = 160,
    window:       str = "hann",
) -> np.ndarray:
    """Compute the magnitude STFT of mono samples. Returns (n_frames, n_bins)."""
    if window == "hann":
        win = np.hanning(frame_length).astype(np.float32)
    else:
        win = np.ones(frame_length, dtype=np.float32)

    n = (len(samples) - frame_length) // hop_length + 1
    if n <= 0:
        return np.zeros((0, frame_length // 2 + 1), dtype=np.float32)

    out = np.empty((n, frame_length // 2 + 1), dtype=np.float32)
    for i in range(n):
        chunk = samples[i * hop_length : i * hop_length + frame_length] * win
        spec = np.fft.rfft(chunk, n=frame_length)
        out[i] = np.abs(spec).astype(np.float32)
    return out
