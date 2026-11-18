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
    int wind_pm = 0;  // how hard the wind blows (spec 08, "Wind")
    int fog_pm = 0;   // how thick the fog is (spec 08, "Fog")
};

// A season of the year (spec 08, "Seasons").
struct Season {
    std::string id;
    int days = 1;
    int tint[4] = {0, 0, 0, 0};              // r, g, b, a laid over the screen (art direction)
    std::map<std::string, int> weights;      // weather weights that replace the ones of the kinds
    std::vector<std::pair<int, int>> light;  // keyframes of its own; empty: the global ones
};

struct TimeParams {
    int day_ticks = 72000;
    std::int64_t start_tick = 0;
    std::vector<std::pair<int, int>> light;  // keyframes (time of day in permille, light in permille)
    int period_ticks = 18000;
    int fade_ticks = 600;
    int night_aggro_cut_pm = 0;  // how much full darkness shortens the aggro distance (spec 08, "The night hides you")
    int rain_aggro_cut_pm = 0;   // how much full rain shortens the aggro distance (spec 08, "Rain hides you")
    int rain_slow_pm = 0;        // how much full rain slows the creatures (spec 08, "Rain slows")
    int wind_haste_pm = 0;       // how much a full wind speeds the player (spec 08, "Wind")
    int fog_aggro_cut_pm = 0;    // how much a full fog shortens the aggro distance (spec 08, "Fog")
    int lightning_ticks = 0;     // the lightning of a storm (spec 08, "Lightning"): how often, 0: never;
    int lightning_pct = 0;       // the share of the health of the creature it strikes;
    int lightning_range_x100 = 0;  // and how far from the player
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
    int wind_pm = 0;
    int fog_pm = 0;
    int effective_light_pm = 1000;
    int season_index = -1;  // index in TimeParams::seasons, -1 without seasons
};

// Index of the season of a day, -1 when the world has no seasons.
int season_index_of(const TimeParams& params, std::int64_t day);

TimeSample sample_time(std::uint64_t seed, const TimeParams& params, std::int64_t world_ticks);

}  // namespace aether
