"""Unified Anthropic + OpenAI native tool-use loop.

run_agent drives a fresh agent turn: it sends the system+user prompt, executes
any tool calls via the tools.registry, feeds results back, and repeats until the
model stops calling tools or the step cap is hit. Tool exceptions never crash the
loop — they are caught and returned to the model as the tool result string.
"""
import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from tools import registry

_MAX_TOOL_OUTPUT = 20000


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-opus-4-8"
    max_tokens: int = 4096
    temperature: float = 1.0
    max_tool_steps: int = 25
    system: str = ""
    api_key: Optional[str] = None


def _truncate(s: str) -> str:
    if s is None:
        s = ""
    s = str(s)
    if len(s) > _MAX_TOOL_OUTPUT:
        return s[:_MAX_TOOL_OUTPUT] + f"\n...(truncated, {len(s)} chars total)"
    return s


def _exec_tool(name: str, args: dict) -> str:
    entry = registry.get(name)
    if entry is None:
        return f"ERROR: unknown tool '{name}'"
    try:
        result = entry["func"](**(args or {}))
        return _truncate(result if isinstance(result, str) else json.dumps(result))
    except Exception as e:
        return f"ERROR executing tool '{name}': {e}"


def _anthropic_schema(tools: List[str]):
    specs = []
    for name in tools:
        entry = registry.get(name)
        if entry is None:
            continue
        specs.append({
            "name": name,
            "description": entry["description"],
            "input_schema": entry["schema"],
        })
    return specs


def _openai_schema(tools: List[str]):
    specs = []
    for name in tools:
        entry = registry.get(name)
        if entry is None:
            continue
        specs.append({
            "type": "function",
            "function": {
                "name": name,
                "description": entry["description"],
                "parameters": entry["schema"],
            },
        })
    return specs


def _run_anthropic(user_prompt: str, tools: List[str], cfg: LLMConfig, on_event):
    import anthropic
    client = anthropic.Anthropic(api_key=cfg.api_key) if cfg.api_key else anthropic.Anthropic()
    tool_specs = _anthropic_schema(tools)
    messages = [{"role": "user", "content": user_prompt}]
    final_text = []
    for _ in range(cfg.max_tool_steps):
        resp = client.messages.create(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            system=cfg.system or None,
            tools=tool_specs or None,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type == "text":
                final_text.append(block.text)
                if on_event:
                    on_event("text", block.text)
            elif block.type == "tool_use":
                if on_event:
                    on_event("tool_use", {"name": block.name, "input": block.input})
                result = _exec_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
                if on_event:
                    on_event("tool_result", {"name": block.name, "result": result})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    return "\n".join(final_text)


def _run_openai(user_prompt: str, tools: List[str], cfg: LLMConfig, on_event):
    import openai
    client = openai.OpenAI(api_key=cfg.api_key) if cfg.api_key else openai.OpenAI()
    tool_specs = _openai_schema(tools)
    messages = []
    if cfg.system:
        messages.append({"role": "system", "content": cfg.system})
    messages.append({"role": "user", "content": user_prompt})
    final_text = []
    for _ in range(cfg.max_tool_steps):
        resp = client.chat.completions.create(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature,
            tools=tool_specs or None,
            messages=messages,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump())
        if msg.content:
            final_text.append(msg.content)
            if on_event:
                on_event("text", msg.content)
        calls = msg.tool_calls or []
        if not calls:
            break
        for call in calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except Exception:
                args = {}
            if on_event:
                on_event("tool_use", {"name": call.function.name, "input": args})
            result = _exec_tool(call.function.name, args)
            if on_event:
                on_event("tool_result", {"name": call.function.name, "result": result})
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })
    return "\n".join(final_text)


def run_agent(user_prompt: str, tools: List[str], cfg: LLMConfig,
              on_event: Optional[Callable] = None) -> str:
    """Run a native tool-use loop for the configured provider. Returns final text."""
    if cfg.provider == "anthropic":
        return _run_anthropic(user_prompt, tools, cfg, on_event)
    elif cfg.provider == "openai":
        return _run_openai(user_prompt, tools, cfg, on_event)
    raise ValueError(f"unknown provider: {cfg.provider}")
