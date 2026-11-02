"""The guild: ranks, the board of a settlement and its generated quests (docs/spec/07-quests-and-dialogue.md, "Guild").

Integer arithmetic only. The board is a pure function of (seed, settlement, day); a generated quest is rebuilt from its id.
"""
from __future__ import annotations

from .numerics import hash64
from .worldgen import Sites


def rank_index(guild: dict, points: int) -> int:
    """Index of the rank (0 = the first) of a guild member with that many guild points."""
    index = 0
    for i, rank in enumerate(guild["ranks"]):
        if points >= rank["points"]:
            index = i
    return index


def offer_id(sx: int, sy: int, day: int, slot: int) -> str:
    return f"board:{sx}:{sy}:{day}:{slot}"


def offers(seed: int, params: dict, sx: int, sy: int, day: int) -> list[dict]:
    """The offers on the board of the settlement of site cell (sx, sy) on a day (empty when the cell has no settlement)."""
    site = Sites(seed, params).site(sx, sy)
    if site is None:
        return []
    return offers_for(seed, params, site, day)


def offers_for(seed: int, params: dict, site: dict, day: int) -> list[dict]:
    guild = params["guild"]
    templates = guild["templates"]
    result = []
    for slot in range(guild["offers_per_day"]):
        h = hash64(hash64(seed, site["sx"], site["sy"], 200 + slot), day, slot)
        template = templates[(h >> 16) % len(templates)]
        span = template["count_max"] - template["count_min"] + 1
        count = template["count_min"] + (h >> 32) % span
        tier = slot + 1
        result.append({
            "id": offer_id(site["sx"], site["sy"], day, slot),
            "slot": slot,
            "min_rank": min(slot, len(guild["ranks"]) - 1),
            "template": template["id"],
            "type": template["type"],
            "target": template["target"],
            "count": count,
            "gold": (template["gold_base"] + count * template["gold_per"]) * tier,
            "xp": (template["xp_base"] + count * template["xp_per"]) * tier,
            "points": (template["points_base"] + count * template["points_per"]) * tier,
            "place": site["name"],
            "tone": params["regions"][site["region"]]["tone"],
        })
    return result


def quest_def(offer: dict) -> dict:
    """The quest document of an offer: one stage, with the arguments of its texts (spec 07)."""
    tone = offer["tone"]
    objective = ({"type": "kill", "enemy": offer["target"], "count": offer["count"]} if offer["type"] == "kill"
                 else {"type": "collect", "item": offer["target"], "count": offer["count"]})
    target_key = offer["target"].split(":", 1)[1].replace("/", ".") + ".name"
    return {
        "id": offer["id"],
        "name": f"$i18n:quest.board.{offer['template']}.{tone}.name",
        "kind": "guild",
        "args": {"count": str(offer["count"]), "target": f"$i18n:{target_key}", "place": offer["place"]},
        "stages": [{"id": "work", "journal": f"$i18n:quest.board.{offer['template']}.{tone}.journal",
                    "objectives": [objective], "next": "end"}],
        "rewards": [{"effect": "add_xp", "amount": offer["xp"]}, {"effect": "add_gold", "amount": offer["gold"]},
                    {"effect": "add_guild_points", "amount": offer["points"]}],
    }


def parse_offer_id(quest_id: str) -> tuple[int, int, int, int] | None:
    parts = quest_id.split(":")
    if len(parts) != 5 or parts[0] != "board":
        return None
    try:
        return int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
    except ValueError:
        return None


def resolve_quest(seed: int, params: dict, quest_id: str) -> dict | None:
    """Rebuilds the quest document of a generated quest from its id (used when a save is loaded)."""
    parsed = parse_offer_id(quest_id)
    if parsed is None:
        return None
    sx, sy, day, slot = parsed
    for offer in offers(seed, params, sx, sy, day):
        if offer["slot"] == slot:
            return quest_def(offer)
    return None
