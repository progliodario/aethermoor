#pragma once

// Animation rigs and clips. Spec: docs/spec/13-vector-art.md. Schemas: rig, clip.

#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace aether {

struct RigPart {
    std::string id;
    std::string parent;  // empty for the root
    float offset_x = 0.0F;
    float offset_y = 0.0F;
    int z = 0;
    std::string art;
    std::string art_back;  // the recipe when the figure is seen from behind (spec 13); the same as `art` if not given
    int z_back = 0;        // the draw order when seen from behind; the same as `z` if not given
};

struct Rig {
    std::string id;
    std::vector<RigPart> parts;  // parents first
};

struct RotKey {
    float tick;
    float degrees;
};

struct PosKey {
    float tick;
    float x;
    float y;
};

struct Track {
    std::vector<RotKey> rot;
    std::vector<PosKey> pos;
};

struct Clip {
    std::string id;
    std::string rig;
    bool loop = false;
    int length_ticks = 1;
    std::map<std::string, Track, std::less<>> tracks;
};

struct PosedPart {
    std::size_t part_index = 0;  // index into Rig::parts
    float x = 0.0F;              // art units, relative to the rig origin
    float y = 0.0F;
    float rotation_deg = 0.0F;
    int z = 0;
};

std::optional<Rig> parse_rig(std::string_view json_text, std::string& error);
std::optional<Clip> parse_clip(std::string_view json_text, std::string& error);

// World placement of every part at `tick`; `mirror` negates x and rotation (facing left).
std::vector<PosedPart> evaluate_pose(const Rig& rig, const Clip& clip, float tick, bool mirror);

}  // namespace aether
