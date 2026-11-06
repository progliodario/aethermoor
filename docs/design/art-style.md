# Stile grafico

Regole per tutta l'arte del gioco (ricette vettoriali in `data/base/art/`, formato in [spec 13](../spec/13-vector-art.md)). Servono a tenere insieme l'aspetto di cose scritte in momenti diversi.

## Principi

- **Luce da in alto a sinistra.** Ogni forma ha tre toni: ombra (in basso a destra), base e luce (in alto a sinistra), di solito con un gradiente lineare o radiale. Un piccolo riflesso bianco (alpha 0,4-0,8) sulle superfici lucide.
- **Contorno scuro sugli oggetti, nessuno sui terreni.** Gli oggetti (alberi, casse, creature, personaggi) hanno un contorno di 1,2-1,5 unità in un colore scuro del loro stesso colore (non nero puro: `#1E1B28` per i personaggi, il verde più scuro per le foglie). I tasselli del terreno non hanno contorno, così si uniscono senza cuciture.
- **Ombra a terra.** Tutto ciò che sta sul terreno ha un'ellisse d'ombra (nero, alpha 0,25-0,3, con un secondo cerchio più piccolo e più scuro) ai piedi: `Recipe.shadow()`.
- **Dettaglio piccolo e sparso.** Un tassello non è mai di un solo colore: ha chiazze morbide di toni vicini (alpha 0,12-0,14), pochi ciuffi, sassolini, fiori o venature. I dettagli stanno lontano dai bordi, il numero è basso (il terreno copre lo schermo: troppo dettaglio fa rumore).
- **Colori:** terreni desaturati e leggermente scuri, oggetti e personaggi più saturi, luce calda sui punti importanti (fuochi, lampade, rune). Le creature di una stessa famiglia condividono la forma e cambiano la tavolozza (e le cose che le distinguono: corona, corna, cristalli).

## Misure

- 32 unità d'arte = 1 tile; il gioco disegna un tile a 48 pixel (scala 1,5) e più su schermi ad alta densità.
- I tasselli sono 32 x 32 con origine (0, 0). Gli oggetti hanno l'origine ai piedi (per l'ordine di disegno e la collisione) e la stessa area di prima, così i raggi di collisione dei dati del mondo restano giusti.
- Alberi: 64 x 96, origine (32, 88). Personaggi: parti del rig `humanoid` (testa, busto, braccio, gamba, ombra).

## Come si fa

Le ricette dei terreni e degli oggetti sono scritte con `python tools/make_art.py` (`tools/artkit.py` ha i pezzi: colori, ellissi, ciuffi, sassolini, gradienti; `tools/art_props.py` ha gli oggetti): si cambia il codice e si rigenerano i JSON, che restano il formato che il gioco legge. `python tools/art_preview.py <schema>` disegna una pagina HTML con le ricette (`tiles`, `props`, `creatures`...), e `aethermoor --smoke-test --screenshot-dir=...` mostra come stanno nel gioco.

## Persone, creature e interfaccia

- `tools/art_chars.py` riscrive le quattro parti del rig umanoide (testa, busto, braccio, gamba) tenendo canvas, palette e varianti; le ombre sono nero o bianco con alpha, così funzionano con ogni palette.
- `tools/art_creatures.py` aggiunge strati di dettaglio sopra le ricette delle creature (non le riscrive): si esegue una volta sola per ricetta, riconosce le originali dal numero di strati. Per cambiare una creatura già rifinita, si modifica il file a mano o si rigenera dal git.
- Interfaccia: `draw_panel` e `draw_bar` in `desktop/src/app/main.cpp` e `drawPanel` e `drawBar` in `AethermoorGame.kt` disegnano pannelli e barre con lo stesso aspetto; ogni pannello nuovo usa questi.

## Differenze tra le varianti

- Una variante non cambia solo i colori: con `only` e `except` (spec 13) uno strato appartiene a certe varianti. Ren è la figura di base (occhiali e cravatta con `except`), ogni altro protagonista e ogni gente ha i propri strati davanti o dietro le parti del rig (`tools/art_looks.py`). Le parti hanno un canvas più grande per lasciare spazio a corna, cappelli e mantelli.
- Ogni creatura ha un tratto suo (`tools/art_creature_looks.py`): quando si aggiunge una creatura nuova serve un tratto che la distingua dalle sorelle della famiglia, non solo una palette.
- `python tools/art_preview.py --figures` disegna ogni persona intera; `python tools/art_preview.py creatures/slime` le creature.

## Strutture

- Le case degli insediamenti (stamp `hamlet*`, `village*`, `town*`, `outpost*`) sono a graticcio: `wall_timber`, `wall_window` (ogni due tile sul lato alto, e uno sul fianco) e `door` con soglia di pietra. Fortezze, tombe e rovine restano di pietra (`wall_stone`): `make_stamps.py` converte da solo i caratteri `:` `'` `;` in `#` e `_` fuori dagli insediamenti.
- Un edificio nuovo si disegna con `Canvas.house()`: porta e finestre arrivano da sole.
