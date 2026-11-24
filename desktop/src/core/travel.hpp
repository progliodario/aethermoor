#pragma once

// Travellers walk (spec 07, "Travellers walk"): where a traveller is at a tick of the day. Integer arithmetic in 1/256
// of a tile; the same in tools/reference/story.py (traveller_position) and in Kotlin (core/sim/Travel.kt).

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace aether {

// How a traveller walks between its stops: it arrives by `arrive_pm` of the day, leaves at `depart_pm`, and walks
// `speed_x256` / 256 of a tile per tick. A speed of 0: it stands at its stop all day.
struct TravellerWalk {
    int arrive_pm = 0;
    int depart_pm = 1000;
    std::int64_t speed_x256 = 0;
};

// The integer square root of v, rounded down (0 for v <= 0); the correction makes it exact on every platform.
inline std::int64_t isqrt64(std::int64_t v) {
    if (v <= 0) {
        return 0;
    }
    auto r = static_cast<std::int64_t>(std::sqrt(static_cast<double>(v)));
    while (r > 0 && r * r > v) {
        --r;
    }
    while ((r + 1) * (r + 1) <= v) {
        ++r;
    }
    return r;
}

// A position in tiles as an integer of 1/256 of a tile: floor(v * 256 + 0.5).
inline std::int64_t to_x256(float v) {
    return static_cast<std::int64_t>(std::floor(static_cast<double>(v) * 256.0 + 0.5));
}

// Where a traveller with `route` is on `day` at the tick `tick` of a day of `day_ticks` ticks (spec 07, "Travellers
// walk"): at its stop of the day, or on its way in from the stop before or out toward the stop after, never past the
// middle.
inline std::pair<float, float> traveller_position(const std::vector<std::pair<float, float>>& route,
                                                  const TravellerWalk& walk, std::int64_t day, std::int64_t tick,
                                                  std::int64_t day_ticks) {
    const auto n = static_cast<std::int64_t>(route.size());
    const std::int64_t s = ((day - 1) % n + n) % n;
    const std::pair<float, float>& here = route[static_cast<std::size_t>(s)];
    if (walk.speed_x256 <= 0 || day_ticks <= 0 || n < 2) {
        return here;
    }
    const std::int64_t arrive = day_ticks * walk.arrive_pm / 1000;
    const std::int64_t depart = day_ticks * walk.depart_pm / 1000;
    std::int64_t walked = 0;
    std::int64_t other_index = s;
    if (tick < arrive) {  // still on its way in, from the stop of the day before
        other_index = (s - 1 + n) % n;
        walked = walk.speed_x256 * (arrive - tick);
    } else if (tick >= depart) {  // on its way out, toward the stop of the day after
        other_index = (s + 1) % n;
        walked = walk.speed_x256 * (tick - depart);
    }
    const std::pair<float, float>& other = route[static_cast<std::size_t>(other_index)];
    const std::int64_t hx = to_x256(here.first);
    const std::int64_t hy = to_x256(here.second);
    const std::int64_t dx = to_x256(other.first) - hx;
    const std::int64_t dy = to_x256(other.second) - hy;
    const std::int64_t length = isqrt64(dx * dx + dy * dy);
    if (walked <= 0 || length == 0) {
        return here;
    }
    const std::int64_t w = std::min(walked, length / 2);
    return {static_cast<float>(hx + dx * w / length) / 256.0F, static_cast<float>(hy + dy * w / length) / 256.0F};
}

}  // namespace aether
