# Stile grafico

Regole per tutta l'arte del gioco (ricette vettoriali in `data/base/art/`, formato in [spec 13](../spec/13-vector-art.md)). Servono a tenere insieme l'aspetto di cose scritte in momenti diversi. Lo stile è **realistico e dipinto**: terreni con la materia vera (fili d'erba, ghiaia, sassi, increspature), oggetti, persone e creature con luce morbida, volume e grana, senza contorni da fumetto. La scelta è spiegata nell'[ADR 0015](../adr/0015-realistic-painted-art.md), che prende il posto dell'aspetto da anime dell'[ADR 0013](../adr/0013-painted-anime-art.md) tenendone ricette, rasterizzatore e strumenti.

![Un pezzo di mondo con l'arte del gioco](img/scene.png)

## Principi

- **Luce da in alto a sinistra, morbida.** Ogni forma ha la sua tinta, un'ombra **sfumata** sul lato lontano dalla luce e una luce sul lato vicino. L'ombra è un viola freddo **moltiplicato** sui colori (`blend: multiply`), così ogni tavolozza conserva la sua tinta; la luce è un bianco caldo **aggiunto** dentro la sagoma (`blend: add` con `clip`). Niente ombre nette da cel shading e niente nero semitrasparente sopra il colore: ingrigisce.
- **Niente contorni da fumetto.** Una sagoma si legge dalla sua luce e dalla sua ombra; resta al più un filo appena visibile nel suo colore. I terreni non hanno contorno.
- **La materia, non la tinta.** Legno, corteccia, pietra, stoffa, capelli, pelliccia, foglie, sabbia e acqua hanno la loro grana: il **rumore** di `artkit.py` (`noise()`), **allungato** per fibre, fili, ciocche e increspature (`scale_y`) e **a creste** per crepe, venature, solchi e la rete di luce sul fondo dell'acqua (`ridged`).
- **Ombra di contatto.** Tutto ciò che sta sul terreno ha ai piedi un'ombra sfumata (`Recipe.shadow()`); ogni sasso, ciuffo, foglia o fiore dei terreni ha la sua, moltiplicata.
- **Luci che splendono.** Fuochi, lampade, rune e occhi che brillano hanno un alone (`Recipe.glow()`: un'ellisse sfumata con `blend: add`).
- **Colori naturali:** terreni poco saturi con chiazze di sole e d'ombra; oggetti e personaggi un po' più vivi ma non accesi; luce calda sui punti importanti. Le creature di una stessa famiglia condividono il corpo e cambiano la tavolozza e il tratto che le distingue.

## La rifinitura

`artkit.finish()` è applicata a ogni oggetto, persona e creatura quando la ricetta viene scritta (`Recipe.finish`, con le regolazioni di ogni generatore: `FINISH` in `art_props.py`, `part()` in `art_chars.py`, `new()` in `art_creatures.py`). Senza ridisegnare nulla:

- il contorno di una forma piena diventa un filo tenue (`outline`: quanto resta della sua opacità);
- ogni ombra e ogni luce nette diventano sfumate (`soften`);
- i colori perdono una parte della saturazione (`desat`); le tavolozze delle creature, lette dai loro file, non sono toccate;
- una luce morbida da in alto a sinistra e la sua ombra danno volume a tutto il disegno (`form`), la luce del cielo cade sui bordi alti (`sky`);
- una grana fine copre il disegno (`grain`).

Sopra la rifinitura ogni generatore aggiunge la materia di ciò che disegna: foglie, lacune scure e luce per le chiome e corteccia a solchi per i tronchi (`crown()` e `trunk()` in `art_props.py`), ciocche e riflessi per i capelli e trama per le stoffe (`textures()` in `art_chars.py`), pelliccia per le bestie e graffi e ruggine per le armature (`matter()` in `art_creatures.py`).

## Misure

- 32 unità d'arte = 1 tile; il desktop disegna un tile a 80 pixel (scala 2,5) e Android a 64 (scala 2), per la densità dello schermo.
- **Terreni: tasselli grandi.** Un terreno naturale è una ricetta di 128 x 128 unità che copre 4 x 4 tile (spec 13, "Macro tiles"), così il dipinto non si ripete a ogni tile. La base è un rumore che si ripete ogni 128 unità ed è **la stessa per tutte le varianti di un terreno** (da `grass_a` a `grass_f`), così ogni variante si unisce a ogni altra; le cose piccole (ciuffi, fiori, sassi) stanno dentro il proprio tile, lontano dai bordi (`cells()` in `art_tiles.py`). Muri, pavimenti e ponte sono tasselli semplici di 32 x 32.
- **Bordi sfumati.** Nel tileset ogni terreno naturale ha un rango `blend`: il terreno di rango più alto sfuma sul bordo del vicino (l'erba sul sentiero, la sabbia sull'acqua). Lo fanno i client (spec 13, "Ground blending"): nelle ricette non serve nulla.
- **Oggetti:** l'origine è ai piedi (ordine di disegno e collisione). Alberi: 96 x 128, origine (48, 120).
- **Persone:** alte circa 56 unità (1,75 tile) con le **proporzioni di un corpo vero**, un po' basse, con la testa generosa e il collo corto perché restino gradevoli: cinque teste e mezza, un collo corto, le spalle che scendono dal collo, la vita, le braccia che arrivano a metà coscia, le gambe lunghe metà dell'altezza. Ogni parte è disegnata nelle sue unità e poi **deformata** a quelle proporzioni da `PROPORTIONS` in `art_chars.py` (con tutti i look); le giunture del rig seguono (`RIG`, `SIDE_OFFSET`). Le parti del rig `humanoid` sono ombra, gambe, braccia, busto, testa e `cape` (mantelli e capelli lunghi dietro il corpo); busto, testa e mantello hanno una seconda ricetta per la **vista di spalle** (`art_back`), usata quando il giocatore cammina verso l'alto.
- **Tre viste.** La persona è disegnata di fronte, di spalle (`art_back`) e **di lato** (`art_side`, guarda a destra e viene specchiata): di lato hanno un disegno proprio testa, busto e mantello, mentre braccia e gambe sono quelle di fronte, appese quasi allo stesso punto (`offset_side`). I look di lato sono in `tools/art_looks_side.py` (`@side("nome", "parte")`): un personaggio nuovo ha bisogno anche di quelli.
- **Bestie:** lupi, selvaggina e alfa sono visti di lato e guardano a sinistra (`"faces": "left"`): i client li specchiano perché guardino il giocatore.

## Come si fa

Tutta l'arte è scritta da codice Python e salvata come JSON, che resta il formato che il gioco legge. Si cambia il codice e si rigenera:

| Cosa | Strumento | File |
|---|---|---|
| terreni | `python tools/make_art.py tiles` | `tools/art_tiles.py` |
| oggetti | `python tools/make_art.py props` | `tools/art_props.py` |
| persone, rig e animazioni | `python tools/art_chars.py` | `tools/art_chars.py` (corpo, tavolozze), `tools/art_looks.py` (abiti e acconciature) |
| creature | `python tools/art_creatures.py`, poi `python tools/make_echoes.py` | `tools/art_creatures.py` |

`tools/artkit.py` ha i pezzi comuni: colori, strati con `blur`, `clip` e `blend`, gradienti, rumore, ombre e luci.

Per guardare il risultato senza il gioco: `python tools/art_preview.py <schema>` disegna le ricette in PNG con il rasterizzatore di riferimento (lo stesso algoritmo dei client) e le raccoglie in una pagina e in un'immagine sola; `--figures` disegna ogni persona di fronte, in cammino e di spalle; `--scene` un pezzo di mondo. Nel gioco: `aethermoor --smoke-test --screenshot-dir=...`.

## Terreni

Un terreno naturale è fatto di **cinque strati di rumore**, uguali per tutte le varianti di un terreno (`ground()` in `art_tiles.py`): la luce e l'ombra larghe della terra, le sue chiazze, la sua materia moltiplicata (allungata lungo y per l'erba), le punte illuminate di quella materia, e una grana più fine di un pixel. Sopra vanno centinaia di cose piccole per tile (un centinaio di fili d'erba e un tappeto di fili corti, decine di granelli di ghiaia, aghi e foglie), disegnate **a gruppi**: uno strato tiene tutti i fili d'erba di un tono di un tile (`clumps()`, `field_blades()`), così come la ghiaia (`gravel()`), i sassi (`stones()`), le foglie (`leaves()`) e i fiori (`flowers()`). Le figure dentro uno stesso strato girano tutte nello stesso verso, perché la regola del riempimento (nonzero) non apra buchi dove si sovrappongono.

## Persone

- La figura di base è Ren. Ogni protagonista e ogni gente è una **variante**: una tavolozza (`VARIANTS` in `art_chars.py`: pelle, capelli, occhi, abiti) e i suoi strati (`art_looks.py`, con `only`; quelli di Ren con `except`). Un look è una funzione `@look("nome", "parte")` che disegna nelle unità della parte, attorno al suo giunto, e riceve `back` per la vista di spalle; `behind=True` lo mette dietro la parte (una coda, un mantello).
- Il viso ha le proporzioni di un viso vero: occhi a mandorla con l'iride del colore `eye` della variante mezza coperta dalla palpebra, una luce sola, ciglia sottili e la piega della palpebra; un'ombra sul lato del naso, le narici, due labbra.
- Un abito lungo (camice, grembiule, tunica) è un look del busto che scende sopra le gambe: il busto si disegna dopo le gambe.

## Creature

- Ogni creatura tiene la tavolozza del suo file; `art_creatures.py` le dà il corpo della famiglia e il suo tratto: gli slime (`FEATURES`, `ROYAL` con corona e collana, `GIANT`), le bestie (`BEASTS`, `ALPHAS`), i guardiani in armatura (`KNIGHTS`) e le creature disegnate una per una.
- Una creatura nuova: copiare un file della stessa famiglia, cambiarne la tavolozza, aggiungere una riga alla tabella della famiglia con un tratto che la distingua dalle sorelle (non solo un colore), rieseguire lo strumento.
- Gli Echi sono un guardiano ricolorato: li scrive `make_echoes.py`, da rieseguire dopo `art_creatures.py`.

## Luce, vento, aria

Non sono nelle ricette ma nei client, uguali su desktop e Android (spec 08, "The colour of the hour"; spec 13, "Sway"):

- **La luce dell'ora.** Di notte il mondo è moltiplicato per un blu, all'alba e al tramonto per una luce calda; lampioni, falò e Pietre della Soglia **si sommano** a ciò che la notte ha scurito. I colori sono in `grading` di `data/base/lights.json`: si cambiano lì, non nel codice.
- **Il vento.** Una ricetta con `sway` (unità d'arte) si piega con il vento: la base resta ferma, la cima si sposta. Alberi 1-2, cespugli e stendardi meno di 1. `art_props.py` ha la tabella.
- **L'acqua.** Un terreno con `surface: water` si muove: i client ridisegnano lo stesso dipinto spostato di tile interi, con un'opacità che va e viene (spec 13, "Water"). Nella ricetta dell'acqua servono quindi riflessi e chiazze, non onde disegnate in un punto solo.
- **Il colpo.** `humanoid_attack` è l'animazione dell'attacco (in `art_chars.py`, con quelle di attesa e cammino).
- **L'aria.** Pulviscolo nel sole di giorno, lucciole di notte (`motes`), e i bordi dello schermo un po' più scuri (`vignette_pm`).

## Interfaccia

Il testo del desktop è scritto con il font del pack (`data/base/fonts/aether.json`, spec 13 "Font"): ogni lettera è fatta di tratti, disegnati con una penna tonda dal rasterizzatore dell'arte alla misura che serve. Le lettere sono disegnate in `tools/make_font.py` (una riga per lettera: larghezza e tratti, in una cella di 8 x 11 con le maiuscole da 1 a 7 e le minuscole alte 4); `python tools/make_font.py --show prova.png "testo"` mostra una frase. Android usa lo stesso font, cotto una volta in una texture alla misura dello schermo (`PackFont.kt`).

`draw_panel` e `draw_bar` in `desktop/src/app/main.cpp` e `drawPanel` e `drawBar` in `AethermoorGame.kt` disegnano pannelli e barre con lo stesso aspetto; ogni pannello nuovo usa questi.

## Strutture

- Le case degli insediamenti (stamp `hamlet*`, `village*`, `town*`, `outpost*`) sono a graticcio: `wall_timber`, `wall_window` (ogni due tile sul lato alto, e uno sul fianco) e `door` con soglia di pietra. Fortezze, tombe e rovine restano di pietra (`wall_stone`): `make_stamps.py` converte da solo i caratteri `:` `'` `;` in `#` e `_` fuori dagli insediamenti.
- Un edificio nuovo si disegna con `Canvas.house()`: porta e finestre arrivano da sole.

## Costo

Le ricette sono cotte in texture al primo uso. Una ricetta ricca ha qualche centinaio di strati: i rasterizzatori lavorano solo sul riquadro di ogni strato, ma sfumature (`blur`) grandi e rumori a tutta tela costano. Regole pratiche: `blur` sotto le 3 unità salvo gli aloni, al massimo quattro ottave di rumore, niente strati a tutta tela oltre la base.
