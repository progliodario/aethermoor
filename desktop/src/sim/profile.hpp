#pragma once

// The profile: what is kept across games in `profile.json` next to the settings (the best count of every creature
// killed and every title ever earned). Spec: docs/spec/12-save-format.md ("Profile"). Headless.

#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <vector>

namespace aether {

struct Profile {
    std::map<std::string, int> bestiary;
    std::vector<std::string> titles;  // in the order they were first earned
    int lives = 0;                    // the games that were reincarnated (spec 11, "Reincarnation")
    std::int64_t heirloom = 0;        // gold that waits for the next new game (spec 11, "Heirloom")
    std::string heirloom_item;        // the weapon that waits for it too; empty: none
};

// The profile in a text; a missing or broken text gives an empty profile, and entries that make no sense are left out.
Profile parse_profile(std::string_view text);

// The profile after a game reports its bestiary and titles: the best count of every creature, every title ever earned.
Profile merge_profile(const Profile& profile, const std::map<std::string, int>& bestiary,
                      const std::vector<std::string>& titles);

std::string profile_to_json(const Profile& profile);

// A game of `level` is reincarnated: one more past life. False, changing nothing, when the level is below 10.
// Half of the game's gold waits in the profile for the next new game (the heirloom), and the weapon in hand too (it
// replaces one already waiting; an empty one keeps it).
bool reincarnate(Profile& profile, std::int64_t level, std::int64_t gold = 0, const std::string& weapon = "");

// A new game takes the heirloom: the gold it starts with (the weapon is `heirloom_item`, read before); the profile
// keeps nothing more.
std::int64_t claim_heirloom(Profile& profile);

// The percent of maximum health that the profile gives to every game: one for each title (up to 15) and three for each
// past life (up to 10). Spec 11, "Echoes".
int profile_echo_pct(const Profile& profile);

}  // namespace aether
