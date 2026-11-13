## People seen from the side, five quests

### Presentation (both clients, spec 13)
- A rig part may have `art_side`, `z_side` and `offset_side`; `evaluate_pose` takes `side` and hangs the parts from their side joints. Reference `pose.py`, six new `rig_pose` cases, desktop and Android.
- The player is drawn from the side when the last movement was mostly sideways, from behind when upward, from the front when downward.
- Art: `head_side`, `torso_side`, `cape_side` for the base figure and the fifteen variants (`tools/art_looks_side.py`); arms and legs are the front ones.

### Content
- Five quests at the outposts about the creatures and scenery of the last batches (268 quests), written in English and Italian.

### Checked
- `validate_data.py`, `ruff`, `pytest tools/tests`, `gen_conformance.py --check` locally; the side figures were looked at with `tools/art_preview.py --figures` (idle, walk, blow).
- Desktop and Android **not** built locally: CI is the build.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
