---
language:
  - de
  - en
license: mit
tags:
  - audio
  - speech
  - hotword
  - wake-word
  - voice
  - keyword-spotting
  - on-device
  - private
  - edge
pipeline_tag: audio-classification
library_name: wakecore
---

# WakeCore

> **Open hotword detection for private voice systems.**
> Lokale Hotword-Erkennung für private KI-Systeme.

WakeCore is a cross-language SDK family for embedding always-listening
hotword ("wake-word") detection into your applications. Detection runs
entirely on-device — no cloud calls, no API keys, no telemetry — so you
stay in control of the microphone signal.

**Drop a `.wake` file into your app, point WakeCore at it, and you get
on-device hotword detection.** Custom `.wake` files for your own phrases
are produced by the WakeCore generator at <https://wakecore.de>.

## Quick start

### Python

```bash
pip install wakecore[audio]
wakecore install-engine
```

```python
from wakecore import Runtime, AudioCapture

with Runtime.load("hey_computer.wake") as rt, \
     AudioCapture(rt.sample_rate, rt.frame_length) as mic:
    for frame in mic:
        if rt.process(frame):
            print("wake!")
```

### Node.js

```bash
npm install wakecore
```

```javascript
const { Runtime } = require("wakecore");
const rt = Runtime.load("hey_computer.wake");
// feed PCM-16 mono frames of rt.bytesPerFrame bytes
rt.close();
```

### Rust

```toml
[dependencies]
wakecore = "0.1"
```

```rust
let mut rt = wakecore::Runtime::load("hey_computer.wake")?;
let frame = [0i16; 512];
if rt.process(&frame)? { println!("wake!"); }
```

## Supported platforms (8 OS families, 17 binary variants)

| Family            | Architectures                                     |
|-------------------|---------------------------------------------------|
| Linux             | x86_64, i386                                      |
| macOS             | x86_64, arm64                                     |
| Windows           | amd64, i686                                       |
| Raspberry Pi      | cortex-a7, cortex-a53, arm11                      |
| ARM Linux         | a9-neon (generic ARMv7+NEON)                      |
| Android           | x86, x86_64, armeabi-v7a, arm64-v8a               |
| iOS               | universal static                                  |
| watchOS           | universal static                                  |

## What's in this repository

| Path                              | Purpose                                        |
|-----------------------------------|------------------------------------------------|
| `hotwords/*.wake`                 | Ready-to-use sample hotword files              |
| `engine/<plat>/<arch>/<ver>/`     | Native engine binary per platform              |
| `engine/<plat>/<arch>/<ver>/SHA256SUMS` | Integrity manifest                       |

## The `.wake` file format

`.wake` files are sealed binary containers — opaque to user code. The
SDK simply hands the body to the bundled inference engine. New `.wake`
files are produced by the WakeCore generator service.

## Audio format

- Sample rate: **16,000 Hz**
- Channels: **mono**
- Sample format: **16-bit signed little-endian PCM**
- Frame size: **512 samples** per `process()` call (~32 ms)

## Why WakeCore

| | WakeCore | Cloud APIs | Other open SDKs |
|-|----------|------------|------------------|
| On-device  | ✓ | ✗ | ✓ |
| No API key | ✓ | ✗ | ✓ |
| Cross-language | ✓ Python · Node.js · C · C++ · C# · Rust | varies | usually single-language |
| Free tier | ✓ first hotword free | rare | training-yourself |
| German-aware | ✓ | rarely | rarely |
| `.wake` files portable across platforms | ✓ | n/a | varies |

## Tags

`audio` · `speech` · `hotword` · `wake-word` · `keyword-spotting` ·
`voice-assistant` · `private-voice` · `german` · `on-device` ·
`edge-ai` · `iot`

## Links

- GitHub:   <https://github.com/Keyvanhardani/wakecore>
- Website:  <https://wakecore.de>
- Generator: <https://api.wakecore.de>
- License:  [MIT](https://github.com/Keyvanhardani/wakecore/blob/main/LICENSE)
