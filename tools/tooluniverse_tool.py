"""ToolUniverse meta-finder — 1000+ scientific tools behind ONE shell surface.

ToolUniverse (mims-harvard) integrates 1000+ ML models, datasets, APIs and
scientific packages under a standardized protocol. Rather than wrap each as its
own agent tool (which would bloat context), we expose ToolUniverse's own
find -> inspect -> call discovery loop at the shell. This is the dynamic-loading
pattern: the agent searches for a capability, reads just that tool's schema, and
calls it — paying context only for what it uses.

Heavy optional dependency. Install on demand:  pip install tooluniverse
If it is not installed, every function returns a friendly install hint instead
of crashing the iteration.

Shell usage (see the tooluniverse skill):
  python -c "from tools.tooluniverse_tool import tu_find; print(tu_find('mhc binding affinity'))"
  python -c "from tools.tooluniverse_tool import tu_spec; print(tu_spec('UniProt_get_function_by_accession'))"
  python -c "from tools.tooluniverse_tool import tu_call; print(tu_call('UniProt_get_function_by_accession', '{\"accession\":\"P05067\"}'))"
"""
import json

from tools.registry import tool

_TRUNC = 18_000
_TU = None  # cached ToolUniverse instance (per-process; each iteration is fresh)

_INSTALL_HINT = (
    "ToolUniverse not installed. It is an optional heavy dependency providing "
    "1000+ scientific tools. Install on demand with:  pip install tooluniverse"
)


def _get_tu():
    """Lazily construct and cache a ToolUniverse with all tools loaded.

    Import is deferred so the tools package still loads when tooluniverse is
    absent. Returns None if the package is not installed.
    """
    global _TU
    if _TU is not None:
        return _TU
    try:
        from tooluniverse import ToolUniverse
    except Exception:
        return None
    tu = ToolUniverse()
    tu.load_tools()
    _TU = tu
    return _TU


@tool(
    "tu_find",
    (
        "Search ToolUniverse's 1000+ scientific tools by keyword (no API key / GPU "
        "needed) — the discovery step before calling one. Returns matching tool "
        "names + one-line descriptions. Use to find a capability this repo lacks "
        "(e.g. UniProt, ChEMBL, FAERS, PubTator, docking) without pre-loading schemas."
    ),
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Capability keywords, e.g. 'mhc binding affinity' or 'adverse event drug'"},
            "limit": {"type": "integer", "description": "Max tools to return (default 8)"},
        },
        "required": ["query"],
    },
)
def tu_find(query: str, limit: int = 8) -> str:
    tu = _get_tu()
    if tu is None:
        return _INSTALL_HINT
    try:
        res = tu.run({
            "name": "Tool_Finder_Keyword",
            "arguments": {"description": query, "limit": limit},
        })
        return (res if isinstance(res, str) else json.dumps(res, indent=2))[:_TRUNC]
    except Exception as e:
        return f"ERROR tu_find: {e}"


@tool(
    "tu_spec",
    (
        "Fetch the full input schema (OpenAI function format) for ONE ToolUniverse "
        "tool by exact name — the inspect step after tu_find, before tu_call. "
        "Pay context only for the tool you actually intend to use."
    ),
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Exact ToolUniverse tool name from tu_find"},
        },
        "required": ["name"],
    },
)
def tu_spec(name: str) -> str:
    tu = _get_tu()
    if tu is None:
        return _INSTALL_HINT
    try:
        spec = tu.tool_specification(name, format="openai")
        return json.dumps(spec, indent=2)[:_TRUNC]
    except Exception as e:
        return f"ERROR tu_spec: {e}"


@tool(
    "tu_call",
    (
        "Execute ONE ToolUniverse tool by exact name with a JSON arguments string — "
        "the call step after tu_find/tu_spec. Gives access to UniProt, ChEMBL, "
        "Open Targets, FAERS, PubTator and 1000+ others through a single surface."
    ),
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Exact ToolUniverse tool name"},
            "arguments_json": {"type": "string", "description": "JSON object of arguments, e.g. '{\"accession\":\"P05067\"}'"},
        },
        "required": ["name", "arguments_json"],
    },
)
def tu_call(name: str, arguments_json: str = "{}") -> str:
    tu = _get_tu()
    if tu is None:
        return _INSTALL_HINT
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as e:
        return f"ERROR tu_call: arguments_json is not valid JSON: {e}"
    try:
        res = tu.run({"name": name, "arguments": args})
        return (res if isinstance(res, str) else json.dumps(res, indent=2))[:_TRUNC]
    except Exception as e:
        return f"ERROR tu_call: {e}"


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "protein function"
    print(tu_find(q))
