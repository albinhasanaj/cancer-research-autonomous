# Multi-mechanism PARPi resistance: reversion + efflux + fork protection

**Date:** 2026-05-30
**Item:** 16 (open_questions)
**Thread:** Resistance dynamics
**Triage:** EXTENDABLE (Iwasa/Michor/Nowak multi-type framework established;
delta = PARPi-specific 3-route parameterization + regime-switching analysis)
**Verdict:** KEEP

## Question

How does the diversity of parallel resistance escape routes (BRCA reversion,
drug efflux, replication fork protection) change the phase transition threshold
and time-to-resistance compared to the single-mechanism model
([[2026-05-30-parp-resistance-dynamics]])?

## Methods

Extended the Iwasa/Michor/Nowak birth-death framework to k=3 independent
resistant subtypes, each with literature-grounded mutation rates and fitness:

| Mechanism | u (per div) | Net growth (/d) | Source |
|-----------|-------------|-----------------|--------|
| BRCA reversion | 1e-8 | 0.050 | Frameshift reversion (Sakai 2008) |
| ABCB1 efflux | 1e-7 | 0.035 | Promoter rearrangement (Patch 2015 Nature 521:489, Christie 2019) |
| Fork protection loss | 5e-8 | 0.030 | PTIP/EZH2/53BP1 LOF (Gogola 2018, Ray Chaudhuri 2016) |

Total u_eff = 1.6e-7 (16× reversion alone).

Tau-leaping simulation (dt=1d, 500 reps per config); analytic multi-type
Iwasa approximation for comparison. Three analyses:
1. Multi vs single comparison at bulk (N0=1e9)
2. Phase transition scan across N0 (1e5–1e9)
3. Combination blocking strategies in MRD (N0=1e7)

## Key findings

### 1. Phase transition shift

- Single mechanism: N0_crit ~ 1/u_rev = **1e8**
- Multi mechanism: N0_crit ~ 1/u_eff = **6e6**
- The MRD "safe zone" shrinks by **16×**

At N0=1e7 (surgical MRD): P(resistance within 10yr) jumps from **10.4%**
(single) to **29.0%** (multi) — nearly 3× increase.

### 2. Regime-switching insight

**Bulk tumour (N0=1e9):** Resistance is preexisting (u·N0 >> 1 for all routes).
Competition is purely on GROWTH RATE → **reversion wins** (net 0.05/d fastest;
490/500 simulated wins). Time-to-resistance is expansion-dominated (~7.8 months).

**MRD (N0=1e7):** Resistance must arise de novo. Competition is on MUTATION
SUPPLY RATE → **efflux wins** (u=1e-7 highest; 89/147 wins in MRD). This is
a qualitative regime switch in which mechanism dominates clinically.

### 3. Combination blocking strategies (MRD, N0=1e7)

| Strategy | u_eff | P(resist) | Median T_R |
|----------|-------|-----------|------------|
| All 3 open | 1.6e-7 | 29.4% | 11.7 mo |
| Block efflux | 6e-8 | 12.2% | 10.0 mo |
| Block fork prot | 1.1e-7 | 27.4% | 11.5 mo |
| Block efflux + fork | 1e-8 | 12.2% | 10.0 mo |

**Blocking efflux alone** halves P(resistance) from 29% → 12% because it is
the dominant supply route. Blocking fork protection adds little marginal gain
once efflux is eliminated. The critical intervention target is ABCB1.

## Honest caveats

1. **Independence assumption.** Mechanisms modelled as independent; in reality,
   hypermutator states (e.g. BRCA-deficient cells already have elevated mutation
   rates) could correlate escape probabilities.
2. **Fixed fitness.** Each resistant type has constant fitness; in practice,
   drug dose changes and adaptive therapy could shift the landscape.
3. **No cross-resistance.** Model assumes each mechanism independently rescues;
   some combinations (reversion + efflux) could co-occur, making resistance
   more robust to second-line therapy.
4. **Parameter uncertainty.** Efflux rate (1e-7) is an upper estimate from
   structural variant frequency; could be lower if restricted to specific
   genomic contexts.

## Connections

- Extends [[2026-05-30-parp-resistance-dynamics]] (item 13, single mechanism)
- The regime-switching finding explains additional PFS heterogeneity beyond
  the N0 variation identified in item 13
- Clinically connects to ATR-inhibitor combinations (blocking fork protection)
  and ABCB1 inhibitors (blocking efflux) — both in active clinical trials

## Script

`simulations/parp_multi_mechanism_resistance.py`

## Output

`simulations/output/parp_multi_vs_single.csv`,
`simulations/output/parp_multi_phase_transition.csv`,
`simulations/output/parp_multi_combination.csv`
