package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.vector.f
import kotlin.math.min
import kotlin.math.sqrt
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.long

// Quests, dialogue, conditions and effects. Spec: docs/spec/07-quests-and-dialogue.md.
// Keep this file in step with desktop/src/sim/story.cpp and tools/reference/story.py.

sealed interface Condition {
    data class Flag(val name: String) : Condition

    data class Negation(val inner: Condition) : Condition

    data class AllOf(val items: List<Condition>) : Condition

    data class AnyOf(val items: List<Condition>) : Condition

    data class QuestActive(val quest: String) : Condition

    data class QuestDone(val quest: String) : Condition

    data class QuestStage(val quest: String, val stage: String) : Condition

    data class HasItem(val item: String, val qty: Long) : Condition

    data class LevelAtLeast(val level: Long) : Condition
}

sealed interface Effect {
    data class AddXp(val amount: Long) : Effect

    data class AddGold(val amount: Long) : Effect

    data class AddItem(val item: String, val qty: Long) : Effect

    data class SetFlag(val flag: String, val value: Boolean) : Effect

    data class StartQuest(val quest: String) : Effect
}

enum class ObjectiveKind { KILL, COLLECT, TALK }

data class Objective(val kind: ObjectiveKind, val target: String, val count: Long = 1) {
    val required: Long get() = if (kind == ObjectiveKind.TALK) 1 else count
}

data class QuestStage(val id: String, val journal: String, val objectives: List<Objective>, val next: String)

data class QuestDef(val id: String, val name: String, val stages: List<QuestStage>, val rewards: List<Effect>)

data class DialogueChoice(val text: String, val whenCondition: Condition?, val effects: List<Effect>, val next: String)

sealed interface DialogueNode {
    data class Say(val speaker: String, val text: String, val next: String) : DialogueNode

    data class Choice(val choices: List<DialogueChoice>) : DialogueNode

    data class SetFlag(val flag: String, val value: Boolean, val next: String) : DialogueNode

    data class Effects(val effects: List<Effect>, val next: String) : DialogueNode

    data class Cond(val whenCondition: Condition, val thenNext: String, val elseNext: String) : DialogueNode
}

data class DialogueDef(val id: String, val start: String, val nodes: Map<String, DialogueNode>)

/** An NPC: [x], [y] is the feet position in tiles. */
data class NpcDef(val key: String, val dialogue: String, val variant: String, val x: Float, val y: Float)

class StorySetup(
    val quests: Map<String, QuestDef> = emptyMap(),
    val dialogues: Map<String, DialogueDef> = emptyMap(),
    val npcs: List<NpcDef> = emptyList(),
)

/** What the player currently sees. */
data class DialogueView(
    val active: Boolean = false,
    val isChoice: Boolean = false,
    val speaker: String = "",
    val text: String = "",
    val choices: List<String> = emptyList(),
)

class QuestProgress(var stage: String, var progress: LongArray, var done: Boolean = false)

/** The part of the story that changes while playing (saves). */
class StoryState(
    val flags: Map<String, Boolean>,
    val gold: Long,
    val quests: Map<String, QuestProgress>,
    val dialogueActive: Boolean,
    val dialogueId: String,
    val node: String,
)

/** What the story needs from the world that owns it. */
interface StoryHost {
    fun grantXp(amount: Long)

    val inventory: MutableMap<String, Long>
    val level: Long
    val playerX: Float
    val playerY: Float
}

// ------------------------------------------------------------------------------------ parsing

private fun JsonObject.str(key: String) = getValue(key).jsonPrimitive.content

private fun optStr(o: JsonObject, key: String) = (o[key] as? JsonPrimitive)?.contentOrNull ?: ""

private fun parseCondition(element: JsonElement): Condition {
    val o = element.jsonObject
    require(o.size == 1) { "a condition must be an object with exactly one key" }
    val (key, value) = o.entries.first()
    return when (key) {
        "flag" -> Condition.Flag(value.jsonPrimitive.content)
        "not" -> Condition.Negation(parseCondition(value))
        "all" -> Condition.AllOf(value.jsonArray.map { parseCondition(it) })
        "any" -> Condition.AnyOf(value.jsonArray.map { parseCondition(it) })
        "quest_active" -> Condition.QuestActive(value.jsonPrimitive.content)
        "quest_done" -> Condition.QuestDone(value.jsonPrimitive.content)
        "quest_stage" -> Condition.QuestStage(value.jsonObject.str("quest"), value.jsonObject.str("stage"))
        "has_item" -> Condition.HasItem(value.jsonObject.str("item"), value.jsonObject.getValue("qty").jsonPrimitive.long)
        "level_at_least" -> Condition.LevelAtLeast(value.jsonPrimitive.long)
        else -> throw IllegalArgumentException("unknown condition $key")
    }
}

private fun parseEffect(element: JsonElement): Effect {
    val o = element.jsonObject
    return when (val kind = o.str("effect")) {
        "add_xp" -> Effect.AddXp(o.getValue("amount").jsonPrimitive.long)
        "add_gold" -> Effect.AddGold(o.getValue("amount").jsonPrimitive.long)
        "add_item" -> Effect.AddItem(o.str("item"), o.getValue("qty").jsonPrimitive.long)
        "set_flag" -> Effect.SetFlag(o.str("flag"), o.getValue("value").jsonPrimitive.boolean)
        "start_quest" -> Effect.StartQuest(o.str("quest"))
        else -> throw IllegalArgumentException("unknown effect $kind")
    }
}

private fun parseEffects(o: JsonObject, key: String): List<Effect> = o[key]?.jsonArray?.map { parseEffect(it) } ?: emptyList()

private fun parseQuestObject(j: JsonObject): QuestDef {
    val stages = j.getValue("stages").jsonArray.map { stageElement ->
        val s = stageElement.jsonObject
        QuestStage(
            id = s.str("id"),
            journal = optStr(s, "journal"),
            objectives = s.getValue("objectives").jsonArray.map { objectiveElement ->
                val o = objectiveElement.jsonObject
                when (val type = o.str("type")) {
                    "kill" -> Objective(ObjectiveKind.KILL, o.str("enemy"), o.getValue("count").jsonPrimitive.long)
                    "collect" -> Objective(ObjectiveKind.COLLECT, o.str("item"), o.getValue("count").jsonPrimitive.long)
                    "talk" -> Objective(ObjectiveKind.TALK, o.str("npc_key"))
                    else -> throw IllegalArgumentException("unknown objective $type")
                }
            },
            next = s.str("next"),
        )
    }
    require(stages.isNotEmpty()) { "a quest needs at least one stage" }
    return QuestDef(optStr(j, "id"), optStr(j, "name"), stages, parseEffects(j, "rewards"))
}

private fun parseDialogueObject(j: JsonObject): DialogueDef {
    val nodes = j.getValue("nodes").jsonObject.mapValues { (_, element) ->
        val n = element.jsonObject
        when (val type = n.str("type")) {
            "say" -> DialogueNode.Say(optStr(n, "speaker"), n.str("text"), n.str("next"))
            "choice" -> DialogueNode.Choice(
                n.getValue("choices").jsonArray.map { choiceElement ->
                    val c = choiceElement.jsonObject
                    DialogueChoice(c.str("text"), c["when"]?.let { parseCondition(it) }, parseEffects(c, "effects"), c.str("next"))
                },
            )
            "set_flag" -> DialogueNode.SetFlag(n.str("flag"), n.getValue("value").jsonPrimitive.boolean, n.str("next"))
            "effects" -> DialogueNode.Effects(parseEffects(n, "effects"), n.str("next"))
            "condition" -> DialogueNode.Cond(parseCondition(n.getValue("when")), n.str("then"), n.str("else"))
            else -> throw IllegalArgumentException("unknown dialogue node type $type")
        }
    }
    val start = j.str("start")
    require(start in nodes) { "the start node does not exist" }
    return DialogueDef(optStr(j, "id"), start, nodes)
}

fun parseQuest(jsonText: String): Result<QuestDef> = runCatching { parseQuestObject(Json.parseToJsonElement(jsonText).jsonObject) }

fun parseDialogue(jsonText: String): Result<DialogueDef> = runCatching { parseDialogueObject(Json.parseToJsonElement(jsonText).jsonObject) }

/** Parses the scenario "story" section used by the conformance tests. */
fun parseStorySetup(element: JsonElement): StorySetup {
    val j = element.jsonObject
    return StorySetup(
        quests = j.getValue("quests").jsonObject.mapValues { parseQuestObject(it.value.jsonObject) },
        dialogues = j.getValue("dialogues").jsonObject.mapValues { parseDialogueObject(it.value.jsonObject) },
        npcs = j.getValue("npcs").jsonArray.map {
            val n = it.jsonObject
            val pos = n.getValue("pos").jsonArray
            NpcDef(n.str("key"), n.str("dialogue"), optStr(n, "variant"), pos[0].f(), pos[1].f())
        },
    )
}

// ------------------------------------------------------------------------------------- runtime

private const val INTERACT_RANGE = 1.5f
private const val MAX_SETTLE_STEPS = 64

class Story(val setup: StorySetup, private val host: StoryHost) {
    val flags = java.util.TreeMap<String, Boolean>()
    var gold = 0L
        private set
    val quests = java.util.TreeMap<String, QuestProgress>()
    var dialogueActive = false
        private set
    private var dialogueId = ""
    private var nodeName = ""

    fun holds(c: Condition): Boolean =
        when (c) {
            is Condition.Flag -> flags[c.name] == true
            is Condition.Negation -> !holds(c.inner)
            is Condition.AllOf -> c.items.all { holds(it) }
            is Condition.AnyOf -> c.items.any { holds(it) }
            is Condition.QuestActive -> quests[c.quest]?.let { !it.done } ?: false
            is Condition.QuestDone -> quests[c.quest]?.done ?: false
            is Condition.QuestStage -> quests[c.quest]?.let { !it.done && it.stage == c.stage } ?: false
            is Condition.HasItem -> (host.inventory[c.item] ?: 0L) >= c.qty
            is Condition.LevelAtLeast -> host.level >= c.level
        }

    fun apply(effect: Effect) {
        when (effect) {
            is Effect.AddXp -> host.grantXp(effect.amount)
            is Effect.AddGold -> gold += effect.amount
            is Effect.AddItem -> {
                host.inventory[effect.item] = (host.inventory[effect.item] ?: 0L) + effect.qty
                refreshAll()
            }
            is Effect.SetFlag -> flags[effect.flag] = effect.value
            is Effect.StartQuest -> startQuest(effect.quest)
        }
    }

    private fun currentStage(questId: String): QuestStage {
        val def = setup.quests.getValue(questId)
        val stage = quests.getValue(questId).stage
        return def.stages.firstOrNull { it.id == stage } ?: def.stages.first()
    }

    fun startQuest(questId: String) {
        if (questId in quests) return
        val def = setup.quests[questId] ?: return
        val stage = def.stages.first()
        quests[questId] = QuestProgress(stage.id, LongArray(stage.objectives.size))
        refresh(questId)
    }

    private fun refreshAll() {
        for (id in ArrayList(quests.keys)) refresh(id)
    }

    private fun refresh(questId: String) {
        while (true) {
            val q = quests.getValue(questId)
            if (q.done) return
            val stage = currentStage(questId)
            for ((i, o) in stage.objectives.withIndex()) {
                if (o.kind == ObjectiveKind.COLLECT) q.progress[i] = min(o.count, host.inventory[o.target] ?: 0L)
            }
            for ((i, o) in stage.objectives.withIndex()) {
                if (q.progress[i] < o.required) return
            }
            if (stage.next == "end") {
                q.done = true
                for (reward in ArrayList(setup.quests.getValue(questId).rewards)) apply(reward)
                return
            }
            val next = setup.quests.getValue(questId).stages.first { it.id == stage.next }
            q.stage = next.id
            q.progress = LongArray(next.objectives.size)
        }
    }

    fun onKill(enemyId: String) {
        for ((questId, q) in quests) {
            if (q.done) continue
            for ((i, o) in currentStage(questId).objectives.withIndex()) {
                if (o.kind == ObjectiveKind.KILL && o.target == enemyId) q.progress[i] = min(o.count, q.progress[i] + 1)
            }
        }
        refreshAll()
    }

    fun onTalk(npcKey: String) {
        for ((questId, q) in quests) {
            if (q.done) continue
            for ((i, o) in currentStage(questId).objectives.withIndex()) {
                if (o.kind == ObjectiveKind.TALK && o.target == npcKey) q.progress[i] = 1
            }
        }
        refreshAll()
    }

    // ----------------------------------------------------------------------------- dialogue

    private fun node(): DialogueNode = setup.dialogues.getValue(dialogueId).nodes.getValue(nodeName)

    private fun startDialogue(id: String) {
        val def = setup.dialogues[id] ?: return
        dialogueActive = true
        dialogueId = id
        nodeName = def.start
        settle()
    }

    private fun go(target: String) {
        if (target == "end") {
            dialogueActive = false
            return
        }
        nodeName = target
        settle()
    }

    private fun settle() {
        repeat(MAX_SETTLE_STEPS) {
            if (!dialogueActive) return
            val target: String =
                when (val n = node()) {
                    is DialogueNode.Say, is DialogueNode.Choice -> return
                    is DialogueNode.SetFlag -> {
                        flags[n.flag] = n.value
                        n.next
                    }
                    is DialogueNode.Effects -> {
                        for (effect in ArrayList(n.effects)) apply(effect)
                        n.next
                    }
                    is DialogueNode.Cond -> if (holds(n.whenCondition)) n.thenNext else n.elseNext
                }
            if (target == "end") {
                dialogueActive = false
                return
            }
            nodeName = target
        }
        dialogueActive = false // runaway graph: close it
    }

    private fun visibleChoices(): List<DialogueChoice> =
        (node() as DialogueNode.Choice).choices.filter { it.whenCondition == null || holds(it.whenCondition) }

    fun advance() {
        val n = if (dialogueActive) node() else return
        if (n is DialogueNode.Say) go(n.next)
    }

    fun choose(index: Int) {
        if (!dialogueActive || node() !is DialogueNode.Choice) return
        val choices = visibleChoices()
        if (index < 0 || index >= choices.size) return
        val choice = choices[index]
        for (effect in choice.effects) apply(effect)
        go(choice.next)
    }

    /** The NPC [interact] would talk to now, or null. */
    fun npcInRange(): NpcDef? {
        var best: NpcDef? = null
        var bestDist = INTERACT_RANGE
        for (npc in setup.npcs) {
            val dx = npc.x - host.playerX
            val dy = npc.y - host.playerY
            val d = sqrt(dx * dx + dy * dy)
            if (d <= bestDist && (best == null || d < bestDist)) {
                best = npc
                bestDist = d
            }
        }
        return best
    }

    fun interact() {
        if (dialogueActive) {
            advance()
            return
        }
        val npc = npcInRange() ?: return
        onTalk(npc.key)
        startDialogue(npc.dialogue)
    }

    fun capture(): StoryState =
        StoryState(
            HashMap(flags), gold, quests.mapValues { QuestProgress(it.value.stage, it.value.progress.copyOf(), it.value.done) },
            dialogueActive, dialogueId, nodeName,
        )

    /** Returns false (and changes nothing) when the state names a quest, dialogue or node that does not exist. */
    fun restore(state: StoryState): Boolean {
        if (state.dialogueActive && setup.dialogues[state.dialogueId]?.nodes?.containsKey(state.node) != true) return false
        if (state.quests.keys.any { it !in setup.quests }) return false
        flags.clear()
        flags.putAll(state.flags)
        gold = state.gold
        quests.clear()
        for ((id, q) in state.quests) quests[id] = QuestProgress(q.stage, q.progress.copyOf(), q.done)
        dialogueActive = state.dialogueActive
        dialogueId = state.dialogueId
        nodeName = state.node
        return true
    }

    fun dialogueView(): DialogueView {
        if (!dialogueActive) return DialogueView()
        return when (val n = node()) {
            is DialogueNode.Say -> DialogueView(active = true, isChoice = false, speaker = n.speaker, text = n.text)
            else -> DialogueView(active = true, isChoice = true, choices = visibleChoices().map { it.text })
        }
    }
}
