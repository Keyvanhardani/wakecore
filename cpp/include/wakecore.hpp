/*  WakeCore C++ wrapper — header-only, zero allocations on the hot path.
 *
 *  Requires linking against the WakeCore native engine binary.
 *  Include the C header (`wakecore.h`) before this one or via -I include/.
 */

#ifndef WAKECORE_HPP
#define WAKECORE_HPP

#include "wakecore.h"
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace wakecore {

class Error : public std::runtime_error {
public:
    explicit Error(wc_status_t status)
        : std::runtime_error(wc_status_to_string(status)), status_(status) {}
    wc_status_t status() const noexcept { return status_; }
private:
    wc_status_t status_;
};

class Runtime {
public:
    explicit Runtime(const std::uint8_t *body, int body_len) {
        wc_engine_t *e = nullptr;
        const auto s = wc_engine_open(body, body_len, &e);
        if (s != WC_OK) throw Error(s);
        engine_.reset(e);
    }

    explicit Runtime(const std::vector<std::uint8_t> &body)
        : Runtime(body.data(), static_cast<int>(body.size())) {}

    Runtime(Runtime &&) noexcept            = default;
    Runtime &operator=(Runtime &&) noexcept = default;
    Runtime(const Runtime &)                = delete;
    Runtime &operator=(const Runtime &)     = delete;

    int sample_rate()  const noexcept { return wc_sample_rate(); }
    int frame_length() const noexcept { return wc_frame_length(); }

    bool process(const std::int16_t *frame) {
        int detected = 0;
        const auto s = wc_engine_feed(engine_.get(), frame, &detected);
        if (s != WC_OK) throw Error(s);
        return detected != 0;
    }

    void set_sensitivity(float sensitivity) {
        const auto s = wc_engine_set_sensitivity(engine_.get(), sensitivity);
        if (s != WC_OK) throw Error(s);
    }

private:
    struct Deleter { void operator()(wc_engine_t *e) const noexcept {
        if (e) wc_engine_close(e);
    } };
    std::unique_ptr<wc_engine_t, Deleter> engine_;
};

}  // namespace wakecore

#endif  // WAKECORE_HPP
