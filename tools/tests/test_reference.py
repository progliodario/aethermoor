import re
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

from reference import numerics as nm  # noqa: E402
from reference import rules  # noqa: E402
from reference.i18n import format_message  # noqa: E402
from reference.ids import valid_id  # noqa: E402


def test_splitmix64_known_answers():
    sm = nm.SplitMix64(0)
    assert sm.next() == 0xE220A8397B1DCDAF
    assert sm.next() == 0x6E789E6AA1B965F4


def test_pcg32_known_answers():
    p = nm.Pcg32(42, 54)
    assert [p.next_u32() for _ in range(6)] == [
        0xA15C02B7, 0x7B47F409, 0xBA1D3330, 0x83D2F293, 0xBFA4784B, 0xCBED606E]


def test_fnv1a64_known_answers():
    assert nm.fnv1a64(b"") == 0xCBF29CE484222325
    assert nm.fnv1a64(b"a") == 0xAF63DC4C8601EC8C


def test_bounded_stays_in_range():
    p = nm.Pcg32(1, 2)
    assert all(0 <= p.next_bounded(7) < 7 for _ in range(1000))


def test_streams_are_independent_and_reproducible():
    a = [nm.derive_stream(5, "combat").next_u32() for _ in range(1)]
    b = [nm.derive_stream(5, "combat").next_u32() for _ in range(1)]
    c = [nm.derive_stream(5, "loot").next_u32() for _ in range(1)]
    assert a == b and a != c


def test_noise_range_and_continuity():
    for x in range(-200000, 200000, 7919):
        for y in (-123456, 0, 98765):
            assert 0 <= nm.noise2(3, x, y) <= 65535
            assert 0 <= nm.fbm2(3, x, y, 5) <= 65535
    # neighbouring samples differ by a small amount
    assert abs(nm.noise2(9, 100000, 100000) - nm.noise2(9, 100001, 100000)) < 8


def test_noise_is_exact_on_lattice():
    assert nm.noise2(11, 5 * 65536, -3 * 65536) == nm.lattice(11, 5, -3)


def test_negative_shift_is_floor():
    assert (-1 >> 16) == -1
    assert nm.mulq(-3, 32768) == -2  # floor(-1.5)


def test_damage_minimum_is_one():
    assert rules.damage(1, 1, 1000, 500, 0, 1, 99, 950, False, 1500, 100) == 1


def test_damage_basic():
    assert rules.damage(20, 100, 0, 1000, 0, 1, 1, 1000, False, 1500, 1000) == 20


def test_xp_table_shape():
    table = rules.generate_xp_table()
    assert len(table) == 98
    assert table[0] == 50 and table[1] == 130
    assert all(b > a for a, b in zip(table, table[1:]))


def test_xp_gain_bounds():
    assert rules.xp_gain(100, 1, 99) == 10      # floor of 10%
    assert rules.xp_gain(100, 99, 1) == 150     # cap of 150%


@pytest.mark.parametrize("text,expected", [
    ("{n, plural, one {# apple} other {# apples}}", {1: "1 apple", 2: "2 apples", 0: "0 apples"}),
])
def test_plural(text, expected):
    for n, out in expected.items():
        assert format_message(text, "en", {"n": n}) == out


def test_missing_argument_is_kept():
    assert format_message("Hi {who}", "en", {}) == "Hi {who}"


def test_valid_id_matches_regex():
    pattern = re.compile(r"[a-z][a-z0-9_]*:[a-z][a-z0-9_]*(?:/[a-z0-9_]+)+")
    for text in ["base:enemy/slime", "a:b/c/d", "Base:enemy/x", "base:enemy", "base:enemy/", "x:y/Z", ""]:
        assert valid_id(text) == bool(pattern.fullmatch(text)), text


def test_generated_files_are_current():
    for script in ("gen_conformance.py", "gen_tables.py", "make_demo_map.py"):
        result = subprocess.run([sys.executable, str(TOOLS / script), "--check"],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr


def test_saves_in_the_vectors_match_the_schema():
    import json

    from jsonschema import Draft202012Validator

    root = TOOLS.parent
    schema = json.loads((root / "schemas" / "save.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    doc = json.loads((root / "tests" / "conformance" / "save.json").read_text(encoding="utf-8"))
    assert doc["cases"]
    for case in doc["cases"]:
        errors = list(validator.iter_errors({"save_version": 1, **case["input"]["save"]}))
        assert not errors, (case["name"], errors[:1])


def test_world_chunks_are_the_restriction_of_the_world():

    from reference import worldgen

    params = worldgen.load_params()
    params = {k: v for k, v in {**params, "width": 80, "height": 72, "border": 2}.items() if k not in ("home", "landmarks")}
    world = worldgen.generate(5, params)
    size = worldgen.CHUNK_SIZE
    props, spawners = [], []
    for cy in range(-1, 4):
        for cx in range(-1, 4):
            chunk = worldgen.generate_chunk(5, params, cx, cy)
            for i, gid in enumerate(chunk["tiles"]):
                x, y = cx * size + i % size, cy * size + i // size
                inside = 0 <= x < params["width"] and 0 <= y < params["height"]
                assert gid == (world["tiles"][y * params["width"] + x] if inside else params["tiles"]["water"])
            props += chunk["props"]
            spawners += chunk["spawners"]
    for cy in range(0, 3):
        for cx in range(0, 3):
            assert worldgen.chunk_spawners(5, params, cx, cy) == worldgen.generate_chunk(5, params, cx, cy)["spawners"]
    key = lambda p: (p["y256"], p["x256"])  # noqa: E731
    assert sorted(props, key=key) == sorted(world["props"], key=key)
    assert sorted(spawners) == sorted(world["spawners"])


def test_world_time_light_and_weather():

    from reference import worldgen, worldtime

    t = worldgen.load_params()["time"]
    assert worldtime.tod_pm(t, t["day_ticks"] * 3 + t["day_ticks"] // 2) == 500
    assert worldtime.day_of(t, t["day_ticks"] * 3) == 4
    assert [worldtime.light_pm(t, tod) for tod in (0, 200, 250, 300, 500, 700, 750, 800, 1000)] == [180, 180, 590, 1000, 1000, 1000, 590, 180, 180]
    for ticks in range(0, 5 * t["weather"]["period_ticks"], 997):
        s = worldtime.sample(42, t, ticks)
        assert 0 <= s["rain_pm"] <= 1000 and 0 <= s["dim_pm"] <= 1000 and 0 <= s["effective_light_pm"] <= 1000
    # The weather only depends on the seed and the period: same period, same kind.
    period = t["weather"]["period_ticks"]
    assert worldtime.weather_at(9, t, 7 * period + 5000)["kind"] == worldtime.weather_at(9, t, 7 * period + 17000)["kind"]


def test_rivers_and_roads_are_overlays_on_land():

    from reference import worldgen

    params = worldgen.load_params()
    seen = set()
    for y in range(8100, 8300, 3):
        for x in range(8100, 8300, 3):
            biome = worldgen.biome_at(3, params, x, y)
            overlay = worldgen.overlay_at(3, params, biome, x, y)
            if overlay is not None:
                assert biome in worldgen.LAND
                assert worldgen.gid_for(3, params, biome, x, y, overlay) == params["tiles"][overlay]
                seen.add(overlay)
    assert {"river", "road"} <= seen
    # Nothing inside the spawn clearing.
    cx = cy = 8192
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            if dx * dx + dy * dy < params["spawn_clear_radius"] ** 2:
                assert worldgen.overlay_at(3, params, "plains", cx + dx, cy + dy) is None


def test_world_map_exploration():

    from reference import worldgen

    params = worldgen.load_params()
    cells: set = set()
    worldgen.explore(cells, params, 8192, 8192)
    assert len(cells) == 9 and (64, 64) in cells and (63, 63) in cells and (65, 65) in cells
    worldgen.explore(cells, params, 8193, 8200)  # same cell: nothing new
    assert len(cells) == 9
    corner: set = set()
    worldgen.explore(corner, params, 0, 0)
    assert corner == {(0, 0), (1, 0), (0, 1), (1, 1)}
    far: set = set()
    worldgen.explore(far, params, 16383, 16383)
    assert far == {(126, 126), (127, 126), (126, 127), (127, 127)}
    assert 0 <= worldgen.biome_code(1, params, 64, 64) < 7


def test_settlements_are_inside_their_cells_and_deterministic():
    from reference import worldgen

    params = worldgen.load_params()
    found = worldgen.settlements_in(7, params, 0, 0, 31, 31)
    assert found and worldgen.settlements_in(7, params, 0, 0, 31, 31) == found
    assert worldgen.settlements_in(8, params, 0, 0, 31, 31) != found
    for site in found:
        cell_x, cell_y = site["px"] // worldgen.SITE_CELL, site["py"] // worldgen.SITE_CELL
        # The footprint lies completely inside the site cell of its site point.
        assert site["x"] // worldgen.SITE_CELL == cell_x and (site["x"] + site["w"] - 1) // worldgen.SITE_CELL == cell_x
        assert site["y"] // worldgen.SITE_CELL == cell_y and (site["y"] + site["h"] - 1) // worldgen.SITE_CELL == cell_y
        assert site["name"] and 0 <= site["region"] < len(params["regions"])
    # The stamp is drawn: the road gid of a village crosses its footprint, and nothing random grows inside it.
    site = next(s for s in found if s["kind"] == "village")
    sites = worldgen.Sites(7, params)
    inside = [sites.at(site["x"] + dx, site["y"] + dy) for dy in range(site["h"]) for dx in range(site["w"])]
    assert all(entry is not None and entry[0]["name"] == site["name"] for entry in inside)
    chunk = worldgen.generate_chunk(7, params, site["px"] // 32, site["py"] // 32)
    assert 13 in chunk["tiles"] and 14 in chunk["tiles"]
    assert all(not (site["x"] <= s[0] < site["x"] + site["w"] and site["y"] <= s[1] < site["y"] + site["h"]) for s in chunk["spawners"])


def test_regions_follow_the_nearest_center():
    from reference import worldgen

    params = worldgen.load_params()
    assert params["regions"][worldgen.region_at(params, 8192, 8192)]["id"] == "verdalis"
    assert params["regions"][worldgen.region_at(params, 0, 16383)]["id"] == "tidehaven"
    assert params["regions"][worldgen.region_at(params, 16383, 8000)]["id"] == "ashen_wastes"


def test_settlement_people_have_dialogues_and_texts():
    import json

    from reference import worldgen

    params = worldgen.load_params()
    data = TOOLS.parent / "data" / "base"
    roles = {entry["npc"] for stamp in params["stamp_defs"].values() for entry in stamp["legend"].values() if "npc" in entry}
    assert {"elder", "shopkeeper", "innkeeper", "guild_clerk", "villager"} <= roles
    texts = {lang: json.loads((data / "i18n" / lang / "roles.json").read_text(encoding="utf-8")) for lang in ("en", "it")}
    for region in params["regions"]:
        for role in roles:
            dialogue = params["settlements"]["dialogue"].replace("{role}", role).replace("{tone}", region["tone"])
            path = data / "dialogues" / "role" / f"{dialogue.rsplit('/', 1)[-1]}.json"
            assert path.exists(), dialogue
            for node in json.loads(path.read_text(encoding="utf-8"))["nodes"].values():
                if node["type"] == "say":
                    for lang in texts:
                        assert node["text"].removeprefix("$i18n:") in texts[lang]
    for quirk in params["settlements"]["quirks"]:
        assert all(quirk in table for table in texts.values())
    # People are deterministic and sit on floor tiles of their settlement.
    found = worldgen.settlements_in(3, params, 0, 0, 40, 40)
    town = next(s for s in found if s["kind"] == "town")
    keys = []
    for (x, y), (index, role) in town["slots"].items():
        person = worldgen.person_at(3, params, town, x, y)
        assert person["role"] == role and person["place"] == town["name"] and person["key"].endswith(f":{index}")
        keys.append(person["key"])
    assert len(set(keys)) == len(keys) >= 7


def test_every_elder_offers_a_local_errand_that_pays_once():
    import json

    from reference import story, worldgen

    class Host:
        x = y = 0.0
        level = 1

        def __init__(self) -> None:
            self.inventory: dict[str, int] = {}
            self.xp = 0

        def grant_xp(self, amount: int) -> None:
            self.xp += amount

        def season_id(self) -> str:
            return ""

        def tod_pm(self) -> int:
            return 500

    data = TOOLS.parent / "data" / "base"
    params = worldgen.load_params()
    tones = {region["tone"] for region in params["regions"]}
    assert len(tones) == len(params["regions"])
    for tone in sorted(tones):
        dialogue = json.loads((data / "dialogues" / "role" / f"elder_{tone}.json").read_text(encoding="utf-8"))
        quests = {}
        for path in (data / "quests" / "side").glob("*.json"):
            quest = json.loads(path.read_text(encoding="utf-8"))
            quests[quest["id"]] = quest
        host = Host()
        s = story.Story(host, {"quests": quests, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})
        s.start_dialogue(dialogue["id"])
        s.advance()  # the greeting
        offer = next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "errand_offer")
        s.choose(offer)
        s.advance()  # the offer
        s.choose(0)  # accept
        (quest_id,) = s.quests
        assert quests[quest_id]["kind"] == "side" and s.quests[quest_id]["done"] is False
        objectives = quests[quest_id]["stages"][0]["objectives"]
        for objective in objectives:
            if objective["type"] == "kill":
                for _ in range(objective["count"]):
                    s.on_kill(objective["enemy"])
            else:
                host.inventory[objective["item"]] = objective["count"]
                s.on_kill("base:enemy/none")
        assert s.quests[quest_id]["done"] is True
        s.start_dialogue(dialogue["id"])
        s.advance()
        report = next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "errand_paid")
        s.choose(report)
        assert s.flags and s.gold > 0 and host.xp > 0 and host.inventory["base:item/potion_small"] > 0
        s.advance()  # the thanks
        s.start_dialogue(dialogue["id"])
        s.advance()
        assert all(c["next"] not in ("errand_offer", "errand_paid") for c in s.visible_choices())


def test_every_innkeeper_has_a_favor_and_every_villager_a_legend():
    import json

    from reference import story, worldgen

    class Host:
        x = y = 0.0
        level = 1

        def __init__(self) -> None:
            self.inventory: dict[str, int] = {}
            self.xp = 0

        def grant_xp(self, amount: int) -> None:
            self.xp += amount

        def season_id(self) -> str:
            return ""

        def tod_pm(self) -> int:
            return 500

    data = TOOLS.parent / "data" / "base"
    params = worldgen.load_params()
    texts = json.loads((data / "i18n" / "en" / "roles.json").read_text(encoding="utf-8"))
    quests = {}
    for path in (data / "quests" / "side").glob("*.json"):
        quest = json.loads(path.read_text(encoding="utf-8"))
        quests[quest["id"]] = quest
    for tone in sorted({region["tone"] for region in params["regions"]}):
        villager = json.loads((data / "dialogues" / "role" / f"villager_{tone}.json").read_text(encoding="utf-8"))
        assert texts[villager["nodes"]["legend"]["text"].removeprefix("$i18n:")]
        dialogue = json.loads((data / "dialogues" / "role" / f"innkeeper_{tone}.json").read_text(encoding="utf-8"))
        host = Host()
        s = story.Story(host, {"quests": quests, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})
        s.start_dialogue(dialogue["id"])
        s.advance()
        s.choose(next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "pantry_offer"))
        s.advance()
        s.choose(0)
        (quest_id,) = s.quests
        (objective,) = quests[quest_id]["stages"][0]["objectives"]
        assert not s.quests[quest_id]["done"]
        host.inventory[objective["item"]] = objective["count"]
        s.on_kill("base:enemy/none")
        assert s.quests[quest_id]["done"]
        s.start_dialogue(dialogue["id"])
        s.advance()
        s.choose(next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "pantry_paid"))
        assert s.gold > 0 and host.xp > 0 and host.inventory["base:item/potion_medium"] > 0
        s.advance()
        s.start_dialogue(dialogue["id"])
        s.advance()
        assert all(c["next"] not in ("pantry_offer", "pantry_paid") for c in s.visible_choices())


def test_every_shopkeeper_can_craft_a_unique_item_from_monster_parts():
    import json

    from reference import story, worldgen

    class Host:
        x = y = 0.0
        level = 1

        def __init__(self) -> None:
            self.inventory: dict[str, int] = {}

        def grant_xp(self, amount: int) -> None:
            pass

    data = TOOLS.parent / "data" / "base"
    params = worldgen.load_params()
    results = set()
    for tone in sorted({region["tone"] for region in params["regions"]}):
        dialogue = json.loads((data / "dialogues" / "role" / f"shopkeeper_{tone}.json").read_text(encoding="utf-8"))
        craft = dialogue["nodes"]["craft_do"]["effects"]
        parts = {e["item"]: e["qty"] for e in craft if e["effect"] == "remove_item"}
        (result,) = [e["item"] for e in craft if e["effect"] == "add_item"]
        assert result not in results and (data / "items" / f"{result.split('/')[-1]}.json").exists()
        results.add(result)
        host = Host()
        s = story.Story(host, {"quests": {}, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})
        s.start_dialogue(dialogue["id"])
        s.advance()
        s.choose(next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "craft_info"))
        s.advance()
        assert [c["next"] for c in s.visible_choices()] == ["end"]  # without the parts the shopkeeper only offers to wait
        s.choose(0)
        host.inventory = {item: qty + 1 for item, qty in parts.items()}  # one more of each than needed
        s.start_dialogue(dialogue["id"])
        s.advance()
        s.choose(next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "craft_info"))
        s.advance()
        s.choose(0)
        assert host.inventory.pop(result) == 1
        assert host.inventory == {item: 1 for item in parts}
        s.advance()
        s.start_dialogue(dialogue["id"])
        s.advance()
        assert all(c["next"] != "craft_info" for c in s.visible_choices())  # made once


def test_every_elder_has_a_second_errand_after_the_first():
    import json

    from reference import story, worldgen

    class Host:
        x = y = 0.0
        level = 1

        def __init__(self) -> None:
            self.inventory: dict[str, int] = {}
            self.xp = 0

        def grant_xp(self, amount: int) -> None:
            self.xp += amount

        def season_id(self) -> str:
            return ""

        def tod_pm(self) -> int:
            return 500

    data = TOOLS.parent / "data" / "base"
    params = worldgen.load_params()
    quests = {}
    for path in (data / "quests" / "side").glob("*.json"):
        quest = json.loads(path.read_text(encoding="utf-8"))
        quests[quest["id"]] = quest
    for tone in sorted({region["tone"] for region in params["regions"]}):
        dialogue = json.loads((data / "dialogues" / "role" / f"elder_{tone}.json").read_text(encoding="utf-8"))
        host = Host()
        s = story.Story(host, {"quests": quests, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})

        def talk(target: str, s=s, dialogue=dialogue) -> None:
            s.start_dialogue(dialogue["id"])
            s.advance()
            s.choose(next(i for i, c in enumerate(s.visible_choices()) if c["next"] == target))

        s.start_dialogue(dialogue["id"])
        s.advance()
        assert all(c["next"] != "hunt_offer" for c in s.visible_choices())  # not before the first errand is paid
        s.choose(len(s.visible_choices()) - 1)
        paid_flag = next(e["flag"] for e in dialogue["nodes"]["errand_paid"]["effects"] if e["effect"] == "set_flag")
        s.flags[paid_flag] = True
        talk("hunt_offer")
        s.advance()
        s.choose(0)
        (quest_id,) = s.quests
        (objective,) = quests[quest_id]["stages"][0]["objectives"]
        assert objective["type"] == "kill" and (data / "enemies" / f"{objective['enemy'].split('/')[-1]}.json").exists()
        s.on_kill(objective["enemy"])
        assert s.quests[quest_id]["done"]
        talk("hunt_paid")
        assert s.gold > 0 and host.xp > 0 and s.guild_points > 0 and host.inventory["base:item/potion_large"] > 0
        s.advance()
        s.start_dialogue(dialogue["id"])
        s.advance()
        assert all(c["next"] not in ("hunt_offer", "hunt_paid") for c in s.visible_choices())


class _InnHost:
    x = y = 0.0

    def __init__(self) -> None:
        self.inventory: dict[str, int] = {}
        self.level = 1
        self.xp = 0
        self.healed = 0

    def grant_xp(self, amount: int) -> None:
        self.xp += amount

    def heal_full(self) -> None:
        self.healed += 1

    def season_id(self) -> str:
        return ""

    def tod_pm(self) -> int:
        return 500


def _regional_dialogues(role: str) -> dict:
    import json

    from reference import worldgen

    data = TOOLS.parent / "data" / "base"
    params = worldgen.load_params()
    tones = sorted({region["tone"] for region in params["regions"]})
    return {tone: json.loads((data / "dialogues" / "role" / f"{role}_{tone}.json").read_text(encoding="utf-8")) for tone in tones}


def test_every_innkeeper_rents_a_bed_and_sells_a_meal():
    from reference import story

    for tone, dialogue in _regional_dialogues("innkeeper").items():
        bed = next(c for c in dialogue["nodes"]["menu"]["choices"] if c["next"] == "inn_rest")
        price = bed["when"]["gold_at_least"]
        meal_price = next(e["amount"] for e in dialogue["nodes"]["inn_meal"]["effects"] if e["effect"] == "spend_gold")
        host = _InnHost()
        s = story.Story(host, {"quests": {}, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})

        def visible(s=s, dialogue=dialogue):
            s.start_dialogue(dialogue["id"])
            s.advance()
            return [c["next"] for c in s.visible_choices()]

        assert "inn_poor" in visible() and "inn_rest" not in visible() and "inn_meal" not in visible(), tone
        s.dialogue = None
        s.gold = price + meal_price
        assert "inn_rest" in visible() and "inn_poor" not in visible() and "inn_meal" in visible(), tone
        s.choose(visible().index("inn_rest"))
        s.advance()
        assert s.gold == meal_price and host.healed == 1, tone
        assert "inn_meal" in visible()
        s.choose(visible().index("inn_meal"))
        s.advance()
        assert s.gold == 0 and sum(host.inventory.values()) >= 1, tone


def test_every_guild_clerk_offers_three_commissions_in_order():
    import json

    from reference import story

    data = TOOLS.parent / "data" / "base"
    quests = {}
    for path in (data / "quests" / "side").glob("*.json"):
        quest = json.loads(path.read_text(encoding="utf-8"))
        quests[quest["id"]] = quest
    for tone, dialogue in _regional_dialogues("guild_clerk").items():
        host = _InnHost()
        s = story.Story(host, {"quests": quests, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})

        def hub(s=s, dialogue=dialogue):
            s.start_dialogue(dialogue["id"])
            s.advance()
            s.choose(next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "comm_hub"))
            return [c["next"] for c in s.visible_choices()]

        assert "comm_offer_2" not in hub() and "comm_offer_3" not in hub(), tone  # the chain starts with the first
        s.dialogue = None
        for n in (1, 2, 3):
            host.level = 99
            options = hub()
            assert f"comm_offer_{n}" in options and all(f"comm_offer_{m}" not in options for m in (1, 2, 3) if m != n), (tone, n)
            s.choose(options.index(f"comm_offer_{n}"))
            s.advance()
            s.choose(0)
            qid = f"base:quest/side/clerk_{tone}_{n}"
            hunt, gather = quests[qid]["stages"]
            assert hunt["next"] == "gather" and gather["next"] == "end"
            (kill,) = hunt["objectives"]
            for _ in range(kill["count"]):
                s.on_kill(kill["enemy"])
            assert s.quests[qid]["stage"] == "gather" and not s.quests[qid]["done"]
            (collect,) = gather["objectives"]
            host.inventory[collect["item"]] = collect["count"]
            s.on_kill("base:enemy/none")
            assert s.quests[qid]["done"]
            options = hub()
            assert f"comm_paid_{n}" in options
            s.choose(options.index(f"comm_paid_{n}"))
            s.advance()
            assert s.flags[f"comm_clerk_{tone}_{n}_paid"] and s.gold > 0


def test_the_wayfarers_tell_three_stories_and_pass_letters_around_a_ring():
    import json

    from reference import story, worldgen

    data = TOOLS.parent / "data" / "base"
    world = json.loads((data / "worlds" / "overworld.json").read_text(encoding="utf-8"))
    people = {n["key"]: n for n in world["npcs"] if n["key"].startswith("wayfarer_")}
    assert len(people) == 8
    params = worldgen.load_params()
    outposts = {landmark["id"].replace("_outpost", ""): landmark for landmark in params["landmarks"] if landmark["id"].endswith("_outpost")}
    assert len(outposts) == 8
    quests = {}
    for path in (data / "quests" / "side").glob("way_*.json"):
        quest = json.loads(path.read_text(encoding="utf-8"))
        quests[quest["id"]] = quest
    dialogues = {}
    for npc in people.values():
        doc = json.loads((data / "dialogues" / "npc" / f"{npc['dialogue'].split('/')[-1]}.json").read_text(encoding="utf-8"))
        dialogues[doc["id"]] = doc
        # every wayfarer stands in the square of an outpost: one tile below its site point
        assert any((landmark["dx"], landmark["dy"] + 1) == (npc["dx"], npc["dy"]) for landmark in outposts.values()), npc["key"]

    class Host:
        x = y = 0.0
        level = 1

        def __init__(self) -> None:
            self.inventory: dict[str, int] = {}
            self.xp = 0

        def grant_xp(self, amount: int) -> None:
            self.xp += amount

        def season_id(self) -> str:
            return ""

        def tod_pm(self) -> int:
            return 500

    host = Host()
    s = story.Story(host, {"quests": quests, "dialogues": dialogues, "npcs": []})

    def talk(key: str) -> None:
        s.on_talk(key)
        s.start_dialogue(people[key]["dialogue"])

    def finish(stage_objectives: list) -> None:
        for objective in stage_objectives:
            if objective["type"] == "kill":
                for _ in range(objective["count"]):
                    s.on_kill(objective["enemy"])
            elif objective["type"] == "collect":
                host.inventory[objective["item"]] = objective["count"]
        s.on_kill("base:enemy/none")

    for key in people:
        w = key.removeprefix("wayfarer_")
        q = [f"base:quest/side/way_{w}_{n}" for n in (1, 2, 3)]
        for n in (1, 2, 3):
            talk(key)
            if s.dialogue is not None and s.dialogue[1] in ("q1_thanks", "q2_thanks"):
                s.advance()  # the thanks of the previous story, then the next offer
            while s.dialogue is not None and s._node()["type"] == "say" and s.dialogue[1].endswith("_offer") is False:
                s.advance()
            assert s.dialogue is not None and s.dialogue[1] == f"q{n}_offer", (key, n, s.dialogue)
            s.advance()
            s.choose(0)
            assert q[n - 1] in s.quests and not s.quests[q[n - 1]]["done"]
            stages = quests[q[n - 1]]["stages"]
            if n == 2:
                (letter,) = stages[0]["objectives"]
                receiver = letter["npc_key"]
                talk(receiver)  # the letter arrives: the receiver reads it first, then the player goes back
                assert s.quests[q[1]]["stage"] == "report"
                assert s.dialogue is not None and s.dialogue[1] == "letter", receiver
                while s.dialogue is not None:
                    s.advance() if s._node()["type"] == "say" else s.choose(len(s.visible_choices()) - 1)
                talk(key)  # back to the sender: the quest ends on this talk
                assert s.quests[q[1]]["done"]
            else:
                finish(stages[0]["objectives"])
                if len(stages) > 1:
                    talk(key)
                assert s.quests[q[n - 1]]["done"]
            while s.dialogue is not None:
                s.advance() if s._node()["type"] == "say" else s.choose(len(s.visible_choices()) - 1)
        reward = next(e["item"] for e in quests[q[2]]["rewards"] if e["effect"] == "add_item")
        assert host.inventory.get(reward) == 1, key


class _TimeHost(_InnHost):
    def __init__(self, season: str, tod: int) -> None:
        super().__init__()
        self.season, self.tod = season, tod

    def season_id(self) -> str:
        return self.season

    def tod_pm(self) -> int:
        return self.tod


def test_season_and_time_of_day_conditions():
    from reference import story

    s = story.Story(_TimeHost("winter", 900), {"quests": {}, "dialogues": {}, "npcs": []})
    assert s.holds({"season": "winter"}) and not s.holds({"season": "summer"})
    assert s.holds({"tod_between": [800, 250]}) and not s.holds({"tod_between": [250, 800]})  # 900 is night, not day
    assert s.holds({"tod_between": [900, 901]}) and not s.holds({"tod_between": [800, 900]})  # the end is excluded
    s.host.tod = 100
    assert s.holds({"tod_between": [800, 250]}) and not s.holds({"tod_between": [250, 800]})  # the night crosses midnight


def test_villagers_talk_about_the_season_and_innkeepers_tell_night_tales():
    from reference import story

    seasons = ("spring", "summer", "autumn", "winter")
    for tone, dialogue in _regional_dialogues("villager").items():
        for season in seasons:
            host = _TimeHost(season, 500)
            s = story.Story(host, {"quests": {}, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})
            s.start_dialogue(dialogue["id"])
            s.advance()
            s.choose(next(i for i, c in enumerate(s.visible_choices()) if c["next"] == "season_spring_check"))
            assert s.dialogue is not None and s.dialogue[1] == f"season_{season}", (tone, season, s.dialogue)
    for tone, dialogue in _regional_dialogues("innkeeper").items():
        for tod, tale in ((500, False), (900, True), (100, True), (400, False)):
            s = story.Story(_TimeHost("summer", tod), {"quests": {}, "dialogues": {dialogue["id"]: dialogue}, "npcs": []})
            s.start_dialogue(dialogue["id"])
            s.advance()
            assert any(c["next"] == "night_tale" for c in s.visible_choices()) is tale, (tone, tod)


def test_landmarks_are_never_buried_in_water_or_mountains():
    from reference import worldgen

    params = worldgen.load_params()
    assert params["landmark_clearing"] > 0
    for seed in (1, 77, 90210):
        for lm in params["landmarks"]:
            px, py = params["width"] // 2 + lm["dx"], params["height"] // 2 + lm["dy"]
            st = params["stamp_defs"][lm["stamp"]]
            r = params["landmark_clearing"]
            x0, y0 = px - st["anchor"][0] - r, py - st["anchor"][1] - r
            for x in range(x0, x0 + st["w"] + 2 * r, 5):
                for y in range(y0, y0 + st["h"] + 2 * r, 5):
                    assert worldgen.biome_at(seed, params, x, y) not in ("water", "mountain"), (seed, lm["id"], x, y)
