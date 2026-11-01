#include "sim/save.hpp"

#include <cstdio>
#include <stdexcept>

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

std::string hex64(std::uint64_t value) {
    char buffer[24];
    std::snprintf(buffer, sizeof(buffer), "0x%016llx", static_cast<unsigned long long>(value));
    return buffer;
}

std::uint64_t parse_hex64(const Json& value) { return std::stoull(value.get<std::string>(), nullptr, 16); }

const char* phase_name(AttackPhase phase) {
    switch (phase) {
        case AttackPhase::None:
            return "none";
        case AttackPhase::Startup:
            return "startup";
        case AttackPhase::Active:
            return "active";
        case AttackPhase::Recovery:
            return "recovery";
    }
    return "none";
}

AttackPhase parse_phase(const std::string& name) {
    if (name == "none") {
        return AttackPhase::None;
    }
    if (name == "startup") {
        return AttackPhase::Startup;
    }
    if (name == "active") {
        return AttackPhase::Active;
    }
    if (name == "recovery") {
        return AttackPhase::Recovery;
    }
    throw std::runtime_error("unknown attack phase " + name);
}

EnemyState parse_enemy_state(const std::string& name) {
    for (const EnemyState state : {EnemyState::Idle, EnemyState::Chase, EnemyState::Attack, EnemyState::Return, EnemyState::Dead}) {
        if (name == to_string(state)) {
            return state;
        }
    }
    throw std::runtime_error("unknown enemy state " + name);
}

}  // namespace

std::string save_to_json(const SaveState& s, const SaveMeta& meta) {
    Json j;
    j["save_version"] = kSaveVersion;
    j["game_version"] = meta.game_version;
    j["data_format_version"] = meta.data_format_version;
    j["protagonist"] = meta.protagonist;
    j["seed"] = hex64(meta.seed);
    j["map"] = meta.map;

    Json player;
    player["x"] = s.position.x;
    player["y"] = s.position.y;
    player["facing"] = Json::array({s.facing.x, s.facing.y});
    player["facing_left"] = s.facing_left;
    player["moving"] = s.moving;
    player["clip_tick"] = s.clip_tick;
    player["hp"] = s.hp;
    player["level"] = s.level;
    player["xp"] = s.xp;
    player["deaths"] = s.deaths;
    player["kills"] = s.kills;
    player["iframes"] = s.iframes;
    player["cooldown"] = s.cooldown;
    player["phase"] = phase_name(s.phase);
    player["phase_tick"] = s.phase_tick;
    Json hit_set = Json::array();
    for (const bool hit : s.hit_set) {
        hit_set.push_back(hit);
    }
    player["hit_set"] = hit_set;
    j["player"] = player;

    j["rng"] = {{"combat", {{"state", hex64(s.combat_state)}, {"inc", hex64(s.combat_inc)}}},
                {"loot", {{"state", hex64(s.loot_state)}, {"inc", hex64(s.loot_inc)}}}};

    Json enemies = Json::array();
    for (const SaveEnemy& e : s.enemies) {
        Json enemy = {{"x", e.position.x}, {"y", e.position.y}, {"hp", e.hp}, {"state", to_string(e.state)},
                      {"state_tick", e.state_tick}};
        if (e.has_spawner) {
            enemy["spawner"] = {e.spawner_x, e.spawner_y};
        }
        enemies.push_back(std::move(enemy));
    }
    j["enemies"] = enemies;
    j["world_ticks"] = s.world_ticks;
    if (meta.map == "world") {
        Json cleared = Json::array();
        for (const ClearedSpawner& c : s.cleared) {
            cleared.push_back({c.x, c.y, c.died});
        }
        j["cleared_spawners"] = cleared;
    }

    Json inventory = Json::object();
    for (const auto& [item, quantity] : s.inventory) {
        inventory[item] = quantity;
    }
    j["inventory"] = inventory;

    Json story;
    Json flags = Json::object();
    for (const auto& [flag, value] : s.story.flags) {
        flags[flag] = value;
    }
    story["flags"] = flags;
    story["gold"] = s.story.gold;
    Json quests = Json::object();
    for (const auto& [id, q] : s.story.quests) {
        Json progress = Json::array();
        for (const std::int64_t count : q.progress) {
            progress.push_back(count);
        }
        quests[id] = {{"stage", q.stage}, {"progress", progress}, {"done", q.done}};
    }
    story["quests"] = quests;
    if (s.story.dialogue_active) {
        story["dialogue"] = {{"id", s.story.dialogue_id}, {"node", s.story.node}};
    } else {
        story["dialogue"] = nullptr;
    }
    j["story"] = story;
    return j.dump(2) + "\n";
}

std::optional<SaveState> save_from_json(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        if (j.at("save_version").get<int>() > kSaveVersion) {
            error = "this save was written by a newer version of the game";
            return std::nullopt;
        }
        SaveState s;
        const Json& p = j.at("player");
        s.position = {p.at("x").get<float>(), p.at("y").get<float>()};
        s.facing = {p.at("facing").at(0).get<float>(), p.at("facing").at(1).get<float>()};
        s.facing_left = p.at("facing_left").get<bool>();
        s.moving = p.at("moving").get<bool>();
        s.clip_tick = p.at("clip_tick").get<int>();
        s.hp = p.at("hp").get<std::int64_t>();
        s.level = p.at("level").get<std::int64_t>();
        s.xp = p.at("xp").get<std::int64_t>();
        s.deaths = p.at("deaths").get<int>();
        s.kills = p.at("kills").get<int>();
        s.iframes = p.at("iframes").get<int>();
        s.cooldown = p.at("cooldown").get<int>();
        s.phase = parse_phase(p.at("phase").get<std::string>());
        s.phase_tick = p.at("phase_tick").get<int>();
        for (const Json& hit : p.at("hit_set")) {
            s.hit_set.push_back(hit.get<bool>());
        }

        const Json& rng = j.at("rng");
        s.combat_state = parse_hex64(rng.at("combat").at("state"));
        s.combat_inc = parse_hex64(rng.at("combat").at("inc"));
        s.loot_state = parse_hex64(rng.at("loot").at("state"));
        s.loot_inc = parse_hex64(rng.at("loot").at("inc"));

        for (const Json& e : j.at("enemies")) {
            SaveEnemy enemy{{e.at("x").get<float>(), e.at("y").get<float>()}, e.at("hp").get<std::int64_t>(),
                            parse_enemy_state(e.at("state").get<std::string>()), e.at("state_tick").get<int>()};
            if (e.contains("spawner")) {
                enemy.has_spawner = true;
                enemy.spawner_x = e.at("spawner").at(0).get<int>();
                enemy.spawner_y = e.at("spawner").at(1).get<int>();
            }
            s.enemies.push_back(enemy);
        }
        s.world_ticks = j.value("world_ticks", static_cast<std::int64_t>(-1));
        if (j.contains("cleared_spawners")) {
            for (const Json& c : j.at("cleared_spawners")) {
                s.cleared.push_back({c.at(0).get<int>(), c.at(1).get<int>(), c.size() > 2 ? c.at(2).get<std::int64_t>() : 0});
            }
        }
        for (const auto& [item, quantity] : j.at("inventory").items()) {
            s.inventory[item] = quantity.get<std::int64_t>();
        }

        if (!j.at("story").is_null()) {
            const Json& story = j.at("story");
            for (const auto& [flag, value] : story.at("flags").items()) {
                s.story.flags[flag] = value.get<bool>();
            }
            s.story.gold = story.at("gold").get<std::int64_t>();
            for (const auto& [id, q] : story.at("quests").items()) {
                QuestProgress progress;
                progress.stage = q.at("stage").get<std::string>();
                progress.done = q.at("done").get<bool>();
                for (const Json& count : q.at("progress")) {
                    progress.progress.push_back(count.get<std::int64_t>());
                }
                s.story.quests[id] = std::move(progress);
            }
            if (!story.at("dialogue").is_null()) {
                s.story.dialogue_active = true;
                s.story.dialogue_id = story.at("dialogue").at("id").get<std::string>();
                s.story.node = story.at("dialogue").at("node").get<std::string>();
            }
        }
        return s;
    } catch (const std::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::optional<SavePeek> save_peek(std::string_view json_text) {
    try {
        const Json j = Json::parse(json_text);
        SavePeek peek;
        peek.seed = parse_hex64(j.at("seed"));
        peek.map = j.value("map", "");
        return peek;
    } catch (const std::exception&) {
        return std::nullopt;
    }
}

}  // namespace aether
