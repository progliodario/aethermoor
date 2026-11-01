#pragma once

#include <string>
#include <string_view>

namespace aether {

// Name and version come from project.json at configure time (single source of truth).
std::string_view game_name();
std::string_view game_version();

// "<name> <version>", for window titles and logs.
std::string version_line();

}  // namespace aether
