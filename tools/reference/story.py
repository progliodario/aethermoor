"""Quests, dialogue, conditions and effects v1 (docs/spec/07-quests-and-dialogue.md). Integer rules.

`Story` works on top of a host (`CombatSim`) that owns the inventory, the XP/level machinery and the player position.
"""
from __future__ import annotations

import math

INTERACT_RANGE = 1.5
NPC_RADIUS = 0.3
MAX_SETTLE_STEPS = 64


def isqrt(v: int) -> int:
    """The integer square root, rounded down (spec 07, "Travellers walk")."""
    return math.isqrt(v)


def div_trunc(a: int, b: int) -> int:
    """a / b rounded toward zero, as C++ and Kotlin divide."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def traveller_position(route: list, walk: dict | None, day: int, tick: int, day_ticks: int) -> list[float]:
    """Where a traveller is (spec 07, "Travellers walk"): at its stop of the day, or on the way in or out of it."""
    n = len(route)
    s = (day - 1) % n
    stop = list(route[s])  # where it stands, as the data gives it
    here = [math.floor(stop[0] * 256 + 0.5), math.floor(stop[1] * 256 + 0.5)]
    speed = (walk or {}).get("speed_x256", 0)
    walked = 0
    other = here
    if speed > 0 and day_ticks > 0 and n > 1:
        arrive = day_ticks * walk["arrive_pm"] // 1000
        depart = day_ticks * walk["depart_pm"] // 1000
        if tick < arrive:  # still on its way in, from the stop of the day before
            prev = route[(s - 1) % n]
            other, walked = [math.floor(prev[0] * 256 + 0.5), math.floor(prev[1] * 256 + 0.5)], speed * (arrive - tick)
        elif tick >= depart:  # on its way out, toward the stop of the day after
            nxt = route[(s + 1) % n]
            other, walked = [math.floor(nxt[0] * 256 + 0.5), math.floor(nxt[1] * 256 + 0.5)], speed * (tick - depart)
    dx, dy = other[0] - here[0], other[1] - here[1]
    length = isqrt(dx * dx + dy * dy)
    if walked <= 0 or length == 0:
        return stop
    w = min(walked, length // 2)
    return [(here[0] + div_trunc(dx * w, length)) / 256, (here[1] + div_trunc(dy * w, length)) / 256]


class Story:
    def __init__(self, host, setup: dict) -> None:
        self.host = host
        self.quest_defs: dict[str, dict] = setup["quests"]
        self.dialogues: dict[str, dict] = setup["dialogues"]
        self.npcs: list[dict] = setup["npcs"]
        self.flags: dict[str, bool] = {}
        self.gold = 0
        self.guild_points = 0
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
        if key == "quest_active":  # an expired timed quest is not active any more (spec 07, "Timed quests")
            return value in self.quests and not self.quests[value]["done"] and not self.expired(value)
        if key == "quest_done":
            return value in self.quests and self.quests[value]["done"]
        if key == "quest_stage":
            q = self.quests.get(value["quest"])
            return q is not None and not q["done"] and not self.expired(value["quest"]) and q["stage"] == value["stage"]
        if key == "has_item":
            return self.host.inventory.get(value["item"], 0) >= value["qty"]
        if key == "level_at_least":
            return self.host.level >= value
        if key == "gold_at_least":
            return self.gold >= value
        if key == "season":
            return self.host.season_id() == value
        if key == "tod_between":
            start, end = value
            tod = self.host.tod_pm()
            return start <= tod < end if start <= end else tod >= start or tod < end
        if key == "day_mod":  # a day of a cycle (spec 07): (day - 1) % every == at
            return (self.host.day() - 1) % value["every"] == value["at"]
        if key == "faction_at_least":  # the standing with a faction (spec 07, "Factions")
            return getattr(self.host, "counters", {}).get("faction:" + value["faction"], 0) >= value["count"]
        if key == "renown_at_least":
            return getattr(self.host, "renown_here", lambda: 0)() >= value  # a host without regions has no renown
        raise ValueError(f"unknown condition {key}")

    # --------------------------------------------------------------------------------- effects

    def apply(self, effect: dict) -> None:
        kind = effect["effect"]
        if kind == "add_xp":
            self.host.grant_xp(effect["amount"])
        elif kind == "add_gold":
            self.gold += effect["amount"]
        elif kind == "add_guild_points":
            self.guild_points += effect["amount"]
        elif kind == "open_shop":
            if effect.get("region"):  # the goods of another region (spec 06, "Goods from afar")
                self.host.open_shop(effect["region"], effect.get("markup_pct", 100))
            else:
                self.host.open_shop()
        elif kind == "open_board":
            self.host.open_board()
        elif kind == "add_item":
            self.host.inventory[effect["item"]] = self.host.inventory.get(effect["item"], 0) + effect["qty"]
            self._refresh_all()
        elif kind == "spend_gold":
            self.gold = max(0, self.gold - effect["amount"])
        elif kind == "heal_full":
            self.host.heal_full()
        elif kind == "temper":  # the smith tempers a worn piece for gold (spec 06, "Tempering"; spec 07): paid only when it is done
            cost = effect.get("gold", 0)
            if self.gold >= cost and getattr(self.host, "temper_worn", lambda: False)():
                self.gold -= cost
        elif kind == "remove_item":
            held = self.host.inventory.get(effect["item"], 0)
            left = held - min(held, effect["qty"])
            if left > 0:
                self.host.inventory[effect["item"]] = left
            else:
                self.host.inventory.pop(effect["item"], None)
            self._refresh_all()
        elif kind == "set_flag":
            self.flags[effect["flag"]] = effect["value"]
        elif kind == "recruit_companion":  # a companion joins the party (spec 10, "The party")
            getattr(self.host, "recruit_companion", lambda _cid: False)(effect["companion"])
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

    def expired(self, quest_id: str) -> bool:
        """A timed quest whose days are over (spec 07, "Timed quests"): `time_limit_days` of its definition, counted from the day it was
        started (`day`); it is not done, it does not count anything more and it can be started again."""
        q = self.quests.get(quest_id)
        limit = self.quest_defs.get(quest_id, {}).get("time_limit_days", 0)
        return q is not None and not q["done"] and limit > 0 and q.get("day", 0) > 0 and self.host.day() >= q["day"] + limit

    def days_left(self, quest_id: str) -> int:
        """The days a timed quest still has, today included; 0 for a quest without a limit or an expired one."""
        q = self.quests.get(quest_id)
        limit = self.quest_defs.get(quest_id, {}).get("time_limit_days", 0)
        if q is None or q["done"] or limit <= 0 or q.get("day", 0) <= 0:
            return 0
        return max(0, q["day"] + limit - self.host.day())

    def start_quest(self, quest_id: str) -> None:
        # a quest that exists is not started again, unless it is done and `repeatable` (spec 07, "Quests"), or a timed quest whose days
        # are over (spec 07, "Timed quests"): then it starts anew
        if quest_id in self.quests and not (self.quests[quest_id]["done"] and self.quest_defs.get(quest_id, {}).get("repeatable", False)) \
                and not self.expired(quest_id):
            return
        stage = self.quest_defs[quest_id]["stages"][0]
        self.quests[quest_id] = {"stage": stage["id"], "progress": [0] * len(stage["objectives"]), "done": False}
        if self.quest_defs[quest_id].get("time_limit_days", 0) > 0:  # the day it starts: the days are counted from it
            self.quests[quest_id]["day"] = self.host.day()
        self._refresh(quest_id)

    def _refresh_all(self) -> None:
        for quest_id in sorted(self.quests):
            self._refresh(quest_id)

    def _refresh(self, quest_id: str) -> None:
        """Updates collect objectives, then advances stages while the current one is complete."""
        while True:
            q = self.quests[quest_id]
            if q["done"] or self.expired(quest_id):
                return
            stage = self._stage(quest_id)
            for i, objective in enumerate(stage["objectives"]):
                if objective["type"] == "collect":
                    q["progress"][i] = min(objective["count"], self.host.inventory.get(objective["item"], 0))
            if not all(q["progress"][i] >= self._required(o) for i, o in enumerate(stage["objectives"])):
                return
            if stage["next"] == "end":
                q["done"] = True
                done = getattr(self.host, "quest_done", None)  # the renown of the region grows (spec 07, "Renown")
                if done is not None:
                    done(quest_id)
                for reward in self.quest_defs[quest_id].get("rewards", []):
                    self.apply(reward)
                return
            nxt = next(s for s in self.quest_defs[quest_id]["stages"] if s["id"] == stage["next"])
            q["stage"] = nxt["id"]
            q["progress"] = [0] * len(nxt["objectives"])

    def on_kill(self, enemy_id: str) -> None:
        for quest_id in sorted(self.quests):
            q = self.quests[quest_id]
            if q["done"] or self.expired(quest_id):
                continue
            for i, o in enumerate(self._stage(quest_id)["objectives"]):
                if o["type"] == "kill" and o["enemy"] == enemy_id:
                    q["progress"][i] = min(o["count"], q["progress"][i] + 1)
        self._refresh_all()

    def on_talk(self, npc_key: str) -> None:
        for quest_id in sorted(self.quests):
            q = self.quests[quest_id]
            if q["done"] or self.expired(quest_id):
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

    def move_travellers(self, day: int, tick: int = 0, day_ticks: int = 0) -> None:
        """Puts every traveller (an NPC with `route`) where its route says for that day and tick of the day (spec 07, "Travellers",
        "Travellers walk")."""
        for npc in self.npcs:
            route = npc.get("route")
            if route:
                npc["pos"] = traveller_position(route, npc.get("walk"), day, tick, day_ticks)

    def npc_present(self, npc: dict) -> bool:
        """Whether an NPC is there now: always, or while the condition of a resident holds (spec 07, "Residents")."""
        return "when" not in npc or self.holds(npc["when"])

    def interact(self) -> None:
        if self.dialogue is not None:
            self.advance()
            return
        best = None
        best_dist = INTERACT_RANGE
        for npc in self.npcs:
            if not self.npc_present(npc):  # a resident that has not come yet (spec 07, "Residents")
                continue
            d = math.sqrt((npc["pos"][0] - self.host.x) ** 2 + (npc["pos"][1] - self.host.y) ** 2)
            if d <= best_dist and (best is None or d < best_dist):
                best, best_dist = npc, d
        if best is not None:
            self.on_talk(best["key"])
            self.start_dialogue(best["dialogue"])

    # ----------------------------------------------------------------------------------- saves

    def save_state(self) -> dict:
        return {
            "flags": {k: self.flags[k] for k in sorted(self.flags)},
            "gold": self.gold,
            "guild_points": self.guild_points,
            "quests": {k: {"stage": v["stage"], "progress": list(v["progress"]), "done": v["done"], **({"day": v["day"]} if v.get("day") else {})}
                       for k, v in sorted(self.quests.items())},
            "dialogue": None if self.dialogue is None else {"id": self.dialogue[0], "node": self.dialogue[1]},
        }

    def load_state(self, state: dict) -> None:
        self.flags = dict(state["flags"])
        self.gold = state["gold"]
        self.guild_points = state.get("guild_points", 0)
        self.quests = {k: {"stage": v["stage"], "progress": list(v["progress"]), "done": v["done"], **({"day": v["day"]} if v.get("day") else {})}
                       for k, v in state["quests"].items()}
        d = state["dialogue"]
        self.dialogue = None if d is None else (d["id"], d["node"])

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
            "guild_points": self.guild_points,
            "quests": {k: {"stage": v["stage"], "done": v["done"], "progress": list(v["progress"])}
                       for k, v in sorted(self.quests.items())},
            "dialogue": self.dialogue_view(),
            # where the travellers are (spec 07, "Travellers walk"), when the story has some
            **({"travellers": [list(n["pos"]) for n in self.npcs if n.get("route")]} if any(n.get("route") for n in self.npcs) else {}),
        }
