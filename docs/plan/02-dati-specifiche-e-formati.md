# 02. Dati, specifiche numeriche e formati

> Questo documento è il nucleo di `docs/spec/`. I numeri sono **valori iniziali di bilanciamento**: stanno in `data/base/tables/` e si possono cambiare senza toccare il codice.

## 1. Pack, ID e manifest

### ID

`namespace:categoria/nome`, minuscolo, `[a-z0-9_]` più `/`. Esempi: `base:enemy/slime_green`, `base:skill/ren/analyze`, `mymod:item/fancy_hat`.
Un ID è stabile per sempre: i salvataggi li usano. Rinominare = migrazione.

### Manifest (`data/base/pack.json`)

```json
{
  "$schema": "../../schemas/pack.schema.json",
  "id": "base",
  "name": "$i18n:pack.base.name",
  "version": "0.1.0",
  "data_format_version": 1,
  "authors": ["Aethermoor contributors"],
  "license": "CC-BY-SA-4.0",
  "depends": [],
  "requires_features": ["vector_art_v1", "dialogue_v1", "quest_v1"],
  "load_order": 0,
  "languages": ["it", "en"]
}
```

I pack si caricano in ordine di dipendenza e `load_order`. Un file con lo stesso ID di uno precedente lo **sostituisce** solo se dichiara `"override": true`; altrimenti è un errore segnalato.

## 2. Catalogo dei tipi di dato

| Cartella | Schema | Contenuto |
|---|---|---|
| `protagonists/` | `protagonist` | Statistiche base, crescita, cheat, albero, regione di partenza, prologo, tono |
| `companions/`, `npcs/` | `companion`, `npc` | Ruolo, IA, routine, dialoghi, legami |
| `enemies/`, `bosses/` | `enemy`, `boss` | Statistiche, comportamento, bottino, fasi |
| `skills/`, `skill_trees/` | `skill`, `skill_tree` | Abilità e alberi |
| `statuses/`, `elements.json` | `status`, `elements` | Stati alterati ed elementi |
| `items/`, `recipes/`, `loot_tables/`, `shops/` | `item`, `recipe`, `loot_table`, `shop` | Oggetti ed economia |
| `crops/`, `animals/` | `crop`, `animal` | Agricoltura e allevamento |
| `quests/`, `dialogues/` | `quest`, `dialogue` | Missioni e conversazioni |
| `guild/`, `titles/`, `tags/`, `achievements/` | `guild`, `title`, `tag`, `achievement` | Meta-sistemi |
| `regions/`, `world.json`, `maps/`, `stamps/`, `biomes/`, `poi/` | `region`, `world`, `map`, `stamp`, `biome`, `poi` | Mondo |
| `prefabs/`, `behaviors/` | `prefab`, `behavior` | Entità e comportamenti |
| `tables/` | `table` | Tabelle numeriche (XP, prezzi, …) |
| `art/`, `audio/`, `ui/` | `art_recipe`, `rig`, `clip`, `palette`, `synth_patch`, `sfx_recipe`, `music_pattern`, `ui_screen`, `ui_theme` | Presentazione |
| `i18n/` | `i18n` | Testi |

## 3. Esempi di formato

### 3.1 Protagonista

```json
{
  "$schema": "../../../../schemas/protagonist.schema.json",
  "id": "base:protagonist/ren",
  "name": "$i18n:protagonist.ren.name",
  "tone": "comedy_light",
  "start_region": "base:region/verdalis",
  "start_map": "base:map/ren_prologue",
  "base_stats": { "str": 6, "vit": 7, "dex": 8, "agi": 8, "int": 7, "wis": 7, "luk": 9 },
  "growth": { "str": 1.0, "vit": 1.0, "dex": 1.2, "agi": 1.1, "int": 1.0, "wis": 1.0, "luk": 1.3 },
  "free_points_per_level": 2,
  "cheat": {
    "id": "base:cheat/system_eye",
    "gauge": { "id": "base:gauge/insight", "max": 100, "regen_per_s": 0 },
    "skill_tree": "base:skill_tree/ren_system_eye"
  },
  "starting_items": [
    { "item": "base:item/practice_sword", "qty": 1 },
    { "item": "base:item/bread", "qty": 3 }
  ],
  "starting_skills": ["base:skill/ren/analyze", "base:skill/common/slash"],
  "rig": "base:art/rig/humanoid_medium",
  "art": "base:art/character/ren",
  "unlock": { "initially_available": true },
  "prologue_dialogue": "base:dialogue/ren/prologue",
  "main_quest": "base:quest/ren/main_01",
  "tags": ["base:tag/ex_office_worker", "base:tag/reincarnated_by_truck"],
  "requires_features": ["gauge_v1"]
}
```

### 3.2 Abilità (azione in tempo reale)

```json
{
  "$schema": "../../../../schemas/skill.schema.json",
  "id": "base:skill/common/slash",
  "name": "$i18n:skill.common.slash.name",
  "description": "$i18n:skill.common.slash.desc",
  "type": "active",
  "cost": { "mp": 0 },
  "cooldown_ticks": 24,
  "timing": { "startup": 6, "active": 4, "recovery": 10 },
  "movement": { "lock": true, "lunge_tiles_x100": 40 },
  "hitboxes": [
    { "shape": "arc", "radius_x100": 160, "angle_deg": 110, "offset_x100": 0, "at_tick": 6, "duration": 4 }
  ],
  "damage": { "kind": "physical", "element": "base:element/none", "power_pct": 100 },
  "on_hit": [ { "effect": "knockback", "tiles_x100": 50 } ],
  "tags": ["melee", "basic"],
  "icon": "base:art/icon/slash"
}
```

Convenzione: valori frazionari come **interi ×100** (`_x100`) o permille (`_pm`) per non avere float nei dati di gioco. Le coordinate di movimento e render possono essere float nel codice, ma i dati usano interi.

### 3.3 Nemico con comportamento dichiarativo

```json
{
  "$schema": "../../../../schemas/enemy.schema.json",
  "id": "base:enemy/slime_green",
  "name": "$i18n:enemy.slime_green.name",
  "level": 1,
  "stats": { "hp": 28, "atk": 6, "def": 2, "mdef": 1, "speed_x100": 250 },
  "element": "base:element/none",
  "weaknesses": { "base:element/fire": 150 },
  "resist_status": { "base:status/poison": 100 },
  "behavior": "base:behavior/melee_chaser_basic",
  "skills": ["base:skill/enemy/slime_bump"],
  "loot": "base:loot/slime_green",
  "xp": 6,
  "art": "base:art/creature/slime_green",
  "rig": "base:art/rig/blob",
  "bestiary": { "category": "slime", "region_hint": "base:region/verdalis" }
}
```

```json
{
  "id": "base:behavior/melee_chaser_basic",
  "states": {
    "idle":   { "do": "stand", "transitions": [
      { "when": { "sees_target": { "range_x100": 600 } }, "to": "chase" } ] },
    "chase":  { "do": "move_to_target", "transitions": [
      { "when": { "target_within": { "range_x100": 120 } }, "to": "attack" },
      { "when": { "target_lost_for_ticks": 180 }, "to": "return" } ] },
    "attack": { "do": { "use_skill": "base:skill/enemy/slime_bump" }, "transitions": [
      { "when": { "skill_finished": true }, "to": "chase" } ] },
    "return": { "do": "move_to_home", "transitions": [
      { "when": { "at_home": true }, "to": "idle" } ] }
  },
  "initial": "idle"
}
```

I boss usano lo stesso formato con `phases`: `{ "hp_below_pct": 60, "enter": [effetti], "behavior": "…" }`.

### 3.4 Quest

```json
{
  "$schema": "../../../../schemas/quest.schema.json",
  "id": "base:quest/guild/slime_extermination",
  "name": "$i18n:quest.slime_extermination.name",
  "kind": "side",
  "giver": "base:npc/guild_clerk_mira",
  "requires": { "all": [ { "guild_rank_at_least": "e" }, { "not": { "quest_done": "base:quest/guild/slime_extermination" } } ] },
  "stages": [
    { "id": "kill", "journal": "$i18n:quest.slime_extermination.kill",
      "objectives": [ { "type": "kill", "enemy": "base:enemy/slime_green", "count": 5 } ],
      "next": "report" },
    { "id": "report", "journal": "$i18n:quest.slime_extermination.report",
      "objectives": [ { "type": "talk", "npc": "base:npc/guild_clerk_mira" } ],
      "next": "end" }
  ],
  "rewards": [
    { "effect": "add_xp", "amount": 40 },
    { "effect": "add_gold", "amount": 120 },
    { "effect": "add_guild_points", "amount": 10 }
  ],
  "repeatable": { "cooldown_days": 3 },
  "failure": { "when": { "protagonist_died_times": 3 } }
}
```

Tipi di obiettivo: `kill`, `collect`, `deliver`, `talk`, `reach`, `craft`, `cook`, `harvest`, `fish`, `escort`, `survive`, `use_skill`, `use_item`, `build`, `tame`, `reach_affinity`, `reach_level`, `flag`.
Le missioni ripetibili della bacheca sono generate da **template** con segnaposto, scelti con un RNG stagionale deterministico per giorno e gilda.

### 3.5 Dialogo

```json
{
  "$schema": "../../../../schemas/dialogue.schema.json",
  "id": "base:dialogue/ren/prologue",
  "start": "n1",
  "nodes": {
    "n1": { "type": "say", "speaker": "base:npc/goddess_lyra", "expression": "gentle",
            "text": "$i18n:dlg.ren.prologue.n1", "next": "n2" },
    "n2": { "type": "choice", "choices": [
      { "text": "$i18n:dlg.ren.prologue.c1", "next": "n3" },
      { "text": "$i18n:dlg.ren.prologue.c2", "when": { "tag": "base:tag/ex_office_worker" }, "next": "n4",
        "effects": [ { "effect": "add_affinity", "target": "base:npc/goddess_lyra", "amount": 1 } ] } ] },
    "n3": { "type": "set_flag", "flag": "ren.accepted_quickly", "value": true, "next": "end" },
    "n4": { "type": "say", "speaker": "base:npc/goddess_lyra", "text": "$i18n:dlg.ren.prologue.n4", "next": "end" }
  }
}
```

Nodi: `say`, `choice`, `condition` (ramificazione), `set_flag`, `effects`, `jump`, `start_quest`, `give_item`, `battle`, `shop`, `end`. I testi possono usare segnaposto `{player_name}`, `{var:nome}`, `{plural:count|uno|altri}`.

### 3.6 Prefab (entità)

```json
{
  "id": "base:prefab/npc_villager_base",
  "components": {
    "transform": {},
    "collider": { "shape": "circle", "radius_x100": 35, "layer": "npc", "solid": true },
    "sprite_rig": { "rig": "base:art/rig/humanoid_medium", "art": "base:art/character/villager_a" },
    "interactable": { "prompt": "$i18n:ui.talk", "range_x100": 150 },
    "schedule": { "table": "base:schedule/villager_default" },
    "dialogue_ref": { "dialogue": "base:dialogue/generic/villager" }
  }
}
```

### 3.7 Ricetta d'arte vettoriale

```json
{
  "$schema": "../../../../schemas/art_recipe.schema.json",
  "id": "base:art/creature/slime_green",
  "canvas": { "w": 64, "h": 64, "origin": [32, 56] },
  "palette": "base:art/palette/slime",
  "layers": [
    { "name": "shadow", "shape": { "ellipse": [32, 56, 20, 6] }, "fill": { "color": "#000000", "alpha": 0.25 } },
    { "name": "body", "shape": { "path": "M12 52 C12 30 22 16 32 16 C42 16 52 30 52 52 Z" },
      "fill": { "radial": { "cx": 0.4, "cy": 0.3, "r": 0.8,
                            "stops": [ [0, "$p.body_light"], [1, "$p.body_dark"] ] } },
      "stroke": { "color": "$p.outline", "width": 2, "join": "round" } },
    { "name": "highlight", "shape": { "ellipse": [24, 28, 6, 4] }, "fill": { "color": "#FFFFFF", "alpha": 0.55 } },
    { "name": "eye_l", "shape": { "ellipse": [26, 36, 3, 4] }, "fill": { "color": "$p.eye" } },
    { "name": "eye_r", "shape": { "ellipse": [38, 36, 3, 4] }, "fill": { "color": "$p.eye" } }
  ],
  "variants": [ { "id": "blue", "palette_override": "base:art/palette/slime_blue" } ]
}
```

Subset supportato (v1): `rect`, `rrect`, `ellipse`, `polygon`, `path` (comandi SVG `M L H V C S Q T A Z`), riempimento `color` / `linear` / `radial` con stop, contorno con `width`, `cap`, `join`, `dash`, `alpha`, `transform` per livello, `blur_baked` (sfocatura applicata solo in fase di bake), maschere semplici (clip con un'altra forma).
Un parametro `$p.nome` pesca da una palette; permette molte varianti con una sola ricetta.

### 3.8 Rig e clip di animazione

```json
{
  "id": "base:art/rig/humanoid_medium",
  "parts": [
    { "id": "torso", "parent": null, "pivot": [0, 0] },
    { "id": "head", "parent": "torso", "pivot": [0, -14], "attach": [0, -14] },
    { "id": "arm_l", "parent": "torso", "pivot": [-6, -10] },
    { "id": "arm_r", "parent": "torso", "pivot": [6, -10] },
    { "id": "leg_l", "parent": "torso", "pivot": [-3, 8] },
    { "id": "leg_r", "parent": "torso", "pivot": [3, 8] },
    { "id": "weapon", "parent": "arm_r", "pivot": [0, 8] }
  ],
  "directions": 4
}
```

```json
{
  "id": "base:art/clip/humanoid_walk",
  "rig": "base:art/rig/humanoid_medium",
  "loop": true,
  "length_ticks": 24,
  "tracks": {
    "leg_l": { "rot": [ [0, -25], [12, 25], [24, -25] ] },
    "leg_r": { "rot": [ [0, 25], [12, -25], [24, 25] ] },
    "torso": { "pos_y": [ [0, 0], [6, -1], [12, 0], [18, -1], [24, 0] ] }
  },
  "easing": "sine_in_out",
  "events": [ { "tick": 6, "event": "footstep" }, { "tick": 18, "event": "footstep" } ]
}
```

### 3.9 Localizzazione (`data/base/i18n/it/…json`)

```json
{
  "protagonist.ren.name": "Ren Takahashi",
  "skill.common.slash.name": "Fendente",
  "ui.hp": "PV",
  "item.bread.name": "{count, plural, one {Pane} other {Pani}}"
}
```

Regola: ogni chiave presente in `it` esiste in `en` e viceversa (verifica in CI). Formato plurali: sottoinsieme ICU (`plural`, `select`) con categorie `one`/`other`.

### 3.10 Mappe a mano

Formato **Tiled TMJ**. Convenzioni:

- Tile da 32×32 unità logiche. Layer obbligatori: `ground`, `decor`, `collision`, `objects`, `light` (opzionale).
- Layer `objects`: oggetti con `type` ∈ `spawn_player`, `portal`, `npc`, `enemy_spawner`, `trigger`, `chest`, `interactable`, `light`, `sound_zone`; proprietà personalizzate = campi dei prefab.
- I **tileset** non sono immagini: un tileset è una tabella che mappa indici → ricette d'arte vettoriali (`data/base/art/tilesets/*.json`). Il TMJ referenzia solo questi ID.

## 4. Cataloghi chiusi: condizioni ed effetti

I mod possono **combinare** questi elementi ma non crearne di nuovi. Nuovi elementi richiedono una nuova versione del formato (con feature gate).

### Condizioni (`when`, `requires`)

Combinatori: `all`, `any`, `not`.
Foglie: `flag` (con `eq`/`gte`/`lte`), `var`, `level` (`gte`, `lte`), `stat`, `has_item`, `has_tag`, `has_title`, `quest_state` / `quest_done` / `quest_active`, `guild_rank_at_least`, `affinity` (`npc`, `gte`), `companion_in_party`, `protagonist_is`, `time_between`, `day_of_week`, `season_is`, `weather_is`, `region_is`, `gold_gte`, `skill_known`, `cheat_gauge_gte`, `reincarnation_count_gte`, `profile_unlocked`, `random_pm` (probabilità in permille con flusso RNG nominato), `difficulty_is`.

### Effetti

`add_xp`, `add_gold`, `add_item`, `remove_item`, `add_stat_modifier`, `remove_stat_modifier`, `heal`, `restore_mp`, `damage`, `apply_status`, `remove_status`, `knockback`, `teleport`, `spawn_entity`, `despawn_entity`, `set_flag`, `add_var`, `start_quest`, `advance_quest`, `fail_quest`, `add_affinity`, `add_title`, `add_tag`, `remove_tag`, `add_guild_points`, `unlock_recipe`, `unlock_skill`, `unlock_protagonist`, `add_echoes`, `set_time`, `set_weather`, `play_sound`, `play_music`, `start_dialogue`, `start_battle`, `open_shop`, `open_screen`, `show_toast`, `camera_shake`, `screen_fade`, `set_waypoint`, `add_journal_entry`, `grant_achievement`.

Ogni elemento ha in `docs/spec` una definizione precisa (parametri, ordine di valutazione, esempi) e un vettore di test.

## 5. Specifica numerica

### Unità e tempo

- 1 **tile** = 1,0 unità di mondo = 32 unità logiche di render. Origine in alto a sinistra, **y verso il basso**.
- **Tick** = 1/60 s. Durate in tick o in secondi di gioco ×60. Giorno di gioco = 24 minuti reali = 86.400 tick; 1 minuto reale = 1 ora di gioco.
- Posizioni e velocità: `float` nel codice (non specificate bit-a-bit). Nei dati: interi ×100 (`_x100`).

### Interi e punto fisso

- Gli stati di gioco (statistiche, danni, oro, XP) sono interi `int32`; i prodotti intermedi usano `int64`.
- Percentuali in `pct` (÷100) e permille `pm` (÷1000). Divisioni: **floor** per valori non negativi; per i negativi si usa un helper `div_floor` (definito in spec) per evitare differenze C++/Kotlin.
- Punto fisso **Q16.16** (`int32`) con prodotto in `int64` e shift aritmetico; tabelle trigonometriche precalcolate (256 voci) per quello che serve.

### RNG

- **PCG32** (XSH-RR). Seed a 64 bit.
- Flussi nominati derivati con **SplitMix64**: `world`, `combat`, `loot`, `quest`, `weather`, `cosmetic`, `ai`. Ogni flusso ha `state` e `inc` salvati nel salvataggio (tranne `world`, che è senza stato e funzione del seed).
- **Hash di coordinate:** `hash(seed, a, b, c)` = mixing SplitMix64 a 64 bit, `uint64`. Usato dal worldgen: nessun RNG sequenziale per chunk, così l'ordine di generazione non conta.
- Per i test, tutti i flussi sono iniettabili.

### Rumore (worldgen)

- Value noise e gradient noise su reticolo intero, interpolazione con `smoothstep` in Q16.16, ottave frattali con somma intera. Nessun `sin`, `cos`, `pow`, `exp`, `sqrt` in virgola mobile nel worldgen.
- La specifica contiene gli algoritmi esatti e **vettori di test** (es. `noise2(seed=1234, x=…, y=…) = …`).

## 6. Statistiche e formule (valori iniziali)

### Statistiche primarie

`STR` (forza), `VIT` (vitalità), `DEX` (destrezza), `AGI` (agilità), `INT` (intelletto), `WIS` (saggezza), `LUK` (fortuna).
A ogni livello: crescita automatica secondo `growth` del protagonista + 2 punti liberi.

### Statistiche derivate

| Derivata | Formula (interi) |
|---|---|
| PV massimi | `50 + VIT*12 + level*8 + equip` |
| PM massimi | `20 + WIS*8 + INT*3 + level*3 + equip` |
| ATK | `STR*2 + DEX/2 + arma` |
| MATK | `INT*2 + WIS/2 + bastone` |
| DEF | `VIT*12/10 + armatura` |
| MDEF | `WIS*12/10 + armatura` |
| Velocità movimento (tile/s) | `4,0 × (1 + min(AGI*0,2%, 40%))` |
| Velocità d'attacco | `×(1 + AGI*0,4% + DEX*0,2%)`, tetto 2,0 |
| Crit chance (pm) | `50 + LUK*15 + DEX*10`, tetto 600 |
| Crit multiplier (pm) | `1500 + LUK*3`, tetto 2500 |
| Resistenza stati (pm) | `WIS*3 + LUK*1`, tetto 750 |
| Rigenerazione PM (per s) | `0,5 + WIS*0,05` (fuori combattimento ×2) |

### Danno

```
raw        = (ATK | MATK) * power_pct / 100
elem       = raw * element_mult_pm / 1000        // 1500 debolezza, 500 resistenza, 1000 neutro
def_eff    = DEF_target * (1000 - pen_pm) / 1000
mitigated  = elem * 100 / (100 + def_eff)
lvl_mod    = clamp(1000 + 30 * (lvl_attacker - lvl_target), 700, 1300) / 1000
variance   = random_pm(950..1050)                // flusso `combat`
crit       = (crit_roll ? crit_mult_pm : 1000)
final      = max(1, floor(mitigated * lvl_mod * variance * crit * buff_mod))
```

Ordine fisso: moltiplicatori percentuali di buff/debuff sommati e applicati una sola volta in `buff_mod`.

### Schivata e parata (tempo reale)

- **Schivata:** 12 tick di invulnerabilità, durata totale 24 tick, ricarica 48 tick (0,8 s). Nessuna stamina (comodità su mobile).
- **Parata:** finestra 8 tick all'inizio della guardia. Parata perfetta: nessun danno, stordimento 45 tick all'attaccante, ricarica di una skill a scelta di 20%.
- **Hit stop:** 3 tick di congelamento a colpo normale, 6 a colpo critico (solo presentazione, non cambia la logica).

### Elementi

Fuoco, Acqua, Vento, Terra, Luce, Oscurità, Neutro. Matrice in `data/base/elements.json` (default: ciclo Fuoco > Vento > Terra > Acqua > Fuoco a 1500/500; Luce ↔ Oscurità reciprocamente a 1500).

### Stati alterati (esempi)

| Stato | Effetto | Durata base | Cumulo |
|---|---|---|---|
| Veleno | `MaxHP/50` danno ogni 60 tick | 10 s | Rinnova |
| Bruciatura | `MATK/8` ogni 30 tick | 6 s | Cumula fino a 3 |
| Gelo | Velocità −40% | 5 s | Rinnova |
| Stordimento | Nessuna azione | 1,5 s | Non cumula; immunità 3 s dopo |
| Sanguinamento | 2% PV ogni 45 tick | 8 s | Cumula fino a 5 |
| Rigenerazione | +`MaxHP/60` ogni 60 tick | 12 s | Rinnova |
| Fretta | Velocità e attacco +25% | 15 s | Rinnova |
| Scudo | Assorbe `valore` danni | 20 s | Maggiore sostituisce |
| Fatica | Tutte le statistiche −10% | 120 s | Non cumula (penalità di morte) |

### Esperienza

- Tabella `xp_table.json`: XP per salire da livello L a L+1, generata dallo script di riferimento con `floor(30·L^1,6 + 20·L)`: ad esempio ≈ 50 (L1), ≈ 1.390 (L10), ≈ 16.700 (L50), ≈ 48.000 (L98). **Il codice legge la tabella, non calcola la potenza.**
- Livello massimo 99 per protagonista. Dopo la reincarnazione il tetto resta 99, ma si acquisiscono **Echi** e **Rango dell'anima**.
- XP del nemico: `enemy.xp * clamp(1000 + 100*(lvl_enemy - lvl_player), 100, 1500) / 1000` (meno XP dai nemici molto più bassi).

### Bottino

- `loot_table`: lista di voci `{item, qty_min, qty_max, weight, condition}` con più tiri (`rolls`) e bonus `luk`: `pm_extra = LUK*2`.
- Rarità oggetti: Comune, Non comune, Raro, Epico, Leggendario, Mitico (valori di prezzo ×1, ×3, ×10, ×35, ×120, ×400).

### Economia

- Valuta: **Aure** (moneta d'oro).
- `prezzo_acquisto = base × fattore_regione_pm × fattore_domanda_pm × (1000 − sconto_cha_pm) / 10^9`.
- `prezzo_vendita = floor(prezzo_acquisto_base × 40%)`.
- Domanda: ogni negozio ha scorte e un fattore 800–1300‰ che sale quando si compra e torna al valore base in 3 giorni di gioco; il rumore giornaliero usa il flusso `quest` con hash `(shop, day)`.
- Penalità morte: perdita di `min(10% oro, 500)` Aure, stato **Fatica** per 120 s, respawn alla **Pietra della Soglia** più vicina.

### Ricette e qualità

- Qualità dell'oggetto creato: `1 + (livello_mestiere × 2 + bonus_stazione + bonus_ingrediente + rng(0..10)) / 25`, da Grezzo a Maestro (1–5). Nessuna durabilità: le armi non si rompono (comodità).

## 7. Tempo, stagioni, meteo, routine

- 4 stagioni × 28 giorni = 112 giorni per anno. Nomi e durata in `world.json`.
- Meteo: catena di Markov per regione e stagione (sereno, nuvoloso, pioggia, temporale, nebbia, neve, tempesta di sabbia secondo regione); estratto una volta per ora di gioco con hash `(seed, day, hour, region)`. Quindi il meteo è **riproducibile**, anche se non richiesto dal vincolo del determinismo.
- Routine PNG: tabella di orari (`schedule`) con luogo e attività per fascia oraria e giorno; fuori dal chunk attivo la posizione si calcola dalla tabella (nessun pathfinding), quando il chunk si attiva il PNG compare nel punto corretto e percorre gli ultimi metri.

## 8. Generazione del mondo (spec 09)

**Dimensione:** 2048×2048 tile (64×64 chunk da 32×32).

**Livello 1, macro-mappa** (celle da 16×16 tile, 128×128 celle): calcolata una volta all'avvio di una partita (< 200 ms attesi):

1. Regioni: ancore a mano in `world.json`; assegnazione cella→regione con Voronoi pesato e disturbo del confine (domain warp) a punto fisso.
2. Altezza, umidità, temperatura: rumore frattale per cella, modulato dal profilo regionale.
3. Biomi per cella da una tabella (`biomes/`).
4. Fiumi: tracciamento "verso il basso" su altezza intera con tie-break deterministico.
5. Strade: grafo tra insediamenti (MST + qualche arco extra), percorso A* su griglia di costi con tie-break per coordinate.
6. Posizionamento punti d'interesse: ancore a mano per città e dungeon chiave; extra con campionamento Poisson-disk con hash.

**Livello 2, chunk** (32×32 tile): funzione pura di `(seed, cx, cy, macro-mappa, dati)`:

1. Terreno base e autotile (bitmask 47 blob) dai biomi.
2. Stamp a mano (mappe TMJ) intersecanti il chunk.
3. Strade e fiumi dal macro-livello.
4. Decor (alberi, rocce, fiori) con hash per tile e densità del bioma.
5. Risorse raccoglibili, nidi di mostri, ingressi di dungeon.
6. Collisioni e luci.

**Persistenza:** differenze (`deltas`) per chunk: risorse raccolte, strutture costruite, tile modificati, nidi sconfitti. Nessun chunk completo nei salvataggi.

**Streaming:** chunk attivi = raggio 3 (49 chunk), semiattivi = raggio 5 per soli dati. Generazione e bake su thread di lavoro con priorità per distanza.

**Test:** vettori con `hash` del contenuto di chunk campione (es. 200 chunk su 5 seed). C++, Kotlin e Python devono dare lo stesso hash.

## 9. Salvataggi (spec 12)

```text
saves/
├─ profile.json        meta-progressione condivisa (Echi, protagonisti sbloccati, titoli, achievement, bestiario globale, impostazioni di sblocco)
├─ settings.json       impostazioni locali (non fanno parte del salvataggio esportabile)
├─ slot_1/ … slot_5/
│  ├─ run.json         protagonista, seed, tempo del mondo, giocatore, party, inventario, quest, flag, variabili, legami, base, RNG
│  ├─ deltas/{cx}_{cy}.json
│  └─ thumbnail.png    256×144
└─ auto/ (rotazione a 3 voci)
```

- Campi comuni: `save_version` (int), `game_version`, `data_format_version`, `pack_list` (id+versione), `created_at`, `play_time_s`, `crc32`.
- **Migrazioni:** funzioni `migrate_N_to_N+1` nella spec e in entrambi i client, testate con file di esempio in `tests/conformance/saves/`.
- Scrittura **atomica** (file temporaneo + rename), con 3 backup `.bak`.
- **Export/Import:** un solo file `.aethersave` (zip) contenente `profile.json` e uno slot. Desktop: copia manuale o pulsante. Android: Storage Access Framework (scegli cartella/file).
- Mod mancanti: il salvataggio si carica, le entità di pack assenti vengono sostituite da segnaposto e viene mostrato un avviso.
- **Ritorno alla Morte** (protagonista Lena): usa lo stesso serializzatore in memoria come snapshot al checkpoint.

## 10. Test di conformità (cosa e come)

Formato dei vettori (`tests/conformance/<categoria>/*.json`):

```json
{
  "suite": "damage",
  "spec_version": 1,
  "cases": [
    { "name": "basic_slash_no_def",
      "input": { "atk": 20, "power_pct": 100, "def": 0, "elem_mult_pm": 1000, "pen_pm": 0,
                 "lvl_a": 1, "lvl_t": 1, "variance_pm": 1000, "crit": false, "buff_mod_pm": 1000 },
      "expect": { "damage": 20 } }
  ]
}
```

Categorie: `rng`, `hash`, `noise`, `worldgen_chunk_hash`, `damage`, `stats_derived`, `xp_table`, `status_ticks`, `loot_roll`, `economy_price`, `time_season`, `weather`, `quest_state_machine`, `dialogue_eval`, `condition_eval`, `effect_apply`, `save_roundtrip`, `save_migration`, `i18n_format`, `vector_recipe_parse`, `crafting_quality`.

- I vettori sono generati da `tools/reference/` (Python) e verificati dal riferimento stesso; il commit include sia vettori sia generatore.
- Ogni client ha un runner: `desktop/tests/conformance` (Catch2) e `android/core/src/test/.../ConformanceTest.kt` (JUnit) che carica gli stessi file.
- **Test visivi (golden):** ricette campione rasterizzate dai due client confrontate con immagini di riferimento con tolleranza (errore medio per pixel e SSIM). Soglie diverse per piattaforma, documentate.
- **Scenari headless:** `tests/scenarios/*.json` con input scriptato per N tick e asserzioni tolleranti ("il nemico è morto entro 600 tick", "la quest è nello stato X"). Non si confronta lo stato bit-a-bit.

## 11. Localizzazione

- Lingue iniziali `it`, `en`. Altre lingue si aggiungono con una cartella `i18n/<lingua>/` e una voce nel manifest.
- Chiavi gerarchiche (`dlg.…`, `item.…`, `ui.…`). Fallback: lingua scelta → inglese → chiave.
- Controlli in CI: chiavi mancanti, chiavi orfane, segnaposto incoerenti, lunghezza massima per UI (avviso se un testo supera la larghezza prevista di +40%).
- Font: set Latin esteso con OFL; le lingue CJK richiedono font aggiuntivi (fuori dall'1.0, ma il sistema di fallback per font c'è fin dall'inizio).
- Formattazione: numeri, date di gioco e plurali via spec; nessuna dipendenza dalla localizzazione del sistema operativo.

## 12. Modding

Cosa è possibile con i soli file dati:

- Nuovi protagonisti, compagni, PNG, nemici, boss (con i comportamenti e gli effetti del catalogo).
- Nuove skill, alberi, oggetti, ricette, quest, dialoghi, negozi, titoli, tag, mappe e stamp.
- Nuove ricette d'arte, rig, clip, patch audio, temi UI e schermate.
- Sovrascrivere l'arte con SVG/PNG/OGG tramite `overrides/`.

Cosa non è possibile: nuove meccaniche (richiedono nuove versioni del motore e del formato).

Distribuzione dei mod: cartella `mods/<id>/` con `pack.json`.

- Desktop: `Documenti/Aethermoor/mods/` (o equivalente Linux in `$XDG_DATA_HOME`).
- Android: import tramite picker che copia lo zip nella cartella dell'app; non si richiede accesso a `Android/data/`.

Documentazione per i modder: `docs/modding/`, con riferimento ai campi **generato dagli schemi**, un pack d'esempio, la guida passo-passo "Il tuo primo protagonista" e la lista degli errori più comuni.
