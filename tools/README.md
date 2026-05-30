# tools/ — genuine-capability agent tools

Only capabilities Copilot does NOT have natively belong here. File/shell ops are
native — don't wrap them. Each tool registers via the `@tool` decorator and is
auto-discovered (`registry.discover()`).

## Contents

- **`registry.py`** — `@tool` decorator, `discover()` auto-import, `get()`/`names()`.
- **`pubmed_tool.py`** — `pubmed_search` / `pubmed_fetch` via NCBI E-utilities.
- **`cbioportal_tool.py`** — tumour genomics (studies, gene mutations, clinical).
- **`depmap_tool.py`** — CRISPR Chronos gene-effect dependencies.
- **`gdc_tool.py`** — GDC/TCGA somatic mutations and cohort sizes.
- **`geo_tool.py`** — GEO expression-dataset discovery.
- **`opentargets_tool.py`** — Open Targets target–disease associations & tractability.
- **`clinicaltrials_tool.py`** — ClinicalTrials.gov v2 ("tried in humans?" triage).
- **`pubtator_tool.py`** — `pubtator_entity` / `pubtator_annotate`: normalize names to
  concept IDs and turn PMID abstracts into graph-linkable entities + relations.
- **`tooluniverse_tool.py`** — `tu_find`/`tu_spec`/`tu_call`: find→inspect→call over
  ToolUniverse's 1000+ tools (optional `pip install tooluniverse`; lazy-imported).

Run a tool directly for a smoke test with `python -m tools.<module> <fn> <arg>`
(the `@tool` imports need package context — plain `python tools/x.py` will fail).

Memory tools (`memory_search`, `write_note`) live in `memory/` and register when
imported. To add a tool: new file here + `@tool` + a skill documenting it. The
discovery layer for all external capabilities is
`.github/skills/capability-catalog/SKILL.md`.
