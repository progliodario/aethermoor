# Aethermoor

> Titolo provvisorio. Un action RPG isekai fantasy, visto dall'alto e in tempo reale, in grafica vettoriale. Gratuito, open source, senza rete e senza pubblicità.
>
> English version: [README.en.md](README.en.md)

Otto persone del nostro mondo vengono portate su Aethermoor dalla dea Lyra, ognuna con un **dono** che spezza le regole. Scegli chi essere: cambiano il tono della storia, il modo di combattere e il compagno che ti segue. Il mondo è uno solo, enorme, e lo esplori come vuoi.

Come in ogni buon isekai, **il protagonista è molto più forte di ciò che incontra**: gli scontri sono fatti per essere facili e spettacolari, non per bloccarti.

## Indice

- [A che punto è](#a-che-punto-è)
- [Che cosa c'è nel gioco](#che-cosa-cè-nel-gioco)
- [I protagonisti](#i-protagonisti)
- [Come si prova](#come-si-prova)
- [Comandi](#comandi)
- [Come è fatto il progetto](#come-è-fatto-il-progetto)
- [Struttura delle cartelle](#struttura-delle-cartelle)
- [Per chi sviluppa](#per-chi-sviluppa)
- [Come si lavora qui](#come-si-lavora-qui)
- [Documentazione](#documentazione)
- [Che cosa manca](#che-cosa-manca)
- [Contribuire e licenza](#contribuire-e-licenza)

## A che punto è

**Versione di prova giocabile** (0.0.1, non ancora pubblicata come release). Si gioca dall'inizio su tre piattaforme: Windows, Linux e Android.

| | Stato |
|---|---|
| Windows e Linux | compilati e provati dalla CI a ogni modifica; provati in gioco dal proprietario |
| Android 11+ | APK di debug compilato e provato dalla CI; provato in gioco dal proprietario |
| Regole di gioco | uguali sui due client: 30 gruppi di vettori di conformità (435 casi) eseguiti da entrambi |
| Lingue | italiano e inglese, complete |
| Suono | effetti sonori sintetizzati dal gioco; musica e suoni d'ambiente sono scritti ma **spenti** finché non suonano bene |

## Che cosa c'è nel gioco

**Mondo**

- Un mondo aperto di 16384 x 16384 caselle generato da un seme, sempre uguale a parità di seme, caricato a pezzi mentre cammini.
- Otto regioni con terreno, creature, negozi e modo di parlare propri; giorno e notte, quattro stagioni, meteo.
- Circa 130 insediamenti, 44 luoghi fatti a mano (sotterranei con guardiano, tane, nidi, avamposti con un viandante e la sua storia), e due paesi scritti a mano: **Fenwick**, il villaggio dove cominci, e **Aldermere**, la città della gilda madre, con persone che hanno un nome e missioni proprie.
- Pietre della Soglia per curarsi e viaggiare fra i posti già visitati.
- Mappa del mondo con zoom, meta da segnare e mini mappa; si scopre la terra in un quadrato di 5 x 5 celle (640 caselle) intorno a te.

**Combattimento**

- Attacco, colpo potente che costa mana, schivata con un momento di invulnerabilità, parata che stordisce chi ti colpisce.
- Sei elementi (fuoco, acqua, vento, terra, luce, buio): armi e abilità ne hanno uno, le creature hanno debolezze e resistenze.
- Stati alterati su creature e giocatore: bruciatura, gelo, stordimento, indebolimento.
- Stagger: i colpi riempiono una barra sotto la vita della creatura; piena, la creatura resta spezzata per due secondi e subisce più danno.
- 68 creature con comportamenti diversi, 27 guardiani e 8 Echi, i boss personali dei protagonisti.

**Vita e progressione**

- Gilda degli avventurieri con bacheca e commissioni, 214 missioni, negozi, locande, lavori degli anziani.
- 157 oggetti; raccolta da cespugli, alberi, rocce e cactus; 28 ricette (pozioni, infusi ed elisir delle regioni, piatti cucinati al fuoco, equipaggiamento, ed equipaggiamento pregiato all'incudine delle città).
- Un compagno per protagonista: ti segue, combatte, resta dove gli dici, e il suo legame cresce con le sue vittorie.
- Titoli del modo di giocare che cambiano il gioco: il Raccoglitore trova di più, l'Artigiano crea di più, la Guardia incrollabile para più a lungo, il Veterano guadagna più esperienza.
- Un albero di dieci talenti: un punto per livello, quattro radici (attacco, vita, mana, difesa), un secondo anello che si apre al rango 5 (critico, secondo fiato, magia, velocità) e una corona (Leggenda, Baluardo).
- Bestiario, 15 titoli che aumentano l'attacco, e un profilo comune a tutte le partite: ogni titolo mai ottenuto dà un po' di vita in più a ogni partita (gli "echi"), e una partita arrivata al livello 10 può **reincarnarsi**: finisce, ogni vita passata dà +3% di vita a tutte le successive, e metà del suo oro passa in eredità alla prossima partita nuova.
- Tre partite separate, salvataggio automatico, esportazione e importazione di una partita in un file.

Il catalogo completo dei contenuti, generato dai dati, è in [`docs/design/catalog.md`](docs/design/catalog.md).

## I protagonisti

Ognuno ha un prologo con Lyra, un dono, due abilità d'attacco, due missioni personali e una storia completa in tre atti, data da Suor Maren ad Aldermere: "Il primo eco" a Verdalis, "Il secondo eco" e "L'ultimo eco" in altre regioni (Ren nelle miniere di Ironspine e nella Cripta di Ossidiana, Sakura all'osservatorio di Lumeria, Gideon nel suo vecchio regno...), tre missioni per atto, ognuno chiuso da un guardiano, e un epilogo contro il proprio **Eco**: il momento che lo ha portato su Aethermoor, diventato una creatura, in uno degli otto santuari intorno alla partenza.

| Protagonista | Chi era | Dono | Tono | Compagno |
|---|---|---|---|---|
| Ren Takahashi | impiegato, investito da un camion | vede i numeri di ciò che lo attacca (Analizza) | commedia leggera | Orbe, un fuoco fatuo |
| Sakura Mori | studentessa di fisica | mana enorme, colpisce con la magia | comica | Newton, un gufo |
| Daichi Okabe | vigile del fuoco | uno scudo che lo salva dalla morte | dramma | Brace, un lupo |
| Haruka Aizawa | veterinaria | capisce e cura le creature | accogliente | Pip, uno slime |
| Marco Ferri | ingegnere e cuoco | il sapere del mondo moderno | avventura | Pentola, un granchio |
| Yuki Shirogane | ladra d'arte | una tasca che nessuno può perquisire | noir | Ombra, un pipistrello |
| Lena Voss | medico legale | vede ciò che uccide, e ha un'altra possibilità | cupo | Mortina, un ragno |
| Gideon Valmor | il Re Demone, reincarnato | le creature lo temono | commedia nera | Tenebra, un lupo d'ombra |

Regole e numeri di ognuno: [spec 18](docs/spec/18-protagonists.md).

## Come si prova

Non c'è ancora una release: le versioni di prova sono gli **artifact della CI** di GitHub (pagina *Actions*, ultima esecuzione riuscita su `main`, conservati 30 giorni).

| Piattaforma | Artifact | Come si avvia |
|---|---|---|
| Windows | `aethermoor-windows-msvc` | scompatta e avvia `aethermoor.exe`, tenendo la cartella `data` accanto |
| Linux | `aethermoor-linux-gcc` | scompatta e avvia `./aethermoor`, con la cartella `data` accanto |
| Android 11+ | `aethermoor-debug-apk` | installa l'APK (serve permettere le app da origini sconosciute) |

Il gioco sceglie italiano o inglese dalla lingua del sistema (`F2` la cambia). Si apre su tre partite: una partita nuova chiede chi essere. Il file [`desktop/PLAY.txt`](desktop/PLAY.txt), incluso nella versione di prova, elenca tutti i comandi e che cosa provare.

## Comandi

**Tastiera** (il gamepad è supportato: levetta sinistra, `A` attacca, `X` parla, `RB` colpo potente, `LB` parata, `B` schivata)

| Azione | Tasto | Azione | Tasto |
|---|---|---|---|
| Muoversi | `WASD` o frecce | Zaino | `I` |
| Attaccare | `J` o `Spazio` | Diario con stato, titoli, bestiario | `Q` o `V` |
| Colpo potente | `K` | Mappa del mondo | `M` |
| Schivata | `L` o `Maiusc` | Mini mappa | `N` |
| Parata | `U` | Creazione, e talenti con `Tab` | `C` |
| Parlare, toccare una pietra, raccogliere | `E` | Compagno: resta / segui | `H` |
| Analizza (Ren) | `Z` | Volumi | `F10` |
| Salvataggio rapido / carica | `F5` / `F9` | Suono sì / no | `F8` |
| Chiudere un pannello, tornare alle partite | `Esc` | Lingua | `F2` |

La scritta sopra ciò che hai vicino dice che cosa farà `E`: *Parla*, *Tocca la pietra* o *Raccogli*. Ogni azione può avere un tasto in più a tua scelta: `F4` nel gioco apre il pannello dei tasti (oppure si compila il file `keys.json` accanto alle impostazioni).

**Android:** la metà sinistra dello schermo è una levetta che compare dove tocchi; un tocco a destra attacca; i pulsanti in basso a destra sono schivata, colpo potente e parata; in alto a sinistra ci sono zaino, mappa, diario, lingua, suono, creazione e il pulsante del compagno. Il tasto Indietro chiude un pannello o torna alle partite. Tutti i dettagli: [spec 16](docs/spec/16-input.md).

## Come è fatto il progetto

Due programmi **separati**, scritti in due linguaggi, che devono comportarsi in modo **identico**:

| Client | Cartella | Tecnologia |
|---|---|---|
| Windows e Linux | [`desktop/`](desktop) | C++20, SDL3, rasterizzatore vettoriale scritto in casa ([ADR 0012](docs/adr/0012-in-house-software-rasterizer.md)) |
| Android 11+ | [`android/`](android) | Kotlin, libGDX, lo stesso rasterizzatore riscritto in Kotlin |

Quello che li tiene uguali:

1. **Le specifiche** in [`docs/spec/`](docs/spec): ogni regola di gioco è scritta lì prima del codice.
2. **Un'implementazione di riferimento in Python** in [`tools/reference/`](tools/reference), che esegue le stesse regole.
3. **I vettori di conformità** in [`tests/conformance/`](tests/conformance): casi con ingressi e risultati attesi, generati dal riferimento. I test dei due client li eseguono tutti; se un client devia, la CI fallisce.
4. **I dati** in [`data/`](data): creature, oggetti, missioni, dialoghi, arte, suoni, mondo e testi sono file JSON letti da entrambi i client. Nel codice non ci sono nomi, testi o numeri di bilanciamento.

Altre scelte importanti: la matematica di gioco è **solo intera** (percentuali e permille), la generazione del mondo è **deterministica** (interi e virgola fissa, niente `float`), la grafica è fatta di **ricette vettoriali** in JSON disegnate dal rasterizzatore, e anche i suoni sono ricette sintetizzate dal gioco. Le decisioni di architettura sono negli [ADR](docs/adr/README.md).

## Struttura delle cartelle

```text
docs/        documentazione
  plan/        piano del progetto, roadmap, rischi (italiano)
  spec/        regole normative per i due client (inglese)
  design/      stile grafico, catalogo dei contenuti e rapporto di bilanciamento (generati)
  adr/         decisioni di architettura
  guides/      come aggiungere contenuti
  dev/         come preparare l'ambiente e compilare
schemas/     JSON Schema di ogni tipo di dato
data/base/   il pacchetto ufficiale: arte, suoni, creature, oggetti, abilità, protagonisti, compagni,
             missioni, dialoghi, mondo, ricette, titoli, testi in italiano e inglese
tests/       vettori di conformità condivisi (generati: non si modificano a mano)
tools/       script Python: validazione, riferimento delle regole, generatori di dati e arte, ship.py
desktop/     client Windows e Linux (C++, CMake, vcpkg)
android/     client Android (Kotlin, Gradle): core (regole, JVM pura), game (libGDX), app (avvio)
```

## Per chi sviluppa

Serve Python 3.12 o più recente per dati e strumenti; per compilare i client servono CMake, Ninja e vcpkg (desktop) e JDK 17 con l'Android SDK (Android). La guida completa è [`docs/dev/setup.md`](docs/dev/setup.md).

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # su Linux: .venv/bin/pip
python tools/validate_data.py                         # controlla dati, schemi e testi
python tools/gen_conformance.py --check               # i vettori corrispondono al riferimento?
```

```bash
# desktop
cmake --preset windows-release        # oppure linux-release
cmake --build --preset windows-release
ctest --preset windows-release

# android
cd android && gradle :core:test :app:assembleDebug
```

Gli script di tutti i giorni sono descritti in [`tools/README.md`](tools/README.md). I più usati:

| Script | A che cosa serve |
|---|---|
| `validate_data.py` | controlla ogni file di dati contro il suo schema, gli ID e i testi nelle due lingue |
| `gen_conformance.py` | rigenera i vettori di conformità dal riferimento Python |
| `make_*.py` | generatori di dati da tabelle nel codice (ricette, titoli, compagni, prologhi, suoni, arte, timbri dei luoghi) |
| `make_catalog.py`, `balance_report.py` | scrivono il catalogo dei contenuti e il rapporto di bilanciamento |
| `ship.py` | controlli, commit firmato, PR, attesa della CI e merge in un solo comando |

Per aggiungere un oggetto, una creatura, una missione, una ricetta, un titolo, un luogo, una regione o una lingua c'è la [guida](docs/guides/add-content.md): quasi tutto è solo dati.

## Come si lavora qui

Il progetto è sviluppato dal proprietario insieme a Claude, un assistente AI che scrive codice, dati e documenti. Le regole di lavoro sono in [`CLAUDE.md`](CLAUDE.md); in breve:

- **Prima la specifica**, poi riferimento, vettori, desktop e Android nella stessa modifica.
- **Tutto è dato**: niente nomi, testi o numeri nel codice; ogni testo in italiano **e** inglese.
- **PR piccole**, una cosa per volta, unite solo con la CI verde.
- Le decisioni di design (storia, tono, bilanciamento) sono delegate a Claude; quelle di pubblicazione e di gestione del repository restano al proprietario.
- Le prove in gioco, su Windows, Linux e Android, le fa il proprietario.

## Documentazione

| Che cosa cerchi | Dove |
|---|---|
| Il piano, la roadmap e lo stato delle milestone | [`docs/plan/`](docs/plan/README.md) (italiano) |
| Le regole di gioco, una per documento | [`docs/spec/`](docs/spec/README.md) |
| Tutti i contenuti in tabelle | [`docs/design/catalog.md`](docs/design/catalog.md) |
| Come aggiungere contenuti | [`docs/guides/add-content.md`](docs/guides/add-content.md) |
| Perché il progetto è fatto così | [`docs/adr/`](docs/adr/README.md) |
| Che cosa è cambiato | [`CHANGELOG.md`](CHANGELOG.md) |
| Indice di tutta la documentazione | [`docs/index.md`](docs/index.md) |

## Che cosa manca

Le prossime cose, in ordine (dettagli nella [roadmap](docs/plan/06-roadmap-rischi-backlog.md)):

- **A breve:** più controlli automatici sulla grafica, la qualità degli oggetti creati.
- **Verso l'Alpha 0.1:** abilità attive nuove nell'albero, tag, la scelta di cosa portare nella reincarnazione, qualità degli oggetti e banchi da lavoro, un sintetizzatore migliore per riaccendere ambiente e musica.
- **Verso la 1.0:** base e residenti, agricoltura e pesca, economia dinamica, accessibilità, altre lingue, strumenti per chi fa mod.

## Contribuire e licenza

Leggi [CONTRIBUTING.md](CONTRIBUTING.md), il [Codice di condotta](CODE_OF_CONDUCT.md), [GOVERNANCE.md](GOVERNANCE.md) e [SECURITY.md](SECURITY.md).

Codice: [GPL-3.0-or-later](LICENSE). Contenuti (dati, testi, arte, documenti di design): [CC BY-SA 4.0](LICENSE-CONTENT.md). Componenti di terzi: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
