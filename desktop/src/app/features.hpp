#pragma once

#include <array>
#include <string_view>

namespace aether {

// Features this client implements (see ADR 0009). Must match the parity rules in docs.
// M0: nothing is implemented yet.
inline constexpr std::array<std::string_view, 0> kSupportedFeatures{};

}  // namespace aether
