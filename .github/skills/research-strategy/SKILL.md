---
name: research-strategy
description: How to decide what to actually do in a research iteration — triage the frontier before computing, choose the right instrument (native search, PubMed, provider research modes, or a tool/workflow you build), and judge when self-improvement pays off. Use at the start of every research iteration, before designing any simulation or analysis.
---

# Research strategy: triage before you compute

## When to use

Every iteration, right after you pick an open question and before you write any
simulation, fit, or analysis. This is the habit that stops you re-deriving things
the world already knows.

## The core move: search the frontier first

Computation is expensive and only valuable for genuinely open questions. Before
building anything, find out what is already known.

1. **Search.** Use your **native web search + web fetch** for the general
   literature, preprints (bioRxiv/medRxiv), reviews, and prior computational
   work; use `pubmed_search` / `pubmed_fetch` for structured biomedical papers.
   For a hard or broad question, consider a **provider research mode** (OpenAI /
   xAI — see below) that searches and synthesises for you.
2. **Classify** the question:
   - **ANSWERED** — consensus already exists. Record it with citations and move
     on. Re-simulating to "confirm" a textbook result is a DEMOTE, not progress.
   - **EXTENDABLE** — partially answered; there is a *specific, cheap* delta worth
     adding (a verification, a missing parameter, an untested edge case). Do only
     that delta.
   - **OPEN** — after a genuine search, no clear answer. *Now* computation earns
     its cost: design the simulation/model/analysis.
3. **Record what you searched** (queries, key hits) in the finding/log so the next
   iteration doesn't repeat it.

## Know your full instrument set

Pick the best tool, not just the most familiar one:

| Need | Reach for |
| --- | --- |
| Is this already known? broad/grey literature, preprints | native web search + web fetch |
| Specific biomedical papers, PMIDs, abstracts | `pubmed_search` / `pubmed_fetch` |
| Hard synthesis / multi-source "what's the state of the art?" | provider **research/deep-research mode** (see `openai-api`, `xai-grok-api`) |
| Recall your own prior notes | `memory_search` |
| Settle a genuinely OPEN quantitative question | your own Python/shell simulation |

You have **budgeted keys in `.env`** (`OPENAI_API_KEY` ~$2000, `XAI_API_KEY`
~$2500) — spending them is pre-approved; just log notable usage. That means a
provider's server-side web search, code interpreter, or deep-research mode is a
legitimate instrument, not something to avoid.

## Build-vs-research: a judgement call you make from ROI

Sometimes the highest-value thing this iteration is **not** a finding — it's
building a capability you'll reuse. Make this call yourself from return on
investment; never because a rule told you to, and never speculatively.

Signals that building now pays off:
- You keep needing the same capability across iterations (recurring need).
- A small tool or **agentic workflow** would make many future passes cheaper,
  faster, or higher-quality (future leverage).
- You're blocked on the current item by a missing external capability.

Worked example of the reasoning:
> "I'm manually stitching together searches every iteration. OpenAI/xAI may have a
> deep-research mode that does this better. → web-search their current docs to
> confirm it exists and fits → if yes, write a small `tools/` function or a
> multi-step workflow that calls it, register it, and document it in a skill →
> use it from now on."

Native-first: web/file/shell/search are already yours — only build a new tool or
workflow for a genuine *external* gap or a high-reuse instrument. Record any new
how-to as a skill; note structural changes in `research/00_index.md`.

## Generating the next question

When you add open questions, bias toward the **frontier**: questions the
literature does *not* already answer, gaps your prior findings exposed, or
capability investments — over re-validating known theory. Re-derivations are
warm-ups to build trust in the machinery, not the goal.

## Gotchas

- A confident-sounding LLM answer is not a citation. Ground empirical claims in a
  PMID/DOI or a script you ran (honesty rules in `AGENTS.md`).
- Provider model names and research-mode availability change — fetch the live
  docs before hardcoding (see the provider skills).
- "Already answered" still needs a real search, not an assumption. If you didn't
  search, you didn't triage.
