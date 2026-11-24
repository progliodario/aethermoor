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
        def.stagger_pct = enemy->value("stagger_pct", static_cast<std::int64_t>(40));
        def.sound = enemy->value("sound", "");
        if (enemy->contains("season_bonus")) {  // spec 05, "Loot": more of every plain drop in a season
            for (const auto& [season, extra] : enemy->at("season_bonus").items()) {
                def.season_bonus[season] = extra.get<int>();
            }
        }
        if (enemy->contains("weaknesses_pm")) {
            for (const auto& [element, multiplier] : enemy->at("weaknesses_pm").items()) {
                def.weaknesses_pm[element] = multiplier.get<std::int64_t>();
            }
        }
        if (enemy->contains("drops")) {
            for (const Json& drop : enemy->at("drops")) {
                def.drops.push_back({drop.at("item").get<std::string>(),
                                     drop.at("qty_min").get<std::int64_t>(),
                                     drop.at("qty_max").get<std::int64_t>(),
                                     drop.at("weight_pm").get<std::int64_t>(),
                                     {}});
                if (drop.contains("pick")) {  // one of a list (spec 05, "Loot")
                    def.drops.back().pick = drop.at("pick").get<std::vector<std::string>>();
                }
            }
        }
        const auto behavior = document(pack, enemy->at("behavior").get<std::string>(), error);
        if (!behavior) {
            return std::nullopt;
        }
        def.behavior.id = enemy->at("behavior").get<std::string>();
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
    setup.gift.companion_atk_pct = protagonist->companion_atk_pct;
    setup.gift.bond_gain = protagonist->bond_gain;
    setup.gift.tame_hp_pct = protagonist->tame_hp_pct;
    setup.gift.tame_range_x100 = protagonist->tame_range_x100;
    setup.gift.tame_bond = protagonist->tame_bond;
    setup.gift.pocket_keep_pm = protagonist->pocket_keep_pm;
    setup.gift.friend_atk_pct = protagonist->friend_atk_pct;
    if (!protagonist->companion.empty()) {  // the companion of the protagonist (spec 10)
        if (const auto companion_text = pack.read_document(protagonist->companion)) {
            const Json c = Json::parse(*companion_text, nullptr, /*allow_exceptions=*/false);
            if (!c.is_discarded() && c.contains("atk_base")) {
                CompanionDef def;
                def.id = protagonist->companion;
                def.name = c.value("name", "");
                def.art = c.value("art", "");
                def.scale_pct = c.value("scale_pct", 100);
                def.atk_base = c.at("atk_base").get<std::int64_t>();
                def.atk_per_level = c.at("atk_per_level").get<std::int64_t>();
                def.range_x100 = c.at("range_x100").get<int>();
                def.cooldown_ticks = c.at("cooldown_ticks").get<int>();
                def.speed_x100 = c.at("speed_x100").get<int>();
                def.follow_x100 = c.at("follow_x100").get<int>();
                def.care_bond = c.value("care_bond", 0);
                def.care_ticks = c.value("care_ticks", 0);
                def.care_pct = c.value("care_pct", 0);
                if (c.contains("moments")) {
                    for (const Json& m : c.at("moments")) {
                        def.moments.emplace_back(m.at("bond").get<int>(), m.at("text").get<std::string>());
                    }
                }
                setup.companion = std::move(def);
            }
        }
    }

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
                setup.skill.element = skill->at("damage").value("element", "none");
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
                setup.strike.skill.element = skill->at("damage").value("element", "none");
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
        def.route = npc.route;    // a traveller (spec 07, "Travellers")
        def.walk = npc.walk;      // and how it walks (spec 07, "Travellers walk")
        if (!npc.when.empty()) {  // a resident (spec 07, "Residents")
            def.when = parse_condition_text(npc.when, error);
            if (!def.when) {
                error = npc.key + ": " + error;
                return std::nullopt;
            }
        }
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
                    def.effects.push_back({effect.at("effect").get<std::string>(),
                                           effect.value("amount", static_cast<std::int64_t>(0)),
                                           effect.value("ticks", 0)});
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
            if (item->contains("accessory")) {
                const Json& a = item->at("accessory");
                def.is_accessory = true;
                def.acc_atk = a.value("atk", static_cast<std::int64_t>(0));
                def.acc_matk = a.value("matk", static_cast<std::int64_t>(0));
                def.acc_def = a.value("def", static_cast<std::int64_t>(0));
                def.acc_mdef = a.value("mdef", static_cast<std::int64_t>(0));
                def.acc_max_hp = a.value("max_hp", static_cast<std::int64_t>(0));
                def.acc_crit_pm = a.value("crit_pm", static_cast<std::int64_t>(0));
                def.acc_drain_pm = a.value("drain_pm", static_cast<std::int64_t>(0));
            }
            if ((*item).contains(
                    "affix")) {  // spec 06, "Affixes": flat bonuses of a weapon or an armor, like an accessory's
                const Json& f = (*item).at("affix");
                def.has_affix = true;
                def.aff_atk = f.value("atk", static_cast<std::int64_t>(0));
                def.aff_matk = f.value("matk", static_cast<std::int64_t>(0));
                def.aff_def = f.value("def", static_cast<std::int64_t>(0));
                def.aff_mdef = f.value("mdef", static_cast<std::int64_t>(0));
                def.aff_max_hp = f.value("max_hp", static_cast<std::int64_t>(0));
                def.aff_crit_pm = f.value("crit_pm", static_cast<std::int64_t>(0));
                def.aff_drain_pm = f.value("drain_pm", static_cast<std::int64_t>(0));
            }
            if (item->contains("affix_roll")) {  // spec 06, "Rolled affixes": how strong it comes out when found
                const Json& r = item->at("affix_roll");
                def.has_affix_roll = true;
                def.roll_min_pct = r.at("min_pct").get<std::int64_t>();
                def.roll_max_pct = r.at("max_pct").get<std::int64_t>();
            }
            if (item->contains("rune")) {  // spec 06, "Runes"
                const Json& r = item->at("rune");
                def.is_rune = true;
                def.rune_element = r.value("element", "none");
                def.rune_atk = r.value("atk", static_cast<std::int64_t>(0));
                def.rune_matk = r.value("matk", static_cast<std::int64_t>(0));
                def.rune_station = r.value("station", "");
            }
            if (item->contains("temper")) {  // spec 06, "Tempering"
                def.is_temper = true;
                def.temper_station = item->at("temper").value("station", "");
            }
            if (item->contains("reforge")) {  // spec 06, "Choosing an affix"
                def.is_reforge = true;
                def.reforge_station = item->at("reforge").value("station", "");
            }
            def.affix_family = item->value("affix_family", "");
            if (item->contains("furniture")) {  // spec 06, "Furniture"
                const Json& f = item->at("furniture");
                def.is_furniture = true;
                def.furniture_art = f.value("art", "");
                def.fur_atk_pct = f.value("atk_pct", static_cast<std::int64_t>(0));
                def.fur_gather_bonus = f.value("gather_bonus", static_cast<std::int64_t>(0));
                def.fur_craft_bonus = f.value("craft_bonus", static_cast<std::int64_t>(0));
                def.fur_parry_bonus = f.value("parry_bonus", static_cast<std::int64_t>(0));
                def.fur_xp_pct = f.value("xp_pct", static_cast<std::int64_t>(0));
                def.fur_fine_pm = f.value("fine_pm", static_cast<std::int64_t>(0));
            }
            setup.items.emplace(id, std::move(def));
        } catch (const Json::exception& e) {
            error = id + ": " + e.what();
            return std::nullopt;
        }
    }

    if (const auto recipe_table = pack.read_document("base:recipes/all")) {  // crafting (spec 06)
        const Json parsed = Json::parse(*recipe_table, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded() && parsed.contains("recipes")) {
            for (const Json& r : parsed.at("recipes")) {
                RecipeDef recipe;
                recipe.id = r.at("id").get<std::string>();
                recipe.output = r.at("output").at("item").get<std::string>();
                recipe.output_qty = r.at("output").at("qty").get<std::int64_t>();
                recipe.station = r.value("station", "");
                recipe.fine_pm = r.value("fine_pm", static_cast<std::int64_t>(0));
                recipe.fine_item = r.value("fine_item", "");
                recipe.requires_flag = r.value("requires_flag", "");
                for (const Json& i : r.at("inputs")) {
                    recipe.inputs.emplace_back(i.at("item").get<std::string>(), i.at("qty").get<std::int64_t>());
                }
                setup.recipes.push_back(std::move(recipe));
            }
        }
    }
    if (const auto talent_table = pack.read_document("base:talents/all")) {  // talents (spec 11)
        const Json parsed = Json::parse(*talent_table, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded() && parsed.contains("talents")) {
            setup.talent_points_per_level = parsed.value("points_per_level", 1);
            for (const Json& t : parsed.at("talents")) {
                TalentDef talent;
                talent.id = t.at("id").get<std::string>();
                talent.name = t.at("name").get<std::string>();
                talent.stat = t.at("stat").get<std::string>();
                talent.pct_per_rank = t.at("pct_per_rank").get<std::int64_t>();
                talent.max_rank = t.at("max_rank").get<int>();
                if (t.contains("requires")) {
                    talent.requires_talent = t.at("requires").at("talent").get<std::string>();
                    talent.requires_rank = t.at("requires").at("rank").get<int>();
                }
                if (t.contains("active")) {
                    talent.has_active = true;
                    talent.active_mp = t.at("active").at("mp").get<std::int64_t>();
                    talent.active_cooldown = t.at("active").at("cooldown_ticks").get<int>();
                    talent.active_radius_x100 = t.at("active").value("radius_x100", 0);
                }
                setup.talents.push_back(std::move(talent));
            }
        }
    }
    // titles (spec 11) and tags (spec 11, "Tags"), which have the same fields
    for (const auto& [doc_id, list_key] : {std::pair<const char*, const char*>{"base:titles/all", "titles"},
                                           std::pair<const char*, const char*>{"base:tags/all", "tags"}}) {
        const auto title_table = pack.read_document(doc_id);
        if (!title_table) {
            continue;
        }
        const Json parsed = Json::parse(*title_table, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded() && parsed.contains(list_key)) {
            for (const Json& t : parsed.at(list_key)) {
                TitleDef title;
                title.id = t.at("id").get<std::string>();
                title.name = t.at("name").get<std::string>();
                title.kind = t.at("kind").get<std::string>();
                title.count = t.at("count").get<std::int64_t>();
                title.enemy = t.value("enemy", "");
                title.atk_pct = t.value("atk_pct", static_cast<std::int64_t>(0));
                title.gather_bonus = t.value("gather_bonus", static_cast<std::int64_t>(0));
                title.craft_bonus = t.value("craft_bonus", static_cast<std::int64_t>(0));
                title.parry_bonus = t.value("parry_bonus", static_cast<std::int64_t>(0));
                title.xp_pct = t.value("xp_pct", static_cast<std::int64_t>(0));
                title.fine_pm = t.value("fine_pm", static_cast<std::int64_t>(0));
                (std::string(list_key) == "tags" ? setup.tags : setup.titles).push_back(std::move(title));
            }
        }
    }
    if (const auto chests = pack.read_document("base:storage/chests")) {  // the chests (spec 06, "Chests")
        const Json parsed = Json::parse(*chests, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded()) {
            setup.chest_art = parsed.value("chest", "");
            setup.chest_reach_x100 = parsed.value("reach_x100", 200);
        }
    }
    if (const auto home = pack.read_document("base:home/cottage")) {  // the furniture spots (spec 06, "Furniture")
        const Json parsed = Json::parse(*home, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded()) {
            setup.home_spot = parsed.value("spot", "");
            setup.home_reach_x100 = parsed.value("reach_x100", 200);
        }
    }
    if (const auto farm = pack.read_document("base:farming/all")) {  // the plots and the crops (spec 06, "Farming")
        const Json parsed = Json::parse(*farm, nullptr, /*allow_exceptions=*/false);
        if (!parsed.is_discarded() && parsed.contains("crops")) {
            FarmingDef farming;
            farming.plot = parsed.value("plot", "");
            farming.reach_x100 = parsed.value("reach_x100", 150);
            farming.rain_grow_cut_pm = parsed.value("rain_grow_cut_pm", 0);
            if (parsed.contains("season_grow_pm")) {  // spec 06, "Seasons on the plots"
                for (const auto& [season, pm] : parsed.at("season_grow_pm").items()) {
                    farming.season_grow_pm[season] = pm.get<int>();
                }
            }
            for (const Json& c : parsed.at("crops")) {
                farming.crops.push_back({c.at("seed").get<std::string>(), c.at("crop").get<std::string>(),
                                         c.at("qty_min").get<std::int64_t>(), c.at("qty_max").get<std::int64_t>(),
                                         c.at("grow_ticks").get<std::int64_t>()});
            }
            setup.farming = std::move(farming);
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
                if (n.contains("season_bonus")) {  // spec 06, "Seasons of the gathering"
                    for (const auto& [season, extra] : n.at("season_bonus").items()) {
                        node.season_bonus[season] = extra.get<int>();
                    }
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
