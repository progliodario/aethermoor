# 04. Grafica, audio, UI e input

> **Stato (novembre 2026).** Fatto: la pipeline a ricette (JSON, palette e varianti), il rasterizzatore proprio uguale nei due client al posto di ThorVG / `android.graphics` (ADR 0012, `docs/spec/13-vector-art.md`), rig e clip, gli atlanti per scala, il giorno e la notte con tinta stagionale, e l'input da tastiera, mouse, gamepad (desktop) e touch con stick fluttuante (`docs/spec/16-input.md`). **Non ancora:** luci puntiformi e ombre morbide, audio (nessun suono), UI dichiarativa (le schermate sono scritte nel codice dei due client, ADR 0008), gli override con SVG/PNG, input adattivo in base all'ultimo dispositivo, il controller su Android.

## 1. Pipeline dell'arte vettoriale (D1-D4)

### Idea

Nessuna immagine nel repo. L'arte è **descritta** in JSON (forme, gradienti, contorni, parti animabili). All'avvio ogni client la **rasterizza** in atlanti di texture alla scala giusta per lo schermo, poi la disegna come sprite normali. Così la grafica è nitida a qualsiasi densità di pixel, costa poco a runtime e si può sostituire con SVG/PNG.

```text
data/art/*.json (ricette, rig, clip, palette)
        │ parse
        ▼
  Ricetta in memoria ──► Rasterizzatore (proprio, ADR 0012; il piano diceva ThorVG | android.graphics)
        │                         │
        │ bake per scala          ▼
        ▼                   Bitmap/Surface
  Cache atlanti (LRU) ──► Texture GPU ──► Sprite/Rig a runtime
        ▲
  overrides/*.svg|png (se presenti, hanno la precedenza)
```

### Specifica delle ricette (spec 13)

- Canvas con origine/pivot, strati ordinati, forme: `rect`, `rrect`, `ellipse`, `polygon`, `path` (SVG), `line`.
- Riempimenti: tinta unita, `linear` e `radial` con stop; contorni con `width`, `cap`, `join`, `dash`; opacità; trasformazioni per strato; maschere (clip) semplici; `blur_baked` (solo in fase di bake).
- **Palette parametriche:** `$p.nome` per avere molte varianti di una stessa ricetta (colori della pelle, dei capelli, dei vestiti, delle creature).
- **Generatori:** ricette con elementi ripetuti e disturbo seeded (foglie, rocce, erba) per varietà senza ripetizioni. Il seed è l'ID della ricetta + indice di variante, quindi coincide nei due client.
- **Stili:** *outline* spesso e uniforme, ombre morbide integrate, highlight a gradiente; tutto da un unico `style.json` con 12-16 colori base per bioma (coerenza visiva).

### Scala e atlanti

- **Densità di bake:** `px_per_unit = round(dpi_scale × zoom_bucket × 32)` con bucket 1×, 1,5×, 2×, 3×. Cambio di zoom o schermo = ribake dei soli asset in uso, in background.
- **Atlanti:** texture massime 2048² (mobile) / 4096² (desktop), packing MaxRects; separati per `terrain`, `characters`, `props`, `fx`, `ui`.
- **Cache:** LRU con tetto di memoria (desktop 256 MB, Android 128 MB di texture). Rebake automatico se la texture è persa (su Android: **perdita del contesto GL** al ritorno dall'app; gli atlanti si ricostruiscono dalla cache CPU, non dalla rete).

### Rasterizzatori

| | Desktop | Android |
|---|---|---|
| Libreria | ~~ThorVG~~ il rasterizzatore proprio di `desktop/src/vector` | ~~`android.graphics`~~ il rasterizzatore proprio di `core/vector` |
| Output | `SDL_Surface` ARGB8888 | `Bitmap` ARGB_8888 |
| Parsing path | parser proprio (comandi assoluti `M L H V C Q Z`) | lo stesso, in Kotlin |
| Thread | Worker pool | Worker (HandlerThread) |
| Upload GPU | `SDL_CreateTextureFromSurface` | `Texture(Pixmap)` / GL sul thread GL |

Le differenze minime di antialiasing sono accettate; i test golden usano tolleranza.

### Animazione a rig (D3)

- Ogni personaggio = **parti** (torso, testa, braccia, gambe, arma, capelli, accessori) rasterizzate separatamente + **rig** gerarchico con pivot.
- **Clip** con tracce `pos`, `rot`, `scale`, `alpha` a keyframe in tick e easing; eventi (passi, impatti, spawn hitbox).
- Direzioni: **4** (su/giù/sinistra/destra) con ribaltamento orizzontale; giù/su hanno parti dedicate quando serve.
- Stati: `idle`, `walk`, `run`, `attack_*`, `cast`, `dodge`, `hurt`, `death`, `interact`, `emote_*`.
- **Costo:** nessuna ri-rasterizzazione per frame: solo trasformazioni di quad. Costo di rendering per personaggio ≈ 8-14 quad.
- **Mix e layering:** clip sovrapposti per parti (gambe camminano, braccia attaccano).
- **Creature procedurali:** slime = deformazione morbida con scala `squash/stretch`; altre con rig a 3-6 parti.

### Luci e atmosfera (D4)

- **Illuminazione 2D:** buffer luminoso a bassa risoluzione (¼ dello schermo) moltiplicato sulla scena. Luce ambiente da orario e meteo (`ambient_color` da una curva), luci puntiformi (torce, magie, finestre), luci dinamiche delle skill.
- **Ombre:** ombra "blob" morbida sotto ogni entità; alberi e strutture con ombra proiettata a ellisse ruotata dall'ora del giorno.
- **Profili di qualità** (impostazioni): *Bassa* (niente luci dinamiche, particelle ridotte), *Media*, *Alta* (bloom leggero, ombre estese). L'impatto è visivo; il gioco è identico.
- **Meteo:** pioggia, neve, nebbia, vento, tempesta come particelle e overlay.
- **Particelle:** emettitori JSON (forma, velocità, durata, colore su curva, gravità), pool fisso di 2.000 particelle desktop / 800 Android.
- **Post-effetti** (opzionali): vignetta, correzione colore per momento della giornata, flash/trasizioni; per desktop con SDL_GPU/shader solo in una fase successiva; baseline = sprite + moltiplicazione luci.

### Mondo e rendering a strati

Ordine: terreno → decorazioni a terra → ombre → entità e oggetti (ordinati per `y`) → effetti → chioma alberi/tetti (sopra) → luci → particelle → UI.
Camera top-down con leggera prospettiva 3/4 (le immagini sono disegnate con altezza), zoom da 0,75× a 2× (zoom iniziale per orientamento: orizzontale 1×, verticale 1,15×). Culling per chunk e per entità; **batching** per atlante.

### Riferimenti di stile

Colori saturi ma morbidi, forme arrotondate, contorni scuri colorati (non neri), palette per regione, 3 livelli di dettaglio (terreno semplice, prop medio, personaggi ricchi). Un `style-guide.md` con esempi accompagna le ricette.

### Sostituzione dell'arte

`overrides/<id>.svg|png` sostituisce la ricetta con lo stesso ID. SVG: stesso rasterizzatore; PNG: usato com'è (con metadati `scale` e `pivot` in un sidecar JSON). Utile per modder o per artisti.

## 2. Audio sintetizzato (spec 14)

### Motore

| Blocco | Funzione |
|---|---|
| Oscillatori | sinusoide, quadra con PWM, dente di sega, triangolo, rumore bianco/rosa |
| Inviluppi | ADSR (attacco, decadimento, sostegno, rilascio) per ampiezza e filtro |
| Filtri | passa-basso/passa-alto/risonante (biquad) |
| Modulazione | LFO su intonazione, ampiezza, filtro |
| Effetti | delay, riverbero (Schroeder), distorsione leggera, compressore semplice |
| Voci | polifonia fino a 16 (desktop) / 10 (Android) |
| Sequencer | pattern a step (16 step/battuta), tempo, trasposizione, accordi |
| Mixer | bus: musica, SFX, ambiente, UI; volumi in impostazioni |

### Dati

```json
{
  "id": "base:audio/patch/soft_pad",
  "osc": [ { "wave": "saw", "detune_cents": -6 }, { "wave": "saw", "detune_cents": 6 } ],
  "amp_env": { "a": 0.4, "d": 0.5, "s": 0.7, "r": 1.2 },
  "filter": { "type": "lowpass", "cutoff": 1800, "q": 0.7, "env_amount": 800 }
}
```

```json
{
  "id": "base:audio/music/verdalis_day",
  "tempo": 92,
  "key": "D",
  "scale": "major",
  "tracks": [
    { "patch": "base:audio/patch/soft_pad",
      "pattern": [ "D2 -- -- -- A2 -- -- --", "G2 -- -- -- D2 -- -- --" ], "bars": 8 },
    { "patch": "base:audio/patch/pluck",
      "pattern": [ "F#4 -- A4 -- D5 -- A4 --" ], "bars": 8 }
  ],
  "layers": { "combat": [ { "patch": "base:audio/patch/drum_soft", "pattern": [ "K -- S -- K K S --" ] } ] }
}
```

- **SFX parametrici** (stile "sfxr"): forme d'onda + inviluppo di frequenza/ampiezza + rumore; ricette per colpi, magie, passi (variano per superficie), UI, ambienti.
- **Musica adattiva:** strati (esplorazione, tensione, combattimento, boss); transizioni su battuta con crossfade di 1 s; musica per regione, orario e meteo.
- **Ambiente:** vento, pioggia, fuoco, folla, insetti notturni, generati da rumore filtrato.

### Implementazione

- **Desktop:** SDL3 `SDL_AudioStream` con callback; sintesi su thread audio, comandi dal thread principale tramite coda senza lock.
- **Android:** `AudioTrack` in modalità streaming (float PCM, buffer 2-4 volte il minimo) su thread a priorità audio; libGDX non è usato per la sintesi.
- **Bake:** SFX pre-renderizzati in PCM al caricamento (cache), la musica si sintetizza in tempo reale ma ha una modalità "pre-render" per dispositivi deboli.
- **Sostituzione:** `overrides/<id>.ogg|wav`.
- **Test:** campioni di riferimento generati da Python per le forme d'onda base; confronto con tolleranza (RMS) e controlli di silenzio/clipping.

## 3. UI dichiarativa (D5, spec 15)

### Tema "Finestra di sistema"

- Pannelli blu profondi semitrasparenti (`#0B1F3A` a 80%), bordo ciano chiaro (`#6FE3FF`), angoli tagliati, griglia sottile, testo bianco-azzurro, accenti oro per titoli e raro, rosso per PV, azzurro per PM, verde per XP.
- Animazioni: comparsa con "scan line", conteggi che scorrono, bagliore leggero sulle voci attive.
- Temi aggiuntivi per protagonista (opzionali): *Dono* modifica colore e decorazioni (Lena: grigio freddo, Gideon: viola e rosso, Haruka: verde e legno).

### Schermate e layout

- Ogni schermata è un JSON con albero di widget: `panel`, `row`, `column`, `grid`, `stack`, `scroll`, `label`, `rich_text`, `icon`, `image`, `button`, `toggle`, `slider`, `progress`, `tabs`, `list`, `tooltip`, `modal`, `toast`, `spacer`.
- **Layout flex:** peso, min/max, allineamento, margini; **unità UI** (indipendenti dai pixel, 1 ui = 1/160 pollice).
- **Breakpoint:** `compact` (< 600 ui di larghezza), `regular` (600-1000), `expanded` (> 1000), e orientamento `portrait`/`landscape`. Una schermata può definire `variants` per breakpoint.
- **Binding:** valori da stato di gioco con un piccolo linguaggio di espressione (`{{player.hp}} / {{player.max_hp}}`, `{{item.name}}`), senza cicli o chiamate. Azioni dei pulsanti = comandi nominati (`open_screen`, `equip`, `use_item`, …) definiti nel motore.
- **Focus/navigazione:** ogni widget interattivo è raggiungibile con frecce, controller e touch; ordine di focus esplicito; scorciatoie.
- **Accessibilità:** contrasto ≥ 4,5:1, dimensioni minime di tocco **48 dp**, ridimensionamento testo 80-150%, supporto a lettori di schermo non nell'1.0 (post).

### Schermate principali

Titolo, selezione protagonista, selezione slot, HUD (PV/PM, XP, skill, minimappa, bussola, quest tracciata, effetti, orario/meteo), status window, inventario, equipaggiamento, skill tree, diario quest, mappa del mondo, bestiario, titoli e tag, party, base/costruzione, negozio, crafting, dialogo, ricettario, impostazioni (video, audio, controlli, accessibilità, lingua, salvataggi), pausa, game over/respawn, reincarnazione e albero dell'eredità, crediti.

### Font

- **Nome/UI:** font umanista leggibile (OFL), **Titoli:** font con carattere fantasy ma pulito (OFL). Set Latin esteso.
- Rendering: SDL3_ttf (desktop), gdx-freetype (Android) con atlante dinamico di glifi e SDF opzionale per scalare senza ribake.
- Testo ricco: grassetto, colore, icone inline (`:hp:`), ritmo di apparizione nei dialoghi (macchina da scrivere, velocità in impostazioni).

## 4. Input adattivo (spec 16)

### Azioni astratte

`move`, `aim`, `attack`, `skill_1..4`, `ultimate`, `dodge`, `guard`, `interact`, `menu`, `map`, `inventory`, `quick_item_1..3`, `target_lock`, `cycle_target`, `party_command`, `confirm`, `cancel`, `tab_prev`, `tab_next`.

### Dispositivi

| Dispositivo | Schema |
|---|---|
| Tastiera/mouse | WASD/frecce, mouse = mira e attacco, Q/E/R/F = skill, Spazio = schivata, Shift = guardia, E = interazione, Tab = menu, M = mappa |
| Gamepad | Stick sinistro movimento, destro mira, RT attacco, X/Y/B/A skill, LB guardia, RB schivata, D-pad oggetti rapidi, Start menu. SDL3 Gamepad API (desktop); Android: eventi controller di libGDX |
| Touch | Stick virtuale **flottante** a sinistra, pulsanti azione a destra, trascinamento sulla scena per mirare, doppio tocco per interagire, tocco prolungato per descrizioni; **vibrazione** su eventi chiave (configurabile) |

- **Rimappatura** completa per tastiera e gamepad, salvata in `settings.json`.
- **Layout touch modificabile:** posizione e dimensione dei pulsanti con editor in-game; preset *Destrimano*, *Mancino*, *Una mano*.
- **Rilevamento automatico** dell'ultimo dispositivo usato per mostrare i suggerimenti corretti (icone tastiera, gamepad, touch).
- **Dead zone, sensibilità, auto-mira** regolabili.

### Orientamento (Android)

- **Orizzontale:** HUD agli angoli, stick a sinistra, pulsanti a destra.
- **Verticale:** HUD in alto e in basso (zona pollice), minimappa ridotta, azioni su due righe, camera con zoom adattato; alcune schermate (inventario, diario) usano il layout `compact` con tab in fondo.
- Rotazione a caldo senza perdita di stato (gli stati vivono nel modello, non nella `Activity`).
- Gestione di **notch**, barre di sistema e gesti di sistema (area di sicurezza), immersive mode, pausa automatica in background e salvataggio automatico alla pausa.

## 5. Prestazioni e budget

| Voce | Obiettivo |
|---|---|
| FPS | 60 stabili su PC recenti e telefoni di fascia media (classe Snapdragon 7); opzione 30 FPS per il risparmio energetico |
| Tempo frame | ≤ 16,6 ms: update ≤ 4 ms, render ≤ 8 ms, margine 4 ms |
| Memoria Android | ≤ 600 MB totali, ≤ 128 MB di texture |
| Entità attive | ≤ 500 (nemici in aggro ≤ 40) |
| Chunk | generazione + bake ≤ 2 ms per chunk sul thread principale, il resto sui worker |
| Avvio a freddo | ≤ 6 s su mobile, ≤ 3 s su PC |
| Dimensioni | APK ≤ 120 MB, build desktop ≤ 200 MB (nessun file di grafica pesante) |
| Batteria | Opzioni di qualità, FPS cap, riduzione particelle e luci |

Strumenti: contatori in un overlay di debug (FPS, tempi per fase, memoria, entità, chunk), Tracy su desktop, Perfetto/Android Profiler su Android, benchmark scriptati in `tests/scenarios/perf_*.json`.
