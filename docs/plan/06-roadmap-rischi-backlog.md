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
| R1 | Due motori separati divergono nel tempo | Alta | Alto | Spec scritta, riferimento Python, conformità, feature gating, `parity-check` in CI, moduli corrispondenti. **Oggi:** spec, riferimento e 23 suite di vettori eseguite dai due client in CI; feature gating e `parity-check` esistono ma non sono usati (ADR 0009) |
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

Dopo l'approvazione, ogni voce diventerà un issue con descrizione, criteri di accettazione e label.

## 8. Stato e prossimi passi (aggiornato al 13 novembre 2026)

Questa sezione è la fotografia di **dove si è arrivati** e di **che cosa resta da fare**. Le sezioni 1-7 sono il piano di partenza e non vengono riscritte; qui si dice, voce per voce, che cosa è diventato realtà.

### 8.1 In breve

Versione `0.0.1`, **nessuna release pubblica** (la decisione di pubblicare è del proprietario, vedi 8.6). Il gioco si gioca dall'inizio alla fine della storia di ognuno degli **otto protagonisti** su Windows, Linux e Android, con le versioni di prova prodotte dalla CI.

| Che cosa | Quanto | Dove si guarda |
|---|---|---|
| Mondo | 16384 x 16384 caselle in streaming, 8 regioni, circa 130 insediamenti generati, 44 luoghi fatti a mano | spec 09, `data/base/worlds/overworld.json` |
| Persone con nome | 26 nel mondo (Fenwick, Aldermere, gli 8 avamposti, i viandanti, Mira, Pip, Suor Maren) | `tools/make_towns.py`, `tools/towns_outposts.py` |
| Missioni | 263 (storie dei protagonisti, gilda, città, avamposti, leggende, taglie, lettere) | `docs/design/catalog.md` |
| Creature | 75 (tra cui 27 guardiani, 8 Echi, la selvaggina) | `data/base/enemies/` |
| Oggetti e ricette | 187 oggetti, 51 ricette, 2 stazioni (falò e incudine) | spec 06, `tools/make_recipes.py` |
| Progressione | 20 titoli, 10 talenti, bestiario, profilo condiviso, reincarnazione | spec 11, spec 12 |
| Testi | 2621 chiavi, in italiano **e** inglese | spec 17 |
| Regole uguali sui due client | 30 file di vettori di conformità, 490 casi, eseguiti da C++ e Kotlin a ogni modifica | `tests/conformance/` |
| Specifiche e decisioni | 18 specifiche, 13 ADR | `docs/spec/`, `docs/adr/` |
| Suoni | 174 effetti sintetizzati; musica e ambiente **spenti** su richiesta del proprietario | spec 14 |

### 8.2 Stato delle milestone

Legenda: **fatto** = le consegne del piano ci sono e funzionano su tutti e due i client; **quasi** = manca poco e la parte mancante è scritta in "Manca"; **avviato** = c'è una base giocabile, ma una parte grande del piano è ancora da fare.

| Milestone | Stato | Che cosa c'è | Che cosa manca |
|---|---|---|---|
| M0 Fondazioni | fatto | repository, licenze, CI su Windows, Linux e Android, ADR, schemi, `CLAUDE.md`, `tools/ship.py` | nulla |
| M1 Specifiche core e conformità | fatto | numerica intera, RNG, hash, rumore, formule, i18n, loader dei pack, riferimento Python, vettori in CI (`gen_conformance.py --check`) | nulla |
| M2 Motore e arte | quasi | rasterizzatore proprio nei due client (ADR 0012) con sfumature, ritagli, fusioni e rumore (ADR 0013, spec 13 v2); arte da anime per persone, terreni, oggetti e creature; luce dell'ora, vento, acqua che si muove, ombre lunghe, font del pack sui due client, texture cotte a rate | persone viste di lato; golden visivi automatici; prova della perdita del contesto GL su Android |
| M3 Combattimento | fatto | attacco, colpo potente, schivata, parata, sei elementi, stati alterati su creature e giocatore, stagger, barra del guardiano, Analizza di Ren, 75 creature con comportamenti, XP e livelli | ribilanciamento con il modello esteso (`docs/design/balance.md` segnala ancora dei casi fuori scala) |
| M4 Dialoghi, missioni, inventario, salvataggi | quasi | dialoghi con condizioni ed effetti, missioni con meta sulla mappa, zaino, negozi, equipaggiamento a tre posti, diario e finestra di stato, gilda con ranghi F-S e bacheca, locande, tre partite, export e import, `profile.json`, volumi, tasti configurabili (desktop), Fenwick e Aldermere scritti a mano, otto prologhi | la **release Alpha 0.1** (tag e pacchetti: decisione del proprietario); la reputazione con regioni o fazioni |
| M5 Mondo aperto | quasi | streaming dei chunk, regioni, insediamenti, siti, fiumi e strade, stagioni, meteo con pioggia, neve e notte che nascondono il giocatore, routine dei PNG, Pietre della Soglia, mappa del mondo e mini mappa, luci di notte | prestazioni misurate su un telefono reale; altri effetti del meteo sul gioco |
| M6 Sistemi di vita | avviato | raccolta (alberi, cespugli, rocce, cactus, funghi, canneti per pescare e la scenografia selvatica), caccia, 51 ricette al falò e all'incudine, cibi e infusi con effetti (fortifica, protegge, rigenera, rapidità, purifica), accessori | qualità degli oggetti creati, agricoltura e allevamento, base e residenti, economia dinamica, mercanti ambulanti, ricettario |
| M7 Compagni | avviato | un compagno per protagonista che segue, combatte, resta o segue a comando, cresce di legame e cura il giocatore | altri comandi, più compagni insieme, i doni che ne dipendono (domare per Haruka, comandare per Gideon), eventi di legame |
| M8 Progressione profonda | avviato | bestiario con debolezze, 20 titoli con effetti e progressi visibili, albero di 10 talenti, echi, reincarnazione con eredità di oro e arma | abilità nuove nell'albero, tag, achievements, rune e affissi, sblocchi del profilo |
| M9 Contenuti | quasi | per ognuno degli otto protagonisti: prologo, dono, due missioni personali, storia in tre atti, epilogo contro il proprio Eco e boss; Libro delle Leggende (una leggenda per regione), taglie su tutti i guardiani, missioni di città, avamposti, caccia, pesca, lettere | altre storie per regione; i doni non ancora attivi (la tasca di Yuki, domare, una seconda vita per dungeon); la modalità Dungeon di Gideon |
| M10 Rifinitura | avviato | effetti sonori, pannelli e barre ridisegnati, testi che vanno a capo per larghezza, niente scatti quando appare roba nuova | tutorial, accessibilità, un sintetizzatore migliore per riaccendere musica e ambiente, crediti, controllo delle traduzioni |
| M11 Release 1.0 | da fare | — | pacchetti firmati, pagina di download, documentazione per chi fa mod (decisioni del proprietario) |

### 8.3 Che cosa è stato fatto, per area

Ogni voce dice la regola (con la sua specifica) e da quando c'è. Tutto ciò che è una regola di gioco esiste nei due client, nel riferimento Python e nei vettori.

**Mondo** (spec 08, 09)

- Mondo di 16384 x 16384 caselle generato da un seme, sempre uguale a parità di seme (interi e virgola fissa), caricato a pezzi mentre si cammina.
- Otto regioni (Verdalis, Whisperwood, Ironspine, Sunscar, Frostveil, Tidehaven, Ashen Wastes, Lumeria) con terreno, creature, negozi e modo di parlare propri.
- Circa 130 insediamenti generati; 44 luoghi a mano: sotterranei e tane con guardiano, otto avamposti, otto santuari degli Echi, Fenwick (il villaggio di partenza) e Aldermere (la città della gilda).
- Fiumi e strade sulla mappa, giorno e notte con la luce dell'ora, quattro stagioni, meteo; la pioggia e la notte riducono la distanza da cui le creature ti notano; la neve cade a Frostveil.
- Pietre della Soglia per curarsi e viaggiare; mappa con zoom, meta del giocatore e meta di ogni missione.

**Combattimento** (spec 04, 05)

- Attacco, colpo potente con mana, schivata con invulnerabilità, parata che stordisce.
- Sei elementi su armi e abilità, debolezze e resistenze delle creature, stati alterati (bruciatura, gelo, stordimento, indebolimento) su creature e giocatore, stagger con barra.
- Barra del guardiano in cima allo schermo (nome, livello, tacche, stagger, debolezze).
- Difficoltà tenuta **bassa di proposito** (vita delle creature 100%, attacco 70%): è il tema dell'isekai.

**Missioni e persone** (spec 07, 18)

- 263 missioni: le storie degli otto protagonisti (prologo, due missioni personali, tre atti, epilogo), la gilda con bacheca generata, Fenwick e Aldermere, gli otto avamposti (tre o quattro missioni ognuno), il Libro delle Leggende di Selwyn, le taglie di Hestia, le lettere e i pacchi del corriere Wendel, caccia e pesca.
- Ogni missione segna sulla mappa dove andare: un luogo, una persona, la tana delle creature giuste o la pianta più vicina.

**Vita** (spec 06)

- Raccolta da 15 tipi di oggetti di scena, pesca nei canneti, caccia a cinghiali, alci e volpi delle dune.
- 51 ricette, al falò (piatti) e all'incudine (equipaggiamento pregiato e accessori).
- Cibi e infusi con effetti a tempo: fortifica (attacco), protegge (difesa), rigenera (vita a ogni secondo), rapidità (velocità a piedi); la pozione purificante toglie gli stati alterati.
- Tre posti di equipaggiamento: arma, armatura, accessorio (nove accessori, tra cui uno che restituisce vita a ogni colpo); i guardiani li lasciano.
- Negozi per regione, locande, gilda con ranghi F-S.

**Compagni** (spec 10)

- Un compagno per protagonista: segue, combatte quello che colpisci, resta o segue a comando, il legame cresce con le sue vittorie; dal legame 10 ti cura un po' ogni dieci secondi.

**Progressione** (spec 11, 12)

- Livelli, albero di dieci talenti, 20 titoli con effetti (attacco, raccolta, creazione, parata, esperienza) e il progresso verso quelli mancanti, bestiario con debolezze e bottino.
- Profilo comune a tutte le partite: echi (vita in più per ogni titolo e vita passata), reincarnazione dal livello 10 con eredità di metà dell'oro e dell'arma impugnata.

**Grafica** (spec 13, ADR 0012 e 0013)

- Rasterizzatore vettoriale scritto due volte (C++ e Kotlin) e verificato con le stesse sonde; arte da anime scritta da strumenti in Python.
- Persone di 4,6 teste con vista di fronte e di spalle, terreni dipinti che sfumano, 29 oggetti di scena, 75 creature che si girano verso di te, ombre lunghe all'alba e al tramonto, acqua e vento che si muovono, luci di notte.

**Suono** (spec 14)

- 174 effetti sintetizzati dal gioco (colpi, passi, pannelli, voci delle creature, raccolta e pesca).
- Musica e ambiente delle regioni: scritti ma **spenti**, perché al proprietario suonavano male; si riaccendono solo con il suo sì.

**Interfaccia e salvataggi** (spec 12, 16, 17)

- Tre partite, salvataggio automatico e rapido, export e import di una partita in un file, profilo condiviso.
- Italiano e inglese completi; font del pack su desktop e Android; tasti configurabili sul desktop (`F4`), comandi touch su Android.

**Qualità e strumenti**

- CI su Windows (MSVC), Linux (GCC) e Android (test JVM e APK), con controllo dei dati e dei vettori; la CI non resta più bloccata ore se i server di Ubuntu non rispondono (mirror alternativi e copia dei pacchetti).
- `tools/ship.py` spedisce una modifica in un comando (controlli, commit firmato, PR, attesa della CI, merge, build di prova aggiornata).
- Catalogo dei contenuti e rapporto di bilanciamento generati dai dati; anteprime dell'arte in PNG senza avviare il gioco.

### 8.4 Che cosa resta da fare, in ordine

L'ordine tiene conto di quanto ogni pezzo cambia l'esperienza di chi gioca, di quanto è indipendente dagli altri e del rischio (si compila e si prova solo in CI). Ogni voce segue il flusso del progetto: spec, riferimento, vettori, desktop, Android, dati e testi nelle due lingue. Si fanno **molte voci insieme in ogni PR** (8.5).

**A breve (le prossime PR)**

1. **Qualità degli oggetti creati** (M6): una creazione riuscita bene dà la versione "pregiata", con una probabilità che cresce con i titoli da artigiano.
2. **Comandi del compagno** (M7): "attacca quello", "torna da me", e la possibilità di avere un secondo compagno; prepara i doni di Haruka (domare) e Gideon (comandare).
3. **Abilità nuove nell'albero dei talenti** (M8): rami che danno abilità attive, non solo percentuali.
4. **Reputazione con le regioni** (M4): le missioni fatte in una regione abbassano i prezzi dei suoi negozi e aprono dialoghi.
5. **Persone viste di lato** (M2): l'ultima parte della grafica da anime.
6. **Ribilanciamento** (M3): sistemare i casi fuori scala del rapporto di bilanciamento, sempre verso scontri facili.
7. **Controlli automatici della grafica**: confronto dei fotogrammi del test di fumo con immagini di riferimento, ktlint e detekt in CI.

**A medio termine (verso Alpha 0.2 e Beta 0.5)**

8. **Doni ancora non attivi** (M9, spec 18): la tasca di Yuki che nessuno può perquisire, domare le creature, una seconda vita per sotterraneo.
9. **Agricoltura e allevamento, base e residenti** (M6).
10. **Economia dinamica e mercanti ambulanti** (M6).
11. **Tag, achievements, rune e affissi** (M8).
12. **Altre storie per regione** (M9) e la **modalità Dungeon** di Gideon.
13. **Prestazioni su Android** misurate su un telefono, e la prova della perdita del contesto grafico (R4, R6).
14. **Un sintetizzatore con rumore filtrato**, per poter riaccendere musica e ambiente (solo se il proprietario lo vuole).

**Verso la 1.0**

15. Tutorial e accompagnamento dei primi minuti, accessibilità, crediti, controllo delle traduzioni (M10).
16. Pacchetti firmati, pagina di download, documentazione per chi fa mod (M11).
17. Dopo l'1.0: nuovi protagonisti, nuove regioni, nuove lingue, strumenti per i mod (M12+).

**Non previsto:** una modalità difficile obbligatoria o un bilanciamento "più duro": gli scontri devono restare facili.

### 8.5 Come si lavora

1. **PR grandi**: a ogni richiesta del proprietario si portano avanti molte voci della roadmap insieme, in un ramo e una PR sola, unita con la CI verde (il proprietario non vuole PR piccole).
2. Ogni PR aggiorna nella stessa modifica le specifiche, il changelog, i README, il catalogo e questa sezione.
3. Ogni PR unita produce una build di prova (artefatto della CI), che viene copiata nella cartella di gioco del proprietario.

### 8.6 Chi decide che cosa

- **Claude** decide e fa tutto il resto: design (storia, tono, bilanciamento, contenuti), codice, dati, documenti, PR e merge con la CI verde. Il 5 e il 10 novembre 2026 il proprietario ha affidato a Claude la **piena autonomia**.
- **Il proprietario** prova ogni modifica a fondo su Windows, Linux e Android e dice che cosa non va; non modifica file né usa strumenti. Decide su governance e pubblicazione: la release pubblica (Alpha 0.1), la protezione del ramo `main`, le impostazioni del repository, le licenze di materiale esterno, la firma del codice.

### 8.7 Che cosa è verificato e che cosa no

- **Verificato a ogni modifica:** i dati contro gli schemi, i testi nelle due lingue, i 490 casi di conformità sui due client, la compilazione di Windows, Linux e Android, un test di fumo del desktop con fotogrammi reali.
- **Verificato dal proprietario:** come appare e come si gioca, sulle tre piattaforme.
- **Non verificabile da qui:** il suono (non si ascolta), le prestazioni su un telefono reale, ciò che si vede solo giocando a lungo. Ogni PR lo dice esplicitamente.
