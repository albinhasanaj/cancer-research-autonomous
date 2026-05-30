# blockers/ — human escalation queue

The agent is autonomy-first. It only writes here when it hits a **true human-only
blocker** (see `AGENTS.md` > Escalation). Difficulty, ambiguity, and dead ends are
NOT blockers — those get logged in `experiments/_log.md` and the agent moves on.

## How it works

- One file per blocker: `blockers/<id>-<slug>.md`, where `<id>` is a short stable
  token (e.g. `xai-key`, `private-portal-3`).
- The agent marks the affected item in `research/open_questions.md` as
  `[BLOCKED:<id>]`, then continues on a different unblocked question.
- The loop (`run_loop.sh`) notifies the human once per new blocker
  (non-blocking) and only **pauses** if `.all-blocked` exists at repo root —
  written by the agent when every remaining open question is blocked.
- Resolve with `scripts/resolve_blocker.sh <id>` (moves the file to `resolved/`,
  clears notification state, and removes `.all-blocked` if nothing is left open —
  which auto-resumes a paused loop).

## Blocker file format

```markdown
---
id: <id>
status: open
created: <ISO-8601 timestamp>
---

- **What's blocked** — which open question / task.
- **What the human must do** — precise, numbered steps. Be exact, e.g.
  "1. Create an X account at https://example.com  2. Generate an API key
   3. Paste it into `.env` as `FOO_API_KEY`".
- **Why you can't do it** — one line (the capability gap).
- **Resume hint** — what you'll do once unblocked.
```

Keep it short and actionable. No essays. `status` is `open` until a human
resolves it (then `resolved`, and the file lives under `resolved/`).
