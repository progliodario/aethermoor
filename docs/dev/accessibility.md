# Accessibility

The checklist of what the game does for players who see, hear or move differently (M10, item E1.3 of the
[operating program](../plan/07-programma-operativo.md)). Each item says where the rule is and whether it is done. What can be tested
is tested: the contrast of the texts by `tools/tests/test_accessibility.py`, the translations by `tools/check_translations.py`.

## Checklist

| Item | State | Where |
|---|---|---|
| Every text of the interface reaches a contrast of 4.5:1 on its panel (WCAG AA) | done, tested | the table below; colors of [spec 15](../spec/15-ui-layout.md) |
| No meaning by color alone: what can be made and what cannot also differ in lightness | done, tested | the table below (the rows of the crafting panel) |
| Larger text | done: `large_text`, a quarter larger on desktop, three tenths on Android | [spec 16](../spec/16-input.md), "Accessibility" |
| The red flash of a creature that is hit can be turned off | done: `flashes` | spec 16, "Accessibility" |
| The numbers that rise from a hit can be turned off | done: `damage_numbers` | spec 16, "Accessibility" |
| The hints of the first minutes can be turned off | done: `hints` | spec 16, "Hints" |
| Every key of the desktop can be changed | done: `F4` | spec 16, "Configurable keys" |
| The touch controls can be moved and resized | done: the editor of the layout, from the journal (Dodge, Strike, Parry, Analyze) | [spec 16](../spec/16-input.md), "The layout of the buttons" |
| A controller on Android | done: the buttons of the gamepad of the desktop | spec 16, "Android" (the row Controller) |
| Play with one hand on a phone | in part: the action buttons can be moved anywhere (E2.1); the stick still takes the left half of the screen | the program |
| No voice is needed: every line of the dialogues is written | done | [spec 07](../spec/07-quests-and-dialogue.md) |
| Sounds have their own volumes, and music and ambience are off | done | spec 16, "Settings"; [spec 14](../spec/14-audio.md) |
| No timed input in the dialogues: a line waits for the player | done | spec 07 |
| Fights are easy on purpose: no reflex test is needed to go on | done | `CLAUDE.md`, "Fights must be too easy" |
| Two languages, with the terms of the game kept the same in both | done, tested | [the glossary](../glossary.md); `tools/check_translations.py` |

## Contrast

The ratios are those of WCAG 2.1 (relative luminance of sRGB). `tools/tests/test_accessibility.py` reads this table and fails when a
pair falls below its minimum: 4.5 for the text of the panels, 2 for two colors that tell two states apart by lightness alone.

| Foreground | Background | What | Minimum |
|---|---|---|---|
| `#EBF5FF` | `#282456` | the body of a panel, on the top of its glass | 4.5 |
| `#EBF5FF` | `#0D0C24` | the body of a panel, on the bottom of its glass | 4.5 |
| `#FFD778` | `#282456` | headings, prices and gold | 4.5 |
| `#AAC8E6` | `#282456` | the line of the keys at the bottom of a panel | 4.5 |
| `#6FE3FF` | `#282456` | the cyan accent: what the world says | 4.5 |
| `#8CDCFF` | `#282456` | the hints | 4.5 |
| `#EBF5FF` | `#285A8C` | the row under the cursor of a list | 4.5 |
| `#96FFAA` | `#285A8C` | a recipe that can be made, under the cursor | 4.5 |
| `#AA9696` | `#282456` | a recipe that cannot be made | 4.5 |
| `#96FFAA` | `#AA9696` | can be made, against cannot: told apart by lightness | 2 |
