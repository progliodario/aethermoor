# Aethermoor

> Titolo provvisorio. Action RPG isekai fantasy, top-down e in tempo reale, in grafica vettoriale. Gratuito e open source.
> English version: [README.en.md](README.en.md)

**Stato:** versione di prova giocabile (un protagonista, Ren). Su Windows, Linux e Android si esplora un mondo di 16384 x 16384 tile generato da un seme (otto regioni, giorno e notte, stagioni, meteo), con ~130 insediamenti, 35 siti a mano (sotterranei con boss, tane, nidi, avamposti con viandanti e storie), 60 creature, 110 oggetti, gilda con bacheca e commissioni, negozi, locande, Pietre della Soglia per viaggiare, diario, tre partite e italiano e inglese. Mancano ancora gli altri protagonisti con i loro doni, i compagni e la base. Il catalogo dei contenuti è in [`docs/design/catalog.md`](docs/design/catalog.md). Vedi la [roadmap](docs/plan/06-roadmap-rischi-backlog.md).

## Di che cosa si tratta

Otto o più anime vengono portate su Aethermoor, ognuna con un "dono" che spezza le regole. Scegli chi essere: cambiano il tono, le meccaniche e la storia. Il mondo è uno solo e i destini si incrociano.

- Open world top-down con città a mano e natura procedurale
- 8 o più protagonisti con trame e meccaniche proprie
- Gilda dei avventurieri con ranghi, status window, titoli e tag
- Compagni, legami, base da costruire, agricoltura, cucina, crafting
- Reincarnazione come progressione tra le vite
- Tutto è dato in JSON: moddabile
- Solo single player, nessuna rete, nessuna pubblicità

## Piattaforme

| Piattaforma | Codice | Tecnologia |
|---|---|---|
| Windows e Linux | [`desktop/`](desktop) | C++20, SDL3, ThorVG |
| Android 11+ | [`android/`](android) | Kotlin, libGDX |

Le due versioni sono implementazioni separate che leggono gli stessi dati in [`data/`](data) e seguono le stesse specifiche in [`docs/spec/`](docs/spec).

## Per iniziare (sviluppatori)

1. Leggi il [piano di progetto](docs/plan/README.md) e [`CLAUDE.md`](CLAUDE.md).
2. Prepara l'ambiente: [`docs/dev/setup.md`](docs/dev/setup.md).
3. Controlla i dati:

```bash
python -m venv .venv
.venv/Scripts/pip install -r tools/requirements.txt   # su Linux: .venv/bin/pip
python tools/validate_data.py
```

## Struttura

```text
docs/      piano, specifiche, design, guide
schemas/   JSON Schema dei dati
data/      contenuti del gioco (pack "base")
tests/     test di conformità condivisi
tools/     script Python (validazione, riferimento)
desktop/   client Windows e Linux
android/   client Android
```

## Contribuire

Leggi [CONTRIBUTING.md](CONTRIBUTING.md) e il [Codice di condotta](CODE_OF_CONDUCT.md).

## Licenza

Codice: [GPL-3.0](LICENSE). Contenuti (dati, testi, documenti di design): [CC BY-SA 4.0](LICENSE-CONTENT.md).
