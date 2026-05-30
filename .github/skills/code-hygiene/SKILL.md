---
name: code-hygiene
description: How to structure code and files for modularity and LLM navigability. Use whenever creating, editing, or refactoring any code or organising any folder — splitting god-files, naming modules, designing directories, keeping files small and single-purpose.
---

# Code & repo hygiene

## Why (read this first)

You navigate a repo by grep / ls / cat and by reading an index, not by holding
the whole tree in your head — so the repo's structure IS your working memory.
Small, single-purpose files are **completely replaceable in one edit** (no
partial-edit errors, no "… rest the same"). A clear directory map lets you load
only relevant context instead of re-discovering the codebase each iteration.
Spaghetti files and flat mega-folders directly degrade your own future
performance. This is self-interest, not style.

## The rules

- **Size:** target ≤ ~200 lines/file; hard refactor trigger at ~300. Every file
  must be replaceable in a single edit.
- **One responsibility per file**, named so its purpose is obvious. New
  capability → new file; don't grow an existing one.
- **Directory fan-out:** more than ~8–10 sibling files → group into subdirs by
  concern. Shallow-but-organised beats deep-and-arbitrary; both beat a flat pile.
- **Separation of concerns & layering:** single responsibility per module,
  minimal coupling, no circular imports, lower layers don't import higher ones.
  Shared logic lives in one clearly-named shared module — never copy-pasted.
- **Maps first:** every major directory has a short `README.md`/`INDEX.md`. Update
  the directory map AND the root index in the same commit as a structure change.
- **Refactor-before-grow:** split FIRST when a file crosses the cap or mixes
  concerns, THEN add new code.

## Smells that mean "split NOW"

- File > 300 lines.
- You want to write "… rest remains the same" / "… etc" in an edit.
- A file imported by almost everything (a god-module).
- A function over ~40 lines doing several distinct things.
- A folder you have to scroll to read its file list.
- Mixed concerns in one file — e.g. parsing + network + formatting together.

## Splitting recipes

Break a god-file by **responsibility**, not arbitrarily:

- **Layer split:** separate `models` (data shapes) / `io` (read-write, network) /
  `logic` (pure computation) / `orchestration` (wiring it together) into modules.
- **Cohesion split:** extract a cluster of functions that always change together
  into their own file.
- **Config split:** pull constants, settings, and schemas out into a `config`/
  `constants` module so logic files stay focused.
- After splitting, add/refresh the directory's index and fix imports so the
  dependency flow stays one-directional.

## Naming

Descriptive, consistent, greppable; the filename states the single
responsibility. `pubmed_tool.py`, `vector_store.py`, `notes.py` — not
`utils.py`, `helpers.py`, `misc.py`.

## Directory design

Group by concern/feature, not by file type alone. Cap fan-out (~8–10), index per
directory, hierarchy over piles.

## Example — bad vs good

**Bad** — one dumping ground:

```
utils.py            # 900 lines: text munging + file IO + date parsing + HTTP
```

**Good** — a focused package, each file ≤ ~200 lines, one job:

```
utils/
  README.md         # what's in here and where to find it
  text.py           # string/text helpers only
  io.py             # file read/write only
  dates.py          # date parsing/formatting only
  http.py           # network calls only
```

## Applies to research too

The `research/` vault obeys the same rules: organise notes into subfolders by
thread/topic, keep an index per subfolder, link with `[[wikilinks]]`. Never let
it become a flat folder of hundreds of dated files.
