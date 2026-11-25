#include "data/hints.hpp"

#include <nlohmann/json.hpp>

#include "data/pack.hpp"

namespace aether {

std::vector<HintDef> load_hints(const Pack& pack) {
    std::vector<HintDef> out;
    const auto text = pack.read_document("base:hints/all");
    if (!text) {
        return out;
    }
    const nlohmann::json doc = nlohmann::json::parse(*text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded() || !doc.contains("hints") || !doc.at("hints").is_array()) {
        return out;
    }
    for (const nlohmann::json& h : doc.at("hints")) {
        if (!h.is_object()) {
            continue;
        }
        HintDef hint;
        hint.id = h.value("id", "");
        hint.when = h.value("when", "");
        hint.text = h.value("text", "");
        hint.text_touch = h.value("text_touch", "");
        hint.text_pad = h.value("text_pad", "");
        if (!hint.id.empty() && !hint.text.empty()) {
            out.push_back(std::move(hint));
        }
    }
    return out;
}

std::vector<CreditLine> load_credits(const Pack& pack) {
    std::vector<CreditLine> out;
    const auto text = pack.read_document("base:credits/all");
    if (!text) {
        return out;
    }
    const nlohmann::json doc = nlohmann::json::parse(*text, nullptr, /*allow_exceptions=*/false);
    if (doc.is_discarded() || !doc.contains("sections") || !doc.at("sections").is_array()) {
        return out;
    }
    for (const nlohmann::json& section : doc.at("sections")) {
        if (!section.is_object()) {
            continue;
        }
        out.push_back({section.value("heading", ""), true});
        if (section.contains("lines") && section.at("lines").is_array()) {
            for (const nlohmann::json& line : section.at("lines")) {
                if (line.is_string()) {
                    out.push_back({line.get<std::string>(), false});
                }
            }
        }
    }
    return out;
}

}  // namespace aether
