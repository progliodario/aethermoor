#pragma once

// Save files. Spec: docs/spec/12-save-format.md. Schema: schemas/save.schema.json.

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

#include "sim/world.hpp"

namespace aether {

inline constexpr int kSaveVersion = 1;

struct SaveMeta {
    std::string game_version;
    int data_format_version = 1;
    std::string protagonist;
    std::uint64_t seed = 0;
};

// Pretty-printed JSON text of the save document.
std::string save_to_json(const SaveState& state, const SaveMeta& meta);

// Parses a save document. On failure (invalid JSON, missing field, newer save_version) returns nullopt and sets `error`.
std::optional<SaveState> save_from_json(std::string_view json_text, std::string& error);

}  // namespace aether
