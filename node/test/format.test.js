"use strict";
const test    = require("node:test");
const assert  = require("node:assert/strict");
const fs      = require("fs");
const os      = require("os");
const path    = require("path");

const { readWake, writeWake, isWakeFile, WakeFormatError } = require("..");

function tmp() {
  return path.join(os.tmpdir(), `wc-${Date.now()}-${Math.random().toString(36).slice(2)}.wake`);
}

test("round-trip", () => {
  const p = tmp();
  const body = Buffer.from([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  writeWake(p, body);
  const wf = readWake(p);
  assert.equal(wf.formatVersion, 1);
  assert.ok(wf.body.equals(body));
  fs.unlinkSync(p);
});

test("isWakeFile / bad magic", () => {
  const p = tmp();
  fs.writeFileSync(p, Buffer.from("NOPE\x00\x00\x00\x00stuff"));
  assert.equal(isWakeFile(p), false);
  assert.throws(() => readWake(p), WakeFormatError);
  fs.unlinkSync(p);
});

test("empty body rejected", () => {
  assert.throws(() => writeWake(tmp(), Buffer.alloc(0)), WakeFormatError);
});
