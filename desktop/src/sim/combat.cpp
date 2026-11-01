#include "sim/combat.hpp"

namespace aether {

const char* to_string(EnemyState state) {
    switch (state) {
        case EnemyState::Idle:
            return "idle";
        case EnemyState::Chase:
            return "chase";
        case EnemyState::Attack:
            return "attack";
        case EnemyState::Return:
            return "return";
        case EnemyState::Dead:
            return "dead";
    }
    return "idle";
}

Primary primary_at_level(const PlayerSetup& setup, std::int64_t level) {
    const auto stat = [level](std::int64_t base, std::int64_t growth_pm) { return base + growth_pm * (level - 1) / 1000; };
    return Primary{stat(setup.base.str, setup.growth_pm.str),   stat(setup.base.vit, setup.growth_pm.vit),
                   stat(setup.base.dex, setup.growth_pm.dex),   stat(setup.base.agi, setup.growth_pm.agi),
                   stat(setup.base.int_, setup.growth_pm.int_), stat(setup.base.wis, setup.growth_pm.wis),
                   stat(setup.base.luk, setup.growth_pm.luk)};
}

}  // namespace aether
