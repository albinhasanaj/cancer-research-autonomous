---
name: xai-grok-api
description: How to call xAI Grok from code. Use when writing a tool/script that generates text, reasons, or needs Grok's server-side web/X search via xAI. Grok is OpenAI-SDK compatible — reuse the OpenAI SDK with a different base_url, key, and model.
---

# xAI Grok API

> Docs fetched live from https://docs.x.ai (model catalog + function-calling /
> Agent Tools guides). Confirm the current flagship at the xAI console before
> pinning a model in a long-lived script.

## When to use

Generating text/reasoning via Grok, or using Grok's server-side **web/X search**.
Key is `XAI_API_KEY` (keys start with `xai-`).

## OpenAI-SDK compatible (preferred integration)

Reuse the OpenAI Python SDK; just swap `base_url`, key, and model. Any tool we
write for OpenAI can switch to Grok by changing those three things.

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["XAI_API_KEY"],
    base_url="https://api.x.ai/v1",
)

resp = client.chat.completions.create(
    model="grok-4.3",
    messages=[{"role": "user", "content": "Explain the age-incidence power law."}],
)
print(resp.choices[0].message.content)
```

- Endpoints: `/chat/completions` and `/responses`. Auth header:
  `Authorization: Bearer $XAI_API_KEY`.
- No role-order limitation: `system`/`user`/`assistant` can appear in any order.
- xAI also ships a native `xai_sdk` (Client/chat/tool helpers) if you prefer it;
  the OpenAI-compat path keeps tools provider-swappable.

## Current default model

- **grok-4.3** — the current most intelligent + fastest general chat/coding model
  per the live catalog. Use the bare `grok-4.3` (latest stable) or
  `grok-4.3-latest` (newest features); `<model>-<date>` pins a fixed release.
  **Confirm live before hardcoding.** Budget is generous (~$2500 credits).

## Server-side web/X search

Use the **Agent Tools / Responses API** built-in tools (`web_search`,
`x_search`) — NOT the legacy `search_parameters`. Grok has no knowledge of
current events without a search tool enabled. Built-in tools run on xAI's servers
and combine with custom function tools in one request.

## Gotchas

- Verify the current flagship in the console before pinning — slugs evolve and
  older ones redirect.
- Per-key rate limits are set in the xAI console; there's a function-calling tool
  limit — check the guide.
- Confirm region/global endpoint behavior for your account.
- `logprobs`/`top_logprobs` are silently ignored on `grok-4.20` and newer.
- Knowledge cutoffs are stale (Grok 3/4 cut off Nov 2024) — enable search for
  anything time-sensitive.
