#pragma once

// Protagonist definitions (schemas/protagonist.schema.json). Only the fields used so far are read.

#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "core/rules.hpp"

namespace aether {

struct ProtagonistDef {
    std::string id;
    std::string name_key;
    Primary base_stats;
    Primary growth_pm;
    std::vector<std::string> starting_items;  // item IDs, in data order
    std::vector<std::string> starting_skills;
    std::map<std::string, std::int64_t> starting_inventory;  // item ID -> quantity
    int mp_regen_pct = 100;                                  // the gift rules (spec 18)
    int aggro_pct = 100;
    int heal_pct = 100;
    int dodge_cooldown_pct = 100;
    int death_save_ticks = 0;
    int companion_atk_pct = 100;
    int bond_gain = 1;
    int tame_hp_pct = 0;
    int tame_range_x100 = 0;
    int tame_bond = 0;
    std::string art_variant;  // palette variant of the character art ("" for the default)
    std::string companion;    // the ID of the companion that follows this protagonist (spec 10), or empty
    bool initially_available = true;
};

std::optional<ProtagonistDef> parse_protagonist(std::string_view json_text, std::string& error);

}  // namespace aether
