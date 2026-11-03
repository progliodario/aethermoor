#include "core/worldtime.hpp"

#include <algorithm>

#include "core/numerics.hpp"

namespace aether {

namespace {

int light_at(const std::vector<std::pair<int, int>>& keys, int tod) {
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

int weight_of(const TimeParams& p, int season, const WeatherKind& k) {
    if (season >= 0) {
        const auto& weights = p.seasons[static_cast<std::size_t>(season)].weights;
        const auto found = weights.find(k.id);
        if (found != weights.end()) {
            return found->second;
        }
    }
    return k.weight;
}

const WeatherKind& kind_of(std::uint64_t seed, const TimeParams& p, std::int64_t period) {
    const int season = season_index_of(p, period * p.period_ticks / p.day_ticks + 1);  // the season of the first tick of the period
    std::uint64_t total = 0;
    for (const WeatherKind& k : p.kinds) {
        total += static_cast<std::uint64_t>(weight_of(p, season, k));
    }
    const std::uint64_t roll = (hash64(seed, period, 21) >> 20) % total;
    std::uint64_t acc = 0;
    for (const WeatherKind& k : p.kinds) {
        acc += static_cast<std::uint64_t>(weight_of(p, season, k));
        if (roll < acc) {
            return k;
        }
    }
    return p.kinds.back();
}

}  // namespace

int season_index_of(const TimeParams& p, std::int64_t day) {
    if (p.seasons.empty()) {
        return -1;
    }
    std::int64_t year = 0;
    for (const Season& s : p.seasons) {
        year += s.days;
    }
    std::int64_t d = (day - 1) % year;
    for (std::size_t i = 0; i < p.seasons.size(); ++i) {
        if (d < p.seasons[i].days) {
            return static_cast<int>(i);
        }
        d -= p.seasons[i].days;
    }
    return static_cast<int>(p.seasons.size()) - 1;
}

TimeSample sample_time(std::uint64_t seed, const TimeParams& p, std::int64_t world_ticks) {
    TimeSample s;
    s.day = world_ticks / p.day_ticks + 1;
    s.tod_pm = static_cast<int>((world_ticks % p.day_ticks) * 1000 / p.day_ticks);
    s.season_index = season_index_of(p, s.day);
    const bool own_light = s.season_index >= 0 && !p.seasons[static_cast<std::size_t>(s.season_index)].light.empty();
    s.light_pm = light_at(own_light ? p.seasons[static_cast<std::size_t>(s.season_index)].light : p.light, s.tod_pm);

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
