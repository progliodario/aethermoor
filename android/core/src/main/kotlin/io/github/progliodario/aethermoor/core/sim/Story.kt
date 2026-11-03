package io.github.progliodario.aethermoor.core.sim

import io.github.progliodario.aethermoor.core.Offer
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

    data class GoldAtLeast(val gold: Long) : Condition
}

sealed interface Effect {
    data class AddXp(val amount: Long) : Effect

    data class AddGold(val amount: Long) : Effect

    data class AddItem(val item: String, val qty: Long) : Effect

    data class RemoveItem(val item: String, val qty: Long) : Effect

    data class SpendGold(val amount: Long) : Effect

    /** The health of the player becomes the maximum. */
    data object HealFull : Effect

    data class SetFlag(val flag: String, val value: Boolean) : Effect

    data class StartQuest(val quest: String) : Effect

    /** Opens the shop of the place (spec 06). */
    data object OpenShop : Effect

    data class AddGuildPoints(val amount: Long) : Effect

    /** Opens the guild board of the settlement (spec 07). */
    data object OpenBoard : Effect
}

enum class ObjectiveKind { KILL, COLLECT, TALK }

data class Objective(val kind: ObjectiveKind, val target: String, val count: Long = 1) {
    val required: Long get() = if (kind == ObjectiveKind.TALK) 1 else count
}

data class QuestStage(val id: String, val journal: String, val objectives: List<Objective>, val next: String)

/** [args] are the arguments of the name and journal texts (spec 07). */
data class QuestDef(
    val id: String,
    val name: String,
    val stages: List<QuestStage>,
    val rewards: List<Effect>,
    val args: Map<String, String> = emptyMap(),
)

/** The quest of a board offer (spec 07, "Guild"). */
fun questFromOffer(offer: Offer): QuestDef {
    val targetKey = offer.target.substringAfter(':').replace('/', '.')
    return QuestDef(
        id = offer.id,
        name = "\$i18n:quest.board.${offer.template}.${offer.tone}.name",
        stages = listOf(
            QuestStage(
                "work", "\$i18n:quest.board.${offer.template}.${offer.tone}.journal",
                listOf(Objective(if (offer.type == "kill") ObjectiveKind.KILL else ObjectiveKind.COLLECT, offer.target, offer.count.toLong())),
                "end",
            ),
        ),
        rewards = listOf(Effect.AddXp(offer.xp), Effect.AddGold(offer.gold), Effect.AddGuildPoints(offer.points)),
        args = mapOf("count" to offer.count.toString(), "target" to "\$i18n:$targetKey.name", "place" to offer.place),
    )
}

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
/** [name] and [args] are set for settlement people: the arguments of the dialogue texts (spec 07). */
data class NpcDef(
    val key: String,
    val dialogue: String,
    val variant: String,
    val x: Float,
    val y: Float,
    val name: String = "",
    val args: Map<String, String> = emptyMap(),
)

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
    val args: Map<String, String> = emptyMap(),
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
    val dialogueArgs: Map<String, String> = emptyMap(),
    val guildPoints: Long = 0,
)

/** What the story needs from the world that owns it. */
interface StoryHost {
    fun grantXp(amount: Long)

    val inventory: MutableMap<String, Long>
    val level: Long
    val playerX: Float
    val playerY: Float

    fun openShop()

    fun openBoard()

    fun healFull()
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
        "gold_at_least" -> Condition.GoldAtLeast(value.jsonPrimitive.long)
        else -> throw IllegalArgumentException("unknown condition $key")
    }
}

private fun parseEffect(element: JsonElement): Effect {
    val o = element.jsonObject
    return when (val kind = o.str("effect")) {
        "add_xp" -> Effect.AddXp(o.getValue("amount").jsonPrimitive.long)
        "add_gold" -> Effect.AddGold(o.getValue("amount").jsonPrimitive.long)
        "add_item" -> Effect.AddItem(o.str("item"), o.getValue("qty").jsonPrimitive.long)
        "spend_gold" -> Effect.SpendGold(o.getValue("amount").jsonPrimitive.long)
        "heal_full" -> Effect.HealFull
        "remove_item" -> Effect.RemoveItem(o.str("item"), o.getValue("qty").jsonPrimitive.long)
        "set_flag" -> Effect.SetFlag(o.str("flag"), o.getValue("value").jsonPrimitive.boolean)
        "start_quest" -> Effect.StartQuest(o.str("quest"))
        "open_shop" -> Effect.OpenShop
        "open_board" -> Effect.OpenBoard
        "add_guild_points" -> Effect.AddGuildPoints(o.getValue("amount").jsonPrimitive.long)
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
    val args = (j["args"] as? JsonObject)?.mapValues { it.value.jsonPrimitive.content } ?: emptyMap()
    return QuestDef(optStr(j, "id"), optStr(j, "name"), stages, parseEffects(j, "rewards"), args)
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
    /** The gold of the player; shops and tests change it directly (spec 06). */
    var gold = 0L

    /** The guild points of the player (spec 07). */
    var guildPoints = 0L

    private val generated = HashMap<String, QuestDef>()

    /** Rebuilds the quest of a generated id when a save is loaded; set by the world. */
    var questResolver: ((String) -> QuestDef?)? = null

    /** The definition of a quest of the pack or a generated one. */
    fun questDef(questId: String): QuestDef? = setup.quests[questId] ?: generated[questId]

    /** Adds the quest of a board offer to the known quests (it can then be started and saved). */
    fun addGeneratedQuest(quest: QuestDef) {
        generated.putIfAbsent(quest.id, quest)
    }
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
            is Condition.GoldAtLeast -> gold >= c.gold
        }

    fun apply(effect: Effect) {
        when (effect) {
            is Effect.AddXp -> host.grantXp(effect.amount)
            is Effect.AddGold -> gold += effect.amount
            is Effect.AddItem -> {
                host.inventory[effect.item] = (host.inventory[effect.item] ?: 0L) + effect.qty
                refreshAll()
            }
            is Effect.SpendGold -> gold = maxOf(0L, gold - effect.amount)
            is Effect.HealFull -> host.healFull()
            is Effect.RemoveItem -> {
                val held = host.inventory[effect.item] ?: 0L
                val left = held - minOf(held, effect.qty)
                if (left > 0L) host.inventory[effect.item] = left else host.inventory.remove(effect.item)
                refreshAll()
            }
            is Effect.SetFlag -> flags[effect.flag] = effect.value
            is Effect.StartQuest -> startQuest(effect.quest)
            is Effect.OpenShop -> host.openShop()
            is Effect.OpenBoard -> host.openBoard()
            is Effect.AddGuildPoints -> guildPoints += effect.amount
        }
    }

    private fun currentStage(questId: String): QuestStage {
        val def = questDef(questId)!!
        val stage = quests.getValue(questId).stage
        return def.stages.firstOrNull { it.id == stage } ?: def.stages.first()
    }

    fun startQuest(questId: String) {
        if (questId in quests) return
        val def = questDef(questId) ?: return
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
                for (reward in ArrayList(questDef(questId)!!.rewards)) apply(reward)
                return
            }
            val next = questDef(questId)!!.stages.first { it.id == stage.next }
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
    /** NPCs that come and go with the world (settlement people), listed after the static ones. */
    var dynamicNpcs: List<NpcDef> = emptyList()
    private var dialogueArgs: Map<String, String> = emptyMap()

    fun npcInRange(): NpcDef? {
        var best: NpcDef? = null
        var bestDist = INTERACT_RANGE
        for (npc in setup.npcs + dynamicNpcs) {
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
        dialogueArgs = if (npc.name.isEmpty()) npc.args else npc.args + ("npc" to npc.name)
        onTalk(npc.key)
        startDialogue(npc.dialogue)
    }

    fun capture(): StoryState =
        StoryState(
            HashMap(flags), gold, quests.mapValues { QuestProgress(it.value.stage, it.value.progress.copyOf(), it.value.done) },
            dialogueActive, dialogueId, nodeName, HashMap(dialogueArgs), guildPoints,
        )

    /** Returns false (and changes nothing) when the state names a quest, dialogue or node that does not exist. */
    fun restore(state: StoryState): Boolean {
        if (state.dialogueActive && setup.dialogues[state.dialogueId]?.nodes?.containsKey(state.node) != true) return false
        for (id in state.quests.keys) {
            if (questDef(id) != null) continue
            // A generated quest (spec 07, "Guild"): the world rebuilds it from its id.
            val rebuilt = questResolver?.invoke(id) ?: return false
            generated[id] = rebuilt
        }
        flags.clear()
        flags.putAll(state.flags)
        gold = state.gold
        guildPoints = state.guildPoints
        quests.clear()
        for ((id, q) in state.quests) quests[id] = QuestProgress(q.stage, q.progress.copyOf(), q.done)
        dialogueActive = state.dialogueActive
        dialogueId = state.dialogueId
        nodeName = state.node
        dialogueArgs = HashMap(state.dialogueArgs)
        return true
    }

    fun dialogueView(): DialogueView {
        if (!dialogueActive) return DialogueView()
        return when (val n = node()) {
            is DialogueNode.Say -> DialogueView(active = true, isChoice = false, speaker = n.speaker, text = n.text, args = dialogueArgs)
            else -> DialogueView(active = true, isChoice = true, choices = visibleChoices().map { it.text }, args = dialogueArgs)
        }
    }
}
