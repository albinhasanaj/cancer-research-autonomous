# Adaptive Therapy Scheduling for PARPi Resistance Delay

**Date:** 2026-05-30
**Item:** 18 (open_questions.md)
**Status:** KEEP (honest negative on clinical benefit)
**Triage:** EXTENDABLE — Gatenby adaptive therapy framework well-established;
delta = PARPi multi-mechanism application + regime analysis.

## Summary

Modelled intermittent PARPi dosing using Lotka-Volterra competition between
sensitive and 3 resistant subtypes (BRCA reversion, ABCB1 efflux, fork
protection) from [[2026-05-30-parp-multi-mechanism-resistance]]. Scanned 30+
fixed on/off schedules.

**Honest negative:** Adaptive therapy provides only **marginal benefit (6–9%)**
for PARPi in the clinically relevant MRD setting (N₀ = 10⁷, N/K = 0.01).

## Key findings

1. **MRD regime (N₀=10⁷):** Best schedule (56on/56off) extends TTP from 15.1
   to 16.0 months (+5.9%). All schedules within a narrow 14–16 month range.
2. **Intermediate burden (N₀=2×10⁸):** Benefit rises slightly to 9.2%
   (21on/14off), confirming competition matters only when N/K is non-trivial.
3. **Fitness cost sensitivity:** Even 2× amplified fitness costs yield only
   +3.1% benefit at N₀=10⁷ — too weak to change the conclusion.
4. **Mechanism dominance invariant:** BRCA reversion dominates (>98%) under
   both continuous and adaptive regimes; the schedule does not shift the
   dominant resistance route.

## Why adaptive therapy fails for PARPi MRD

The Gatenby mechanism requires:
- (A) Tumour near carrying capacity (strong competition for niche)
- (B) Significant fitness cost of resistance off-drug

PARPi maintenance post-surgery violates BOTH:
- N₀ ≈ 10⁶–10⁷ << K ≈ 10⁹ → competition term (1 − N/K) ≈ 1 (negligible)
- BRCA reversion restores full HR → minimal fitness cost (r_off = 0.045 vs
  S r_off = 0.05, only 10% difference)

This contrasts with metastatic castration-resistant prostate cancer (the
canonical adaptive therapy setting) where tumour IS near K and androgen
independence carries measurable cost.

## Clinical implication (hypothesis)

For PARPi maintenance in BRCA-mutated ovarian cancer, continuous dosing is
predicted to be near-optimal. Intermittent schedules save toxicity but provide
negligible resistance-delay benefit. Strategies targeting mutation supply
(e.g., ABCB1 efflux blocking, per [[2026-05-30-parp-multi-mechanism-resistance]])
remain more promising than scheduling optimisation.

## Model details

- Framework: Lotka-Volterra ODE with 4 populations (S + 3 R subtypes)
- Carrying capacity K = 10⁹; progression threshold 5×10⁸
- Drug effect: r_S_on = −0.04/d, r_S_off = +0.05/d
- Resistance: reversion (u=10⁻⁸, r_on=0.05), efflux (u=10⁻⁷, r_on=0.035),
  fork protection (u=5×10⁻⁸, r_on=0.03)
- Script: `simulations/adaptive_therapy_parp.py`
- Output: `simulations/output/adaptive_therapy_schedules.csv`,
  `adaptive_therapy_near_capacity.csv`, `adaptive_therapy_fitness_cost.csv`,
  `adaptive_therapy_burden.csv`

## What would change this conclusion

- **Spatial structure** (agent-based model with local competition): could make
  competition relevant even at low total N
- **Pre-existing resistant subclones** (not modelled): would shift dynamics
- **Much higher fitness cost** of resistance (e.g., if efflux carries severe
  growth penalty in absence of drug)
- **Adaptive scheduling by biomarker** (rather than fixed cycles): could
  exploit transient windows

## Literature grounding

- Gatenby RA et al. "Adaptive Therapy" Cancer Research 2009; 69(11):4894-4903
- Gatenby RA et al. "Towards Multidrug Adaptive Therapy" Cancer Res 2020;
  80(7):1578
- Anderson et al. "Deriving Optimal Treatment Timing" Bull Math Biol 2024/2025
- Sun et al. "Conditional Success of Adaptive Therapy" arXiv:2502.09392 (2025)

## Links

- Extends: [[2026-05-30-parp-resistance-dynamics]],
  [[2026-05-30-parp-multi-mechanism-resistance]]
- Thread: Resistance dynamics → adaptive scheduling
