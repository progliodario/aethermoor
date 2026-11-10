"""The named people of the eight outposts, one each beside the wayfarer: the table that `make_towns.py` adds to Fenwick and Aldermere.

Same shape as `make_towns.PEOPLE`. Each person gives two quests about their region (its creatures and what they leave), with rewards that grow with
the danger of the region. The tile is a free cobblestone of the outpost's plaza (checked by `tools/tests/test_content.py`)."""
from __future__ import annotations


def _quest(qid, name, task, objectives, xp, gold, items, offer, busy, thanks):
    return {"id": qid, "name": name, "task": task, "objectives": objectives,
            "rewards": {"xp": xp, "gold": gold, "points": xp // 20, "items": items}, "offer": offer, "busy": busy, "thanks": thanks}


def _kill(enemy, count):
    return {"type": "kill", "enemy": f"base:enemy/{enemy}", "count": count}


def _collect(item, count):
    return {"type": "collect", "item": f"base:item/{item}", "count": count}


OUTPOST_PEOPLE = [
    {
        "key": "outpost_carter_pell", "file": "pell", "variant": "brown", "dx": 385, "dy": 127,
        "name": ("Pell, carter of the Crossroads", "Pell, carrettiere del Crocevia"),
        "after": ("The roads are clear and my mules are fat. Life is simple at a crossroads, when someone like you passes.", "Le strade sono libere e i miei muli sono grassi. La vita è semplice a un crocevia, quando ci passa uno come te."),
        "quests": [
            _quest("crossroads_mint", ("Mint in the Wheels", "Menta nelle ruote"), ("Mint slimes clog the wheels of Pell's carts at the Crossroads Camp. Clear them out and bring some leaves.", "Gli slime alla menta intasano le ruote dei carri di Pell al Campo del Crocevia. Scacciali e porta qualche foglia."),
                   [_kill("slime_mint", 8), _collect("mint_leaf", 4)], 120, 150, {"base:item/potion_small": 3},
                   ("Every morning my wheels are green and sticky. Mint slimes. They love a slow cart. Would you thin them out?", "Ogni mattina le mie ruote sono verdi e appiccicose. Slime alla menta. Adorano i carri lenti. Li sfoltiresti?"),
                   ("Eight mint slimes, four leaves. The mules thank you in advance.", "Otto slime alla menta, quattro foglie. I muli ringraziano in anticipo."),
                   ("Clean wheels! And the leaves make a tea my mules will not touch. More for me.", "Ruote pulite! E le foglie fanno una tisana che i muli non toccano. Più per me.")),
            _quest("crossroads_wolves", ("Escort Duty", "Di scorta"), ("Tawny wolves follow Pell's carts out of the Crossroads. Drive them off and bring their fur.", "I lupi fulvi seguono i carri di Pell fuori dal Crocevia. Allontanali e porta la loro pelliccia."),
                   [_kill("wolf_tawny", 6), _collect("tawny_fur", 3)], 180, 220, {"base:item/leather_vest": 1},
                   ("The wolves have learned my timetable. I have not learned theirs. You look like someone who could teach them a new one.", "I lupi hanno imparato i miei orari. Io i loro no. Hai l'aria di chi potrebbe insegnargliene di nuovi."),
                   ("Six tawny wolves, three furs.", "Sei lupi fulvi, tre pellicce."),
                   ("The tanner at Fenwick made this from the furs. It smells of road. All the best things do.", "Il conciatore di Fenwick ci ha fatto questa, con le pellicce. Sa di strada. Le cose migliori sanno di strada.")),
        ],
    },
    {
        "key": "outpost_herbalist_wren", "file": "wren", "variant": "green", "dx": -4222, "dy": -2689,
        "name": ("Wren, herbalist of Hollow's Edge", "Wren, erborista di Hollow's Edge"),
        "after": ("My shelves are full, and the wood is kinder. Come back when you are hurt; I will not charge a Guest.", "I miei scaffali sono pieni, e il bosco è più gentile. Torna quando sei ferito: a un Ospite non faccio pagare."),
        "quests": [
            _quest("whisperwood_spores", ("Spores for Salves", "Spore per gli unguenti"), ("Wren needs spore caps from the myconids of Whisperwood for her salves.", "A Wren servono cappelle di spore dai miconidi di Whisperwood per i suoi unguenti."),
                   [_kill("myconid", 6), _collect("spore_cap", 4)], 360, 450, {"base:item/potion_medium": 3},
                   ("The mushroom folk keep the best medicine on their heads, and they will not share it. I am too slow to argue with them. You are not.", "I funghi tengono la medicina migliore sulla testa, e non la dividono. Io sono troppo lenta per discutere con loro. Tu no."),
                   ("Six myconids, four caps. Mind the spores; they make you sneeze for a week.", "Sei miconidi, quattro cappelle. Attento alle spore: fanno starnutire per una settimana."),
                   ("Perfect caps. Here, potions from last season's batch; they are better than they look.", "Cappelle perfette. Tieni, pozioni dell'ultima infornata: sono meglio di quanto sembrino.")),
            _quest("whisperwood_silk", ("Silk for Bandages", "Seta per le bende"), ("The spiders of Whisperwood spin the best bandages in the world. Bring Wren their silk.", "I ragni di Whisperwood tessono le bende migliori del mondo. Porta a Wren la loro seta."),
                   [_kill("cave_spider", 6), _collect("spider_silk", 4)], 540, 680, {"base:item/wisp_mantle": 1},
                   ("Spider silk closes a wound like nothing else. Getting it is the part I leave to others.", "La seta di ragno chiude una ferita come nient'altro. Procurarla è la parte che lascio agli altri."),
                   ("Six spiders, four silk.", "Sei ragni, quattro di seta."),
                   ("Enough bandages for a war, and no war to use them on, thanks to people like you. Take this mantle; the wisps wove it.", "Bende per una guerra, e nessuna guerra in cui usarle, grazie a quelli come te. Prendi questo mantello: l'hanno tessuto i fuochi fatui.")),
        ],
    },
    {
        "key": "outpost_cook_brakka", "file": "brakka", "variant": "ochre", "dx": 4226, "dy": -4737,
        "name": ("Brakka, cook of the Waystation", "Brakka, cuoca della Stazione"),
        "after": ("The miners eat like kings now. Kings with very dirty hands. Sit, there is always a bowl for you.", "I minatori ora mangiano come re. Re con le mani sporchissime. Siediti, c'è sempre una scodella per te."),
        "quests": [
            _quest("ironspine_rust", ("Rust in the Soup", "Ruggine nella zuppa"), ("Rust slimes have crept into the Waystation's kitchen. Clear them out of Ironspine and bring back their flakes.", "Gli slime di ruggine si sono infilati nella cucina della Stazione. Scacciali da Ironspine e riporta le loro scaglie."),
                   [_kill("slime_rust", 8), _collect("rust_flake", 4)], 480, 600, {"base:item/hearty_stew": 3},
                   ("There is rust in my soup, Guest. Not a little. A slime. Again. Get them out of my mountain and I will feed you until you cannot move.", "C'è ruggine nella mia zuppa, Ospite. Non un po'. Uno slime. Di nuovo. Cacciali dalla mia montagna e ti sfamo finché non riesci a muoverti."),
                   ("Eight rust slimes, four flakes. I want to see the flakes. I want to be sure.", "Otto slime di ruggine, quattro scaglie. Voglio vedere le scaglie. Voglio esserne sicura."),
                   ("Every last one. Sit. Eat. Do not argue with the cook.", "Fino all'ultimo. Siediti. Mangia. Non si discute con la cuoca.")),
            _quest("ironspine_golems", ("A Better Oven", "Un forno migliore"), ("Brakka wants golem cores to build an oven that never goes out. The stone golems of Ironspine carry them.", "Brakka vuole nuclei di golem per costruire un forno che non si spegne mai. Li portano i golem di pietra di Ironspine."),
                   [_kill("stone_golem", 3), _collect("golem_core", 2)], 720, 900, {"base:item/slate_cleaver": 1},
                   ("A golem's core stays warm for a hundred years. Two of them, and I never light a fire again. Bring me two.", "Il nucleo di un golem resta caldo per cent'anni. Con due, non accendo mai più un fuoco. Portamene due."),
                   ("Three golems, two cores. They are slow, but they hit like a landslide.", "Tre golem, due nuclei. Sono lenti, ma colpiscono come una frana."),
                   ("The oven hums. The bread is perfect. Take this cleaver; I used it for meat, but you will find better uses.", "Il forno ronza. Il pane è perfetto. Prendi questa mannaia: io la usavo per la carne, tu troverai usi migliori.")),
        ],
    },
    {
        "key": "outpost_netmender_nella", "file": "nella", "variant": "teal", "dx": -6271, "dy": 4225,
        "name": ("Nella, net-mender of Brinewatch", "Nella, rammendatrice di reti di Brinewatch"),
        "after": ("The nets come up full and whole. The sea is still the sea, but it has learned some manners.", "Le reti tornano su piene e intere. Il mare resta il mare, ma ha imparato un po' di educazione."),
        "quests": [
            _quest("tidehaven_crabs", ("Cut Nets", "Reti tagliate"), ("Shore crabs cut the nets of Brinewatch every night. Teach eight of them otherwise and bring their shells.", "I granchi di riva tagliano le reti di Brinewatch ogni notte. Insegna a otto di loro a smettere e porta i gusci."),
                   [_kill("shore_crab", 8), _collect("crab_shell", 4)], 360, 450, {"base:item/fish_stew": 3},
                   ("Every morning, a hole. Every hole, a crab. I mend all day and they cut all night. One of us must stop, and it will not be me.", "Ogni mattina un buco. Ogni buco, un granchio. Io rammendo tutto il giorno e loro tagliano tutta la notte. Uno dei due deve smettere, e non sarò io."),
                   ("Eight crabs, four shells.", "Otto granchi, quattro gusci."),
                   ("Whole nets! I had forgotten what they look like. Stew, from the first catch.", "Reti intere! Avevo dimenticato com'erano. Zuppa, dalla prima pesca.")),
            _quest("tidehaven_coral", ("Coral Weights", "Pesi di corallo"), ("Nella weights her best nets with coral. The coral slimes of Tidehaven carry the right kind.", "Nella appesantisce le reti migliori col corallo. Gli slime di corallo di Tidehaven portano quello giusto."),
                   [_kill("slime_coral", 6), _collect("coral_fragment", 3)], 540, 680, {"base:item/coralweave_vest": 1},
                   ("Coral sinks a net straight and true. The slimes wear the best of it. They will not mind; they will not be anything any more.", "Il corallo fa scendere una rete dritta e precisa. Gli slime ne portano il migliore. Non se ne avranno a male: non saranno più niente."),
                   ("Six coral slimes, three fragments.", "Sei slime di corallo, tre frammenti."),
                   ("I wove the leftovers into a vest. It is the first thing I ever made that is not a net. Wear it.", "Con gli avanzi ho tessuto un gilet. È la prima cosa che faccio che non sia una rete. Indossalo.")),
        ],
    },
    {
        "key": "outpost_sculptor_henrik", "file": "henrik", "variant": "cream", "dx": -1151, "dy": -6529,
        "name": ("Old Henrik, ice-sculptor of Rimewatch", "Il vecchio Henrik, scultore del ghiaccio di Rimewatch"),
        "after": ("I carved you, you know. In ice, beside the door. You will melt in spring, but so will everything.", "Ti ho scolpito, sai. Nel ghiaccio, accanto alla porta. In primavera ti scioglierai, ma così tutto."),
        "quests": [
            _quest("frostveil_ice", ("Clear Ice", "Ghiaccio limpido"), ("Henrik carves only the clearest ice, and the ice slimes of Frostveil hoard it. Bring him crystals.", "Henrik scolpisce solo il ghiaccio più limpido, e gli slime di ghiaccio di Frostveil lo accumulano. Portagli dei cristalli."),
                   [_kill("slime_ice", 8), _collect("ice_crystal", 4)], 600, 750, {"base:item/potion_large": 2},
                   ("Lake ice is cloudy. River ice is cracked. The slimes keep the clear stuff inside, like a secret. I am too old to ask them for it.", "Il ghiaccio del lago è torbido. Quello del fiume è crepato. Gli slime tengono quello limpido dentro, come un segreto. Sono troppo vecchio per chiederglielo."),
                   ("Eight ice slimes, four crystals.", "Otto slime di ghiaccio, quattro cristalli."),
                   ("Look how the light goes through them. I will carve a swan. No, a Guest. No, a swan.", "Guarda come li attraversa la luce. Scolpirò un cigno. No, un Ospite. No, un cigno.")),
            _quest("frostveil_polar", ("A Warm Coat for an Old Man", "Un cappotto caldo per un vecchio"), ("Henrik's coat is older than he is. The polar wolves of Frostveil would make a better one.", "Il cappotto di Henrik è più vecchio di lui. I lupi polari di Frostveil ne farebbero uno migliore."),
                   [_kill("wolf_polar", 5), _collect("polar_fur", 3)], 900, 1100, {"base:item/frostfur_coat": 1},
                   ("Eighty winters in this coat. It has holes in places I did not know a coat had. Polar fur, Guest. Three should do.", "Ottanta inverni in questo cappotto. Ha buchi in posti che non sapevo un cappotto avesse. Pelliccia polare, Ospite. Tre bastano."),
                   ("Five polar wolves, three furs.", "Cinque lupi polari, tre pellicce."),
                   ("The tailor made two, the fool. One is yours. Do not argue with an old man in a new coat.", "Il sarto ne ha fatti due, lo sciocco. Uno è tuo. Non discutere con un vecchio in un cappotto nuovo.")),
        ],
    },
    {
        "key": "outpost_waterseller_farid", "file": "farid", "variant": "purple", "dx": 5505, "dy": 3969,
        "name": ("Farid, water-seller of the Caravanserai", "Farid, venditore d'acqua del Caravanserraglio"),
        "after": ("The caravans come and go and nobody is stung. Business is good, and so, I suspect, are you.", "Le carovane vanno e vengono e nessuno viene punto. Gli affari vanno bene, e anche tu, sospetto."),
        "quests": [
            _quest("sunscar_scorpions", ("Stings in the Water", "Pungiglioni nell'acqua"), ("Dune scorpions nest by the wells of Sunscar. Drive six away and bring Farid their stings, for the apothecary.", "Gli scorpioni delle dune fanno il nido vicino ai pozzi di Sunscar. Allontanane sei e porta a Farid i pungiglioni, per lo speziale."),
                   [_kill("dune_scorpion", 6), _collect("scorpion_sting", 3)], 480, 600, {"base:item/potion_medium": 3},
                   ("Three wells, three nests of scorpions. A water-seller with no water to sell is a man with a very heavy cart. Help me.", "Tre pozzi, tre nidi di scorpioni. Un venditore d'acqua senza acqua da vendere è un uomo con un carro molto pesante. Aiutami."),
                   ("Six scorpions, three stings. The apothecary pays well for them.", "Sei scorpioni, tre pungiglioni. Lo speziale li paga bene."),
                   ("The wells are mine again. Drink, Guest, as much as you like. For you, it is free. Today.", "I pozzi sono di nuovo miei. Bevi, Ospite, quanto vuoi. Per te è gratis. Oggi.")),
            _quest("sunscar_dunes", ("The Dune Pack", "Il branco delle dune"), ("The dune wolves of Sunscar raid the caravans at dusk. Break the pack and bring their pelts.", "I lupi delle dune di Sunscar assaltano le carovane al tramonto. Spezza il branco e porta le loro pelli."),
                   [_kill("wolf_dune", 6), _collect("dune_pelt", 3)], 720, 900, {"base:item/amber_plate": 1},
                   ("At dusk they come, from the colour of the sand. You see them when they bite. I would like to see them when they are gone.", "Al tramonto arrivano, del colore della sabbia. Li vedi quando mordono. Vorrei vederli quando se ne sono andati."),
                   ("Six dune wolves, three pelts.", "Sei lupi delle dune, tre pelli."),
                   ("The caravan masters took up a collection. It bought this. They argued for an hour about who would carry it to you.", "I capi carovana hanno fatto una colletta. Ci hanno comprato questa. Hanno discusso per un'ora su chi dovesse portartela.")),
        ],
    },
    {
        "key": "outpost_stargazer_astra", "file": "astra", "variant": "purple", "dx": -639, "dy": 6271,
        "name": ("Astra, stargazer of Lantern Rest", "Astra, astronoma di Lantern Rest"),
        "after": ("I have named a star after you. A small one. It was the best I could do; the big ones are taken.", "Ti ho dedicato una stella. Una piccola. È il meglio che ho potuto: le grandi sono tutte prese."),
        "quests": [
            _quest("lumeria_glow", ("Star Dust", "Polvere di stelle"), ("Astra grinds lenses with star dust, and the glow slimes of Lumeria carry it.", "Astra leviga le lenti con la polvere di stelle, e la portano gli slime luminosi di Lumeria."),
                   [_kill("slime_glow", 8), _collect("star_dust", 4)], 600, 750, {"base:item/potion_mana_medium": 3},
                   ("My lens is scratched and the sky is blurred. Star dust polishes it; the glow slimes are full of it. You do the hard part, I will do the polishing.", "La mia lente è graffiata e il cielo è sfocato. La polvere di stelle la lucida: gli slime luminosi ne sono pieni. Tu fai la parte difficile, io lucido."),
                   ("Eight glow slimes, four of star dust.", "Otto slime luminosi, quattro di polvere di stelle."),
                   ("Clear as a winter night. I can see a moon I did not know we had.", "Limpida come una notte d'inverno. Vedo una luna che non sapevo avessimo.")),
            _quest("lumeria_storm", ("Calm Skies", "Cieli calmi"), ("Astra cannot see the stars through the storms. The storm wolves of Lumeria feed them; ground five.", "Astra non vede le stelle attraverso le tempeste. Le alimentano i lupi della tempesta di Lumeria: abbattine cinque."),
                   [_kill("wolf_storm", 5), _collect("storm_feather", 3)], 900, 1100, {"base:item/starlit_vestment": 1},
                   ("Every night a storm, and every storm a howl. The wolves bring the clouds, I am sure of it. Take away the wolves, I keep the stars.", "Ogni notte una tempesta, e ogni tempesta un ululato. I lupi portano le nuvole, ne sono certa. Togli i lupi, io mi tengo le stelle."),
                   ("Five storm wolves, three feathers.", "Cinque lupi della tempesta, tre piume."),
                   ("A clear sky, at last, and you in it, counting with me. This robe was sewn for an astronomer. You count well enough.", "Un cielo sereno, finalmente, e tu sotto a contare con me. Questa veste fu cucita per un astronomo. Tu conti abbastanza bene.")),
        ],
    },
    {
        "key": "outpost_smith_grael", "file": "grael", "variant": "red", "dx": 6786, "dy": -385,
        "name": ("Grael, smith of Ember Watch", "Grael, fabbro di Ember Watch"),
        "after": ("The forge burns clean and so does the land, almost. I have never had so little to do. It is terrible. It is wonderful.", "La forgia brucia pulita e anche la terra, quasi. Non ho mai avuto così poco da fare. È terribile. È meraviglioso."),
        "quests": [
            _quest("ashen_embers", ("Fuel for the Forge", "Combustibile per la forgia"), ("Grael's forge runs on ember cores, and the ember slimes of the Ashen Wastes carry them.", "La forgia di Grael va a nuclei di brace, e li portano gli slime di brace delle Lande di Cenere."),
                   [_kill("slime_ember", 8), _collect("ember_core", 4)], 840, 1050, {"base:item/potion_large": 3},
                   ("A forge in the Wastes, and nothing to burn. The irony is not lost on me. The ember slimes burn for a week each. Bring me four.", "Una forgia nelle Lande, e niente da bruciare. L'ironia non mi sfugge. Gli slime di brace bruciano una settimana ciascuno. Portamene quattro."),
                   ("Eight ember slimes, four cores.", "Otto slime di brace, quattro nuclei."),
                   ("The forge roars. Here, potions; I trade them from the caravans for horseshoes.", "La forgia ruggisce. Tieni, pozioni: le scambio con le carovane per ferri di cavallo.")),
            _quest("ashen_char", ("Charcoal of the Wastes", "Carbone delle Lande"), ("For his best steel Grael wants char from the char slimes of the Ashen Wastes.", "Per il suo acciaio migliore Grael vuole il carbone degli slime carbonizzati delle Lande di Cenere."),
                   [_kill("slime_char", 6), _collect("char_chunk", 4)], 1260, 1575, {"base:item/ember_greatsword": 1},
                   ("The best steel wants the blackest charcoal, and the char slimes are made of nothing else. I have one blade left in me worth making. Help me make it.", "L'acciaio migliore vuole il carbone più nero, e gli slime carbonizzati non sono fatti d'altro. Ho ancora una lama da fare che ne valga la pena. Aiutami a farla."),
                   ("Six char slimes, four chunks.", "Sei slime carbonizzati, quattro pezzi."),
                   ("It is done. It is yours. I made it for whoever brought the charcoal, and I hoped it would be you.", "È fatta. È tua. L'ho fatta per chi avesse portato il carbone, e speravo fossi tu.")),
        ],
    },
]
