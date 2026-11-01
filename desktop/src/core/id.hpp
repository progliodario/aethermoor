#pragma once

#include <string_view>

namespace aether {

// namespace:category/name[/more]. Spec: docs/spec/00-conventions.md. Reference: tools/reference/ids.py.
bool valid_id(std::string_view text);

}  // namespace aether
