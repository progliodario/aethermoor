# 06. Items: selecting and using

Status: **v1.1 (M6a: using items, M6b: equipment and shops; the ladder of weapons and armors is data)**. Reference: `CombatSim.use_item`, `equip`, `buy` and `sell` in `tools/reference/combat.py`.
Conformance: the `combat` scenarios with the `use`, `equip`, `open_shop`, `buy`, `sell` and `close_shop` commands.
Item data: `data/base/items/*.json` (`schemas/item.schema.json`). Accessories and more slots come with the progression systems.

## Inventory

The inventory is a map from item ID to a positive quantity (spec 12); an item whose quantity reaches 0 is removed. Clients list it ordered by ID.

## Gathering

The props of the world that look like something can be **gathered from**: pressing `E` (the interact button) with nobody to talk to and no Threshold Stone in reach picks the nearest of them.
The table is `data/base/gathering.json` (schema `gathering`): for each prop art ID, the `sound` of gathering (`plant`, `wood`, `stone` or `water`), a `cooldown_ticks`, a `reach_x100`
(how far from the prop the player may be, besides the radius of the prop) and `drops`. The base pack has the bush (berries, healing herbs), the oak and the pine (logs, resin, dry branches),
the dead tree, the rock (stone, a little iron ore), the cactus (pulp), the **mushroom patches** of the forests (spore caps, herbs, now and then moss) and the **reeds** of the beaches, where one fishes (fresh fish, and now and then a golden carp that merchants pay well for). The materials are items of kind `material` or `food`.

- The prop is the nearest of those whose distance from the player is at most `reach + radius` and that have grown back (ties: the smaller `x`, then the smaller `y`). Dialogues refuse it.
- A prop is identified by `(x100, y100) = floor(x * 100 + 0.5), floor(y * 100 + 0.5)` of its feet. The game keeps, for each prop gathered from, the tick when it grows back
  (`world tick + cooldown_ticks`) and how many times it has been gathered (`times`). A prop that has not grown back is not picked.
- **What is found** is decided without a random stream, from the seed, the prop and `times`: `h = hash64(fnv1a64("gather") xor seed, x100, y100, times)` (spec 01), and the draw `j` is
  `mix64((h + j) mod 2^64)`. For the drops in order, with index `i`: the drop is found when `draw(2 i) mod 1000 < weight_pm`, and then its quantity is
  `qty_min + draw(2 i + 1) mod (qty_max - qty_min + 1)`. The items go into the bag at once. A gathering that finds nothing still uses the prop up.
- The state of what was gathered is **not saved**: after loading a game the props are as if they had grown back.
- Presentation: a message with the items, and the sound `gather.<sound>` (the creature cue `gather`, spec 14). The conformance scenario `gather_nodes` covers the nearest prop, the cooldown, the reach and
  the draws.

### Seasons of the gathering

A gatherable prop may have `season_bonus`, an object from season id to a number: in that season (the season of the day, spec 08; the
`season` of a scenario) every drop found there gives that many more, after the titles. The base pack: bushes in summer and autumn,
flowers and ferns in spring, mushrooms in autumn, the reeds of the fishing in summer, oaks, pines and shards of ice in winter, one more
each (`tools/make_gathering.py`). Conformance: the scenarios `gather_in_autumn`, `gather_in_spring`.

## Farming

`data/base/farming.json` (ID `base:farming/all`, schema `farming`) names the **plot** prop, the reach of the player and the **crops**, in order: each a `seed` item, a `crop` item, `qty_min`, `qty_max` and `grow_ticks`. `tend()`:

- is refused, changing nothing, while a dialogue is open and when no plot is within `reach_x100 / 100 + its radius` tiles of the player (the nearest one, then the smaller x, then the smaller y, like gathering);
- on a **sown** plot that is not ripe yet (`world_ticks < ripe`) it is refused; on a **ripe** one it **harvests**: `qty = qty_min + mix64(hash64(fnv1a64("harvest") ^ seed, x100, y100, ripe)) % (qty_max - qty_min + 1)`, plus the `gather_bonus` of the earned titles, of the crop go into the bag, the plot is bare again and the counter `harvested` goes up by one;
- on a **bare** plot it **sows** the first crop of the data whose seed the bag holds: one seed leaves the bag, the plot is ripe at `world_ticks + grow_ticks`, and the counter `sown` goes up by one; with no seed it is refused.

The sown plots are saved (`plots` in the save document, spec 12): `[x100, y100, seed, ripe]`, where `x100` and `y100` are the position of the plot in hundredths of a tile. The base pack has a **garden plot** (art `base:art/prop/garden_plot`): three of them by the campfire of every village of the `village` stamp, Fenwick among them, and four seeds sold by every shop: herb seeds (healing herbs in a minute), berry seeds, mint seeds (a minute and a half) and mushroom spores (spore caps in two minutes). The clients tend a plot with the action of talking (`E`, or the `Tend` button), and draw sprouts on a growing plot and flowers on a ripe one. Conformance: the scenario `farming_plots` (its checkpoints carry `plots`).

### Seasons on the plots

`season_grow_pm` of the farming data (an object from season id to permille; a season not listed, and a world without seasons, is 1000)
makes a seed grow sooner or later with the season of the day it is sown (spec 08, "Seasons"): the ripe tick is
`now + grow_ticks * (1000 - rain_cut) / 1000 * season_pm / 1000` (integer divisions, in this order, with the rain of the next section).
The base pack: spring 800, summer 900, autumn 1000, winter 1250. In the scenarios the season is `season` of the scenario:
`farming_in_winter`, `farming_in_spring` (with the rain).

### Rain on the plots

`rain_grow_cut_pm` of the farming data (default 0) says how much **full rain** shortens the growing of a seed: a seed sown while it rains is ripe at `world_ticks + grow_ticks * (1000 - rain_pm * rain_grow_cut_pm / 1000) / 1000` (integer divisions, in this order), with the `rain_pm` of that tick (spec 08; 0 on a map without weather). The rain that falls later does not change a plot already sown. In the base pack the cut is 500: a seed sown in a downpour grows in half the time. Conformance: the scenario `farming_in_the_rain`.

## Animals

Every village of the `village` stamp keeps animals by its houses: a **hen coop** (art `base:art/prop/coop`) and a **goat pen** (`base:art/prop/pen`). They are props to gather from (see "Gathering"; `tools/make_gathering.py`): the coop gives two to four eggs and now and then a hen feather every minute and a half, the pen one to three bowls of fresh milk every two minutes. Eggs and milk restore a little health, and at a campfire they become an omelette (two eggs and an herb), a goat cheese (three bowls of milk) and berry pancakes (an egg, a bowl of milk and berries); six hen feathers and some silk make an owl charm at an anvil. No rule is new: the animals are gathering nodes.

## Chests

`data/base/storage.json` (ID `base:storage/chests`, schema `storage`) names the **chest** prop and the reach of the player (`reach_x100`). Every chest of the world holds the same things: one store of items, saved as `chest` (spec 12), shared by all the chests, so what is put in one is taken from any other.

- `open_chest()` is refused, changing nothing, while a dialogue is open and when no chest is within `reach_x100 / 100 + its radius` tiles of the player; otherwise the chests are open. `close_chest()` closes them. A loaded game has them closed.
- `chest_put(item)` moves the **whole stack** of the item from the bag into the chest; when the item is worn, the last copy stays in the bag. It is refused, changing nothing, when the chests are closed or nothing would move.
- `chest_take(item)` moves the whole stack of the item from the chest into the bag, and the quests are checked again at once (an item in the bag may finish a quest that collects it). It is refused when the chests are closed or the chest has none.

The base pack has a **chest** (art `base:art/prop/chest`) in a house of every village and in the inn of every town (the stamps `village`, `village_b` to `village_d`, `town`, `town_b`, `town_c`; Fenwick has one in the house of Nana Brin, spec 07). The clients open the chests with the action of talking (`E`, or the `Chest` button) and show them in the panel of the shop: a tab "Take" with what the chest holds and a tab "Store" with the bag, each entry with its quantity; `E` (or a second tap) moves the stack, `Esc` closes. The world is paused while they are open. Conformance: the scenario `chest_storage` (its checkpoints carry `chest` and `chest_open`), and a save split of it.

## Runes

An item of kind `rune` has `rune {element, atk, matk, station}` (each optional: `none`, 0, 0 and anywhere when absent). **Using** a rune from the bag (`use_item`) engraves it on the **worn weapon**:

- it is refused, changing nothing, while a dialogue is open, when no weapon item is worn (the base weapon of the protagonist bears no rune), when the worn weapon already bears that same rune, and when the `station` of the rune is not within 2 tiles of the player (plus its radius, as in "Stations");
- otherwise one rune leaves the bag and `runes[weapon] = rune`: a rune the weapon bore before is **lost**. The counter `engraved` grows by one (spec 11) and the derived statistics are recomputed at once (the current health is capped to the new maximum).

The rune of the worn weapon adds its `atk` and `matk` to `weapon_atk` and `weapon_matk` (spec 04), and when its `element` is not `none` the weapon hits with that element instead of its own (spec 05, "Elements" and "Status effects": the weakness, the resistance and the status of the hit follow the rune). A skill with its own element keeps it. Every weapon keeps its own rune: changing weapon changes which rune counts. The runes are saved (`runes`, spec 12).

The base pack has seven, made at an anvil (`tools/make_furnishings.py`): the ember (fire), tide (water), gale (wind), stone (earth), dawn (light) and dusk (dark) runes, each +6 attack (the stone +8), and the rune of might (+12 attack, no element). The status window names the rune after the weapon. Conformance: the scenario `runes_engrave` (its checkpoints carry `runes` and the derived `atk`) and two save splits of it.

## Furniture

`data/base/home.json` (ID `base:home/cottage`, schema `home`) names the **spot** prop, an empty place of the home, and the reach of the player (`reach_x100`). An item of kind `furniture` has `furniture {art, atk_pct, gather_bonus, craft_bonus, parry_bonus, xp_pct, fine_pm}`: the prop it is drawn as and what it adds (each optional, 0 when absent).

**Using** a piece from the bag (`use_item`) places it on the **nearest spot** within `reach_x100 / 100 + its radius` tiles of the player (the nearest by distance, then by `x`, then by `y`, as the plots):

- it is refused, changing nothing, while a dialogue is open, when no spot is in reach, and when that spot already holds the same piece;
- otherwise one piece leaves the bag and stands on the spot; the piece that stood there goes **back to the bag**. The counter `furnished` grows by one (spec 11).

What the pieces add counts **like the effects of a title** (spec 11, "Titles with effects"), wherever the player is: `atk_pct` adds to the percent of the titles on the attack of the hits, `gather_bonus`, `craft_bonus`, `parry_bonus`, `xp_pct` and `fine_pm` to the bonuses of the same name. Every **kind** of piece counts once, however many of it stand in the home. The placed pieces are saved (`furniture`, spec 12).

The base pack has ten pieces, made at an anvil (`tools/make_furnishings.py`): the quilted bed (+10% experience), the weapon rack (+5% attack), the bookshelf (+5% fine work), the drying rack (one more of everything gathered), the training dummy (the parry four ticks longer) and the work table (one more of every recipe) for the house, and for the garden the bench (+5% experience), the scarecrow (one more of everything gathered), the archery target (+5% attack) and the stone lantern (+5% fine work, the parry two ticks longer). The Guest's cottage (spec 07) has ten spots, the round braided rugs along the walls of its house (art `base:art/prop/furniture_spot`, the character `1` of the cottage stamp) and four in its garden (`2`, on the grass); any piece can stand on any spot, and is drawn on its rug. Old Tam tells the owner about them. Conformance: the scenario `furniture_home` (its checkpoints carry `furniture`) and a save split of it.

## Hunting

Hunting is fighting creatures that are game: they are ordinary creatures (spec 05) of the fauna of the regions (spec 09), shy (the behavior `skittish`), weak and slow to anger, and what they leave is
food and materials. The base pack has the **wild boar** (Verdalis, Whisperwood, Tidehaven: game meat, boar hide) the **ridge elk** (Frostveil, Ironspine, Lumeria: game meat, elk antler) and the **dune fox** (Sunscar, the Ashen Wastes: game meat, fox pelt), written by
`tools/make_hunting.py`, with their art made from the body of the wolves. Game meat heals a little raw and more roasted at a campfire; hides and antlers make a hunter's jerkin and an antler spear
at an anvil (see "Crafting").

## Crafting

Materials can be made into things from the bag, anywhere, without a workshop. The recipes are `data/base/recipes.json` (schema `recipes`): each has an `id` (a short name),
an `output` (`item`, `qty`) and `inputs` (a list of `item`, `qty`). The base pack has sixty-three (`tools/make_recipes.py`; eight of them are the secret dishes below, three are made of eggs and milk): tonics, small, medium and large health potions, small and medium mana potions, a travel ration, a honey cake, cooked dishes (a hearty stew, a fish stew, a royal feast, a miners' broth, grilled fish and a fisherman's stew from the fish of the reeds, roast meat and a hunter's stew from the game), a hunter's jerkin, an antler spear and a fox-fur cloak at an anvil, the brews of the regions, a hand axe, an iron sword, a pike, a leather vest, a studded one, and five pieces of fine gear.

`craft(id)` is refused, changing nothing, while a dialogue is open, when the recipe does not exist, and when the bag has less than the `qty` of any input. Otherwise it removes every input
(an item that reaches 0 leaves the bag) and adds `qty` of the output (an item the bag did not have enters it). There is no random number, no time and no gold in it. A craft is a creature
cue `craft` for the sound director (spec 14, event `craft`). The conformance scenario `craft_recipes` covers a recipe made twice, then refused for what is missing, an unknown recipe and a second recipe the bag can no longer pay.

Desktop: `C` opens a panel with the recipes (green when the bag has everything), `W`/`S` choose, `E` makes, `Esc` or `C` closes; the game pauses meanwhile. Android: a button next to the sound
button opens it; a tap on a recipe chooses it and a tap on the chosen one makes it. On both clients a list longer than the panel scrolls with the chosen recipe. The unique pieces that a shopkeeper makes from monster parts (spec 07, "Workshops") are a different thing and stay.

### Recipe book

A recipe may have `requires_flag`: it is **taught**, and `craft` is also refused until the story has that flag (spec 07). The crafting panels list only the recipes the player knows. In the base pack (`tools/make_secret_recipes.py`) every region has a **secret dish**, a rare food with two or three effects at once, cooked at a campfire (the flag `recipe_<dish>`): the shopkeeper of the region teaches it ("Do you know a recipe of these parts?") for 300 to 700 gold, with the existing effects `spend_gold` and `set_flag`. Verdalis teaches the grandmother's pie, Whisperwood a moonlit tea, Ironspine a forge stew, Sunscar sunfire skewers, Frostveil a hearth broth, Tidehaven a captain's chowder, the Ashen Wastes an ember chili and Lumeria a starlight soufflé. Conformance: the scenario `recipe_taught`.

### Quality

A recipe may have `fine_pm`, the chance in permille that what is made comes out **fine**, and `fine_item`. When a recipe with `fine_pm` is made:

1. `h = hash64(fnv1a64("craft") ^ seed, crafted)`, where `crafted` is the counter of the recipes made so far (spec 11), before this one;
2. the piece is fine when `mix64(h) % 1000 < fine_pm + sum of fine_pm of the earned titles` (spec 11, "Titles with effects");
3. a fine recipe with a `fine_item` gives that item instead of the output, in the same quantity; without one it gives one more of the output. The counter `crafted_fine` goes up by one.

The roll uses no random stream, so nothing is added to the save: the same game makes the same fine pieces in the same order. A recipe without `fine_pm` never rolls. In the base pack (`tools/make_recipes.py`) every dish, potion and brew has `fine_pm` 150, and so have the plain iron sword, hand axe, pike, leather vest and studded leather, whose fine piece is the fine gear of the anvil; the accessories, the cloaks and the fine gear itself have no quality. The titles of an artisan add 100 (Artisan), 150 (Master Artisan) and 150 (Fine Hand, ten fine pieces), up to 550 permille. The clients say "Fine work!" in place of the usual notice, and the crafting panel shows the chance of every recipe that has one ("fine 25%": `fine_pm` plus the titles, at most 1000). Conformance: the scenario `craft_quality`.

### Stations

A recipe may have a `station`: the art of a prop it must be made next to. `craft` is then also refused unless a prop of that art is within `2 + its radius` tiles of the player (the distance between the centres). The base pack
cooks its dishes (hearty stew, fish stew, royal feast, miner's broth) at a **campfire** (one in the plaza of every village and town, Fenwick and Aldermere among them, and of every outpost), and makes **fine gear** at an **anvil** (one in every town, Aldermere among them): a fine iron sword, hand axe and pike, a fine leather vest and studded leather, each from the plain piece and materials, with about half again its stats. The panels name the station next to such a recipe (`ui.station_<prop>`), or say that the player is at it.
Conformance: the scenario `craft_at_fire`.

## Using an item

`use_item(id)` returns whether the item was used. It is refused (nothing changes) when:

- a dialogue is open;
- the inventory does not hold the item, or the item has no `use` effects;
- none of its effects would change anything right now: no `heal` (or one at full health), no `restore_mp` (or one at full mana), no `fortify`, `ward`, `regen` or `haste`. An item with both effects is used when either one would change something.

A rune and a piece of furniture are used in their own way: see "Runes" and "Furniture".

Otherwise the effects are applied in order and the quantity of the item drops by one. Supported effects:

| Effect | Fields | Result |
|---|---|---|
| `heal` | `amount` | `hp = min(max_hp, hp + amount)` |
| `restore_mp` | `amount` (points) | `mp_u = min(max_mp * 6000, mp_u + amount * 6000)` (spec 05, "Mana") |
| `ward` | `amount` (percent), `ticks` | **Ward**: `ward_pct = amount`, `ward = ticks` (a later brew replaces both). While `ward > 0` the creatures' hits on the player use `def * (100 + ward_pct) / 100` as the player's defense (spec 05, "Hurting the player"). Like `fortify`, it goes down by one every tick, goes to 0 on death and on loading, and makes the item always useful. The regional brews ward: the miners' broth, the desert nectar and the pearl elixir +30% for 30 s, the frost tonic +40% and the ember brew +50% for a minute. Conformance: the scenario `ward_brew`. |
| `regen` | `amount` (health), `ticks` | **Regen**: `regen_amount = amount`, `regen = ticks` (a later dish replaces both). Every tick where `ward` goes down, `regen` goes down by one too; when it reaches a multiple of 60 (once a second) and the player is alive and hurt, `hp = min(max_hp, hp + regen_amount)`. It goes to 0 on death and on loading (not saved) and makes the item always useful. The honey cake (+4 a second for 20 s), the tonic (+3 for 10 s), the travel ration (+2 for 30 s) and the hearty stew (+5 for 30 s) regenerate. Conformance: the scenario `regen_cake`. The status window lists the effects still working with their seconds left (`ui.status_effects`). |
| `haste` | `amount` (percent), `ticks` | **Haste**: `haste_pct = amount`, `haste = ticks` (a later brew replaces both). While `haste > 0` walking uses `move_speed_x100 * (100 + haste_pct) / 100` (spec 05; the dodge roll does not change). It goes down with the other effects, goes to 0 on death and on loading, and makes the item always useful. The windleaf brew (+30% for a minute; a storm feather and two mint leaves) hastens. Conformance: the scenario `haste_brew`. |
| `cleanse` | none | **Cleanse**: when the player has burn, chill, stun or weaken, all of them end at once (`burn`, `burn_clock`, `chill`, `stun`, `weaken` go to 0). It counts as useful only then: with no status, an item whose only effect is `cleanse` is refused and kept. The cleansing draught (two healing herbs and a spore cap make two; it also heals 30) cleanses. Conformance: the scenario `cleanse_draught`. |
| `fortify` | `amount` (percent), `ticks` | **Fortify**: `fortify_pct = amount`, `fortify = ticks` (a later meal replaces both). While `fortify > 0` the player's hits use `atk * (100 + title_attack_pct + fortify_pct) / 100` (spec 05, spec 11). `fortify` goes down by one every tick, where `weaken` does, and goes to 0 on death and on loading (not saved). An item with `fortify` is always useful, even at full health. Conformance: the scenario `fortify_meal`. |

Using an item is instant: it takes no time, has no cooldown and does not interrupt an attack. An unknown effect counts as an effect that changes nothing.

Every item used counts in the counter `used` (spec 11); with the gift `pocket_keep_pm` (spec 18) an item used may stay in the bag.

## Equipment

Three slots, **weapon**, **armor** and **accessory**. An item of kind `weapon` has `weapon {atk, matk}`, one of kind `armor` has `armor {def, mdef}`. The character wears at most one item per slot; the
slot of a new game holds the starting weapon of the protagonist, and the armor slot is empty. The equipped items give the **equipment** terms of the derived statistics (spec 04):
`weapon_atk`, `weapon_matk`, `armor_def`, `armor_mdef`; with an empty weapon slot the base weapon of the protagonist data counts. The equipped item ids are saved (spec 12, `equipped`).

An item of kind `accessory` has `accessory {atk, matk, def, mdef, max_hp, crit_pm, drain_pm}` (each optional, 0 when absent): **flat bonuses** added to the derived statistics last, after the equipment terms, the echoes and the talents (`crit_pm` to `crit_chance_pm`). **Drain**: with `drain_pm`, every hit of the player gives back `max(1, damage * drain_pm / 1000)` health (the damage after the stagger bonus, before the creature's death; never above the maximum, never to a dead player); conformance: the scenario `accessory_drain`. The accessory slot of a new game is empty. The base pack has five, made at an anvil and sold in one region each: the fang necklace (+6 attack), the pearl pendant (+40 health), the owl-feather charm (+6% critical chance), the golem amulet (+5 defense, +3 magic defense), the star brooch (+8 magic), the bat-wing charm (drains 15%), the ember ring (+4 attack, +2 defense), the frost locket (+6 magic defense, +20 health) and the sand charm (+4% critical chance, +20 health). Every guardian of a region drops its region's accessory one time in three (350 per mille), and Hestia's bounties give one. Conformance: the scenario `accessory_worn`. The status window lists what is worn (`ui.status_worn`).

`equip(id)` is refused (nothing changes) when the inventory does not hold the item, it is unknown, it is not a weapon, an armor or an accessory, or it is already the one in its slot. Otherwise it fills the slot,
the derived statistics are recomputed at once and the current hit points are capped to the new maximum. The previous item stays in the inventory.

## Affixes

A weapon or an armor may have an **affix**: `affix {atk, matk, def, mdef, max_hp, crit_pm, drain_pm}`, the fields of an accessory
(each optional, 0 when absent). While the piece is worn its affix adds to the derived statistics like an accessory, after it: the
flat bonuses of the accessory, then of the affix of the weapon, then of the armor (section "Equipment"). The drains add up: every hit
gives back `max(1, damage * (accessory drain_pm + weapon affix drain_pm + armor affix drain_pm) / 1000)` health, on the same terms.
Nothing else changes: an affixed piece is an item like any other, with its own ID.

The base pack has sixteen (`tools/make_affixes.py`), an affixed weapon and an affixed armor for every region (the shepherd's blade and
the meadow coat of Verdalis, the owl-eye dagger and the moss cloak of Whisperwood, the forgeborn axe and plate of Ironspine, the dune
scimitar and the sand-silk robe of Sunscar, the glacier spear and the snowbear coat of Frostveil, the tidecaller cutlass and the
sailcloth vest of Tidehaven, the cinder brand and the ashwalker mail of the Ashen Wastes, the starglass staff and the comet robe of
Lumeria). Every guardian of a region (the creatures that drop the accessory of the region) leaves each of the two one time in five
(200 per mille), and the shop of the region keeps them for its friends (`renown_stock`, spec 07 "Renown": the weapon from renown 15,
the armor from 20). Conformance: the scenario `affixes_worn` (its checkpoints carry the `derived` stats) and a save split of it.

## Rolled affixes

An affixed piece may also have `affix_roll {min_pct, max_pct}` (`min_pct` at least 1, `max_pct` at least `min_pct`): how strong its
affix comes out when the piece is **found on a creature**. When a kill drops it (spec 05, "Loot"), right after the quantity of that drop
is drawn, the percent is drawn from the same `loot` stream:

```
pct = min_pct + loot.next_bounded(max_pct - min_pct + 1)       (no draw when max_pct == min_pct: pct = min_pct)
rolls[item] = max(rolls[item] or 0, pct)                        (finding it again keeps the better roll)
```

The **affix held** of a piece with a roll is every bonus of its `affix` times the roll, `value * pct / 100` (integer division, field by
field: `atk`, `matk`, `def`, `mdef`, `max_hp`, `crit_pm`, `drain_pm`); a piece without a roll (bought, given by a quest or a gift, or
never rolled) has the affix of the data. The affix held is what adds to the derived stats and to the drain (section "Affixes"); when a
roll of a worn piece grows, the derived stats are worked out again at once. The roll belongs to the item ID: every copy has it, in
the bag or in the chest. Selling the last copy of the bag, with none in the chest, forgets it.

The base pack rolls the sixteen regional pieces from 100 to 160 percent (`tools/make_affixes.py`): a piece found is never weaker than
the one of the shop. It also has twenty-four **common pieces with an affix** (`tools/make_common_affixes.py`): the iron sword and the
leather vest, the knight's sword and the chain mail, the claymore and the knight's plate, each of vigor (health), of might (attack), of
keenness (critical chance) and of the leech (a drain), rolled from 100 to 150 percent. Every creature of the fauna leaves one of the
eight of its tier (level up to 4, up to 8, above) one time in thirty: a drop "one of a list" (`pick`, spec 05, "Loot"). The rolls are saved (`rolls`, spec 12). Presentation: the bag and the status window write the roll after the name
(`ui.affix_roll`, "affix 132%"). Conformance: the scenario `affixes_rolled` (its checkpoints carry `rolls`) and two save
splits of it.

## Shops

A region sells goods: `regions[].shop` is `{price_pm, stock}` (spec 09); a settlement shop sells the stock of its region, so prices and goods differ across the world. Shops open from a dialogue with the effect
`open_shop` (spec 07). While a shop is open the game is paused and the player can buy, sell and close it. A shop closes when it is closed, and it is not saved.

- **Prices.** Item `price` is its base value. Buying costs `max(1, price * price_pm / 1000)` (integer division), then the market of the day moves it (below): `max(1, that * market_pm / 1000)`, then the renown of the region takes its share off (spec 07, "Renown"): `max(1, that * (1000 - discount_pm) / 1000)`; selling gives `max(1, price / 2 * market_pm / 1000)`. An item with `price` 0 cannot be bought or sold.
- `buy(id)` is refused unless the shop is open, the item is in its stock, the gold is at least the price, and the inventory holds fewer than the stack limit of the item (`stack_max`,
  default 1 for weapons, armor and accessories and 99 for the rest). Otherwise gold drops by the price and the inventory gets one more.
- `sell(id)` is refused unless the shop is open, the inventory holds the item, and it has a price; it is also refused for the last copy of an item that is equipped. Otherwise gold grows and the inventory loses one.

### Glut

A shop may have `glut_step_pm` and `glut_floor_pm` (`regions[].shop`, spec 09): it pays less for an item the more of it the player has sold to any shop that day. The selling price is `max(1, price * max(glut_floor_pm, 1000 - glut_step_pm * sold) / 1000)`, where `price` is the selling price of "Shops" and "Market days" and `sold` the copies of that item sold since the day began (the day of the world, spec 08; 1 on a map without a clock). A new day forgets them. Nothing of it is saved: a loaded game starts the day afresh. In the base pack every shop takes 80 permille off for every copy sold, down to 400: selling one sword is a good trade, selling twenty of the same pelt is not. Conformance: the scenario `shop_glut`.

### Market days

A shop may have `market_swing_pm` (`regions[].shop`, spec 09): its prices move with the day, the same way for buying and for selling. `market_pm = 1000 - swing + hash64(fnv1a64("market:" + region id) ^ seed, day) % (2 * swing + 1)`, where `day` is the day of the world (spec 08; `world_ticks / day_ticks + 1`, and 1 on a map without a clock) and the hash is unsigned. Without a swing, or with no shop open, `market_pm` is 1000. Nothing is saved: the day gives the price. In the base pack the swing goes from 60 permille in Ironspine ("prices fixed") to 200 in Sunscar, where one haggles. The shop panel says "Today +7%" or "Today -12%". Conformance: the scenario `market_days`.

A shop may also have `renown_stock`, wares for the friends of the region (spec 07, "Renown").

### Goods from afar

The effect `open_shop` may name a `region` and a `markup_pct` (spec 07): the shop that opens then sells the stock of that region at `price_pm * markup_pct / 100` (integer division) of its prices, with its own swing of the market; it has no wares for friends, and the market of the day and the renown are still those of the region where the player stands. A region the world does not have opens the shop of the place. In the base pack the shopkeeper of every settlement also sells "what the caravan brought": the goods of the next region along the ring of the wayfarers (Verdalis sells those of Ironspine, Ironspine of the Ashen Wastes, then Sunscar, Lumeria, Tidehaven, Frostveil, Whisperwood and Verdalis again), at 125 percent (`tools/make_friend_quests.py`). In a conformance scenario the far shops are `far_shops`, by region. Conformance: the scenario `goods_from_afar`.

## Bag screen

The bag shows the items ordered by ID with a cursor on one of them; the name and quantity are listed, and the description of the item under the cursor is shown below the list. Clients
move the cursor with the up and down keys (W/S, arrows, D-pad), use the item under it (or equip it, for a weapon or an armor; an equipped item is marked) with the confirm key (E, Enter, gamepad X, or tapping it a second time on a touch screen), and
close the bag with the bag key or Esc. A notice tells what happened ("Used Bread", or that nothing was changed). The game is paused while the bag is open.
