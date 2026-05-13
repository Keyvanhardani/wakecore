# WakeCore

> Open hotword detection for private voice systems.
> Lokale Hotword-Erkennung für private KI-Systeme.

WakeCore is a cross-language SDK family for on-device hotword
("wake-word") detection. Drop a `.wake` file into your app, point
WakeCore at it, and you get always-listening detection with no cloud
calls, no API keys, no telemetry.

## Languages

| Language | Path | Package |
|----------|------|---------|
| Python   | [`wakecore/`](wakecore/) (root)   | `pip install wakecore`      |
| Node.js  | [`node/`](node/)                  | `npm install wakecore`      |
| C        | [`include/wakecore.h`](include/)  | use directly                |
| C++      | [`cpp/`](cpp/) (header-only)      | use directly                |
| Rust     | [`rust/`](rust/)                  | `cargo add wakecore`        |
| C# / .NET| [`csharp/`](csharp/)              | NuGet `WakeCore`            |

All languages call into the same native engine binary, which is
distributed separately. See [hotwords/](hotwords/) for sample `.wake`
files you can use to verify your setup.

## Quick start (Python)

```bash
pip install wakecore[audio]
```

```python
from wakecore import Runtime, AudioCapture

with Runtime.load("hotwords/hey_computer.wake") as rt, \
     AudioCapture(rt.sample_rate, rt.frame_length) as mic:
    for frame in mic:
        if rt.process(frame):
            print("wake!")
```

## Quick start (Node.js)

```bash
npm install wakecore
```

```javascript
const { Runtime } = require("wakecore");

const rt = Runtime.load("hotwords/hey_computer.wake");
// feed PCM-16 mono frames of rt.bytesPerFrame bytes
rt.close();
```

## Quick start (Rust)

```toml
# Cargo.toml
[dependencies]
wakecore = "0.1"
```

```rust
let mut rt = wakecore::Runtime::load("hotwords/hey_computer.wake")?;
let frame = [0i16; 512];
if rt.process(&frame)? { println!("wake!"); }
```

`.wake` files are produced by the WakeCore generator service.

## License

MIT — see [LICENSE](LICENSE).
