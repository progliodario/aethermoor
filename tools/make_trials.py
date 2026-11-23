#!/usr/bin/env python3
"""Writes the trials of the seasons of the guild (spec 07, "Trials of the seasons"): a timed quest for every season, for the Guest who has
done everything.

The clerk of the guild in every town (one more pair of choices of the role dialogue `guild_clerk_<tone>`, after the standing bounty) offers,
on a day of the season and from level 25, `base:quest/side/bounty_trial_<season>`: defeat two great creatures of two far regions within
three days (`time_limit_days`, spec 07, "Timed quests"). It is `repeatable`, for the Guild (the prefix `bounty_` of `set_factions.py`), and
pays experience, gold, guild points and a rare piece with two affixes, one for each season. A trial that is over is offered again at once.

It changes the role dialogues in place (the nodes written here are written again and the choices keep their place, so it can be run any
number of times) and writes the quests and their texts (it and en). Then run `set_quest_places.py`, `make_catalog.py` and `make_facts.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

TONES = ("warm", "mystic", "gruff", "flowery", "stoic", "salty", "grim", "scholarly")
LEVEL = 25
DAYS = 3
# season: (the two great creatures, the rare piece of the prize)
TRIALS = {
    "spring": (("gel_king", "coral_matron"), "claymore_vigor_might"),
    "summer": (("sand_sentinel", "magma_heart"), "knight_plate_vigor_keenness"),
    "autumn": (("moonshade_alpha", "forge_tyrant"), "claymore_keenness_leech"),
    "winter": (("ice_warden", "storm_sovereign"), "knight_plate_vigor_might"),
}
SEASON_NAMES = {"en": {"spring": "Spring", "summer": "Summer", "autumn": "Autumn", "winter": "Winter"},
                "it": {"spring": "della primavera", "summer": "dell'estate", "autumn": "dell'autunno", "winter": "dell'inverno"}}
WORDS = {
    "en": {"ask": "Is there a trial for this season?", "status": "About the trial of the season...",
           "offer": "For the strongest only: the trial of the {season}. {first} and {second}, both of them, within three days. "
                    "The guild pays well, and there is a piece in the vault that waits for whoever does it.",
           "busy": "The trial is running: {first} and {second}, and the days are counted. The stones will take you there faster than any horse.",
           "name": "Trial of {season}: {first} and {second}",
           "task": "The trial of the guild: defeat {first} and {second} within three days. If the days run out, the clerk gives it again."},
    "it": {"ask": "C'è una prova per questa stagione?", "status": "A proposito della prova della stagione...",
           "offer": "Solo per i più forti: la prova {season}. {first} e {second}, tutti e due, entro tre giorni. "
                    "La gilda paga bene, e nella cassaforte c'è un pezzo che aspetta chi ci riesce.",
           "busy": "La prova è in corso: {first} e {second}, e i giorni si contano. Le pietre ti ci portano prima di qualsiasi cavallo.",
           "name": "Prova {season}: {first} e {second}",
           "task": "La prova della gilda: sconfiggi {first} e {second} entro tre giorni. Se i giorni finiscono, l'impiegato la ridà."},
}
EN_SEASON_IN_OFFER = {"spring": "spring", "summer": "summer", "autumn": "autumn", "winter": "winter"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def quest_id(season: str) -> str:
    return f"base:quest/side/bounty_trial_{season}"


def patch_clerk(tone: str) -> None:
    path = DATA / "dialogues" / "role" / f"guild_clerk_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    mine = {f"trial_{s}_{part}" for s in TRIALS for part in ("offer", "busy")}
    old = nodes["menu"]["choices"]
    choices = [c for c in old if c.get("next") not in mine]
    # after the standing bounty (spec 07, "Standing bounties"), or at the place they had
    where = next((i for i, c in enumerate(old) if c.get("next") in mine), None)
    if where is None:
        where = max((i + 1 for i, c in enumerate(choices) if c.get("next") in ("standing_offer", "standing_busy")), default=2)
    added = []
    for season in TRIALS:
        q = quest_id(season)
        added.append({"text": "$i18n:dlg.role.trial.ask", "when": {"all": [{"season": season}, {"level_at_least": LEVEL}, {"not": {"quest_active": q}}]},
                      "next": f"trial_{season}_offer"})
        added.append({"text": "$i18n:dlg.role.trial.status", "when": {"quest_active": q}, "next": f"trial_{season}_busy"})
    nodes["menu"]["choices"] = choices[:where] + added + choices[where:]
    for season in TRIALS:
        nodes[f"trial_{season}_offer"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.trial.{season}.offer", "next": f"trial_{season}_choice"}
        nodes[f"trial_{season}_choice"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.wayfarer.accept", "effects": [{"effect": "start_quest", "quest": quest_id(season)}], "next": "end"},
            {"text": "$i18n:dlg.wayfarer.later", "next": "menu"}]}
        nodes[f"trial_{season}_busy"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.trial.{season}.busy", "next": "end"}
    newline = "\r\n" if "\r\n" in raw else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def write_quest(season: str, guardians: tuple[str, str], prize: str) -> None:
    qid = f"bounty_trial_{season}"
    quests = DATA / "quests" / "side"
    old = quests / f"{qid}.json"
    stages = [{"id": "trial", "journal": f"$i18n:quest.{qid}.task",
               "objectives": [{"type": "kill", "enemy": f"base:enemy/{g}", "count": 1} for g in guardians], "next": "end"}]
    if old.exists():  # the place set by set_quest_places.py stays
        place = load(old)["stages"][0].get("place")
        if place:
            stages[0]["place"] = place
    quest = {"$schema": "../../../../schemas/quest.schema.json", "id": f"base:quest/side/{qid}", "name": f"$i18n:quest.{qid}.name",
             "kind": "side", "faction": "guild", "repeatable": True, "time_limit_days": DAYS, "stages": stages,
             "rewards": [{"effect": "add_xp", "amount": 6000}, {"effect": "add_gold", "amount": 5000},
                         {"effect": "add_guild_points", "amount": 60}, {"effect": "add_item", "item": f"base:item/{prize}", "qty": 1}]}
    old.write_text(json.dumps(quest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    for tone in TONES:
        patch_clerk(tone)
    roles = {lang: {"dlg.role.trial.ask": WORDS[lang]["ask"], "dlg.role.trial.status": WORDS[lang]["status"]} for lang in ("en", "it")}
    content: dict[str, dict[str, str]] = {"en": {}, "it": {}}
    for season, (guardians, prize) in TRIALS.items():
        for name in (*guardians, prize):
            assert (DATA / ("enemies" if name in guardians else "items") / f"{name}.json").exists(), name
        write_quest(season, guardians, prize)
        qid = f"bounty_trial_{season}"
        for lang in ("en", "it"):
            texts = load(DATA / "i18n" / lang / "content.json")
            names = {"first": texts[f"enemy.{guardians[0]}.name"], "second": texts[f"enemy.{guardians[1]}.name"]}
            w = WORDS[lang]
            offer_season = EN_SEASON_IN_OFFER[season] if lang == "en" else SEASON_NAMES[lang][season]
            roles[lang].update({f"dlg.trial.{season}.offer": w["offer"].format(season=offer_season, **names),
                                f"dlg.trial.{season}.busy": w["busy"].format(**names)})
            content[lang].update({f"quest.{qid}.name": w["name"].format(season=SEASON_NAMES[lang][season], **names),
                                  f"quest.{qid}.task": w["task"].format(**names)})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, roles[lang])
        set_texts("content.json", lang, content[lang])
    print(f"wrote the trials of {len(TRIALS)} seasons, offered by the clerks of {len(TONES)} regions")


if __name__ == "__main__":
    main()
