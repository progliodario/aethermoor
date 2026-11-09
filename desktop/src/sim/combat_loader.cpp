#include "sim/combat_loader.hpp"

#include <map>

#include <nlohmann/json.hpp>

#include "data/protagonist.hpp"

namespace aether {

namespace {

using Json = nlohmann::json;

std::optional<Json> document(const Pack& pack, std::string_view id, std::string& error) {
    const auto text = pack.read_document(id);
    if (!text) {
        error = "missing document " + std::string(id);
        return std::nullopt;
    }
    Json parsed = Json::parse(*text, nullptr, /*allow_exceptions=*/false);
    if (parsed.is_discarded()) {
        error = "invalid JSON in " + std::string(id);
        return std::nullopt;
    }
    return parsed;
}

std::optional<EnemyDef> load_enemy_impl(const Pack& pack, const std::string& id, std::string& error) {
    const auto enemy = document(pack, id, error);
    if (!enemy) {
        return std::nullopt;
    }
    try {
        EnemyDef def;
        def.id = id;
        def.art = enemy->at("art").get<std::string>();
        def.level = enemy->at("level").get<std::int64_t>();
        const Json& stats = enemy->at("stats");
        def.hp = stats.at("hp").get<std::int64_t>();
        def.atk = stats.at("atk").get<std::int64_t>();
        def.def = stats.at("def").get<std::int64_t>();
        def.speed_x100 = stats.at("speed_x100").get<int>();
        def.xp = enemy->at("xp").get<std::int64_t>();
        def.radius_x100 = enemy->at("radius_x100").get<int>();
        def.element = enemy->value("element", "none");
        def.sound = enemy->value("sound", "");
        if (enemy->contains("weaknesses_pm")) {
            for (const auto& [element, multiplier] : enemy->at("weaknesses_pm").items()) {
                def.weaknesses_pm[element] = multiplier.get<std::int64_t>();
            }
        }
        if (enemy->contains("drops")) {
            for (const Json& drop : enemy->at("drops")) {
                def.drops.push_back({drop.at("item").get<std::string>(), drop.at("qty_min").get<std::int64_t>(),
                                     drop.at("qty_max").get<std::int64_t>(), drop.at("weight_pm").get<std::int64_t>()});
            }
        }
        const auto behavior = document(pack, enemy->at("behavior").get<std::string>(), error);
        if (!behavior) {
            return std::nullopt;
        }
        def.behavior.aggro_x100 = behavior->at("aggro_x100").get<int>();
        def.behavior.leash_x100 = behavior->at("leash_x100").get<int>();
        def.behavior.attack_range_x100 = behavior->at("attack_range_x100").get<int>();
        def.behavior.hit_range_x100 = behavior->at("hit_range_x100").get<int>();
        def.behavior.windup_ticks = behavior->at("windup_ticks").get<int>();
        def.behavior.recovery_ticks = behavior->at("recovery_ticks").get<int>();
        return def;
    } catch (const Json::exception& e) {
        error = id + ": " + e.what();
        return std::nullopt;
    }
}

}  // namespace

std::optional<EnemyDef> load_enemy_def(const Pack& pack, const std::string& id, std::string& error) {
    return load_enemy_impl(pack, id, error);
}

std::optional<CombatSetup> load_combat_setup(const Pack& pack, const TileMap& map, std::string_view protagonist_id,
                                             std::uint64_t seed, std::string& error) {
    const auto protagonist_text = pack.read_document(protagonist_id);
    if (!protagonist_text) {
        error = "missing protagonist " + std::string(protagonist_id);
        return std::nullopt;
    }
    const auto protagonist = parse_protagonist(*protagonist_text, error);
    if (!protagonist) {
        return std::nullopt;
    }

    CombatSetup setup;
    setup.enabled = true;
    setup.seed = seed;
    setup.player.base = protagonist->base_stats;
    setup.player.growth_pm = protagonist->growth_pm;
    setup.start_inventory = protagonist->starting_inventory;
    setup.gift.mp_regen_pct = protagonist->mp_regen_pct;
    setup.gift.aggro_pct = protagonist->aggro_pct;
    setup.gift.heal_pct = protagonist->heal_pct;
    setup.gift.dodge_cooldown_pct = protagonist->dodge_cooldown_pct;
    setup.gift.death_save_ticks = protagonist->death_save_ticks;

    try {
        for (const std::string& item_id : protagonist->starting_items) {
            const auto item = document(pack, item_id, error);
            if (!item) {
                return std::nullopt;
            }
            if (item->at("kind").get<std::string>() == "weapon") {
                setup.player.weapon_atk = item->at("weapon").at("atk").get<std::int64_t>();
                setup.player.weapon_matk = item->at("weapon").at("matk").get<std::int64_t>();
                setup.start_weapon = item_id;
                break;
            }
        }
        bool found_skill = false;
        for (const std::string& skill_id : protagonist->starting_skills) {
            const auto skill = document(pack, skill_id, error);
            if (!skill) {
                return std::nullopt;
            }
            if (skill->contains("hitbox")) {
                setup.skill.startup = skill->at("timing").at("startup").get<int>();
                setup.skill.active = skill->at("timing").at("active").get<int>();
                setup.skill.recovery = skill->at("timing").at("recovery").get<int>();
                setup.skill.cooldown = skill->at("cooldown_ticks").get<int>();
                setup.skill.power_pct = skill->at("damage").at("power_pct").get<std::int64_t>();
                setup.skill.radius_x100 = skill->at("hitbox").at("radius_x100").get<int>();
                setup.skill.angle_deg = skill->at("hitbox").at("angle_deg").get<int>();
                setup.skill.magical = skill->at("damage").at("kind").get<std::string>() == "magical";
                found_skill = true;
                break;
            }
        }
        if (!found_skill) {
            error = "the protagonist has no skill with a hitbox";
            return std::nullopt;
        }
        int hitbox_skills = 0;
        for (const std::string& skill_id :
             protagonist->starting_skills) {  // the power strike: the second skill with a hitbox
            const auto skill = document(pack, skill_id, error);
            if (!skill) {
                return std::nullopt;
            }
            if (skill->contains("hitbox") && ++hitbox_skills == 2) {
                setup.strike.enabled = true;
                setup.strike.mp = skill->at("cost").at("mp").get<std::int64_t>();
                setup.strike.skill.startup = skill->at("timing").at("startup").get<int>();
                setup.strike.skill.active = skill->at("timing").at("active").get<int>();
                setup.strike.skill.recovery = skill->at("timing").at("recovery").get<int>();
                setup.strike.skill.cooldown = skill->at("cooldown_ticks").get<int>();
                setup.strike.skill.power_pct = skill->at("damage").at("power_pct").get<std::int64_t>();
                setup.strike.skill.radius_x100 = skill->at("hitbox").at("radius_x100").get<int>();
                setup.strike.skill.angle_deg = skill->at("hitbox").at("angle_deg").get<int>();
                setup.strike.skill.magical = skill->at("damage").at("kind").get<std::string>() == "magical";
                break;
            }
        }
        for (const std::string& skill_id :
             protagonist->starting_skills) {  // the dodge roll: a skill with a `movement` block
            const auto skill = document(pack, skill_id, error);
            if (!skill) {
                return std::nullopt;
            }
            if (skill->contains("movement")) {
                setup.dodge.enabled = true;
                setup.dodge.ticks = skill->at("timing").at("active").get<int>();
                setup.dodge.cooldown = skill->at("cooldown_ticks").get<int>();
                setup.dodge.speed_mult_x100 = skill->at("movement").at("speed_mult_x100").get<int>();
                setup.dodge.iframes = skill->at("movement").at("iframes").get<int>();
                break;
            }
        }
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }

    const auto table = pack.int_tables.find("base:table/xp");
    if (table != pack.int_tables.end()) {
        setup.xp_table = table->second.values;
    }

    // Story: every quest and dialogue document of the pack, and the NPCs of the map.
    for (const auto& [id, path] : pack.document_paths) {
        const bool quest = path.rfind("quests/", 0) == 0;
        const bool dialogue = path.rfind("dialogues/", 0) == 0;
        if (!quest && !dialogue) {
            continue;
        }
        const auto text = pack.read_document(id);
        if (!text) {
            error = "cannot read " + id;
            return std::nullopt;
        }
        if (quest) {
            auto parsed = parse_quest(*text, error);
            if (!parsed) {
                return std::nullopt;
            }
            setup.story.quests.emplace(id, std::move(*parsed));
        } else {
            auto parsed = parse_dialogue(*text, error);
            if (!parsed) {
                return std::nullopt;
            }
            setup.story.dialogues.emplace(id, std::move(*parsed));
        }
    }
    for (const NpcPoint& npc : map.npcs) {
        NpcDef def;
        def.key = npc.key;
        def.dialogue = npc.dialogue;
        def.variant = npc.variant;
        def.x = npc.x;
        def.y = npc.y;
        setup.story.npcs.push_back(std::move(def));
    }

    // Items that can be used (spec 06).
    for (const auto& [id, path] : pack.document_paths) {
        if (path.rfind("items/", 0) != 0) {
            continue;
        }
        const auto item = document(pack, id, error);
        if (!item) {
            return std::nullopt;
        }
        try {
            ItemDef def;
            def.kind = item->at("kind").get<std::string>();
            def.price = item->at("price").get<std::int64_t>();
            def.stack_max = item->value("stack_max", 0);
            if (item->contains("use")) {
                for (const Json& effect : item->at("use").at("effects")) {
                    def.effects.push_back(
                        {effect.at("effect").get<std::string>(), effect.value("amount", static_cast<std::int64_t>(0))});
                }
            }
            if (item->contains("weapon")) {
                def.is_weapon = true;
                def.weapon_atk = item->at("weapon").at("atk").get<std::int64_t>();
                def.weapon_matk = item->at("weapon").at("matk").get<std::int64_t>();
                def.weapon_element = item->at("weapon").value("element", "none");
            }
            if (item->contains("armor")) {
                def.is_armor = true;
                def.armor_def = item->at("armor").at("def").get<std::int64_t>();
                def.armor_mdef = item->at("armor").at("mdef").get<std::int64_t>();
            }
            setup.items.emplace(id, std::move(def));
        } catch (const Json::exception& e) {
            error = id + ": " + e.what();
            return std::nullopt;
        }
    }

    if (const auto table = pack.read_document("base:recipes/all")) {  // crafting (spec 06)
        const Json parsed = Json::parse(*table, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded() && parsed.contains("recipes")) {
            for (const Json& r : parsed.at("recipes")) {
                RecipeDef recipe;
                recipe.id = r.at("id").get<std::string>();
                recipe.output = r.at("output").at("item").get<std::string>();
                recipe.output_qty = r.at("output").at("qty").get<std::int64_t>();
                for (const Json& i : r.at("inputs")) {
                    recipe.inputs.emplace_back(i.at("item").get<std::string>(), i.at("qty").get<std::int64_t>());
                }
                setup.recipes.push_back(std::move(recipe));
            }
        }
    }
    if (const auto nodes =
            pack.read_document("base:gathering/nodes")) {  // the props that can be gathered from (spec 06)
        const Json parsed = Json::parse(*nodes, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded() && parsed.contains("nodes")) {
            for (const Json& n : parsed.at("nodes")) {
                GatherNode node;
                node.sound = n.value("sound", "plant");
                node.cooldown_ticks = n.at("cooldown_ticks").get<int>();
                node.reach_x100 = n.at("reach_x100").get<int>();
                for (const Json& d : n.at("drops")) {
                    node.drops.push_back({d.at("item").get<std::string>(), d.at("qty_min").get<std::int64_t>(),
                                          d.at("qty_max").get<std::int64_t>(), d.at("weight_pm").get<std::int64_t>()});
                }
                setup.gather_nodes[n.at("prop").get<std::string>()] = std::move(node);
            }
        }
    }

    std::map<std::string, EnemyDef> cache;
    for (const SpawnPoint& spawn : map.spawners) {
        auto found = cache.find(spawn.enemy);
        if (found == cache.end()) {
            auto def = load_enemy_impl(pack, spawn.enemy, error);
            if (!def) {
                return std::nullopt;
            }
            found = cache.emplace(spawn.enemy, std::move(*def)).first;
        }
        setup.spawns.push_back({found->second, spawn.x, spawn.y});
    }
    return setup;
}

}  // namespace aether
