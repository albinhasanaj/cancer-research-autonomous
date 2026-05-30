# Heterogeneous Per-Gene Mutation Rates and Effective Exponent

**Date:** 2026-05-30  
**Item:** Q17 (driver-count discrepancy thread)  
**Status:** KEEP (honest negative on hypothesis)  
**Script:** `simulations/multistage_heterogeneous_rates.py`

## Question

When k required hits each have a DIFFERENT per-gene mutation rate (drawn from
a lognormal distribution), does the effective age-incidence exponent drop below
k-1, thereby explaining the driver-count discrepancy?

## Triage

**EXTENDABLE.** Frank (2007, "Dynamics of Cancer") and Luebeck & Moolgavkar
(2002) establish that heterogeneous rates can depress the observed exponent.
However, those treatments focus on inter-individual heterogeneity (population
mixing). The specific delta here: computational test of per-GENE rate
variation within a single individual's multistage pathway.

## Method

- k ∈ {4,5,6,7} required hits, each with rate μ_i ~ LogNormal(log(μ_geom), σ)
- μ_geom = 0.07/yr (calibrated so homogeneous k=6 has median onset ~81yr)
- σ ∈ {0, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0} (σ=1 → ~7× 95% spread in rates)
- N = 300,000 lineages per trial; 30 independent rate draws per (k, σ)
- Hazard estimated by life-table; effective exponent from log-log slope in
  shared fit window (45–81yr, from homogeneous k=6 percentiles)
- Analytic verification via exact Hypoexponential hazard at t → 0

## Results

### Ensemble-averaged exponents (k=6, theoretical = 5)

| σ   | Mean exponent | Std   | Depression from 5 |
|-----|--------------|-------|-------------------|
| 0.0 | 1.68         | 0.02  | 3.32              |
| 0.5 | 1.60         | 0.41  | 3.40              |
| 1.0 | 1.53         | 0.79  | 3.47              |
| 1.5 | 1.53         | 0.86  | 3.47              |
| 2.0 | 1.47         | 0.95  | 3.53              |

### Key observation

The **homogeneous** case (σ=0) already gives exponent 1.68 — a massive
depression of 3.32 from the theoretical 5. This is the **finite-window
effect** established in [[2026-05-30_age_incidence_power_law]] (item 3):
μt ≈ 3–6 in the 45–81yr window, far from the t→0 asymptotic regime.

Adding rate heterogeneity (σ up to 2.0, corresponding to ~55× spread between
fastest and slowest genes) provides only **~0.15–0.2 additional depression**.
This marginal effect is dwarfed by trial-to-trial variance (std 0.8–0.95).

### Analytic verification

For T = Σ Exp(λ_i) (sum of k independent exponentials with distinct rates):
- CDF near t=0: F(t) ≈ (∏ λ_i) · t^k / k!
- Hazard: h(t) ≈ (∏ λ_i) · t^(k-1) / (k-1)!
- **Exponent = k-1 ALWAYS, regardless of rate values**

Verified numerically: at t = 0.5–3yr, log-log slope = 4.92 for σ=1 and 4.91
for σ=2 (both ≈ 5 = k-1). The asymptotic exponent is strictly invariant to
per-gene rate heterogeneity.

## Conclusion (HONEST NEGATIVE)

**Per-gene mutation-rate heterogeneity does NOT explain the driver-count
discrepancy.** The Hypoexponential hazard always has asymptotic exponent k-1;
heterogeneous rates change the magnitude (∏ λ_i) but not the power-law slope.

This rules out the **third** candidate mechanism:
- Q14: clonal expansion → NO (realistic s ≈ 0.004 too weak)
- Q15: non-ordered accumulation → NO (exponent invariant to ordering)
- Q17: heterogeneous per-gene rates → NO (exponent invariant to rate spread)

## Reframing the discrepancy

The "discrepancy" (tumours have ~6 drivers but fitted exponent implies k ≈ 3)
may be **largely a finite-window artifact**. Even a homogeneous 6-hit model
gives fitted exponent ≈ 1.7 (inferred k ≈ 2.7) when measured in the 45–80yr
epidemiological window, because μt is not small enough for the power-law
asymptotic to hold. The classic Armitage-Doll method of inferring k from the
exponent is only valid in the μt → 0 limit — which is never reached for
cancers with onset in adulthood.

## What remains

The only mechanism NOT yet tested for population-level exponent depression is
**inter-individual heterogeneity** (population mixing of susceptibilities), as
in Frank (2007). This is fundamentally different from per-gene variation: it
averages hazards across people with different overall rates, depleting
susceptibles and flattening the population curve. Item 4 explored this via
Gamma frailty — it does depress the population hazard, but its main effect is
the old-age peak-and-decline, not exponent reduction in the rising phase.

## Links

- [[2026-05-30_age_incidence_power_law]] — finite-window effect (item 3)
- [[2026-05-30-fitness-effect-multistage]] — clonal expansion negative (item 14)
- [[2026-05-30-unordered-hit-accumulation]] — ordering invariance (item 15)
- [[2026-05-30-cellpool-frailty-old-age-incidence-deceleration]] — frailty (item 4)
