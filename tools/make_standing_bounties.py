#!/usr/bin/env python3
"""Writes the standing bounties of the guild (spec 07, "Guild"): a bounty on the great creature of every region that never closes.

The clerk of the guild in every town of a region offers it (one more choice of the role dialogue `guild_clerk_<tone>`, after the board):
`base:quest/side/bounty_standing_<region>`, a `repeatable` quest (spec 07, "Quests") on the guardian of a lair of the region, which comes
back as every creature does (spec 08, "Respawn"). It is offered while it is not active and pays every time: experience, gold and guild
points that grow with the danger of the region. They count for the Guild (`set_factions.py`, the prefix `bounty_`).

It changes the role dialogues in place (the choices keep their place, so it can be run any number of times) and writes the quests and
their texts (it and en). Then run `set_quest_places.py`, `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

# region: (tone, danger, the guardian)
REGIONS = {
    "verdalis": ("warm", 1, "gel_king"), "whisperwood": ("mystic", 3, "moonshade_alpha"), "ironspine": ("gruff", 4, "forge_tyrant"),
    "sunscar": ("flowery", 4, "sand_sentinel"), "frostveil": ("stoic", 5, "ice_warden"), "tidehaven": ("salty", 3, "coral_matron"),
    "ashen_wastes": ("grim", 7, "magma_heart"), "lumeria": ("scholarly", 5, "storm_sovereign"),
}
WORDS = {
    "en": {"ask": "Is there a standing bounty?", "status": "About the standing bounty...",
           "offer": "The guild keeps a standing bounty: {guardian}. It always comes back, and somebody always has to send it away again. Paid every time.",
           "busy": "The bounty is still open: {guardian} is out there. The guild pays when it falls.",
           "name": "Standing Bounty: {guardian}", "task": "Standing bounty of the guild in {region}: {guardian}. Defeat it; it will come back, and so can you."},
    "it": {"ask": "C'è una taglia permanente?", "status": "A proposito della taglia permanente...",
           "offer": "La gilda tiene una taglia permanente: {guardian}. Torna sempre, e qualcuno deve sempre rimandarlo via. Pagata ogni volta.",
           "busy": "La taglia è ancora aperta: {guardian} è là fuori. La gilda paga quando cade.",
           "name": "Taglia permanente: {guardian}", "task": "Taglia permanente della gilda a {region}: {guardian}. Sconfiggilo; tornerà, e potrai farlo anche tu."},
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def patch_clerk(region: str, tone: str) -> None:
    path = DATA / "dialogues" / "role" / f"guild_clerk_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    q = f"base:quest/side/bounty_standing_{region}"
    mine = ("standing_offer", "standing_busy")
    old = nodes["menu"]["choices"]
    where = next((i for i, c in enumerate(old) if c.get("next") in mine), 2)  # after the board (the clients' tests open it with the first choice)
    choices = [c for c in old if c.get("next") not in mine]
    added = [{"text": "$i18n:dlg.role.standing.ask", "when": {"not": {"quest_active": q}}, "next": "standing_offer"},
             {"text": "$i18n:dlg.role.standing.status", "when": {"quest_active": q}, "next": "standing_busy"}]
    nodes["menu"]["choices"] = choices[:where] + added + choices[where:]
    nodes["standing_offer"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.standing.{region}.offer", "next": "standing_choice"}
    nodes["standing_choice"] = {"type": "choice", "choices": [
        {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": q}], "next": "end"},
        {"text": "$i18n:dlg.wayfarer.later", "next": "menu"}]}
    nodes["standing_busy"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.standing.{region}.busy", "next": "end"}
    newline = "\r\n" if "\r\n" in raw else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def main() -> None:
    roles = {lang: {"dlg.role.standing.ask": WORDS[lang]["ask"], "dlg.role.standing.status": WORDS[lang]["status"]} for lang in ("en", "it")}
    content: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for region, (tone, danger, guardian) in REGIONS.items():
        patch_clerk(region, tone)
        qid = f"bounty_standing_{region}"
        quest = {"$schema": "../../../../schemas/quest.schema.json", "id": f"base:quest/side/{qid}", "name": f"$i18n:quest.{qid}.name",
                 "kind": "side", "faction": "guild", "repeatable": True,
                 "stages": [{"id": "hunt", "journal": f"$i18n:quest.{qid}.task",
                             "objectives": [{"type": "kill", "enemy": f"base:enemy/{guardian}", "count": 1}], "next": "end"}],
                 "rewards": [{"effect": "add_xp", "amount": 500 * danger}, {"effect": "add_gold", "amount": 400 * danger},
                             {"effect": "add_guild_points", "amount": 10 * danger}]}
        (DATA / "quests" / "side" / f"{qid}.json").write_text(json.dumps(quest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        for lang in ("en", "it"):
            texts = load(DATA / "i18n" / lang / "content.json")
            names = {"guardian": texts[f"enemy.{guardian}.name"], "region": texts[f"region.{region}.name"]}
            w = WORDS[lang]
            roles[lang].update({f"dlg.standing.{region}.offer": w["offer"].format(**names), f"dlg.standing.{region}.busy": w["busy"].format(**names)})
            content[lang].update({f"quest.{qid}.name": w["name"].format(**names), f"quest.{qid}.task": w["task"].format(**names)})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, roles[lang])
        set_texts("content.json", lang, content[lang])
    print(f"wrote the standing bounties of {len(REGIONS)} regions")


if __name__ == "__main__":
    main()
