#pragma once

#include <array>
#include <string_view>

namespace aether {

// Features this client implements (see ADR 0009). Must match the parity rules in docs.
// Empty on purpose: the two clients are kept equal by the shared specs and conformance vectors, and no feature is gated
// yet.
inline constexpr std::array<std::string_view, 0> kSupportedFeatures{};

}  // namespace aether
