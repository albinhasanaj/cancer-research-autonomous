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
tools/               registry (@tool) + pubmed tool — only genuine capabilities
memory/              vector_store (ChromaDB) + notes (Obsidian write_note)
api_backend/         FALLBACK raw-API loop (llm_client, prompts, iteration,
                     ralph.sh, primitive file/shell tools) — used only without Copilot
orchestration/       design for the future parallel-orchestrator layer
research/            the Obsidian vault: SCOPE, index, open questions, notes
experiments/         _log.md — one line per iteration, including dead ends
simulations/ data/ scratch/   working artifacts
```

## Execution model

The **primary** execution model is **Copilot CLI driving the loop** directly: it
uses its native file/shell abilities and the genuine-capability tools (`pubmed_*`,
`memory_search`, `write_note`). The constitution is `AGENTS.md` (auto-loaded), and
operational how-to knowledge lives in `.github/skills/`.

`api_backend/` is an **optional fallback** that drives the same loop via a raw
provider API (Anthropic/OpenAI) — only needed when running without Copilot as the
brain. That path bundles its own primitive file/shell tools.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

## Running (fallback raw-API path)

A single iteration (fresh context, orient -> act -> critic -> record):

```bash
python -m api_backend.iteration
```

The full loop (fresh process per pass, commits between):

```bash
MAX_ITERS=0 SLEEP=5 bash api_backend/ralph.sh
```

The human watches progress via the Obsidian vault (`research/`) and `git log`.

## Safety

- **In-silico only.** Modelling, simulation, literature synthesis, hypothesis
  generation. No wet-lab protocols, nothing physically hazardous, no medical
  advice, no "cure" claims. See `research/SCOPE.md` and `AGENTS.md`.
- **Shell execution is NOT sandboxed.** The agent runs arbitrary commands on the
  host with its own privileges (native shell, or `run_shell` in the fallback
  path). Isolate at the OS level (container / VM / dedicated machine / restricted
  user) before running an autonomous loop.
- Secrets live in `.env` (git-ignored). Never commit keys.
