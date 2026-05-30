"""File tools, all path-scoped to the repo root.

AGENT_ROOT env var (set by iteration.py) defines the root; defaults to the
current working directory. Any path that resolves outside the root is rejected.
"""
import os
import glob as _glob
from pathlib import Path

from tools.registry import tool


def _root() -> Path:
    return Path(os.environ.get("AGENT_ROOT", os.getcwd())).resolve()


def _resolve(path: str) -> Path:
    """Resolve a path against the repo root and reject escapes."""
    root = _root()
    p = (root / path).resolve() if not os.path.isabs(path) else Path(path).resolve()
    if root != p and root not in p.parents:
        raise ValueError(f"path escapes repo root: {path}")
    return p


@tool(
    "read_file",
    "Read a UTF-8 text file (path relative to repo root). Returns its contents.",
    {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Path relative to repo root"}},
        "required": ["path"],
    },
)
def read_file(path: str) -> str:
    p = _resolve(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    return p.read_text(encoding="utf-8", errors="replace")


@tool(
    "write_file",
    "Write (overwrite) a UTF-8 text file at path (relative to repo root). Creates parent dirs.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)
def write_file(path: str, content: str) -> str:
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} chars to {path}"


@tool(
    "append_file",
    "Append text to a UTF-8 file at path (relative to repo root). Creates it if missing.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)
def append_file(path: str, content: str) -> str:
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(content)
    return f"appended {len(content)} chars to {path}"


@tool(
    "list_dir",
    "List entries in a directory (path relative to repo root).",
    {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Dir relative to repo root; default '.'"}},
        "required": [],
    },
)
def list_dir(path: str = ".") -> str:
    p = _resolve(path)
    if not p.is_dir():
        return f"ERROR: not a directory: {path}"
    entries = []
    for child in sorted(p.iterdir()):
        kind = "d" if child.is_dir() else "f"
        entries.append(f"{kind} {child.name}")
    return "\n".join(entries) if entries else "(empty)"


@tool(
    "grep",
    "Search files matching a glob for a substring. Returns matching lines (capped at 200).",
    {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Substring to search for"},
            "glob": {"type": "string", "description": "Glob relative to repo root, e.g. 'research/**/*.md'"},
        },
        "required": ["pattern", "glob"],
    },
)
def grep(pattern: str, glob: str) -> str:
    root = _root()
    results = []
    for match in _glob.glob(str(root / glob), recursive=True):
        mp = Path(match)
        if not mp.is_file():
            continue
        try:
            _resolve(os.path.relpath(mp, root))
        except ValueError:
            continue
        try:
            for i, line in enumerate(mp.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if pattern in line:
                    rel = os.path.relpath(mp, root)
                    results.append(f"{rel}:{i}: {line.strip()}")
                    if len(results) >= 200:
                        return "\n".join(results) + "\n... (capped at 200)"
        except Exception:
            continue
    return "\n".join(results) if results else "(no matches)"
