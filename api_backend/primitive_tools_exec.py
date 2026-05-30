"""Execution tools ÔÇö how the agent uses the host CPU/GPU.

SECURITY NOTE: run_shell is intentionally NOT sandboxed. It executes arbitrary
commands on the host with the agent's privileges. The human operator MUST
isolate this at the OS level (container, VM, dedicated machine, restricted user)
before running an autonomous loop. There is no application-level safety net here.
"""
import os
import subprocess
from pathlib import Path

from tools.registry import tool


def _root() -> Path:
    return Path(os.environ.get("AGENT_ROOT", os.getcwd())).resolve()


@tool(
    "run_python",
    "Write code to scratch/_exec.py and run it from repo root. Returns stdout+stderr.",
    {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "timeout_s": {"type": "integer", "description": "Timeout seconds (default 600)"},
        },
        "required": ["code"],
    },
)
def run_python(code: str, timeout_s: int = 600) -> str:
    root = _root()
    scratch = root / "scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    script = scratch / "_exec.py"
    script.write_text(code, encoding="utf-8")
    try:
        proc = subprocess.run(
            ["python", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        out = f"[exit {proc.returncode}]\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        return out
    except subprocess.TimeoutExpired:
        return f"ERROR: run_python timed out after {timeout_s}s"
    except Exception as e:
        return f"ERROR run_python: {e}"


@tool(
    "run_shell",
    "Run a shell command from repo root (pip, nvidia-smi, git, etc). NOT sandboxed.",
    {
        "type": "object",
        "properties": {
            "cmd": {"type": "string"},
            "timeout_s": {"type": "integer", "description": "Timeout seconds (default 600)"},
        },
        "required": ["cmd"],
    },
)
def run_shell(cmd: str, timeout_s: int = 600) -> str:
    root = _root()
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return f"[exit {proc.returncode}]\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    except subprocess.TimeoutExpired:
        return f"ERROR: run_shell timed out after {timeout_s}s"
    except Exception as e:
        return f"ERROR run_shell: {e}"
