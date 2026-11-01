// Combat on the real data: the loader, the demo map spawners and a short fight.

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <filesystem>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "data/pack.hpp"
#include "sim/combat_loader.hpp"
#include "data/world_data.hpp"
#include "sim/save.hpp"
#include "sim/world_map.hpp"
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

TEST_CASE("the overworld is streamed from the content pack and is playable", "[world]") {
    const Demo demo = load_demo();
    const auto text = demo.pack.read_document("base:world/overworld");
    REQUIRE(text.has_value());
    std::string error;
    const auto params = aether::load_world_params(demo.pack, "base:world/overworld", error);
    INFO(error);
    REQUIRE(params.has_value());
    REQUIRE(params->width == 16384);
    REQUIRE(params->regions.size() == 8);
    REQUIRE(params->stamps.size() == 3);
    REQUIRE(params->home_radius == 72);

    const aether::TileMap map = aether::make_stream_map(*params);
    REQUIRE(map.ground.empty());
    REQUIRE(map.npcs.size() == 1);
    REQUIRE(map.npcs[0].key == "guild_clerk_mira");

    auto setup = aether::load_combat_setup(demo.pack, map, "base:protagonist/ren", 42, error);
    INFO(error);
    REQUIRE(setup.has_value());
    setup->stream_enemy = aether::load_enemy_def(demo.pack, params->spawner_enemy, error);
    REQUIRE(setup->stream_enemy.has_value());
    aether::WorldSim sim(map, demo.tileset, 0.0F, *setup, aether::StreamConfig{*params, 42});
    REQUIRE(sim.streamed());
    REQUIRE(sim.chunks()->loaded() >= 25);

    // The spawn clearing is walkable plains, and Mira stands next to it.
    const int cx = map.width / 2;
    const int cy = map.height / 2;
    REQUIRE((sim.gid_at(cx, cy) == 1 || sim.gid_at(cx, cy) == 2));
    for (int i = 0; i < 120; ++i) {
        sim.tick(0.0F, 0.0F, false);
    }
    REQUIRE(sim.story().npc_in_range() != nullptr);
    REQUIRE(sim.world_ticks() == params->time.start_tick + 120);  // the world clock runs with the ticks
    REQUIRE(sim.time().has_value());
    REQUIRE(sim.explored().size() == 9);  // the cell of the spawn and its neighbours
    REQUIRE(sim.time()->tod_pm == static_cast<int>(sim.world_ticks() * 1000 / params->time.day_ticks));

    // The enemies are exactly those of the spawners in the 5 x 5 chunks around the player, whichever chunk that is.
    const auto check_window = [&]() {
        const int pcx = aether::chunk_of(static_cast<int>(std::floor(sim.player().position.x)));
        const int pcy = aether::chunk_of(static_cast<int>(std::floor(sim.player().position.y)));
        std::set<std::pair<int, int>> expected;
        for (int j = pcy - 2; j <= pcy + 2; ++j) {
            for (int i = pcx - 2; i <= pcx + 2; ++i) {
                for (const auto& s : aether::generate_chunk(42, *params, i, j).spawners) {
                    expected.insert(s);
                }
            }
        }
        std::set<std::pair<int, int>> found;
        for (const aether::Enemy& e : sim.enemies()) {
            REQUIRE(found.insert({e.spawner_x, e.spawner_y}).second);
        }
        REQUIRE(found == expected);
        REQUIRE(sim.chunks()->loaded() <= 49);
    };
    check_window();
    const std::size_t at_spawn = sim.enemies().size();

    // The spawn is at the left edge of its chunk: a few steps to the left enter the next chunk and the window moves.
    for (int i = 0; i < 90; ++i) {
        sim.tick(-1.0F, 0.0F, false);
    }
    REQUIRE(aether::chunk_of(static_cast<int>(std::floor(sim.player().position.x))) == cx / 32 - 1);
    check_window();
    INFO("enemies at the spawn " << at_spawn);

    // The home village has people: walk up to its elder and talk (spec 07 and 09).
    sim.teleport(8228.5F, 8234.5F);
    sim.tick(0.0F, 0.0F, false);
    REQUIRE(!sim.story().dynamic_npcs().empty());
    const aether::NpcDef* elder = sim.story().npc_in_range();
    REQUIRE(elder != nullptr);
    REQUIRE(!elder->name.empty());
    REQUIRE(elder->dialogue.rfind("base:dialogue/role/", 0) == 0);
    REQUIRE(elder->args.count("place") == 1);
    sim.story().interact();
    REQUIRE(sim.story().dialogue_active());
    const aether::DialogueView spoken = sim.story().dialogue_view();
    REQUIRE(spoken.speaker == "npc");
    REQUIRE(spoken.args.at("npc") == elder->name);
    sim.story().advance();  // the elder has a menu with news and goodbye: pick goodbye (the last choice)
    sim.story().choose(1);
    REQUIRE(!sim.story().dialogue_active());
    sim.teleport(static_cast<float>(map.width / 2) + 0.5F, static_cast<float>(map.height / 2) + 0.5F);  // back to the spawn
    sim.tick(0.0F, 0.0F, false);
    check_window();

    // Saving and loading into a fresh world of the same seed gives the same enemies.
    const aether::SaveState state = sim.capture();
    REQUIRE(state.enemies.size() == sim.enemies().size());
    REQUIRE((state.enemies.empty() || state.enemies[0].has_spawner));
    std::string json_error;
    aether::SaveMeta meta;
    meta.seed = 42;
    meta.map = "world";
    const auto reread = aether::save_from_json(aether::save_to_json(state, meta), json_error);
    INFO(json_error);
    REQUIRE(reread.has_value());
    aether::WorldSim fresh(map, demo.tileset, 0.0F, *setup, aether::StreamConfig{*params, 42});
    REQUIRE(fresh.restore(*reread, error));
    REQUIRE(fresh.enemies().size() == sim.enemies().size());
    REQUIRE(fresh.player().position.x == sim.player().position.x);
    REQUIRE(fresh.world_ticks() == sim.world_ticks());
    REQUIRE(fresh.explored() == sim.explored());

    // A save with an enemy that does not exist in this world is refused and changes nothing.
    aether::SaveState bad = *reread;
    bad.enemies.push_back({{0.0F, 0.0F}, 1, aether::EnemyState::Idle, 0, true, 1, 1});
    bad.hit_set.push_back(false);
    REQUIRE_FALSE(fresh.restore(bad, error));
}
