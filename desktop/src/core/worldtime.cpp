#include "core/worldtime.hpp"

#include <algorithm>

#include "core/numerics.hpp"

namespace aether {

namespace {

int light_at(const TimeParams& p, int tod) {
    const auto& keys = p.light;
    for (std::size_t i = 0; i + 1 < keys.size(); ++i) {
        const int p0 = keys[i].first;
        const int l0 = keys[i].second;
        const int p1 = keys[i + 1].first;
        const int l1 = keys[i + 1].second;
        if (p0 <= tod && tod <= p1) {
            const int span = p1 - p0;
            const int d = tod - p0;
            return l1 >= l0 ? l0 + (l1 - l0) * d / span : l0 - (l0 - l1) * d / span;
        }
    }
    return keys.empty() ? 1000 : keys.back().second;
}

const WeatherKind& kind_of(std::uint64_t seed, const TimeParams& p, std::int64_t period) {
    std::uint64_t total = 0;
    for (const WeatherKind& k : p.kinds) {
        total += static_cast<std::uint64_t>(k.weight);
    }
    const std::uint64_t roll = (hash64(seed, period, 21) >> 20) % total;
    std::uint64_t acc = 0;
    for (const WeatherKind& k : p.kinds) {
        acc += static_cast<std::uint64_t>(k.weight);
        if (roll < acc) {
            return k;
        }
    }
    return p.kinds.back();
}

}  // namespace

TimeSample sample_time(std::uint64_t seed, const TimeParams& p, std::int64_t world_ticks) {
    TimeSample s;
    s.day = world_ticks / p.day_ticks + 1;
    s.tod_pm = static_cast<int>((world_ticks % p.day_ticks) * 1000 / p.day_ticks);
    s.light_pm = light_at(p, s.tod_pm);

    const std::int64_t period = world_ticks / p.period_ticks;
    const WeatherKind& cur = kind_of(seed, p, period);
    const WeatherKind& prev = kind_of(seed, p, std::max<std::int64_t>(period - 1, 0));
    const int since = static_cast<int>(world_ticks % p.period_ticks);
    s.kind = cur.id;
    if (since >= p.fade_ticks) {
        s.rain_pm = cur.rain_pm;
        s.dim_pm = cur.dim_pm;
    } else {
        s.rain_pm = (prev.rain_pm * (p.fade_ticks - since) + cur.rain_pm * since) / p.fade_ticks;
        s.dim_pm = (prev.dim_pm * (p.fade_ticks - since) + cur.dim_pm * since) / p.fade_ticks;
    }
    s.effective_light_pm = s.light_pm * (1000 - s.dim_pm) / 1000;
    return s;
}

}  // namespace aether
