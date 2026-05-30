# Multi-hit model with driver-specific fitness effects

**Date:** 2026-05-30  
**Status:** KEEP  
**Thread:** Multistage carcinogenesis  
**Item:** 14 (open_questions)  
**Triage:** EXTENDABLE — framework established by Beerenwinkel 2007 / Bozic 2010;
delta = quantitative exponent analysis + connection to driver-count discrepancy

## Question

Does clonal expansion after each driver hit substantially alter the
age-incidence power-law exponent, explaining why sequenced tumours carry more
drivers than the Armitage-Doll exponent implies?

## Model

Extends the neutral k-hit model ([[2026-05-30_khit_montecarlo_baseline]]) with
selective advantage s per hit:

- Phase i (i→i+1 hits): i-hit clone grows at rate r_i = i·s
- Instantaneous mutation rate at time t after clone founding: μ·exp(r_i·t)
- Waiting time: T_i = ln(1 + r_i·E/μ) / r_i, where E ~ Exp(1)
- Phase 0 (no expansion): T_0 ~ Exp(μ) regardless of s
- Total time: T = Σ T_i for i=0..k-1
- When s=0: recovers Erlang(k, μ) (neutral baseline)

Parameters: μ = 0.07/yr, k ∈ {3,5,6,7}, s ∈ {0, 0.004, 0.01, 0.02, 0.04},
N = 100,000 lineages per condition.

## Key results

### 1. Speedup vs neutral

| k | s=0.004 | s=0.01 | s=0.02 | s=0.04 |
|---|---------|--------|--------|--------|
| 5 | 1.10x   | 1.21x  | 1.35x  | 1.56x  |
| 6 | 1.11x   | 1.24x  | 1.42x  | 1.67x  |
| 7 | 1.14x   | 1.29x  | 1.48x  | 1.77x  |

At realistic s ≈ 0.004 (Bozic 2010 estimate): only 10-14% speedup for k=5-7.

### 2. Effective age-incidence exponent (α in h(t) ~ t^α, fitted 30-70yr)

| k | s=0    | s=0.004 | s=0.01 | s=0.02 | s=0.04 | k-1 |
|---|--------|---------|--------|--------|--------|-----|
| 5 | 1.48   | 1.56    | 1.60   | 1.47   | 1.06   | 4   |
| 6 | 2.14   | 2.28    | 2.30   | 2.12   | 1.55   | 5   |
| 7 | 2.84   | 3.06    | 3.05   | 2.88   | 2.23   | 6   |

**Critical finding:** At realistic s=0.004, the exponent is slightly HIGHER
(not lower) than neutral, because moderate selection shifts events into the
fitting window without distorting the shape. Only at unrealistically high s
(≥0.02-0.04) does the exponent clearly decrease.

### 3. Implication for the driver-count discrepancy

The observed discrepancy (sequenced tumours show ~5-7 drivers but age-incidence
exponents suggest k ≈ 4-6) is **NOT explained by realistic clonal expansion
alone** (s ≈ 0.004). The exponent depression from selection is negligible at
biologically estimated fitness advantages. Other mechanisms must contribute:

- Tissue architecture / spatial constraints (limit effective clonal expansion)
- Heterogeneous mutation rates across stages
- Passenger hitchhiking inflating apparent driver counts
- Non-ordered accumulation (relaxing the strict sequential constraint)

## Evidence quality

- **Simulation:** exact inverse-CDF sampling from analytically known distribution;
  s=0 limit matches Erlang to floating-point precision (validates implementation)
- **Grounding:** Bozic et al. 2010 PNAS 107:18545 (s ≈ 0.004 per driver);
  Beerenwinkel et al. 2007 PLoS Comp Biol 3:e225 (waiting-time framework)
- **Honest limitation:** model assumes deterministic exponential clonal expansion
  (ignores stochastic extinction of small clones, which would INCREASE waiting
  times further, strengthening the conclusion that selection alone is insufficient)

## Script

`simulations/multistage_fitness_expansion.py`  
Output: `simulations/output/fitness_expansion_{summary,hazard}.csv`

## Links

- [[2026-05-30_khit_montecarlo_baseline]] — neutral baseline (item 2)
- [[2026-05-30_age_incidence_power_law]] — exponent deficit in neutral model (item 3)
- [[2026-05-30-senescence-shrinking-pool-late-peak]] — senescence extension (item 6)
