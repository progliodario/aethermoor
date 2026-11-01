---
description: Validate data, schemas, localization and tool tests
---

Run the project validation and report the result honestly:

1. `python tools/validate_data.py`
2. `python -m pytest -q tools/tests`
3. `python -m ruff check tools`

Use `.venv/Scripts/python` on Windows if the virtual environment exists. If something fails, show the exact failing lines, explain the cause, and fix it (or ask if the fix is a design decision). Do not claim success without running the commands.
