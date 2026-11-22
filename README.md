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
- [Come si lavora qui (anche con un'AI)](#come-si-lavora-qui-anche-con-unai)
- [Documentazione](#documentazione)
- [Che cosa manca](#che-cosa-manca)
- [Contribuire e licenza](#contribuire-e-licenza)

## A che punto è

**Versione di prova giocabile** (0.0.1, non ancora pubblicata come release). Si gioca dall'inizio alla fine su Windows, Linux e Android 11+: la CI compila e prova i tre a ogni modifica, e il proprietario li prova in gioco.

I numeri del gioco, contati dai dati (non si scrivono a mano: li aggiorna `python tools/make_facts.py`, e un test fallisce se sono vecchi):

<!-- facts:begin -->
| Che cosa | Quanti (contati dai dati da `tools/make_facts.py`) |
|---|---|
| Mondo | 8 regioni, 45 luoghi fatti a mano (sotterranei, tane, avamposti, santuari, Fenwick, il cottage dell'Ospite, Aldermere) e circa 130 insediamenti generati |
| Protagonisti | 8, ognuno con un compagno (8 compagni) e una storia in sei atti (112 missioni di storia) |
| Creature | 75, di cui 27 guardiani e 8 Echi |
| Missioni | 354 (24 storie dei paesani) |
| Oggetti e ricette | 279 oggetti, 81 ricette (8 segrete) |
| Progressione | 45 titoli, 8 tag, 16 talenti, 26 imprese |
| Persone con nome | 48 nei dati del mondo, oltre ai paesani generati |
| Suono | 174 effetti sonori sintetizzati (musica e ambiente spenti) |
| Testi | 3828 chiavi, in italiano e inglese |
| Regole uguali sui due client | 30 file di vettori di conformità, 573 casi, eseguiti dai test C++ e Kotlin |
| Documenti | 18 specifiche, 13 ADR |
<!-- facts:end -->

**Fatto e da fare, in una riga per parte** (il dettaglio voce per voce è nella [sezione 8 della roadmap](docs/plan/06-roadmap-rischi-backlog.md#8-stato-e-prossimi-passi)):

| Parte | Fatto | Da fare |
|---|---|---|
| Fondamenta, regole, CI | tutto, anche i fotogrammi del test di fumo controllati in CI | ktlint e detekt in CI |
| Grafica | arte da anime per tutto, persone viste di fronte, di lato e di spalle, luce dell'ora, vento, acqua, ombre, font del pack | — |
| Combattimento | completo: elementi, stati, parata, stagger, guardiani, abilità a comando | ritocchi, sempre verso scontri facili |
| Mondo | enorme, otto regioni, città, sotterranei, meteo che nasconde e rallenta, vento che spinge, nebbia e temporali | prestazioni misurate su un telefono |
| Missioni e storie | storie in sei atti per ogni protagonista, storie dei paesani, gilda, leggende, taglie | la modalità Dungeon di Gideon |
| Vita | raccolta, pesca, caccia, orti, animali, bauli condivisi, il cottage dell'Ospite con i suoi mobili, venditori ambulanti, ricette segrete, cibi con effetti | carri che si vedono viaggiare, una casa più grande |
| Compagni | uno per protagonista con comandi, legame e cura; Haruka doma un secondo compagno | più compagni scelti dal giocatore |
| Progressione | talenti con abilità, titoli con effetti, bestiario, reincarnazione con eredità, imprese che danno echi, rune sulle armi, tag da indossare, armi e armature con affissi tirati a sorte (anche su ventiquattro pezzi comuni) e ritemprati all'incudine o dai fabbri, pezzi con due affissi, doni delle imprese | affissi che si scelgono |
| Accessibilità | consigli, numeri dei danni e lampi disattivabili, testo grande, tasti configurabili | — |
| Uscita | versioni di prova dalla CI | release Alpha 0.1 e poi 1.0 (decide il proprietario) |

## Che cosa c'è nel gioco

Il catalogo completo, generato dai dati, è in [`docs/design/catalog.md`](docs/design/catalog.md).

**Mondo**

- Un mondo aperto di 16384 x 16384 caselle generato da un seme (sempre uguale a parità di seme), caricato a pezzi mentre cammini; otto regioni con terreno, creature, negozi e modo di parlare propri.
- Giorno e notte, quattro stagioni, meteo: la pioggia e la notte ti nascondono alle creature, pioggia e neve le rallentano, la pioggia fa crescere prima gli orti, il vento alle spalle ti fa camminare più veloce, la nebbia ti nasconde, nei temporali i fulmini colpiscono le creature che ti inseguono.
- Insediamenti generati e luoghi fatti a mano: sotterranei e tane con guardiano, nidi, otto avamposti (con un viandante, un abitante del posto e un venditore ambulante), otto santuari degli Echi, **Fenwick** (dove cominci), **il cottage dell'Ospite** a est di Fenwick e **Aldermere**, la città della gilda madre.
- Pietre della Soglia per curarsi e viaggiare; mappa del mondo con zoom, meta da segnare e mini mappa; ogni missione segna dove andare.

**Combattimento**

- Attacco, colpo potente che costa mana, schivata con un attimo di invulnerabilità, parata che stordisce.
- Sei elementi con debolezze e resistenze, stati alterati (bruciatura, gelo, stordimento, indebolimento) su creature e giocatore, stagger.
- Guardiani con la loro barra in cima allo schermo, e otto Echi, i boss personali dei protagonisti.
- Facile di proposito: il protagonista è fortissimo, ed è il tema del gioco.

**Persone e missioni**

- Gilda con ranghi e bacheca, negozi, locande, lavori degli anziani, favori dei locandieri, botteghe, il Libro delle Leggende, le taglie su ogni guardiano.
- I paesani di ogni regione raccontano i loro guai in tre missioni; persone con nome a Fenwick (Bran, Odile, Tobin, Nonna Brin), ad Aldermere (Hestia, Rook, Selwyn, Wendel, Suor Maren, Corvin) e negli avamposti.
- Quattro fazioni (la Gilda, l'Anello dei Viandanti, i Cronisti, la Gente) con titoli e doni; la fama nelle regioni abbassa i prezzi e cambia il saluto della gente.

**Vita**

- Raccolta da alberi, cespugli, rocce e dalla scenografia selvatica; pesca nei canneti; caccia a cinghiali, alci e volpi delle dune.
- Orti in ogni villaggio, pollai e recinti delle capre; ricette al falò e all'incudine, opere pregiate, un piatto segreto per regione insegnato dal bottegaio.
- Cibi e infusi che fortificano, proteggono, rigenerano o fanno correre; una pozione che purifica.
- Un **baule** in ogni villaggio e città: tutti tengono le stesse cose.
- Il **cottage dell'Ospite**: baule, falò, incudine, orti, galline, una capra e una Pietra della Soglia; Nonna Brin te lo regala dopo i suoi tre favori. Dieci tappeti, in casa e in giardino, aspettano i **mobili** che costruisci all'incudine (letto, rastrelliera, libreria, essiccatoio, manichino, banco, panchina, spaventapasseri, bersaglio, lanterna di pietra), e ognuno ti aiuta ovunque come un titolo.
- **Residenti**: quando una regione ti conosce (sei missioni finite lì), qualcuno si trasferisce nel suo avamposto, ti saluta e ti regala una runa; con otto missioni arriva un colono in ogni villaggio della regione, con il suo mestiere (fornaia, scalpellino, pescatore del ghiaccio...), una missione e una bottega.
- Negozi con giorni di mercato, merci di altre regioni, pezzi rari per gli amici; pagano meno se vendi troppo della stessa cosa. Corvin ad Aldermere e un venditore in ogni avamposto portano ogni giorno le merci di una regione diversa; Odo, il capo carovana, ogni giorno è in un avamposto diverso. Gli orti crescono più svelti in primavera e più lenti d'inverno, e ogni pianta dà di più nella sua stagione; Odo ha tre commissioni per la carovana.

**Progressione**

- Livelli, un albero di talenti con abilità (due da usare con un tasto), titoli che cambiano il gioco, un bestiario con le debolezze; **rune** fatte all'incudine da incidere sull'arma, che allora colpisce più forte e con l'elemento della runa; **tag**, tratti guadagnati da come giochi, da indossare uno alla volta; **affissi**: ogni regione ha un'arma e un'armatura con un bonus in più, lasciate dai suoi guardiani, con un affisso tirato a sorte (dal 100 al 160%).
- Un profilo comune a tutte le partite: titoli, vite passate e **imprese** danno "echi" (salute in più a ogni partita); ogni impresa fatta lascia un dono nello zaino di ogni partita nuova; dal livello 10 una partita può **reincarnarsi** e lasciare in eredità metà dell'oro e l'arma.
- Un compagno per protagonista che segue, combatte, resta, torna e cura; Haruka doma le creature e l'ultima resta con lei.

## I protagonisti

Ognuno ha un prologo con Lyra, un dono, due abilità d'attacco, due missioni personali e una storia in cinque atti data da Suor Maren ad Aldermere: "Il primo eco" a Verdalis, il secondo e il terzo in altre regioni, l'epilogo contro il proprio **Eco** (il momento che lo ha portato qui, diventato una creatura, in uno degli otto santuari intorno alla partenza) "Una vita qui", i primi passi della vita nuova, e "Due Ospiti", le tracce di un altro protagonista venuto in un'altra vita del mondo.

| Protagonista | Chi era | Dono | Tono | Compagno |
|---|---|---|---|---|
| Ren Takahashi | impiegato, investito da un camion | vede i numeri di ciò che lo attacca (Analizza) | commedia leggera | Orbe, un fuoco fatuo |
| Sakura Mori | studentessa di fisica | mana enorme, colpisce con la magia | comica | Newton, un gufo |
| Daichi Okabe | vigile del fuoco | uno scudo che lo salva dalla morte | dramma | Brace, un lupo |
| Haruka Aizawa | veterinaria | capisce, cura e doma le creature | accogliente | Pip, uno slime |
| Marco Ferri | ingegnere e cuoco | il sapere del mondo moderno | avventura | Pentola, un granchio |
| Yuki Shirogane | ladra d'arte | una tasca che nessuno può perquisire | noir | Ombra, un pipistrello |
| Lena Voss | medico legale | vede ciò che uccide, e ha un'altra possibilità | cupo | Mortina, un ragno |
| Gideon Valmor | il Re Demone, reincarnato | le creature lo temono, il suo compagno colpisce il doppio | commedia nera | Tenebra, un lupo d'ombra |

Regole e numeri di ognuno: [spec 18](docs/spec/18-protagonists.md).

## Come si prova

Non c'è ancora una release: le versioni di prova sono gli **artifact della CI** di GitHub (pagina *Actions*, ultima esecuzione riuscita su `main`, conservati 30 giorni).

| Piattaforma | Artifact | Come si avvia |
|---|---|---|
| Windows | `aethermoor-windows-msvc` | scompatta e avvia `aethermoor.exe`, tenendo la cartella `data` accanto |
| Linux | `aethermoor-linux-gcc` | scompatta e avvia `./aethermoor`, con la cartella `data` accanto |
| Android 11+ | `aethermoor-debug-apk` | installa l'APK (serve permettere le app da origini sconosciute) |

Il gioco sceglie italiano o inglese dalla lingua del sistema (`F2` la cambia). Si apre su tre partite; una partita nuova chiede chi essere. Il file [`desktop/PLAY.txt`](desktop/PLAY.txt), incluso nella versione di prova, elenca tutti i comandi e che cosa provare.

## Comandi

**Tastiera** (anche gamepad: levetta sinistra, `A` attacca, `X` parla, `RB` colpo potente, `LB` parata, `B` schivata)

| Azione | Tasto | Azione | Tasto |
|---|---|---|---|
| Muoversi | `WASD` o frecce | Zaino | `I` |
| Attaccare | `J` o `Spazio` | Diario con stato, titoli, bestiario | `Q` o `V` |
| Colpo potente | `K` | Mappa del mondo / mini mappa | `M` / `N` |
| Schivata | `L` o `Maiusc` | Creazione, e talenti con `Tab` | `C` |
| Parata | `U` | Compagno: resta / segui, torna | `H`, `G` |
| Parlare, toccare una pietra, raccogliere, coltivare, aprire un baule | `E` | Onda d'urto / Rimarginare (talenti) | `R` / `T` |
| Analizza (Ren) | `Z` | Domare (Haruka) | `B` |
| Salvataggio rapido / carica | `F5` / `F9` | Impostazioni (volumi, accessibilità, testo grande) | `F10` |
| Tasti a scelta | `F4` | Suono sì / no, lingua | `F8`, `F2` |
| Chiudere un pannello, tornare alle partite | `Esc` | Imprese (schermata delle partite) | `A` |

La scritta sopra ciò che hai vicino dice che cosa farà `E`. Ogni azione può avere un tasto in più a tua scelta (`F4`, oppure il file `keys.json` accanto alle impostazioni).

**Android:** la metà sinistra dello schermo è una levetta che compare dove tocchi; un tocco a destra attacca; i pulsanti in basso a destra sono schivata, colpo potente e parata; in alto ci sono zaino, mappa, diario, lingua, suono, creazione e compagno; le opzioni di accessibilità sono in fondo al diario. Il tasto Indietro chiude un pannello o torna alle partite. Tutti i dettagli: [spec 16](docs/spec/16-input.md).

## Come è fatto il progetto

Due programmi **separati**, in due linguaggi, che devono comportarsi in modo **identico**:

| Client | Cartella | Tecnologia |
|---|---|---|
| Windows e Linux | [`desktop/`](desktop) | C++20, SDL3, rasterizzatore vettoriale scritto in casa ([ADR 0012](docs/adr/0012-in-house-software-rasterizer.md)) |
| Android 11+ | [`android/`](android) | Kotlin, libGDX, lo stesso rasterizzatore riscritto in Kotlin |

Quello che li tiene uguali:

1. **Le specifiche** in [`docs/spec/`](docs/spec/README.md): ogni regola di gioco è scritta lì prima del codice.
2. **Un'implementazione di riferimento in Python** in [`tools/reference/`](tools/reference), che esegue le stesse regole.
3. **I vettori di conformità** in [`tests/conformance/`](tests/conformance): ingressi e risultati attesi generati dal riferimento ed eseguiti dai test dei due client; se un client devia, la CI fallisce.
4. **I dati** in [`data/`](data): creature, oggetti, missioni, dialoghi, arte, suoni, mondo e testi sono JSON letti da entrambi i client. Nel codice non ci sono nomi, testi o numeri di bilanciamento.

La matematica di gioco è **solo intera** (percentuali e permille), la generazione del mondo è **deterministica** (interi e virgola fissa), la grafica è fatta di **ricette vettoriali** in JSON scritte da strumenti Python, e anche i suoni sono ricette sintetizzate. Le decisioni di architettura sono negli [ADR](docs/adr/README.md).

## Struttura delle cartelle

```text
AGENTS.md, CLAUDE.md  regole di lavoro per gli assistenti AI (e utili a chiunque modifichi il progetto)
docs/        documentazione (indice: docs/index.md)
  plan/        piano del progetto, roadmap e stato (italiano)
  spec/        regole normative per i due client (inglese)
  design/      stile grafico; catalogo, bilanciamento e traduzioni (generati)
  adr/         decisioni di architettura
  guides/      come aggiungere contenuti
  dev/         come preparare l'ambiente e compilare
schemas/     JSON Schema di ogni tipo di dato
data/base/   il pacchetto ufficiale: arte, suoni, creature, oggetti, missioni, dialoghi, mondo, testi (it, en)
tests/       vettori di conformità condivisi (generati: non si modificano a mano)
tools/       Python: validazione, riferimento delle regole, generatori, ship.py (guida: tools/README.md)
desktop/     client Windows e Linux (C++, CMake, vcpkg)
android/     client Android (Kotlin, Gradle): core (regole, JVM pura), game (libGDX), app (avvio)
```

## Per chi sviluppa

Serve Python 3.12 o più recente per dati e strumenti; per compilare i client servono CMake, Ninja e vcpkg (desktop) e JDK 17 con l'Android SDK (Android). La guida completa è [`docs/dev/setup.md`](docs/dev/setup.md).

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # su Linux: .venv/bin/pip
python tools/validate_data.py                         # dati, schemi, riferimenti, testi
python -m pytest -q tools/tests                       # riferimento, contenuti, documenti
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

Che cosa fa ogni script, quale si può rilanciare e che cosa lanciare dopo aver cambiato qualcosa: [`tools/README.md`](tools/README.md). Per aggiungere un oggetto, una creatura, una missione, una ricetta, un titolo, un luogo, una regione o una lingua c'è la [guida](docs/guides/add-content.md): quasi tutto è solo dati.

## Come si lavora qui (anche con un'AI)

Il progetto è sviluppato dal proprietario insieme a Claude, un assistente AI che scrive codice, dati e documenti. Le regole di lavoro sono in [`CLAUDE.md`](CLAUDE.md) (e [`AGENTS.md`](AGENTS.md) rimanda lì per gli altri assistenti); in breve:

- **Prima la specifica**, poi riferimento, vettori, desktop e Android nella stessa modifica.
- **Tutto è dato**: niente nomi, testi o numeri nel codice; ogni testo in italiano **e** inglese.
- **Generato è generato**: i vettori, il catalogo, i numeri dei README e molti dati escono da strumenti; si cambia la fonte e si rilancia lo strumento.
- **PR grandi**: a ogni richiesta Claude porta avanti molte voci della roadmap insieme e le spedisce in una PR sola con `tools/ship.py`, unita solo con la CI verde.
- Le decisioni di design sono delegate a Claude; pubblicazione e gestione del repository restano al proprietario, che prova ogni modifica in gioco.

## Documentazione

| Che cosa cerchi | Dove |
|---|---|
| Indice di tutta la documentazione | [`docs/index.md`](docs/index.md) |
| Il piano, la roadmap e lo stato delle milestone | [`docs/plan/`](docs/plan/README.md) (italiano) |
| Le regole di gioco, una per documento | [`docs/spec/`](docs/spec/README.md) |
| Tutti i contenuti in tabelle | [`docs/design/catalog.md`](docs/design/catalog.md) |
| Come aggiungere contenuti | [`docs/guides/add-content.md`](docs/guides/add-content.md) |
| Che cosa fa ogni script | [`tools/README.md`](tools/README.md) |
| Perché il progetto è fatto così | [`docs/adr/`](docs/adr/README.md) |
| Che cosa è cambiato | [`CHANGELOG.md`](CHANGELOG.md) |

## Che cosa manca

Le prossime cose, in ordine (dettagli nella [roadmap](docs/plan/06-roadmap-rischi-backlog.md#84-che-cosa-resta-da-fare-in-ordine)):

- **A breve:** ridurre la baseline di detekt; i viaggiatori che si vedono camminare; i paesani che vanno davvero alla festa vicina.
- **A medio termine:** carri che si vedono viaggiare; la modalità Dungeon di Gideon; prestazioni misurate su un telefono; un sintetizzatore migliore per musica e ambiente (solo se il proprietario lo vuole).
- **Verso la 1.0:** pacchetti firmati, documentazione per chi fa mod, altre lingue.
- **Decide il proprietario:** quando pubblicare la prima release (Alpha 0.1).

## Contribuire e licenza

Leggi [CONTRIBUTING.md](CONTRIBUTING.md), il [Codice di condotta](CODE_OF_CONDUCT.md), [GOVERNANCE.md](GOVERNANCE.md) e [SECURITY.md](SECURITY.md).

Codice: [GPL-3.0-or-later](LICENSE). Contenuti (dati, testi, arte, documenti di design): [CC BY-SA 4.0](LICENSE-CONTENT.md). Componenti di terzi: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
