---
name: external-apis
description: How to call external APIs from code — LLM providers (OpenAI, xAI Grok) and data sources (NCBI E-utilities / PubMed). Use when writing a tool or script that hits an external service, needs auth, or runs into rate limits. Covers fetching current docs before integrating.
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

## LLM providers used by this project

This project uses **two** LLM providers only — **OpenAI** (`OPENAI_API_KEY`) and
**xAI Grok** (`XAI_API_KEY`). Do not add others. Each has its own how-to skill:

- **OpenAI** → see [`openai-api`](../openai-api/SKILL.md)
- **xAI Grok** → see [`xai-grok-api`](../xai-grok-api/SKILL.md)

**When to use which:** OpenAI for native tool-rich agentic calls and reasoning
(Responses API with built-in web_search/code_interpreter/file_search); xAI/Grok
for Grok-specific capability (web/X search) or to spread load/cost across the two
generous free credit pools (~$2000 OpenAI, ~$2500 xAI). Both share the same
OpenAI-SDK shape, so a tool can switch providers by swapping `base_url` + key +
model. Use strong models freely; just log notable usage.

## Services → where to read the current docs

| Service              | Docs (fetch live)                                      |
| -------------------- | ------------------------------------------------------ |
| OpenAI               | https://platform.openai.com/docs                       |
| xAI Grok             | https://docs.x.ai                                      |
| NCBI E-utilities     | https://www.ncbi.nlm.nih.gov/books/NBK25501/           |

## Known working patterns in this repo

- **NCBI E-utilities / PubMed** (`tools/pubmed_tool.py`): base
  `https://eutils.ncbi.nlm.nih.gov/entrez/eutils`; `esearch` → `esummary`/`efetch`.
  Works with no key; set `NCBI_API_KEY` to raise the rate limit. Sleep ~0.34s
  between calls (3 req/s unauthenticated limit). Send a `User-Agent` header.
- **PubTator Central** (`tools/pubtator_tool.py`): base
  `https://www.ncbi.nlm.nih.gov/research/pubtator3-api`; `find_entity_id` (name →
  concept id) and `publications/export/biocjson?pmids=` (pre-computed, normalized
  gene/disease/chemical/variant annotations). No key, free, no inference cost.
- **LLM providers**: this project calls **OpenAI** and **xAI Grok** only, both via
  the OpenAI SDK shape (swap `base_url` + key + model). Keys from `.env`. See the
  `openai-api` / `xai-grok-api` skills for the request shapes.

## Gotchas

- Keys live in `.env` (git-ignored). Never hardcode or commit them.
- Always wrap external calls in try/except and surface the error string — a
  flaky network must not crash an iteration.
- Respect rate limits; add backoff/sleep. NCBI will throttle aggressive callers.
- When you integrate a NEW service, add a row above and a "known working
  pattern" once you have it working.
