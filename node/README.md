# wakecore (Node.js)

> Open hotword detection for private voice systems.

```bash
npm install wakecore
```

```javascript
const { Runtime } = require("wakecore");

const rt = Runtime.load("hey_computer.wake");
const frame = Buffer.alloc(rt.bytesPerFrame);   // your audio frame here
const hit = rt.process(frame);
if (hit) console.log("wake!");
rt.close();
```

The reference inference binary is distributed separately.
Set `WAKECORE_NATIVE_DIR` to its location.

MIT — see [LICENSE](../LICENSE).
