//! FFI bridge to the native engine.

use std::os::raw::{c_int, c_void};

use crate::Error;

#[repr(C)]
struct WcEngine {
    _private: [u8; 0],
}

extern "C" {
    fn wc_engine_open(body: *const u8, body_len: c_int, engine: *mut *mut WcEngine) -> c_int;
    fn wc_engine_feed(engine: *mut WcEngine, frame: *const i16, detected: *mut c_int) -> c_int;
    fn wc_engine_close(engine: *mut WcEngine);
}

pub(crate) struct Engine {
    handle: *mut WcEngine,
}

impl Engine {
    pub fn open(body: &[u8]) -> Result<Self, Error> {
        let mut h: *mut WcEngine = std::ptr::null_mut();
        let rc = unsafe { wc_engine_open(body.as_ptr(), body.len() as c_int, &mut h) };
        if rc != 0 || h.is_null() {
            return Err(Error::Engine(rc));
        }
        Ok(Self { handle: h })
    }

    pub fn feed(&mut self, frame: &[i16]) -> Result<bool, Error> {
        let mut detected: c_int = 0;
        let rc = unsafe { wc_engine_feed(self.handle, frame.as_ptr(), &mut detected) };
        if rc != 0 {
            return Err(Error::Engine(rc));
        }
        Ok(detected != 0)
    }
}

impl Drop for Engine {
    fn drop(&mut self) {
        if !self.handle.is_null() {
            unsafe { wc_engine_close(self.handle) };
            self.handle = std::ptr::null_mut();
        }
    }
}

// SAFETY: the native engine is documented to be thread-compatible per handle.
unsafe impl Send for Engine {}
