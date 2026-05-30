# scripts/ — repo maintenance utilities

Small, standalone maintenance scripts. Not agent tools (those live in `tools/`)
and not part of the research loop.

## Contents

- **`hygiene_check.py`** — advisory check for the hygiene rules in `AGENTS.md`:
  flags source files over the line cap, directories with too many sibling files,
  and major directories missing an index/README map.
  Run: `python scripts/hygiene_check.py` (report only) or
  `python scripts/hygiene_check.py --strict` (exit 1 on any violation).
- **`notify.sh "<message>"`** — alert the human about an escalation. Always prints
  a console banner and appends to `NEEDS_HUMAN.log`; also POSTs to `$NOTIFY_WEBHOOK`
  (Discord/Slack) and fires a desktop notification if available. Never fails the loop.
- **`resolve_blocker.sh <id>`** — human convenience: marks a blocker resolved,
  moves it to `blockers/resolved/`, clears its `.notified` entry, and removes
  `.all-blocked` if no open blockers remain (auto-resuming a paused loop).
