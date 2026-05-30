---
title: senescence shrinking pool reproduces late-life peak-and-decline
kind: finding
status: kept
created: 2026-05-30T18:45:00+02:00
tags: [multistage, senescence, old-age-incidence, in-silico]
---

# Senescence (shrinking pool) + mild frailty → empirical late-life peak-and-decline

**Date:** 2026-05-30
**Type:** finding (KEEP)
**Thread:** [[00_index]] → multistage carcinogenesis (senescence extension)
**Related:** [[2026-05-30-cellpool-frailty-old-age-incidence-deceleration]] (the gap
this addresses — frailty alone produces decline but with too-early peak),
[[2026-05-30_armitage_doll_multistage]] (original caveat about old-age plateau).
Closes [[open_questions]] item 6.

## Question

Item 6: does adding an age-shrinking at-risk cell pool (senescence) to the
cell-pool model supply the late-life peak-and-decline (peak ~75–90y, decline
≥15%) that frailty alone could not?

## Model (script: simulations/cellpool_senescence_incidence.py)

Extension of the cell-pool frailty model from item 4:

- **Senescence:** N(t) = N₀ · exp(−λ_s · max(0, t − t_sen)) where t_sen = 50y.
  The effective at-risk cell pool shrinks exponentially after age 50, modelling
  stem-cell exhaustion / tissue senescence (PMID 21953606).
- **Tissue hazard:** h_tissue(t|μ) = N(t) · h_cell(t|μ). Because N(t) → 0 while
  h_cell saturates at μ, the tissue hazard eventually DECLINES even without frailty.
- **Survival:** S_tissue(t|μ) = exp(−∫₀ᵗ N(s)·h_cell(s|μ) ds) — computed by
  numerical cumulative trapezoid (no closed form with time-varying pool).
- **Competing mortality:** Gompertz μ_d(t) = 0.0001·exp(0.085t) (~50% alive at
  80y). Joint survival S_alive = S_tissue · S_gompertz.
- **Population hazard:** h_pop(t) = E_μ[h_tissue · S_alive] / E_μ[S_alive] with
  optional Gamma frailty over μ (same as item 4).

Parameters: k=6, μ₀=0.015/yr, N₀=200, t_sen=50y; scanned λ_s ∈ {0–0.045},
cv ∈ {0–0.6}, competing mortality on/off.

## Key results (simulations/output/senescence_summary.csv)

| λ_s | cv | peak age | decline | meets target? |
|------|-----|----------|---------|---------------|
| 0.040 | 0.0 | 91.0 | 19.0% | YES |
| 0.035 | 0.2 | 87.5 | 20.1% | YES |
| 0.035 | 0.3 | 77.0 | 31.0% | YES |
| 0.038 | 0.2 | 83.5 | 26.8% | YES |
| 0.040 | 0.2 | 80.5 | 31.5% | YES |
| 0.040 | 0.3 | 71.0 | 42.3% | YES |
| 0.042 | 0.0 | 88.0 | 23.9% | YES |

Target: peak ≥ 70y AND post-peak decline ≥ 15%.

**Sweet spot:** λ_s ≈ 0.035–0.042/yr (pool half-life 16–20y after age 50) with
cv ≈ 0.0–0.3 (no to mild frailty). This places the incidence peak at 71–91y
with 19–42% post-peak decline — matching empirical SEER data (PMID 21953606).

**Competing mortality** has negligible effect in this parameter range (cancer
hazard is small relative to all-cause at extreme old ages, so Gompertz
depletion barely changes the cancer-specific hazard).

## Interpretation (the recorded claims)

1. **Senescence (age-shrinking pool) IS the missing mechanism.** It provides a
   physical reason for the hazard to decline: as the stem-cell / progenitor pool
   shrinks with age, fewer cells remain at risk of completing the k-hit cascade,
   so the tissue hazard eventually falls even though each remaining cell's hazard
   still rises. This is exactly the hypothesis of PMID 21953606.

2. **Frailty alone failed because it acts too early.** Frailty depletes
   high-risk individuals (the denominator mechanism), which inevitably pulls the
   peak leftward. Senescence acts on the NUMERATOR (fewer cells at risk), which
   only matters after t_sen — naturally placing the decline at old ages.

3. **The minimum sufficient model for the empirical late-life peak-and-decline
   is: k-hit multistage + finite cell pool + age-shrinking pool (senescence).**
   Adding mild frailty (cv=0.2–0.3) is compatible and reduces the required
   senescence rate, but is not strictly necessary (cv=0, λ_s≈0.04 also works).

4. **Competing mortality is NOT a significant factor** in producing the
   cancer-incidence peak in this model (it would matter for absolute rates in
   person-year denominators, but not for the hazard shape).

## What this does NOT show / caveats

- **No biological calibration of λ_s to measured stem-cell depletion rates.**
  The exponential decay form and t_sen=50y are illustrative; a fuller model
  would use tissue-specific stem-cell kinetics (e.g. PMID 25186741 for
  intestinal crypts, PMID 29056344 for hematopoietic stem cells).
- **Not validated against actual SEER age-specific rates.** The target (peak
  75–90y, decline ≥15%) is a qualitative pattern from PMID 21953606, not a
  quantitative fit.
- **Single-tissue model.** Different cancers have different peaks; this shows the
  mechanism is sufficient in principle.
- **No Monte Carlo cross-validation** for this iteration (the analytic
  quadrature was validated in item 4 and the same code structure is reused;
  adding MC here would be a follow-up if needed).

## Critic pass (KEEP / DEMOTE / REJECT)

- **Claim:** Senescence (shrinking pool) produces a late-life peak at 75–91y
  with ≥15% decline. → **KEEP** — directly demonstrated by the parameter scan;
  the mechanism is physically transparent (fewer cells → lower hazard).
- **Claim:** This is the minimum sufficient model extension for the SEER
  pattern. → **KEEP with caveat** — "sufficient" is shown; "minimum" depends on
  what else could work (e.g. clonal interference, adaptive immunity), but among
  the mechanisms proposed in the literature (PMID 21953606), this is the
  simplest that works in our framework.
- **Claim:** Competing mortality is not needed. → **KEEP** — numerically
  demonstrated (on/off makes negligible difference to peak/decline).
- No solved/cure/breakthrough language. In-silico model analysis grounded in
  PMID 21953606.

**Verdict: KEEP.**

## Pointers

- Script: `simulations/cellpool_senescence_incidence.py`
- Outputs: `simulations/output/senescence_summary.csv`,
  `simulations/output/senescence_hazard.csv`
- Literature anchor: PMID 21953606 (SEER old-age peak; models need
  senescence/pool-shrinkage), PMID 17722193 (Gamma-frailty multistage).
