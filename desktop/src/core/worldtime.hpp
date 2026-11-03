#pragma once

// World time, light and weather. Spec: docs/spec/08-world-time.md. Reference: tools/reference/worldtime.py.
// Integer arithmetic only: no floating point in this module.

#include <cstdint>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace aether {

struct WeatherKind {
    std::string id;
    int weight = 1;
    int rain_pm = 0;
    int dim_pm = 0;
};

// A season of the year (spec 08, "Seasons").
struct Season {
    std::string id;
    int days = 1;
    int tint[4] = {0, 0, 0, 0};                        // r, g, b, a laid over the screen (art direction)
    std::map<std::string, int> weights;                // weather weights that replace the ones of the kinds
    std::vector<std::pair<int, int>> light;            // keyframes of its own; empty: the global ones
};

struct TimeParams {
    int day_ticks = 72000;
    std::int64_t start_tick = 0;
    std::vector<std::pair<int, int>> light;  // keyframes (time of day in permille, light in permille)
    int period_ticks = 18000;
    int fade_ticks = 600;
    std::vector<WeatherKind> kinds;
    std::vector<Season> seasons;  // empty: no seasons
};

struct TimeSample {
    std::int64_t day = 1;
    int tod_pm = 0;  // 0 = midnight, 500 = noon
    int light_pm = 1000;
    std::string kind;
    int rain_pm = 0;
    int dim_pm = 0;
    int effective_light_pm = 1000;
    int season_index = -1;  // index in TimeParams::seasons, -1 without seasons
};

// Index of the season of a day, -1 when the world has no seasons.
int season_index_of(const TimeParams& params, std::int64_t day);

TimeSample sample_time(std::uint64_t seed, const TimeParams& params, std::int64_t world_ticks);

}  // namespace aether
