//! WakeCore — open hotword detection for private voice systems.
//!
//! High-level Rust API around the bundled native engine.
//!
//! ```no_run
//! use wakecore::Runtime;
//!
//! let mut rt = Runtime::load("hey_computer.wake")?;
//! let frame = [0i16; 512];
//! if rt.process(&frame)? {
//!     println!("wake!");
//! }
//! # Ok::<(), wakecore::Error>(())
//! ```

#![deny(missing_docs)]

use std::fs;
use std::path::Path;
use thiserror::Error;

mod format;
#[cfg(feature = "native")]
mod ffi;

pub use format::{WakeFile, read_wake, write_wake, is_wake_file};

/// Native sample rate of the engine (16 kHz).
pub const SAMPLE_RATE: i32 = 16_000;

/// Number of int16 samples expected per `process()` call.
pub const FRAME_LENGTH: i32 = 512;

/// Errors returned by the SDK.
#[derive(Debug, Error)]
pub enum Error {
    /// I/O error reading or writing a `.wake` file.
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// The file is not a well-formed WakeCore container.
    #[error("format error: {0}")]
    Format(String),

    /// The native engine returned an error.
    #[error("engine error (code {0})")]
    Engine(i32),
}

/// A detection runtime bound to one `.wake` file.
pub struct Runtime {
    #[cfg(feature = "native")]
    inner: ffi::Engine,
}

impl Runtime {
    /// Load a `.wake` file and initialise the native engine.
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, Error> {
        let raw = fs::read(path)?;
        let wf  = format::parse(&raw)?;
        Self::from_body(&wf.body)
    }

    /// Construct from the raw container body (bytes after the outer frame).
    pub fn from_body(body: &[u8]) -> Result<Self, Error> {
        #[cfg(feature = "native")]
        {
            Ok(Self { inner: ffi::Engine::open(body)? })
        }
        #[cfg(not(feature = "native"))]
        {
            let _ = body;
            Err(Error::Engine(-1))
        }
    }

    /// Process a single mono int16 frame of length `FRAME_LENGTH`.
    pub fn process(&mut self, frame: &[i16]) -> Result<bool, Error> {
        if frame.len() != FRAME_LENGTH as usize {
            return Err(Error::Format(
                format!("frame must be {} samples", FRAME_LENGTH)
            ));
        }
        #[cfg(feature = "native")]
        {
            self.inner.feed(frame)
        }
        #[cfg(not(feature = "native"))]
        {
            Ok(false)
        }
    }
}
