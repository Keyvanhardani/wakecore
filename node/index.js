/**
 * WakeCore — JavaScript/Node.js SDK.
 *
 * Loads `.wake` hotword containers and runs detection on streamed PCM
 * audio. Requires the bundled native engine binary; see INSTALL for
 * setup.
 */
"use strict";

const { Runtime }     = require("./lib/runtime");
const { readWake, writeWake, isWakeFile, WakeFormatError }
                       = require("./lib/format");

const VERSION = "0.1.0";
const SAMPLE_RATE  = 16000;
const FRAME_LENGTH = 512;

module.exports = {
  VERSION,
  SAMPLE_RATE,
  FRAME_LENGTH,
  Runtime,
  readWake,
  writeWake,
  isWakeFile,
  WakeFormatError,
};
