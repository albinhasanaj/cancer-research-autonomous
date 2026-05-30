---
name: capability-catalog
description: The master index of external scientific capabilities the agent can reach — tools already wired in this repo, optional heavy libraries to install on demand, and high-value APIs/datasets/frameworks to adopt when ROI justifies. Use when "checking the frontier", looking for real data instead of simulating, or deciding whether to build/install a new capability. Answers "what can I reach for, and how do I call it?".
---

# Capability catalog

## When to use
During the **Check the frontier** triage step, or whenever you are about to
simulate something that real data / an existing tool could answer. This is the
discovery layer: scan it, pick the instrument, call it on demand. It is the
keyword-searchable "tool finder" for this repo — grep it for a capability, then
invoke the one thing you need.

## How capabilities are loaded here (read this first)
This repo runs on the **Copilot CLI path** (`run_loop.sh`). Tools are **plain
Python called from the shell** — NOT MCP, NOT pre-loaded schemas. Discovery is via
skills like this one; invocation is `python -c "from tools.X import f; print(f(...))"`.
That is the dynamic-loading design: you pay context only for the capability you
actually use, the moment you use it. **Do not add MCP servers** (`run_loop.sh`
runs `--disable-builtin-mcps` deliberately) and do not wrap native file/shell/web
in tools. See `AGENTS.md` > Tool policy.

Adoption ladder (cheapest first):
1. **Native** web-fetch / shell / code — most "capabilities" are already this.
2. **Wired tool** in `tools/` — call it from the shell (table below).
3. **Optional pip library** — `pip install` on demand, then use; document in a skill.
4. **ToolUniverse** — one shell surface over 1000+ tools (see `tooluniverse` skill).
5. **Reference pattern** — read it, steal the design; do not vendor it.

List everything currently registered:
`python -c "from tools import registry; registry.discover(); print(registry.names())"`

## Tier 1 — already wired in `tools/` (call now)
| Capability | Call | Use for |
|---|---|---|
| PubMed | `from tools.pubmed_tool import pubmed_search, pubmed_fetch` | literature grounding (PMIDs) |
| cBioPortal | `from tools.cbioportal_tool import cbioportal_studies, cbioportal_gene_mutations, cbioportal_clinical` | tumour mutation freq, survival |
| DepMap | `from tools.depmap_tool import depmap_query, depmap_compare` | CRISPR dependency / synthetic-lethality |
| GDC/TCGA | `from tools.gdc_tool import gdc_projects, gdc_gene_mutations, gdc_case_count` | somatic mutation freq, cohort sizes |
| GEO | `from tools.geo_tool import geo_search, geo_summary` | expression dataset discovery |
| Open Targets | `from tools.opentargets_tool import opentargets_associations, opentargets_tractability` | "is this target worth pursuing?" — genetic/somatic evidence, druggability, known drugs |
| ClinicalTrials.gov | `from tools.clinicaltrials_tool import clinicaltrials_search, clinicaltrials_phase_summary` | "has anyone tried this in humans?" — ANSWERED/OPEN triage |
| PubTator3 | `from tools.pubtator_tool import pubtator_entity, pubtator_annotate` | normalize names → concept IDs; turn PMID abstracts into graph-linkable entities + relations |
| ToolUniverse | `from tools.tooluniverse_tool import tu_find, tu_spec, tu_call` | 1000+ tools (UniProt, ChEMBL, FAERS, PubTator, IEDB/NetMHCpan…) — needs `pip install tooluniverse` |

See the `cancer-data` skill for worked cBioPortal/DepMap/GDC/GEO patterns, the
`tooluniverse` skill for the find→inspect→call loop, the `simulation-engines` skill
for validated tumour/Boolean simulators, and the `knowledge-graph` skill for
multi-hop PrimeKG reasoning.

## Tier 2 — optional pip libraries (install on demand)
Keep core `requirements.txt` lean; these are heavy or niche. Install when a task
needs them, then write/refresh a skill.

| Library | Install | Use for | Notes |
|---|---|---|---|
| `mhcflurry` | `pip install mhcflurry` then `mhcflurry-downloads fetch models_class1_presentation` | peptide–MHC binding/presentation; grounds neoantigen `p_neo` | pulls tensorflow (heavy). Already wired optionally in `simulations/neoantigen_mhc.py` (falls back if absent). No NetMHC licence wall. Alt: ToolUniverse `IEDB_predict_mhci_binding`. |
| `tooluniverse` | `pip install tooluniverse` | 1000+ scientific tools via `tools/tooluniverse_tool.py` | heavy; lazy-imported, friendly hint if absent |
| `gseapy` | already in requirements | GSEA / enrichment | Rust core, fast |
| `scanpy` | `pip install scanpy` | single-cell RNA-seq analysis | only if going single-cell |

## Tier 3 — high-value APIs reachable NATIVELY (no install, just fetch)
Use native web-fetch / `urllib`; wrap in a `tools/` file only if reused a lot.
- **ChEMBL** — bioactivity REST: `https://www.ebi.ac.uk/chembl/api/data/...` (also via ToolUniverse `ChEMBL_*`).
- **UniProt** — protein function/sequence: `https://rest.uniprot.org/...` (also ToolUniverse `UniProt_*`).
- **PrimeKG** (mims-harvard) — precision-medicine knowledge graph (100k+ nodes, 4M+ edges, 29 edge types) as CSV from Harvard Dataverse, for multi-hop drug→target→pathway→disease reasoning. **Wired pattern:** see the `knowledge-graph` skill (download + cached pandas traversal).
- (PubTator3 is now a wired tool — see Tier 1; ChEMBL/UniProt also reachable via ToolUniverse.)

## Tier 4 — simulation engines (peer-reviewed; prefer over hand-rolled)
Reach for a validated engine before re-deriving a tumour model — **see the
`simulation-engines` skill** for install + adoption discipline:
- **tugHall** — hallmarks-of-cancer cell-evolution simulator (R).
- **SISTEM** (Python) — mutation profiles + read counts with ground-truth lineages, incl. metastasis/migration.
- **CancerSim** (JOSS) — neutral-evolution power-law tumours.
- **BooLEVARD** (Python) — counts activating/repressing paths to a node state in Boolean models; directly relevant to the repo's Boolean-SL work.

## Tier 5 — literature → structured knowledge
- **BERN2** (dmis-lab) — biomedical NER+normalization (links entities to concept IDs → mergeable into a KG).
- **scispaCy** — lighter local biomedical NER.
- **biomedmcp** — agentic PubMed query optimization (better recall than naive phrasing).

## Tier 6 — autonomous-science frameworks (reference patterns, do NOT vendor)
Read their loops, steal designs; don't adopt wholesale: **InternAgent/NovelSeek**,
**AI-Researcher** (HKUDS), **HypoGeniC**, **freephdlabor**, **DeepCritical**
(its ClinicalTrials tooling notes). Master maps: `awesome-ai-for-science`,
`awesome-computational-biology`.

## Tier 7 — single-cell / perturbation (future expansion)
- **GEARS** — graph model predicting transcriptional response to genetic perturbations.
- **CancerFoundation** — scRNA-seq foundation model on malignant cells.
- **scanpy** — single-cell backbone.

## Adoption discipline
- Prefer Tier 1/3 (already reachable) before installing or building.
- Install Tier 2 only when a task needs it; add a row + a skill once it works.
- Promote a Tier-3 native recipe into a `tools/` file only when you reuse it
  enough to justify the maintenance (the existing data tools are the bar).
- Every empirical claim still traces to a real query you ran or a PMID — a tool
  existing is not evidence; running it is.
