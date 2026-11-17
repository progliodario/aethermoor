#include "sim/profile.hpp"

#include <algorithm>
#include <utility>
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
    if (doc.contains("lives") && doc.at("lives").is_number_integer() && doc.at("lives").get<std::int64_t>() >= 0) {
        profile.lives = static_cast<int>(doc.at("lives").get<std::int64_t>());
    }
    if (doc.contains("heirloom") && doc.at("heirloom").is_number_integer() &&
        doc.at("heirloom").get<std::int64_t>() >= 0) {
        profile.heirloom = doc.at("heirloom").get<std::int64_t>();
    }
    if (doc.contains("heirloom_item") && doc.at("heirloom_item").is_string()) {
        profile.heirloom_item = doc.at("heirloom_item").get<std::string>();
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
    doc["lives"] = profile.lives;
    doc["heirloom"] = profile.heirloom;
    if (!profile.heirloom_item.empty()) {
        doc["heirloom_item"] = profile.heirloom_item;
    }
    return doc.dump();
}

bool reincarnate(Profile& profile, std::int64_t level, std::int64_t gold, const std::string& weapon) {
    if (level < 10) {
        return false;
    }
    ++profile.lives;
    profile.heirloom += std::max<std::int64_t>(0, gold) * 50 / 100;
    if (!weapon.empty()) {
        profile.heirloom_item = weapon;
    }
    return true;
}

std::int64_t claim_heirloom(Profile& profile) {
    profile.heirloom_item.clear();
    return std::exchange(profile.heirloom, 0);
}

int profile_echo_pct(const Profile& profile, int deeds) {
    return std::min(static_cast<int>(profile.titles.size()), 15) + 3 * std::min(profile.lives, 10) + std::max(0, deeds);
}

std::vector<DeedDef> parse_deeds(std::string_view text) {
    std::vector<DeedDef> out;
    const Json doc = Json::parse(text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded()) {
        return out;
    }
    const Json* list = doc.is_array() ? &doc : (doc.is_object() && doc.contains("deeds") ? &doc.at("deeds") : nullptr);
    if (list == nullptr || !list->is_array()) {
        return out;
    }
    for (const Json& d : *list) {
        if (!d.is_object() || !d.contains("id") || !d.at("id").is_string()) {
            continue;
        }
        DeedDef deed;
        deed.id = d.at("id").get<std::string>();
        deed.kind = d.contains("kind") && d.at("kind").is_string() ? d.at("kind").get<std::string>() : "";
        deed.count = d.contains("count") && d.at("count").is_number_integer() ? d.at("count").get<std::int64_t>() : 0;
        for (const char* key : {"enemies", "titles"}) {
            if (d.contains(key) && d.at(key).is_array()) {
                for (const Json& e : d.at(key)) {
                    if (e.is_string()) {
                        deed.list.push_back(e.get<std::string>());
                    }
                }
            }
        }
        deed.name = d.contains("name") && d.at("name").is_string() ? d.at("name").get<std::string>() : "";
        deed.text = d.contains("text") && d.at("text").is_string() ? d.at("text").get<std::string>() : "";
        out.push_back(std::move(deed));
    }
    return out;
}

std::vector<std::string> profile_deeds(const Profile& profile, const std::vector<DeedDef>& defs) {
    std::vector<std::string> done;
    for (const DeedDef& deed : defs) {
        bool ok = false;
        if (deed.kind == "kills") {
            std::int64_t kills = 0;
            for (const auto& entry : profile.bestiary) {
                kills += entry.second;
            }
            ok = kills >= deed.count;
        } else if (deed.kind == "kinds") {
            ok = static_cast<std::int64_t>(profile.bestiary.size()) >= deed.count;
        } else if (deed.kind == "titles") {
            ok = static_cast<std::int64_t>(profile.titles.size()) >= deed.count;
        } else if (deed.kind == "lives") {
            ok = profile.lives >= deed.count;
        } else if (deed.kind == "defeated") {
            ok = std::all_of(deed.list.begin(), deed.list.end(), [&](const std::string& enemy) {
                const auto found = profile.bestiary.find(enemy);
                return found != profile.bestiary.end() && found->second >= 1;
            });
        } else if (deed.kind == "earned") {
            ok = std::all_of(deed.list.begin(), deed.list.end(), [&](const std::string& title) {
                return std::find(profile.titles.begin(), profile.titles.end(), title) != profile.titles.end();
            });
        }
        if (ok) {
            done.push_back(deed.id);
        }
    }
    return done;
}

}  // namespace aether
