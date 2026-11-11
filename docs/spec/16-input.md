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
| Title screen, export and import (desktop) | `X`: export the chosen game to a file; `I`: import `import.aethersave` into the chosen empty game (spec 12, "Export and import") |
| Keyboard, crafting | `C`: the crafting panel (spec 06, "Crafting"); `W`/`S` choose, `E` makes, `Esc` or `C` closes; Android: a button |
| Keyboard, the `E` hint | the hint over what `E` would act on says what it does: `ui.interact` over a person (talk), `ui.interact_stone` over a Threshold Stone, `ui.interact_gather` over a prop to gather from; on Android the button has the same three words (`ui.touch_talk`, `ui.touch_stone`, `ui.touch_gather`). When more than one is near, the order is person, stone, prop |
| Keyboard, title screen | besides `W`/`S`, `E`, `D`, `X` and `I` (spec 12): `R` reincarnates the chosen game when it has reached level 10, after a second `R` (spec 11). On Android the row of such a game has a `Rebirth` button |
| Keyboard, talents | `Tab` in the crafting panel (`C`) switches between the recipes and the talents (spec 11); `W`/`S` choose, `E` learns a rank. On Android the panel has a button for it; a tap chooses a talent, a second tap learns |
| Keyboard, companion | `H`: the companion stays where it is, or follows again (spec 10, "Commands") |
| Keyboard, parry | `U`: the parry (spec 05, "Parry"); held, it opens a window whenever the wait is over |
| Keyboard, power strike | `K`: the power strike (spec 05, "Mana"), while there is mana; held, it repeats when the cooldown ends; with `J` held too, the strike wins |
| Keyboard, dodge | `L` or `Left Shift`: the dodge roll (spec 05), in the direction of the movement keys, or the way you face when none is held; held, it repeats when the cooldown ends |
| Keyboard, analyze | `Z`: Ren's Analyze, a panel for six seconds (again to hide it) |
| Keyboard, interact | `E` or `Enter`: talk to the person in front of you, wake and use a Threshold Stone, confirm |
| Dialogue | `W`/`S` or the arrows choose, `E`/`Enter`/`Space` or a mouse click confirm, `1` to `9` pick a choice directly |
| Bag | `I` opens and closes it; `W`/`S` move the cursor; `E`/`Enter`/`Space` use or wear the item; `Esc` closes it |
| Shop | opened by the dialogue with a shopkeeper; `W`/`S` move, `Tab` switches between buying and selling, `E`/`Enter` confirm, `Esc` closes |
| Guild board | opened by the dialogue with a guild clerk; `W`/`S` move, `E`/`Enter` accept the work, `Esc` closes |
| Threshold Stones | `E` next to a stone: wakes it and heals; the list of woken stones opens: `W`/`S` move, `E`/`Enter` travel, `Esc` closes |
| Journal | `Q` opens and closes it; `W`/`S` scroll |
| World map | `M` opens and closes it; open: `+`/`-` (or `=`) and the mouse wheel zoom, `W A S D` or the arrows and dragging with the left button move the view, `P` marks the goal at the center of the view (a right click at the pointer), `X` removes it, `Tab` jumps to the next place found, `Q` puts the goal on the place of the next quest in progress (spec 07, "Places"; the [Quest] button on Android), `C` goes back to the player, `0` or `Home` frames all that was explored (spec 09, "The map view") |
| Language | `F2` switches between Italian and English at any time |
| Saves | `F5` quick save, `F9` quick load, `F7` new game (a new world in the same game) |
| Small map | `N` shows or hides the small map in the corner |
| Debug | `F3` toggles the debug overlay |
| `Esc` | closes the open panel (map, bag, journal, shop, board, stones); with none open it saves the game and returns to the list of games; on the list it quits |
| Title screen | `W`/`S` or the arrows move, `E`/`Enter`/`Space`, the number keys `1` to `3` or a mouse click choose a game, `D` or `Delete` twice deletes the selected one |
| Gamepad | left stick moves; `A` (south) attacks and confirms; `X` (west) talks and confirms; `RB` (right shoulder) is the power strike; `LB` (left shoulder) is the parry; `B` (east) rolls out of the way in the game (and closes a panel); `Y` (north) switches buy/sell in a shop; `B` (east) closes a panel; the D-pad moves in lists and choices |

Several things share a key because they never happen together: `E` talks next to a person, wakes a stone next to a stone and uses the item in the bag.

## Android

| Device | Mapping |
|---|---|
| Touch, move | **Floating stick**: the first touch on the left half of the screen is the origin of the stick; dragging up to 64 dp from it gives the vector, scaled to length 1 at 64 dp |
| Touch, attack | any touch on the right half of the screen, except on a button or a panel |
| Parry | a button above the Strike button (`Parry`): held, it opens the parry window; a touch on it is never an attack; `U` on a keyboard |
| Strike | a button above the Dodge button (`Strike`): held, it uses the power strike while there is mana; a touch on it is never an attack; `K` on a keyboard |
| Dodge | a round button in the bottom right corner (`Dodge`): held, it rolls in the direction of the stick; a touch on it is never an attack; `L` or `Left Shift` on a keyboard |
| Analyze | a button left of the Dodge button: a tap shows the panel of Analyze for six seconds (again to hide it) |
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

## Status window

The journal opens with the **status** of the Guest: the protagonist and the last title earned (spec 11), level and experience, health and mana, attack, magic, defense and magic defense (spec 04, after equipment, talents and echoes),
the critical chance, the speed, what the titles add to the attack, the gold and the creatures defeated. Desktop: `V` opens the journal at it (as `Q` does); Android: the journal button. Presentation only.

## Configurable keys

Desktop: `<user data>/keys.json` (next to `settings.json`) is `{"keys": {"<action>": "<key>", ...}}` with the actions `up`, `down`, `left`, `right`, `attack`, `strike`, `dodge`, `parry`, `interact`, `bag`, `journal`, `map`,
`minimap`, `crafting`, `companion` and `analyze`. A key is named as SDL names it (`"F"`, `"Space"`, `"Left Ctrl"`, `"Keypad 5"`); an empty name, an unknown one or the default key changes nothing. The key named for an
action does what the default key of the action does, in the game, while it is held and when it is pressed; **the default keys keep working**. A key given to an action stops doing what it did before (so giving `E` to
`attack` leaves talking to `Enter`). The file is written the first time the game starts, with every action and an empty key, and read when the game starts. The **keys panel** (`F4` in a game) does the same from inside the game: `W`/`S` choose an action, `E` waits for a key and gives it to the action (`Esc` cancels; the default key or `Backspace` takes the choice away), `Esc` closes; the file is written at once. The game pauses meanwhile. Android uses touch; a physical keyboard there keeps the
default keys. Presentation only: nothing of it is in the simulation or in the vectors.

## Settings

The settings are kept in `<user data>/settings.json`: `{"language": "it", "volume_master_pm": 1000, "volume_effects_pm": 800, "volume_ambience_pm": 500, "volume_music_pm": 500}` (the volumes are permille from 0 to 1000; the numbers above are the defaults, used for what is missing). Spec 14 says what each volume scales: the master volume all of the sound, the others the sound effects, the ambience and the music. Desktop: `F10` opens a panel with four bars (`W`/`S` choose, `A`/`D` change by a tenth, `Esc` closes; the game pauses meanwhile). Android: the sound button next to the language button cycles the master volume 100, 60, 30 and 0 percent; the other three volumes can be set in the file. The language is kept in the same file as `{"language": "it"}` (desktop: next to the `saves` folder; Android: the app-private
folder). Without it the language of the system is used (`it` if it is Italian, else `en`). The language can be changed at any time: texts are resolved when they are drawn (spec 17).

## Orientation (Android)

The app allows portrait and landscape (`fullUser`) and handles configuration changes itself (no activity restart).
The camera adapts: the visible area in tiles is `screen_px / tile_px`, with `tile_px` derived from the screen density
(`tile_px = round(48 * density)`, bucketed).
