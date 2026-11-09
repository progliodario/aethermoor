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

## 8. Stato e prossimi passi (aggiornato a novembre 2026)

### 8.1 Dove siamo

Aggiornato al 6 novembre 2026 (versione `0.0.1`, nessuna release pubblicata). Il gioco è giocabile su desktop con **otto protagonisti** (Ren, Sakura, Daichi, Haruka, Marco, Yuki, Lena, Gideon), un mondo di 16384² tile in streaming con otto regioni, 35 siti a mano, 60 creature, 135 oggetti e 110 missioni (`docs/design/catalog.md`).

| Milestone | Stato | Note |
|---|---|---|
| M0 Fondazioni | fatto | Repo, CI, ADR, schemi, scheletri dei due client |
| M1 Spec core e conformità | fatto | Numerica intera, RNG, hash, rumore, formule, i18n, loader dei pack; 23 file di vettori |
| M2 Motore base e arte vettoriale | fatto | Rasterizzatore proprio (ADR 0012), rig/clip, mappa, collisioni, camera |
| M3 Combattimento | quasi fatto | Fendente, colpo potente con mana, **schivata** con invulnerabilità, abilità magiche (matk), regole dei doni (rigenerazione di mana, salvezza dalla morte, cure, aggro), Analizza di Ren, 60 creature con comportamenti diversi, boss ed élite, XP, livelli, difficoltà bilanciata dal modello (`docs/design/balance.md`). **Mancano:** parata, stati alterati, elementi e debolezze (sono nei dati ma senza effetto), stagger, **suoni** (non c'è audio) |
| M4 Dialoghi, quest, inventario, salvataggi | quasi fatto | Dialoghi e quest con condizioni ed effetti, PNG, salvataggi v1 con tre partite e il protagonista per partita, zaino, negozi, equipaggiamento, diario, lingua, gilda con bacheca, lavori degli anziani e dei locandieri, laboratori, locande, **scelta del protagonista** con storia personale. **Mancano:** profilo condiviso ed export dei salvataggi, altre impostazioni, Alpha 0.1 con Fenwick e Aldermere a mano |
| M5 Mondo aperto | quasi fatto | Streaming, otto regioni che modellano il terreno, insediamenti, siti, stagioni, meteo (solo grafica), routine dei PNG, Pietre della Soglia, **mappa del mondo** con zoom, dettaglio per tile, mini mappa, meta e frecce. **Mancano:** risorse da raccogliere, città chiave scritte a mano, fiumi e strade sulla mappa, luci 2D, effetti del meteo sul gioco |
| M6 Sistemi di vita | iniziato | Oggetti usabili, mana e pozioni, negozi, equipaggiamento, locande. **Mancano:** agricoltura, cucina e qualità, crafting, pesca, caccia, base e residenti, economia dinamica, ricettario |
| M7 Compagni | da fare | Nessun compagno; i doni dei protagonisti non ne hanno ancora (domare, tasca dimensionale, costruire un dungeon) |
| M8 Progressione profonda | da fare | Alberi di abilità, titoli e tag, ranghi oltre la gilda, bestiario, reincarnazione e Albero dell'Eredità, profilo con sblocchi |
| M9 Contenuti | iniziato | Per ogni protagonista: storia, dono, due missioni personali. Mancano i prologhi, le trame in tre atti, i boss personali |
| M10-M12 | da fare | Rifinitura, audio, release 1.0 |

Verificato finora: la CI (Windows MSVC, Linux GCC, Android: test JVM e `assembleDebug`), 23 file di vettori eseguiti dai due client, e centinaia di fotogrammi reali del client desktop (`aethermoor --smoke-test --screenshot-dir=...`: gioco, mappa, pannelli, schermata di scelta). **Non verificato:** il client Android non è mai stato eseguito su un dispositivo o su un emulatore (si sa che compila e supera i test); non c'è stata una lunga sessione di gioco a mano, quindi il bilanciamento (200% di salute e 175% di attacco delle creature, scelto con il modello) e le regole dei doni sono da provare.

### 8.2 Direzione scelta: un mondo da isekai con molte storie

Il primo test in gioco ha confermato che le basi funzionano, e che il gioco deve diventare **molto più complesso**: un mondo con tanti insediamenti, una gilda viva, fazioni, e molte storie possibili, non una sola quest. Per arrivarci senza riscrivere codice a ogni storia, si applica un principio a tutto ciò che resta da costruire:

> **Ampiezza dai dati e dai modelli.** Insediamenti, PNG, missioni, dialoghi e storie sono descritti da dati (stamp, ruoli, modelli di quest, tabelle di nomi) e generati in modo deterministico dal seme; il codice conosce solo i meccanismi. Il materiale scritto a mano (città chiave, trama dei protagonisti, boss) si innesta nello stesso sistema.

Conseguenze sull'ordine del lavoro (tutte le tappe sono spec-first, in entrambi i client, con vettori di conformità):

1. **Regioni e insediamenti (M5f, fatto).** Il mondo si divide in regioni con nome, tema e livello di pericolo (dati); villaggi e città sono posti dal seme su una griglia di siti e disegnati da **stamp** (case, strade, piazza, mura) con **ruoli** di PNG (gilda, bottega, locanda, abitanti). Sulla mappa del mondo compaiono come punti di interesse.
2. **PNG di insediamento e dialoghi a ruoli (M5g, fatto).** I PNG compaiono e scompaiono con la finestra di chunk; hanno nome e aspetto generati; i dialoghi sono modelli con parametri (nome, insediamento, regione).
3. **Gilda, bacheca e quest a modelli (M4c, fatto; manca la reputazione con le fazioni).** Ranghi F-S, punti gilda, bacheca con missioni generate (sconfiggi, raccogli, consegna, scorta), catene di quest scritte a mano che usano gli stessi meccanismi, reputazione con le fazioni.
4. **Negozi, equipaggiamento, diario (M4d, fatto; mancano le impostazioni oltre alla lingua).** Monete e prezzi, comprare e vendere, slot di equipaggiamento (più armi e armature), diario delle quest, impostazioni e slot di salvataggio.
5. **Alpha 0.1** con un villaggio scritto a mano (Fenwick) e la gilda di Aldermere dentro il sistema generale (da fare). M5 (Pietre della Soglia, routine dei PNG, stagioni, dungeon in ogni regione) è fatto; restano M6-M9 come da roadmap.

Il 5 novembre 2026 il proprietario ha affidato a Claude le decisioni di design (protagonisti, bilanciamento, storia): i protagonisti sono otto, la difficoltà è tarata con il modello e le storie personali sono scritte (vedi 8.1). Restano al proprietario governance e pubblicazione (8.4).

### 8.3 Come si lavora

1. Una tappa alla volta, con PR piccole e CI verde prima del merge.
2. A ogni tappa si prepara una build da provare (artefatto della CI) e si raccolgono le impressioni.
3. Aggiornare questa sezione a ogni milestone chiusa.

### 8.4 Prossimi passi (decisi il 6 novembre 2026)

L'ordine tiene conto di quanto ogni pezzo cambia l'esperienza di chi gioca, di quanto è indipendente dagli altri e del rischio (si può compilare e provare solo in CI). Ogni passo segue il flusso del progetto: spec, riferimento, vettori, desktop, Android, dati e testi in italiano e inglese.

1. **Audio sintetizzato** (spec 14, M3/M10). **Fatto il 6 novembre 2026: gli effetti** (14 ricette in `data/base/audio/sfx/`, la stessa sintesi in C++ e Kotlin, suite `audio`, riproduzione desktop con SDL e Android con libGDX, `F8` per il muto); **restano** passi, musica per regione, ambiente e le impostazioni di volume (passo 3). È la mancanza più grande: il gioco era muto. Una piccola sintesi in codice (onde, rumore, inviluppi) descritta nei dati: colpo, danno, schivata, mana, oggetto, passi, UI, e una musica d'ambiente per regione. Desktop con SDL audio, Android con libGDX. Prima si scrive la spec dei suoni come ricette (come le ricette d'arte); non si possono fare vettori di ascolto, quindi si controllano forma d'onda e durata.
2. **Completare il combattimento** (M3). **Fatto il 9 novembre 2026:** elementi (l'arma ha un elemento, le creature debolezze e resistenze; spec 05 "Elements"), stati alterati sulle creature (bruciatura, gelo, stordimento, indebolimento; "Status effects") e la parata ("Parry": finestra, nessun danno, stordimento dell'attaccante), tutto con vettori in entrambi i client. **Restano:** stati alterati sul giocatore, elemento delle abilità, stagger dei boss; poi riprovare il bilanciamento con il modello esteso.
3. **Profilo e impostazioni** (M4). **Fatto:** i quattro volumi in `settings.json` (pannello `F10` sul desktop, pulsante su Android). **Restano:** `profile.json` condiviso fra le partite, export e import dei salvataggi (`.aethersave`), tasti configurabili. Prerequisito della reincarnazione.
4. **Alpha 0.1** (M4): Fenwick e Aldermere scritti a mano nel sistema dei siti, prologo breve per protagonista, tag `v0.1.0` e artefatti di release (zip Windows, tar.gz Linux, APK di debug firmato in modo semplice). **Decisione del proprietario:** quando pubblicare (una release pubblica, la protezione del ramo `main`).
5. **Verifica su dispositivo Android** (rischio R4/R6): provare un APK su un telefono o un emulatore, controllare tocco, bottoni, orientamento e prestazioni, e correggere ciò che si vede. Serve una macchina con l'Android SDK: non si può fare da qui.
6. **Raccolta e mestieri** (M5/M6): risorse da raccogliere nel mondo (erbe, minerali), crafting con qualità, cucina; il laboratorio degli anziani esiste già come base.
7. **Compagni** (M7): un compagno per protagonista (spec 10), IA, comandi, legame; i doni di Haruka (domare) e Gideon (comandare) ne dipendono.
8. **Progressione** (M8): titoli, tag, bestiario, reincarnazione.
9. **Qualità continua** (`gen_conformance.py --check` è ora in CI): CodeQL, ktlint e detekt, golden visivi dei fotogrammi del test di fumo, fiumi e strade sulla mappa, luci 2D.

Le decisioni di design (storia, tono, bilanciamento, protagonisti) sono state affidate a Claude dal proprietario il 5 novembre 2026; restano **al proprietario** le decisioni su governance e pubblicazione (release pubblica, protezione del ramo, impostazioni del repository, licenze di materiale esterno, firma del codice).
