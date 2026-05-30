# Copilot instructions — autonomous in-silico research agent

This repo is a **Ralph-loop harness** for an autonomous agent doing sustained,
self-directed **in-silico** computational / literature research in cancer biology
(modelling, simulation, literature synthesis, hypothesis generation only).

## Always-true norms

- **Scope is in-silico only.** No wet-lab protocols, nothing physically
  hazardous, no medical advice, no "cure/solved/breakthrough" claims. See
  `research/SCOPE.md`.
- **Read `AGENTS.md` for the full operating protocol** — the iteration loop
  (one small verifiable unit of work per pass), the honesty rules, and
  self-extension rules. It is the constitution.
- **Triage the frontier before computing.** Don't default to simulating. First
  search (native web search/fetch + PubMed, and a provider research mode when
  warranted) to decide if the question is already ANSWERED / EXTENDABLE / OPEN —
  only OPEN questions justify a fresh simulation. You have a wide capability
  surface (native search/file/shell, budgeted OpenAI + xAI keys incl. their
  research modes, and tools/workflows you can build); pick the best instrument.
  See `.github/skills/research-strategy/SKILL.md`.
- **Tool policy.** Use your native file/shell/search abilities directly. Only
  write a new file in `tools/` (or build an agentic workflow) when you hit a
  genuine external capability gap or a high-reuse instrument — never to wrap
  something native. When you do, register it via `@tool` and write a skill.
- **Two knowledge stores, kept distinct.** `research/` = domain knowledge (the
  science). `.github/skills/` = operational knowledge (how to use a
  tool/API/library, environment quirks). Check `.github/skills/` before doing
  anything unfamiliar, and record new how-to learnings there.
- **Code & repo hygiene (always on).** Keep files ≤ ~200 lines (split before
  ~300), one responsibility per file, descriptive greppable names, no flat
  folders (group into subdirs past ~8–10 files), an index/README per major
  directory, refactor-before-grow. Applies to `research/` too. See `AGENTS.md`
  and `.github/skills/code-hygiene/SKILL.md`.
