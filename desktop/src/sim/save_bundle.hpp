#pragma once

// The save bundle: the files of a slot packed into one `.aethersave` text, to move a game between devices.
// Spec: docs/spec/12-save-format.md ("Export and import"). Headless.

#include <map>
#include <optional>
#include <string>
#include <string_view>

namespace aether {

// The names of the files of a slot that a bundle may hold.
bool is_bundle_file(std::string_view name);

// Packs the files of a slot (those with an allowed name; the others are left out).
std::string export_bundle(const std::map<std::string, std::string>& files, std::string_view game_version);

// The files of a bundle, or nullopt when it is not a valid one.
std::optional<std::map<std::string, std::string>> import_bundle(std::string_view text);

}  // namespace aether
