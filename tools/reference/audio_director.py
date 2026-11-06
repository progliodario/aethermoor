"""Reference sound director (spec 14, "What plays when"): from a snapshot of the game each frame, the sound events to play.

The director is presentation logic with no randomness: the same snapshots give the same events in every client.
"""
from __future__ import annotations

import math

STRIDE_TILES = 0.85  # a step every so many tiles walked
HEARTBEAT_FRAMES = 70
THUNDER_PERIOD = 1200
THUNDER_AT = 600
MIN_AUDIBLE_PM = 60
FALLOFF_PM_PER_TILE = 70
PANELS = ("bag", "map", "journal", "shop", "board", "travel")


class Director:
    def __init__(self) -> None:
        self.prev: dict | None = None
        self.walked = 0.0
        self.since_heartbeat = HEARTBEAT_FRAMES

    def update(self, s: dict) -> list[dict]:
        """One frame. `s` is the snapshot (see docs/spec/14-audio.md); the result is a list of {"event", "volume_pm"}."""
        out: list[dict] = []

        def emit(event: str, volume: int = 1000) -> None:
            out.append({"event": event, "volume_pm": volume})

        p = s["player"]
        prev = self.prev
        # --- what the creatures did this frame (cues from the simulation)
        for cue in s["cues"]:
            dist = math.hypot(cue["x"] - p["x"], cue["y"] - p["y"])
            volume = max(0, min(1000, 1000 - math.floor(dist * FALLOFF_PM_PER_TILE + 0.5)))
            kind = cue["kind"]
            if kind == "hurt":
                emit("player.hurt")
            elif volume >= MIN_AUDIBLE_PM:
                emit(f"enemy.{cue['family']}.{kind}", volume)
            if kind == "hit":
                if cue.get("crit"):
                    emit("crit")
                if cue.get("weak"):
                    emit("weak")
        if prev is not None:
            pp = prev["player"]
            # --- the player
            if p["phase"] != 0 and pp["phase"] == 0:
                emit("power" if p["strike"] else "swing")
            if p["dodge"] and not pp["dodge"]:
                emit("dodge")
            if p["level"] > pp["level"]:
                emit("level_up")
            if p["hp"] <= 0 < pp["hp"]:
                emit("player.death")
            if p["save_cd"] > pp["save_cd"]:
                emit("death_save")
            # footsteps: one per stride walked, in the sound of the ground under the feet
            if p["moving"]:
                self.walked += math.hypot(p["x"] - pp["x"], p["y"] - pp["y"])
                if self.walked >= STRIDE_TILES:
                    self.walked -= STRIDE_TILES
                    emit(f"step.{p['surface']}", 700)
            else:
                self.walked = 0.0
            # a heartbeat while badly hurt
            if p["hp"] > 0 and p["hp"] * 4 < p["max_hp"]:
                self.since_heartbeat += 1
                if self.since_heartbeat >= HEARTBEAT_FRAMES:
                    self.since_heartbeat = 0
                    emit("heartbeat", 800)
            else:
                self.since_heartbeat = HEARTBEAT_FRAMES
            # --- the bag
            d_items = s["items"] - prev["items"]
            d_gold = s["gold"] - prev["gold"]
            d_hp = p["hp"] - pp["hp"]
            shop = s["panels"]["shop"]
            if d_gold > 0 and d_items < 0 and shop:
                emit("shop.sell")
            elif d_gold < 0 and d_items > 0:
                emit("shop.buy")
            elif d_gold > 0:
                emit("coin")
            elif d_items > 0:
                emit("pickup")
            elif d_items < 0 and d_hp > 0:
                emit("use.heal")
            elif d_items < 0 and s["mp"] > prev["mp"]:
                emit("use.mana")
            elif d_items < 0 and not shop:
                emit("use.other")
            if s["weapon"] != prev["weapon"]:
                emit("equip.weapon")
            if s["armor"] != prev["armor"]:
                emit("equip.armor")
            # --- panels, the cursor, the dialogue
            for name in PANELS:
                if s["panels"][name] != prev["panels"][name]:
                    emit(f"ui.{'open' if s['panels'][name] else 'close'}.{name}")
            if s["dialogue"] != prev["dialogue"]:
                emit("dialogue.open" if s["dialogue"] else "dialogue.close")
            elif s["dialogue"] and s["line"] != prev["line"]:
                emit("dialogue.next")
            if s["cursor"] != prev["cursor"] and (s["dialogue"] or any(s["panels"].values())):
                emit("ui.move")
            # --- the story and the world
            if s["quests_started"] > prev["quests_started"]:
                emit("quest.accept")
            if s["quests_done"] > prev["quests_done"]:
                emit("quest.complete")
            if s["stones"] > prev["stones"]:
                emit("stone.wake")
            if s["region"] != prev["region"]:
                emit("region.enter")
            if prev["rain_pm"] == 0 < s["rain_pm"]:
                emit("rain.start")
            elif s["rain_pm"] == 0 < prev["rain_pm"]:
                emit("rain.stop")
            if s["rain_pm"] >= 700 and s["frame"] % THUNDER_PERIOD == THUNDER_AT:
                emit("thunder")
            if prev["tod_pm"] < 250 <= s["tod_pm"]:
                emit("dawn")
            if prev["tod_pm"] < 750 <= s["tod_pm"]:
                emit("nightfall")
        self.prev = s
        return out


def ambience(region: str, tod_pm: int, rain_pm: int, rules: dict) -> dict[str, int]:
    """The gain (permille) of every looping sound for a place and a moment. `rules` is the `ambience` section of events.json."""
    gains: dict[str, int] = {}
    day = 250 <= tod_pm <= 750
    for entry in rules["regions"].get(region, []):
        when = entry.get("when", "always")
        if (when == "day" and not day) or (when == "night" and day):
            continue
        gains[entry["sound"]] = max(gains.get(entry["sound"], 0), entry["gain_pm"])
    if rain_pm > 0:
        gains[rules["rain"]["light"]] = min(1000, rain_pm)
        heavy = max(0, rain_pm - 500) * 2
        if heavy > 0:
            gains[rules["rain"]["heavy"]] = min(1000, heavy)
        for sound in list(gains):  # the birds and the crickets stop when it rains
            if sound in rules["rain"].get("silences", []):
                gains[sound] = 0
    return {k: v for k, v in gains.items() if v > 0}
