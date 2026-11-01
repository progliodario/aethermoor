# 06. Items: selecting and using

Status: **v1 (M6a)**. Reference: `CombatSim.use_item` in `tools/reference/combat.py`. Conformance: the `combat` scenarios with the `use` command.
Item data: `data/base/items/*.json` (`schemas/item.schema.json`). Equipment (several weapons, armor, slots) comes with the progression systems.

## Inventory

The inventory is a map from item ID to a positive quantity (spec 12); an item whose quantity reaches 0 is removed. Clients list it ordered by ID.

## Using an item

`use_item(id)` returns whether the item was used. It is refused (nothing changes) when:

- a dialogue is open;
- the inventory does not hold the item, or the item has no `use` effects;
- none of its effects would change anything right now (for example, healing at full health).

Otherwise the effects are applied in order and the quantity of the item drops by one. Supported effects:

| Effect | Fields | Result |
|---|---|---|
| `heal` | `amount` | `hp = min(max_hp, hp + amount)` |

Using an item is instant: it takes no time, has no cooldown and does not interrupt an attack. An unknown effect counts as an effect that changes nothing.

## Bag screen

The bag shows the items ordered by ID with a cursor on one of them; the name and quantity are listed, and the description of the item under the cursor is shown below the list. Clients
move the cursor with the up and down keys (W/S, arrows, D-pad), use the item under it with the confirm key (E, Enter, gamepad X, or tapping it a second time on a touch screen), and
close the bag with the bag key or Esc. A notice tells what happened ("Used Bread", or that nothing was changed). The game is paused while the bag is open.
