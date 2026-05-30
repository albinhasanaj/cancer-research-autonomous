# Orchestration layer — NOT YET IMPLEMENTED

This directory documents the **intended** layer that will run MANY research
agents in parallel on top of the single-agent harness in this repo. It is a
design note, not working code. Do not assume any of it exists yet.

## Why this works (the proven pattern)

Parallel agentic systems that scale (Copilot `/fleet`, Steve Yegge's "Gas Town",
Claude Code agent teams) all share one shape:

> **orchestrator decomposes work → ephemeral workers with isolated context
> windows → shared filesystem + git → orchestrator is the only coordination
> layer → durable external memory, disposable context.**

This is the same principle the single-agent Ralph loop rests on, lifted one
level: context is disposable, memory is external and on disk.

## Intended components

### Director ("Mayor")
Reads `research/open_questions.md`, selects N independent items, and dispatches N
workers — one question each. It is the **only** coordination point. It does not
do research itself; it decomposes and assigns.

### Workers (ephemeral)
Each worker is exactly the existing single-agent iteration, but run in its **own
git worktree / branch** so writes never collide:

```
git worktree add ../worker-<id> -b worker/<id>
# worker runs a fresh `copilot` iteration against its worktree, e.g.
#   cd ../worker-<id> && copilot --prompt "Read AGENTS.md and do exactly one
#   iteration of the protocol, then exit." --allow-all --no-color --disable-builtin-mcps
```

A worker **claims** an item by checking its box in `open_questions.md` and
tagging it with its worker id, e.g.:

```
- [x] (worker-3) Build a clonal-evolution Monte Carlo of time-to-malignancy
```

Because items are kept independent, two workers can run at once without
stepping on each other.

### Refinery (merge + critic)
After workers finish, a consolidation step runs the **critic** pass on each
worker's surviving notes, resolves merge conflicts, and integrates the kept
findings back into `main` and the Obsidian knowledge graph. Rejected work is
logged (in `experiments/_log.md`) so it is not retried.

### Human
Watches the whole thing via the Obsidian vault (`research/`) and `git log`. No
dashboard required — the filesystem and git history *are* the dashboard.

## Constraints honoured by the current base (so this stays possible)

- **No global mutable singletons** and **no assumption of a single writer** in
  the tools/memory code — every worker is its own process with its own
  `AGENT_ROOT`.
- Work units in `open_questions.md` are kept **independent** where possible so
  separate workers can claim different items without colliding.
- All state is on disk + git, so a worktree-per-worker model "just works".

## Status

**NOT YET IMPLEMENTED.** Build the Director / Refinery here later. The
single-agent base in the parent repo is complete and runnable on its own.
