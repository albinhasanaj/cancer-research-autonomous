"""Tool registry: @tool decorator + auto-discovery of the tools package.

No global mutable singletons beyond the registry dict, which is treated as
append-only per-process. Each Ralph iteration is a fresh process, so this is
safe for parallel workers (each has its own process/registry).
"""
import importlib
import pkgutil
from typing import Callable, Dict, Any

# name -> {"func": callable, "description": str, "schema": dict}
_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, schema: dict):
    """Register a function as an agent tool.

    schema is a JSON-schema object describing the function input. On the live
    Copilot path tools are called directly from the shell, so the schema is used
    for discovery/documentation (and by any future orchestration layer) rather
    than being pushed into a model's tool list.
    """
    def decorator(func: Callable):
        _REGISTRY[name] = {
            "func": func,
            "description": description,
            "schema": schema,
        }
        return func
    return decorator


def discover():
    """Import every submodule of the tools package so their @tool calls run.

    Skips this registry module and __init__. A newly written tool file is
    auto-picked-up on the next iteration (fresh process).
    """
    import tools as _pkg
    for mod in pkgutil.iter_modules(_pkg.__path__):
        if mod.name in ("registry", "__init__"):
            continue
        importlib.import_module(f"tools.{mod.name}")


def get(name: str):
    """Return the registry entry dict for a tool, or None."""
    return _REGISTRY.get(name)


def all_tools() -> Dict[str, Dict[str, Any]]:
    """Return the full registry dict."""
    return _REGISTRY


def names():
    """Return a sorted list of registered tool names."""
    return sorted(_REGISTRY.keys())
