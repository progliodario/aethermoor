#!/usr/bin/env python3
"""Writes the numbers of the game, counted from the data, into the documents that show them.

Every document that states how many quests, creatures, items... the game has keeps those numbers in one block between the markers

    <!-- facts:begin -->
    ...
    <!-- facts:end -->

and this tool writes the block (in the language of the document) from the data of the base pack, the conformance vectors and the docs,
so that the numbers never go stale. The prose around the block should not repeat them. `--check` changes nothing and fails when a block
is not what the data says (the tests run it).

    python tools/make_facts.py           # write the blocks
    python tools/make_facts.py --check   # check them
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"
BEGIN = "<!-- facts:begin -->"
END = "<!-- facts:end -->"
# the documents with a block, and the language of each
DOCUMENTS = {
    "README.md": "it",
    "README.en.md": "en",
    "CLAUDE.md": "en",
    "docs/plan/06-roadmap-rischi-backlog.md": "it",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def files(folder: str) -> list[Path]:
    return sorted((DATA / folder).rglob("*.json"))


def count() -> dict[str, int]:
    """The numbers of the game, from the data."""
    sys.path.insert(0, str(ROOT / "tools"))
    from reference import worldgen

    params = worldgen.load_params()
    world = load(DATA / "worlds" / "overworld.json")
    fauna = {f["enemy"] for region in params["regions"] for f in region["fauna"]}
    stamped = {entry["spawner"] for stamp in params["stamp_defs"].values() for entry in stamp["legend"].values() if "spawner" in entry}
    only_in_sites = stamped - fauna
    echoes = {e for e in only_in_sites if "/echo_" in e}
    quests = [p.stem for p in files("quests")]
    recipes = load(DATA / "recipes.json")["recipes"]
    suites = [load(p) for p in sorted((ROOT / "tests" / "conformance").glob("*.json"))]
    texts = {lang: sum(len([k for k in load(p) if k != "$schema"]) for p in sorted((DATA / "i18n" / lang).glob("*.json"))) for lang in ("en", "it")}
    return {
        "regions": len(params["regions"]),
        "protagonists": len(files("protagonists")),
        "companions": len(files("companions")),
        "creatures": len(files("enemies")),
        "guardians": len(only_in_sites - echoes),
        "echoes": len(echoes),
        "items": len(files("items")),
        "recipes": len(recipes),
        "secret_recipes": sum(1 for r in recipes if r.get("requires_flag")),
        "quests": len(quests),
        "story_quests": sum(1 for q in quests if q.startswith("act")),
        "tales": sum(1 for q in quests if q.startswith("tale_")),
        "titles": len(load(DATA / "titles.json")["titles"]),
        "tags": len(load(DATA / "tags.json")["tags"]),
        "deeds": len(load(DATA / "deeds.json")["deeds"]),
        "talents": len(load(DATA / "talents.json")["talents"]),
        "people": len(world["npcs"]),
        "sites": len(world["landmarks"]),
        "sounds": len(list((DATA / "audio" / "sfx").glob("*.json"))),
        "texts": min(texts.values()),
        "suites": len(suites),
        "cases": sum(len(s.get("cases", [])) for s in suites),
        "specs": len([p for p in (ROOT / "docs" / "spec").glob("[0-9]*.md")]),
        "adrs": len(list((ROOT / "docs" / "adr").glob("[0-9]*.md"))),
    }


ROWS = {
    "en": [
        ("World", "{regions} regions, {sites} hand-made sites (dungeons, lairs, outposts, sanctums, Fenwick, the Guest's cottage, Aldermere) and about 130 generated settlements"),
        ("Protagonists", "{protagonists}, each with a companion ({companions} companions) and a story of six acts ({story_quests} story quests)"),
        ("Creatures", "{creatures}, of which {guardians} guardians and {echoes} Echoes"),
        ("Quests", "{quests} ({tales} tales of the villagers)"),
        ("Items and recipes", "{items} items, {recipes} recipes ({secret_recipes} secret)"),
        ("Progression", "{titles} titles, {tags} tags, {talents} talents, {deeds} deeds"),
        ("Named people", "{people} in the world data, besides the generated villagers"),
        ("Sound", "{sounds} synthesized sound effects (music and ambience are off)"),
        ("Texts", "{texts} keys, in Italian and English"),
        ("Same rules on both clients", "{suites} files of conformance vectors, {cases} cases, run by the C++ and the Kotlin tests"),
        ("Documents", "{specs} specs, {adrs} ADRs"),
    ],
    "it": [
        ("Mondo", "{regions} regioni, {sites} luoghi fatti a mano (sotterranei, tane, avamposti, santuari, Fenwick, il cottage dell'Ospite, Aldermere) e circa 130 insediamenti generati"),
        ("Protagonisti", "{protagonists}, ognuno con un compagno ({companions} compagni) e una storia in sei atti ({story_quests} missioni di storia)"),
        ("Creature", "{creatures}, di cui {guardians} guardiani e {echoes} Echi"),
        ("Missioni", "{quests} ({tales} storie dei paesani)"),
        ("Oggetti e ricette", "{items} oggetti, {recipes} ricette ({secret_recipes} segrete)"),
        ("Progressione", "{titles} titoli, {tags} tag, {talents} talenti, {deeds} imprese"),
        ("Persone con nome", "{people} nei dati del mondo, oltre ai paesani generati"),
        ("Suono", "{sounds} effetti sonori sintetizzati (musica e ambiente spenti)"),
        ("Testi", "{texts} chiavi, in italiano e inglese"),
        ("Regole uguali sui due client", "{suites} file di vettori di conformità, {cases} casi, eseguiti dai test C++ e Kotlin"),
        ("Documenti", "{specs} specifiche, {adrs} ADR"),
    ],
}
HEAD = {"en": ("What", "How many (counted from the data by `tools/make_facts.py`)"),
        "it": ("Che cosa", "Quanti (contati dai dati da `tools/make_facts.py`)")}


def block(lang: str, facts: dict[str, int]) -> str:
    what, many = HEAD[lang]
    lines = [BEGIN, f"| {what} | {many} |", "|---|---|"]
    lines += [f"| {name} | {text.format(**facts)} |" for name, text in ROWS[lang]]
    return "\n".join(lines + [END])


def main() -> int:
    check = "--check" in sys.argv
    facts = count()
    stale = []
    for rel, lang in DOCUMENTS.items():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        # a marker counts only on a line of its own: a document may name the markers in its text (CLAUDE.md does)
        begin = re.search(rf"^{re.escape(BEGIN)}$", text, re.M)
        start = begin.start() if begin else -1
        close = re.search(rf"^{re.escape(END)}$", text[start:], re.M) if begin else None
        end = start + close.start() if close else -1
        if start < 0 or end < start:
            stale.append(f"{rel}: no facts block")
            continue
        new = text[:start] + block(lang, facts) + text[end + len(END):]
        if new != text:
            stale.append(rel)
            if not check:
                path.write_text(new, encoding="utf-8", newline="\n")
    if check:
        for rel in stale:
            print(f"stale: {rel} (run python tools/make_facts.py)")
        return 1 if stale else 0
    print(f"facts: {', '.join(f'{k} {v}' for k, v in facts.items())}")
    print(f"wrote {len(stale)} document(s)" if stale else "every block was up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
