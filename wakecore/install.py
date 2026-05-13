"""Engine installer — downloads the platform-specific native binary.

The binary is hosted publicly at https://download.wakecore.de/. No
authentication is required to obtain it: the engine on its own only
runs `.wake` files that already exist; new `.wake` files are produced
by the paid generator at https://api.wakecore.de.

Files are verified against a SHA-256 manifest after download.
"""
from __future__ import annotations
import hashlib
import os
import platform
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


DOWNLOAD_HOST = os.environ.get(
    "WAKECORE_DOWNLOAD_HOST", "https://download.wakecore.de"
)

# Mirrors tried in order if the primary fails.
DOWNLOAD_MIRRORS: list[str] = [
    "https://huggingface.co/Keyvanhardani/wakecore/resolve/main",
]


_LIB_FILENAME = {
    "linux":   "libwakecore_engine.so",
    "darwin":  "libwakecore_engine.dylib",
    "win32":   "wakecore_engine.dll",
}


def install_engine(*,
                   license_token: Optional[str] = None,  # kept for API stability
                   target_dir: Optional[Path] = None,
                   force: bool = False,
                   verify_sha256: bool = True) -> int:
    """Install the native engine binary for the current platform.

    Returns 0 on success, non-zero on failure.
    """
    del license_token  # not used; engine is unrestricted

    from . import VERSION

    target_dir = Path(target_dir) if target_dir else \
                 (Path.home() / ".wakecore" / VERSION)
    target_dir.mkdir(parents=True, exist_ok=True)

    plat = _detect_platform()
    arch = _detect_arch()
    lib_name = _LIB_FILENAME.get(plat)
    if lib_name is None:
        _err(f"unsupported platform {plat!r}")
        return 2

    target_path = target_dir / lib_name
    if target_path.exists() and not force:
        print(f"engine already installed at {target_path}")
        print("use --force to reinstall.")
        return 0

    rel_path = f"/engine/{plat}/{arch}/{VERSION}/{lib_name}"
    candidates = [DOWNLOAD_HOST + rel_path]
    for mirror in DOWNLOAD_MIRRORS:
        candidates.append(mirror + rel_path)

    print(f"target:   {plat}/{arch}  (sdk v{VERSION})")
    print(f"install:  {target_path}")

    tmp_path = target_path.with_suffix(target_path.suffix + ".download")
    last_err: Optional[Exception] = None
    for url in candidates:
        print(f"download: {url}")
        try:
            _download(url, tmp_path)
            if verify_sha256:
                _verify_against_manifest(plat, arch, lib_name, tmp_path)
            tmp_path.replace(target_path)
            try:
                target_path.chmod(0o755)
            except OSError:
                pass
            print("done.")
            return 0
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            last_err = e
            print(f"  failed: {e}")
            try: tmp_path.unlink()
            except OSError: pass
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"  error: {e}")
            try: tmp_path.unlink()
            except OSError: pass

    _err(f"all download candidates failed; last error: {last_err}")
    return 2


def _download(url: str, target: Path) -> None:
    req = urllib.request.Request(
        url, headers={"User-Agent": "wakecore-installer"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        with target.open("wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)


def _verify_against_manifest(plat: str, arch: str, lib_name: str, downloaded: Path) -> None:
    """Compare SHA-256 of downloaded file against the published manifest."""
    from . import VERSION

    manifest_url = (
        f"{DOWNLOAD_HOST}/engine/{plat}/{arch}/{VERSION}/SHA256SUMS"
    )
    print(f"verify:   {manifest_url}")
    try:
        req = urllib.request.Request(
            manifest_url, headers={"User-Agent": "wakecore-installer"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            manifest = r.read().decode("utf-8", "replace")
    except Exception:
        print("  (skip — manifest not reachable)")
        return

    expected: Optional[str] = None
    for line in manifest.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1].endswith(lib_name):
            expected = parts[0]
            break
    if expected is None:
        print("  (skip — no entry in manifest)")
        return

    h = hashlib.sha256()
    with downloaded.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    got = h.hexdigest()
    if got != expected:
        raise RuntimeError(f"SHA-256 mismatch: expected {expected}, got {got}")
    print(f"  ok  ({got[:16]}…)")


def _detect_platform() -> str:
    s = sys.platform
    if s.startswith("linux"):   return "linux"
    if s == "darwin":            return "darwin"
    if s == "win32":             return "win32"
    return s


def _detect_arch() -> str:
    m = platform.machine().lower()
    if m in ("x86_64", "amd64"):  return "x86_64"
    if m in ("arm64", "aarch64"): return "aarch64"
    if m.startswith("armv7"):     return "armv7"
    if m == "armv6l":             return "armv6"
    return m or "unknown"


def _err(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
