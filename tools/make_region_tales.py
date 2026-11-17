#!/usr/bin/env python3
"""Writes the tales of the regions (spec 07, "Tales of the villagers"): the villagers of every region tell of a trouble of theirs, in two
quests, one after the other: `base:quest/side/tale_<region>_1` and `_2`, each a hunt of a creature of the region and a collection of what it
leaves, paid by the villager who is asked (the flags `tale_<region>_<n>_paid`).

It writes the quests and their texts, and changes the role dialogues of the villagers in place (the nodes written here are written again, so
the tool can be run any number of times). Then run `set_factions.py` (the tales count for the Folk) and `make_catalog.py`.
"""
from __future__ import annotations

import json

from make_towns import DATA, set_texts

# region: (tone, danger, [(enemy, kills, drop, count) for the first and the second tale])
REGIONS = {
    "verdalis": ("warm", 1, [("slime_mint", 5, "mint_leaf", 4), ("wolf_tawny", 6, "tawny_fur", 3)]),
    "whisperwood": ("mystic", 3, [("night_owl", 4, "owl_feather", 3), ("wisp", 4, "wisp_ember", 2)]),
    "ironspine": ("gruff", 4, [("slime_rust", 5, "rust_flake", 4), ("cave_bat", 6, "bat_wing", 3)]),
    "sunscar": ("flowery", 4, [("slime_amber", 5, "amber_drop", 4), ("dune_fox", 4, "fox_pelt", 3)]),
    "frostveil": ("stoic", 5, [("slime_ice", 5, "ice_crystal", 4), ("wolf_frost", 5, "frost_pelt", 3)]),
    "tidehaven": ("salty", 3, [("shore_crab", 5, "crab_shell", 4), ("slime_coral", 5, "coral_fragment", 3)]),
    "ashen_wastes": ("grim", 7, [("slime_char", 5, "char_chunk", 4), ("slime_magma", 5, "magma_shard", 3)]),
    "lumeria": ("scholarly", 5, [("slime_glow", 5, "star_dust", 4), ("wolf_storm", 4, "storm_feather", 3)]),
}
CHOICES = {
    "en": {"dlg.role.tale.ask": "You look worried. What is it?", "dlg.role.tale.status": "About your trouble...",
           "dlg.role.tale.report": "Your trouble is over.", "dlg.role.tale.accept": "Leave it to me.", "dlg.role.tale.later": "Another time."},
    "it": {"dlg.role.tale.ask": "Hai l'aria preoccupata. Che succede?", "dlg.role.tale.status": "A proposito del tuo problema...",
           "dlg.role.tale.report": "Il tuo problema è risolto.", "dlg.role.tale.accept": "Lascia fare a me.", "dlg.role.tale.later": "Un'altra volta."},
}
# tone: for each tale (offer, busy, thanks, quest name, journal); en then it
TALES = {
    "en": {
        "warm": [("The mint slimes have found my kitchen garden and they think the mint is theirs. Could you chase five of them off, and bring me back a little mint?",
                  "They're still in the garden, rolling in the mint. Bless them, but no.", "My garden smells of mint again instead of slime! Here, with my thanks, and a jar of jam.",
                  "Mint and mischief", "Chase the mint slimes from the kitchen gardens of Verdalis and bring back some mint."),
                 ("Now the tawny wolves howl at the edge of the fields every night and the children can't sleep. Six of them, and some fur for winter blankets?",
                  "Still howling. The children have started howling back, which is worse.", "Quiet nights at last! The whole street baked for you. And here's something from all of us.",
                  "A quiet night", "Hunt the tawny wolves that howl at the edge of the fields of Verdalis and bring back their fur.")],
        "mystic": [("The owls have stopped speaking to us. Four have gone strange and angry. Calm them, and bring three feathers: the trees will understand.",
                    "The owls are still silent. The trees wait.", "The owls speak again; they say your name. Take this, it was meant for you before you came.",
                    "When the owls fell silent", "Calm the night owls that have gone strange in Whisperwood and bring back their feathers."),
                   ("Wisps lead travellers from the paths. Four of them are too bright, too hungry. Put them out, and keep two embers for the lanterns of the shrine.",
                    "The wisps still lure. Mind your feet.", "The paths are honest again. The shrine burns your embers in your honour, quietly.",
                    "The lights that lie", "Put out the hungry wisps that lead travellers astray in Whisperwood and bring back their embers.")],
        "gruff": [("Rust slimes. In the tool shed. Eating the tools. Five of them. Bring the flakes, the smith can use them.",
                   "Shed's still full of slime.", "Tools are safe. Here. Don't spend it all on ale. Or do.",
                   "The tool shed", "Clear the rust slimes from the tool sheds of Ironspine and bring back the rust flakes."),
                  ("Bats in the mine shaft. Six. Can't work with them in your hair. Bring the wings, they make good glue.",
                   "Bats are still there. Still in my hair.", "Shaft's clear. Good work. You'd make a miner.",
                   "Bats in the shaft", "Drive the bats out of the mine shafts of Ironspine and bring back their wings.")],
        "flowery": [("Oh, the amber slimes have set upon my perfume garden, and every bloom tastes of resin! Five of them, I beg, and four drops of amber for my new scent!",
                     "Alas, the slimes still bathe in my roses!", "My garden breathes again, and my new perfume is named after you! Well, after your boots. Accept this, darling!",
                     "Resin in the roses", "Chase the amber slimes from the perfume gardens of Sunscar and bring back drops of amber."),
                    ("The dune foxes have stolen three silk scarves and an entire picnic! Four of the rascals, please, and three pelts for the winter market!",
                     "The foxes laugh at me from the dunes. Laugh!", "Avenged! The scarves are lost, but my honour is restored. And here is your reward, with kisses!",
                     "The picnic thieves", "Catch the dune foxes that rob the picnics of Sunscar and bring back their pelts.")],
        "stoic": [("Ice slimes in the well. Five. The water tastes of nothing. Bring four crystals.", "The well is still cold.", "The water is good. Thank you. This is yours.",
                   "The frozen well", "Clear the ice slimes from the wells of Frostveil and bring back ice crystals."),
                  ("Frost wolves near the sheds. Five. Bring three pelts. For the long winter.", "The wolves are still there.", "The sheds are safe. We will remember. This is yours.",
                   "Before the long winter", "Hunt the frost wolves near the sheds of Frostveil and bring back their pelts.")],
        "salty": [("Crabs, matey! Crabs in me nets! Five o' the clawed devils, an' bring four shells, the kids paint 'em.",
                   "Still crabs in the nets. Still pinchin'.", "Nets are clean an' the kids are paintin'! Here's yer share, shipmate.",
                   "Crabs in the nets", "Clear the crabs from the fishing nets of Tidehaven and bring back their shells."),
                  ("Coral slimes be growin' on me boat, an' now she's slower than a drunk turtle. Five of 'em, an' three bits o' coral for luck.",
                   "Boat's still crusty, matey.", "She flies again! Fastest hull in the harbour. Ye've earned this, an' a song in yer name.",
                   "The crusty hull", "Scrape the coral slimes off the boats of Tidehaven and bring back coral for luck.")],
        "grim": [("Char slimes in the grain store. Five. If the grain burns, we go hungry. Bring the char; it still burns, at least.",
                  "The store still smoulders.", "The grain is safe. For now. Take this. Eat something.",
                  "The grain store", "Clear the char slimes from the grain stores of the Ashen Wastes and bring back the char."),
                 ("Magma slimes are creeping toward the houses. Five. Bring three shards; the smith wants them.", "They are still creeping.", "The houses stand. Most of them. Thank you. Truly.",
                  "What creeps toward the houses", "Stop the magma slimes creeping toward the houses of the Ashen Wastes and bring back their shards.")],
        "scholarly": [("The glow slimes are interfering with my measurements of the night sky. Five would restore statistical significance. Four samples of star dust, please.",
                       "The measurements remain contaminated.", "Clean data! I shall cite you. Please accept this honorarium.",
                       "Contaminated measurements", "Clear the glow slimes that spoil the measurements of Lumeria and bring back star dust."),
                      ("Storm wolves keep knocking over my weathervanes, which is ironic and inconvenient. Four, and three feathers for the calibration.",
                       "The weathervanes are still on the ground.", "The vanes turn true again. A footnote is too small for this. Here.",
                       "The fallen weathervanes", "Hunt the storm wolves that knock over the weathervanes of Lumeria and bring back their feathers.")],
    },
    "it": {
        "warm": [("Le melme di menta hanno trovato il mio orto e pensano che la menta sia loro. Potresti cacciarne cinque e portarmi un po' di menta?",
                  "Sono ancora nell'orto, a rotolarsi nella menta. Care, ma no.", "Il mio orto profuma di nuovo di menta invece che di melma! Ecco, con la mia gratitudine e un vasetto di marmellata.",
                  "Menta e dispetti", "Caccia le melme di menta dagli orti di Verdalis e riporta un po' di menta."),
                 ("Adesso i lupi fulvi ululano ai margini dei campi ogni notte e i bambini non dormono. Sei lupi, e un po' di pelliccia per le coperte d'inverno?",
                  "Ululano ancora. I bambini hanno cominciato a ululare anche loro, che è peggio.", "Finalmente notti tranquille! Tutta la via ha sfornato per te. E questo è da parte di tutti.",
                  "Una notte tranquilla", "Caccia i lupi fulvi che ululano ai margini dei campi di Verdalis e riporta la loro pelliccia.")],
        "mystic": [("I gufi hanno smesso di parlarci. Quattro sono diventati strani e rabbiosi. Calmali, e porta tre piume: gli alberi capiranno.",
                    "I gufi tacciono ancora. Gli alberi aspettano.", "I gufi parlano di nuovo; dicono il tuo nome. Prendi questo, era destinato a te prima che arrivassi.",
                    "Quando i gufi tacquero", "Calma i gufi notturni diventati strani nel Bosco dei Sussurri e riporta le loro piume."),
                   ("I fuochi fatui portano i viandanti fuori dai sentieri. Quattro sono troppo luminosi, troppo affamati. Spegnili, e tieni due braci per le lanterne del santuario.",
                    "I fuochi attirano ancora. Attento a dove metti i piedi.", "I sentieri sono di nuovo onesti. Il santuario brucia le tue braci in tuo onore, in silenzio.",
                    "Le luci che mentono", "Spegni i fuochi fatui affamati che sviano i viandanti nel Bosco dei Sussurri e riporta le loro braci.")],
        "gruff": [("Melme di ruggine. Nel capanno degli attrezzi. Si mangiano gli attrezzi. Cinque. Porta le scaglie, al fabbro servono.",
                   "Il capanno è ancora pieno di melma.", "Gli attrezzi sono salvi. Ecco. Non spenderli tutti in birra. O sì.",
                   "Il capanno degli attrezzi", "Libera i capanni degli attrezzi della Dorsale di Ferro dalle melme di ruggine e riporta le scaglie."),
                  ("Pipistrelli nel pozzo della miniera. Sei. Non si lavora con quelli nei capelli. Porta le ali, fanno buona colla.",
                   "I pipistrelli sono ancora lì. Ancora nei miei capelli.", "Il pozzo è libero. Buon lavoro. Saresti un buon minatore.",
                   "Pipistrelli nel pozzo", "Scaccia i pipistrelli dai pozzi delle miniere della Dorsale di Ferro e riporta le loro ali.")],
        "flowery": [("Oh, le melme d'ambra hanno assalito il mio giardino dei profumi, e ogni fiore sa di resina! Cinque, ti supplico, e quattro gocce d'ambra per il mio nuovo profumo!",
                     "Ahimè, le melme fanno ancora il bagno tra le mie rose!", "Il mio giardino respira di nuovo, e il mio nuovo profumo porta il tuo nome! Be', quello dei tuoi stivali. Accetta questo, tesoro!",
                     "Resina tra le rose", "Caccia le melme d'ambra dai giardini dei profumi della Cicatrice del Sole e riporta gocce d'ambra."),
                    ("Le volpi delle dune hanno rubato tre sciarpe di seta e un picnic intero! Quattro di quelle birbanti, per favore, e tre pellicce per il mercato d'inverno!",
                     "Le volpi ridono di me dalle dune. Ridono!", "Vendicata! Le sciarpe sono perse, ma il mio onore è salvo. Ed ecco la tua ricompensa, con baci!",
                     "I ladri del picnic", "Prendi le volpi delle dune che derubano i picnic della Cicatrice del Sole e riporta le loro pellicce.")],
        "stoic": [("Melme di ghiaccio nel pozzo. Cinque. L'acqua non sa di niente. Porta quattro cristalli.", "Il pozzo è ancora freddo.", "L'acqua è buona. Grazie. Questo è tuo.",
                   "Il pozzo gelato", "Libera i pozzi del Velo di Gelo dalle melme di ghiaccio e riporta cristalli di ghiaccio."),
                  ("Lupi del gelo vicino ai capanni. Cinque. Porta tre pellicce. Per il lungo inverno.", "I lupi sono ancora lì.", "I capanni sono al sicuro. Ce ne ricorderemo. Questo è tuo.",
                   "Prima del lungo inverno", "Caccia i lupi del gelo vicino ai capanni del Velo di Gelo e riporta le loro pellicce.")],
        "salty": [("Granchi, mozzo! Granchi nelle mie reti! Cinque di quei diavoli con le chele, e porta quattro gusci, i ragazzi li dipingono.",
                   "Ancora granchi nelle reti. Ancora pizzicano.", "Reti pulite e i ragazzi dipingono! Ecco la tua parte, compagno.",
                   "Granchi nelle reti", "Libera le reti da pesca del Porto della Marea dai granchi e riporta i loro gusci."),
                  ("Le melme di corallo crescono sulla mia barca, e ora è più lenta di una tartaruga ubriaca. Cinque, e tre pezzi di corallo per fortuna.",
                   "La barca è ancora incrostata, mozzo.", "Vola di nuovo! Lo scafo più veloce del porto. Te lo sei guadagnato, e una canzone col tuo nome.",
                   "Lo scafo incrostato", "Raschia via le melme di corallo dalle barche del Porto della Marea e riporta corallo per fortuna.")],
        "grim": [("Melme di carbone nel granaio. Cinque. Se il grano brucia, facciamo la fame. Porta il carbone; almeno brucia ancora.",
                  "Il granaio cova ancora.", "Il grano è salvo. Per ora. Prendi questo. Mangia qualcosa.",
                  "Il granaio", "Libera i granai delle Terre di Cenere dalle melme di carbone e riporta il carbone."),
                 ("Le melme di magma strisciano verso le case. Cinque. Porta tre schegge; il fabbro le vuole.", "Strisciano ancora.", "Le case sono in piedi. Quasi tutte. Grazie. Davvero.",
                  "Ciò che striscia verso le case", "Ferma le melme di magma che strisciano verso le case delle Terre di Cenere e riporta le loro schegge.")],
        "scholarly": [("Le melme luminose interferiscono con le mie misure del cielo notturno. Cinque ristabilirebbero la significatività statistica. Quattro campioni di polvere di stelle, prego.",
                       "Le misure restano contaminate.", "Dati puliti! Ti citerò. Accetta questo onorario.",
                       "Misure contaminate", "Libera Lumeria dalle melme luminose che rovinano le misure e riporta polvere di stelle."),
                      ("I lupi della tempesta continuano a rovesciarmi le banderuole, il che è ironico e scomodo. Quattro, e tre piume per la taratura.",
                       "Le banderuole sono ancora per terra.", "Le banderuole girano di nuovo giuste. Una nota a piè di pagina è troppo poco. Ecco.",
                       "Le banderuole cadute", "Caccia i lupi della tempesta che rovesciano le banderuole di Lumeria e riporta le loro piume.")],
    },
}


def write_json(path, doc, like: str | None = None) -> None:
    newline = "\r\n" if like is not None and "\r\n" in like else "\n"
    path.write_text((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").replace("\n", newline), encoding="utf-8", newline="")


def quest_id(region: str, n: int) -> str:
    return f"base:quest/side/tale_{region}_{n}"


def patch_villager(region: str, tone: str, danger: int) -> None:
    path = DATA / "dialogues" / "role" / f"villager_{tone}.json"
    raw = path.read_text(encoding="utf-8", newline="")
    doc = json.loads(raw)
    nodes = doc["nodes"]
    mine = {"tale_offer_1", "tale_offer_2", "tale_busy_1", "tale_busy_2", "tale_paid_1", "tale_paid_2"}
    choices = [c for c in nodes["menu"]["choices"] if c.get("next") not in mine]
    added = []
    for n in (1, 2):
        q = quest_id(region, n)
        paid = f"tale_{region}_{n}_paid"
        untouched = {"not": {"any": [{"quest_active": q}, {"quest_done": q}]}}
        offer_when = untouched if n == 1 else {"all": [{"flag": f"tale_{region}_1_paid"}, untouched]}
        added += [{"text": "$i18n:dlg.role.tale.ask", "when": offer_when, "next": f"tale_offer_{n}"},
                  {"text": "$i18n:dlg.role.tale.status", "when": {"quest_active": q}, "next": f"tale_busy_{n}"},
                  {"text": "$i18n:dlg.role.tale.report", "when": {"all": [{"quest_done": q}, {"not": {"flag": paid}}]}, "next": f"tale_paid_{n}"}]
        nodes[f"tale_offer_{n}"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.tale.{tone}.offer_{n}", "next": f"tale_choice_{n}"}
        nodes[f"tale_choice_{n}"] = {"type": "choice", "choices": [
            {"text": "$i18n:dlg.role.tale.accept", "effects": [{"effect": "start_quest", "quest": q}], "next": "end"},
            {"text": "$i18n:dlg.role.tale.later", "next": "end"}]}
        nodes[f"tale_busy_{n}"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.tale.{tone}.busy_{n}", "next": "end"}
        nodes[f"tale_paid_{n}"] = {"type": "effects", "next": f"tale_thanks_{n}", "effects": [
            {"effect": "set_flag", "flag": paid, "value": True}, {"effect": "add_xp", "amount": (60 + 30 * n) * danger},
            {"effect": "add_gold", "amount": 100 + 60 * n * danger}, {"effect": "add_item", "item": "base:item/potion_medium", "qty": n}]}
        nodes[f"tale_thanks_{n}"] = {"type": "say", "speaker": "npc", "text": f"$i18n:dlg.tale.{tone}.thanks_{n}", "next": "end"}
    nodes["menu"]["choices"] = added + choices
    write_json(path, doc, raw)


def main() -> None:
    texts = {lang: dict(CHOICES[lang]) for lang in ("en", "it")}
    content = {"en": {}, "it": {}}
    for region, (tone, danger, tales) in REGIONS.items():
        for n, (enemy, kills, drop, count) in enumerate(tales, start=1):
            quest = {"$schema": "../../../../schemas/quest.schema.json", "id": quest_id(region, n), "name": f"$i18n:quest.tale_{region}_{n}.name",
                     "kind": "side", "stages": [{"id": "hunt", "journal": f"$i18n:quest.tale_{region}_{n}.hunt", "objectives": [
                         {"type": "kill", "enemy": f"base:enemy/{enemy}", "count": kills},
                         {"type": "collect", "item": f"base:item/{drop}", "count": count}], "next": "end"}], "rewards": []}
            write_json(DATA / "quests" / "side" / f"tale_{region}_{n}.json", quest)
        patch_villager(region, tone, danger)
        for lang in ("en", "it"):
            for n, (offer, busy, thanks, name, journal) in enumerate(TALES[lang][tone], start=1):
                texts[lang].update({f"dlg.tale.{tone}.offer_{n}": offer, f"dlg.tale.{tone}.busy_{n}": busy, f"dlg.tale.{tone}.thanks_{n}": thanks})
                content[lang].update({f"quest.tale_{region}_{n}.name": name, f"quest.tale_{region}_{n}.hunt": journal})
    for lang in ("en", "it"):
        set_texts("roles.json", lang, texts[lang])
        set_texts("content.json", lang, content[lang])
    __import__("set_factions").main()  # the tales count for the Folk (spec 07, "Factions")
    print(f"wrote {2 * len(REGIONS)} tales of the regions")


if __name__ == "__main__":
    main()
