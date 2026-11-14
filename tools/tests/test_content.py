"""Consistency of the content of the base pack: what the quests ask for exists and can be found in the world."""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent.parent / "data" / "base"


def load_all(folder: str) -> dict[str, dict]:
    docs = {}
    for path in sorted((DATA / folder).rglob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        docs[doc["id"]] = doc
    return docs


def walk(node, found: dict[str, set[str]]) -> None:
    """Collects the ids a dialogue or quest refers to: quests, items, enemies and flags, in conditions and effects."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("quest_active", "quest_done") and isinstance(value, str):
                found["quests"].add(value)
            elif key == "quest_stage" and isinstance(value, dict):
                found["quests"].add(value["quest"])
            elif key == "has_item" and isinstance(value, dict):
                found["items"].add(value["item"])
            elif key == "effect" and value in ("add_item", "remove_item"):
                found["items"].add(node["item"])
            elif key == "effect" and value == "start_quest":
                found["quests"].add(node["quest"])
            elif key == "enemy" and isinstance(value, str):
                found["enemies"].add(value)
            elif key == "item" and isinstance(value, str) and node.get("type") == "collect":
                found["items"].add(value)
            else:
                walk(value, found)
    elif isinstance(node, list):
        for value in node:
            walk(value, found)


def spawnable_enemies() -> set[str]:
    world = json.loads((DATA / "worlds" / "overworld.json").read_text(encoding="utf-8"))
    found = {f["enemy"] for region in world["regions"] for f in region["fauna"]}
    for path in (DATA / "stamps").glob("*.json"):
        stamp = json.loads(path.read_text(encoding="utf-8"))
        found |= {entry["spawner"] for entry in stamp["legend"].values() if "spawner" in entry}
    return found


def test_everything_the_quests_and_dialogues_name_exists():
    quests, items, enemies = load_all("quests"), load_all("items"), load_all("enemies")
    for folder in ("quests", "dialogues"):
        for doc in load_all(folder).values():
            found = {"quests": set(), "items": set(), "enemies": set()}
            walk(doc, found)
            assert found["quests"] <= set(quests), (doc["id"], found["quests"] - set(quests))
            assert found["items"] <= set(items), (doc["id"], found["items"] - set(items))
            assert found["enemies"] <= set(enemies), (doc["id"], found["enemies"] - set(enemies))


def test_every_kill_target_spawns_and_every_item_asked_for_can_be_found():
    spawn = spawnable_enemies()
    enemies, items = load_all("enemies"), load_all("items")
    dropped = {drop["item"] for enemy_id in spawn for drop in enemies[enemy_id]["drops"]}
    # what grows on the props of the world (spec 06, "Gathering") and what the recipes make can be found too
    gathering = json.loads((DATA / "gathering.json").read_text(encoding="utf-8"))
    recipes = json.loads((DATA / "recipes.json").read_text(encoding="utf-8"))
    dropped |= {drop["item"] for node in gathering["nodes"] for drop in node["drops"]}
    dropped |= {recipe["output"]["item"] for recipe in recipes["recipes"]}
    rewarded = set()
    for doc in list(load_all("quests").values()) + list(load_all("dialogues").values()):
        found = {"quests": set(), "items": set(), "enemies": set()}
        for key in ("rewards", "nodes"):
            if key in doc:
                walk(doc[key], found)
        rewarded |= found["items"]
    for quest in load_all("quests").values():
        found = {"quests": set(), "items": set(), "enemies": set()}
        walk(quest["stages"], found)
        assert found["enemies"] <= spawn, (quest["id"], "does not spawn anywhere:", found["enemies"] - spawn)
        for item in found["items"]:
            assert item in dropped or item in rewarded, (quest["id"], "cannot be found:", item)
    for enemy_id in spawn:
        for drop in enemies[enemy_id]["drops"]:
            assert drop["item"] in items, (enemy_id, drop["item"])


def test_every_region_item_in_a_shop_exists():
    world = json.loads((DATA / "worlds" / "overworld.json").read_text(encoding="utf-8"))
    items = load_all("items")
    for region in world["regions"]:
        assert set(region["shop"]["stock"]) <= set(items), region["id"]
        for fauna in region["fauna"]:
            assert fauna["drop"] in items, (region["id"], fauna)


def test_the_people_of_the_overworld_stand_on_open_floor():
    """Mira, Pip and the wayfarers must not stand on a wall, a prop or another person of a stamp."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from reference import worldgen

    params = worldgen.load_params()
    world = json.loads((DATA / "worlds" / "overworld.json").read_text(encoding="utf-8"))
    cx, cy = params["width"] // 2, params["height"] // 2
    for npc in world["npcs"]:
        x, y = cx + npc["dx"], cy + npc["dy"]
        for landmark in params["landmarks"]:
            stamp = params["stamp_defs"][landmark["stamp"]]
            x0 = cx + landmark["dx"] - stamp["anchor"][0]
            y0 = cy + landmark["dy"] - stamp["anchor"][1]
            if x0 <= x < x0 + stamp["w"] and y0 <= y < y0 + stamp["h"]:
                entry = stamp["legend"].get(stamp["rows"][y - y0][x - x0])
                assert entry is not None and entry.get("tile") == 14 and not {"prop", "spawner", "npc"} & set(entry), (npc["key"], entry)


# --------------------------------------------------------------------------------- protagonists (spec 18)


def _protagonists():
    import json
    root = Path(__file__).resolve().parents[2] / "data" / "base"
    return root, [json.loads(p.read_text(encoding="utf-8")) for p in sorted((root / "protagonists").glob("*.json"))]


def test_every_protagonist_is_complete():
    import json
    root, protagonists = _protagonists()
    assert len(protagonists) >= 4
    texts = {}
    for lang in ("en", "it"):
        texts[lang] = {}
        for f in (root / "i18n" / lang).glob("*.json"):
            texts[lang].update(json.loads(f.read_text(encoding="utf-8")))
    skills = {json.loads(p.read_text(encoding="utf-8"))["id"]: json.loads(p.read_text(encoding="utf-8")) for p in (root / "skills").rglob("*.json")}
    items = {json.loads(p.read_text(encoding="utf-8"))["id"] for p in (root / "items").glob("*.json")}
    variants = [json.loads((root / "art/characters/ren" / f"{part}.json").read_text(encoding="utf-8"))["variants"] for part in ("head", "torso", "arm", "leg")]
    for pr in protagonists:
        name = pr["id"].rsplit("/", 1)[1]
        for what in ("name", "tagline", "gift", "story"):
            for lang in ("en", "it"):
                assert f"protagonist.{name}.{what}" in texts[lang], (name, what, lang)
        assert all(i["item"] in items for i in pr["starting_items"]), name
        assert all(s in skills for s in pr["starting_skills"]), name
        chosen = [skills[s] for s in pr["starting_skills"]]
        assert sum("hitbox" in s for s in chosen) >= 2, name  # the attack and the power strike
        assert sum("movement" in s for s in chosen) == 1, name  # one dodge
        assert any(i["item"] for i in pr["starting_items"] if skills and items) and any(
            json.loads((root / "items" / (i["item"].rsplit("/", 1)[1] + ".json")).read_text(encoding="utf-8"))["kind"] == "weapon" for i in pr["starting_items"]), name
        if pr.get("art_variant"):
            assert all(pr["art_variant"] in v for v in variants), name


def test_quality_abilities_and_renown_point_at_things_that_exist():
    """Spec 06 "Quality", spec 11 "Abilities", spec 07 "Renown": the fine pieces, the talents asked for and the regions of the titles exist."""
    items = load_all("items")
    recipes = json.loads((DATA / "recipes.json").read_text(encoding="utf-8"))["recipes"]
    assert any("fine_pm" in r for r in recipes) and any("fine_item" in r for r in recipes)
    for r in recipes:
        assert "fine_item" not in r or ("fine_pm" in r and r["fine_item"] in items), r["id"]
    talents = json.loads((DATA / "talents.json").read_text(encoding="utf-8"))["talents"]
    names = [t["id"] for t in talents]
    for t in talents:
        assert "requires" not in t or names.index(t["requires"]["talent"]) < names.index(t["id"]), t["id"]
    assert {"riposte", "kill_heal", "kill_mana", "whirl"} <= {t["stat"] for t in talents}
    world = json.loads((DATA / "worlds" / "overworld.json").read_text(encoding="utf-8"))
    regions = {r["id"] for r in world["regions"]}
    assert all(0 < r["shop"]["renown_step_pm"] <= r["shop"]["renown_max_pm"] for r in world["regions"])
    titles = json.loads((DATA / "titles.json").read_text(encoding="utf-8"))["titles"]
    renown = [t["kind"].split(":", 1)[1] for t in titles if t["kind"].startswith("renown:")]
    assert sorted(renown) == sorted(regions)


def test_market_wares_actives_and_gifts_of_the_companions():
    """Spec 06 "Market days", spec 07 "Renown", spec 11 "Active abilities", spec 18: the data of each exists and points at real things."""
    items = load_all("items")
    world = json.loads((DATA / "worlds" / "overworld.json").read_text(encoding="utf-8"))
    for region in world["regions"]:
        shop = region["shop"]
        assert shop["market_swing_pm"] > 0, region["id"]
        assert [w["renown"] for w in shop["renown_stock"]] == [5, 10], region["id"]
        assert all(w["item"] in items and w["item"] not in shop["stock"] for w in shop["renown_stock"]), region["id"]
    talents = json.loads((DATA / "talents.json").read_text(encoding="utf-8"))["talents"]
    active = {t["stat"]: t["active"] for t in talents if "active" in t}
    assert set(active) == {"burst", "mend"} and "radius_x100" in active["burst"]
    gifts = {p.stem: json.loads(p.read_text(encoding="utf-8")).get("gift_rules", {}) for p in (DATA / "protagonists").glob("*.json")}
    assert gifts["haruka"]["bond_gain"] > 1 and gifts["gideon"]["companion_atk_pct"] > 100
