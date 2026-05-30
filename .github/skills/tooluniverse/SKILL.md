---
name: tooluniverse
description: How to reach 1000+ external scientific tools (UniProt, ChEMBL, FAERS, PubTator, IEDB/NetMHCpan, Open Targets, docking and more) through ToolUniverse via a single shell surface, using a find→inspect→call loop that keeps context cost near zero. Use when this repo lacks a wired tool for a biomedical capability and you want to discover and call one on demand.
---

# ToolUniverse — 1000+ tools, one shell surface

## When to use
You need an external scientific capability this repo does NOT already wire (see
the `capability-catalog` skill for what is wired). Instead of building a new tool
or browsing 2000+ tools, use ToolUniverse's own discovery loop: **find** a tool by
keyword, **inspect** just its schema, **call** it. You pay context only for the
one tool you use — the dynamic-loading pattern at the shell layer.

## Install (optional heavy dependency)
```bash
pip install tooluniverse
```
If absent, the wrapper returns a friendly install hint (never crashes). On Windows
set `PYTHONIOENCODING=utf-8` (ToolUniverse prints a unicode banner).

## The find → inspect → call loop
Wired in `tools/tooluniverse_tool.py`; call from the shell:

```bash
# 1. FIND — keyword search (no API key / GPU). Returns names + descriptions.
python -c "from tools.tooluniverse_tool import tu_find; print(tu_find('mhc peptide binding affinity', 5))"

# 2. INSPECT — full input schema for ONE tool (OpenAI function format).
python -c "from tools.tooluniverse_tool import tu_spec; print(tu_spec('IEDB_predict_mhci_binding'))"

# 3. CALL — execute with a JSON arguments string.
python -c "from tools.tooluniverse_tool import tu_call; print(tu_call('UniProt_get_function_by_accession', '{\"accession\":\"P05067\"}'))"
```

First call per process loads the catalog (~2000+ tools), so it is slow (tens of
seconds); subsequent calls in the same `python` process are fast. Each Ralph
iteration is a fresh process, so prefer doing related ToolUniverse work in one
script rather than many separate `python -c` shells.

## What's in there (high-value for this repo)
- **IEDB_predict_mhci_binding** — NetMHCpan peptide–MHC I binding (neoantigen work;
  complements `simulations/neoantigen_mhc.py` / MHCflurry).
- **UniProt_*** — protein function, sequence, features.
- **ChEMBL_*** — bioactivity, compounds, mechanisms.
- **OpenTargets_*** — target–disease associations (also wired natively in
  `tools/opentargets_tool.py` for the common cases).
- **PubTator_*** — normalized PubMed entity annotations.
- **FAERS_*** — drug adverse-event counts (pharmacovigilance).

## Discipline
- Prefer a **wired** repo tool when one exists (cheaper, cached) — check the
  `capability-catalog` table first. Reach for ToolUniverse for the long tail.
- Treat results like any data: record the exact `tu_call` you ran in the finding
  note, the same way you cite a PMID. A tool existing is not evidence.
- Do NOT add ToolUniverse as an MCP server — this repo runs `--disable-builtin-mcps`
  on purpose. Shell-call the wrapper instead.
