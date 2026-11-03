#pragma once

// Quests, dialogue, conditions and effects. Spec: docs/spec/07-quests-and-dialogue.md.
// Reference: tools/reference/story.py.

#include <cstdint>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace aether {

struct Condition {
    enum class Kind { Flag, Not, All, Any, QuestActive, QuestDone, QuestStage, HasItem, LevelAtLeast };
    Kind kind = Kind::Flag;
    std::string a;  // flag / quest / item
    std::string b;  // stage
    std::int64_t n = 0;  // quantity / level
    std::vector<Condition> children;
};

struct Effect {
    enum class Kind { AddXp, AddGold, AddItem, RemoveItem, SetFlag, StartQuest, OpenShop, AddGuildPoints, OpenBoard };
    Kind kind = Kind::AddXp;
    std::string a;  // item / flag / quest
    std::int64_t n = 0;  // amount / quantity
    bool value = true;
};

struct Objective {
    enum class Kind { Kill, Collect, Talk };
    Kind kind = Kind::Kill;
    std::string target;  // enemy ID / item ID / npc key
    std::int64_t count = 1;
    std::int64_t required() const { return kind == Kind::Talk ? 1 : count; }
};

struct QuestStage {
    std::string id;
    std::string journal;  // "$i18n:..." reference
    std::vector<Objective> objectives;
    std::string next;
};

struct QuestDef {
    std::string id;
    std::string name;  // "$i18n:..." reference
    std::vector<QuestStage> stages;
    std::vector<Effect> rewards;
    std::map<std::string, std::string> args;  // arguments of the name and journal texts (spec 07)
};

struct Offer;
// The quest of a board offer (spec 07, "Guild").
QuestDef quest_from_offer(const Offer& offer);

struct DialogueChoice {
    std::string text;
    bool has_when = false;
    Condition when;
    std::vector<Effect> effects;
    std::string next;
};

struct DialogueNode {
    enum class Kind { Say, Choice, SetFlag, Effects, Cond };
    Kind kind = Kind::Say;
    std::string speaker;
    std::string text;
    std::string next;
    std::vector<DialogueChoice> choices;
    std::string flag;
    bool value = true;
    std::vector<Effect> effects;
    Condition when;
    std::string then_next;
    std::string else_next;
};

struct DialogueDef {
    std::string id;
    std::string start;
    std::map<std::string, DialogueNode> nodes;
};

struct NpcDef {
    std::string key;
    std::string dialogue;  // dialogue ID
    std::string variant;   // art palette variant of the player rig
    float x = 0.0F;
    float y = 0.0F;
    std::string name;                          // settlement people: a proper noun, empty for the others
    std::map<std::string, std::string> args;   // arguments of the dialogue texts (spec 07)
};

struct StorySetup {
    std::map<std::string, QuestDef> quests;
    std::map<std::string, DialogueDef> dialogues;
    std::vector<NpcDef> npcs;
};

std::optional<QuestDef> parse_quest(std::string_view json_text, std::string& error);
std::optional<DialogueDef> parse_dialogue(std::string_view json_text, std::string& error);
// Parses the scenario "story" section used by the conformance tests (quests and dialogues keyed by ID, plus NPCs).
std::optional<StorySetup> parse_story_setup(std::string_view json_text, std::string& error);

// What the player currently sees.
struct DialogueView {
    bool active = false;
    bool is_choice = false;
    std::string speaker;                // say
    std::string text;                   // say
    std::vector<std::string> choices;   // choice: texts of the visible choices
    std::map<std::string, std::string> args;  // arguments of the texts (spec 07, "Dialogue arguments")
};

struct QuestProgress {
    std::string stage;
    std::vector<std::int64_t> progress;
    bool done = false;
};

// The part of the story that changes while playing (saves).
struct StoryState {
    std::map<std::string, bool> flags;
    std::int64_t gold = 0;
    std::int64_t guild_points = 0;
    std::map<std::string, QuestProgress> quests;
    bool dialogue_active = false;
    std::string dialogue_id;
    std::string node;
    std::map<std::string, std::string> dialogue_args;
};

// What the story needs from the world that owns it.
class StoryHost {
public:
    virtual ~StoryHost() = default;
    virtual void grant_xp(std::int64_t amount) = 0;
    virtual std::map<std::string, std::int64_t>& host_inventory() = 0;
    virtual std::int64_t level() const = 0;
    virtual float player_x() const = 0;
    virtual float player_y() const = 0;
    virtual void open_shop() = 0;
    virtual void open_board() = 0;
};

class Story {
public:
    Story(StorySetup setup, StoryHost& host);

    bool holds(const Condition& condition) const;
    void apply(const Effect& effect);

    void start_quest(const std::string& quest_id);
    void on_kill(std::string_view enemy_id);
    void on_talk(std::string_view npc_key);

    bool dialogue_active() const { return m_dialogue_active_; }
    void interact();
    void advance();
    void choose(int index);
    DialogueView dialogue_view() const;

    // The NPC `interact` would talk to now, or nullptr.
    const NpcDef* npc_in_range() const;
    // NPCs that come and go with the world (settlement people); owned by the world, listed after the static ones.
    void set_dynamic_npcs(const std::vector<NpcDef>* npcs) { m_dynamic_npcs_ = npcs; }
    const std::vector<NpcDef>& dynamic_npcs() const { return *m_dynamic_npcs_; }

    StoryState capture() const;
    // Returns false (and changes nothing) when the state names a dialogue or node that does not exist.
    bool restore(const StoryState& state);

    const StorySetup& setup() const { return m_setup_; }
    const std::map<std::string, bool>& flags() const { return m_flags_; }
    std::int64_t gold() const { return m_gold_; }
    void set_gold(std::int64_t gold) { m_gold_ = gold; }
    std::int64_t guild_points() const { return m_guild_points_; }
    // Adds the quest of a board offer to the known quests (it can then be started and saved).
    void add_generated_quest(QuestDef quest) { m_setup_.quests.emplace(quest.id, std::move(quest)); }
    // Rebuilds the quest of a generated id when a save is loaded.
    void set_quest_resolver(std::function<std::optional<QuestDef>(const std::string&)> resolver) { m_resolver_ = std::move(resolver); }
    const std::map<std::string, QuestProgress>& quests() const { return m_quests_; }

private:
    const QuestStage& current_stage(const std::string& quest_id) const;
    void refresh_all();
    void refresh(const std::string& quest_id);
    void start_dialogue(const std::string& dialogue_id);
    const DialogueNode& node() const;
    void go(const std::string& target);
    void settle();
    std::vector<const DialogueChoice*> visible_choices() const;

    StorySetup m_setup_;
    StoryHost& m_host_;
    std::map<std::string, bool> m_flags_;
    std::int64_t m_gold_ = 0;
    std::int64_t m_guild_points_ = 0;
    std::function<std::optional<QuestDef>(const std::string&)> m_resolver_;
    std::map<std::string, QuestProgress> m_quests_;
    bool m_dialogue_active_ = false;
    std::string m_dialogue_id_;
    std::string m_node_;
    std::map<std::string, std::string> m_dialogue_args_;
    const std::vector<NpcDef>* m_dynamic_npcs_ = &s_no_npcs;
    static const std::vector<NpcDef> s_no_npcs;
};

}  // namespace aether
