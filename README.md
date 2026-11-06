# Aethermoor

> Titolo provvisorio. Action RPG isekai fantasy, top-down e in tempo reale, in grafica vettoriale. Gratuito e open source.
> English version: [README.en.md](README.en.md)

**Stato:** versione di prova giocabile (otto protagonisti: Ren, Sakura, Daichi, Haruka, Marco, Yuki, Lena e Gideon), provata a mano solo su Windows (Linux e Android sono compilati e testati dalla CI, Android non è mai stato eseguito su un dispositivo). Si esplora un mondo di 16384 x 16384 tile generato da un seme (otto regioni, giorno e notte, stagioni, meteo), con ~130 insediamenti, 35 siti a mano (sotterranei con boss, tane, nidi, avamposti con viandanti e storie), 60 creature, 135 oggetti, gilda con bacheca e commissioni, negozi, locande, Pietre della Soglia per viaggiare, diario, tre partite e italiano e inglese. Mancano ancora l'audio, i compagni, la base e i mestieri (raccolta, cucina, agricoltura). Il catalogo dei contenuti è in [`docs/design/catalog.md`](docs/design/catalog.md). Vedi la [roadmap](docs/plan/06-roadmap-rischi-backlog.md).

## Di che cosa si tratta

Otto o più anime vengono portate su Aethermoor, ognuna con un "dono" che spezza le regole. Scegli chi essere: cambiano il tono, le meccaniche e la storia. Il mondo è uno solo e i destini si incrociano.

- Open world top-down con città a mano e natura procedurale
- 8 o più protagonisti con trame e meccaniche proprie
- Gilda degli avventurieri con ranghi, status window, titoli e tag
- Compagni, legami, base da costruire, agricoltura, cucina, crafting
- Reincarnazione come progressione tra le vite
- Tutto è dato in JSON: moddabile
- Solo single player, nessuna rete, nessuna pubblicità

## Piattaforme

| Piattaforma | Codice | Tecnologia |
|---|---|---|
| Windows e Linux | [`desktop/`](desktop) | C++20, SDL3, rasterizzatore vettoriale interno ([ADR 0012](docs/adr/0012-in-house-software-rasterizer.md)) |
| Android 11+ | [`android/`](android) | Kotlin, libGDX, lo stesso rasterizzatore in Kotlin |

Le due versioni sono implementazioni separate che leggono gli stessi dati in [`data/`](data) e seguono le stesse specifiche in [`docs/spec/`](docs/spec).

## Provarlo

Ogni esecuzione della CI di GitHub carica la versione di prova per Windows e per Linux (artifact `aethermoor-windows-msvc` e `aethermoor-linux-gcc`, conservati 30 giorni): si scompatta, si avvia `aethermoor` tenendo la cartella `data` accanto e si legge [`desktop/PLAY.txt`](desktop/PLAY.txt), che elenca i comandi e che cosa provare. In breve: `WASD` per muoversi, `J` o `Spazio` per attaccare, `E` per parlare, `I` zaino, `Q` diario, `M` mappa, `Esc` per tornare all'elenco delle partite. La versione Android (APK di debug, artifact `aethermoor-debug-apk`) compila e supera i test in CI ma non è mai stata provata su un telefono. Non c'è ancora una release pubblica.

## Per iniziare (sviluppatori)

1. Leggi il [piano di progetto](docs/plan/README.md) e [`CLAUDE.md`](CLAUDE.md).
2. Prepara l'ambiente: [`docs/dev/setup.md`](docs/dev/setup.md).
3. Controlla i dati:

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # su Linux: .venv/bin/pip
python tools/validate_data.py
```

Gli strumenti di tutti i giorni (vettori di conformità, catalogo dei contenuti, rapporto di bilanciamento, `ship.py` che fa controlli, commit, PR e merge in un colpo) sono nella tabella di [`docs/dev/setup.md`](docs/dev/setup.md). Per aggiungere contenuti (un oggetto, una creatura, una missione, un luogo, una regione, una lingua) c'è la [guida](docs/guides/add-content.md).

## Struttura

```text
docs/      piano (it), specifiche (en), design e catalogo, guide, ADR, setup
schemas/   JSON Schema dei dati
data/      contenuti del gioco (pack "base": arte, creature, oggetti, missioni, dialoghi, mondo, testi it/en)
tests/     vettori di conformità condivisi dai due client (generati, non si modificano a mano)
tools/     script Python: validazione, riferimento delle regole, generatori, ship.py
desktop/   client Windows e Linux (C++)
android/   client Android (Kotlin)
```

## Contribuire

Leggi [CONTRIBUTING.md](CONTRIBUTING.md) e il [Codice di condotta](CODE_OF_CONDUCT.md).

## Licenza

Codice: [GPL-3.0](LICENSE). Contenuti (dati, testi, documenti di design): [CC BY-SA 4.0](LICENSE-CONTENT.md).
