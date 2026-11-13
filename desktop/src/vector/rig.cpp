#include "vector/rig.hpp"

#include <cmath>
#include <cstddef>

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

constexpr double kPi = 3.14159265358979323846;

template <typename Key, typename Pick>
float interpolate(const std::vector<Key>& keys, float t, Pick pick, std::size_t width, float* out) {
    // `pick(key, i)` returns component i (0-based) of a keyframe. Writes `width` values to `out`.
    if (keys.empty()) {
        for (std::size_t i = 0; i < width; ++i) {
            out[i] = 0.0F;
        }
        return 0.0F;
    }
    if (t <= keys.front().tick) {
        for (std::size_t i = 0; i < width; ++i) {
            out[i] = pick(keys.front(), i);
        }
        return 0.0F;
    }
    if (t >= keys.back().tick) {
        for (std::size_t i = 0; i < width; ++i) {
            out[i] = pick(keys.back(), i);
        }
        return 0.0F;
    }
    for (std::size_t k = 0; k + 1 < keys.size(); ++k) {
        const Key& a = keys[k];
        const Key& b = keys[k + 1];
        if (a.tick <= t && t <= b.tick) {
            const float span = b.tick - a.tick;
            const float u = span == 0.0F ? 0.0F : (t - a.tick) / span;
            for (std::size_t i = 0; i < width; ++i) {
                out[i] = pick(a, i) + (pick(b, i) - pick(a, i)) * u;
            }
            return 0.0F;
        }
    }
    for (std::size_t i = 0; i < width; ++i) {
        out[i] = 0.0F;
    }
    return 0.0F;
}

float pick_rot(const RotKey& key, std::size_t) { return key.degrees; }

float pick_pos(const PosKey& key, std::size_t i) { return i == 0 ? key.x : key.y; }

}  // namespace

std::optional<Rig> parse_rig(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        Rig rig;
        rig.id = j.value("id", "");
        for (const Json& p : j.at("parts")) {
            RigPart part;
            part.id = p.at("id").get<std::string>();
            if (!p.at("parent").is_null()) {
                part.parent = p.at("parent").get<std::string>();
            }
            part.offset_x = p.at("offset").at(0).get<float>();
            part.offset_y = p.at("offset").at(1).get<float>();
            part.z = p.value("z", 0);
            part.art = p.at("art").get<std::string>();
            part.art_back = p.value("art_back", part.art);
            part.z_back = p.value("z_back", part.z);
            part.art_side = p.value("art_side", part.art);
            part.z_side = p.value("z_side", part.z);
            part.offset_side_x = part.offset_x;
            part.offset_side_y = part.offset_y;
            if (p.contains("offset_side")) {
                part.offset_side_x = p.at("offset_side").at(0).get<float>();
                part.offset_side_y = p.at("offset_side").at(1).get<float>();
            }
            rig.parts.push_back(std::move(part));
        }
        return rig;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::optional<Clip> parse_clip(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        Clip clip;
        clip.id = j.value("id", "");
        clip.rig = j.value("rig", "");
        clip.loop = j.value("loop", false);
        clip.length_ticks = j.at("length_ticks").get<int>();
        for (const auto& [part, track_json] : j.at("tracks").items()) {
            Track track;
            if (track_json.contains("rot")) {
                for (const Json& k : track_json.at("rot")) {
                    track.rot.push_back({k.at(0).get<float>(), k.at(1).get<float>()});
                }
            }
            if (track_json.contains("pos")) {
                for (const Json& k : track_json.at("pos")) {
                    track.pos.push_back({k.at(0).get<float>(), k.at(1).get<float>(), k.at(2).get<float>()});
                }
            }
            clip.tracks[part] = std::move(track);
        }
        return clip;
    } catch (const Json::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::vector<PosedPart> evaluate_pose(const Rig& rig, const Clip& clip, float tick, bool mirror, bool side) {
    float t = tick;
    const auto length = static_cast<float>(clip.length_ticks);
    if (clip.loop) {
        t = std::fmod(tick, length);
        if (t < 0.0F) {
            t += length;
        }
    } else if (t > length) {
        t = length;
    }

    struct World {
        float x = 0.0F;
        float y = 0.0F;
        float rot = 0.0F;
    };
    std::vector<World> world(rig.parts.size());
    std::map<std::string, std::size_t, std::less<>> index;
    std::vector<PosedPart> out;
    out.reserve(rig.parts.size());

    for (std::size_t i = 0; i < rig.parts.size(); ++i) {
        const RigPart& part = rig.parts[i];
        index[part.id] = i;
        float rot = 0.0F;
        float pos[2] = {0.0F, 0.0F};
        const auto track = clip.tracks.find(part.id);
        if (track != clip.tracks.end()) {
            if (!track->second.rot.empty()) {
                interpolate(track->second.rot, t, pick_rot, 1, &rot);
            }
            if (!track->second.pos.empty()) {
                interpolate(track->second.pos, t, pick_pos, 2, pos);
            }
        }
        const float lx = (side ? part.offset_side_x : part.offset_x) + pos[0];
        const float ly = (side ? part.offset_side_y : part.offset_y) + pos[1];
        World w;
        const auto parent = part.parent.empty() ? index.end() : index.find(part.parent);
        if (parent == index.end()) {
            w = {lx, ly, rot};
        } else {
            const World& p = world[parent->second];
            const double r = static_cast<double>(p.rot) * kPi / 180.0;
            const auto c = static_cast<float>(std::cos(r));
            const auto s = static_cast<float>(std::sin(r));
            w = {p.x + c * lx - s * ly, p.y + s * lx + c * ly, p.rot + rot};
        }
        world[i] = w;
        PosedPart posed;
        posed.part_index = i;
        posed.x = mirror ? -w.x : w.x;
        posed.y = w.y;
        posed.rotation_deg = mirror ? -w.rot : w.rot;
        posed.z = part.z;
        out.push_back(posed);
    }
    return out;
}

}  // namespace aether
