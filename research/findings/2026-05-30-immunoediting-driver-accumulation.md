# Immunoediting shapes driver accumulation: population filter, not rate limiter

**Date:** 2026-05-30  
**Status:** finding  
**Thread:** multistage + immune  
**Item:** 21  
**Triage:** EXTENDABLE (Lakatos 2020 PMID 32929288 + Rosenthal 2019 PMID 30894752)  
**Verdict:** KEEP (honest partial-negative on hypothesis)

## Question

Does immune negative selection on immunogenic drivers substantially slow the
effective driver accumulation rate and time-to-malignancy?

## Model

Extended the k-hit Armitage-Doll framework:
- Clone acquires k ordered drivers at rate μ=0.07/yr
- Each driver independently immunogenic with probability p_neo
- Immune elimination hazard: α × n_neoantigens (per year)
- Immune escape possible at rate u_escape=0.005/yr (models HLA-LOH)
- After escape, no further immune elimination
- 100k–200k lineages per condition

## Key findings

### 1. Immunoediting is a population filter, NOT a rate limiter

At moderate immune pressure (α=0.1, p_neo=0.5):
- **80% of lineages are eliminated** (P(malignancy) = 0.20)
- But surviving lineages take only **5% longer** (median T: 85.5 vs 81.1 yr)
- The delay factor saturates at ~1.10–1.13 even at strong α=0.5

**Interpretation:** Immunoediting primarily reduces cancer *incidence* (fewer
successful lineages), not *onset age* (timing barely changes). This is consistent
with the epidemiological observation that immunosuppressed patients have higher
cancer rates but not dramatically earlier onset.

### 2. Immune escape dominates in successful tumours

At α≥0.1, p_neo=0.5: **78–85%** of successful tumours escaped immune
surveillance before completing k hits. The dominant route to malignancy is:
accumulate a few drivers → hit immune pressure → escape (HLA-LOH) → complete
remaining drivers unimpeded.

This is consistent with Rosenthal 2019's finding of widespread HLA-LOH and
neoantigen depletion in established NSCLC.

### 3. Neoantigen depletion confirmed (Lakatos 2020 prediction)

Successful tumours carry ~20% fewer neoantigens than the neutral expectation
(k × p_neo). Depletion ratio:
- α=0.05: 0.82
- α=0.1: 0.80
- α=0.5: 0.78

The depletion **plateaus** because once escape occurs, further hits accumulate
neutrally. This matches Lakatos 2020's prediction that the neoantigen frequency
spectrum appears "more neutral" under stronger selection.

### 4. k-dependence: higher k → lower P(malignancy), minimal timing effect

| k | P(malig) | Delay factor | P(escaped) |
|---|----------|-------------|------------|
| 2 | 0.73     | 0.92        | 0.15       |
| 4 | 0.33     | 0.97        | 0.45       |
| 6 | 0.20     | 1.06        | 0.79       |
| 7 | 0.18     | 1.07        | 0.89       |

More required hits → more neoantigens → more immune pressure → stronger
population filtering. But timing remains nearly unchanged because escape is
the dominant survival mechanism.

### 5. Implication for the driver-count question

Item 21 asked: "Could immunoediting explain why some cancers accumulate fewer
drivers than expected?" **Partial answer:**
- Successful tumours do show ~20% neoantigen depletion (consistent)
- But the mechanism is not "slower accumulation" — it's "early escape + neutral
  accumulation thereafter"
- The effective driver count is reduced by ~0.6 drivers (from 3.0 → 2.4 immunogenic
  out of 6 total), not by slowing the rate

## Honest assessment (critic pass)

**What is claimed?** Immunoediting acts primarily as a population filter (reducing
incidence) rather than a rate limiter (slowing individual timelines). Successful
tumours escape early and accumulate remaining drivers neutrally.

**Evidence?** Simulation with 100k–200k lineages per condition; consistent with
Lakatos 2020's predictions and Rosenthal 2019's observations.

**What would falsify?** If immunoediting substantially slowed malignancy (delay
factor >1.5). Our model shows only 5–13% delay.

**Is this a rediscovery?** Partially. Lakatos 2020 already showed neoantigen
depletion under negative selection. Our novel contribution: (1) coupling to
the pre-malignant k-hit framework (not post-malignancy); (2) quantifying the
delay factor as modest (<13%); (3) showing the population-filter vs rate-limiter
distinction explicitly; (4) demonstrating that immune escape dominates at
realistic parameters.

**Verdict: KEEP** — the population-filter insight and the quantitative coupling
to the multistage framework are novel extensions beyond Lakatos.

## Connections

- [[2026-05-30-immune-escape-checkpoint-dynamics]] — same immune escape framework,
  applied to therapy (item 19). Item 21 applies it to pre-malignant surveillance.
- [[2026-05-30-fitness-effect-multistage]] — driver-count discrepancy thread.
  Immunoediting contributes ~20% neoantigen depletion but via escape, not rate.
- [[2026-05-30_armitage_doll_multistage]] — base multistage model.

## Script

`simulations/immunoediting_driver_accumulation.py`

## Output

- `simulations/output/immunoediting_param_scan.csv`
- `simulations/output/immunoediting_k_scan.csv`
- `simulations/output/immunoediting_depletion.csv`
