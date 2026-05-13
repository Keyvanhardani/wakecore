"use strict";

const { readWake } = require("./format");
const { NativeBackend, StubBackend } = require("./native");

const COOLDOWN_MS = 400;

class Runtime {
  static load(path, opts = {}) {
    const wf = readWake(path);
    const kind = opts.backend || "native";
    const backend = kind === "stub" ? new StubBackend(wf, opts)
                                    : new NativeBackend(wf, opts);
    return new Runtime(backend, wf);
  }

  constructor(backend, wakeFile) {
    this._b = backend;
    this._w = wakeFile;
    this._frame = 0;
    this._lastHit = 0;
  }

  get sampleRate()    { return this._b.sampleRate; }
  get frameLength()   { return this._b.frameLength; }
  get bytesPerFrame() { return this.frameLength * 2; }

  process(frame) {
    if (!Buffer.isBuffer(frame) || frame.length !== this.bytesPerFrame)
      throw new Error(`frame must be ${this.bytesPerFrame} bytes`);
    const hit = this._b.process(frame);
    this._frame++;
    if (!hit) return null;
    const now = Date.now();
    if (now - this._lastHit < COOLDOWN_MS) return null;
    this._lastHit = now;
    return {
      timestamp:  now / 1000,
      confidence: 1.0,
      frameIndex: this._frame - 1,
    };
  }

  close() {
    try { this._b.close(); } catch {}
  }
}

module.exports = { Runtime };
