#include "sim/story.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include <nlohmann/json.hpp>

namespace aether {

namespace {

using Json = nlohmann::json;

constexpr float kInteractRange = 1.5F;
constexpr int kMaxSettleSteps = 64;

// ------------------------------------------------------------------------------------ parsing

Condition parse_condition(const Json& j) {
    if (!j.is_object() || j.size() != 1) {
        throw std::runtime_error("a condition must be an object with exactly one key");
    }
    const auto entry = j.begin();
    const std::string key = entry.key();
    const Json& value = entry.value();
    Condition c;
    if (key == "flag") {
        c.kind = Condition::Kind::Flag;
        c.a = value.get<std::string>();
    } else if (key == "not") {
        c.kind = Condition::Kind::Not;
        c.children.push_back(parse_condition(value));
    } else if (key == "all" || key == "any") {
        c.kind = key == "all" ? Condition::Kind::All : Condition::Kind::Any;
        for (const Json& child : value) {
            c.children.push_back(parse_condition(child));
        }
    } else if (key == "quest_active") {
        c.kind = Condition::Kind::QuestActive;
        c.a = value.get<std::string>();
    } else if (key == "quest_done") {
        c.kind = Condition::Kind::QuestDone;
        c.a = value.get<std::string>();
    } else if (key == "quest_stage") {
        c.kind = Condition::Kind::QuestStage;
        c.a = value.at("quest").get<std::string>();
        c.b = value.at("stage").get<std::string>();
    } else if (key == "has_item") {
        c.kind = Condition::Kind::HasItem;
        c.a = value.at("item").get<std::string>();
        c.n = value.at("qty").get<std::int64_t>();
    } else if (key == "level_at_least") {
        c.kind = Condition::Kind::LevelAtLeast;
        c.n = value.get<std::int64_t>();
    } else {
        throw std::runtime_error("unknown condition " + key);
    }
    return c;
}

Effect parse_effect(const Json& j) {
    const std::string kind = j.at("effect").get<std::string>();
    Effect e;
    if (kind == "add_xp" || kind == "add_gold") {
        e.kind = kind == "add_xp" ? Effect::Kind::AddXp : Effect::Kind::AddGold;
        e.n = j.at("amount").get<std::int64_t>();
    } else if (kind == "add_item") {
        e.kind = Effect::Kind::AddItem;
        e.a = j.at("item").get<std::string>();
        e.n = j.at("qty").get<std::int64_t>();
    } else if (kind == "set_flag") {
        e.kind = Effect::Kind::SetFlag;
        e.a = j.at("flag").get<std::string>();
        e.value = j.at("value").get<bool>();
    } else if (kind == "start_quest") {
        e.kind = Effect::Kind::StartQuest;
        e.a = j.at("quest").get<std::string>();
    } else {
        throw std::runtime_error("unknown effect " + kind);
    }
    return e;
}

std::vector<Effect> parse_effects(const Json& j, const char* key) {
    std::vector<Effect> out;
    if (j.contains(key)) {
        for (const Json& e : j.at(key)) {
            out.push_back(parse_effect(e));
        }
    }
    return out;
}

QuestDef parse_quest_json(const Json& j) {
    QuestDef quest;
    quest.id = j.value("id", "");
    quest.name = j.value("name", "");
    for (const Json& s : j.at("stages")) {
        QuestStage stage;
        stage.id = s.at("id").get<std::string>();
        stage.journal = s.value("journal", "");
        stage.next = s.at("next").get<std::string>();
        for (const Json& o : s.at("objectives")) {
            Objective objective;
            const std::string type = o.at("type").get<std::string>();
            if (type == "kill") {
                objective.kind = Objective::Kind::Kill;
                objective.target = o.at("enemy").get<std::string>();
                objective.count = o.at("count").get<std::int64_t>();
            } else if (type == "collect") {
                objective.kind = Objective::Kind::Collect;
                objective.target = o.at("item").get<std::string>();
                objective.count = o.at("count").get<std::int64_t>();
            } else if (type == "talk") {
                objective.kind = Objective::Kind::Talk;
                objective.target = o.at("npc_key").get<std::string>();
            } else {
                throw std::runtime_error("unknown objective " + type);
            }
            stage.objectives.push_back(std::move(objective));
        }
        quest.stages.push_back(std::move(stage));
    }
    quest.rewards = parse_effects(j, "rewards");
    if (quest.stages.empty()) {
        throw std::runtime_error("a quest needs at least one stage");
    }
    return quest;
}

DialogueDef parse_dialogue_json(const Json& j) {
    DialogueDef dialogue;
    dialogue.id = j.value("id", "");
    dialogue.start = j.at("start").get<std::string>();
    for (const auto& [name, n] : j.at("nodes").items()) {
        DialogueNode node;
        const std::string type = n.at("type").get<std::string>();
        if (type == "say") {
            node.kind = DialogueNode::Kind::Say;
            node.speaker = n.value("speaker", "");
            node.text = n.at("text").get<std::string>();
            node.next = n.at("next").get<std::string>();
        } else if (type == "choice") {
            node.kind = DialogueNode::Kind::Choice;
            for (const Json& c : n.at("choices")) {
                DialogueChoice choice;
                choice.text = c.at("text").get<std::string>();
                if (c.contains("when")) {
                    choice.has_when = true;
                    choice.when = parse_condition(c.at("when"));
                }
                choice.effects = parse_effects(c, "effects");
                choice.next = c.at("next").get<std::string>();
                node.choices.push_back(std::move(choice));
            }
        } else if (type == "set_flag") {
            node.kind = DialogueNode::Kind::SetFlag;
            node.flag = n.at("flag").get<std::string>();
            node.value = n.at("value").get<bool>();
            node.next = n.at("next").get<std::string>();
        } else if (type == "effects") {
            node.kind = DialogueNode::Kind::Effects;
            node.effects = parse_effects(n, "effects");
            node.next = n.at("next").get<std::string>();
        } else if (type == "condition") {
            node.kind = DialogueNode::Kind::Cond;
            node.when = parse_condition(n.at("when"));
            node.then_next = n.at("then").get<std::string>();
            node.else_next = n.at("else").get<std::string>();
        } else {
            throw std::runtime_error("unknown dialogue node type " + type);
        }
        dialogue.nodes.emplace(name, std::move(node));
    }
    if (dialogue.nodes.find(dialogue.start) == dialogue.nodes.end()) {
        throw std::runtime_error("the start node does not exist");
    }
    return dialogue;
}

}  // namespace

std::optional<QuestDef> parse_quest(std::string_view json_text, std::string& error) {
    try {
        return parse_quest_json(Json::parse(json_text));
    } catch (const std::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::optional<DialogueDef> parse_dialogue(std::string_view json_text, std::string& error) {
    try {
        return parse_dialogue_json(Json::parse(json_text));
    } catch (const std::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

std::optional<StorySetup> parse_story_setup(std::string_view json_text, std::string& error) {
    try {
        const Json j = Json::parse(json_text);
        StorySetup setup;
        for (const auto& [id, q] : j.at("quests").items()) {
            setup.quests.emplace(id, parse_quest_json(q));
        }
        for (const auto& [id, d] : j.at("dialogues").items()) {
            setup.dialogues.emplace(id, parse_dialogue_json(d));
        }
        for (const Json& n : j.at("npcs")) {
            NpcDef npc;
            npc.key = n.at("key").get<std::string>();
            npc.dialogue = n.at("dialogue").get<std::string>();
            npc.variant = n.value("variant", "");
            npc.x = n.at("pos").at(0).get<float>();
            npc.y = n.at("pos").at(1).get<float>();
            setup.npcs.push_back(std::move(npc));
        }
        return setup;
    } catch (const std::exception& e) {
        error = e.what();
        return std::nullopt;
    }
}

// ------------------------------------------------------------------------------------- runtime

Story::Story(StorySetup setup, StoryHost& host) : m_setup_(std::move(setup)), m_host_(host) {}

bool Story::holds(const Condition& c) const {
    switch (c.kind) {
        case Condition::Kind::Flag: {
            const auto found = m_flags_.find(c.a);
            return found != m_flags_.end() && found->second;
        }
        case Condition::Kind::Not:
            return !holds(c.children.front());
        case Condition::Kind::All:
            return std::all_of(c.children.begin(), c.children.end(), [this](const Condition& x) { return holds(x); });
        case Condition::Kind::Any:
            return std::any_of(c.children.begin(), c.children.end(), [this](const Condition& x) { return holds(x); });
        case Condition::Kind::QuestActive: {
            const auto found = m_quests_.find(c.a);
            return found != m_quests_.end() && !found->second.done;
        }
        case Condition::Kind::QuestDone: {
            const auto found = m_quests_.find(c.a);
            return found != m_quests_.end() && found->second.done;
        }
        case Condition::Kind::QuestStage: {
            const auto found = m_quests_.find(c.a);
            return found != m_quests_.end() && !found->second.done && found->second.stage == c.b;
        }
        case Condition::Kind::HasItem: {
            const auto& inventory = m_host_.host_inventory();
            const auto found = inventory.find(c.a);
            return found != inventory.end() && found->second >= c.n;
        }
        case Condition::Kind::LevelAtLeast:
            return m_host_.level() >= c.n;
    }
    return false;
}

void Story::apply(const Effect& effect) {
    switch (effect.kind) {
        case Effect::Kind::AddXp:
            m_host_.grant_xp(effect.n);
            break;
        case Effect::Kind::AddGold:
            m_gold_ += effect.n;
            break;
        case Effect::Kind::AddItem:
            m_host_.host_inventory()[effect.a] += effect.n;
            refresh_all();
            break;
        case Effect::Kind::SetFlag:
            m_flags_[effect.a] = effect.value;
            break;
        case Effect::Kind::StartQuest:
            start_quest(effect.a);
            break;
    }
}

const QuestStage& Story::current_stage(const std::string& quest_id) const {
    const QuestDef& def = m_setup_.quests.at(quest_id);
    const std::string& stage = m_quests_.at(quest_id).stage;
    for (const QuestStage& s : def.stages) {
        if (s.id == stage) {
            return s;
        }
    }
    return def.stages.front();
}

void Story::start_quest(const std::string& quest_id) {
    if (m_quests_.find(quest_id) != m_quests_.end()) {
        return;
    }
    const auto def = m_setup_.quests.find(quest_id);
    if (def == m_setup_.quests.end()) {
        return;
    }
    const QuestStage& stage = def->second.stages.front();
    QuestProgress progress;
    progress.stage = stage.id;
    progress.progress.assign(stage.objectives.size(), 0);
    m_quests_[quest_id] = std::move(progress);
    refresh(quest_id);
}

void Story::refresh_all() {
    std::vector<std::string> ids;
    for (const auto& entry : m_quests_) {
        ids.push_back(entry.first);
    }
    for (const std::string& id : ids) {
        refresh(id);
    }
}

void Story::refresh(const std::string& quest_id) {
    for (;;) {
        QuestProgress& q = m_quests_.at(quest_id);
        if (q.done) {
            return;
        }
        const QuestStage& stage = current_stage(quest_id);
        for (std::size_t i = 0; i < stage.objectives.size(); ++i) {
            const Objective& o = stage.objectives[i];
            if (o.kind == Objective::Kind::Collect) {
                const auto& inventory = m_host_.host_inventory();
                const auto found = inventory.find(o.target);
                const std::int64_t have = found == inventory.end() ? 0 : found->second;
                q.progress[i] = std::min(o.count, have);
            }
        }
        for (std::size_t i = 0; i < stage.objectives.size(); ++i) {
            if (q.progress[i] < stage.objectives[i].required()) {
                return;
            }
        }
        if (stage.next == "end") {
            q.done = true;
            // Copy: applying a reward can change the quest table through other effects.
            const std::vector<Effect> rewards = m_setup_.quests.at(quest_id).rewards;
            for (const Effect& reward : rewards) {
                apply(reward);
            }
            return;
        }
        const QuestDef& def = m_setup_.quests.at(quest_id);
        for (const QuestStage& next : def.stages) {
            if (next.id == stage.next) {
                q.stage = next.id;
                q.progress.assign(next.objectives.size(), 0);
                break;
            }
        }
    }
}

void Story::on_kill(std::string_view enemy_id) {
    for (auto& [quest_id, q] : m_quests_) {
        if (q.done) {
            continue;
        }
        const QuestStage& stage = current_stage(quest_id);
        for (std::size_t i = 0; i < stage.objectives.size(); ++i) {
            const Objective& o = stage.objectives[i];
            if (o.kind == Objective::Kind::Kill && o.target == enemy_id) {
                q.progress[i] = std::min(o.count, q.progress[i] + 1);
            }
        }
    }
    refresh_all();
}

void Story::on_talk(std::string_view npc_key) {
    for (auto& [quest_id, q] : m_quests_) {
        if (q.done) {
            continue;
        }
        const QuestStage& stage = current_stage(quest_id);
        for (std::size_t i = 0; i < stage.objectives.size(); ++i) {
            const Objective& o = stage.objectives[i];
            if (o.kind == Objective::Kind::Talk && o.target == npc_key) {
                q.progress[i] = 1;
            }
        }
    }
    refresh_all();
}

// ----------------------------------------------------------------------------------- dialogue

const DialogueNode& Story::node() const { return m_setup_.dialogues.at(m_dialogue_id_).nodes.at(m_node_); }

void Story::start_dialogue(const std::string& dialogue_id) {
    const auto found = m_setup_.dialogues.find(dialogue_id);
    if (found == m_setup_.dialogues.end()) {
        return;
    }
    m_dialogue_active_ = true;
    m_dialogue_id_ = dialogue_id;
    m_node_ = found->second.start;
    settle();
}

void Story::go(const std::string& target) {
    if (target == "end") {
        m_dialogue_active_ = false;
        return;
    }
    m_node_ = target;
    settle();
}

void Story::settle() {
    for (int step = 0; step < kMaxSettleSteps; ++step) {
        if (!m_dialogue_active_) {
            return;
        }
        const DialogueNode& n = node();
        std::string target;
        switch (n.kind) {
            case DialogueNode::Kind::Say:
            case DialogueNode::Kind::Choice:
                return;
            case DialogueNode::Kind::SetFlag:
                m_flags_[n.flag] = n.value;
                target = n.next;
                break;
            case DialogueNode::Kind::Effects: {
                const std::vector<Effect> effects = n.effects;
                for (const Effect& effect : effects) {
                    apply(effect);
                }
                target = n.next;
                break;
            }
            case DialogueNode::Kind::Cond:
                target = holds(n.when) ? n.then_next : n.else_next;
                break;
        }
        if (target == "end") {
            m_dialogue_active_ = false;
            return;
        }
        m_node_ = target;
    }
    m_dialogue_active_ = false;  // runaway graph: close it
}

std::vector<const DialogueChoice*> Story::visible_choices() const {
    std::vector<const DialogueChoice*> out;
    for (const DialogueChoice& c : node().choices) {
        if (!c.has_when || holds(c.when)) {
            out.push_back(&c);
        }
    }
    return out;
}

void Story::advance() {
    if (m_dialogue_active_ && node().kind == DialogueNode::Kind::Say) {
        go(node().next);
    }
}

void Story::choose(int index) {
    if (!m_dialogue_active_ || node().kind != DialogueNode::Kind::Choice) {
        return;
    }
    const auto choices = visible_choices();
    if (index < 0 || index >= static_cast<int>(choices.size())) {
        return;
    }
    const DialogueChoice choice = *choices[static_cast<std::size_t>(index)];
    for (const Effect& effect : choice.effects) {
        apply(effect);
    }
    go(choice.next);
}

const NpcDef* Story::npc_in_range() const {
    const NpcDef* best = nullptr;
    float best_dist = kInteractRange;
    for (const NpcDef& npc : m_setup_.npcs) {
        const float dx = npc.x - m_host_.player_x();
        const float dy = npc.y - m_host_.player_y();
        const float d = std::sqrt(dx * dx + dy * dy);
        if (d <= best_dist && (best == nullptr || d < best_dist)) {
            best = &npc;
            best_dist = d;
        }
    }
    return best;
}

void Story::interact() {
    if (m_dialogue_active_) {
        advance();
        return;
    }
    if (const NpcDef* npc = npc_in_range()) {
        const std::string key = npc->key;
        const std::string dialogue = npc->dialogue;
        on_talk(key);
        start_dialogue(dialogue);
    }
}

StoryState Story::capture() const {
    StoryState state;
    state.flags = m_flags_;
    state.gold = m_gold_;
    state.quests = m_quests_;
    state.dialogue_active = m_dialogue_active_;
    state.dialogue_id = m_dialogue_id_;
    state.node = m_node_;
    return state;
}

bool Story::restore(const StoryState& state) {
    if (state.dialogue_active) {
        const auto dialogue = m_setup_.dialogues.find(state.dialogue_id);
        if (dialogue == m_setup_.dialogues.end() || dialogue->second.nodes.find(state.node) == dialogue->second.nodes.end()) {
            return false;
        }
    }
    for (const auto& entry : state.quests) {
        if (m_setup_.quests.find(entry.first) == m_setup_.quests.end()) {
            return false;
        }
    }
    m_flags_ = state.flags;
    m_gold_ = state.gold;
    m_quests_ = state.quests;
    m_dialogue_active_ = state.dialogue_active;
    m_dialogue_id_ = state.dialogue_id;
    m_node_ = state.node;
    return true;
}

DialogueView Story::dialogue_view() const {
    DialogueView view;
    if (!m_dialogue_active_) {
        return view;
    }
    view.active = true;
    const DialogueNode& n = node();
    if (n.kind == DialogueNode::Kind::Say) {
        view.speaker = n.speaker;
        view.text = n.text;
    } else {
        view.is_choice = true;
        for (const DialogueChoice* c : visible_choices()) {
            view.choices.push_back(c->text);
        }
    }
    return view;
}

}  // namespace aether
