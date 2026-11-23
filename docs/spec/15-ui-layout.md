# 15. UI layout and the "System window" theme

Status: **v1 (written from the two clients as they are, B1.2 of the operating program)**. Presentation only: nothing of it is in the
simulation, the saves or the conformance vectors. The screens are written in the code of each client (ADR 0014; the declarative UI of
ADR 0008 is deferred): `desktop/src/app/main.cpp` and `android/game/.../AethermoorGame.kt`. The desktop frames are checked in CI
(spec 16, "Checks of the frames"); the owner checks both clients by playing. The input of every panel (keys, mouse, touch) is in spec 16.

## Units

- **Density** `d`: 1 on a desktop window of 1280 x 720 (the size of the window at start, `kWindowWidth` and `kWindowHeight`), the
  display density of the device on Android (`Gdx.graphics.density`). Every size below is in points: multiply by `d` for pixels.
- **Text.** Desktop draws the font of the pack (spec 13) on a grid of 8 x 8 units, at scale 2 in the panels (16 pixels a character,
  22 a line) and at scale 1 for the small lines of the HUD; the option `large_text` makes it a quarter larger (spec 16,
  "Accessibility"). Android bakes the font of the pack into a bitmap font at the density of the device (three tenths larger with
  `large_text`); a line is `font.lineHeight`.
- **Wrapping.** A text longer than its panel is wrapped at spaces by the number of characters that fit (desktop: the width of the panel
  less its margins, divided by 16; Android: measured with the font). No text is cut.

## The "System window" theme

Every panel is the same piece of glass, the "system window" an isekai hero sees: night-violet, with a thread of an accent colour
around it. In this order, for a panel at `(x, y)` of size `w x h` with accent `A`:

1. a soft shadow: three veils of `#060414` at alpha 34, each 2 points wider than the last, 4 points lower;
2. a frame of `#0A081A` 3 points outside the panel, then a thread of `A * 0.75` 2 points outside, then `#100D26` 1 point outside;
3. the glass: horizontal strips of 3 points from `#282456` at the top to `#0D0C24` at the bottom, at the alpha of the panel;
4. a sheen of white at alpha 12 over the upper `min(0.35 h, 28)` points, a line of white at alpha 54 at the top and of black at alpha 70
   at the bottom;
5. a bracket of `A` at alpha 230 in every corner, 3 points inside, with arms of `min(10, min(w, h) / 3)` points.

The **accents**: cyan `#6FE3FF` for what the world says (the dialogue, the quest board, the Threshold Stones, the bag and its notice,
the Analyze of Ren), gold `#FFD778` for what the player handles (the shop and the chests, the craft, the journal, the keys and the
settings), sky `#8CDCFF` for the hints. The **row under the cursor** of a list is a bar of `#285A8C` (desktop `40, 90, 140`) behind it.
The texts: white `#EBF5FF` for the body, gold `#FFD778` for headings, prices and gold, `#AAC8E6` for the line of keys at the bottom of
a panel, orange for the status effects of the player.

**Bars** (health, mana, experience, the guardian): a frame of `#0A081A`, a rim of `#7870AA`, a well of `#120F28`, then the fill, light
at the top and deep at the bottom (its colour plus 70, down to its colour less 55), with a gloss line and a bright end.

## Where things are

- **HUD**, top left, 12 points from the corner: the health bar (220 x 16, red), the mana bar under it (7 high, blue), the experience bar
  (6 high, green), then the level, the keys of the bag and of the map, and the status effects. Right of the bars, squares of 15 points
  for the abilities that wait (the roll `L`, the power strike `K`, the Eternal Aegis `A`): lit when ready, filling while they wait.
- **Top right:** the clock and the region, then the gold and the rank of the guild, the coordinates and the goal, then the quests
  tracked with the place each sends to (desktop: a column 410 points from the right edge).
- **Top centre:** the bar of a guardian within ten tiles (spec 05, "Guardians"), and Analyze for a few seconds.
- **Bottom:** the dialogue, as wide as the screen less 24 points on each side, as high as its lines; the hint (at most 760 points wide),
  70 points above the bottom; on Android the touch controls (spec 16, "Touch").
- **Centre:** the shop and the chests, the board, the stones, the craft, the journal, the settings and the keys: centred, at most 560
  points wide (and the width of the screen less 40), as high as their rows; a list longer than the screen scrolls with the cursor, which
  stays near the middle (`first = clamp(cursor - rows / 2, 0, total - rows)`).
- **Corner:** the mini map (spec 09, "The map view"); the world map covers the screen.

While a panel or a dialogue is open the game is paused (spec 06, spec 07), and the HUD stays under it.

## Known differences

The two clients agree on the theme, the accents and the places above. They differ, on purpose or not yet, in:

- the width of the shop: 560 points on desktop, 460 on Android, where the buy and sell tabs are two buttons at the top of the panel
  (desktop writes the side in the title and switches it with `A`/`D`);
- the touch screen: Android has buttons for the actions (spec 16), which desktop does not draw;
- a few small panels of Android (the board, the world map, the title screen) draw plain rectangles of the theme's colours instead of the
  full glass.

A change to the look of a panel changes both clients in the same pull request, or says here which of them waits.
