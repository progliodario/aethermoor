# 16. Input

Status: **v1 (M2 subset)**.

## Abstract actions

The simulation never sees devices, only a movement vector in `[-1, 1]^2` (screen axes, y down) that is passed through
`normalize_input` (see `02-entities-and-movement.md`). More actions (attack, skills, dodge, interact...) are added with
combat in M3.

## Devices

| Device | M2 mapping |
|---|---|
| Keyboard | `W A S D` and arrow keys; `Esc` quits (desktop); `F3` toggles the debug overlay |
| Gamepad | Left stick (SDL gamepad on desktop). Android controller support arrives later |
| Touch (Android) | **Floating stick**: the first touch on the left half of the screen is the stick origin; dragging up to 64 dp from the origin gives the vector, scaled to length 1 at 64 dp |

The last used device decides which hints are shown (later milestones).

## Orientation (Android)

The app allows portrait and landscape (`fullUser`) and handles configuration changes itself (no activity restart).
The camera adapts: the visible area in tiles is `screen_px / tile_px`, with `tile_px` derived from the screen density
(`tile_px = round(48 * density)`, bucketed).
