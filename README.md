# Autonomous Research Agent (Ralph-loop harness)

A harness for a coding agent to do **sustained, self-directed, in-silico**
computational / literature research on a hard open domain (cancer biology,
modelling and simulation only). This repository is the *base*: the agent's tools,
memory, and operating rules. A separate "Ralph prompt" starts the actual research
loop — **this repo does not start any loop on its own.**

## The one principle

A long single agent session **rots**: its context window fills, compacts lossily,
and drifts. The Ralph pattern fixes this by making **each iteration a fresh
process with a clean context window**. Nothing persists in-context between
iterations. ALL memory lives on disk:

- **files** (`research/`, `experiments/`) — working state
- **git history** — episodic memory (the loop commits every pass)
- **vector store** (`memory/.chroma`) — semantic recall over notes
- **Obsidian graph** — `research/` is a navigable vault for the human

## Layout

```
AGENTS.md            operating constitution (auto-loaded each iteration)
.github/             copilot-instructions.md + skills/ (operational how-to memory)
config/config.yaml   provider/model/loop/compute settings
tools/               registry (@tool) + data/lit/meta tools — only genuine capabilities
memory/              vector_store (ChromaDB) + notes (Obsidian write_note)
orchestration/       design for the future parallel-orchestrator layer
scripts/             repo maintenance utilities (e.g. hygiene_check.py)
research/            the Obsidian vault: SCOPE, index, open questions, notes
experiments/         _log.md — one line per iteration, including dead ends
simulations/ data/ scratch/   working artifacts
```

Every major directory carries its own `README.md` map. Run
`python scripts/hygiene_check.py` to flag oversized files, flat-dump
directories, or missing maps (see `AGENTS.md` > Code & repo hygiene).

## Execution model

The execution model is **Copilot CLI driving the loop** directly: it uses its
native file/shell/web abilities and the genuine-capability tools (`pubmed_*`,
`memory_search`, `write_note`, the data tools in `tools/`). The constitution is
`AGENTS.md` (auto-loaded), and operational how-to knowledge lives in
`.github/skills/`. Tools are plain Python invoked from the shell
(`python -c "from tools.X import f; print(f(...))"`) — **not** MCP and **not**
pre-loaded schemas, so each capability costs context only when actually used. See
the `capability-catalog` skill for the full map.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY and/or XAI_API_KEY (+ optional NCBI_API_KEY)
```

## Running

The full loop (fresh Copilot process per pass, commits between):

```bash
MAX_ITERS=0 SLEEP=5 bash run_loop.sh
```

One iteration is `copilot --prompt "Read AGENTS.md and do exactly one iteration…"`
spawned with a clean context window. The human watches progress via the Obsidian
vault (`research/`) and `git log`.

## Safety

- **In-silico only.** Modelling, simulation, literature synthesis, hypothesis
  generation. No wet-lab protocols, nothing physically hazardous, no medical
  advice, no "cure" claims. See `research/SCOPE.md` and `AGENTS.md`.
- **Shell execution is NOT sandboxed.** The agent runs arbitrary commands on the
  host with its own privileges via its native shell. Isolate at the OS level
  (container / VM / dedicated machine / restricted user) before running an
  autonomous loop.
- Secrets live in `.env` (git-ignored). Never commit keys.
