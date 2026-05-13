"use strict";
const fs = require("fs");

const HEADER = Buffer.from("WAKE", "ascii");

class WakeFormatError extends Error {
  constructor(msg) { super(msg); this.name = "WakeFormatError"; }
}

function isWakeFile(path) {
  try {
    const fd = fs.openSync(path, "r");
    try {
      const buf = Buffer.alloc(4);
      fs.readSync(fd, buf, 0, 4, 0);
      return buf.equals(HEADER);
    } finally { fs.closeSync(fd); }
  } catch { return false; }
}

function _parse(buf) {
  if (buf.length < 8 || !buf.slice(0, 4).equals(HEADER))
    throw new WakeFormatError("not a WakeCore container");
  const version = buf.readUInt32LE(4);
  const body    = buf.slice(8);
  if (body.length === 0) throw new WakeFormatError("empty body");
  return { body, formatVersion: version };
}

function readWake(path) {
  const buf = fs.readFileSync(path);
  const { body, formatVersion } = _parse(buf);
  return {
    body, formatVersion,
    sourcePath: path,
    size:       body.length,
    filename:   path.split(/[\\/]/).pop(),
  };
}

function writeWake(path, body, formatVersion = 1) {
  if (!Buffer.isBuffer(body)) body = Buffer.from(body);
  if (body.length === 0) throw new WakeFormatError("body is empty");
  if (!Number.isInteger(formatVersion) || formatVersion <= 0 || formatVersion > 0xFFFFFFFF)
    throw new WakeFormatError("invalid format_version");

  const ver = Buffer.alloc(4);
  ver.writeUInt32LE(formatVersion, 0);
  const out = Buffer.concat([HEADER, ver, body]);
  const tmp = path + ".tmp";
  fs.writeFileSync(tmp, out);
  fs.renameSync(tmp, path);
  return path;
}

module.exports = { readWake, writeWake, isWakeFile, WakeFormatError };
