"""Engine installer — downloads and unpacks the platform-specific
native binary.

Implementation lands in v0.2. This module is a placeholder that
documents the install flow.
"""
from __future__ import annotations
import platform
import sys
from pathlib import Path


def install_engine(*,
                   license_token: str,
                   target_dir: Path | None = None,
                   force: bool = False) -> int:
    """Install the native engine binary into `target_dir`.

    Default `target_dir` is `~/.wakecore/<version>/`.
    """
    from . import VERSION
    target_dir = target_dir or (Path.home() / ".wakecore" / VERSION)
    target_dir.mkdir(parents=True, exist_ok=True)

    arch = _detect_arch()
    plat = _detect_platform()
    print(f"target platform: {plat}/{arch}")
    print(f"target dir:      {target_dir}")
    print(f"license token:   {license_token[:8]}…")
    print()
    print("[ ] download   engine package from https://download.wakecore.de")
    print("[ ] verify     license + signature")
    print("[ ] decrypt    payload using license-derived key")
    print("[ ] decompress payload (zstd)")
    print("[ ] place      libwakecore_engine binary in target dir")
    print()
    print("install support not yet shipped in v0.1.")
    print("get a token at https://wakecore.de and try again with v0.2.")
    return 1


def _detect_platform() -> str:
    s = sys.platform
    if s.startswith("linux"):   return "linux"
    if s == "darwin":            return "darwin"
    if s == "win32":             return "windows"
    return s


def _detect_arch() -> str:
    m = platform.machine().lower()
    if m in ("x86_64", "amd64"):  return "x86_64"
    if m in ("arm64", "aarch64"): return "aarch64"
    if m.startswith("armv7"):     return "armv7"
    if m == "armv6l":             return "armv6"
    return m or "unknown"
