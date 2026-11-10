#include "sim/profile.hpp"

#include <algorithm>
#include <nlohmann/json.hpp>

namespace aether {

namespace {
using Json = nlohmann::json;
}  // namespace

Profile parse_profile(std::string_view text) {
    Profile profile;
    const Json doc = Json::parse(text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded() || !doc.is_object() || !doc.contains("profile_version") ||
        !doc.at("profile_version").is_number_integer() || doc.at("profile_version").get<std::int64_t>() != 1) {
        return profile;
    }
    if (doc.contains("bestiary") && doc.at("bestiary").is_object()) {
        for (const auto& [name, count] : doc.at("bestiary").items()) {
            if (count.is_number_integer() && count.get<std::int64_t>() >= 1) {
                profile.bestiary[name] = static_cast<int>(count.get<std::int64_t>());
            }
        }
    }
    if (doc.contains("titles") && doc.at("titles").is_array()) {
        for (const Json& title : doc.at("titles")) {
            if (title.is_string() && std::find(profile.titles.begin(), profile.titles.end(),
                                               title.get<std::string>()) == profile.titles.end()) {
                profile.titles.push_back(title.get<std::string>());
            }
        }
    }
    return profile;
}

Profile merge_profile(const Profile& profile, const std::map<std::string, int>& bestiary,
                      const std::vector<std::string>& titles) {
    Profile merged = profile;
    for (const auto& [name, count] : bestiary) {
        if (count >= 1) {
            int& best = merged.bestiary[name];
            best = std::max(best, count);
        }
    }
    for (const std::string& title : titles) {
        if (std::find(merged.titles.begin(), merged.titles.end(), title) == merged.titles.end()) {
            merged.titles.push_back(title);
        }
    }
    return merged;
}

std::string profile_to_json(const Profile& profile) {
    Json doc = Json::object();
    doc["profile_version"] = 1;
    Json bestiary = Json::object();
    for (const auto& [name, count] : profile.bestiary) {
        bestiary[name] = count;
    }
    doc["bestiary"] = bestiary;
    doc["titles"] = profile.titles;
    return doc.dump();
}

}  // namespace aether
