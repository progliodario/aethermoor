#!/usr/bin/env python3
"""Writes the companions of the base pack (data/base/companions/), their names, and gives each protagonist theirs. Spec 10.
Run it after changing the table here."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "base"

# Care (spec 10): from this bond on, every companion heals the player now and then (ten seconds, 5% of the health).
CARE_BOND, CARE_TICKS, CARE_PCT = 10, 600, 5
# The duo strike (spec 10): after twenty kills together, a power strike near the companion brings its hit, three times its attack, every
# ten seconds.
DUO = {"duo_bond": 20, "duo_pct": 300, "duo_range_x100": 400, "duo_cooldown_ticks": 600}

# companion: (protagonist, creature art, name en, name it, atk_base, atk_per_level, range_x100, cooldown_ticks, speed_x100, scale_pct)
COMPANIONS = {
    "orb": ("ren", "wisp", "Orb", "Orbe", 7, 1, 350, 110, 330, 70),
    "newton": ("sakura", "night_owl", "Newton", "Newton", 8, 1, 400, 100, 340, 70),
    "ember": ("daichi", "wolf_tawny", "Ember", "Brace", 10, 1, 250, 90, 360, 60),
    "pip": ("haruka", "slime_mint", "Pip", "Pip", 6, 1, 200, 80, 320, 90),
    "pot": ("marco", "shore_crab", "Pot", "Pentola", 9, 1, 220, 100, 300, 80),
    "shade": ("yuki", "cave_bat", "Shade", "Ombra", 9, 1, 300, 75, 380, 80),
    "mort": ("lena", "cave_spider", "Mort", "Mortina", 8, 1, 280, 85, 340, 80),
    "gloom": ("gideon", "wolf_shade", "Gloom", "Tenebra", 11, 1, 300, 90, 360, 60),
}


# Moments of the bond (spec 10, "Moments of the bond"): at these bonds the companion shows what it feels, once a game.
MOMENT_BONDS = (5, 15, 30)
MOMENTS = {  # companion: (en, it) for each bond of MOMENT_BONDS
    "orb": (("Orb blinks twice. In wisp, that is a whole sentence.", "Orbe lampeggia due volte. In lingua di fuoco fatuo è una frase intera."),
            ("Orb drifts a little closer to you than before, as if you were the warm one.", "Orbe ti fluttua un po' più vicino di prima, come se il caldo fossi tu."),
            ("Orb glows the colour of your eyes. It will not leave you now.", "Orbe brilla del colore dei tuoi occhi. Ormai non ti lascerà più.")),
    "newton": (("Newton hoots once, precisely, as if correcting your arithmetic.", "Newton fa un solo verso, preciso, come se correggesse i tuoi conti."),
               ("Newton brings you a feather of a creature you defeated. A gift, or a specimen.", "Newton ti porta una piuma di una creatura sconfitta. Un dono, o un campione."),
               ("Newton sleeps on your shoulder, one eye open, guarding you.", "Newton dorme sulla tua spalla, un occhio aperto, a farti la guardia.")),
    "ember": (("Ember sniffs your hand and decides you smell like home.", "Brace ti annusa la mano e decide che sai di casa."),
              ("Ember walks between you and every shadow now.", "Brace ora cammina tra te e ogni ombra."),
              ("Ember howls at the sky, and somewhere far away the other wolves answer.", "Brace ulula al cielo, e da qualche parte lontano gli altri lupi rispondono.")),
    "pip": (("Pip bounces twice. That means yes. To everything.", "Pip rimbalza due volte. Vuol dire sì. A tutto."),
            ("Pip tries to share its lunch with you. Its lunch is a leaf. It insists.", "Pip prova a dividere il pranzo con te. Il pranzo è una foglia. Insiste."),
            ("Pip falls asleep on your boot, glowing softly. Nothing in the world is safer.", "Pip si addormenta sul tuo stivale, brillando piano. Niente al mondo è più al sicuro.")),
    "pot": (("Pot clicks its claws in a rhythm. It might be a recipe.", "Pentola fa schioccare le chele a ritmo. Potrebbe essere una ricetta."),
            ("Pot guards the campfire while you cook, and takes only a small taste.", "Pentola fa la guardia al falò mentre cucini, e assaggia solo un po'."),
            ("Pot climbs into your bag and refuses to leave. You let it.", "Pentola si arrampica nello zaino e si rifiuta di uscire. Lo lasci fare.")),
    "shade": (("Shade hangs from your sleeve for a moment, then pretends it didn't.", "Ombra si appende alla tua manica per un attimo, poi fa finta di niente."),
              ("Shade squeaks a warning before you even see the creature.", "Ombra squittisce un avvertimento prima ancora che tu veda la creatura."),
              ("Shade sleeps folded in your hood. In the dark it is your second pair of eyes.", "Ombra dorme piegata nel tuo cappuccio. Al buio è il tuo secondo paio d'occhi.")),
    "mort": (("Mort taps your boot with one leg. A greeting, clinically speaking.", "Mortina ti tocca lo stivale con una zampa. Un saluto, in termini clinici."),
             ("Mort spins a tiny bandage of silk and leaves it on your wound.", "Mortina tesse una minuscola benda di seta e la lascia sulla tua ferita."),
             ("Mort has written your name in its web. Spiders do not do that for anyone.", "Mortina ha scritto il tuo nome nella sua tela. I ragni non lo fanno per nessuno.")),
    "gloom": (("Gloom bows its head when you pass. Old habits of a court.", "Tenebra china il capo quando passi. Vecchie abitudini di corte."),
              ("Gloom growls at the dark itself, on your behalf.", "Tenebra ringhia al buio stesso, per conto tuo."),
              ("Gloom lies at your feet like a throne's shadow. Its loyalty is not for sale.", "Tenebra si stende ai tuoi piedi come l'ombra di un trono. La sua lealtà non è in vendita.")),
}


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def add_texts(lang: str, entries: dict[str, str]) -> None:
    path = DATA / "i18n" / lang / "content.json"
    raw = path.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    existing = {line.split('"')[1] for line in lines if line.startswith('  "')}
    anchor = max(k for k, line in enumerate(lines) if line.startswith('  "item.'))
    for key, value in entries.items():
        if key in existing:
            continue
        anchor += 1
        lines.insert(anchor, f'  "{key}": {json.dumps(value, ensure_ascii=False)},')
    path.write_text(newline.join(lines), encoding="utf-8", newline="")


def main() -> None:
    en: dict[str, str] = {}
    it: dict[str, str] = {}
    for name, (who, art, name_en, name_it, atk, per_level, reach, cooldown, speed, scale) in COMPANIONS.items():
        write_json(DATA / "companions" / f"{name}.json", {
            "$schema": "../../../schemas/companion.schema.json", "id": f"base:companion/{name}", "name": f"$i18n:companion.{name}.name",
            "art": f"base:art/creature/{art}", "scale_pct": scale, "atk_base": atk, "atk_per_level": per_level, "range_x100": reach,
            "cooldown_ticks": cooldown, "speed_x100": speed, "follow_x100": 220, "care_bond": CARE_BOND, "care_ticks": CARE_TICKS, "care_pct": CARE_PCT, **DUO,
            "moments": [{"bond": bond, "text": f"$i18n:companion.{name}.moment_{bond}"} for bond in MOMENT_BONDS]})
        for bond, (line_en, line_it) in zip(MOMENT_BONDS, MOMENTS[name]):
            en[f"companion.{name}.moment_{bond}"], it[f"companion.{name}.moment_{bond}"] = line_en, line_it
        en[f"companion.{name}.name"], it[f"companion.{name}.name"] = name_en, name_it
        path = DATA / "protagonists" / f"{who}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["companion"] = f"base:companion/{name}"
        write_json(path, doc)
    add_texts("en", en)
    add_texts("it", it)
    print(f"wrote {len(COMPANIONS)} companions")


if __name__ == "__main__":
    main()
