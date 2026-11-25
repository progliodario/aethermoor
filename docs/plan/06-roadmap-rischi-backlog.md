# 06. Roadmap, rischi e backlog

## 1. Come leggere la roadmap

- Ogni milestone ha **obiettivo**, **consegne**, **criteri di accettazione** e **taglia** relativa (S, M, L, XL). Le taglie sono stime di lavoro **relativo**, non di calendario: il ritmo dipenderà da quante sessioni dedichiamo al progetto.
- Ogni milestone termina con una **build eseguibile su Windows, Linux e Android** (tranne dove indicato) e una release `0.x`.
- Ordine guidato dal principio: **prima fondamenta e dati, poi una fetta verticale giocabile, poi ampiezza, poi contenuti**.

## 2. Milestone

### M0: Fondazioni (taglia S)

**Obiettivo:** repository pronto, regole e CI scritte, nessun gioco.

Consegne:

- Cartella progetto con Git, `README.md`/`README.en.md`, `LICENSE` (GPL-3.0), `LICENSE-CONTENT.md`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `SECURITY`, `CHANGELOG`, `CLAUDE.md`.
- `docs/` con ADR 0001-0011 e struttura delle specifiche (vuote ma indicizzate), `project.json`.
- `.github/` con workflow (CI vuote ma verdi), template, label, CODEOWNERS, dependabot.
- `.claude/` con i comandi base.
- `tools/` con `validate_data.py` minimale e `requirements.txt`; pre-commit.
- Scheletri: `desktop/` (CMake + SDL3 apre una finestra e disegna un colore; ThorVG non è stato usato, vedi ADR 0012), `android/` (Gradle + libGDX avvia un'activity con schermata di colore).

Accettazione: CI verde su tutte le piattaforme; i tre eseguibili si avviano e mostrano nome e versione del gioco; docs pubblicate; primo tag `v0.0.1`.

### M1: Specifiche core, formati e conformità (taglia M)

**Obiettivo:** il "linguaggio comune" dei due client.

Consegne:

- Spec 00-03, 12, 17: convenzioni, numerica (interi, punto fisso, RNG, hash, rumore), componenti, ordine sistemi, salvataggi, i18n.
- JSON Schema v1 per i tipi base (`pack`, `protagonist`, `skill`, `item`, `enemy`, `quest`, `dialogue`, `art_recipe`, `rig`, `clip`, `ui_screen`, `ui_theme`, `i18n`).
- `tools/reference/` con RNG, hash, noise, formule base; generatore di vettori.
- Loader dei pack e i18n in C++ e Kotlin, con test di conformità per RNG, hash, noise, xp, danno, condizioni, i18n.

Accettazione: tutte le suite `rng`, `hash`, `noise`, `damage`, `stats_derived`, `xp_table`, `condition_eval`, `i18n_format` passano su C++ e Kotlin; `validate_data` verde su un pack base con pochi contenuti.

### M2: Motore base e arte vettoriale (taglia L)

**Obiettivo:** muovere un personaggio vettoriale su una mappa.

Consegne:

- Loop a passo fisso, ECS, eventi, input astratto (tastiera, gamepad, touch con stick virtuale).
- Camera, mappa TMJ, collisioni, stream di chunk fissi (senza worldgen).
- Rasterizzatore ricette: fatto un rasterizzatore proprio, uguale nei due client (ADR 0012, al posto di ThorVG / `android.graphics`), con atlanti, cache e ribake al cambio di scala. La perdita del contesto GL su Android non è stata provata.
- Rig/clip, personaggio base con camminata e idle, ombre, ordinamento per `y`, particelle di base.
- Overlay di debug, logger, profiler. Gestione orientamento Android.

Accettazione: un protagonista cammina in una piccola mappa con alberi e casa, con la stessa resa su 3 piattaforme (golden con tolleranza), 60 FPS in scenario perf, rotazione Android senza perdita di stato.

### M3: Combattimento (fetta verticale 1) (taglia L)

**Obiettivo:** combattere davvero.

Consegne:

- Spec 04-05: statistiche, danni, elementi, stati; hitbox, skill, cooldown, mana, schivata, parata, stagger.
- IA nemica dichiarativa; 3 nemici (slime, lupo, goblin) e 1 mini-boss; bottino ed esperienza; livelli.
- HUD, numeri di danno, status window v1, effetti di colpo e suoni sintetizzati base (colpo, magia, danno).
- Ren con **Occhio del Sistema** (Analizza).

Accettazione: si combatte e si sale di livello; le conformità `damage`, `status_ticks`, `loot_roll` passano; scenari headless di combattimento verdi.

### M4: Dialoghi, quest, inventario, salvataggi (fetta verticale 2) → **Alpha 0.1** (taglia XL)

**Obiettivo:** un'ora giocabile con un villaggio.

Consegne:

- Toolkit UI e schermate dichiarative (dialogo, inventario, equip, diario, negozio, menu, impostazioni, slot).
- Dialoghi, quest, flag, condizioni/effetti completi del catalogo base.
- Inventario, equipaggiamento, negozi, economia base.
- Salvataggio v1 (autosave + manuale), caricamento, export/import, `profile.json`.
- Villaggio Fenwick e Aldermere (gilda base con rango F-E), 8 quest, 40 dialoghi.
- Traduzioni IT/EN, tema "Finestra di sistema".

Accettazione: dall'inizio al primo rango E in ~60 minuti; salvataggio copiato tra desktop e Android funziona; suite quest/dialoghi/save passano; cambio lingua a caldo.

**Release Alpha 0.1** (primo pacchetto pubblico per Windows, Linux e APK).

### M5: Mondo aperto procedurale e vita del mondo (taglia XL)

**Obiettivo:** esplorare una regione grande.

Consegne:

- Spec 08-09, worldgen a due livelli, mondo 2048×2048, regioni, biomi, stamp, strade, fiumi, POI, risorse.
- Streaming dei chunk con worker thread, persistenza `deltas`.
- Ciclo giorno/notte, meteo, stagioni, luci 2D, routine PNG.
- Minimappa e mappa del mondo; Pietre della Soglia (checkpoint e viaggio rapido).
- Regione **Verdalis** completa (livelli 1-12) con 2 dungeon.

Accettazione: la suite `worldgen_chunk_hash` passa su C++, Kotlin e Python per 5 seed; salvataggio di una partita su un OS e caricamento su un altro riproducono lo stesso mondo; 60 FPS con scenario di esplorazione; tempo di generazione chunk entro budget.

### M6: Sistemi di vita (taglia XL) → **Alpha 0.2**

**Obiettivo:** vivere il mondo oltre a combattere.

Consegne: agricoltura e allevamento, cucina, crafting e qualità, raccolta, pesca, caccia, costruzione della base e residenti, economia dinamica, bottega e mercanti ambulanti, ricettario.

Accettazione: un giocatore può coltivare, cucinare e vendere in modo sostenibile; le conformità `crafting_quality`, `economy_price`, `time_season`, `weather` passano; scenario "una settimana di gioco" senza anomalie.

### M7: Party, compagni e legami (taglia L)

**Obiettivo:** combattere e vivere con compagni.

Consegne: IA dei compagni con profili e comandi, party da 3, 4 compagni iniziali, legami e eventi, doni, relazioni opzionali, interfaccia di party, abilità di coppia.

Accettazione: i compagni si comportano in modo credibile per 20 minuti di combattimento in scenario; touch e controller gestiscono i comandi; eventi di legame giocabili.

### M8: Progressione profonda → **Beta 0.5** (taglia XL)

**Obiettivo:** tutti i sistemi dell'RPG presenti.

Consegne: alberi abilità (doni + classi), titoli e tag, ranghi gilda completi (F-S), fazioni, bestiario, achievements, reincarnazione e Albero dell'Eredità, profilo con sblocchi, difficoltà e Hardcore, ricette avanzate, runi e affissi.

Accettazione: una run completa di Ren (prologo + atto I) con tutti i sistemi attivi; la reincarnazione porta Echi al profilo e sblocca un secondo protagonista; nessun sistema "mock".

**Release Beta 0.5.**

### M9: Contenuti (taglia XL × 8, a ondate)

**Obiettivo:** i protagonisti 1-8 completi. Si lavora **un protagonista per volta** con il template di contenuto (documento 03, sezione 16).

| Ondata | Protagonisti | Release |
|---|---|---|
| 9a | **Ren** (atto II-III, Verdalis completa), **Haruka** (Whisperwood) | 0.6 |
| 9b | **Daichi** (Ironspine), **Sakura** (Lumeria) | 0.7 |
| 9c | **Marco** (Tidehaven), **Yuki** (Sunscar) | 0.8 |
| 9d | **Lena** (Frostveil), **Gideon** (Ashen Wastes, modalità Dungeon) | 0.9 |

Per ogni protagonista:

1. Specifica del dono e dell'albero (`/spec-change`).
2. Prologo, trama in 3 atti, compagni, boss.
3. Arte (ricette e rig) per personaggi, nemici, ambienti.
4. Audio (temi, SFX).
5. i18n IT/EN.
6. Bilanciamento con scenari e giocate.
7. Test di regressione.

Accettazione per ondata: ogni protagonista giocabile dall'inizio alla fine, con i suoi finali; nessun blocco di quest; conformità e scenari verdi.

### M10: Rifinitura (taglia L)

Consegne: tutorial e onboarding, ottimizzazione prestazioni e memoria, modalità qualità, accessibilità, audio completo, VFX, controllo traduzioni, bilanciamento globale, crash reporter locale (log), rimappatura, editor layout touch, schermata Crediti, localizzazione revisionata.

Accettazione: obiettivi di prestazioni del documento 04 soddisfatti sui dispositivi di test; zero crash nelle sessioni di prova da 2 ore; checklist di accessibilità completata.

### M11: Release 1.0 (taglia M)

Consegne: tutte le piattaforme firmate, store (GitHub Releases + itch.io, Google Play se scelto), sito/pagina di download, trailer e screenshot, docs complete per modder, FAQ, annuncio.

Accettazione: release-checklist superata; installazione pulita su 3 PC e 3 telefoni; il salvataggio di una vita completa passa tra piattaforme.

### M12+: Dopo l'1.0

Protagonisti 9-10 (Slime, Aurelia), "Tre Re", aste, fotografia, nuove regioni e dungeon, strumenti per modder (editor visuale dei dati, validazione online), Flathub, Steam (se desiderato), nuove lingue, rilascio di modalità "sfida".

## 3. Dipendenze tra milestone

```text
M0 → M1 → M2 → M3 → M4 → M5 → M6
                  │         │     └→ M7 → M8 → M9 (a,b,c,d) → M10 → M11
                  └─────────┴──────────────→ (M5 e M6 possono avanzare in parallelo dopo M4 in sessioni separate)
```

Le sessioni parallele hanno senso da M5: *worldgen* e *sistemi di vita* toccano file diversi. Il *contenuto* (M9) può procedere in parallelo ai protagonisti se i sistemi sono stabili.

## 4. Valvole di portata (cosa tagliare, in ordine)

Se il progetto rischia di non arrivare all'1.0, si tagliano in quest'ordine, **senza compromettere l'architettura**:

1. Protagonisti 6-8 slittano a 1.1-1.3 (gli altri 5 completi all'1.0).
2. Minigiochi extra (corse, gioco di carte, fotografia).
3. Meteo estremo, post-effetti, stagioni complete (restano ciclo giorno/notte e 2 stagioni).
4. Modalità Dungeon di Gideon ridotta a variante semplificata.
5. Rapid travel tramite carovane (restano le Pietre).
6. Seconda lingua oltre l'inglese e l'italiano (comunque già rimandata).
7. Costruzione della base a griglia libera: si riduce a slot predefiniti.

Rimangono fissi: i quattro vincoli (spec-first, data-driven, due client, parità) e la qualità dei sistemi di base (combattimento, salvataggi, quest).

## 5. Registro dei rischi

| # | Rischio | Prob. | Impatto | Mitigazione |
|---|---|---|---|---|
| R1 | Due motori separati divergono nel tempo | Alta | Alto | Spec scritta, riferimento Python, conformità, feature gating, `parity-check` in CI, moduli corrispondenti. **Oggi:** spec, riferimento e 30 file di vettori eseguiti dai due client in CI (la matrice che lo verifica è la voce B1.4 del [programma](07-programma-operativo.md)); feature gating e `parity-check` esistono ma non sono usati (ADR 0009) |
| R2 | Portata eccessiva (8 protagonisti, mondo aperto, molti sistemi) | Alta | Alto | Fetta verticale prima (M3-M4), template di contenuto, valvole di portata, release incrementali |
| R3 | Differenze di rasterizzazione ThorVG/Skia rovinano la coerenza visiva | Media | Medio | **Ridotto:** ADR 0012 ha scelto un rasterizzatore unico, scritto due volte e verificato con le stesse sonde (suite `raster`). Resta il rischio delle prestazioni su mobile (R4), non misurato |
| R4 | Prestazioni scarse su mobile (rasterizzazione, GC) | Media | Alto | Bake in background e cache, atlanti, pool di oggetti, niente allocazioni nel tick, profiling da M2 |
| R5 | Mondo procedurale non identico tra piattaforme | Media | Alto | Punto fisso, flag del compilatore, vettori di hash dei chunk, test su CI di entrambi i client |
| R6 | Perdita del contesto GL su Android rompe l'arte | Media | Medio | Cache CPU degli atlanti, test strumentato di pausa/ripresa, gestione esplicita in `game` |
| R7 | UI dichiarativa troppo complessa da implementare due volte | Media | Medio | Insieme di widget ridotto, test golden, in caso di blocco: schermate critiche a mano con la stessa specifica (ADR) |
| R8 | Bilanciamento difficile con 8 doni molto diversi | Alta | Medio | Triangolo potere/costo/limite, scenari automatici di combattimento, tabelle in dati, playtest per ondata |
| R9 | Coerenza narrativa e di tono tra 8 trame | Media | Medio | Guida al tono, bibbia del mondo, template, revisione per ondata, glossario |
| R10 | Licenze (font, libreria, arte) incompatibili con GPLv3 | Bassa | Alto | Controllo automatico in CI, solo OFL/MIT/Apache/zlib |
| R11 | Tooling Android (Gradle, SDK, target Play) cambia | Media | Basso | Version catalog, aggiornamenti mensili, `targetSdk` verificato a ogni release |
| R12 | Salvataggi incompatibili dopo cambi del formato | Media | Alto | `save_version`, migrazioni testate, backup, export |
| R13 | Contenuti sensibili (schiavitù, romance, violenza) percepiti male | Bassa | Medio | Linee guida di tono, personaggi adulti, nessun contenuto esplicito, impostazioni di attenuazione |
| R14 | Dipendenza dalla disponibilità del progettista (tu) | Media | Medio | Documentazione completa, CLAUDE.md, ADR, contenuti riproducibili da template |
| R15 | Mod malevoli | Bassa | Basso | Dati dichiarativi senza codice, validazione stretta, nessun accesso a file fuori dal pack |

## 6. Metriche di progresso

- **Parità:** funzionalità `released` presenti in entrambi i client (obiettivo 100%).
- **Conformità:** suite verdi su entrambi i client; numero di vettori.
- **Dati:** contenuti per protagonista rispetto al template (grafico a barre generato).
- **Qualità:** tempo medio di CI, bug aperti per area, copertura del core.
- **Prestazioni:** FPS medio e minimo negli scenari perf, tempo di generazione chunk, memoria.
- **Localizzazione:** percentuale di chiavi tradotte per lingua.

## 7. Backlog iniziale (pronto per GitHub Issues)

### M0

1. `chore(repo)`: inizializza il repo, licenze, README, CONTRIBUTING, COC, SECURITY, CHANGELOG
2. `docs(adr)`: scrivi ADR 0001-0011
3. `docs(claude)`: scrivi `CLAUDE.md` e `.claude/` con i comandi base
4. `ci(data)`: workflow `ci-data` con validazione
5. `ci(desktop)`: workflow `ci-desktop` con matrice Windows/Linux
6. `ci(android)`: workflow `ci-android`
7. `ci(release)`: skeleton di `release.yml`
8. `chore(github)`: label, template, CODEOWNERS, dependabot, branch protection
9. `feat(desktop)`: finestra SDL3 + versione (ThorVG non linkato, ADR 0012)
10. `feat(android)`: activity libGDX + versione
11. `feat(tools)`: `validate_data.py` minimale, pre-commit
12. `docs(dev)`: guide di setup Windows, Linux, Android

### M1

13. `spec`: 00-conventions
14. `spec`: 01-numerics (interi, punto fisso, RNG, hash, rumore)
15. `tools`: riferimento Python per RNG/hash/noise
16. `tools`: generatore di vettori e `--check` in CI
17. `feat(desktop)`: RNG, hash, noise, fixed-point + test conformità
18. `feat(android)`: RNG, hash, noise, fixed-point + test conformità
19. `schemas`: pack, protagonist, skill, item, enemy, quest, dialogue
20. `feat(data)`: loader pack + validazione runtime in C++
21. `feat(data)`: loader pack + validazione runtime in Kotlin
22. `spec`: 12-save-format, 17-localization
23. `feat(i18n)`: caricamento e formattazione ICU-lite nei due client

### M2

24. `spec`: 13-vector-art
25. `feat(gfx)`: rasterizzatore ricette (proprio, ADR 0012)
26. `feat(gfx)`: rasterizzatore ricette (android.graphics)
27. `feat(gfx)`: atlanti, cache, ribake
28. `feat(sim)`: ECS + loop a passo fisso nei due client
29. `feat(input)`: azioni astratte + tastiera/gamepad + touch
30. `feat(gfx)`: rig/clip + personaggio base
31. `feat(sim)`: collisioni, camera, mappa TMJ
32. `feat(gfx)`: particelle e ombre
33. `tools`: overlay di debug, profiling
34. `test(gfx)`: golden con tolleranza per ricette campione
35. `feat(android)`: orientamento e ciclo di vita, perdita contesto GL

Dopo l'approvazione, ogni voce diventa un issue con descrizione, criteri di accettazione e label: è successo il 23 novembre 2026, con il [programma operativo](07-programma-operativo.md) (la sezione 9 dice il numero di ogni issue).

## 8. Stato e prossimi passi

Aggiornato al 23 novembre 2026.

Questa sezione è la fotografia di **dove si è arrivati** e di **che cosa resta da fare**. Le sezioni 1-7 sono il piano di partenza e non vengono riscritte; qui si dice, voce per voce, che cosa è diventato realtà.

### 8.1 In breve

Versione `0.0.1`, **nessuna release pubblica** (la decisione di pubblicare è del proprietario, vedi 8.6). Il gioco si gioca dall'inizio alla fine della storia di ognuno degli **otto protagonisti** su Windows, Linux e Android, con le versioni di prova prodotte dalla CI.

I numeri, contati dai dati da `tools/make_facts.py` (dove si guarda: il [catalogo](../design/catalog.md), le [specifiche](../spec/README.md), `tests/conformance/`):

<!-- facts:begin -->
| Che cosa | Quanti (contati dai dati da `tools/make_facts.py`) |
|---|---|
| Mondo | 8 regioni, 46 luoghi fatti a mano (sotterranei, tane, avamposti, santuari, Fenwick, il cottage dell'Ospite, Aldermere) e circa 130 insediamenti generati |
| Protagonisti | 8, ognuno con un compagno, altri 4 compagni che possono entrare nel gruppo, e una storia in sei atti (120 missioni di storia) |
| Creature | 83, di cui 27 guardiani e 8 Echi |
| Missioni | 407 (24 storie dei paesani) |
| Oggetti e ricette | 290 oggetti, 86 ricette (8 segrete) |
| Progressione | 50 titoli, 8 tag, 16 talenti, 29 imprese |
| Persone con nome | 58 nei dati del mondo, oltre ai paesani generati |
| Suono | 174 effetti sonori sintetizzati (musica e ambiente spenti) |
| Testi | 4300 chiavi, in italiano e inglese |
| Regole uguali sui due client | 31 file di vettori di conformità, 634 casi, eseguiti dai test C++ e Kotlin |
| Documenti | 19 specifiche, 14 ADR |
<!-- facts:end -->

### 8.2 Stato delle milestone

Legenda: **fatto** = le consegne del piano ci sono e funzionano su tutti e due i client; **quasi** = manca poco e la parte mancante è scritta in "Manca"; **avviato** = c'è una base giocabile, ma una parte grande del piano è ancora da fare.

| Milestone | Stato | Che cosa c'è | Che cosa manca |
|---|---|---|---|
| M0 Fondazioni | fatto | repository, licenze, CI su Windows, Linux e Android, ADR, schemi, `CLAUDE.md`, `tools/ship.py` | nulla |
| M1 Specifiche core e conformità | fatto | numerica intera, RNG, hash, rumore, formule, i18n, loader dei pack, riferimento Python, vettori in CI (`gen_conformance.py --check`) | nulla |
| M2 Motore e arte | quasi | rasterizzatore proprio nei due client (ADR 0012) con sfumature, ritagli, fusioni e rumore (ADR 0013, spec 13 v2); arte da anime per persone, terreni, oggetti e creature; persone viste di fronte, di lato e di spalle; luce dell'ora, vento, acqua che si muove, ombre lunghe, font del pack sui due client, texture cotte a rate, fotogrammi controllati in CI | prova della perdita del contesto GL su Android |
| M3 Combattimento | fatto | attacco, colpo potente, schivata, parata, sei elementi, stati alterati su creature e giocatore, stagger, barra del guardiano, Analizza di Ren, creature con comportamenti, XP e livelli | nulla di aperto: nessuno scontro del modello dura più di tre secondi al proprio livello (`docs/design/balance.md`); si ricontrolla a ogni creatura nuova |
| M4 Dialoghi, missioni, inventario, salvataggi | quasi | dialoghi con condizioni ed effetti, missioni con meta sulla mappa, zaino, negozi, equipaggiamento a tre posti, diario e finestra di stato, gilda con ranghi F-S e bacheca, locande, tre partite, export e import, `profile.json`, volumi, tasti configurabili (desktop), Fenwick e Aldermere scritti a mano, otto prologhi | la **release Alpha 0.1** (tag e pacchetti: decisione del proprietario) |
| M5 Mondo aperto | quasi | streaming dei chunk, regioni, insediamenti, siti, fiumi e strade, stagioni, meteo con pioggia, neve, nebbia e notte che nascondono il giocatore, vento che lo spinge, temporali, stagioni che rallentano le creature o le rendono meno attente, routine dei PNG, Pietre della Soglia, mappa del mondo e mini mappa, luci di notte | prestazioni misurate su un telefono reale |
| M6 Sistemi di vita | fatto | raccolta (alberi, cespugli, rocce, cactus, funghi, canneti per pescare e la scenografia selvatica), caccia, ricette al falò e all'incudine (otto segrete, insegnate dai bottegai), cibi e infusi con effetti (fortifica, protegge, rigenera, rapidità, purifica), accessori, opere pregiate, giorni di mercato, merci di altre regioni portate dalle carovane, orti (che crescono prima con la pioggia), pollai e recinti nei villaggi, negozi che pagano meno se vendi troppo, bauli condivisi in ogni villaggio e città, Nonna Brin, il venditore ambulante Corvin, il cottage dell'Ospite con i suoi mobili e tre stanze da sistemare, otto residenti che arrivano agli avamposti, Odo il capo carovana, Brannoc il fabbro errante e Lark la cantastorie che ogni giorno sono in un altro avamposto e camminano tra le tappe, stagioni che cambiano i raccolti, il giardino del cottage, un colono in ogni villaggio generato con il suo mestiere, la sua missione e la sua bottega, una festa per regione con i suoi giochi, i paesani che ne parlano | nulla |
| M7 Compagni | fatto | un compagno per protagonista che segue, combatte, resta, segue o torna a comando, cresce di legame e cura il giocatore; i doni di Haruka (legame più rapido) e di Gideon (compagno più forte) ; Haruka doma le creature ferite e l'ultima resta con lei come secondo compagno ; momenti del legame; il compagno domato obbedisce a resta e torna, un gruppo di compagni (i quattro randagi del cottage) che seguono uno alla volta, ognuno con il suo legame | nulla |
| M8 Progressione profonda | fatto | bestiario con debolezze, titoli con effetti e progressi visibili, albero di talenti con quattro abilità e due abilità a comando, echi, reincarnazione con eredità di oro e arma, imprese di tutte le partite lette dal profilo, rune incise sulle armi, tag da indossare, armi e armature con affissi tirati a sorte quando si trovano, anche ventiquattro pezzi comuni, e ritemprati all'incudine o dai fabbri, dodici pezzi rari con due affissi, affissi scelti all'incudine con il prisma, doni delle imprese a ogni partita nuova | nulla |
| M9 Contenuti | fatto | per ognuno degli otto protagonisti: prologo, dono, due missioni personali, storia in tre atti, epilogo, quinto e sesto atto ("Due Ospiti", che lega i protagonisti a coppie), epilogo contro il proprio Eco e boss; Libro delle Leggende (una leggenda per regione), taglie su tutti i guardiani, missioni di città, avamposti, caccia, pesca, lettere, il Dungeon di Gideon (cinque ondate di avventurieri, trappole, un titolo) | nulla |
| M10 Rifinitura | avviato | effetti sonori, pannelli e barre ridisegnati, testi che vanno a capo per larghezza, niente scatti quando appare roba nuova, consigli per i primi minuti, opzioni di accessibilità (consigli, numeri, lampi, testo grande), crediti, traduzioni controllate da uno strumento (anche i termini del glossario), log dei crash, la lista di controllo dell'accessibilità | un sintetizzatore migliore per riaccendere musica e ambiente |
| M11 Release 1.0 | avviato | la guida per chi fa mod, il mod di esempio e il suo controllo in CI | pacchetti firmati, pagina di download (decisioni del proprietario) |

### 8.3 Che cosa è stato fatto, per area

Ogni voce dice la regola (con la sua specifica) e da quando c'è. Tutto ciò che è una regola di gioco esiste nei due client, nel riferimento Python e nei vettori.

**Mondo** (spec 08, 09)

- Mondo di 16384 x 16384 caselle generato da un seme, sempre uguale a parità di seme (interi e virgola fissa), caricato a pezzi mentre si cammina.
- Otto regioni (Verdalis, Whisperwood, Ironspine, Sunscar, Frostveil, Tidehaven, Ashen Wastes, Lumeria) con terreno, creature, negozi e modo di parlare propri.
- Circa 130 insediamenti generati; luoghi fatti a mano: sotterranei e tane con guardiano, otto avamposti, otto santuari degli Echi, Fenwick (il villaggio di partenza), il cottage dell'Ospite e Aldermere (la città della gilda).
- Fiumi e strade sulla mappa, giorno e notte con la luce dell'ora, quattro stagioni, meteo; la pioggia e la notte riducono la distanza da cui le creature ti notano; la neve cade a Frostveil.
- **Nebbia e temporali** (dal 18 novembre, seconda PR): due tempi nuovi; la nebbia accorcia fino al 40% la distanza da cui le creature ti notano (un velo pallido e banchi di foschia), il temporale è pioggia e vento insieme, con i lampi (che si spengono con l'opzione dei lampi). L'orologio dice che tempo fa.
- **Vento** (dal 18 novembre): ogni tempo ha il suo vento (brezza col sereno, forte sotto le nuvole, a raffiche con la pioggia); il vento alle spalle fa camminare il giocatore fino al 15% più veloce e muove di più le piante.
- Pietre della Soglia per curarsi e viaggiare; mappa con zoom, meta del giocatore e meta di ogni missione.
- **Il tempo cambia i prezzi** (dal 23 novembre, B2.1, spec 06 "Weather and prices"): con la pioggia le merci di campagna (cibo, legna,
  resina, erbe, fiori, muschio e i semi degli orti) costano il 10% in più e i bottegai le pagano il 10% in più; nella neve di Frostveil
  il 20%. Il negozio scrive "Pioggia +10%" o "Neve +20%" e colora d'azzurro quei prezzi; un consiglio lo dice la prima volta che piove.
- **Stagioni** (dal 18 al 23 novembre): cambiano la crescita degli orti, i raccolti, la caccia (`season_bonus`) e le creature (l'inverno le
  rallenta, l'estate e l'autunno le rendono meno attente); sedici visitatori di altre regioni arrivano in una stagione e quattro gelatine
  vivono solo nella loro, con un bottino e un tè propri; ogni bottega e ogni carro vende alcune merci solo nella loro stagione.

**Combattimento** (spec 04, 05)

- Attacco, colpo potente con mana, schivata con invulnerabilità, parata che stordisce.
- Sei elementi su armi e abilità, debolezze e resistenze delle creature, stati alterati (bruciatura, gelo, stordimento, indebolimento) su creature e giocatore, stagger con barra.
- Barra del guardiano in cima allo schermo (nome, livello, tacche, stagger, debolezze).
- Difficoltà tenuta **bassa di proposito** (vita delle creature 100%, attacco 70%): è il tema dell'isekai.

**Missioni e persone** (spec 07, 18)

- Tutte le missioni del [catalogo](../design/catalog.md) (ventiquattro sono le storie dei paesani, tre per regione; otto sono i compiti da amico degli anziani, per chi ha otto missioni nella regione): le storie degli otto protagonisti (prologo, due missioni personali, tre atti, epilogo), la gilda con bacheca generata, Fenwick e Aldermere, gli otto avamposti (tre o quattro missioni ognuno), il Libro delle Leggende di Selwyn, le taglie di Hestia, le lettere e i pacchi del corriere Wendel, caccia e pesca.
- Ogni missione segna sulla mappa dove andare: un luogo, una persona, la tana delle creature giuste o la pianta più vicina.
- **Fama** (dal 14 novembre): ogni missione finita in una regione vale un punto di fama lì; i negozi della regione scontano l'1,5% per punto fino al 25%, anziani e bottegai salutano un amico da tre missioni, i locandieri danno un letto gratis da cinque; otto titoli "Amico di ...". Ogni regione tiene due pezzi rari per chi ha cinque e dieci missioni lì.
- **Giorni di mercato** (dal 14 novembre): i prezzi di ogni regione oscillano con il giorno, per comprare e per vendere (dal 6% di Ironspine al 20% di Sunscar).
- **Coloni e feste** (dal 18 al 22 novembre): un colono in ogni villaggio generato quando la regione ti conosce, con un mestiere, una bottega e
  un compito che si può rifare; una festa per regione con pasto gratis, mercato al 75% e una gara (otto missioni), i paesani che ne parlano.
- **I paesani vanno alle feste** (dal 23 novembre, B3.2, spec 07 "Feasts" e spec 09 "Settlement people"): nel giorno di festa dei vicini i
  paesani dei borghi e dei villaggi di una regione non sono a casa (anziano, bottegaio, locandiere e colono restano); nel giorno di festa
  della regione ogni sua città ha tre ospiti in piazza, che raccontano da dove vengono. La condizione di presenza di ogni persona è nei vettori.
- **Viaggiatori** (dal 18 al 22 novembre): Odo il capo carovana, Brannoc il fabbro errante (al contrario di Odo) e Lark la cantastorie, ogni
  giorno in un altro avamposto; le canzoni di Lark, la canzone della strada e le cacce delle stagioni.
- **I viaggiatori camminano** (dal 24 novembre, B3.1, spec 07 "Travellers walk"): restano alla tappa da un quarto a tre quarti del giorno;
  la mattina arrivano a piedi dalla tappa del giorno prima, la sera ripartono verso quella del giorno dopo, in linea retta e al passo.
  La posizione viene dall'orologio del mondo con aritmetica intera, uguale nel riferimento e nei due client, e non si salva.
- **Le missioni che chiedono oggetti si chiudono subito** (dal 24 novembre, spec 07 "Quests"): la borsa si conta all'inizio di ogni tick,
  non più solo a un'uccisione o a una parola.
- **Missioni ripetibili** (dal 22 novembre, `repeatable`): le cacce delle stagioni, le botteghe dei coloni e le taglie permanenti della gilda
  (una per regione, su un grande guardiano); il diario le segna "(si può rifare)".
- **Missioni a tempo e prove delle stagioni** (dal 23 novembre, B4.1, spec 07 "Timed quests"): una missione può avere dei giorni
  (`time_limit_days`); passati, non conta più nulla e si riprende subito. Dal livello 25 gli impiegati della gilda offrono in ogni stagione
  una prova: due grandi creature di due regioni lontane in tre giorni, pagata con un pezzo raro a due affissi. Il diario dice i giorni rimasti.
- **Il Dungeon di Gideon** (dal 24 novembre, C3.1, spec 18 "Gideon's Dungeon", la forma ridotta scelta dal proprietario): un sito accanto
  al Santuario della Cenere, tre stanze dal cancello al nucleo; finita la storia di Gideon, Grubb apre i cancelli a cinque ondate di
  avventurieri che marciano sul nucleo; trappole di spuntoni e di catrame; la ricompensa e il titolo Signore del Dungeon.
- **Storie laterali** (dal 23 novembre, D1-D4, spec 18 "Side stories"): ognuno degli otto protagonisti ha una storia di tre missioni,
  raccontata ad Aldermere solo a chi porta il suo ricordo, con un finale scelto in dialogo che cambia l'oggetto ricevuto: Bertram Quill
  (Ren, i registri della gilda), Mirela (Haruka, le stalle), la capitana Wren Hale (Daichi, i pompieri volontari), Ottilie Brask (Sakura,
  l'osservatorio), Bruna Calder (Marco, la mensa), Ilse Marrow (Yuki, la cassaforte), il dottor Aurel Finch (Lena, il medico) e Dorrit Ash
  (Gideon, la fornaia delle Terre di Cenere).
- **Storia** (dal 22 novembre): il sesto atto "Due Ospiti" lega i protagonisti a coppie, poi l'altro Eco, il riposo degli Echi e la lanterna di
  Lyra, l'ultimo atto comune a tutti.

**Vita** (spec 06)

- Raccolta da 15 tipi di oggetti di scena, pesca nei canneti, caccia a cinghiali, alci e volpi delle dune.
- Ricette al falò (piatti) e all'incudine (equipaggiamento pregiato, accessori, rune e mobili); otto sono i piatti segreti delle regioni, che il bottegaio insegna a pagamento (dal 17 novembre).
- **Rune** (dal 18 novembre): sette rune fatte all'incudine (brace, marea, burrasca, pietra, alba, crepuscolo, forza); usata dallo zaino accanto a un'incudine, una runa si incide sull'arma impugnata, che colpisce più forte e con l'elemento della runa. Ogni arma tiene la sua.
- **Mobili del cottage** (dal 18 novembre): sei mobili fatti all'incudine (letto con la trapunta, rastrelliera, libreria, essiccatoio, manichino, banco da lavoro) da posare sui sei tappeti del cottage; ognuno aiuta ovunque come un titolo (esperienza, attacco, opere pregiate, raccolta, parata, creazione).
- **Stanze del cottage** (dal 24 novembre, C1.1, spec 06 "Rooms"): un annesso a est della casa con tre stanze da due posti, il
  laboratorio, lo studio e la serra, che Garrick, il falegname di Fenwick, sistema per il padrone del cottage in cambio di oro e
  materiali; ogni stanza ha il suo tappeto, e tre mobili nuovi (mola, scrittoio, fioriera).
- **Opere pregiate** (dal 14 novembre): una creazione può riuscire pregiata (15%, fino al 55% con i titoli da artigiano): una porzione in più, o il pezzo pregiato al posto di quello semplice.
- Cibi e infusi con effetti a tempo: fortifica (attacco), protegge (difesa), rigenera (vita a ogni secondo), rapidità (velocità a piedi); la pozione purificante toglie gli stati alterati.
- Tre posti di equipaggiamento: arma, armatura, accessorio (nove accessori, tra cui uno che restituisce vita a ogni colpo); i guardiani li lasciano.
- Negozi per regione, locande, gilda con ranghi F-S.
- **Residenti** (dal 18 novembre): otto persone si trasferiscono negli avamposti quando hai finito sei missioni nella regione (Maela, Sorrel, Bram, Yasmin, Hald, Cormac, Ash, Ines); ognuna ti saluta, ti regala una runa e racconta la vita nuova.
- **Bauli** (dal 17 novembre): uno in ogni villaggio e città, tutti con le stesse cose; Nonna Brin a Fenwick (riposo gratis, tre favori) e Corvin, il venditore ambulante di Aldermere, con le merci di una regione diversa ogni giorno; la pioggia fa crescere prima gli orti.

**Compagni** (spec 10)

- Un compagno per protagonista: segue, combatte quello che colpisci, resta o segue a comando, torna subito da te a comando (dal 14 novembre), il legame cresce con le sue vittorie; dal legame 10 ti cura un po' ogni dieci secondi.
- **Il gruppo** (dal 24 novembre, C2.1, spec 10 "The party"): il vecchio Tam lascia portare via i quattro randagi del cottage (Biscotto
  il cane, Gufetto il gufo, Furbo la volpe, Brace la gelatina di brace); ne segue uno alla volta, `O` o il pulsante `Altro` fa seguire
  il prossimo, e ognuno tiene il suo legame.

**Progressione** (spec 11, 12)

- Livelli, albero dei talenti, di cui quattro abilità (dal 14 novembre: Turbine, Fame di battaglia, Flusso, Risposta) e due a comando con il loro tasto (Onda d'urto, Rimarginare), titoli con effetti (attacco, raccolta, creazione, opere pregiate, parata, esperienza; dal 18 novembre l'Incisore di rune e il Padrone di casa) e il progresso verso quelli mancanti, bestiario con debolezze e bottino.
- **Fulmini e doni delle imprese** (dal 18 novembre, quarta PR): nei temporali, ogni sette secondi circa, un fulmine colpisce la creatura più vicina che ti insegue (il 40% della sua salute); ogni impresa fatta lascia un dono (pozioni, rune, accessori) nello zaino di ogni partita nuova.
- **Affissi** (dal 18 novembre, terza PR): armi e armature con un affisso, bonus fissi come quelli di un accessorio (salute, attacco, difesa, critico, risucchio); sedici pezzi, un'arma e un'armatura per regione, che i guardiani della regione lasciano una volta su cinque.
- **Affissi tirati a sorte e tempra** (dal 21 e 22 novembre): un pezzo trovato ha l'affisso dal 100 al 160%; ventiquattro pezzi comuni con un
  affisso e dodici rari con due; l'olio di tempra all'incudine, o un fabbro a pagamento, ritira l'affisso e tiene il tiro migliore.
- **Affissi scelti** (dal 24 novembre, C1.2, spec 06 "Choosing an affix"): con il prisma degli affissi (fatto all'incudine, venduto a
  Ironspine), un pezzo comune con un affisso diventa lo stesso pezzo con un altro affisso, scelto tra tre (la terza pagina del pannello
  di creazione); il tiro e la runa restano al pezzo.
- **Tag** (dal 18 novembre, seconda PR): otto tratti guadagnati da come giochi (Berserker, Sentinella, Cercatore, Artefice, Epicureo, Coltivatore, Naturalista, Campione del popolo); se ne indossa uno alla volta (`Y`, o il pulsante Tag del diario) e solo quello dà il suo effetto, più forte di quello di un titolo.
- Profilo comune a tutte le partite: echi (vita in più per ogni titolo e vita passata), reincarnazione dal livello 10 con eredità di metà dell'oro e dell'arma impugnata, imprese (dal 17 novembre) lette dal profilo e elencate dalla schermata del titolo.

**Grafica** (spec 13, ADR 0012 e 0013)

- Rasterizzatore vettoriale scritto due volte (C++ e Kotlin) e verificato con le stesse sonde; arte da anime scritta da strumenti in Python.
- Persone di 4,6 teste con vista di fronte e di spalle, terreni dipinti che sfumano, oggetti di scena (dal 18 novembre anche sette mobili), creature che si girano verso di te, ombre lunghe all'alba e al tramonto, acqua e vento che si muovono, luci di notte.

**Suono** (spec 14)

- 174 effetti sintetizzati dal gioco (colpi, passi, pannelli, voci delle creature, raccolta e pesca).
- Musica e ambiente delle regioni: scritti ma **spenti**, perché al proprietario suonavano male; si riaccendono solo con il suo sì.

**Interfaccia e salvataggi** (spec 12, 16, 17)

- Tre partite, salvataggio automatico e rapido, export e import di una partita in un file, profilo condiviso.
- Italiano e inglese completi; font del pack su desktop e Android; tasti configurabili sul desktop (`F4`), comandi touch su Android.
- **Log dei crash** (dal 24 novembre, E1.2, spec 12 "The crash log"): un errore che ferma il gioco scrive `crash.txt` nella cartella dei
  salvataggi (versione, errore, ultimi avvisi); all'avvio dopo, la schermata del titolo dice dov'è (Android lo copia anche). Niente esce dal dispositivo.
- **Qualità della grafica** (dal 25 novembre, E1.1, spec 13 "Quality"): bassa, normale o alta, salvata nelle impostazioni (desktop:
  l'ultima riga del pannello `F10`; Android: un pulsante in fondo al diario). La bassa cuoce le texture al massimo a 64 pixel per casella e
  toglie l'acqua che si muove, gli angoli arrotondati del terreno e le ombre lunghe dell'alba e del tramonto; la normale al massimo a 128;
  l'alta a 256. La prima volta sceglie il gioco (il desktop alta, Android dalla memoria del telefono); un test controlla in tutte e tre le
  implementazioni che tutta l'arte stia nel budget di memoria di ogni livello.
- **Controller su Android** (dal 25 novembre, E2.2, spec 16): il primo controller collegato gioca con i pulsanti del gamepad del desktop
  (levetta, `A` attacca e conferma, `X` parla, `RB` colpo potente, `LB` parata, `B` schiva e chiude, `Y` compra o vende, la croce nelle liste);
  ogni pannello funziona come con una tastiera.
- **Il contesto grafico perso su Android** (dal 25 novembre, C4.2): le texture dell'arte e del font sono gestite da libGDX, che le ricarica
  da sola quando Android toglie il contesto (rischio R6).
- **Disposizione dei pulsanti touch** (dal 25 novembre, E2.1, spec 16 "The layout of the buttons"): su Android Schivata, Colpo, Parata e
  Analizza si spostano e si ridimensionano; l'editor si apre dal pulsante `Disposizione` del diario (trascinare, `-` e `+`, Ripristina,
  Fatto); la disposizione resta dopo un riavvio e una rotazione (è in millesimi dello schermo).
- **I consigli seguono l'ultimo dispositivo** (dal 25 novembre, spec 16 "The last device"): tastiera, tocco o controller; nove consigli
  hanno un testo per il controller. `Start` apre lo zaino e `Back` il diario, sul desktop e su Android.

**Qualità e strumenti**

- CI su Windows (MSVC), Linux (GCC) e Android (test JVM e APK), con controllo dei dati e dei vettori, dei fotogrammi del test di fumo e dello
  stile del Kotlin (ktlint, detekt); dal 22 novembre una PR si controlla in pochi minuti (cache di vcpkg e ccache); la CI non resta più bloccata ore se i server di Ubuntu non rispondono (mirror alternativi e copia dei pacchetti).
- `tools/ship.py` spedisce una modifica in un comando (controlli, commit firmato, PR, attesa della CI, merge, build di prova aggiornata).
- **Fondamenta B1** (dal 23 novembre): le copie congelate dei salvataggi di ogni versione (`tests/saves/`, suite `save_fixtures`, spec 12),
  che il riferimento e i due client devono caricare; la matrice di parità generata (`docs/design/parity.md`) e il controllo delle licenze
  (`tools/licenses.py`), tutti e due in `ci-data`; la spec 15 (il tema "Finestra di sistema" e dove sta ogni pannello) e l'ADR 0014 (le
  schermate restano nel codice fino all'1.0); la lista di rilascio (`docs/dev/release-checklist.md`); la baseline di detekt da 104 a 96, poi a 90 (i cicli del modulo `core` hanno ognuno una sola uscita), poi a 87 (i suoni, i consigli e la partita nuova di Android in funzioni più piccole), poi a 82 (l'interazione, i viaggi, la bacheca, la mappa e il negozio), poi a 73 (la lettura del tempo, del mondo, delle mappe, dei messaggi, del profilo, dei pacchetti di salvataggi, delle ricette dell'arte e del pack, e l'input di Android).
- Catalogo dei contenuti e rapporto di bilanciamento generati dai dati; anteprime dell'arte in PNG senza avviare il gioco.
- **Mod** (dal 24 novembre, E4.1): una guida passo per passo al primo mod (`docs/modding/README.md`), un mod di esempio
  (`examples/mod-example/`, una creatura e una missione) e il validatore che controlla un pacchetto qualsiasi sopra quelli da cui dipende;
  la CI controlla il mod di esempio. Il gioco non carica ancora i mod.
- **Accessibilità e traduzioni** (dal 24 novembre, E1.3): la lista di controllo dell'accessibilità (`docs/dev/accessibility.md`), con il
  contrasto dei testi controllato da un test; il controllo delle traduzioni tiene anche i termini del glossario (Pietra della Soglia,
  gilda, Echi, fama, Ospite, titolo, missione, festa, talento, affisso, legame, gruppo) in ogni testo.
- **Una settimana di gioco** (dal 24 novembre, C5.1): lo scenario `week_of_play` dei vettori (sette giorni con campi, cucina, due mercati
  sotto la pioggia, caccia, la festa, un viaggiatore e una missione a tempo), eseguito dal riferimento e dai due client, con le sue
  invarianti in un test; `docs/design/suites.md` (`tools/make_suites_map.py`, in `ci-data`) dice dove sono le suite che il piano nomina.
- **Misure** (dal 25 novembre, C4.2, `docs/design/performance.md`): un test di prestazione nei due client con budget ampi per un chunk
  del mondo (25 ms) e un tick (4 ms), i cui numeri la CI stampa; un workflow notturno che prova il gioco su un emulatore Android di API 30 e
  34 (avvio, rotazione, pausa e ripresa, la stessa partita dopo). Mancano i numeri del telefono del proprietario.
- **Il mondo davanti su un thread** (dal 25 novembre, C4.1, spec 09 "Streaming"): i due client generano su un thread l'anello di
  chunk appena fuori dalla finestra, che la finestra prende quando sono pronti; la simulazione li carica sempre nello stesso punto del
  tick, quindi il gioco non cambia (un test di ogni client confronta un archivio con il thread e uno senza, chunk per chunk). Un job
  notturno esegue quel test del desktop con ThreadSanitizer (opzione CMake `AETHER_HEADLESS_ONLY`).
- **Pipeline di rilascio** (dal 25 novembre, E3.1): su un tag `v*` il workflow di rilascio costruisce tutti i pacchetti con gli stessi
  workflow delle PR, li chiama con la versione, scrive `SHA256SUMS` e la distinta dei componenti (SPDX, `tools/licenses.py --sbom`),
  ricontrolla le somme e crea una release in **bozza** con tutti i file; non pubblica mai. A mano fa una prova senza release.

### 8.4 Che cosa resta da fare, in ordine

L'ordine tiene conto di quanto ogni pezzo cambia l'esperienza di chi gioca, di quanto è indipendente dagli altri e del rischio (si compila e si prova solo in CI). Ogni voce segue il flusso del progetto: spec, riferimento, vettori, desktop, Android, dati e testi nelle due lingue. Si fanno **molte voci insieme in ogni PR** (8.5).

Che cosa è entrato, PR per PR, lo dice il [`CHANGELOG.md`](../../CHANGELOG.md) (sezione `[Unreleased]`, in inglese) e la storia di `main`
su GitHub; questa sezione tiene solo ciò che resta da fare. Quando una voce è fatta, si toglie da qui e si aggiunge all'area giusta di 8.3. Ogni voce ha il suo dettaglio (file, criteri, rischi, batch) nel [programma operativo](07-programma-operativo.md) e la sua issue su GitHub.

**A breve (le prossime PR)**

1. **Ridurre la baseline di detekt** (B1.1, issue #224; ktlint e detekt in CI ci sono): le segnalazioni del codice vecchio restano in
   `android/config/detekt-baseline.xml`, 73 (54 di complessità, 18 di annidamento, una di uscite dai cicli): 24 in `AethermoorGame.kt`,
   16 in `World.kt`, le altre in 14 file. Si spezzano a poco a poco le funzioni più complesse, qualche voce in ogni batch.
2. **I numeri del telefono** (C4.2, #240): il proprietario misura i fotogrammi al secondo su un telefono con la lista di rilascio e li
   scrive in `docs/design/performance.md` (rischio R4); il resto di C4.2 è fatto.
3. **Le abilità di coppia** (spec 10): un colpo fatto insieme dal protagonista e dal compagno quando il legame è alto; regola nuova,
   quindi spec, riferimento, vettori e due client.
4. **I carri che si vedono viaggiare** (spec 07, "Travellers walk"): i viaggiatori camminano già; manca un carro disegnato per Odo.

**Verso la 1.0**

5. **Una prova del rilascio** (E3.1, #252): la pipeline c'è e la prova a mano è verde; la bozza di un tag di prova la decide il
   proprietario.
6. **I suggerimenti del controller nell'HUD** (spec 16, "The last device"): oggi seguono l'ultimo dispositivo solo i consigli; le scritte
   dell'HUD (per esempio "E: parla") mostrano ancora i tasti.

**Decide il proprietario** (programma, sezione 8; issue #234)

7. La prima release (Alpha 0.1), le impostazioni del repository, la firma del codice (E3.2, #253), la pagina di download (E4.2, #255).
8. **Un sintetizzatore con rumore filtrato** (C6.1, #242), per poter riaccendere musica e ambiente: solo con il sì del proprietario.

**Dopo l'1.0** (F1, #256): nuovi protagonisti, nuove regioni, nuove lingue, il caricamento dei mod nel gioco, strumenti per i mod (M12+).

**Non previsto:** una modalità difficile obbligatoria o un bilanciamento "più duro": gli scontri devono restare facili.

### 8.5 Come si lavora

1. **PR grandi**: a ogni richiesta del proprietario si portano avanti molte voci della roadmap insieme, in un ramo e una PR sola, unita con la CI verde (il proprietario non vuole PR piccole).
2. Ogni PR aggiorna nella stessa modifica le specifiche, il changelog, i README, il catalogo e questa sezione.
3. Ogni PR unita produce una build di prova (artefatto della CI), che viene copiata nella cartella di gioco del proprietario.
4. I passi di una sessione di lavoro, dall'inizio alla fine, e gli errori già incontrati sono in [`CLAUDE.md`](../../CLAUDE.md) ("A session, from
   start to end", "Pitfalls already met").

### 8.6 Chi decide che cosa

- **Claude** decide e fa tutto il resto: design (storia, tono, bilanciamento, contenuti), codice, dati, documenti, PR e merge con la CI verde. Il 5 e il 10 novembre 2026 il proprietario ha affidato a Claude la **piena autonomia**.
- **Il proprietario** prova ogni modifica a fondo su Windows, Linux e Android e dice che cosa non va; non modifica file né usa strumenti. Decide su governance e pubblicazione: la release pubblica (Alpha 0.1), la protezione del ramo `main`, le impostazioni del repository, le licenze di materiale esterno, la firma del codice.

### 8.7 Che cosa è verificato e che cosa no

- **Verificato a ogni modifica:** i dati contro gli schemi, i testi nelle due lingue, tutti i casi di conformità sui due client, la compilazione di Windows, Linux e Android, un test di fumo del desktop con fotogrammi reali.
- **Verificato dal proprietario:** come appare e come si gioca, sulle tre piattaforme.
- **Non verificabile da qui:** il suono (non si ascolta), le prestazioni su un telefono reale, ciò che si vede solo giocando a lungo. Ogni PR lo dice esplicitamente.
