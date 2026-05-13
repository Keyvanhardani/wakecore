"""WakeCore command-line interface."""
from __future__ import annotations
import argparse
import os
import sys
import time
from pathlib import Path


def _cmd_check(args: argparse.Namespace) -> int:
    from .format import is_wake_file, read_wake, WakeFormatError
    if not is_wake_file(args.path):
        print(f"{args.path}: not a WakeCore container", file=sys.stderr)
        return 2
    try:
        wf = read_wake(args.path)
    except WakeFormatError as e:
        print(f"{args.path}: {e}", file=sys.stderr)
        return 2
    print(f"{args.path}: OK  (format v{wf.format_version}, {wf.size} bytes)")
    return 0


def _cmd_devices(_args: argparse.Namespace) -> int:
    from .audio import list_devices, AudioError
    try:
        for d in list_devices():
            print(f"  [{d['index']}] {d['name']} ({d['channels']} ch, "
                  f"{int(d['default_sample_rate'])} Hz)")
    except AudioError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


def _cmd_listen(args: argparse.Namespace) -> int:
    from .runtime import Runtime
    from .audio   import AudioCapture, AudioError
    try:
        rt = Runtime.load(args.wake_file, sensitivity=args.sensitivity,
                          backend=args.backend)
    except Exception as e:
        print(f"failed to load runtime: {e}", file=sys.stderr)
        return 2

    print(f"listening   sample_rate={rt.sample_rate} Hz, frame={rt.frame_length}")
    print("press Ctrl+C to stop\n")

    try:
        with AudioCapture(rt.sample_rate, rt.frame_length, device=args.device) as mic:
            for frame in mic:
                hit = rt.process(frame)
                if hit:
                    t = time.strftime("%H:%M:%S", time.localtime(hit.timestamp))
                    print(f"  [{t}] detected  (frame={hit.frame_index})")
    except KeyboardInterrupt:
        print("\nstopping")
        return 0
    except AudioError as e:
        print(f"audio error: {e}", file=sys.stderr)
        return 2
    finally:
        rt.close()
    return 0


def _cmd_install_engine(args: argparse.Namespace) -> int:
    """Download + install the native engine binary for the current platform.

    The engine is publicly hosted at https://download.wakecore.de — no
    license token needed for the engine itself; only the generator
    service (https://api.wakecore.de) requires a paid plan.
    """
    from .install import install_engine
    return install_engine(
        target_dir=args.target_dir,
        force=args.force,
        verify_sha256=not args.no_verify,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wakecore",
                                     description="WakeCore CLI — hotword detection")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_c = sub.add_parser("check", help="verify a .wake file is well-formed")
    p_c.add_argument("path", type=Path)
    p_c.set_defaults(func=_cmd_check)

    p_d = sub.add_parser("devices", help="list audio input devices")
    p_d.set_defaults(func=_cmd_devices)

    p_l = sub.add_parser("listen", help="listen on the microphone for a hotword")
    p_l.add_argument("wake_file", type=Path)
    p_l.add_argument("--sensitivity", type=float, default=None)
    p_l.add_argument("--backend", default="native")
    p_l.add_argument("--device", default=None)
    p_l.set_defaults(func=_cmd_listen)

    p_i = sub.add_parser("install-engine",
                         help="download + install the native engine binary")
    p_i.add_argument("--target-dir", type=Path, default=None,
                     help="install path (default: ~/.wakecore/<version>/)")
    p_i.add_argument("--force", action="store_true",
                     help="overwrite an existing installation")
    p_i.add_argument("--no-verify", action="store_true",
                     help="skip SHA-256 verification of the download")
    p_i.set_defaults(func=_cmd_install_engine)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
