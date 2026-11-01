#pragma once

// Builds the combat setup of a protagonist on a map from the content pack (spec 05, "Data used").

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

#include "data/pack.hpp"
#include "sim/combat.hpp"
#include "sim/tilemap.hpp"

namespace aether {

// Reads the protagonist, its first weapon and first skill with a hitbox, the enemies named by the map spawners
// (with their behaviors) and the XP table. On failure returns nullopt and sets `error`.
std::optional<CombatSetup> load_combat_setup(const Pack& pack, const TileMap& map, std::string_view protagonist_id,
                                             std::uint64_t seed, std::string& error);

// One enemy document with its behavior (used by streamed worlds, which have no spawner list).
std::optional<EnemyDef> load_enemy_def(const Pack& pack, const std::string& id, std::string& error);

}  // namespace aether
