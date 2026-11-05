# 06. Items: selecting and using

Status: **v1.1 (M6a: using items, M6b: equipment and shops; the ladder of weapons and armors is data)**. Reference: `CombatSim.use_item`, `equip`, `buy` and `sell` in `tools/reference/combat.py`.
Conformance: the `combat` scenarios with the `use`, `equip`, `open_shop`, `buy`, `sell` and `close_shop` commands.
Item data: `data/base/items/*.json` (`schemas/item.schema.json`). Accessories and more slots come with the progression systems.

## Inventory

The inventory is a map from item ID to a positive quantity (spec 12); an item whose quantity reaches 0 is removed. Clients list it ordered by ID.

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
