#pragma once

// ICU-like message formatting. Spec: docs/spec/17-localization.md.
// Reference: tools/reference/i18n.py.

#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <variant>

namespace aether {

using FormatArg = std::variant<std::int64_t, std::string>;
using FormatArgs = std::map<std::string, FormatArg, std::less<>>;

std::string format_message(std::string_view message, std::string_view lang, const FormatArgs& args);

}  // namespace aether
