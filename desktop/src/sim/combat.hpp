#pragma once

// Combat data structures. Spec: docs/spec/05-combat-v1.md. Reference: tools/reference/combat.py.

#include <array>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <vector>

#include "core/rules.hpp"
#include "core/worldtime.hpp"
#include "sim/story.hpp"

namespace aether {

struct SkillDef {
    int startup = 6;
    int active = 4;
    int recovery = 10;
    int cooldown = 24;
    std::int64_t power_pct = 100;
    int radius_x100 = 160;
    int angle_deg = 110;
    bool magical = false;          // hits with matk instead of atk (spec 05, "Damage kind")
    std::string element = "none";  // the element of its hits; none: the element of the weapon (spec 05, "Elements")
};

// The dodge roll (spec 05, "Dodge roll"): from a skill of type "movement"; `enabled` is false when the protagonist has
// none.
struct DodgeDef {
    bool enabled = false;
    int ticks = 12;
    int speed_mult_x100 = 260;
    int iframes = 14;
    int cooldown = 40;
};

// The power strike (spec 05, "Mana"): the second skill with a hitbox; `enabled` is false when the protagonist has none.
struct StrikeDef {
    bool enabled = false;
    SkillDef skill;
    std::int64_t mp = 10;
};

// The rules of a gift (spec 18, "Gift rules"): percentages (100 is neutral) and the ticks of the death save (0: none).
struct GiftDef {
    int mp_regen_pct = 100;
    int aggro_pct = 100;
    int heal_pct = 100;
    int dodge_cooldown_pct = 100;
    int death_save_ticks = 0;
    int companion_atk_pct = 100;  // the attack of the companion, in percent (a gift of command)
    int bond_gain = 1;            // what a kill of the companion adds to its bond (a gift of taming)
    // Taming (spec 18): a creature at this percent of its health or less, within this distance, can be tamed, and the
    // bond of the companion grows by `tame_bond`; 0 percent: the protagonist cannot tame.
    int tame_hp_pct = 0;
    int tame_range_x100 = 0;
    int tame_bond = 0;
    int pocket_keep_pm = 0;
    int friend_atk_pct = 0;  // above 0 a tamed creature stays as the tamed friend, hitting with this percent of its
                             // attack  // the pocket of Yuki: the chance in permille that an item used stays in the bag
};

struct DropDef {
    std::string item;
    std::int64_t qty_min = 1;
    std::int64_t qty_max = 1;
    std::int64_t weight_pm = 0;
    std::vector<std::string> pick;  // one of a list (spec 05, "Loot"): the item or one of these, drawn when it drops
};

struct BehaviorDef {
    std::string id;  // the behavior document, e.g. base:behavior/guardian (presentation: the guardian bar)
    int aggro_x100 = 600;
    int leash_x100 = 900;
    int attack_range_x100 = 120;
    int hit_range_x100 = 150;
    int windup_ticks = 18;
    int recovery_ticks = 30;
};

struct EnemyDef {
    std::string id;
    std::string art;
    std::int64_t level = 1;
    std::int64_t hp = 1;
    std::int64_t atk = 0;
    std::int64_t def = 0;
    std::int64_t xp = 0;
    int radius_x100 = 35;
    int speed_x100 = 250;
    std::string element = "none";   // spec 05, "Elements"
    std::int64_t stagger_pct = 40;  // the share of the health that fills the stagger bar; 0: never (spec 05, "Stagger")
    std::string sound;              // the family of voices of the creature (spec 14)
    std::map<std::string, std::int64_t> weaknesses_pm;  // element -> multiplier in permille
    std::vector<DropDef> drops;
    BehaviorDef behavior;
    std::map<std::string, int> season_bonus;  // more of every plain drop in a season (spec 05, "Loot")
};

struct EnemySpawn {
    EnemyDef def;
    float x = 0.0F;
    float y = 0.0F;
};

struct PlayerSetup {
    Primary base;
    Primary growth_pm;
    std::int64_t weapon_atk = 0;
    std::int64_t weapon_matk = 0;
};

// What using an item does (spec 06): a list of effects.
struct ItemEffect {
    std::string effect;  // "heal", "restore_mp", "fortify"
    std::int64_t amount = 0;
    int ticks = 0;  // how long it lasts (fortify, spec 06)
};

struct ItemDef {
    std::string kind;  // weapon, armor, food, material, ...
    std::int64_t price = 0;
    int stack_max = 0;  // 0: the default of the kind (spec 06)
    std::vector<ItemEffect> effects;
    bool is_weapon = false;
    std::int64_t weapon_atk = 0;
    std::int64_t weapon_matk = 0;
    std::string weapon_element = "none";  // spec 05, "Elements"
    bool is_armor = false;
    std::int64_t armor_def = 0;
    std::int64_t armor_mdef = 0;
    bool is_accessory = false;  // an accessory (spec 06, "Equipment"): flat bonuses while worn
    std::int64_t acc_atk = 0;
    std::int64_t acc_matk = 0;
    std::int64_t acc_def = 0;
    std::int64_t acc_mdef = 0;
    std::int64_t acc_max_hp = 0;
    std::int64_t acc_crit_pm = 0;
    std::int64_t acc_drain_pm = 0;  // share of the damage of every hit given back to the player
    bool has_affix = false;  // an affix (spec 06, "Affixes"): flat bonuses of a weapon or an armor while it is worn
    std::int64_t aff_atk = 0;
    std::int64_t aff_matk = 0;
    std::int64_t aff_def = 0;
    std::int64_t aff_mdef = 0;
    std::int64_t aff_max_hp = 0;
    std::int64_t aff_crit_pm = 0;
    std::int64_t aff_drain_pm = 0;
    bool has_affix_roll =
        false;  // rolled when found on a creature (spec 06, "Rolled affixes"): a percent in [min, max]
    std::int64_t roll_min_pct = 100;
    std::int64_t roll_max_pct = 100;
    bool is_rune = false;  // a rune (spec 06, "Runes"): engraved on the worn weapon at its station
    std::string rune_element = "none";
    std::int64_t rune_atk = 0;
    std::int64_t rune_matk = 0;
    std::string rune_station;      // the art of the prop it is engraved next to; empty: anywhere
    bool is_temper = false;        // tempers the affix of a worn piece at its station (spec 06, "Tempering")
    std::string temper_station;    // the art of the prop it is used next to; empty: anywhere
    bool is_reforge = false;       // changes the worn piece of a family at its station (spec 06, "Choosing an affix")
    std::string reforge_station;   // the art of the prop it is used next to; empty: anywhere
    std::string affix_family;      // the family of an affixed piece (spec 06, "Choosing an affix"); empty: none
    bool is_furniture = false;     // a piece of furniture (spec 06, "Furniture"): placed on a spot of the home
    std::string furniture_art;     // the prop it is drawn as (presentation)
    std::int64_t fur_atk_pct = 0;  // what it adds while placed, like a title (spec 11, "Titles with effects")
    std::int64_t fur_gather_bonus = 0;
    std::int64_t fur_craft_bonus = 0;
    std::int64_t fur_parry_bonus = 0;
    std::int64_t fur_xp_pct = 0;
    std::int64_t fur_fine_pm = 0;
};

// What a shop sells: prices in permille of the base price (spec 06).
struct ShopDef {
    int price_pm = 1000;
    std::vector<std::string> stock;
    int renown_step_pm = 0;   // what every quest finished in the region takes off the prices (spec 07, "Renown")
    int renown_max_pm = 0;    // and the most the renown takes off
    int market_swing_pm = 0;  // how far the prices swing with the day, either way (spec 06, "Market days")
    std::vector<std::pair<std::string, int>> renown_stock;  // item, renown: sold only to somebody that well known
    int glut_step_pm = 0;      // what every one of an item sold the same day takes off its price (spec 06, "Glut")
    int glut_floor_pm = 1000;  // and the least it pays, in permille
};

// A prop that can be gathered from (spec 06, "Gathering").
struct GatherDrop {
    std::string item;
    std::int64_t qty_min = 1;
    std::int64_t qty_max = 1;
    std::int64_t weight_pm = 0;
};

struct GatherNode {
    std::string sound;  // plant, wood, stone or water: the sound of gathering
    int cooldown_ticks = 0;
    int reach_x100 = 150;
    std::vector<GatherDrop> drops;
    std::map<std::string, int>
        season_bonus;  // more of every drop found in a season (spec 06, "Seasons of the gathering")
};

// Farming (spec 06, "Farming"): what a seed grows into, how much and in how many ticks; the plot prop and its reach.
struct FarmCrop {
    std::string seed;
    std::string crop;
    std::int64_t qty_min = 1;
    std::int64_t qty_max = 1;
    std::int64_t grow_ticks = 1;
};

struct FarmingDef {
    std::string plot;  // the art of the plot prop
    int reach_x100 = 150;
    std::vector<FarmCrop> crops;  // in the order of the data: a bare plot takes the first seed the bag holds
    int rain_grow_cut_pm = 0;     // how much full rain shortens the growing of a seed sown in it
    std::map<std::string, int> season_grow_pm;  // the growing of a seed sown in each season, in permille (spec 06)
};

// A companion that follows the player and fights (spec 10).
struct CompanionDef {
    std::string id;
    std::string name;  // an $i18n: key
    std::string art;   // the creature art it is drawn with
    int scale_pct = 100;
    std::int64_t atk_base = 0;
    std::int64_t atk_per_level = 0;
    int range_x100 = 300;
    int cooldown_ticks = 60;
    int speed_x100 = 320;
    int follow_x100 = 220;
    int care_bond = 0;           // care (spec 10): from this bond on it heals the player
    int care_ticks = 0;          // every so many ticks; 0: never
    int care_pct = 0;            // by this share of the maximum health
    int duo_bond = 0;            // the duo strike (spec 10): from this bond on it joins a power strike
    int duo_pct = 0;             // with this power; 0: never
    int duo_range_x100 = 0;      // on a creature this near to it
    int duo_cooldown_ticks = 0;  // and then it waits so long
    // Moments of the bond (spec 10): at this bond the companion shows a line, once a game ($i18n: keys). Presentation.
    std::vector<std::pair<int, std::string>> moments;
};

// A crafting recipe (spec 06, "Crafting").
struct RecipeDef {
    std::string id;
    std::string output;
    std::int64_t output_qty = 1;
    std::vector<std::pair<std::string, std::int64_t>> inputs;
    std::string station;        // the art of the prop it must be made next to (spec 06, "Stations"); empty: anywhere
    std::int64_t fine_pm = 0;   // the chance in permille that it comes out fine (spec 06, "Quality"); 0: never
    std::string fine_item;      // what a fine one gives instead of the output; empty: one more of the output
    std::string requires_flag;  // the story flag that teaches it (spec 06, "Recipe book"); empty: always known
};

// A title (spec 11): earned when its condition holds. kind: kills, kills_of, level, species or quests.
struct TitleDef {
    std::string id;
    std::string name;
    std::string kind;
    std::int64_t count = 1;
    std::string enemy;              // kills_of only
    std::int64_t atk_pct = 0;       // percent added to the attack of the player's hits while the title is earned
    std::int64_t gather_bonus = 0;  // one more of every drop gathered, for each
    std::int64_t craft_bonus = 0;   // more of the output of every recipe
    std::int64_t parry_bonus = 0;   // ticks added to the parry window
    std::int64_t xp_pct = 0;        // percent more experience from a kill
    std::int64_t fine_pm = 0;       // permille added to the chance of a fine piece (spec 06, "Quality")
};

// A talent (spec 11, "Talents"): every rank multiplies a kind of stat. stat: attack, health, mana, defense, magic,
// critical or speed; or an ability (spec 11, "Abilities"): riposte, kill_heal, kill_mana or whirl, whose power is
// `pct_per_rank` times the rank.
struct TalentDef {
    std::string id;
    std::string name;
    std::string stat;
    std::int64_t pct_per_rank = 0;
    int max_rank = 1;
    std::string
        requires_talent;  // the talent that must have `requires_rank` first (the branches of the tree); empty: none
    int requires_rank = 0;
    // An active ability (spec 11, "Active abilities"; stat burst or mend): used on command, for mana, then it waits.
    bool has_active = false;
    std::int64_t active_mp = 0;
    int active_cooldown = 0;
    int active_radius_x100 = 0;  // burst: how far it reaches
};

// Gideon's Dungeon (spec 18): a trap of the defense, armed by a story flag.
struct DefenseTrap {
    std::string kind;  // "spikes" or "tar"
    float x = 0.0F;
    float y = 0.0F;
    int radius_x100 = 50;
    std::string flag;
};

// Gideon's Dungeon (spec 18): the core, the gate and the waves of the defense (positions from the centre of the world
// in a streamed world, as they are in a scenario), its traps and its reward.
struct DefenseDef {
    float core_x = 0.0F;
    float core_y = 0.0F;
    float gate_x = 0.0F;
    float gate_y = 0.0F;
    int core_radius_x100 = 120;
    int wave_ticks = 3600;
    std::vector<std::vector<std::string>> waves;
    std::map<std::string, EnemyDef> enemies;
    std::vector<DefenseTrap> traps;
    int spikes_pct = 20;
    int tar_ticks = 180;
    std::int64_t reward_gold = 0;
    std::vector<std::pair<std::string, std::int64_t>> reward_items;
    std::string reward_counter;
};

// The rules of the game (spec 04, "The rules of the game"): percents the player sets for each game, saved with it; 100
// is the game as it is made. The creatures take theirs when they come into the world; the player's apply to the derived
// stats.
struct Rules {
    int player_hp_pct = 100;
    int player_mp_pct = 100;
    int player_atk_pct = 100;
    int player_def_pct = 100;
    int player_speed_pct = 100;
    int enemy_hp_pct = 100;
    int enemy_atk_pct = 100;
    int enemy_def_pct = 100;
    int enemy_speed_pct = 100;
    int enemy_sight_pct = 100;
    int xp_pct = 100;
    int drop_pct = 100;
    int buy_price_pct = 100;
    int sell_price_pct = 100;
    int companion_atk_pct = 100;
    bool operator==(const Rules&) const = default;
};
inline constexpr int kRuleMin = 10;
inline constexpr int kRuleMax = 1000;
inline constexpr std::size_t kRuleCount = 15;
// The names of the rules in the save, in the order of the settings, and their fields.
inline constexpr std::array<const char*, kRuleCount> kRuleKeys = {
    "player_hp_pct", "player_mp_pct", "player_atk_pct", "player_def_pct",  "player_speed_pct",
    "enemy_hp_pct",  "enemy_atk_pct", "enemy_def_pct",  "enemy_speed_pct", "enemy_sight_pct",
    "xp_pct",        "drop_pct",      "buy_price_pct",  "sell_price_pct",  "companion_atk_pct"};
inline constexpr std::array<int Rules::*, kRuleCount> kRuleFields = {
    &Rules::player_hp_pct,    &Rules::player_mp_pct,   &Rules::player_atk_pct,   &Rules::player_def_pct,
    &Rules::player_speed_pct, &Rules::enemy_hp_pct,    &Rules::enemy_atk_pct,    &Rules::enemy_def_pct,
    &Rules::enemy_speed_pct,  &Rules::enemy_sight_pct, &Rules::xp_pct,           &Rules::drop_pct,
    &Rules::buy_price_pct,    &Rules::sell_price_pct,  &Rules::companion_atk_pct};

// The values the settings offer for a rule (spec 16, "Settings"), and the next one from `now` up (direction > 0) or
// down; the ends stay.
inline constexpr std::array<int, 11> kRuleSteps = {10, 25, 50, 75, 100, 125, 150, 200, 300, 500, 1000};
inline int next_rule_step(int now, int direction) {
    if (direction > 0) {
        for (const int value : kRuleSteps) {
            if (value > now) {
                return value;
            }
        }
        return kRuleSteps.back();
    }
    for (auto it = kRuleSteps.rbegin(); it != kRuleSteps.rend(); ++it) {
        if (*it < now) {
            return *it;
        }
    }
    return kRuleSteps.front();
}

// The rules with every value kept within kRuleMin..kRuleMax.
inline Rules clamped_rules(Rules r) {
    for (int Rules::* field : kRuleFields) {
        r.*field = r.*field < kRuleMin ? kRuleMin : (r.*field > kRuleMax ? kRuleMax : r.*field);
    }
    return r;
}

struct CombatSetup {
    bool enabled = false;
    Rules rules;                     // the rules of the game at its start (spec 04); the save keeps those of the game
    std::vector<TalentDef> talents;  // the talents that can be learned, in the order of the data
    int talent_points_per_level = 1;
    int echo_pct = 0;  // percent added to the maximum health, from the profile of past games (spec 11, "Echoes")
    PlayerSetup player;
    SkillDef skill;
    DodgeDef dodge;
    StrikeDef strike;
    GiftDef gift;
    // The rain of a world without a clock (the conformance scenarios; spec 08, "Rain hides you"): a streamed world
    // reads both from its time instead.
    int rain_pm = 0;
    int rain_aggro_cut_pm = 0;
    int rain_slow_pm = 0;  // how much full rain slows the creatures (spec 08, "Rain slows")
    int light_pm = 1000;   // the same for the night (spec 08, "The night hides you")
    int night_aggro_cut_pm = 0;
    int wind_pm = 0;  // the wind (spec 08, "Wind"): how hard it blows, and how much a full wind speeds the player
    int wind_haste_pm = 0;
    int fog_pm = 0;  // the fog (spec 08, "Fog"): how thick it is, and how much a full fog shortens the aggro distance
    int fog_aggro_cut_pm = 0;
    std::vector<std::string> season_stock;  // the goods of the season of the setup (spec 06, "Goods of the season")
    WeatherGoods weather_goods;             // what the rain of the setup makes dearer (spec 06, "Weather and prices")
    int season_slow_pm =
        0;  // what the season of the setup does to the creatures (spec 08, "Seasons and the creatures")
    int season_aggro_cut_pm = 0;
    int lightning_ticks = 0;  // the lightning of a storm (spec 08, "Lightning"): how often, how hard, how far
    int lightning_pct = 0;
    int lightning_range_x100 = 0;
    std::vector<EnemySpawn> spawns;
    std::vector<std::int64_t> xp_table;  // table[level - 1] = XP to go from `level` to `level + 1`
    std::uint64_t seed = 0;
    int start_level = 1;
    StorySetup story;
    std::map<std::string, std::int64_t> start_inventory;  // items owned in a new game
    std::map<std::string, ItemDef> items;                 // every item, by item ID
    std::string start_weapon;                             // the weapon worn in a new game (an item ID, or empty)
    std::string start_armor;                              // the armor worn in a new game (an item ID, or empty)
    std::optional<ShopDef> shop;  // the shop of fixed maps and scenarios (streamed worlds use their regions)
    std::map<std::string, ShopDef> far_shops;  // the same for the shops of other regions (spec 06, "Goods from afar")
    std::optional<FarmingDef> farming;         // the plots and the crops (spec 06, "Farming"); none: no farming
    std::string chest_art;                     // the chest prop (spec 06, "Chests"); empty: no chests
    int chest_reach_x100 = 200;
    std::string home_spot;  // the furniture spot prop (spec 06, "Furniture"); empty: no furniture
    int home_reach_x100 = 200;
    // The rooms of the home (spec 06, "Rooms"): the props of `spot` are places once the story flag `flag` is set.
    struct HomeRoom {
        std::string id;
        std::string flag;
        std::string spot;
    };
    std::vector<HomeRoom> home_rooms;
    std::map<std::string, EnemyDef> stream_enemies;  // the enemies of the fauna of a streamed world, by ID
    std::map<std::string, GatherNode> gather_nodes;  // the props that can be gathered from, by art ID
    std::vector<RecipeDef> recipes;                  // crafting recipes, in the order of the data
    std::optional<CompanionDef> companion;           // the companion of the protagonist (spec 10)
    std::map<std::string, CompanionDef>
        companions;                     // every companion of the pack, by ID: those that may join the party
    std::optional<DefenseDef> defense;  // Gideon's Dungeon (spec 18)
    std::vector<TitleDef> titles;       // the titles that can be earned (spec 11), in order of rank
    std::vector<TitleDef> tags;  // the tags (spec 11, "Tags"): earned like titles, one worn at a time; in data order
    int day_ticks = 0;   // the length of a day of a world without a clock, for the market (spec 06); 0: always day 1
    std::string region;  // the region of a world without regions: the renown is counted by region (spec 07, "Renown")
    std::string season;  // the season of a world without a clock (spec 06, "Seasons on the plots"); empty: none
};

enum class AttackPhase { None, Startup, Active, Recovery };
enum class EnemyState { Idle, Chase, Attack, Return, Dead };

const char* to_string(EnemyState state);

// Primary stats at `level` (spec 05): base + growth_pm * (level - 1) / 1000.
Primary primary_at_level(const PlayerSetup& setup, std::int64_t level);

}  // namespace aether
