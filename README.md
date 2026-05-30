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
AGENT.md            operating constitution (fed to the agent each iteration)
config/config.yaml  provider/model/loop/compute settings
agents/             llm_client (unified tool-use loop), prompts
tools/              registry + file / pubmed / exec tools (auto-discovered)
memory/             vector_store (ChromaDB) + notes (Obsidian write_note)
agentic_loops/      iteration.py (one fresh pass) + ralph.sh (the loop)
orchestration/      design for the future parallel-orchestrator layer
research/           the Obsidian vault: SCOPE, index, open questions, notes
experiments/        _log.md — one line per iteration, including dead ends
simulations/ data/ scratch/   working artifacts
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

## Running

A single iteration (fresh context, orient -> act -> critic -> record):

```bash
python -m agentic_loops.iteration
```

The full loop (fresh process per pass, commits between):

```bash
MAX_ITERS=0 SLEEP=5 bash agentic_loops/ralph.sh
```

The human watches progress via the Obsidian vault (`research/`) and `git log`.

## Safety

- **In-silico only.** Modelling, simulation, literature synthesis, hypothesis
  generation. No wet-lab protocols, nothing physically hazardous, no medical
  advice, no "cure" claims. See `research/SCOPE.md` and `AGENT.md`.
- **`run_shell` is NOT sandboxed.** It executes arbitrary commands on the host
  with the agent's privileges. Isolate at the OS level (container / VM /
  dedicated machine / restricted user) before running an autonomous loop.
- Secrets live in `.env` (git-ignored). Never commit keys.
