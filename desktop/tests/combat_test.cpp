// Combat on the real data: the loader, the demo map spawners and a short fight.

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <filesystem>
#include <string>
#include <vector>

#include "data/pack.hpp"
#include "sim/combat_loader.hpp"
#include "sim/save.hpp"
#include "sim/world.hpp"

namespace {

const std::filesystem::path kRepoRoot = AETHER_REPO_ROOT;

struct Demo {
    aether::Pack pack;
    aether::TileMap map;
    aether::Tileset tileset;
    aether::CombatSetup setup;
};

Demo load_demo() {
    std::vector<std::string> errors;
    auto pack = aether::load_pack(kRepoRoot / "data" / "base", errors);
    REQUIRE(errors.empty());
    REQUIRE(pack.has_value());
    std::string error;
    auto map = aether::parse_tilemap(*pack->read_file("maps/demo.tmj"), error);
    auto tileset = aether::parse_tileset(*pack->read_document("base:tileset/overworld"), error);
    INFO(error);
    REQUIRE(map.has_value());
    REQUIRE(tileset.has_value());
    auto setup = aether::load_combat_setup(*pack, *map, "base:protagonist/ren", 7, error);
    INFO(error);
    REQUIRE(setup.has_value());
    return {std::move(*pack), std::move(*map), std::move(*tileset), std::move(*setup)};
}

}  // namespace

TEST_CASE("combat setup is built from the content pack", "[combat]") {
    const Demo demo = load_demo();
    REQUIRE(demo.map.spawners.size() == 12);
    REQUIRE(demo.setup.spawns.size() == 12);
    REQUIRE(demo.setup.spawns[0].def.id == "base:enemy/slime_green");
    REQUIRE(demo.setup.spawns[0].def.hp == 28);
    REQUIRE(demo.setup.spawns[0].def.drops.size() == 1);
    REQUIRE(demo.setup.spawns[0].def.behavior.windup_ticks == 18);
    REQUIRE(demo.setup.skill.startup == 6);
    REQUIRE(demo.setup.skill.angle_deg == 110);
    REQUIRE(demo.setup.player.weapon_atk == 3);
    REQUIRE(demo.setup.player.base.luk == 9);
    REQUIRE(demo.setup.xp_table.size() == 98);
}

TEST_CASE("the player starts with full health and derived stats", "[combat]") {
    const Demo demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 0.0F, demo.setup);
    REQUIRE(sim.player().level == 1);
    REQUIRE(sim.player().hp == sim.derived().max_hp);
    REQUIRE(sim.derived().atk == 6 * 2 + 8 / 2 + 3);
    REQUIRE(sim.enemies().size() == 12);
}

TEST_CASE("a swing against nothing changes nothing; the cooldown limits swings", "[combat]") {
    const Demo demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 0.0F, demo.setup);
    for (int i = 0; i < 100; ++i) {
        sim.tick(0.0F, 0.0F, true);
    }
    REQUIRE(sim.player().kills == 0);
    REQUIRE(sim.player().hp == sim.derived().max_hp);
    REQUIRE(sim.take_events().empty());
}

TEST_CASE("an enemy that reaches the player hurts it, and respawn restores health", "[combat]") {
    Demo demo = load_demo();
    // Put a deadly enemy right next to the player.
    aether::EnemySpawn spawn = demo.setup.spawns[0];
    spawn.def.atk = 100000;
    spawn.x = demo.map.spawn_x + 1.0F;
    spawn.y = demo.map.spawn_y;
    demo.setup.spawns = {spawn};
    aether::WorldSim sim(demo.map, demo.tileset, 0.0F, demo.setup);
    for (int i = 0; i < 120; ++i) {
        sim.tick(0.0F, 0.0F, false);
    }
    REQUIRE(sim.player().deaths >= 1);
    REQUIRE(sim.player().hp > 0);
    REQUIRE(sim.player().position.x == Catch::Approx(demo.map.spawn_x).margin(0.01F));
}

TEST_CASE("talking to the guild clerk with the real data starts her quest", "[combat][story]") {
    Demo demo = load_demo();
    demo.map.spawn_x = 8.5F;
    demo.map.spawn_y = 15.4F;
    aether::WorldSim sim(demo.map, demo.tileset, 0.0F, demo.setup);
    REQUIRE(sim.story().npc_in_range() != nullptr);
    sim.story().interact();
    REQUIRE(sim.story().dialogue_view().active);
    REQUIRE(sim.story().dialogue_view().text == "$i18n:dlg.mira.offer");
    sim.story().advance();
    REQUIRE(sim.story().dialogue_view().is_choice);
    REQUIRE(sim.story().dialogue_view().choices.size() == 2);
    sim.story().choose(0);
    sim.story().advance();
    REQUIRE_FALSE(sim.story().dialogue_active());
    REQUIRE(sim.story().quests().count("base:quest/guild/slime_extermination") == 1);

    // Talking again shows the "busy" line, and while the dialogue is open the player does not move.
    sim.story().interact();
    REQUIRE(sim.story().dialogue_view().text == "$i18n:dlg.mira.busy");
    const aether::Vec2 before = sim.player().position;
    for (int i = 0; i < 30; ++i) {
        sim.tick(1.0F, 0.0F, true);
    }
    REQUIRE(sim.player().position.x == before.x);
    REQUIRE(sim.player().position.y == before.y);
}

TEST_CASE("the player starts with the protagonist's items", "[combat]") {
    const Demo demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 0.0F, demo.setup);
    REQUIRE(sim.inventory().at("base:item/practice_sword") == 1);
    REQUIRE(sim.inventory().at("base:item/bread") == 3);
}

TEST_CASE("a save of the real world survives the round trip and has the same future", "[combat][save]") {
    const Demo demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 0.0F, demo.setup);
    for (int i = 0; i < 200; ++i) {
        sim.tick(1.0F, 0.0F, i % 3 == 0);
    }
    sim.story().interact();
    aether::SaveMeta meta;
    meta.game_version = "test";
    meta.seed = demo.setup.seed;
    const std::string text = aether::save_to_json(sim.capture(), meta);

    std::string error;
    const auto state = aether::save_from_json(text, error);
    INFO(error);
    REQUIRE(state.has_value());
    aether::WorldSim copy(demo.map, demo.tileset, 0.0F, demo.setup);
    REQUIRE(copy.restore(*state, error));
    for (int i = 0; i < 300; ++i) {
        sim.tick(1.0F, 0.0F, i % 2 == 0);
        copy.tick(1.0F, 0.0F, i % 2 == 0);
    }
    REQUIRE(aether::save_to_json(sim.capture(), meta) == aether::save_to_json(copy.capture(), meta));
}

TEST_CASE("a save for a different world or a newer game is refused", "[combat][save]") {
    const Demo demo = load_demo();
    aether::WorldSim sim(demo.map, demo.tileset, 0.0F, demo.setup);
    aether::SaveState state = sim.capture();
    state.enemies.pop_back();
    std::string error;
    REQUIRE_FALSE(sim.restore(state, error));
    REQUIRE_FALSE(error.empty());

    std::string parse_error;
    REQUIRE_FALSE(aether::save_from_json("{\"save_version\": 99}", parse_error).has_value());
    REQUIRE_FALSE(aether::save_from_json("not json", parse_error).has_value());
}
