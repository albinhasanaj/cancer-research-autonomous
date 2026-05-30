# scripts/ — repo maintenance utilities

Small, standalone maintenance scripts. Not agent tools (those live in `tools/`)
and not part of the research loop.

## Contents

- **`check_hygiene.py`** — advisory check for the hygiene rules in `AGENTS.md`:
  flags source files over the line cap, directories with too many sibling files,
  and major directories missing an index/README map.
  Run: `python scripts/check_hygiene.py` (report only) or
  `python scripts/check_hygiene.py --strict` (exit 1 on any violation).
