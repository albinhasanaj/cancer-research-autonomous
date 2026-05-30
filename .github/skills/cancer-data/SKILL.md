---
name: cancer-data
description: How to test cancer hypotheses against REAL public data (cBioPortal tumour genomics, DepMap CRISPR dependencies, GDC/TCGA somatic mutations, GEO expression, Open Targets target–disease evidence & druggability, ClinicalTrials.gov human-trial status) instead of building toy models that re-derive known theory. Use whenever an open question could be checked against actual tumours, cell lines, the curated evidence base, or clinical trials — which is most of them.
---

# Grounding research in real cancer data

## When to use
Whenever you are tempted to write a simulation. Before modelling, ask: *is there a
public dataset that already answers this empirically?* A real-data test almost
always beats an elegant toy model. The agent's strongest past result came from
testing a prediction against DepMap and watching it get honestly debunked; its
weakest came from Boolean/birth-death models that re-derived textbook theory.

All tools are registered (auto-discovered from `tools/`) and callable from the
shell. They return plain strings; on failure they return an `ERROR ...` string
(they never crash the loop). List them anytime:
`python -c "from tools import registry; registry.discover(); print(registry.names())"`

## The four data sources

### cBioPortal — tumour mutations / CNA / clinical outcomes
```bash
python -c "from tools.cbioportal_tool import cbioportal_studies; print(cbioportal_studies('breast'))"
python -c "from tools.cbioportal_tool import cbioportal_gene_mutations; print(cbioportal_gene_mutations('brca_tcga_pub','TP53'))"
python -c "from tools.cbioportal_tool import cbioportal_clinical; print(cbioportal_clinical('brca_tcga_pub','OS_MONTHS'))"
```
Use for: "how often is gene X mutated in cancer type Y?", "what are the hotspot
protein changes?", survival attributes for outcome analysis.

### DepMap — CRISPR Chronos gene-effect dependencies
```bash
python -c "from tools.depmap_tool import depmap_query; print(depmap_query('BRCA1'))"
python -c "from tools.depmap_tool import depmap_query; print(depmap_query('PARP1','breast'))"
python -c "from tools.depmap_tool import depmap_compare; print(depmap_compare('PARP1','breast','lung'))"
```
Chronos score: more negative = more essential; dependent if < -0.5. Use for:
"is gene X a dependency in context Y?", synthetic-lethality checks, comparing
dependency between lineages/mutation backgrounds. First call per gene downloads +
caches to `data/depmap/genes/` (git-ignored); later calls are instant.

⚠️ **DepMap is a false-positive factory** (~18k genes × ~1k lines). A
context-specific "dependency" will appear by chance constantly. Before believing a
hit: correct for multiple testing (BH/FDR via `statsmodels.stats.multitest.
multipletests` — report q-values + #tests), demand a real **effect size** (not
just p), and require **replication + mechanism + orthogonal evidence**. A lone
uncorrected hit is a *lead* (`confidence: speculative`), not a finding. The
canonical SLs you already validate (WRN/MSI, PARP/BRCA) clear all these bars — see
the `epistemics` skill.

### GDC / TCGA — somatic mutations & cohort sizes
```bash
python -c "from tools.gdc_tool import gdc_projects; print(gdc_projects('TCGA'))"
python -c "from tools.gdc_tool import gdc_gene_mutations; print(gdc_gene_mutations('TP53','TCGA-BRCA'))"
python -c "from tools.gdc_tool import gdc_case_count; print(gdc_case_count('TCGA-BRCA'))"
```
Use for: somatic mutation frequencies in a defined TCGA cohort, cohort sizes for
power calculations.

### GEO — gene-expression dataset discovery
```bash
python -c "from tools.geo_tool import geo_search; print(geo_search('BRCA1 breast cancer expression', 5))"
python -c "from tools.geo_tool import geo_summary; print(geo_summary('GSE309617'))"
```
Use for: finding expression datasets to download (the FTP/supplementary URL is in
the summary), sizing a re-analysis.

### Open Targets — is this target worth pursuing?
```bash
python -c "from tools.opentargets_tool import opentargets_associations; print(opentargets_associations('PARP1', 10))"
python -c "from tools.opentargets_tool import opentargets_tractability; print(opentargets_tractability('PARP1'))"
```
Use for: target–disease association scores broken down by evidence type
(genetic/somatic/drug/literature), druggability buckets, and known drugs — before
committing compute to a target, check the curated evidence base.

### ClinicalTrials.gov — has anyone tried this in humans?
```bash
python -c "from tools.clinicaltrials_tool import clinicaltrials_search; print(clinicaltrials_search('olaparib BRCA', 10))"
python -c "from tools.clinicaltrials_tool import clinicaltrials_phase_summary; print(clinicaltrials_phase_summary('WRN MSI'))"
```
Use as a sharp ANSWERED/OPEN triage signal: if a drug/combination is already in
late-phase trials, the question may be settled clinically — don't re-derive it.

### Beyond these — ToolUniverse (1000+ tools) and the full catalog
For UniProt, ChEMBL, FAERS, PubTator, IEDB/NetMHCpan and the long tail, use the
`tooluniverse` skill (`tu_find`/`tu_spec`/`tu_call`). The complete map of reachable
capabilities is the `capability-catalog` skill.

## Worked patterns

**Is gene X co-essential with gene Y?** → `depmap_compare(Y, 'X-mutant lines', 'X-wt lines')`
for a real effect size + Mann-Whitney p, instead of asserting it from a network model.

**Survival split by mutation** → pull `cbioportal_clinical(study,'OS_MONTHS')` +
mutation status, then `lifelines` KaplanMeierFitter / CoxPHFitter (installed).

**Mutation frequency claim** → confirm with `gdc_gene_mutations` or
`cbioportal_gene_mutations` and cite the real count, never a remembered number.

## Discipline
- Use the installed stack for statistics: `statsmodels` (regression/GLM),
  `lifelines` (survival), `pingouin` (effect sizes), `scikit-learn` (ML with a
  held-out split). Don't hand-roll what these do correctly.
- Every empirical claim must trace to a real query you actually ran (paste the
  command + a result snippet into the finding note), the same way literature
  claims trace to a PMID.
- If a tool returns `ERROR ...`, that is a real capability gap — fix the tool or
  file a `[HEALTH]` note; do not silently fall back to inventing the answer.
