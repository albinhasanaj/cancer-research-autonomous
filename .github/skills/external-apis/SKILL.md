---
name: external-apis
description: How to call external APIs from code — LLM providers (OpenAI, Anthropic) and data sources (NCBI E-utilities / PubMed). Use when writing a tool or script that hits an external service, needs auth, or runs into rate limits. Covers fetching current docs before integrating.
---

# Calling external APIs

## When to use

You're writing a `tools/` tool or a script that talks to an external service —
an LLM provider, a literature/data source, any HTTP API.

## Rule: fetch docs first, trust memory never

API surfaces drift. Before integrating a service, **fetch its current docs**
(model names, endpoints, auth headers, rate limits change often). Then record the
working pattern back here (or in a service-specific skill) so the next
integration is copy-paste.

## Services → where to read the current docs

| Service              | Docs (fetch live)                                      |
| -------------------- | ------------------------------------------------------ |
| OpenAI               | https://platform.openai.com/docs                       |
| Anthropic            | https://docs.claude.com                                |
| NCBI E-utilities     | https://www.ncbi.nlm.nih.gov/books/NBK25501/           |

## Known working patterns in this repo

- **NCBI E-utilities / PubMed** (`tools/pubmed_tool.py`): base
  `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`; `esearch` → `esummary`/`efetch`.
  Works with no key; set `NCBI_API_KEY` to raise the rate limit. Sleep ~0.34s
  between calls (3 req/s unauthenticated limit). Send a `User-Agent` header.
- **LLM providers** (fallback `api_backend/llm_client.py`): native tool-use loop
  for both Anthropic (`messages.create`, `tools=[{name,description,input_schema}]`,
  `tool_use`/`tool_result` blocks) and OpenAI
  (`chat.completions`, `tools=[{type:function,...}]`, `role:"tool"` results).

## Gotchas

- Keys live in `.env` (git-ignored). Never hardcode or commit them.
- Always wrap external calls in try/except and surface the error string — a
  flaky network must not crash an iteration.
- Respect rate limits; add backoff/sleep. NCBI will throttle aggressive callers.
- When you integrate a NEW service, add a row above and a "known working
  pattern" once you have it working.
