"""Quests, dialogue, conditions and effects v1 (docs/spec/07-quests-and-dialogue.md). Integer rules.

`Story` works on top of a host (`CombatSim`) that owns the inventory, the XP/level machinery and the player position.
"""
from __future__ import annotations

import math

INTERACT_RANGE = 1.5
NPC_RADIUS = 0.3
MAX_SETTLE_STEPS = 64


class Story:
    def __init__(self, host, setup: dict) -> None:
        self.host = host
        self.quest_defs: dict[str, dict] = setup["quests"]
        self.dialogues: dict[str, dict] = setup["dialogues"]
        self.npcs: list[dict] = setup["npcs"]
        self.flags: dict[str, bool] = {}
        self.gold = 0
        self.quests: dict[str, dict] = {}
        self.dialogue: tuple[str, str] | None = None  # (dialogue id, node name)

    # ------------------------------------------------------------------------------ conditions

    def holds(self, c: dict) -> bool:
        (key, value), = c.items()
        if key == "flag":
            return self.flags.get(value, False)
        if key == "not":
            return not self.holds(value)
        if key == "all":
            return all(self.holds(x) for x in value)
        if key == "any":
            return any(self.holds(x) for x in value)
        if key == "quest_active":
            return value in self.quests and not self.quests[value]["done"]
        if key == "quest_done":
            return value in self.quests and self.quests[value]["done"]
        if key == "quest_stage":
            q = self.quests.get(value["quest"])
            return q is not None and not q["done"] and q["stage"] == value["stage"]
        if key == "has_item":
            return self.host.inventory.get(value["item"], 0) >= value["qty"]
        if key == "level_at_least":
            return self.host.level >= value
        raise ValueError(f"unknown condition {key}")

    # --------------------------------------------------------------------------------- effects

    def apply(self, effect: dict) -> None:
        kind = effect["effect"]
        if kind == "add_xp":
            self.host.grant_xp(effect["amount"])
        elif kind == "add_gold":
            self.gold += effect["amount"]
        elif kind == "add_item":
            self.host.inventory[effect["item"]] = self.host.inventory.get(effect["item"], 0) + effect["qty"]
            self._refresh_all()
        elif kind == "set_flag":
            self.flags[effect["flag"]] = effect["value"]
        elif kind == "start_quest":
            self.start_quest(effect["quest"])
        else:
            raise ValueError(f"unknown effect {kind}")

    # ----------------------------------------------------------------------------------- quests

    @staticmethod
    def _required(objective: dict) -> int:
        return 1 if objective["type"] == "talk" else objective["count"]

    def _stage(self, quest_id: str) -> dict:
        q = self.quests[quest_id]
        return next(s for s in self.quest_defs[quest_id]["stages"] if s["id"] == q["stage"])

    def start_quest(self, quest_id: str) -> None:
        if quest_id in self.quests:
            return
        stage = self.quest_defs[quest_id]["stages"][0]
        self.quests[quest_id] = {"stage": stage["id"], "progress": [0] * len(stage["objectives"]), "done": False}
        self._refresh(quest_id)

    def _refresh_all(self) -> None:
        for quest_id in sorted(self.quests):
            self._refresh(quest_id)

    def _refresh(self, quest_id: str) -> None:
        """Updates collect objectives, then advances stages while the current one is complete."""
        while True:
            q = self.quests[quest_id]
            if q["done"]:
                return
            stage = self._stage(quest_id)
            for i, objective in enumerate(stage["objectives"]):
                if objective["type"] == "collect":
                    q["progress"][i] = min(objective["count"], self.host.inventory.get(objective["item"], 0))
            if not all(q["progress"][i] >= self._required(o) for i, o in enumerate(stage["objectives"])):
                return
            if stage["next"] == "end":
                q["done"] = True
                for reward in self.quest_defs[quest_id].get("rewards", []):
                    self.apply(reward)
                return
            nxt = next(s for s in self.quest_defs[quest_id]["stages"] if s["id"] == stage["next"])
            q["stage"] = nxt["id"]
            q["progress"] = [0] * len(nxt["objectives"])

    def on_kill(self, enemy_id: str) -> None:
        for quest_id in sorted(self.quests):
            q = self.quests[quest_id]
            if q["done"]:
                continue
            for i, o in enumerate(self._stage(quest_id)["objectives"]):
                if o["type"] == "kill" and o["enemy"] == enemy_id:
                    q["progress"][i] = min(o["count"], q["progress"][i] + 1)
        self._refresh_all()

    def on_talk(self, npc_key: str) -> None:
        for quest_id in sorted(self.quests):
            q = self.quests[quest_id]
            if q["done"]:
                continue
            for i, o in enumerate(self._stage(quest_id)["objectives"]):
                if o["type"] == "talk" and o["npc_key"] == npc_key:
                    q["progress"][i] = 1
        self._refresh_all()

    # ---------------------------------------------------------------------------------- dialogue

    @property
    def dialogue_active(self) -> bool:
        return self.dialogue is not None

    def _node(self) -> dict:
        dialogue_id, name = self.dialogue
        return self.dialogues[dialogue_id]["nodes"][name]

    def start_dialogue(self, dialogue_id: str) -> None:
        self.dialogue = (dialogue_id, self.dialogues[dialogue_id]["start"])
        self._settle()

    def _go(self, target: str) -> None:
        if target == "end":
            self.dialogue = None
        else:
            self.dialogue = (self.dialogue[0], target)
            self._settle()

    def _settle(self) -> None:
        for _ in range(MAX_SETTLE_STEPS):
            if self.dialogue is None:
                return
            node = self._node()
            kind = node["type"]
            if kind in ("say", "choice"):
                return
            if kind == "set_flag":
                self.flags[node["flag"]] = node["value"]
                target = node["next"]
            elif kind == "effects":
                for effect in node["effects"]:
                    self.apply(effect)
                target = node["next"]
            else:  # condition
                target = node["then"] if self.holds(node["when"]) else node["else"]
            if target == "end":
                self.dialogue = None
                return
            self.dialogue = (self.dialogue[0], target)
        self.dialogue = None  # runaway graph: close it

    def visible_choices(self) -> list[dict]:
        node = self._node()
        return [c for c in node["choices"] if "when" not in c or self.holds(c["when"])]

    def advance(self) -> None:
        if self.dialogue is not None and self._node()["type"] == "say":
            self._go(self._node()["next"])

    def choose(self, index: int) -> None:
        if self.dialogue is None or self._node()["type"] != "choice":
            return
        choices = self.visible_choices()
        if index < 0 or index >= len(choices):
            return
        choice = choices[index]
        for effect in choice.get("effects", []):
            self.apply(effect)
        self._go(choice["next"])

    def interact(self) -> None:
        if self.dialogue is not None:
            self.advance()
            return
        best = None
        best_dist = INTERACT_RANGE
        for npc in self.npcs:
            d = math.sqrt((npc["pos"][0] - self.host.x) ** 2 + (npc["pos"][1] - self.host.y) ** 2)
            if d <= best_dist and (best is None or d < best_dist):
                best, best_dist = npc, d
        if best is not None:
            self.on_talk(best["key"])
            self.start_dialogue(best["dialogue"])

    # ------------------------------------------------------------------------------------ view

    def dialogue_view(self) -> dict | None:
        if self.dialogue is None:
            return None
        node = self._node()
        if node["type"] == "say":
            return {"type": "say", "speaker": node["speaker"], "text": node["text"]}
        return {"type": "choice", "choices": [c["text"] for c in self.visible_choices()]}

    def snapshot(self) -> dict:
        return {
            "flags": {k: self.flags[k] for k in sorted(self.flags)},
            "gold": self.gold,
            "quests": {k: {"stage": v["stage"], "done": v["done"], "progress": list(v["progress"])}
                       for k, v in sorted(self.quests.items())},
            "dialogue": self.dialogue_view(),
        }
