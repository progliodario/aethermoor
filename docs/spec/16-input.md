# 16. Input

Status: **v1**. Implemented by both clients; the simulation is tested through the shared scenarios, the devices are not (they are the platform layer).

## Abstract actions

The simulation never sees devices. A tick receives a movement vector in `[-1, 1]^2` (screen axes, y down), passed through
`normalize_input` (see `02-entities-and-movement.md`), and a boolean `attack`. Everything else is an action of the platform layer on
the simulation or the story engine: interact (talk, wake a Threshold Stone, open a shop or the guild board), choose, confirm, close, use or wear an item,
open a panel, save, load. While a dialogue is open the movement and the attack of the tick are ignored (spec 07).

## Desktop

| Device | Mapping |
|---|---|
| Keyboard, move | `W A S D` and the arrows (diagonals are normalized) |
| Keyboard, attack | `J`, `Space` or the left mouse button |
| Keyboard, interact | `E` or `Enter`: talk to the person in front of you, wake and use a Threshold Stone, confirm |
| Dialogue | `W`/`S` or the arrows choose, `E`/`Enter`/`Space` or a mouse click confirm, `1` to `9` pick a choice directly |
| Bag | `I` opens and closes it; `W`/`S` move the cursor; `E`/`Enter`/`Space` use or wear the item; `Esc` closes it |
| Shop | opened by the dialogue with a shopkeeper; `W`/`S` move, `Tab` switches between buying and selling, `E`/`Enter` confirm, `Esc` closes |
| Guild board | opened by the dialogue with a guild clerk; `W`/`S` move, `E`/`Enter` accept the work, `Esc` closes |
| Threshold Stones | `E` next to a stone: wakes it and heals; the list of woken stones opens: `W`/`S` move, `E`/`Enter` travel, `Esc` closes |
| Journal | `Q` opens and closes it; `W`/`S` scroll |
| World map | `M` opens and closes it; open: `+`/`-` (or `=`) and the mouse wheel zoom, `W A S D` or the arrows and dragging with the left button move the view, `P` marks the goal at the center of the view (a right click at the pointer), `X` removes it, `Tab` jumps to the next place found, `C` goes back to the player, `0` or `Home` frames all that was explored (spec 09, "The map view") |
| Language | `F2` switches between Italian and English at any time |
| Saves | `F5` quick save, `F9` quick load, `F7` new game (a new world in the same game) |
| Small map | `N` shows or hides the small map in the corner |
| Debug | `F3` toggles the debug overlay |
| `Esc` | closes the open panel (map, bag, journal, shop, board, stones); with none open it saves the game and returns to the list of games; on the list it quits |
| Title screen | `W`/`S` or the arrows move, `E`/`Enter`/`Space`, the number keys `1` to `3` or a mouse click choose a game, `D` or `Delete` twice deletes the selected one |
| Gamepad | left stick moves; `A` (south) attacks and confirms; `X` (west) talks and confirms; `Y` (north) switches buy/sell in a shop; `B` (east) closes a panel; the D-pad moves in lists and choices |

Several things share a key because they never happen together: `E` talks next to a person, wakes a stone next to a stone and uses the item in the bag.

## Android

| Device | Mapping |
|---|---|
| Touch, move | **Floating stick**: the first touch on the left half of the screen is the origin of the stick; dragging up to 64 dp from it gives the vector, scaled to length 1 at 64 dp |
| Touch, attack | any touch on the right half of the screen, except on a button or a panel |
| Buttons | bag and world map (first row) and journal and the language (`IT`/`EN`, second row) in the top left corner; a talk button on the right edge, shown next to a person or a stone |
| World map | drag to move, pinch (or the `+` and `-` buttons) to zoom, `Goal` marks the center of the view as the goal (again to remove it), `Next` jumps to the next place found, `You` to go back to the player, `All` to frame what was explored, `X` to close; the Back key closes it too |
| Lists | a tap on a row chooses it, a second tap on the chosen row confirms (use an item, buy, accept, travel); the journal scrolls with a tap above or below its middle; a tap outside a panel closes it |
| Title screen | a tap chooses a game, the cross twice deletes it |
| Back key | closes the open panel; with none open it saves the game and returns to the list of games; on the list it leaves the app |
| Keyboard | as on desktop (`WASD`, `J`, `Space`, `E`, `I`, `Q`, `M`, `F2`) for a physical keyboard |

Android controller support is not implemented.

The last used device decides which hints are shown: not implemented yet; the HUD shows the keys of the desktop and the buttons of Android.

## Lists that do not fit

When a list (the bag, a shop, the stones, the board) has more rows than the screen shows, the clients show a window of rows that follows the cursor, so the
last entries can be reached. The window is a presentation detail; the cursor is clamped to the list.

## Settings

The language chosen by the player is kept in `<user data>/settings.json` as `{"language": "it"}` (desktop: next to the `saves` folder; Android: the app-private
folder). Without it the language of the system is used (`it` if it is Italian, else `en`). The language can be changed at any time: texts are resolved when they are drawn (spec 17).

## Orientation (Android)

The app allows portrait and landscape (`fullUser`) and handles configuration changes itself (no activity restart).
The camera adapts: the visible area in tiles is `screen_px / tile_px`, with `tile_px` derived from the screen density
(`tile_px = round(48 * density)`, bucketed).
