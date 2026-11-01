#include "core/version.hpp"

namespace aether {

std::string_view game_name() { return AETHER_GAME_NAME; }

std::string_view game_version() { return AETHER_GAME_VERSION; }

std::string version_line() {
    std::string line(game_name());
    line += ' ';
    line += game_version();
    return line;
}

}  // namespace aether
