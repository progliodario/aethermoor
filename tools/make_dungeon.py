#!/usr/bin/env python3
"""Writes Gideon's Dungeon (spec 18, "Gideon's Dungeon"): the defense (`data/base/defense.json`), its adventurers (four creatures and
their two behaviors), Grubb, Gideon's steward, who arms the traps and opens the gates (his dialogue, his texts, his line in `npcs`), the
landmark `gideon_dungeon` in the world data, and the texts of the interface of the defense (it and en).

The positions of the defense are read from the stamp `base:stamp/gideon_dungeon` (`tools/make_stamps.py`): the core is `3`, the gate `4`,
the spikes `1` and the tar `2`, from the centre of the world through the landmark and the anchor of the stamp. It can be run any number of
times. Run `make_stamps.py` first, then `make_titles.py` (the Lord of the Dungeon), `gen_conformance.py` and `make_catalog.py`.
"""
from __future__ import annotations

import json
import re

from make_towns import DATA, set_texts

WORLD = DATA / "worlds" / "overworld.json"
LANDMARK = {"id": "gideon_dungeon", "name": "Gideon's Dungeon", "stamp": "base:stamp/gideon_dungeon", "kind": "dungeon", "dx": 896, "dy": 384}
STEWARD = ("dungeon_steward_grubb", "grubb", "teal", (4, 2))  # key, dialogue, look, the tile of the stamp he stands on
WAVE_TICKS = 3600
# the adventurers: name, art, level, hp, atk, def, mdef, speed, xp, behavior, en, it
ADVENTURERS = {
    "warrior": ("hollow_armor", 22, 420, 40, 22, 10, 210, 320, "adventurer", "Adventurer warrior", "Avventuriero guerriero"),
    "archer": ("rust_baron", 22, 300, 44, 14, 12, 230, 320, "adventurer_archer", "Adventurer archer", "Avventuriera arciera"),
    "cleric": ("vault_warden", 22, 340, 30, 18, 30, 200, 340, "adventurer", "Adventurer cleric", "Avventuriero chierico"),
    "knight": ("iron_foreman", 24, 800, 48, 34, 20, 170, 600, "adventurer", "Adventurer knight", "Avventuriera cavaliera"),
}
BEHAVIORS = {
    "adventurer": {"aggro_x100": 250, "leash_x100": 600, "attack_range_x100": 150, "hit_range_x100": 190, "windup_ticks": 30,
                   "recovery_ticks": 50},
    "adventurer_archer": {"aggro_x100": 400, "leash_x100": 700, "attack_range_x100": 400, "hit_range_x100": 450, "windup_ticks": 40,
                          "recovery_ticks": 60},
}
WAVES = [["warrior", "warrior"], ["warrior", "archer", "warrior"], ["warrior", "warrior", "archer", "cleric"],
         ["warrior", "warrior", "archer", "archer", "cleric"], ["knight", "warrior", "warrior", "archer", "archer", "cleric"]]
TRAP_PRICE = {"dungeon_spikes": ("iron_ore", 10), "dungeon_tar": ("pine_resin", 6)}
REWARD = {"gold": 500, "items": [{"item": "base:item/ember_core", "qty": 2}, {"item": "base:item/iron_ore", "qty": 5}], "counter": "defenses_won"}
WORDS = {
    "en": {"speaker": "Grubb, steward of the Dungeon",
           "waiting": "The Master will come back. They always do, the masters. When he does, the Dungeon will be ready. Mostly ready.",
           "lord": "Master! The adventurers are gathering at the gate again. Heroes, they call themselves. Shall I let them in?",
           "spikes": "Arm the pits of spikes (10 iron ores)", "tar": "Fill the pits of tar (6 pine resins)",
           "open": "Open the gates", "later": "Not now",
           "armed_spikes": "The spikes are sharp and hungry. They will remember every boot.",
           "armed_tar": "The tar is warm and deep. Heroes hate tar. It is very undignified.",
           "opened": "The gates are open! Five waves, Master. If one of them touches the core, they go home happy. Do not let them go home happy.",
           "ui.defense_wave": "Wave {wave} of {waves}: the adventurers come through the gate!",
           "ui.defense_won": "The Dungeon stands! Every wave is beaten.",
           "ui.defense_lost": "An adventurer touched the core: the others leave, laughing. Try again when you like.",
           "ui.defense_hud": "Defense: wave {wave}/{waves}"},
    "it": {"speaker": "Grubb, intendente del Dungeon",
           "waiting": "Il Padrone tornerà. Tornano sempre, i padroni. Quando tornerà, il Dungeon sarà pronto. Più o meno pronto.",
           "lord": "Padrone! Gli avventurieri si radunano di nuovo al cancello. Eroi, si fanno chiamare. Li faccio entrare?",
           "spikes": "Arma le fosse di spuntoni (10 minerali di ferro)", "tar": "Riempi le fosse di catrame (6 resine di pino)",
           "open": "Apri i cancelli", "later": "Non adesso",
           "armed_spikes": "Gli spuntoni sono affilati e affamati. Si ricorderanno di ogni stivale.",
           "armed_tar": "Il catrame è caldo e profondo. Gli eroi odiano il catrame. È molto poco dignitoso.",
           "opened": "I cancelli sono aperti! Cinque ondate, Padrone. Se uno di loro tocca il nucleo, tornano a casa contenti. Non lasciateli tornare contenti.",
           "ui.defense_wave": "Ondata {wave} di {waves}: gli avventurieri entrano dal cancello!",
           "ui.defense_won": "Il Dungeon resiste! Tutte le ondate sono battute.",
           "ui.defense_lost": "Un avventuriero ha toccato il nucleo: gli altri se ne vanno ridendo. Riprova quando vuoi.",
           "ui.defense_hud": "Difesa: ondata {wave}/{waves}"},
}


def write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def stamp_places() -> dict[str, list[list[float]]]:
    """The places of the stamp (`1` spikes, `2` tar, `3` core, `4` gate), as centres of tiles from the centre of the world."""
    stamp = json.loads((DATA / "stamps" / "gideon_dungeon.json").read_text(encoding="utf-8"))
    x0, y0 = LANDMARK["dx"] - stamp["anchor"][0], LANDMARK["dy"] - stamp["anchor"][1]
    places: dict[str, list[list[float]]] = {}
    for j, row in enumerate(stamp["rows"]):
        for i, ch in enumerate(row):
            if ch in "1234":
                places.setdefault(ch, []).append([x0 + i + 0.5, y0 + j + 0.5])
    return places


def say(key: str, nxt: str) -> dict:
    return {"type": "say", "speaker": STEWARD[0], "text": f"$i18n:dlg.grubb.{key}", "next": nxt}


def dialogue() -> dict:
    menu = []
    nodes: dict[str, dict] = {
        "c_lord": {"type": "condition", "when": {"quest_done": "base:quest/side/act6_gideon_3"}, "then": "lord", "else": "waiting"},
        "waiting": say("waiting", "end"),
        "lord": say("lord", "menu"),
        "open": {"type": "effects", "effects": [{"effect": "start_defense"}], "next": "opened"},
        "opened": say("opened", "end"),
    }
    for flag, (item, qty) in TRAP_PRICE.items():
        kind = flag.split("_")[1]
        menu.append({"text": f"$i18n:dlg.grubb.{kind}", "next": f"arm_{kind}",
                     "when": {"all": [{"not": {"flag": flag}}, {"has_item": {"item": f"base:item/{item}", "qty": qty}}]}})
        nodes[f"arm_{kind}"] = {"type": "effects", "effects": [{"effect": "remove_item", "item": f"base:item/{item}", "qty": qty},
                                                               {"effect": "set_flag", "flag": flag, "value": True}], "next": f"armed_{kind}"}
        nodes[f"armed_{kind}"] = say(f"armed_{kind}", "menu")
    menu += [{"text": "$i18n:dlg.grubb.open", "next": "open"}, {"text": "$i18n:dlg.grubb.later", "next": "end"}]
    nodes["menu"] = {"type": "choice", "choices": menu}
    return {"$schema": "../../../../schemas/dialogue.schema.json", "id": f"base:dialogue/npc/{STEWARD[1]}", "start": "c_lord", "nodes": nodes}


def patch_world() -> None:
    """The landmark of the Dungeon and Grubb in the world data, one line each; a second run changes nothing."""
    raw = WORLD.read_text(encoding="utf-8", newline="")
    line = "{ " + ", ".join(f'"{k}": {json.dumps(v)}' for k, v in LANDMARK.items()) + " }"
    if f'"id": "{LANDMARK["id"]}"' in raw:
        raw = re.sub(r'\{ "id": "' + LANDMARK["id"] + r'"[^\n]*?\}', line, raw)
    else:
        last = raw.index('"id": "sanctum_gideon"')
        start = raw.rindex("{", 0, last)
        end = raw.index("}", last) + 1
        indent = raw[raw.rindex("\n", 0, start) + 1:start]
        raw = raw[:end] + ",\n" + indent + line + raw[end:]
    key, file, variant, (sx, sy) = STEWARD
    stamp = json.loads((DATA / "stamps" / "gideon_dungeon.json").read_text(encoding="utf-8"))
    dx, dy = LANDMARK["dx"] - stamp["anchor"][0] + sx, LANDMARK["dy"] - stamp["anchor"][1] + sy
    npc = f'{{ "key": "{key}", "dialogue": "base:dialogue/npc/{file}", "variant": "{variant}", "dx": {dx}, "dy": {dy} }}'
    if f'"key": "{key}"' in raw:
        raw = re.sub(r'\{ "key": "' + key + r'"[^\n]*\}', npc, raw)
    else:
        last = raw.rindex('{ "key": "')
        end = raw.index("}", last) + 1
        indent = raw[raw.rindex("\n", 0, last) + 1:last]
        raw = raw[:end] + ",\n" + indent + npc + raw[end:]
    WORLD.write_text(raw, encoding="utf-8", newline="")


def main() -> None:
    places = stamp_places()
    for name, behavior in BEHAVIORS.items():
        write_json(DATA / "behaviors" / f"{name}.json", {"$schema": "../../../schemas/behavior.schema.json", "id": f"base:behavior/{name}",
                                                         "kind": "melee_chaser", **behavior})
    for name, (art, level, hp, atk, dfn, mdef, speed, xp, behavior, _en, _it) in ADVENTURERS.items():
        write_json(DATA / "enemies" / f"adventurer_{name}.json", {
            "$schema": "../../../schemas/enemy.schema.json", "id": f"base:enemy/adventurer_{name}", "name": f"$i18n:enemy.adventurer_{name}.name",
            "level": level, "stats": {"hp": hp, "atk": atk, "def": dfn, "mdef": mdef, "speed_x100": speed}, "element": "none",
            "sound": "knight", "xp": xp,
            "drops": [{"item": "base:item/iron_ore", "qty_min": 1, "qty_max": 2, "weight_pm": 600},
                      {"item": "base:item/rust_flake", "qty_min": 1, "qty_max": 1, "weight_pm": 400}],
            "radius_x100": 45, "behavior": f"base:behavior/{behavior}", "art": f"base:art/creature/{art}"})
    traps = [{"kind": "spikes", "at": at, "radius_x100": 60, "flag": "dungeon_spikes"} for at in places["1"]]
    traps += [{"kind": "tar", "at": at, "radius_x100": 60, "flag": "dungeon_tar"} for at in places["2"]]
    write_json(DATA / "defense.json", {
        "$schema": "../../schemas/defense.schema.json", "id": "base:defense/dungeon", "core": places["3"][0], "gate": places["4"][0],
        "core_radius_x100": 120, "wave_ticks": WAVE_TICKS, "waves": [[f"base:enemy/adventurer_{n}" for n in wave] for wave in WAVES],
        "traps": traps, "spikes_pct": 20, "tar_ticks": 180, "reward": REWARD})
    write_json(DATA / "dialogues" / "npc" / f"{STEWARD[1]}.json", dialogue())
    for lang in ("en", "it"):
        w = WORDS[lang]
        core = {f"speaker.{STEWARD[0]}": w["speaker"]}
        core.update({f"dlg.grubb.{k}": v for k, v in w.items() if k != "speaker" and not k.startswith("ui.")})
        core.update({k: v for k, v in w.items() if k.startswith("ui.")})
        set_texts("core.json", lang, core)
        set_texts("content.json", lang, {f"enemy.adventurer_{n}.name": a[9 if lang == "en" else 10] for n, a in ADVENTURERS.items()})
    patch_world()
    print(f"wrote Gideon's Dungeon: {len(WAVES)} waves, {len(ADVENTURERS)} adventurers, {len(traps)} traps")


if __name__ == "__main__":
    main()
