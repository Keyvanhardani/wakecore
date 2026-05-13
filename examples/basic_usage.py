"""Minimal example: open the microphone and print detections."""
from wakecore import Runtime, AudioCapture


def main() -> int:
    rt = Runtime.load("hotwords/hey_computer.wake")
    print(f"listening for {rt.wake_phrase!r}")

    try:
        with AudioCapture(rt.sample_rate, rt.frame_length) as mic:
            for frame in mic:
                hit = rt.process(frame)
                if hit:
                    print(f"  detected at {hit.timestamp:.2f}")
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        rt.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
