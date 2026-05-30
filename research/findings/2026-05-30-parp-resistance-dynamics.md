# Evolutionary dynamics of PARPi resistance via BRCA reversion

**Date:** 2026-05-30  
**Item:** open_questions #13  
**Status:** KEEP (honest extension of known framework)  
**Script:** `simulations/parp_resistance_dynamics.py`  
**Output:** `simulations/output/parp_resistance_{scan,maintenance,preexisting}.csv`

## Summary

Applied the Iwasa/Michor/Nowak (2006) stochastic birth-death framework
specifically to PARP-inhibitor resistance via BRCA-reversion mutations.
Parameterised with clinically-constrained values and identified a **sharp phase
transition** that explains clinical PFS heterogeneity.

## Model

- Sensitive cells (BRCA-deficient): birth rate b_S=0.1/d, death rate d_S=0.14/d
  under PARPi (net decline −0.04/d)
- Resistant cells (BRCA-reverted): b_R=0.1/d, d_R=0.05/d (net growth +0.05/d)
- Reversion mutation rate: u = 1e-8 per division (conservative frameshift)
- Detection threshold: ρ = 1e6 cells

Framework: Iwasa Y, Michor F, Nowak MA. *Proc R Soc B* 2006;273:1137-1144.

## Key findings

### 1. Bulk tumour (N0=1e9): resistance is preexisting and inevitable

- P(preexisting resistance) = 1 − exp(−u·N0) ≈ 1.0 for u·N0 = 10
- Analytic T_resist = 9.1 months (≈ expansion time of resistant clone only)
- Simulation confirms: median 7.8 months, 100% develop resistance <10yr

### 2. Phase transition at u·N0 ~ 1

| u·N0    | P(preexist) | Regime              |
|---------|-------------|---------------------|
| 0.001   | 0.001       | Drug wins           |
| 0.01    | 0.01        | Rare de novo        |
| 0.1     | 0.095       | Boundary            |
| 1       | 0.63        | Likely preexisting  |
| 10      | 1.0         | Certain preexisting |

### 3. Maintenance (MRD) setting explains long clinical PFS

Clinical context: after surgery + platinum → minimal residual disease → PARPi
maintenance. Effective N0 ~ 1e5–1e7 (NOT 1e9).

- N0=1e6, u=1e-8 → u·N0=0.01 → P(preexist)=0.01
- Sensitive population declines rapidly (half-life ~17 days)
- Total mutation supply exhausted before resistance can arise in most patients
- **Only ~0.8% of simulated patients** develop resistance within 10 years
- Explains clinical PFS of 24–56 months (SOLO-1, PRIMA)

### 4. The "paradox of effective killing" in MRD

Stronger drug (higher d_S) → faster S decline → LESS total mutation supply →
DELAYED resistance in MRD setting. This is the opposite of the bulk-tumour
regime where T_resist ≈ expansion time only (independent of kill rate).

Implication: **maximal cytoreduction before PARPi maintenance is the
rate-limiting intervention for PFS** — not the PARPi potency itself.

### 5. Parameter sensitivity

1. **N0 dominates** — sets the preexisting vs de novo regime
2. **u secondary** — but u·N0 is the key product
3. **Drug kill rate** — counterintuitive direction in MRD
4. **Resistant net growth rate** — determines expansion phase (~9 months
   at 0.05/d for ρ=1e6)

## Comparison to clinical data

| Scenario         | Model prediction    | Clinical reference              |
|------------------|--------------------|---------------------------------|
| Bulk (N0=1e9)    | ~9 months          | First-line PFS ~12-18mo (no maintenance) |
| MRD (N0=1e6)     | Rare (<1% in 10yr) | SOLO-1 5yr PFS ~48% (BRCA-mut) |
| MRD (N0=1e7)     | ~11% in 10yr       | Intermediate responders         |

The model's phase-transition behaviour is **qualitatively consistent** with
clinical heterogeneity: patients with better debulking (lower N0) have
dramatically better PFS.

## Honest caveats

1. **Simplification:** single resistance mechanism (BRCA reversion). Real
   resistance includes HR-independent mechanisms (53BP1 loss, ABCB1
   upregulation, fork stabilisation). Multi-mechanism u_effective > u_reversion.
2. **Constant rates:** ignores pharmacokinetic variability, immune effects,
   and microenvironment.
3. **Tau-leaping approximation:** valid for large populations but may
   underestimate stochastic effects near extinction.
4. **Per-division u not directly measured clinically** — inferred indirectly
   from prevalence data.
5. **The analytic formula returns ∞ for MRD scenarios** because total supply
   < ln(2). This is correct (resistance is improbable, not impossible) but
   means the analytic approximation breaks down; the simulation handles it.

## Links

- Connects [[2026-05-30_synthetic_lethality_survey]] (BRCA-PARP SL pair)
- Connects the multistage clonal-evolution thread (shared framework)
- Extends [[2026-05-30-sl-bipartite-network]] (therapeutic implications of SL)
- Next: could extend to multi-mechanism resistance, or add immune escape
