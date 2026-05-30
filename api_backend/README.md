# api_backend/ — FALLBACK raw-API loop (NOT the primary path)

The primary execution model is **Copilot CLI driving the loop** using its native
abilities. This package is the optional fallback used only when running the loop
via a raw provider API (OpenAI/xAI) instead of Copilot. Because a raw API has no
native file/shell abilities, this path bundles its own primitive tools.

## Contents

- **`llm_client.py`** — unified provider tool-use loop (`run_agent`, `LLMConfig`).
- **`prompts.py`** — RESEARCHER / CRITIC / PLANNER system prompts.
- **`iteration.py`** — one fresh-context iteration (`python -m api_backend.iteration`).
- **`ralph.sh`** — the loop: fresh process per pass, git commit between.
- **`primitive_tools_file.py`** — file ops (read/write/append/list_dir/grep).
- **`primitive_tools_exec.py`** — `run_python` / `run_shell`.
