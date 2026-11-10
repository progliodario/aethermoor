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
};

// The profile in a text; a missing or broken text gives an empty profile, and entries that make no sense are left out.
Profile parse_profile(std::string_view text);

// The profile after a game reports its bestiary and titles: the best count of every creature, every title ever earned.
Profile merge_profile(const Profile& profile, const std::map<std::string, int>& bestiary,
                      const std::vector<std::string>& titles);

std::string profile_to_json(const Profile& profile);

// A game of `level` is reincarnated: one more past life. False, changing nothing, when the level is below 10.
bool reincarnate(Profile& profile, std::int64_t level);

// The percent of maximum health that the profile gives to every game: one for each title (up to 15) and three for each
// past life (up to 10). Spec 11, "Echoes".
int profile_echo_pct(const Profile& profile);

}  // namespace aether
