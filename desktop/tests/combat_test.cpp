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

TEST_CASE("a save is summarized without building its world", "[save]") {
    const auto peek = aether::save_peek(R"({"seed": "0x0000000000000010", "map": "world", "player": {"level": 4}, "story": {"gold": 75}})");
    REQUIRE(peek.has_value());
    REQUIRE(peek->seed == 16U);
    REQUIRE(peek->map == "world");
    REQUIRE(peek->level == 4);
    REQUIRE(peek->gold == 75);

    const auto bare = aether::save_peek(R"({"seed": "0x0000000000000001", "story": null})");
    REQUIRE(bare.has_value());
    REQUIRE(bare->level == 1);
    REQUIRE(bare->gold == 0);
    REQUIRE_FALSE(aether::save_peek("not json").has_value());
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
    REQUIRE(params->stamps.size() == 38);
    REQUIRE(params->home_radius == 72);

    const aether::TileMap map = aether::make_stream_map(*params);
    REQUIRE(map.ground.empty());
    REQUIRE(map.npcs.size() == 1);
    REQUIRE(map.npcs[0].key == "guild_clerk_mira");

    auto setup = aether::load_combat_setup(demo.pack, map, "base:protagonist/ren", 42, error);
    INFO(error);
    REQUIRE(setup.has_value());
    for (const std::string& enemy : aether::world_enemy_ids(*params)) {
        auto def = aether::load_enemy_def(demo.pack, enemy, error);
        INFO(error);
        REQUIRE(def.has_value());
        setup->stream_enemies.emplace(enemy, std::move(*def));
    }
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
    sim.story().advance();  // the elder has a menu (errand, news, goodbye): pick goodbye (the last choice)
    sim.story().choose(static_cast<int>(sim.story().dialogue_view().choices.size()) - 1);
    REQUIRE(!sim.story().dialogue_active());
    sim.teleport(static_cast<float>(map.width / 2) + 0.5F, static_cast<float>(map.height / 2) + 0.5F);  // back to the spawn
    sim.tick(0.0F, 0.0F, false);
    check_window();

    // The shopkeeper of the home village sells the wares of Verdalis (spec 06): open the shop from the dialogue, buy, equip.
    sim.teleport(8236.5F, 8229.5F);
    sim.tick(0.0F, 0.0F, false);
    REQUIRE(sim.story().npc_in_range() != nullptr);
    sim.story().interact();
    REQUIRE(sim.story().dialogue_active());
    sim.story().advance();
    sim.story().choose(0);  // "show me your wares"
    REQUIRE(!sim.story().dialogue_active());
    REQUIRE(sim.shop() != nullptr);
    REQUIRE(!sim.buy("base:item/iron_sword"));  // no gold yet
    sim.story().set_gold(1000);
    const std::int64_t attack_before = sim.derived().atk;
    REQUIRE(sim.buy("base:item/iron_sword"));
    REQUIRE(sim.story().gold() == 1000 - sim.buy_price("base:item/iron_sword"));
    REQUIRE(!sim.buy("base:item/iron_sword"));  // one is the limit for a weapon
    REQUIRE(!sim.buy("base:item/steel_sword"));  // not sold in Verdalis
    REQUIRE(sim.equip("base:item/iron_sword"));
    REQUIRE(sim.derived().atk > attack_before);
    REQUIRE(!sim.sell("base:item/iron_sword"));  // the last copy of a worn item stays
    sim.close_shop();
    REQUIRE(sim.shop() == nullptr);
    sim.teleport(static_cast<float>(map.width / 2) + 0.5F, static_cast<float>(map.height / 2) + 0.5F);
    sim.tick(0.0F, 0.0F, false);
    check_window();

    // The guild board of a town (spec 07, "Guild"): talk to a clerk, see the offers, accept one and keep it across a save.
    {
        const auto towns = aether::settlements_in(42, *params, 0, 0, 63, 63);
        const aether::Settlement* town = nullptr;
        std::pair<int, int> clerk_tile{0, 0};
        for (const aether::Settlement& s : towns) {
            for (const auto& [tile, slot] : s.slots) {
                if (slot.second == "guild_clerk" && town == nullptr) {
                    town = &s;
                    clerk_tile = tile;
                }
            }
        }
        REQUIRE(town != nullptr);
        sim.teleport(static_cast<float>(clerk_tile.first) + 0.5F, static_cast<float>(clerk_tile.second) + 1.4F);
        sim.tick(0.0F, 0.0F, false);
        const aether::NpcDef* clerk = sim.story().npc_in_range();
        REQUIRE(clerk != nullptr);
        REQUIRE(clerk->dialogue.find("guild_clerk") != std::string::npos);
        sim.story().interact();
        sim.story().advance();
        sim.story().choose(0);  // "show me the board"
        REQUIRE(!sim.story().dialogue_active());
        REQUIRE(sim.board() != nullptr);
        REQUIRE(sim.board()->offers.size() == static_cast<std::size_t>(params->guild.offers_per_day));
        REQUIRE(sim.guild_rank() == 0);
        REQUIRE(sim.accept_offer(0));
        REQUIRE(!sim.accept_offer(0));  // already taken
        REQUIRE(!sim.accept_offer(3));  // needs a higher rank
        const std::string quest_id = sim.board()->offers[0].id;
        REQUIRE(sim.story().quests().count(quest_id) == 1);
        // A save keeps the generated quest and a fresh world rebuilds it from its id.
        const aether::SaveState with_quest = sim.capture();
        aether::SaveMeta quest_meta;
        quest_meta.seed = 42;
        quest_meta.map = "world";
        std::string quest_json_error;
        const auto quest_save = aether::save_from_json(aether::save_to_json(with_quest, quest_meta), quest_json_error);
        REQUIRE(quest_save.has_value());
        aether::WorldSim reloaded(map, demo.tileset, 0.0F, *setup, aether::StreamConfig{*params, 42});
        std::string reload_error;
        REQUIRE(reloaded.restore(*quest_save, reload_error));
        REQUIRE(reloaded.story().quests().count(quest_id) == 1);
        sim.close_board();
        sim.teleport(static_cast<float>(map.width / 2) + 0.5F, static_cast<float>(map.height / 2) + 0.5F);
        sim.tick(0.0F, 0.0F, false);
        check_window();
    }

    // Threshold Stones (spec 09): wake the stone of the home village and the one of a town, then travel between them.
    {
        const auto stone_of = [&params](const aether::Settlement& s) {
            for (int cy = s.y / 32; cy <= (s.y + s.h - 1) / 32; ++cy) {
                for (int cx = s.x / 32; cx <= (s.x + s.w - 1) / 32; ++cx) {
                    for (const aether::GenProp& prop : aether::generate_chunk(42, *params, cx, cy).props) {
                        const int tx = prop.x256 / 256;
                        const int ty = prop.y256 / 256;
                        if (prop.art == params->stone_art && tx >= s.x && tx < s.x + s.w && ty >= s.y && ty < s.y + s.h) {
                            return std::make_pair(static_cast<float>(prop.x256) / 256.0F, static_cast<float>(prop.y256) / 256.0F);
                        }
                    }
                }
            }
            return std::make_pair(-1.0F, -1.0F);
        };
        sim.teleport(8230.5F, 8232.7F);
        sim.tick(0.0F, 0.0F, false);
        REQUIRE(sim.stone_near().has_value());
        REQUIRE(sim.use_stone());
        REQUIRE(sim.travel() != nullptr);
        REQUIRE(sim.travel()->fresh);
        REQUIRE(sim.travel()->stops.size() == 1);
        REQUIRE(sim.travel()->here == 0);
        REQUIRE(!sim.travel()->stops[0].place.empty());
        REQUIRE(!sim.travel_to(0));  // never to the stone in use
        sim.close_travel();
        REQUIRE(sim.use_stone());  // the second time the stone is not new
        REQUIRE(!sim.travel()->fresh);
        sim.close_travel();

        const auto towns = aether::settlements_in(42, *params, 0, 0, 63, 63);
        const aether::Settlement* town = nullptr;
        for (const aether::Settlement& s : towns) {
            if (town == nullptr && s.kind == "town") {
                town = &s;
            }
        }
        REQUIRE(town != nullptr);
        const auto stone = stone_of(*town);
        REQUIRE(stone.first > 0.0F);
        sim.teleport(stone.first, stone.second + 0.9F);
        sim.tick(0.0F, 0.0F, false);
        REQUIRE(sim.use_stone());
        REQUIRE(sim.travel()->fresh);
        REQUIRE(sim.travel()->stops.size() == 2);
        REQUIRE(sim.travel()->here == 1);
        REQUIRE(sim.travel()->stops[1].place == town->name);
        REQUIRE(sim.travel_to(0));
        REQUIRE(sim.travel() == nullptr);
        REQUIRE(std::abs(sim.player().position.x - 8230.5F) < 1.0F);
        REQUIRE(std::abs(sim.player().position.y - 8232.75F) < 1.0F);
        REQUIRE(sim.stones().size() == 2);
        // The stones are saved.
        aether::SaveMeta stone_meta;
        stone_meta.seed = 42;
        stone_meta.map = "world";
        std::string stone_error;
        const auto stone_save = aether::save_from_json(aether::save_to_json(sim.capture(), stone_meta), stone_error);
        REQUIRE(stone_save.has_value());
        REQUIRE(stone_save->stones == sim.stones());
        sim.teleport(static_cast<float>(map.width / 2) + 0.5F, static_cast<float>(map.height / 2) + 0.5F);
        sim.tick(0.0F, 0.0F, false);
        check_window();
    }

    // Routines (spec 08): the shopkeeper of the home village is at the counter by day and indoors at night.
    {
        sim.teleport(8236.5F, 8229.5F);
        sim.tick(0.0F, 0.0F, false);
        const std::int64_t day_ticks = params->time.day_ticks;
        const auto at_time_of_day = [&](int tod_pm) {
            aether::SaveState state = sim.capture();
            state.world_ticks = (state.world_ticks / day_ticks) * day_ticks + day_ticks * tod_pm / 1000;
            std::string restore_error;
            REQUIRE(sim.restore(state, restore_error));
        };
        at_time_of_day(500);
        REQUIRE(sim.story().npc_in_range() != nullptr);
        at_time_of_day(100);
        REQUIRE(sim.story().npc_in_range() == nullptr);
        at_time_of_day(500);
        REQUIRE(sim.story().npc_in_range() != nullptr);
        sim.teleport(static_cast<float>(map.width / 2) + 0.5F, static_cast<float>(map.height / 2) + 0.5F);
        sim.tick(0.0F, 0.0F, false);
        check_window();
    }

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
    REQUIRE(fresh.equipped_weapon() == "base:item/iron_sword");
    REQUIRE(fresh.derived().atk == sim.derived().atk);
    REQUIRE(fresh.explored() == sim.explored());

    // A save with an enemy that does not exist in this world is refused and changes nothing.
    aether::SaveState bad = *reread;
    bad.enemies.push_back({{0.0F, 0.0F}, 1, aether::EnemyState::Idle, 0, true, 1, 1});
    bad.hit_set.push_back(false);
    REQUIRE_FALSE(fresh.restore(bad, error));
}
