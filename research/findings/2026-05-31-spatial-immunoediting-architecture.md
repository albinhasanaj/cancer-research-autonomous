# Spatial immunoediting: tissue architecture weakens filter but does not create rate-limiting

**Date:** 2026-05-31  
**Status:** finding  
**Thread:** multistage + immune  
**Item:** 23  
**Triage:** OPEN (no prior work on pre-malignant spatial immunoediting)  
**Verdict:** KEEP (honest positive with nuance)

## Question

Does spatial tissue architecture (crypts, lobules creating immune refugia)
change the immunoediting conclusion from "population filter, not rate limiter"
(established in item 21)?

## Model

Niche-frailty extension of item 21's well-mixed immunoediting model:
- Each lineage assigned immune accessibility a_i ∈ [0,1] from tissue architecture
- Effective immune rate: α_local = α × a_i × n_neo
- Deep crypts: low a_i (sheltered); surface: high a_i (exposed)
- Four architecture models tested at matched mean E[a]:
  - Well-mixed (a=1), homogeneous-low (a=0.3), graded Beta, bimodal crypt
- Dynamic variant: clones migrate out of crypt at rate m (becoming exposed)
- 150k–200k lineages per condition; k=6, μ=0.07/yr, α=0.1, p_neo=0.5

NOT a full spatial ABM — captures first-order spatial refugia effect without
clone migration or spatial competition.

## Key findings

### 1. Spatial architecture WEAKENS the population filter

| Architecture     | E[a] | P(malignancy) | Delay factor | P(escaped) |
|-----------------|------|---------------|-------------|-----------|
| Well-mixed      | 1.00 | 0.20          | 1.06        | 0.79      |
| Homogeneous low | 0.30 | 0.33          | 0.98        | 0.64      |
| Graded (het.)   | 0.30 | 0.38          | 0.98        | 0.57      |
| Bimodal crypt   | 0.38 | 0.39          | 0.98        | 0.56      |

Graded > homogeneous at same mean (0.38 vs 0.33): **heterogeneity itself adds
~15% incidence beyond the mean-reduction effect.** This is the genuine spatial
refugia contribution — some clones in deep niches face near-zero immune pressure.

### 2. NOT a rate limiter — robust across all architectures

Delay factor stays ~0.98 across all architectures (actually slightly FASTER than
well-mixed because sheltered clones accumulate without immune friction). The
item 21 conclusion — immunoediting is a population filter, not a rate limiter —
is **robust to spatial structure**.

### 3. Sheltered accumulation: a new survival route

Deep-crypt lineages (a < 0.1) succeed 3× more often than surface lineages
(P(mal) = 0.67 vs 0.23) and only 43% need immune escape (vs 78% for surface).
Spatial architecture creates a **dual survival mechanism:**
- Route A (surface): accumulate some drivers → escape (HLA-LOH) → finish neutrally
- Route B (crypt): accumulate ALL drivers with minimal immune pressure → emerge

### 4. Neoantigen retention in sheltered tumours

| Accessibility bin | P(malignancy) | P(escaped) | Mean neoantigens |
|-------------------|---------------|-----------|-----------------|
| [0.0, 0.1)        | 0.67          | 0.43      | 2.80            |
| [0.3, 0.5)        | 0.29          | 0.66      | 2.48            |
| [0.7, 1.0)        | 0.23          | 0.78      | 2.43            |

Sheltered tumours retain MORE neoantigens (2.80 vs 2.43). This predicts:
**crypt-origin tumours should be more immunotherapy-responsive** at diagnosis
(higher neoantigen load despite immune surveillance during development).

### 5. Migration erodes sheltering smoothly

| Migration rate | P(malignancy) | P(escaped) |
|---------------|---------------|-----------|
| 0.000          | 0.38          | 0.57      |
| 0.005          | 0.34          | 0.62      |
| 0.010          | 0.30          | 0.65      |
| 0.050          | 0.23          | 0.76      |

Clonal expansion leaving the crypt smoothly converges outcomes toward well-mixed.
No phase transition — just gradual loss of spatial protection.

### 6. Mean accessibility sweep confirms heterogeneity effect

At EVERY mean E[a] tested (0.05 to 1.0), graded (heterogeneous) gives higher
P(malignancy) than matched homogeneous. The variance/refugia effect is robust,
not parameter-specific.

## Clinical implications (hypothesis-level)

1. **Tissue architecture predicts cancer incidence rates:** tissues with more
   immune-sheltered compartments (colonic crypts, breast lobules) may have higher
   per-lineage malignancy probability — partially explaining organ-specific
   cancer rates beyond stem cell divisions (Tomasetti & Vogelstein 2015).
2. **Crypt-origin tumours may respond better to immunotherapy:** higher
   neoantigen retention from sheltered accumulation predicts stronger checkpoint
   response — testable in TCGA by correlating neoantigen load with tissue of
   origin architecture.
3. **The population filter weakens with architectural sheltering but never
   converts to rate-limiting:** public health implications differ — spatial
   structure affects incidence (how many), not onset timing (when).

## Honest assessment (critic pass)

**What is claimed?** Spatial architecture weakens the immunoediting population
filter by ~90% (0.20→0.38 P(malignancy)) and creates a sheltered accumulation
route, but does not convert immunoediting to a rate limiter.

**Evidence?** 150k–200k lineage simulations with matched-mean controls and
sensitivity sweeps.

**What would falsify?** If spatial structure made delay factor > 1.5 (rate-
limiting). We see ~0.98.

**Is this a rediscovery?** No. Existing spatial ABMs (PMIDs 42135010, 28931635,
42215447) address established tumours under therapy, not pre-malignant
immunoediting in the k-hit framework.

**Limitations:**
1. Niche-frailty model, not full spatial ABM — no clone competition for crypt
   stem-cell slots, no spatial immune front propagation
2. Fixed accessibility scores — real crypts have dynamic remodelling
3. Independent lineages — tissue-level incidence would need min-over-lineages
4. Accessibility distributions are illustrative, not calibrated to histology

**Verdict: KEEP** — novel extension with honest quantitative result; the matched-
mean controls separate true heterogeneity effect from trivial mean reduction.

## Connections

- [[2026-05-30-immunoediting-driver-accumulation]] — well-mixed baseline (item 21)
- [[2026-05-30-immune-escape-checkpoint-dynamics]] — immune escape under therapy
- [[2026-05-30-unified-escape-framework]] — the unified Φ framework applies with
  a distribution over α; spatial structure creates a mixture of escape
  probabilities weighted by tissue architecture
- [[2026-05-30_armitage_doll_multistage]] — base multistage model

## Script

`simulations/spatial_immunoediting.py`

## Output

- `simulations/output/spatial_architecture_comparison.csv`
- `simulations/output/spatial_mean_sweep.csv`
- `simulations/output/spatial_migration_test.csv`
- `simulations/output/spatial_bin_analysis.csv`
