"""FALLBACK PATH (raw-API backend). One fresh-context Ralph iteration.

This is the optional raw-API backend, used ONLY when the loop is driven by a
provider API directly instead of by Copilot CLI as the brain. The primary
execution model is Copilot CLI driving the loop. Because this path has no native
file/shell abilities, it registers the primitive tools bundled in this package
(primitive_tools_file / primitive_tools_exec).

Run as:  python -m api_backend.iteration

Nothing persists in-context between iterations; all state is on disk. This module
sets AGENT_ROOT, loads config, registers tools, reindexes the vector store, then
runs a researcher turn followed by a critic turn.
"""
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read(root: Path, rel: str, limit: int = 6000) -> str:
    p = root / rel
    if not p.exists():
        return f"(missing: {rel})"
    text = p.read_text(encoding="utf-8", errors="replace")
    return text[:limit]


def _load_config(root: Path):
    import yaml
    from api_backend.llm_client import LLMConfig
    cfg_path = root / "config" / "config.yaml"
    data = {}
    if cfg_path.exists():
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    prov = data.get("provider", {})
    loop = data.get("loop", {})
    return LLMConfig(
        provider=prov.get("name", "anthropic"),
        model=prov.get("model", "claude-opus-4-8"),
        max_tokens=prov.get("max_tokens", 4096),
        temperature=prov.get("temperature", 1.0),
        max_tool_steps=loop.get("max_tool_steps", 25),
    )


def main():
    root = _repo_root()
    os.environ["AGENT_ROOT"] = str(root)
    sys.path.insert(0, str(root))

    from tools import registry
    from api_backend.llm_client import run_agent
    from api_backend import prompts

    # Register tools: auto-discover the genuine-capability tools package, then
    # explicitly import the memory tools so their @tool decorators run. This
    # fallback path also registers the primitive file/shell tools, since (unlike
    # Copilot CLI) a raw provider API has no native file/shell abilities.
    registry.discover()
    import api_backend.primitive_tools_file  # noqa: F401 (registers file ops)
    import api_backend.primitive_tools_exec  # noqa: F401 (registers run_python/run_shell)
    import memory.notes  # noqa: F401  (registers write_note)
    import memory.vector_store as vector_store  # registers memory_search

    tool_names = registry.names()
    print(f"[iteration] registered tools: {', '.join(tool_names)}")

    # Refresh semantic memory over the vault.
    try:
        n = vector_store.reindex()
        print(f"[iteration] reindexed {n} chunks")
    except Exception as e:
        print(f"[iteration] reindex failed (continuing): {e}")

    cfg = _load_config(root)
    print(f"[iteration] provider={cfg.provider} model={cfg.model}")

    agent_md = _read(root, "AGENTS.md")
    scope = _read(root, "research/SCOPE.md")
    index = _read(root, "research/00_index.md")
    open_q = _read(root, "research/open_questions.md")
    log = _read(root, "experiments/_log.md", limit=3000)

    def on_event(kind, payload):
        if kind == "tool_use":
            print(f"  -> tool {payload['name']}({payload['input']})")
        elif kind == "text":
            print(f"  [model] {payload[:500]}")

    # --- Researcher turn ---
    cfg.system = prompts.RESEARCHER
    researcher_prompt = (
        "=== AGENTS.md (constitution) ===\n" + agent_md +
        "\n\n=== research/SCOPE.md ===\n" + scope +
        "\n\n=== research/00_index.md ===\n" + index +
        "\n\n=== research/open_questions.md ===\n" + open_q +
        "\n\n=== experiments/_log.md (recent) ===\n" + log +
        "\n\nProceed with ONE iteration now."
    )
    print("\n[iteration] === RESEARCHER TURN ===")
    researcher_out = run_agent(researcher_prompt, tool_names, cfg, on_event)
    print("\n[iteration] researcher output:\n" + (researcher_out or "(none)"))

    # --- Critic turn ---
    cfg.system = prompts.CRITIC
    critic_prompt = (
        "Review the newest notes under research/findings/ and research/hypotheses/. "
        "Use list_dir and read_file to find them, deliver a verdict for each "
        "(KEEP/DEMOTE/REJECT), update note status, and append your verdict(s) to "
        "experiments/_log.md."
    )
    print("\n[iteration] === CRITIC TURN ===")
    critic_out = run_agent(critic_prompt, tool_names, cfg, on_event)
    print("\n[iteration] critic output:\n" + (critic_out or "(none)"))

    print("\n[iteration] done.")


if __name__ == "__main__":
    main()
