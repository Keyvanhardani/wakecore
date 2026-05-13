/*  WakeCore — public C ABI for the bundled hotword inference engine.
 *
 *  All language bindings (Python, Node.js, C#, Rust, C++…) call into this
 *  ABI. The ABI is implemented by the closed-source `libwakecore_engine`
 *  binary; this header is the public contract.
 *
 *  Audio format: 16-bit signed little-endian PCM, mono, 16000 Hz.
 *
 *  Lifecycle:
 *      wc_engine_open()  →  wc_engine_feed()*  →  wc_engine_close()
 */

#ifndef WAKECORE_H
#define WAKECORE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define WAKECORE_VERSION       "0.1.0"
#define WAKECORE_SAMPLE_RATE   16000
#define WAKECORE_FRAME_LENGTH  512

typedef struct wc_engine wc_engine_t;

typedef enum {
    WC_OK            = 0,
    WC_ERR_INVALID   = 1,
    WC_ERR_IO        = 2,
    WC_ERR_NOMEM     = 3,
    WC_ERR_INTERNAL  = 4,
    WC_ERR_FORMAT    = 5,
} wc_status_t;

/* Open a sealed `.wake` container.
 *
 *   body, body_len : bytes after the outer frame header (i.e. starting at
 *                    file offset 8). Must remain valid until *engine is
 *                    closed (or be copied internally — caller-agnostic).
 *   engine         : on success, receives a handle. Free with wc_engine_close().
 */
wc_status_t wc_engine_open(const uint8_t *body,
                           int            body_len,
                           wc_engine_t  **engine);

/* Feed exactly WAKECORE_FRAME_LENGTH int16 samples.
 *   detected : on success, set to 1 if the hotword fired in this frame,
 *              else 0. Detection events are not buffered.
 */
wc_status_t wc_engine_feed(wc_engine_t   *engine,
                           const int16_t *frame,
                           int           *detected);

/* Release all resources held by the engine handle. */
void wc_engine_close(wc_engine_t *engine);

/* Optional: set detection sensitivity in [0.0, 1.0]. */
wc_status_t wc_engine_set_sensitivity(wc_engine_t *engine, float sensitivity);

/* Library metadata. */
const char *wc_version(void);
int         wc_sample_rate(void);
int         wc_frame_length(void);
const char *wc_status_to_string(wc_status_t status);

#ifdef __cplusplus
}  /* extern "C" */
#endif

#endif  /* WAKECORE_H */
