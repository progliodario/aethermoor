// Tests for tile maps, the world simulation and the rig, on the real demo data.

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <filesystem>
#include <string>
#include <vector>

#include "data/pack.hpp"
#include "sim/movement.hpp"
#include "sim/world.hpp"
#include "vector/raster.hpp"
#include "vector/recipe.hpp"
#include "vector/rig.hpp"

namespace {

const std::filesystem::path kRepoRoot = AETHER_REPO_ROOT;

struct Loaded {
    aether::Pack pack;
    aether::TileMap map;
    aether::Tileset tileset;
};

Loaded load_demo() {
    std::vector<std::string> errors;
    auto pack = aether::load_pack(kRepoRoot / "data" / "base", errors);
    REQUIRE(errors.empty());
    REQUIRE(pack.has_value());
    std::string error;
    const auto map_text = pack->read_file("maps/demo.tmj");
    const auto tileset_text = pack->read_document("base:tileset/overworld");
    REQUIRE(map_text.has_value());
    REQUIRE(tileset_text.has_value());
    auto map = aether::parse_tilemap(*map_text, error);
    auto tileset = aether::parse_tileset(*tileset_text, error);
    INFO(error);
    REQUIRE(map.has_value());
    REQUIRE(tileset.has_value());
    return {std::move(*pack), std::move(*map), std::move(*tileset)};
}

}  // namespace

TEST_CASE("demo map loads", "[sim]") {
    const Loaded demo = load_demo();
    REQUIRE(demo.map.width == 40);
    REQUIRE(demo.map.height == 30);
    REQUIRE(demo.map.tileset_id == "base:tileset/overworld");
    REQUIRE(demo.map.ground.size() == 1200);
    REQUIRE(demo.map.spawn_x == Catch::Approx(5.5F));
    REQUIRE(demo.map.spawn_y == Catch::Approx(15.5F));
    REQUIRE_FALSE(demo.map.props.empty());
    REQUIRE(demo.tileset.tiles.size() == 14);
    REQUIRE(demo.map.gid_at(0, 0) == 5);   // border wall
    REQUIRE(demo.map.gid_at(-1, 0) == 0);  // out of range
}

TEST_CASE("every art recipe referenced by the demo map can be baked", "[sim][vector]") {
    const Loaded demo = load_demo();
    std::vector<std::string> ids;
    for (const auto& [gid, tile] : demo.tileset.tiles) {
        ids.push_back(tile.art);
    }
    for (const aether::Prop& prop : demo.map.props) {
        ids.push_back(prop.art);
    }
    for (const std::string& id : ids) {
        INFO(id);
        const auto text = demo.pack.read_document(id);
        REQUIRE(text.has_value());
        std::string error;
        const auto recipe = aether::parse_recipe(*text, error);
        INFO(error);
        REQUIRE(recipe.has_value());
        const aether::Bitmap bitmap = aether::rasterize(*recipe, 1.0F);
        REQUIRE(bitmap.width > 0);
        std::size_t opaque = 0;
        for (std::size_t i = 3; i < bitmap.rgba.size(); i += 4) {
            opaque += bitmap.rgba[i] > 0 ? 1U : 0U;
        }
        REQUIRE(opaque > 0);
    }
}

TEST_CASE("player walks, is blocked by walls and keeps constant speed on diagonals", "[sim]") {
    const Loaded demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 4.0F);
    const aether::Vec2 start = sim.player().position;
    for (int i = 0; i < 30; ++i) {
        sim.tick(1.0F, 0.0F);
    }
    REQUIRE(sim.player().position.x - start.x == Catch::Approx(2.0F).margin(0.01F));
    REQUIRE(sim.player().moving);
    REQUIRE_FALSE(sim.player().facing_left);

    aether::WorldSim diag1(demo.map, demo.tileset, 4.0F);
    diag1.tick(1.0F, 1.0F);
    const float dx = diag1.player().position.x - demo.map.spawn_x;
    const float dy = diag1.player().position.y - demo.map.spawn_y;
    REQUIRE(std::sqrt(dx * dx + dy * dy) == Catch::Approx(4.0F / 60.0F).margin(0.0005F));

    aether::WorldSim wall(demo.map, demo.tileset, 4.0F);
    for (int i = 0; i < 400; ++i) {
        wall.tick(-1.0F, 0.0F);
    }
    REQUIRE(wall.player().position.x == Catch::Approx(1.0F + aether::kPlayerRadius).margin(0.01F));
    REQUIRE(wall.player().facing_left);
}

TEST_CASE("animation state follows movement", "[sim]") {
    const Loaded demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 4.0F);
    REQUIRE_FALSE(sim.player().moving);
    sim.tick(0.0F, 0.0F);
    sim.tick(0.0F, 0.0F);
    REQUIRE(sim.player().clip_tick == 2);
    sim.tick(0.0F, -1.0F);
    REQUIRE(sim.player().moving);
    REQUIRE(sim.player().clip_tick == 0);
    sim.tick(0.0F, -1.0F);
    REQUIRE(sim.player().clip_tick == 1);
}

TEST_CASE("camera is clamped to the map and centered when the map is smaller than the view", "[sim]") {
    const Loaded demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 4.0F);
    const aether::Camera near_edge = sim.camera(20.0F, 12.0F);
    REQUIRE(near_edge.x == Catch::Approx(0.0F));  // spawn is 5.5 tiles from the left edge, view is 20 wide
    const aether::Camera huge = sim.camera(60.0F, 40.0F);
    REQUIRE(huge.x == Catch::Approx(-10.0F));
    REQUIRE(huge.y == Catch::Approx(-5.0F));
}

TEST_CASE("rig of the demo character has its parts parents-first", "[vector]") {
    const Loaded demo = load_demo();
    std::string error;
    const auto rig = aether::parse_rig(*demo.pack.read_document("base:art/rig/humanoid"), error);
    const auto walk = aether::parse_clip(*demo.pack.read_document("base:art/clip/humanoid_walk"), error);
    INFO(error);
    REQUIRE(rig.has_value());
    REQUIRE(walk.has_value());
    REQUIRE(rig->parts.size() == 7);
    const auto pose = aether::evaluate_pose(*rig, *walk, 0.0F, false);
    REQUIRE(pose.size() == rig->parts.size());
    const auto mirrored = aether::evaluate_pose(*rig, *walk, 0.0F, true);
    for (std::size_t i = 0; i < pose.size(); ++i) {
        REQUIRE(mirrored[i].x == Catch::Approx(-pose[i].x).margin(0.0001F));
        REQUIRE(mirrored[i].y == Catch::Approx(pose[i].y).margin(0.0001F));
        REQUIRE(mirrored[i].rotation_deg == Catch::Approx(-pose[i].rotation_deg).margin(0.0001F));
    }
}
