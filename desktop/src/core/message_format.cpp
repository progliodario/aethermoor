#include "core/message_format.hpp"

#include <cstddef>
#include <optional>
#include <vector>

namespace aether {

namespace {

constexpr std::size_t kNpos = std::string_view::npos;

bool is_space(char c) { return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\f' || c == '\v'; }

std::string_view trim(std::string_view s) {
    while (!s.empty() && is_space(s.front())) {
        s.remove_prefix(1);
    }
    while (!s.empty() && is_space(s.back())) {
        s.remove_suffix(1);
    }
    return s;
}

std::string_view plural_category(std::int64_t n) { return n == 1 ? "one" : "other"; }

// Index of the '}' that closes the '{' at `start`, or kNpos.
std::size_t matching_brace(std::string_view text, std::size_t start) {
    int depth = 0;
    for (std::size_t i = start; i < text.size(); ++i) {
        if (text[i] == '{') {
            ++depth;
        } else if (text[i] == '}') {
            --depth;
            if (depth == 0) {
                return i;
            }
        }
    }
    return kNpos;
}

std::vector<std::string_view> split_top_level_commas(std::string_view body, std::size_t limit) {
    std::vector<std::string_view> parts;
    int depth = 0;
    std::size_t begin = 0;
    for (std::size_t i = 0; i < body.size(); ++i) {
        const char ch = body[i];
        if (ch == '{') {
            ++depth;
        } else if (ch == '}') {
            --depth;
        }
        if (ch == ',' && depth == 0 && parts.size() < limit) {
            parts.push_back(body.substr(begin, i - begin));
            begin = i + 1;
        }
    }
    parts.push_back(body.substr(begin));
    return parts;
}

using Branches = std::map<std::string, std::string, std::less<>>;

std::optional<Branches> parse_branches(std::string_view spec) {
    Branches branches;
    std::size_t i = 0;
    const std::size_t n = spec.size();
    while (i < n) {
        while (i < n && is_space(spec[i])) {
            ++i;
        }
        if (i >= n) {
            break;
        }
        const std::size_t start = i;
        while (i < n && !is_space(spec[i]) && spec[i] != '{') {
            ++i;
        }
        const std::string selector(spec.substr(start, i - start));
        while (i < n && is_space(spec[i])) {
            ++i;
        }
        if (selector.empty() || i >= n || spec[i] != '{') {
            return std::nullopt;
        }
        const std::size_t end = matching_brace(spec, i);
        if (end == kNpos) {
            return std::nullopt;
        }
        branches[selector] = std::string(spec.substr(i + 1, end - i - 1));
        i = end + 1;
    }
    return branches;
}

std::string format_impl(std::string_view message, std::string_view lang, const FormatArgs& args,
                        std::optional<std::int64_t> pound);

std::string arg_to_string(const FormatArg& value) {
    if (const auto* number = std::get_if<std::int64_t>(&value)) {
        return std::to_string(*number);
    }
    return std::get<std::string>(value);
}

std::string format_argument(std::string_view body, std::string_view lang, const FormatArgs& args) {
    const std::vector<std::string_view> parts = split_top_level_commas(body, 2);
    const std::string_view name = trim(parts[0]);
    const std::string verbatim = "{" + std::string(body) + "}";
    const auto found = args.find(name);
    if (found == args.end()) {
        return verbatim;
    }
    const FormatArg& value = found->second;
    if (parts.size() == 1) {
        return arg_to_string(value);
    }
    const std::string_view kind = trim(parts[1]);
    std::optional<Branches> branches;
    if (parts.size() > 2) {
        branches = parse_branches(parts[2]);
    }
    if (!branches) {
        return verbatim;
    }
    if (kind == "plural" && std::holds_alternative<std::int64_t>(value)) {
        const std::int64_t n = std::get<std::int64_t>(value);
        auto chosen = branches->find("=" + std::to_string(n));
        if (chosen == branches->end()) {
            chosen = branches->find(plural_category(n));
            if (chosen == branches->end()) {
                chosen = branches->find("other");
            }
        }
        if (chosen == branches->end()) {
            return "";
        }
        return format_impl(chosen->second, lang, args, n);
    }
    if (kind == "select") {
        auto chosen = branches->find(arg_to_string(value));
        if (chosen == branches->end()) {
            chosen = branches->find("other");
        }
        if (chosen == branches->end()) {
            return "";
        }
        return format_impl(chosen->second, lang, args, std::nullopt);
    }
    return verbatim;
}

std::string format_impl(std::string_view message, std::string_view lang, const FormatArgs& args,
                        std::optional<std::int64_t> pound) {
    std::string out;
    std::size_t i = 0;
    const std::size_t n = message.size();
    while (i < n) {
        const char ch = message[i];
        if (ch == '{') {
            if (i + 1 < n && message[i + 1] == '{') {
                out += '{';
                i += 2;
                continue;
            }
            const std::size_t end = matching_brace(message, i);
            if (end == kNpos) {
                out += message.substr(i);
                break;
            }
            out += format_argument(message.substr(i + 1, end - i - 1), lang, args);
            i = end + 1;
        } else if (ch == '}' && i + 1 < n && message[i + 1] == '}') {
            out += '}';
            i += 2;
        } else if (ch == '#' && pound.has_value()) {
            out += std::to_string(*pound);
            ++i;
        } else {
            out += ch;
            ++i;
        }
    }
    return out;
}

}  // namespace

std::string format_message(std::string_view message, std::string_view lang, const FormatArgs& args) {
    return format_impl(message, lang, args, std::nullopt);
}

}  // namespace aether
