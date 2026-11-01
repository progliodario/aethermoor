#include <catch2/catch_test_macros.hpp>

#include "core/version.hpp"

TEST_CASE("version line combines name and version", "[core]") {
    const std::string line = aether::version_line();
    REQUIRE_FALSE(aether::game_name().empty());
    REQUIRE_FALSE(aether::game_version().empty());
    REQUIRE(line == std::string(aether::game_name()) + " " + std::string(aether::game_version()));
}

TEST_CASE("version looks like semver", "[core]") {
    const auto version = aether::game_version();
    REQUIRE(version.find('.') != std::string_view::npos);
    REQUIRE(version.front() >= '0');
    REQUIRE(version.front() <= '9');
}
