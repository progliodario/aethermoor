# 03. Game design

> Tutto ciò che riguarda mondo, nomi e personaggi è una **proposta modificabile**: mi hai dato i temi, non i dettagli. I nomi sono provvisori e vivono nei file i18n e nei dati.
>
> **Stato (novembre 2026).** Nel gioco c'è un solo protagonista, Ren (senza dono), in un mondo di otto regioni con i nomi e i temi della tabella delle regioni qui sotto (ognuna ha anche un tono di parlata: caldo, mistico, burbero, fiorito, stoico, salato, cupo, erudito), la gilda con ranghi F-S, negozi, locande, Pietre della Soglia e le stagioni. Gli altri sette protagonisti, i doni, i compagni, i legami, la reincarnazione, i titoli e i tag, la base e l'agricoltura non ci sono ancora. Le scelte di tono, storia e bilanciamento sono del proprietario. Il catalogo di ciò che esiste è `docs/design/catalog.md`.

## 1. Pitch e pilastri

**Pitch:** otto anime vengono strappate al loro mondo e portate su Aethermoor, ognuna con un dono che spezza le regole. Chi scegli di essere cambia il tono, le regole e la storia. Ma il mondo è uno solo, e i destini si incrociano.

**Pilastri:**

1. **Un mondo, molti eroi.** Ogni protagonista gioca diversamente e racconta un genere diverso (commedia, dramma, noir, horror, cozy).
2. **Il cheat è una meccanica, non un trucco.** Ogni dono ha un indicatore, regole proprie e un prezzo da pagare.
3. **Isekai da vivere.** Gilda e ranghi, status window, titoli, tag, villaggio, cibo, compagni.
4. **Reincarnarsi è progredire.** Fine e inizio sono lo stesso gesto: ogni vita lascia qualcosa alla successiva.
5. **Comodo ovunque.** Sessioni da 10 minuti su telefono, da 3 ore su PC. Autosalvataggio, penalità lieve, controlli adattivi.

**Tono e rating:** commedia, avventura e dramma. Toni scuri solo dove il protagonista lo prevede. Target PEGI 12 / Teen: violenza stilizzata, nessun sangue realistico, tutti i personaggi adulti. Relazioni romantiche opzionali, senza contenuti espliciti (dissolvenza). Tema del "compagno liberato" gestito con sensibilità (vedi sezione 7).

## 2. Mondo di Aethermoor (bozza)

**Cosmologia.** Aethermoor è mantenuta da **Lyra, Dea della Soglia**, che chiama "Ospiti" da altri mondi per fermare la **Marea Oscura** che torna ogni ciclo. Il **Re dei Demoni** nasce e rinasce con la Marea. Gli Ospiti ricevono un **Dono** (il cheat), frammento della potenza di Lyra.

**Verità nascosta.** Il Ciclo non è un incidente: Lyra raccoglie le anime degli Ospiti caduti per tenere in vita il mondo. Il "vero finale" consiste nel decidere di spezzarlo (vedi sezione 5).

### Regioni

| # | Regione | Carattere | Bioma | Insediamenti chiave | Protagonista di partenza |
|---|---|---|---|---|---|
| 1 | **Verdalis** | Pianure, villaggi, gilda madre | Prati, boschi, fiumi | Aldermere (capitale della gilda), Fenwick, Soglia di Lyra | Ren |
| 2 | **Whisperwood** | Foresta elfica millenaria | Foresta fitta, radure | Sylvenar, Tana dei Cinquanta Nidi | Haruka |
| 3 | **Ironspine** | Montagne dei nani e miniere | Roccia, ghiacciai, vulcanelli | Karak-Dûn, Fucina Alta | Daichi |
| 4 | **Sunscar** | Deserto e città di mercanti | Dune, oasi, canyon | Qasr al-Zahar, Oasi dei Miraggi | Yuki |
| 5 | **Frostveil** | Tundra, antichi templi | Neve, ghiaccio, taiga | Hollow Nord, Torre Gelata | Lena |
| 6 | **Tidehaven** | Arcipelago e porti | Costa, isole, mare | Porto Belmare, Faro dei Sussurri | Marco |
| 7 | **Ashen Wastes** | Terre del Re dei Demoni | Cenere, rovine, magma | Cittadella Spenta, Fosse di Vhal | Gideon |
| 8 | **Lumeria (Isole Celesti)** | Accademia arcana e rovine volanti | Isole, nuvole, cristalli | Accademia di Lumeria | Sakura |

**Grafo delle regioni** (in `world.json`): archi pesati con la distanza di viaggio. La **difficoltà** di un luogo per un protagonista è funzione della distanza dalla sua regione di partenza (default: `danger_level = 1 + distanza_in_archi × 2`, con tetto 8). Ogni nemico ha una banda di livelli; l'adattamento è nei dati (`danger_curve`). Dungeon e boss principali hanno livello fisso consigliato, mostrato nel diario.

**Zone del mondo:** ogni regione ha 3-5 città/villaggi, 2-3 dungeon, 1 area boss, risorse uniche, un'attività secondaria tipica (pesca a Tidehaven, caccia nel Whisperwood, miniere a Ironspine, corse di cammelli a Sunscar, ecc.).

**Viaggio rapido:** Pietre della Soglia (checkpoint e punti di salvataggio, anche rapid travel una volta attivate), carovane a pagamento, cavalcature domate.

## 3. I protagonisti (8 per la versione 1.0)

Ogni protagonista ha: **prologo di reincarnazione** (30 min), **trama in 3 atti**, **dono con indicatore**, **albero del dono** (5 tier × ~12 nodi), **regione di partenza**, **3 compagni dedicati**, **boss finale personale**, **tono**.

| # | Nome | Reincarnazione | Dono (cheat) | Indicatore | Prezzo / limite | Tono | Stile di gioco |
|---|---|---|---|---|---|---|---|
| 1 | **Ren Takahashi**, impiegato di 27 anni | Camion | **Occhio del Sistema:** analizza nemici, scopre statistiche, copia abilità viste 3 volte | *Intuizione* | Statistiche base basse, dipende dall'osservazione | Commedia leggera | Spadaccino versatile, impara skill |
| 2 | **Sakura Mori**, studentessa di fisica | Esperimento di laboratorio | **Mana Infinito Ingovernabile:** PM mai esauriti | *Instabilità* | A instabilità alta gli incantesimi colpiscono anche gli alleati | Slapstick | Maga ad area, rischio/ricompensa |
| 3 | **Daichi Okabe**, vigile del fuoco | Crollo di un edificio | **Egida Eterna:** sopravvive a un colpo letale per scontro, riflette parte dei danni | *Egida* | Poco danno diretto, forza dai compagni | Dramma, onore | Tank/protettore, guida il party |
| 4 | **Haruka Aizawa**, veterinaria | Incidente d'auto | **Domatrice Universale:** doma qualunque creatura, anche i boss, in base al legame | *Legame* | Le creature domate combattono per lei, lei è fragile | Cozy, guaritore | Evocatrice con cavalcature |
| 5 | **Marco Ferri**, ingegnere e cuoco | Esplosione in cucina | **Sapere Moderno:** progetti di tecnologia e cucina impossibili per questo mondo | *Ingegno* | Risorse e tempo di costruzione | Avventura ingegnosa | Gadget, torrette, buff da cibo |
| 6 | **Yuki Shirogane**, ladra d'arte | Salto da un tetto | **Tasca Dimensionale:** inventario infinito, teletrasporto breve, lancio di oggetti | *Ombra* | Fragile, cooldown lunghi | Noir, intrigo politico | Assassina mobile, stealth |
| 7 | **Lena Voss**, medico legale | Assassinata | **Ritorno alla Morte:** a ogni morte ritorna all'ultima Pietra, conserva la memoria | *Memoria* | Ogni ritorno costa sanità mentale (penalità progressive) | Dark, psicologico | Puzzle di conoscenza, trappole segnalate |
| 8 | **Gideon Valmor**, ex re dei demoni reincarnato | Morto in battaglia contro Lyra | **Sovrano delle Tenebre:** comanda mostri e costruisce un dungeon | *Presenza* | Nemico del mondo, i PNG lo temono | Commedia nera, redenzione | Costruttore di dungeon, legioni |

**Futuri (post 1.0):** 9) **Slime** (reincarnato come slime, assorbe e evolve), 10) **Aurelia**, "cattiva" da gioco di seduzione (intrigo di corte, duelli, statistiche sociali), 11+) proposte della community.

### Dettaglio meccanica dei doni

1. **Occhio del Sistema:** `Analizza` costa 1 secondo di osservazione (anche in combattimento, a distanza). Dopo 3 analisi di un tipo di nemico si può "studiare" una sua skill (l'indicatore Intuizione si consuma per apprenderla). Albero: scoperta debolezze, copia a 2 slot, fusione di skill, "Errore del sistema" (ultimate: annulla una skill nemica).
2. **Mana Infinito:** niente barra PM. L'Instabilità cresce con l'uso e cala col tempo. Sotto 40: potenza normale. 40-80: +25% potenza. Oltre 80: +60% ma "sovraccarico" danneggia gli alleati e il lanciatore. Ultimate: *Singolarità* (area enorme, 10 s di stordimento al lanciatore).
3. **Egida Eterna:** una barra *Egida* assorbe danno al posto dei PV e si ricarica quando i compagni colpiscono. Ultimate: *Muro* (protegge tutto il party per 6 s).
4. **Domatrice:** ogni creatura ha un valore di *Legame* (0-100). Si doma con cibo e pazienza (minigioco), poi combatte come evocazione o compagna controllata dall'IA. Le cavalcature danno velocità e attacco in carica. Boss domabili con una sequenza speciale a metà scontro.
5. **Sapere Moderno:** albero di *Blueprint* (conserve, antibiotici, polvere nera "limitata", motore a vapore giocattolo, batterie alchemiche, radio a cristallo). Il cibo dà buff speciali; la torretta è un'entità posizionabile.
6. **Tasca Dimensionale:** *Blink* (teletrasporto breve), *Sacca* (inventario senza limite di peso), *Lancio* (qualsiasi oggetto come proiettile, danno in base al peso/rarità). Il furto è un sistema di gioco con rischio.
7. **Ritorno alla Morte:** alla morte il mondo torna allo snapshot dell'ultima Pietra (la memoria no). La *Memoria* registra posizioni di trappole, schemi dei boss e dialoghi che hanno portato al male. La sanità cala a ogni ritorno; a sanità bassa le allucinazioni ingannano il giocatore, ma una *Memoria* alta svela scorciatoie e segreti.
8. **Sovrano delle Tenebre:** modalità *Dungeon*: costruisce stanze e trappole in una mappa a griglia, evoca mostri con la *Presenza*, difende il dungeon da eroi invasori (mini-difesa a ondate), poi esce dal dungeon per le missioni nel mondo (con le legioni al seguito).

### Regola di bilanciamento dei doni

Ogni dono segue il triangolo **potere ↔ costo ↔ limite**: nessun dono rende il gioco banale; il limite è parte del divertimento. Tutti i doni devono funzionare in combattimento, esplorazione e almeno un sistema di vita (cucina, agricoltura, commercio, ecc.).

## 4. Compagni e PNG speciali

**Party:** 3 attivi (protagonista + 2) + riserve. Ogni compagno ha: ruolo (Tank, Mischia, Distanza, Mago, Supporto, Evocatore), profilo IA, albero abilità a 3 rami, 12 eventi di legame, equipaggiamento, preferenze (cibi, doni).

**Comandi in battaglia (touch e controller):** Segui / Resta / Attacca bersaglio / Difendi me / Usa skill. Profili IA: *Aggressivo*, *Equilibrato*, *Cauto*, *Supporto*, *Solo comandi*. L'IA è dichiarativa (stessa struttura dei `behavior`).

**Roster iniziale di 24 (bozza):**

| Archetipo | Esempi |
|---|---|
| Creature | Slime parlante *Pip*, lupo d'ombra *Kuro*, draghetto *Emberling*, spirito della foresta |
| Elfi | Arciera *Ilyana*, druido *Thalen* |
| Nani | Fabbra *Brunhild*, minatore burbero *Gorrik* |
| Bestie-umane | Guerriera volpe *Kitsu*, ladro gatto *Nyx* |
| Cavalieri | Ex cavaliere sconfitto *Sir Aldric*, paladina in fuga *Seraphine* |
| Liberati | *Mei* (ex prigioniera della Compagnia dei Catenieri), *Taro* (ex gladiatore) |
| Morti | Principessa lich *Morgana*, scheletro cuoco *Bones* |
| Demoni | Generale *Zahar* (alleato per Gideon), succube-sacerdotessa *Lilith* |
| Divini | Angelo caduto *Cael*, guardiano antico *Aegis-7* |
| Umani | Contabile del guild *Mira*, taverniere *Hobb*, studente *Pim* |

**Liberazione:** i personaggi liberati dalla Compagnia dei Catenieri non sono "acquistati" né posseduti. Il gioco tratta la schiavitù come un male da combattere: li si libera con missioni di sabotaggio e il legame è una libera scelta del personaggio (non esiste alcun meccanismo di proprietà).

**Tipi di legame (affinità 0-10):** conoscente → amico → fidato → intimo → legame profondo. Eventi di legame sbloccano abilità di coppia e dialoghi. Opzioni di relazione romantica a partire dal livello 8, **solo con personaggi adulti**, senza esclusività obbligatoria: puoi coltivare più legami; gli eventi di gelosia o di tensione sono comici o drammatici a seconda del tono del protagonista (opzionali, disattivabili nelle impostazioni).

## 5. Struttura narrativa

### Trama del protagonista (3 atti)

| Atto | Durata | Contenuto |
|---|---|---|
| Prologo | ~30 min | Morte e reincarnazione nel tono del protagonista, incontro con Lyra, primo villaggio |
| Atto I | ~2 h | Gilda, primo rango, primo compagno, primo dungeon, scoperta del dono |
| Atto II | ~2 h | Crisi regionale, incontro con altri Ospiti (come PNG con stato dal profilo), reclutamento, base |
| Atto III | ~2 h | Boss personale e scelta finale del protagonista |

~6-7 ore per protagonista; ~50 ore con tutti. La parte condivisa del mondo (città, gilda, dungeon, minigiochi) si riusa.

### Intreccio

- Gli altri protagonisti che hai già completato **compaiono come PNG** in base al profilo (es. Ren come eroe di rango A).
- Ogni protagonista ha un **segreto** che ne rivela un pezzo: dopo averne conclusi 4, si sblocca **L'Epilogo del Ciclo** (vera fine). Con tutti e 8 completati si sblocca la **Verità** (scelta di spezzare o mantenere il Ciclo).
- **Finali:** ogni protagonista ha 2 finali (Onore/Libertà); la scelta finale cambia il mondo di tutti i protagonisti successivi (flag nel profilo).

### Reincarnazione (meta-progressione)

- **Fine di una vita:** completare la trama, scegliere "Reincarnati" all'**Altare della Soglia**, morire in hardcore o usare l'Oggetto *Ruota dell'Anima*.
- **Echi dell'anima:** valuta del profilo. Si guadagnano con: boss sconfitti, quest completate, livello raggiunto, bestiario, titoli, legami. Formula: `echi = livello + boss*5 + quest/4 + titoli*2 + bestiario/10`.
- **Albero dell'Eredità** (profilo): bonus piccoli e permanenti (+5% XP, inventario +4, oro iniziale, un'abilità iniziale in più, nuova cavalcatura, migliori prezzi), e **slot di ricordi** (una skill o un titolo dal protagonista precedente).
- **Rango dell'anima:** aumenta con le reincarnazioni, dà piccole stat a tutti (+1 a ogni rango).
- **Sblocco protagonisti:** tre disponibili (Ren, Haruka, Daichi), gli altri si sbloccano incontrandoli come PNG o completando eventi ("incontra Sakura nell'Accademia", ecc.).
- **Camion-kun:** easter egg dell'inizio di Ren, un minigioco di schivata finto-drammatico.

## 6. Gilda dei avventurieri

- **Ranghi:** F, E, D, C, B, A, S. Ogni rango richiede **punti gilda** e un **esame** (combattimento o missione speciale).
- **Bacheca:** missioni generate da template per giorno; livello e ricompense scalano con il rango.
- **Vantaggi di rango:** sconti, accesso a dungeon, locali riservati, missioni uniche, alloggio gratuito, cavalcature.
- **Punti Gilda** alimentati da missioni, boss, commercio con la gilda.
- **Gilde rivali / fazioni (minori):** Compagnia dei Catenieri (antagonista), Ordine della Luce, Camera dei Mercanti, Cerchio dei Maghi, Clan delle Ombre. Ogni fazione ha reputazione (−100…+100) con effetti su prezzi, accesso e quest.

## 7. Titoli, tag, status window

### Status window

Pannello blu semitrasparente (stile "finestra di sistema") con: Nome, Titolo principale, Classe/Dono, Livello, PV/PM, 7 statistiche, derivate, Tag attivi, Skill, Rango della gilda, Echi, Ore giocate. Aggiornato in tempo reale. Navigabile da tastiera, controller, tocco.

### Titoli

- Si ottengono con condizioni (`unlock.when`). Se ne equipaggia **1 principale e 2 minori**.
- Danno piccoli bonus (stat, XP, prezzi) o cambi di dialogo.
- Esempi: *Sopravvissuto al Camion*, *Eroe del Villaggio*, *Cacciatore di Slime*, *Amico delle Bestie*, *Chef Leggendario*, *Re dei Mercanti*, *Distruttore di Dungeon*, *Il Dimenticato*, *Colui che Spezzò il Ciclo*, *Vita Lenta*.

### Tag

I tag sono **etichette di stato** che influenzano dialoghi, eventi e piccole meccaniche; possono essere permanenti o temporanei, visibili o nascosti.

| Categoria | Esempi |
|---|---|
| Origine | *Reincarnato dal Camion*, *Ex impiegato*, *Ex re dei demoni* |
| Carattere | *Pigro*, *Coraggioso*, *Gentile*, *Spietato*, *Goloso* |
| Stato | *Maledetto dalla sfortuna*, *Benedetto da Lyra*, *Ricercato*, *Affamato* |
| Mondo | *Amico dei nani*, *Nemico dei Catenieri*, *Sacro alla foresta* |

Un tag può avere modificatori (es. *Goloso*: cibo +20%, ma −10% se a stomaco vuoto), sbloccare scelte di dialogo e filtrare quest. Si acquisiscono con eventi e scelte; alcuni sono rimovibili.

## 8. Combattimento (azione in tempo reale)

- **Input:** movimento (stick/WASD), attacco base (combo a 3 colpi), 4 slot skill + 1 ultimate, schivata, parata/guardia, interazione, uso rapido di 3 oggetti.
- **Mira:** automatica verso il bersaglio più vicino nell'arco frontale (assist configurabile); blocco bersaglio opzionale; mouse/stick destro per mira libera.
- **Hitbox:** forme (arco, rettangolo, cerchio, linea) con frame di attivazione. Proiettili con traiettoria, velocità, penetrazione, rimbalzo.
- **Stagger (squilibrio):** ogni nemico ha una barra; riempita → stordito per 2 s, subisce danno extra. I boss hanno tacche.
- **Combo e concatenamenti:** annullare il recupero di una skill con la schivata entro 6 tick.
- **Resistenze e debolezze** visualizzate nel bestiario e dopo `Analizza`.
- **Numeri di danno** colorati per tipo; opzione per ridurre il rumore visivo.
- **Boss:** fasi con soglie di PV, arene con meccaniche (zone di pericolo, adds, pattern), checkpoint all'ingresso. Ogni regione ha un boss; ogni protagonista un boss personale; il Re dei Demoni è condiviso.
- **Difficoltà:** *Storia* (danno ricevuto −40%, bersaglio automatico forte), *Normale*, *Difficile* (+30% PV nemici, assist ridotto), *Hardcore* (permadeath → reincarnazione forzata con Echi doppi). Si può cambiare tranne da/verso Hardcore.
- **Morte:** −10% oro (max 500), stato Fatica per 2 minuti, respawn alla Pietra più vicina.

## 9. Skill, classi e alberi

- Ogni protagonista ha l'**albero del dono** (unico). Tutti condividono gli **alberi di classe** (acquistabili con punti abilità e maestri): Guerriero, Mago, Ladro, Ranger, Chierico, Evocatore, Artigiano.
- **Skill:** attive (con costo PM/cooldown, hitbox, effetti), passive, di movimento, reazioni (parata speciale), ultimate (caricata dal combattimento).
- **Equipaggiamento di skill:** 4 slot + 1 ultimate, riordinabili. Aggiornamento di skill: livelli 1-5 con potenza, costo, cooldown.
- **Punti abilità:** 1 per livello + extra da boss e quest. Reset a pagamento (cresce con i reset, poi tetto).

## 10. Oggetti, equipaggiamento e artigianato

- **Slot:** arma, secondaria/scudo, testa, corpo, mani, gambe/piedi, 2 accessori, cavalcatura, 1 titolo principale + 2 minori.
- **Armi:** spade, spadoni, daghe, lance, archi, bastoni, bacchette, pugni, martelli, armi da lancio.
- **Rarità** (6) con **affissi** casuali (max 3, scelti da tabella) e **tacche per rune**.
- **Nessuna durabilità** e niente rottura.
- **Mestieri:** Fabbro, Alchimista, Cuoco, Incantatore, Sarto, Ingegnere (Marco). Hanno livello e maestria.
- **Stazioni:** banco da lavoro, forgia, laboratorio alchemico, cucina, telaio. Si costruiscono e si potenziano nella base.
- **Ricette** si imparano da libri, maestri, esperimenti, scoperta di ingredienti.
- **Cibo:** piatti con buff di 5-30 minuti; combinazioni di ingredienti scoperte con sperimentazione ("ricettario" nel diario).

## 11. Vita lenta

### Agricoltura e allevamento

- Appezzamenti arabili sulla base e in luoghi del mondo. Colture con crescita a stadi (giorni di gioco), acqua, concime, stagioni. Qualità (1-5 stelle) in base a cura e fertilizzante.
- Allevamento: polli, mucche, "slime da latte", bestie domate (produzione giornaliera, felicità).

### Cucina

Minigioco opzionale a tempismo (o cottura automatica con qualità minore). Ricette a più ingredienti, tag di gusto e sinergie.

### Pesca e caccia

Minigioco di tensione sulla lenza (tocco/pulsante), pesci per regione/stagione/ora. Caccia con trappole e archi, tracce da seguire.

### Raccolta e mining

Nodi di risorse con ricrescita (giorni), strumenti (piccone, ascia, falce, canna) con livello.

### Villaggio / Base

- Ogni run ha una **base** (villaggio nascente) in una zona assegnata: griglia di costruzione con edifici: casa, fattoria, fucina, locanda, bottega, magazzino, torre di guardia, gilda locale, stalla, laboratorio, giardino, cappella, mura.
- **Residenti:** PNG e compagni assegnabili a lavori; produzione passiva giornaliera; benessere. Eventi di villaggio (festival, attacchi, ospiti).
- **Modalità Dungeon (Gideon):** la base è un dungeon con stanze, trappole, mostri; eroi invasori attaccano a ondate.
- Il tempo di costruzione procede in tempo di gioco; progressi non avanzano mentre si è in una scena (nessun avanzamento "offline").

## 12. Economia e scambi

- Negozi regionali con scorte, prezzi dinamici, mercanti ambulanti con oggetti rari e stagionali.
- Camera dei Mercanti: commercio tra regioni (differenze di prezzo, scorte), contratti, carovane.
- Aste (post 1.0). Nessuna microtransazione né valuta premium.

## 13. Minigiochi e attività secondarie

Pesca, cucina, domare, **Arena** (combattimenti a ondate con ricompense), **gioco di carte "Tre Re"** (post 1.0), **corse di cavalcature**, **esplorazione di rovine**, **caccia al tesoro** con mappe, **fotografia** di creature per il bestiario (post 1.0).

## 14. Bestiario e collezioni

Nemici, creature, ingredienti, pesci, minerali, piante, oggetti, titoli, tag, luoghi, personaggi. Ogni voce si sblocca con l'osservazione. Completamenti danno Echi e titoli.

## 15. Onboarding e ritmo

- Il prologo di ogni protagonista insegna movimento, attacco, schivata, interazione e il suo dono, in 10-15 minuti.
- Tutorial **contestuali e saltabili**, ricordabili dal diario.
- Ritmo: nuova meccanica ogni ~20 min nelle prime 3 ore; poi consolidamento e libertà.
- Accessibilità di gioco: modalità Storia, auto-battaglia dei compagni, assist di mira, daltonismo, ridotto movimento, sottotitoli, dimensione testo, comandi a una mano su mobile.

## 16. Budget di contenuto per protagonista

| Elemento | Quantità minima per l'1.0 |
|---|---|
| Quest principali | 18 (3 atti × 6) |
| Quest secondarie dedicate | 12 |
| Dialoghi con scelte | 120 |
| Compagni dedicati | 3 (+12 eventi di legame ciascuno) |
| Skill del dono | ~60 (5 tier × 12) |
| Nemici nuovi | 6 |
| Boss | 1 personale + 1 mini-boss |
| Aree/Dungeon | 1 dungeon + 1 area speciale |
| Ricette uniche | 8 |
| Titoli / tag unici | 6 / 4 |

Con 8 protagonisti, il volume totale è molto alto: la roadmap (documento 06) lo gestisce con modelli di contenuto e **valvole di portata**.
