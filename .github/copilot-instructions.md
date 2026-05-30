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
- **Tool policy.** Use your native file/shell abilities directly. Only write a
  new file in `tools/` when you hit a capability you genuinely lack (a new
  external API, a specialized simulation harness, a dataset fetcher). When you
  do, register it via `@tool` and write a skill documenting it.
- **Two knowledge stores, kept distinct.** `research/` = domain knowledge (the
  science). `.github/skills/` = operational knowledge (how to use a
  tool/API/library, environment quirks). Check `.github/skills/` before doing
  anything unfamiliar, and record new how-to learnings there.
- **Code & repo hygiene (always on).** Keep files ≤ ~200 lines (split before
  ~300), one responsibility per file, descriptive greppable names, no flat
  folders (group into subdirs past ~8–10 files), an index/README per major
  directory, refactor-before-grow. Applies to `research/` too. See `AGENTS.md`
  and `.github/skills/code-hygiene/SKILL.md`.
