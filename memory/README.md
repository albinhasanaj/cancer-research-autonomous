# memory/ — durable memory tools

Semantic recall and structured note-writing — capabilities the agent lacks
natively. Tools here register when imported (explicitly, by the iteration).

## Contents

- **`vector_store.py`** — ChromaDB persistent store; `reindex()` over
  `research/**/*.md` and the `memory_search` tool.
- **`notes.py`** — the `write_note` tool (dated Obsidian notes with YAML
  frontmatter + `[[wikilinks]]`, routed to `research/{hypotheses,findings,literature}`).
