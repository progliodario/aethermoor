#pragma once

// World generation parameters (schemas/world.schema.json) read from JSON.

#include <optional>
#include <string>
#include <string_view>

#include "core/worldgen.hpp"

namespace aether {

std::optional<WorldParams> parse_world_params(std::string_view json_text, std::string& error);

}  // namespace aether
