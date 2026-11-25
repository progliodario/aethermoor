#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "data/pack.hpp"
#include "data/world_data.hpp"
#include "sim/chunk_store.hpp"
#include "sim/combat_loader.hpp"
#include "sim/world.hpp"
#include "sim/world_map.hpp"
#include "vector/quality.hpp"
#include "vector/recipe.hpp"

// The budgets of the simulation (docs/design/performance.md; item C4.2 of the operating program). The budgets are wide:
// they catch a change that makes the generation of the world or a tick many times slower, not a few percent. The
// numbers go to performance.txt in the folder of the build, which the CI prints.
TEST_CASE("performance: the world and the ticks stay within their budgets", "[performance]") {
    using Clock = std::chrono::steady_clock;
    constexpr int kWarmUpWindows = 4;
    constexpr int kWindows = 12;
    constexpr int kChunksPerWindow = 25;
    constexpr int kWarmUpTicks = 120;
    constexpr int kTicks = 600;
    constexpr double kChunkBudgetMs = 25.0;  // wide budgets: a frame of 60 Hz is 16.7 ms
    constexpr double kTickBudgetMs = 4.0;

    const std::filesystem::path root = AETHER_REPO_ROOT;
    std::vector<std::string> errors;
    auto pack = aether::load_pack(root / "data" / "base", errors);
    REQUIRE(errors.empty());
    REQUIRE(pack.has_value());
    std::string error;
    auto params = aether::load_world_params(*pack, "base:world/overworld", error);
    INFO(error);
    REQUIRE(params.has_value());
    auto tileset = aether::parse_tileset(*pack->read_document("base:tileset/overworld"), error);
    REQUIRE(tileset.has_value());

    // the chunks: windows of 5 x 5 chunks far from each other, so that every chunk is generated anew
    aether::ChunkStore store(*params, 42, *tileset);
    for (int i = 0; i < kWarmUpWindows; ++i) {
        store.keep_around(100 + i * 5, 60);
    }
    const auto chunk_start = Clock::now();
    for (int i = 0; i < kWindows; ++i) {
        store.keep_around(160 + i * 5, 80);
    }
    const double chunk_ms = std::chrono::duration<double, std::milli>(Clock::now() - chunk_start).count() /
                            static_cast<double>(kWindows * kChunksPerWindow);

    // the ticks: the player walks east through the streamed world for ten seconds
    const aether::TileMap map = aether::make_stream_map(*params);
    auto setup = aether::load_combat_setup(*pack, map, "base:protagonist/ren", 42, error);
    INFO(error);
    REQUIRE(setup.has_value());
    for (const std::string& enemy : aether::world_enemy_ids(*params)) {
        auto def = aether::load_enemy_def(*pack, enemy, error);
        REQUIRE(def.has_value());
        setup->stream_enemies.emplace(enemy, std::move(*def));
    }
    aether::WorldSim sim(map, *tileset, 0.0F, *setup, aether::StreamConfig{*params, 42});
    for (int i = 0; i < kWarmUpTicks; ++i) {
        sim.tick(1.0F, 0.0F, false);
    }
    const auto tick_start = Clock::now();
    for (int i = 0; i < kTicks; ++i) {
        sim.tick(1.0F, 0.0F, false);
    }
    const double tick_ms =
        std::chrono::duration<double, std::milli>(Clock::now() - tick_start).count() / static_cast<double>(kTicks);

    char line[160];
    std::snprintf(line, sizeof(line), "desktop: %.3f ms a chunk (%d chunks), %.3f ms a tick (%d ticks walking)",
                  chunk_ms, kWindows * kChunksPerWindow, tick_ms, kTicks);
    std::ofstream out("performance.txt");
    out << line << "\n";
    INFO(line);
    REQUIRE(chunk_ms < kChunkBudgetMs);
    REQUIRE(tick_ms < kTickBudgetMs);
}

// The memory budget of the quality levels (spec 13, "Quality"): every recipe of the art of the pack, baked once at the
// largest bucket of a level (four bytes a pixel, the size the rasterizer gives), fits in the budget of that level.
TEST_CASE("quality: all the art baked once at the largest bucket of a level fits its budget", "[performance]") {
    const std::filesystem::path root = AETHER_REPO_ROOT;
    std::vector<std::string> errors;
    auto pack = aether::load_pack(root / "data" / "base", errors);
    REQUIRE(pack.has_value());
    int recipes = 0;
    for (const aether::QualityLevel& level : aether::kQualityLevels) {
        std::int64_t bytes = 0;
        recipes = 0;
        for (const auto& [id, relative] : pack->document_paths) {
            std::string path = relative;
            std::replace(path.begin(), path.end(), '\\', '/');
            if (path.rfind("art/", 0) != 0 || path.rfind("art/rigs/", 0) == 0 || path.rfind("art/clips/", 0) == 0) {
                continue;
            }
            const auto text = pack->read_document(id);
            std::string error;
            const auto recipe = text ? aether::parse_recipe(*text, error) : std::nullopt;
            if (!recipe) {
                continue;
            }
            const float scale = static_cast<float>(level.bucket_cap) / 32.0F;
            const std::int64_t w = std::max(1, static_cast<int>(std::ceil(recipe->width * scale)));
            const std::int64_t h = std::max(1, static_cast<int>(std::ceil(recipe->height * scale)));
            bytes += w * h * 4;
            ++recipes;
        }
        INFO(std::string(level.id) << ": " << bytes / (1024 * 1024) << " MiB of " << recipes << " recipes");
        REQUIRE(bytes <= static_cast<std::int64_t>(level.texture_budget_mib) * 1024 * 1024);
    }
    REQUIRE(recipes > 100);
}
