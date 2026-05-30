# tools/ — genuine-capability agent tools

Only capabilities Copilot does NOT have natively belong here. File/shell ops are
native — don't wrap them. Each tool registers via the `@tool` decorator and is
auto-discovered (`registry.discover()`).

## Contents

- **`registry.py`** — `@tool` decorator, `discover()` auto-import, `get()`/`names()`.
- **`pubmed_tool.py`** — `pubmed_search` / `pubmed_fetch` via NCBI E-utilities.

Memory tools (`memory_search`, `write_note`) live in `memory/` and register when
imported. To add a tool: new file here + `@tool` + a skill documenting it.
