#pragma once

// World generation parameters (schemas/world.schema.json) read from JSON.

#include <optional>
#include <string>
#include <string_view>

#include "core/worldgen.hpp"

namespace aether {

std::optional<WorldParams> parse_world_params(std::string_view json_text, std::string& error);

class Pack;

// Reads the world document `world_id` of the pack and resolves the stamps of its settlements from the pack too.
std::optional<WorldParams> load_world_params(const Pack& pack, std::string_view world_id, std::string& error);

}  // namespace aether
