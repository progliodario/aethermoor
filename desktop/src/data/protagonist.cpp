#include "data/protagonist.hpp"

#include <nlohmann/json.hpp>

namespace aether {

std::optional<ProtagonistDef> parse_protagonist(std::string_view json_text, std::string& error) {
    using Json = nlohmann::json;
    try {
        const Json j = Json::parse(json_text);
        ProtagonistDef def;
        def.id = j.at("id").get<std::string>();
        def.name_key = j.value("name", "");
        const Json& s = j.at("base_stats");
        def.base_stats = Primary{s.at("str").get<std::int64_t>(), s.at("vit").get<std::int64_t>(),
                                 s.at("dex").get<std::int64_t>(), s.at("agi").get<std::int64_t>(),
                                 s.at("int").get<std::int64_t>(), s.at("wis").get<std::int64_t>(),
                                 s.at("luk").get<std::int64_t>()};
        return def;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

}  // namespace aether
