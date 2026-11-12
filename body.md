## Two fixes after looking at the screenshots of the anime art build

- Desktop: `wrap_text` measured lines by counting characters (the old font had a fixed width), so with the font of the pack the lines broke too early and the boxes were half empty. It now measures with `text_columns`.
- `grass_f` had a ring of mushrooms in each of its 16 tiles; now in about a third of them.

Checked: `validate_data.py`, `ruff`, tool tests and vectors locally (by `ship.py`); the C++ change is built by CI only.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
