#include "sim/save_bundle.hpp"

#include <nlohmann/json.hpp>

namespace aether {

namespace {
using Json = nlohmann::json;
constexpr const char* kNames[] = {"auto.json", "quick.json", "protagonist.txt", "goal.txt"};
}  // namespace

bool is_bundle_file(std::string_view name) {
    for (const char* allowed : kNames) {
        if (name == allowed) {
            return true;
        }
    }
    return false;
}

std::string export_bundle(const std::map<std::string, std::string>& files, std::string_view game_version) {
    Json packed = Json::object();
    for (const char* name : kNames) {
        const auto found = files.find(name);
        if (found != files.end()) {
            packed[name] = found->second;
        }
    }
    Json doc = Json::object();
    doc["aethersave"] = 1;
    doc["game_version"] = std::string(game_version);
    doc["files"] = std::move(packed);
    return doc.dump();
}

std::optional<std::map<std::string, std::string>> import_bundle(std::string_view text) {
    const Json doc = Json::parse(text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded() || !doc.is_object() || !doc.contains("aethersave") ||
        !doc.at("aethersave").is_number_integer() || doc.at("aethersave").get<std::int64_t>() != 1 ||
        !doc.contains("files") || !doc.at("files").is_object()) {
        return std::nullopt;
    }
    std::map<std::string, std::string> out;
    for (const auto& [name, content] : doc.at("files").items()) {
        if (!is_bundle_file(name) || !content.is_string()) {
            return std::nullopt;
        }
        out[name] = content.get<std::string>();
    }
    bool has_save = false;
    for (const char* name : {"auto.json", "quick.json"}) {
        const auto found = out.find(name);
        if (found == out.end()) {
            continue;
        }
        has_save = true;
        const Json save = Json::parse(found->second, nullptr, /*allow_exceptions=*/false);
        if (save.is_discarded() || !save.is_object() || !save.contains("save_version") ||
            !save.at("save_version").is_number_integer()) {
            return std::nullopt;
        }
    }
    if (!has_save) {
        return std::nullopt;
    }
    return out;
}

}  // namespace aether
