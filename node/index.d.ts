// Type declarations for the WakeCore Node.js SDK.

export const VERSION:      string;
export const SAMPLE_RATE:  number;
export const FRAME_LENGTH: number;

export interface Detection {
  timestamp:  number;   /* unix epoch seconds */
  confidence: number;
  frameIndex: number;
}

export interface WakeFile {
  body:           Buffer;
  formatVersion:  number;
  sourcePath:     string | null;
  size:           number;
  filename:       string | null;
}

export class WakeFormatError extends Error {}

export function readWake(path: string): WakeFile;
export function writeWake(path: string, body: Buffer, formatVersion?: number): string;
export function isWakeFile(path: string): boolean;

export class Runtime {
  static load(path: string, opts?: { sensitivity?: number; backend?: string }): Runtime;
  readonly sampleRate:    number;
  readonly frameLength:   number;
  readonly bytesPerFrame: number;
  process(frame: Buffer): Detection | null;
  close(): void;
}
