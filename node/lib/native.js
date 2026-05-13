"use strict";

const path = require("path");
const fs   = require("fs");
const os   = require("os");

const SAMPLE_RATE  = 16000;
const FRAME_LENGTH = 512;

const LIB_FILE = {
  linux:  "libwakecore_engine.so",
  darwin: "libwakecore_engine.dylib",
  win32:  "wakecore_engine.dll",
}[process.platform];

function _resolveLibPath() {
  const candidates = [];
  if (process.env.WAKECORE_NATIVE_DIR)
    candidates.push(path.join(process.env.WAKECORE_NATIVE_DIR, LIB_FILE));
  candidates.push(path.join(__dirname, "..", "native", LIB_FILE));
  for (const p of candidates) if (fs.existsSync(p)) return p;
  throw new Error(
    `native engine ${LIB_FILE} not found. ` +
    `Set WAKECORE_NATIVE_DIR or place it next to node/native/.`
  );
}

class StubBackend {
  constructor() {}
  get sampleRate()  { return SAMPLE_RATE; }
  get frameLength() { return FRAME_LENGTH; }
  process(_frame)   { return false; }
  close()           {}
}

class NativeBackend {
  constructor(wakeFile, _opts) {
    let koffi;
    try { koffi = require("koffi"); }
    catch (e) {
      throw new Error("koffi is required for the native backend. " +
        "Install with `npm install koffi`, or use { backend: 'stub' }.");
    }
    const lib = koffi.load(_resolveLibPath());
    this._open  = lib.func("int wc_engine_open(uint8 *, int, void **)");
    this._feed  = lib.func("int wc_engine_feed(void *, int16 *, int *)");
    this._close = lib.func("void wc_engine_close(void *)");

    const enginePtr = [null];
    const rc = this._open(wakeFile.body, wakeFile.body.length, enginePtr);
    if (rc !== 0) throw new Error(`native engine open failed (rc=${rc})`);
    this._h = enginePtr[0];
    this._koffi = koffi;
  }

  get sampleRate()  { return SAMPLE_RATE; }
  get frameLength() { return FRAME_LENGTH; }

  process(frame) {
    const detected = [0];
    const rc = this._feed(this._h, frame, detected);
    if (rc !== 0) throw new Error(`feed failed (rc=${rc})`);
    return detected[0] !== 0;
  }

  close() {
    if (this._h) { this._close(this._h); this._h = null; }
  }
}

module.exports = { NativeBackend, StubBackend };
