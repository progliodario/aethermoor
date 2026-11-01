#include <catch2/catch_test_macros.hpp>

#include <filesystem>
#include <string>
#include <vector>

#include "data/pack.hpp"

namespace {

const std::filesystem::path kRepoRoot = AETHER_REPO_ROOT;

aether::Pack load_base() {
    std::vector<std::string> errors;
    auto pack = aether::load_pack(kRepoRoot / "data" / "base", errors);
    REQUIRE(errors.empty());
    REQUIRE(pack.has_value());
    return *pack;
}

}  // namespace

TEST_CASE("base pack manifest", "[data]") {
    const aether::Pack pack = load_base();
    REQUIRE(pack.manifest.id == "base");
    REQUIRE(pack.manifest.data_format_version == 1);
    REQUIRE(pack.manifest.languages == std::vector<std::string>{"it", "en"});
}

TEST_CASE("pack localization", "[data]") {
    const aether::Pack pack = load_base();
    REQUIRE(pack.text("it", "$i18n:game.title") == "Aethermoor");
    REQUIRE(pack.text("en", "$i18n:game.subtitle") == "Chronicles of Another World");
    REQUIRE(pack.text("it", "$i18n:ui.version", {{"version", std::string("0.1.0")}}) == "Versione 0.1.0");
    REQUIRE(pack.text("it", "$i18n:item.bread.name", {{"count", std::int64_t{1}}}) == "Pane");
    REQUIRE(pack.text("it", "$i18n:item.bread.name", {{"count", std::int64_t{3}}}) == "Pani");
    REQUIRE(pack.text("en", "$i18n:item.bread.name", {{"count", std::int64_t{3}}}) == "Breads");
}

TEST_CASE("pack localization falls back to the key", "[data]") {
    const aether::Pack pack = load_base();
    REQUIRE(pack.text("it", "$i18n:no.such.key") == "no.such.key");
    // An unknown language falls back to English.
    REQUIRE(pack.text("fr", "$i18n:game.subtitle") == "Chronicles of Another World");
}

TEST_CASE("xp table", "[data]") {
    const aether::Pack pack = load_base();
    REQUIRE(pack.xp_to_next(1) == 50);
    REQUIRE(pack.xp_to_next(2) == 130);
    REQUIRE(pack.xp_to_next(98) == 47994);
    REQUIRE(pack.xp_to_next(99) == 0);
    REQUIRE(pack.xp_to_next(0) == 0);
}

TEST_CASE("missing pack reports an error instead of crashing", "[data]") {
    std::vector<std::string> errors;
    const auto pack = aether::load_pack(kRepoRoot / "data" / "does_not_exist", errors);
    REQUIRE_FALSE(pack.has_value());
    REQUIRE_FALSE(errors.empty());
}
