#pragma once

// Protagonist definitions (schemas/protagonist.schema.json). Only the fields used so far are read.

#include <optional>
#include <string>
#include <string_view>

#include "core/rules.hpp"

namespace aether {

struct ProtagonistDef {
    std::string id;
    std::string name_key;
    Primary base_stats;
};

std::optional<ProtagonistDef> parse_protagonist(std::string_view json_text, std::string& error);

}  // namespace aether
