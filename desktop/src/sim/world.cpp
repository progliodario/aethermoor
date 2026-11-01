#include "sim/world.hpp"

#include <algorithm>
#include <cmath>
#include <utility>

namespace aether {

namespace {

constexpr int kPlayerHitIframes = 45;
constexpr int kRespawnIframes = 90;
constexpr float kAttackMoveMult = 0.5F;
constexpr std::int64_t kMaxLevel = 99;
constexpr float kReturnArrival = 0.1F;
constexpr int kHitFlashTicks = 6;
constexpr double kPi = 3.14159265358979323846;

CollisionWorld build_collision(const TileMap& map, const Tileset& tileset) {
    std::vector<bool> solid(map.ground.size(), false);
    for (std::size_t i = 0; i < map.ground.size(); ++i) {
        const auto tile = tileset.tiles.find(map.ground[i]);
        solid[i] = tile != tileset.tiles.end() && tile->second.solid;
    }
    std::vector<Circle> props;
    props.reserve(map.props.size());
    for (const Prop& prop : map.props) {
        props.push_back({prop.x, prop.y, prop.radius});
    }
    return CollisionWorld(map.width, map.height, std::move(solid), std::move(props));
}

float axis_origin(float player, float view, float map_size) {
    if (map_size <= view) {
        return (map_size - view) / 2.0F;
    }
    const float origin = player - view / 2.0F;
    if (origin < 0.0F) {
        return 0.0F;
    }
    const float max_origin = map_size - view;
    return origin > max_origin ? max_origin : origin;
}

float distance(float ax, float ay, float bx, float by) {
    const float dx = bx - ax;
    const float dy = by - ay;
    return std::sqrt(dx * dx + dy * dy);
}

}  // namespace

WorldSim::WorldSim(TileMap map, Tileset tileset, float speed_tiles_per_s, CombatSetup combat)
    : m_map_(std::move(map)),
      m_tileset_(std::move(tileset)),
      m_collision_(build_collision(m_map_, m_tileset_)),
      m_speed_(speed_tiles_per_s),
      m_setup_(std::move(combat)),
      m_combat_rng_(derive_stream(m_setup_.seed, "combat")),
      m_loot_rng_(derive_stream(m_setup_.seed, "loot")) {
    m_player_.position = {m_map_.spawn_x, m_map_.spawn_y};
    m_collision_.resolve(m_player_.position.x, m_player_.position.y);
    m_spawn_ = m_player_.position;
    if (m_setup_.enabled) {
        m_player_.level = m_setup_.start_level;
        recompute_derived();
        m_player_.hp = m_derived_.max_hp;
        for (const EnemySpawn& spawn : m_setup_.spawns) {
            Enemy enemy;
            enemy.def = spawn.def;
            enemy.position = {spawn.x, spawn.y};
            enemy.home = enemy.position;
            enemy.hp = spawn.def.hp;
            m_enemies_.push_back(std::move(enemy));
        }
        m_hit_set_.assign(m_enemies_.size(), false);
    }
}

void WorldSim::recompute_derived() {
    Equipment equipment;
    equipment.weapon_atk = m_setup_.player.weapon_atk;
    equipment.weapon_matk = m_setup_.player.weapon_matk;
    m_derived_ = derived_stats(m_player_.level, primary_at_level(m_setup_.player, m_player_.level), equipment);
}

std::vector<DamageEvent> WorldSim::take_events() { return std::exchange(m_events_, {}); }

void WorldSim::tick(float raw_x, float raw_y, bool attack) {
    Player& p = m_player_;
    const bool combat = m_setup_.enabled;
    if (p.iframes > 0) {
        --p.iframes;
    }
    if (p.cooldown > 0) {
        --p.cooldown;
    }

    const Vec2 direction = normalize_input(raw_x, raw_y);
    const bool moving = direction.x != 0.0F || direction.y != 0.0F;
    if (combat && moving && (p.phase == AttackPhase::None || p.phase == AttackPhase::Startup)) {
        const float length = std::sqrt(direction.x * direction.x + direction.y * direction.y);
        p.facing = {direction.x / length, direction.y / length};
    }
    float speed = combat ? static_cast<float>(m_derived_.move_speed_x100) / 100.0F : m_speed_;
    if (combat && p.phase != AttackPhase::None) {
        speed *= kAttackMoveMult;
    }
    m_collision_.step(p.position, direction, speed);

    if (direction.x != 0.0F) {
        p.facing_left = direction.x < 0.0F;
    }
    if (moving != p.moving) {
        p.moving = moving;
        p.clip_tick = 0;
    } else {
        ++p.clip_tick;
    }

    if (!combat) {
        return;
    }
    if (attack && p.phase == AttackPhase::None && p.cooldown == 0) {
        p.phase = AttackPhase::Startup;
        p.phase_tick = 0;
        p.cooldown = m_setup_.skill.cooldown;
        std::fill(m_hit_set_.begin(), m_hit_set_.end(), false);
    }
    advance_attack();
    for (Enemy& enemy : m_enemies_) {
        update_enemy(enemy);
        if (enemy.hit_flash > 0) {
            --enemy.hit_flash;
        }
    }
}

void WorldSim::advance_attack() {
    Player& p = m_player_;
    const SkillDef& s = m_setup_.skill;
    switch (p.phase) {
        case AttackPhase::Startup:
            if (++p.phase_tick >= s.startup) {
                p.phase = AttackPhase::Active;
                p.phase_tick = 0;
            }
            break;
        case AttackPhase::Active:
            do_hits();
            if (++p.phase_tick >= s.active) {
                p.phase = AttackPhase::Recovery;
                p.phase_tick = 0;
            }
            break;
        case AttackPhase::Recovery:
            if (++p.phase_tick >= s.recovery) {
                p.phase = AttackPhase::None;
            }
            break;
        case AttackPhase::None:
            break;
    }
}

void WorldSim::do_hits() {
    Player& p = m_player_;
    const SkillDef& s = m_setup_.skill;
    const auto cos_half =
        static_cast<float>(std::cos(static_cast<double>(s.angle_deg) / 2.0 * kPi / 180.0));
    for (std::size_t index = 0; index < m_enemies_.size(); ++index) {
        Enemy& enemy = m_enemies_[index];
        if (enemy.state == EnemyState::Dead || m_hit_set_[index]) {
            continue;
        }
        const float dx = enemy.position.x - p.position.x;
        const float dy = enemy.position.y - p.position.y;
        const float dist = std::sqrt(dx * dx + dy * dy);
        if (dist > static_cast<float>(s.radius_x100) / 100.0F + enemy.radius()) {
            continue;
        }
        if (dist > 0.0F) {
            const float dot = (dx * p.facing.x + dy * p.facing.y) / dist;
            if (dot < cos_half) {
                continue;
            }
        }
        m_hit_set_[index] = true;
        const std::int64_t variance = 950 + static_cast<std::int64_t>(m_combat_rng_.next_bounded(101));
        const bool crit = static_cast<std::int64_t>(m_combat_rng_.next_bounded(1000)) < m_derived_.crit_chance_pm;
        DamageInput in;
        in.atk = m_derived_.atk;
        in.power_pct = s.power_pct;
        in.def_target = enemy.def.def;
        in.lvl_attacker = p.level;
        in.lvl_target = enemy.def.level;
        in.variance_pm = variance;
        in.crit = crit;
        in.crit_mult_pm = m_derived_.crit_mult_pm;
        const std::int64_t amount = damage(in);
        enemy.hp -= amount;
        enemy.hit_flash = kHitFlashTicks;
        m_events_.push_back({enemy.position, amount, crit, false});
        if (enemy.hp <= 0) {
            enemy.hp = 0;
            enemy.state = EnemyState::Dead;
            on_kill(enemy);
        }
    }
}

void WorldSim::on_kill(Enemy& enemy) {
    Player& p = m_player_;
    ++p.kills;
    for (const DropDef& drop : enemy.def.drops) {
        if (static_cast<std::int64_t>(m_loot_rng_.next_bounded(1000)) < drop.weight_pm) {
            std::int64_t quantity = drop.qty_min;
            if (drop.qty_max > drop.qty_min) {
                quantity += static_cast<std::int64_t>(
                    m_loot_rng_.next_bounded(static_cast<std::uint32_t>(drop.qty_max - drop.qty_min + 1)));
            }
            m_inventory_[drop.item] += quantity;
        }
    }
    p.xp += xp_gain(enemy.def.xp, enemy.def.level, p.level);
    while (p.level < kMaxLevel && p.level - 1 < static_cast<std::int64_t>(m_setup_.xp_table.size()) &&
           p.xp >= m_setup_.xp_table[static_cast<std::size_t>(p.level - 1)]) {
        p.xp -= m_setup_.xp_table[static_cast<std::size_t>(p.level - 1)];
        ++p.level;
        recompute_derived();
        p.hp = m_derived_.max_hp;
    }
}

void WorldSim::update_enemy(Enemy& enemy) {
    if (enemy.state == EnemyState::Dead) {
        return;
    }
    const BehaviorDef& b = enemy.def.behavior;
    const Player& p = m_player_;
    const float dist = distance(enemy.position.x, enemy.position.y, p.position.x, p.position.y);
    switch (enemy.state) {
        case EnemyState::Idle:
            if (dist <= static_cast<float>(b.aggro_x100) / 100.0F) {
                enemy.state = EnemyState::Chase;
                enemy.state_tick = 0;
            }
            break;
        case EnemyState::Chase:
            if (dist > static_cast<float>(b.leash_x100) / 100.0F) {
                enemy.state = EnemyState::Return;
            } else if (dist <= static_cast<float>(b.attack_range_x100) / 100.0F) {
                enemy.state = EnemyState::Attack;
                enemy.state_tick = 0;
            } else {
                move_enemy(enemy, p.position.x, p.position.y);
            }
            break;
        case EnemyState::Attack:
            ++enemy.state_tick;
            if (enemy.state_tick == b.windup_ticks && dist <= static_cast<float>(b.hit_range_x100) / 100.0F &&
                p.iframes == 0) {
                hurt_player(enemy);
            }
            if (enemy.state_tick >= b.windup_ticks + b.recovery_ticks) {
                enemy.state = EnemyState::Chase;
                enemy.state_tick = 0;
            }
            break;
        case EnemyState::Return:
            if (distance(enemy.position.x, enemy.position.y, enemy.home.x, enemy.home.y) <= kReturnArrival) {
                enemy.state = EnemyState::Idle;
                enemy.hp = enemy.def.hp;
            } else {
                move_enemy(enemy, enemy.home.x, enemy.home.y);
            }
            break;
        case EnemyState::Dead:
            break;
    }
}

void WorldSim::move_enemy(Enemy& enemy, float target_x, float target_y) {
    const float dx = target_x - enemy.position.x;
    const float dy = target_y - enemy.position.y;
    const float dist = std::sqrt(dx * dx + dy * dy);
    const float step = (static_cast<float>(enemy.def.speed_x100) / 100.0F) * kTickDt;
    if (dist > 0.0F) {
        if (dist <= step) {
            enemy.position = {target_x, target_y};
        } else {
            enemy.position.x += dx / dist * step;
            enemy.position.y += dy / dist * step;
        }
    }
    m_collision_.resolve(enemy.position.x, enemy.position.y, enemy.radius());
}

void WorldSim::hurt_player(const Enemy& enemy) {
    Player& p = m_player_;
    const std::int64_t variance = 950 + static_cast<std::int64_t>(m_combat_rng_.next_bounded(101));
    DamageInput in;
    in.atk = enemy.def.atk;
    in.power_pct = 100;
    in.def_target = m_derived_.def;
    in.lvl_attacker = enemy.def.level;
    in.lvl_target = p.level;
    in.variance_pm = variance;
    const std::int64_t amount = damage(in);
    p.hp -= amount;
    p.iframes = kPlayerHitIframes;
    m_events_.push_back({p.position, amount, false, true});
    if (p.hp <= 0) {
        ++p.deaths;
        p.hp = m_derived_.max_hp;
        p.position = m_spawn_;
        p.phase = AttackPhase::None;
        p.phase_tick = 0;
        p.iframes = kRespawnIframes;
    }
}

Camera WorldSim::camera(float view_w, float view_h) const {
    return {axis_origin(m_player_.position.x, view_w, static_cast<float>(m_map_.width)),
            axis_origin(m_player_.position.y, view_h, static_cast<float>(m_map_.height))};
}

}  // namespace aether
