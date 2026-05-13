//! Sealed `.wake` container reader.

use std::fs;
use std::path::{Path, PathBuf};

use crate::Error;

const HEADER: &[u8; 4] = b"WAKE";

/// A parsed `.wake` file. `body` is opaque to this crate.
pub struct WakeFile {
    pub body:           Vec<u8>,
    pub format_version: u32,
    pub source_path:    Option<PathBuf>,
}

pub(crate) fn parse(raw: &[u8]) -> Result<WakeFile, Error> {
    if raw.len() < 8 || &raw[..4] != HEADER {
        return Err(Error::Format("not a WakeCore container".into()));
    }
    let format_version = u32::from_le_bytes([raw[4], raw[5], raw[6], raw[7]]);
    let body = raw[8..].to_vec();
    if body.is_empty() {
        return Err(Error::Format("empty body".into()));
    }
    Ok(WakeFile { body, format_version, source_path: None })
}

/// Read a `.wake` file from disk.
pub fn read_wake<P: AsRef<Path>>(path: P) -> Result<WakeFile, Error> {
    let raw = fs::read(&path)?;
    let mut wf = parse(&raw)?;
    wf.source_path = Some(path.as_ref().to_path_buf());
    Ok(wf)
}

/// Write a sealed `.wake` file.
pub fn write_wake<P: AsRef<Path>>(path: P, body: &[u8], format_version: u32)
    -> Result<PathBuf, Error>
{
    if body.is_empty() {
        return Err(Error::Format("body is empty".into()));
    }
    let mut out = Vec::with_capacity(8 + body.len());
    out.extend_from_slice(HEADER);
    out.extend_from_slice(&format_version.to_le_bytes());
    out.extend_from_slice(body);
    fs::write(&path, out)?;
    Ok(path.as_ref().to_path_buf())
}

/// Quick check whether a file looks like a `.wake` container.
pub fn is_wake_file<P: AsRef<Path>>(path: P) -> bool {
    let mut buf = [0u8; 4];
    use std::io::Read;
    fs::File::open(path).ok()
        .and_then(|mut f| f.read_exact(&mut buf).ok())
        .map(|_| &buf == HEADER)
        .unwrap_or(false)
}
