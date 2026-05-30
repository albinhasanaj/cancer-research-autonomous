---
name: openai-api
description: How to call OpenAI from code. Use when writing a tool/script that generates text, reasons, or uses native tools (web search, code interpreter, file search, image generation, remote MCP) via OpenAI. Covers the Responses API, the GPT-5 reasoning models, and function calling.
---

# OpenAI API

> Docs fetched live from https://platform.openai.com/docs (Responses API guide +
> migrate-to-Responses guide). Model names/pricing drift — re-fetch before
> hardcoding a model in a long-lived script.

## When to use

Generating text, reasoning, structured outputs, or native agentic tool use via
OpenAI. Key is `OPENAI_API_KEY`.

## Default: the Responses API

Use `client.responses.create(...)` as the default — it's a stateful, agentic
superset of Chat Completions and the direction OpenAI is pushing (better
reasoning-model performance, built-in tools, better cache utilization). Use
`store=false` for stateless calls.

```python
from openai import OpenAI
client = OpenAI()  # reads OPENAI_API_KEY

resp = client.responses.create(
    model="gpt-5.4",
    input="Summarize the Armitage-Doll multistage model in two sentences.",
    store=False,
)
print(resp.output_text)
```

With native built-in tools (run on OpenAI's side within one request):

```python
resp = client.responses.create(
    model="gpt-5.4",
    input="Find recent reviews of clonal evolution models.",
    tools=[{"type": "web_search"}],
    store=False,
)
```

Built-in tools available in one request: `web_search`, `file_search`,
`code_interpreter`, `image_generation`, remote MCP, plus custom functions.

## Current default model

- **GPT-5 family**; **gpt-5.4** is the current reasoning flagship referenced in
  the live docs (tool calling, reasoning). Use the `gpt-5` alias for the latest
  stable. **Confirm against the live catalog before pinning** — it changes.
  Budget is generous (~$2000 credits); use strong models freely and log notable
  usage.

## Gotchas

- Responses uses `input` + **Items** (typed: `message`, `function_call`,
  `function_call_output`) and returns an `output` array — NOT `messages` +
  `choices`. There's no `n`/parallel `choices`; use the `output_text` helper.
- **Function-calling schema differs** from Chat Completions (both the request
  tool config and the returned call shape). See the function-calling guide.
- **Structured Outputs:** use `text.format` in Responses, not `response_format`.
- **Reasoning models:** starting GPT-5.4, tool calling is NOT supported in *Chat
  Completions* with `reasoning: none` — another reason to default to Responses.
- Multi-turn: chain with `previous_response_id` or the Conversations API instead
  of manually re-sending message history.
- Always re-fetch the docs for exact tool schemas and current model slugs.
