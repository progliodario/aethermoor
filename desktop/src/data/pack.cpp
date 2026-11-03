#include "data/pack.hpp"

#include <algorithm>
#include <fstream>
#include <iterator>

#include <nlohmann/json.hpp>

namespace aether {

namespace {

namespace fs = std::filesystem;
using Json = nlohmann::json;

constexpr std::string_view kI18nPrefix = "$i18n:";

std::optional<Json> read_json(const fs::path& path, std::vector<std::string>& errors) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) {
        errors.push_back(path.generic_string() + ": cannot open file");
        return std::nullopt;
    }
    Json parsed = Json::parse(stream, nullptr, /*allow_exceptions=*/false);
    if (parsed.is_discarded()) {
        errors.push_back(path.generic_string() + ": invalid JSON");
        return std::nullopt;
    }
    return parsed;
}

// All *.json files below `dir`, sorted so that loading is deterministic.
std::vector<fs::path> json_files(const fs::path& dir) {
    std::vector<fs::path> files;
    std::error_code ec;
    if (!fs::is_directory(dir, ec)) {
        return files;
    }
    for (const auto& entry : fs::recursive_directory_iterator(dir, ec)) {
        if (entry.is_regular_file() && entry.path().extension() == ".json") {
            files.push_back(entry.path());
        }
    }
    std::sort(files.begin(), files.end());
    return files;
}

std::vector<std::string> string_array(const Json& object, const char* key) {
    std::vector<std::string> out;
    if (object.contains(key) && object[key].is_array()) {
        for (const Json& item : object[key]) {
            if (item.is_string()) {
                out.push_back(item.get<std::string>());
            }
        }
    }
    return out;
}

}  // namespace

std::string Pack::message(std::string_view lang, std::string_view key) const {
    for (const std::string_view candidate : {lang, std::string_view("en")}) {
        const auto language = strings.find(candidate);
        if (language != strings.end()) {
            const auto entry = language->second.find(key);
            if (entry != language->second.end()) {
                return entry->second;
            }
        }
    }
    return std::string(key);
}

std::string Pack::text(std::string_view lang, std::string_view reference, const FormatArgs& args) const {
    std::string_view key = reference;
    if (key.substr(0, kI18nPrefix.size()) == kI18nPrefix) {
        key.remove_prefix(kI18nPrefix.size());
    }
    return format_message(message(lang, key), lang, args);
}

std::optional<std::string> Pack::read_file(std::string_view relative_path) const {
    std::ifstream stream(root / std::string(relative_path), std::ios::binary);
    if (!stream) {
        return std::nullopt;
    }
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

std::optional<std::string> Pack::read_document(std::string_view id) const {
    const auto found = document_paths.find(id);
    if (found == document_paths.end()) {
        return std::nullopt;
    }
    return read_file(found->second);
}

std::int64_t Pack::xp_to_next(std::int64_t level) const {
    const auto table = int_tables.find("base:table/xp");
    if (table == int_tables.end()) {
        return 0;
    }
    const std::int64_t index = level - table->second.start_level;
    if (index < 0 || index >= static_cast<std::int64_t>(table->second.values.size())) {
        return 0;
    }
    return table->second.values[static_cast<std::size_t>(index)];
}

std::optional<Pack> load_pack(const fs::path& dir, std::vector<std::string>& errors) {
    const auto manifest_json = read_json(dir / "pack.json", errors);
    if (!manifest_json || !manifest_json->is_object()) {
        errors.push_back((dir / "pack.json").generic_string() + ": missing or not an object");
        return std::nullopt;
    }

    Pack pack;
    pack.root = dir;
    const Json& m = *manifest_json;
    pack.manifest.id = m.value("id", "");
    pack.manifest.name_key = m.value("name", "");
    pack.manifest.version = m.value("version", "");
    pack.manifest.data_format_version = m.value("data_format_version", 0);
    pack.manifest.languages = string_array(m, "languages");
    pack.manifest.requires_features = string_array(m, "requires_features");

    if (pack.manifest.id.empty() || pack.manifest.version.empty() || pack.manifest.languages.empty()) {
        errors.push_back("pack.json: id, version and languages are required");
        return std::nullopt;
    }
    if (pack.manifest.data_format_version < 1 || pack.manifest.data_format_version > kSupportedDataFormatVersion) {
        errors.push_back("pack.json: unsupported data_format_version " +
                         std::to_string(pack.manifest.data_format_version));
        return std::nullopt;
    }

    for (const std::string& lang : pack.manifest.languages) {
        auto& table = pack.strings[lang];
        for (const fs::path& file : json_files(dir / "i18n" / lang)) {
            const auto json = read_json(file, errors);
            if (!json || !json->is_object()) {
                continue;
            }
            for (const auto& [key, value] : json->items()) {
                if (key == "$schema") {
                    continue;
                }
                if (!value.is_string()) {
                    errors.push_back(file.generic_string() + ": value of '" + key + "' is not a string");
                    continue;
                }
                if (!table.emplace(key, value.get<std::string>()).second) {
                    errors.push_back(file.generic_string() + ": duplicate key '" + key + "'");
                }
            }
        }
    }

    for (const fs::path& file : json_files(dir / "tables")) {
        const auto json = read_json(file, errors);
        if (!json || !json->is_object() || json->value("kind", "") != "int_list") {
            continue;
        }
        IntTable table;
        table.start_level = json->value("start_level", 0);
        if (json->contains("values") && (*json)["values"].is_array()) {
            for (const Json& v : (*json)["values"]) {
                if (v.is_number_integer()) {
                    table.values.push_back(v.get<std::int64_t>());
                }
            }
        }
        pack.int_tables[json->value("id", "")] = std::move(table);
    }

    for (const fs::path& file : json_files(dir)) {
        const std::string relative = fs::relative(file, dir).generic_string();
        if (relative == "pack.json" || relative.rfind("i18n/", 0) == 0) {
            continue;
        }
        const auto json = read_json(file, errors);
        if (!json || !json->is_object() || !json->contains("id") || !(*json)["id"].is_string()) {
            continue;
        }
        const std::string id = (*json)["id"].get<std::string>();
        if (!pack.document_paths.emplace(id, relative).second) {
            errors.push_back(relative + ": duplicate id '" + id + "'");
        }
    }

    return pack;
}

}  // namespace aether
