#include "audio/director.hpp"

#include <algorithm>
#include <cmath>

namespace aether {

namespace {
constexpr double kStrideTiles = 0.85;
constexpr int kHeartbeatFrames = 70;
constexpr std::int64_t kThunderPeriod = 1200;
constexpr std::int64_t kThunderAt = 600;
constexpr int kMinAudiblePm = 60;
constexpr double kFalloffPmPerTile = 70.0;
}  // namespace

std::vector<SoundEvent> SoundDirector::update(const SoundSnapshot& s) {
    std::vector<SoundEvent> out;
    const auto emit = [&out](const std::string& event, int volume = 1000) { out.push_back({event, volume}); };
    const PlayerSound& p = s.player;

    // What the creatures did this frame.
    for (const SoundCue& cue : s.cues) {
        const double dist = std::hypot(cue.x - p.x, cue.y - p.y);
        const int volume = std::clamp(1000 - static_cast<int>(std::floor(dist * kFalloffPmPerTile + 0.5)), 0, 1000);
        if (cue.kind == "hurt") {
            emit("player.hurt");
        } else if (cue.kind == "parry") {
            emit("player.parry");
        } else if (cue.kind == "gather") {
            emit("gather." + cue.family);
        } else if (cue.kind == "craft") {
            emit("craft");
        } else if (volume >= kMinAudiblePm) {
            emit("enemy." + cue.family + "." + cue.kind, volume);
        }
        if (cue.kind == "hit") {
            if (cue.crit) {
                emit("crit");
            }
            if (cue.weak) {
                emit("weak");
            }
        }
    }

    if (m_prev_) {
        const SoundSnapshot& prev = *m_prev_;
        const PlayerSound& pp = prev.player;
        // The player.
        if (p.phase != 0 && pp.phase == 0) {
            emit(p.strike ? "power" : "swing");
        }
        if (p.dodge && !pp.dodge) {
            emit("dodge");
        }
        if (p.level > pp.level) {
            emit("level_up");
        }
        if (p.hp <= 0 && pp.hp > 0) {
            emit("player.death");
        }
        if (p.save_cd > pp.save_cd) {
            emit("death_save");
        }
        if (p.moving) {
            m_walked_ += std::hypot(p.x - pp.x, p.y - pp.y);
            if (m_walked_ >= kStrideTiles) {
                m_walked_ -= kStrideTiles;
                emit("step." + p.surface, 700);
            }
        } else {
            m_walked_ = 0.0;
        }
        if (p.hp > 0 && p.hp * 4 < p.max_hp) {
            ++m_since_heartbeat_;
            if (m_since_heartbeat_ >= kHeartbeatFrames) {
                m_since_heartbeat_ = 0;
                emit("heartbeat", 800);
            }
        } else {
            m_since_heartbeat_ = kHeartbeatFrames;
        }
        // The bag.
        const std::int64_t d_items = s.items - prev.items;
        const std::int64_t d_gold = s.gold - prev.gold;
        const std::int64_t d_hp = p.hp - pp.hp;
        const bool shop = s.panels.shop;
        if (d_gold > 0 && d_items < 0 && shop) {
            emit("shop.sell");
        } else if (d_gold < 0 && d_items > 0) {
            emit("shop.buy");
        } else if (d_gold > 0) {
            emit("coin");
        } else if (d_items > 0) {
            emit("pickup");
        } else if (d_items < 0 && d_hp > 0) {
            emit("use.heal");
        } else if (d_items < 0 && s.mp > prev.mp) {
            emit("use.mana");
        } else if (d_items < 0 && !shop) {
            emit("use.other");
        }
        if (s.weapon != prev.weapon) {
            emit("equip.weapon");
        }
        if (s.armor != prev.armor) {
            emit("equip.armor");
        }
        // Panels, the cursor, the dialogue.
        const auto panel = [&](const char* name, bool now, bool before) {
            if (now != before) {
                emit(std::string("ui.") + (now ? "open." : "close.") + name);
            }
        };
        panel("bag", s.panels.bag, prev.panels.bag);
        panel("map", s.panels.map, prev.panels.map);
        panel("journal", s.panels.journal, prev.panels.journal);
        panel("shop", s.panels.shop, prev.panels.shop);
        panel("board", s.panels.board, prev.panels.board);
        panel("travel", s.panels.travel, prev.panels.travel);
        if (s.dialogue != prev.dialogue) {
            emit(s.dialogue ? "dialogue.open" : "dialogue.close");
        } else if (s.dialogue && s.line != prev.line) {
            emit("dialogue.next");
        }
        if (s.cursor != prev.cursor && (s.dialogue || s.panels.any())) {
            emit("ui.move");
        }
        // The story and the world.
        if (s.quests_started > prev.quests_started) {
            emit("quest.accept");
        }
        if (s.quests_done > prev.quests_done) {
            emit("quest.complete");
        }
        if (s.stones > prev.stones) {
            emit("stone.wake");
        }
        if (s.region != prev.region) {
            emit("region.enter");
        }
        if (prev.rain_pm == 0 && s.rain_pm > 0) {
            emit("rain.start");
        } else if (s.rain_pm == 0 && prev.rain_pm > 0) {
            emit("rain.stop");
        }
        if (s.rain_pm >= 700 && s.frame % kThunderPeriod == kThunderAt) {
            emit("thunder");
        }
        if (prev.tod_pm < 250 && s.tod_pm >= 250) {
            emit("dawn");
        }
        if (prev.tod_pm < 750 && s.tod_pm >= 750) {
            emit("nightfall");
        }
    }
    m_prev_ = s;
    return out;
}

std::map<std::string, int> ambience_gains(const std::string& region, int tod_pm, int rain_pm,
                                          const AmbienceRules& rules) {
    std::map<std::string, int> gains;
    const bool day = tod_pm >= 250 && tod_pm <= 750;
    const auto found = rules.regions.find(region);
    if (found != rules.regions.end()) {
        for (const AmbienceEntry& entry : found->second) {
            if ((entry.when == "day" && !day) || (entry.when == "night" && day)) {
                continue;
            }
            gains[entry.sound] = std::max(gains[entry.sound], entry.gain_pm);
        }
    }
    if (rain_pm > 0) {
        gains[rules.rain_light] = std::min(1000, rain_pm);
        const int heavy = std::max(0, rain_pm - 500) * 2;
        if (heavy > 0) {
            gains[rules.rain_heavy] = std::min(1000, heavy);
        }
        for (auto& [sound, gain] : gains) {
            if (std::find(rules.silences.begin(), rules.silences.end(), sound) != rules.silences.end()) {
                gain = 0;
            }
        }
    }
    for (auto it = gains.begin(); it != gains.end();) {
        it = it->second > 0 ? std::next(it) : gains.erase(it);
    }
    return gains;
}

}  // namespace aether
