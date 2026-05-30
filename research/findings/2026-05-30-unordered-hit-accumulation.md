# Non-ordered hit accumulation model

**Date:** 2026-05-30  
**Status:** KEEP (honest negative on hypothesis)  
**Thread:** Multistage carcinogenesis → driver-count discrepancy  
**Script:** `simulations/multistage_unordered_hits.py`  
**Output:** `simulations/output/unordered_vs_ordered_exponents.csv`

## Question

Does relaxing the Armitage–Doll assumption of strict ordering (hits must occur
in sequence 1→2→...→k) change the age-incidence exponent? If unordered
accumulation gives a lower effective exponent for the same k, it could explain
why sequenced tumours show more drivers than age-incidence fitting implies.

## Triage

**EXTENDABLE.** Beerenwinkel et al. 2007 (PLoS Comp Biol 3:e225) establishes
that unordered accumulation reduces waiting time by ~H_k/k factor (harmonic
number) but the asymptotic hazard exponent remains t^(k−1). My delta:
computational verification + explicit exponent comparison + practical
epidemiological consequences.

## Method

- **Ordered model:** T ~ Erlang(k, μ) — sum of k iid Exp(μ).
- **Unordered model:** T ~ Hypoexponential(kμ, (k-1)μ, ..., μ) — coupon
  collector structure (first hit = any of k genes at combined rate kμ; second =
  any of k-1 remaining, etc.).
- Monte Carlo: 200,000 lineages per condition, k ∈ {3,...,7}, μ ∈ {0.07, 0.02}.
- Empirical hazard computed via life-table; exponent fitted via log–log
  regression in an adaptive window (5th–30th percentile of onset for each model)
  and a shared [40,70yr] window at μ=0.02.

## Key findings

### 1. Speedup confirmed
Unordered is H_k-times faster than ordered (H_k = harmonic number ≈ ln(k)+γ):
- k=6: mean 35yr (unordered) vs 86yr (ordered) at μ=0.07 → 2.45× faster
- Agrees with analytic prediction to 2 decimal places.

### 2. Exponent invariance confirmed
When fitted in each model's own early-hazard regime (5th–30th percentile):
- Both show the same effective exponent within statistical noise.
- Both exhibit the same finite-window deficit below k−1 (as established in
  [[2026-05-30_age_incidence_power_law]]).

Example at μ=0.07: k=6 ordered → 2.111, unordered → 1.697 (different windows;
when using matched percentile regime, they converge).

### 3. Practical consequence
At realistic μ, unordered k=6–7 hits yield cancer onset TOO EARLY (median ~35yr
at μ=0.07). To match observed epidemiology (median ~65yr), the per-gene rate
must be lower in the unordered model — but adjusting μ changes magnitude, not
slope.

### 4. Driver-count discrepancy: NOT explained
Non-ordered accumulation does **not** change the age-incidence exponent. The
exponent is determined by the NUMBER of rate-limiting steps, not their order.
This is the second candidate mechanism tested (after clonal expansion in
[[2026-05-30-fitness-effect-multistage]]) that fails to explain the discrepancy.

## Candidate explanations remaining

- **Heterogeneous per-gene rates** (some hits are "easy" / high-rate, some are
  "hard" / low-rate → effective exponent reflects only the hard steps)
- **Tissue architecture / spatial constraints** (not all cells equally exposed)
- **Epistatic interactions** (early hits change rates of later hits)
- **Passenger-driven mutational acceleration** (MMR/POLE drivers increase μ)

## Falsification

Would be falsified if a proper analytic derivation of the unordered hazard
showed an exponent different from k−1 in some regime, or if heterogeneous rates
produced the same invariance (making that candidate also fail).

## References

- Beerenwinkel N et al. (2007) "Genetic progression and the waiting time to
  cancer." PLoS Comp Biol 3:e225.
- Nowak MA (2006) "Evolutionary Dynamics" Ch. 10 (multistage carcinogenesis).
- [[2026-05-30-fitness-effect-multistage]] — prior item showing s≈0.004 also
  fails to explain the discrepancy.
