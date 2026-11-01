#include "core/id.hpp"

#include <algorithm>
#include <cstddef>

namespace aether {

namespace {

bool is_lower(char c) { return c >= 'a' && c <= 'z'; }
bool is_digit(char c) { return c >= '0' && c <= '9'; }
bool is_word_char(char c) { return is_lower(c) || is_digit(c) || c == '_'; }

// [a-z][a-z0-9_]*
bool is_ident(std::string_view s) {
    return !s.empty() && is_lower(s.front()) && std::all_of(s.begin(), s.end(), is_word_char);
}

// [a-z0-9_]+
bool is_word(std::string_view s) {
    return !s.empty() && std::all_of(s.begin(), s.end(), is_word_char);
}

}  // namespace

bool valid_id(std::string_view text) {
    if (std::count(text.begin(), text.end(), ':') != 1) {
        return false;
    }
    const std::size_t colon = text.find(':');
    if (!is_ident(text.substr(0, colon))) {
        return false;
    }
    std::string_view path = text.substr(colon + 1);
    const std::size_t first_slash = path.find('/');
    if (first_slash == std::string_view::npos || !is_ident(path.substr(0, first_slash))) {
        return false;
    }
    path.remove_prefix(first_slash + 1);
    for (;;) {
        const std::size_t slash = path.find('/');
        if (!is_word(path.substr(0, slash))) {
            return false;
        }
        if (slash == std::string_view::npos) {
            return true;
        }
        path.remove_prefix(slash + 1);
    }
}

}  // namespace aether
