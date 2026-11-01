#pragma once

// Content pack loading (manifest, localization tables, numeric tables).
// Spec: docs/spec/00-conventions.md and docs/spec/17-localization.md.

#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "core/message_format.hpp"

namespace aether {

// Highest data_format_version this client understands (project.json: data_format_version).
inline constexpr int kSupportedDataFormatVersion = 1;

struct PackManifest {
    std::string id;
    std::string name_key;  // "$i18n:..." reference
    std::string version;
    int data_format_version = 0;
    std::vector<std::string> languages;
    std::vector<std::string> requires_features;
};

struct IntTable {
    std::int64_t start_level = 0;
    std::vector<std::int64_t> values;
};

class Pack {
public:
    PackManifest manifest;
    std::map<std::string, std::map<std::string, std::string, std::less<>>, std::less<>> strings;
    std::map<std::string, IntTable, std::less<>> int_tables;

    // Raw message for `key` in `lang`, falling back to "en", then to the key itself.
    std::string message(std::string_view lang, std::string_view key) const;

    // Resolves "$i18n:key" (or a bare key) and formats it with `args`.
    std::string text(std::string_view lang, std::string_view reference,
                     const FormatArgs& args = {}) const;

    // XP needed to go from `level` to `level + 1`, from table "base:table/xp"; 0 if out of range.
    std::int64_t xp_to_next(std::int64_t level) const;
};

// Loads the pack in `dir`. Problems are appended to `errors`; on a fatal problem (missing or
// invalid manifest, unsupported format) the result is empty. Never throws for bad data.
std::optional<Pack> load_pack(const std::filesystem::path& dir, std::vector<std::string>& errors);

}  // namespace aether
