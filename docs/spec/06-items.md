# 06. Items: selecting and using

Status: **v1.1 (M6a: using items, M6b: equipment and shops; the ladder of weapons and armors is data)**. Reference: `CombatSim.use_item`, `equip`, `buy` and `sell` in `tools/reference/combat.py`.
Conformance: the `combat` scenarios with the `use`, `equip`, `open_shop`, `buy`, `sell` and `close_shop` commands.
Item data: `data/base/items/*.json` (`schemas/item.schema.json`). Accessories and more slots come with the progression systems.

## Inventory

The inventory is a map from item ID to a positive quantity (spec 12); an item whose quantity reaches 0 is removed. Clients list it ordered by ID.

## Gathering

The props of the world that look like something can be **gathered from**: pressing `E` (the interact button) with nobody to talk to and no Threshold Stone in reach picks the nearest of them.
The table is `data/base/gathering.json` (schema `gathering`): for each prop art ID, the `sound` of gathering (`plant`, `wood` or `stone`), a `cooldown_ticks`, a `reach_x100`
(how far from the prop the player may be, besides the radius of the prop) and `drops`. The base pack has the bush (berries, healing herbs), the oak and the pine (logs, resin, dry branches),
the dead tree, the rock (stone, a little iron ore) and the cactus (pulp). The materials are items of kind `material` or `food`.

- The prop is the nearest of those whose distance from the player is at most `reach + radius` and that have grown back (ties: the smaller `x`, then the smaller `y`). Dialogues refuse it.
- A prop is identified by `(x100, y100) = floor(x * 100 + 0.5), floor(y * 100 + 0.5)` of its feet. The game keeps, for each prop gathered from, the tick when it grows back
  (`world tick + cooldown_ticks`) and how many times it has been gathered (`times`). A prop that has not grown back is not picked.
- **What is found** is decided without a random stream, from the seed, the prop and `times`: `h = hash64(fnv1a64("gather") xor seed, x100, y100, times)` (spec 01), and the draw `j` is
  `mix64((h + j) mod 2^64)`. For the drops in order, with index `i`: the drop is found when `draw(2 i) mod 1000 < weight_pm`, and then its quantity is
  `qty_min + draw(2 i + 1) mod (qty_max - qty_min + 1)`. The items go into the bag at once. A gathering that finds nothing still uses the prop up.
- The state of what was gathered is **not saved**: after loading a game the props are as if they had grown back.
- Presentation: a message with the items, and the sound `gather.<sound>` (the creature cue `gather`, spec 14). The conformance scenario `gather_nodes` covers the nearest prop, the cooldown, the reach and
  the draws.

## Crafting

Materials can be made into things from the bag, anywhere, without a workshop. The recipes are `data/base/recipes.json` (schema `recipes`): each has an `id` (a short name),
an `output` (`item`, `qty`) and `inputs` (a list of `item`, `qty`). The base pack has sixteen: tonics, small, medium and large health potions, small and medium mana potions, a travel ration, a honey cake, cooked dishes (a hearty stew, a fish stew, a royal feast), a hand axe, an iron sword, a pike, a leather vest and a studded one.

`craft(id)` is refused, changing nothing, while a dialogue is open, when the recipe does not exist, and when the bag has less than the `qty` of any input. Otherwise it removes every input
(an item that reaches 0 leaves the bag) and adds `qty` of the output (an item the bag did not have enters it). There is no random number, no time and no gold in it. A craft is a creature
cue `craft` for the sound director (spec 14, event `craft`). The conformance scenario `craft_recipes` covers a recipe made twice, then refused for what is missing, an unknown recipe and a second recipe the bag can no longer pay.

Desktop: `C` opens a panel with the recipes (green when the bag has everything), `W`/`S` choose, `E` makes, `Esc` or `C` closes; the game pauses meanwhile. Android: a button next to the sound
button opens it; a tap on a recipe chooses it and a tap on the chosen one makes it. On both clients a list longer than the panel scrolls with the chosen recipe. The unique pieces that a shopkeeper makes from monster parts (spec 07, "Workshops") are a different thing and stay.

### Stations

A recipe may have a `station`: the art of a prop it must be made next to. `craft` is then also refused unless a prop of that art is within `2 + its radius` tiles of the player (the distance between the centres). The base pack
cooks its dishes (hearty stew, fish stew, royal feast, miner's broth) at a **campfire** (one in the plaza of every village and town, Fenwick and Aldermere among them, and of every outpost), and makes **fine gear** at an **anvil** (one in every town, Aldermere among them): a fine iron sword, hand axe and pike, a fine leather vest and studded leather, each from the plain piece and materials, with about half again its stats. The panels name the station next to such a recipe (`ui.station_<prop>`), or say that the player is at it.
Conformance: the scenario `craft_at_fire`.

## Using an item

`use_item(id)` returns whether the item was used. It is refused (nothing changes) when:

- a dialogue is open;
- the inventory does not hold the item, or the item has no `use` effects;
- none of its effects would change anything right now: no `heal` (or one at full health) and no `restore_mp` (or one at full mana). An item with both effects is used when either one would change something.

Otherwise the effects are applied in order and the quantity of the item drops by one. Supported effects:

| Effect | Fields | Result |
|---|---|---|
| `heal` | `amount` | `hp = min(max_hp, hp + amount)` |
| `restore_mp` | `amount` (points) | `mp_u = min(max_mp * 6000, mp_u + amount * 6000)` (spec 05, "Mana") |

Using an item is instant: it takes no time, has no cooldown and does not interrupt an attack. An unknown effect counts as an effect that changes nothing.

## Equipment

Two slots, **weapon** and **armor**. An item of kind `weapon` has `weapon {atk, matk}`, one of kind `armor` has `armor {def, mdef}`. The character wears at most one item per slot; the
slot of a new game holds the starting weapon of the protagonist, and the armor slot is empty. The equipped items give the **equipment** terms of the derived statistics (spec 04):
`weapon_atk`, `weapon_matk`, `armor_def`, `armor_mdef`; with an empty weapon slot the base weapon of the protagonist data counts. The equipped item ids are saved (spec 12, `equipped`).

`equip(id)` is refused (nothing changes) when the inventory does not hold the item, it is unknown, it is not a weapon or an armor, or it is already the one in its slot. Otherwise it fills the slot,
the derived statistics are recomputed at once and the current hit points are capped to the new maximum. The previous item stays in the inventory.

## Shops

A region sells goods: `regions[].shop` is `{price_pm, stock}` (spec 09); a settlement shop sells the stock of its region, so prices and goods differ across the world. Shops open from a dialogue with the effect
`open_shop` (spec 07). While a shop is open the game is paused and the player can buy, sell and close it. A shop closes when it is closed, and it is not saved.

- **Prices.** Item `price` is its base value. Buying costs `max(1, price * price_pm / 1000)` (integer division); selling gives `max(1, price / 2)`. An item with `price` 0 cannot be bought or sold.
- `buy(id)` is refused unless the shop is open, the item is in its stock, the gold is at least the price, and the inventory holds fewer than the stack limit of the item (`stack_max`,
  default 1 for weapons, armor and accessories and 99 for the rest). Otherwise gold drops by the price and the inventory gets one more.
- `sell(id)` is refused unless the shop is open, the inventory holds the item, and it has a price; it is also refused for the last copy of an item that is equipped. Otherwise gold grows and the inventory loses one.

## Bag screen

The bag shows the items ordered by ID with a cursor on one of them; the name and quantity are listed, and the description of the item under the cursor is shown below the list. Clients
move the cursor with the up and down keys (W/S, arrows, D-pad), use the item under it (or equip it, for a weapon or an armor; an equipped item is marked) with the confirm key (E, Enter, gamepad X, or tapping it a second time on a touch screen), and
close the bag with the bag key or Esc. A notice tells what happened ("Used Bread", or that nothing was changed). The game is paused while the bag is open.
