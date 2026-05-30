# Stochastic Boolean DDR Network — SL Penetrance Screen

**Date:** 2026-05-30  
**Item:** 10 (open_questions.md)  
**Status:** KEEP (honest negative on functional prediction)

## Summary

Extended the deterministic 14-node DDR Boolean model
([[2026-05-30-boolean-sl-network]]) to a **stochastic** version with:
- **Asynchronous random update** (one node per step, randomly chosen)
- **Noise on rules** (probability `p_noise` of flipping any rule output)
- **SL penetrance** = continuous [0,1] score (fraction of 2000 replicates dying)

Tested robustness across noise levels p ∈ {0.02, 0.05, 0.10}.

## Key findings

### 1. Top SL pairs are robust to noise
The top-5 pairs are identical across all tested noise levels:
1. RB1+PLK1 (SL score 0.53 at p=0.05)
2. BRCA1+PARP1 (0.49)
3. BRCA1+WRN (0.49)
4. BRCA2+PARP1 (0.49)
5. BRCA2+WRN (0.49)

This confirms the topological SL predictions are **structurally stable** — they
don't depend on the synchronous update assumption.

### 2. Stochastic model reveals penetrance gradient
Unlike the binary deterministic screen (SL or not), the stochastic model shows
graded vulnerability. Even non-SL pairs have elevated penetrance under noise,
and the SL score (excess over single-KO) provides a continuous ranking.

### 3. NO significant correlation with DepMap functional data
**Spearman ρ = 0.272, p = 0.31** (N=16 matched pairs) between network SL
penetrance score and DepMap Cohen's d from item 12.

Interpretation: the simplified Boolean topology captures **which** pairs are
qualitatively SL but does NOT predict the **quantitative** rank order of drug
sensitivity. Real vulnerability depends on:
- Expression levels and protein abundance
- Pathway redundancy beyond 14 nodes
- Cell-type specific wiring
- Dosage effects vs binary KO

## Critic assessment

- **What is claimed?** Stochastic extension adds continuous scoring and confirms
  topological robustness, but fails to predict functional rank order.
- **Evidence:** 2000 replicates × 3 noise levels × 66 pairs; Spearman test on
  16 matched pairs with DepMap.
- **What would falsify?** A richer network (>14 nodes, quantitative logic) might
  correlate; or a different comparison metric might reveal partial agreement.
- **Did I check the frontier?** Yes — stochastic Boolean SL screening is a known
  methodology (Shmulevich & Dougherty 2010, Lee et al 2018 Briefings Bioinf);
  the specific delta is applying it to our DDR model and comparing to our DepMap
  data. Classification: EXTENDABLE.
- **Rediscovery?** The topology robustness is expected; the negative correlation
  is a genuine finding from this specific comparison — not a rediscovery.
- **Verdict: KEEP** — honest negative on prediction, positive on robustness.

## Implications

The synthetic-lethal thread has reached its useful ceiling with this 14-node
topology. Further progress requires either:
- A larger, quantitative model (ODE/continuous, fitted to expression data), or
- Direct data-driven approaches (ML on DepMap, not topology-first)

The Boolean model remains useful as a **didactic/qualitative tool** for
understanding SL logic but should not be used for quantitative prioritisation.

## Scripts & output

- Script: `simulations/stochastic_boolean_sl.py`
- Output: `simulations/output/stochastic_sl_penetrance.csv`
- Multi-noise JSON: `simulations/output/stochastic_sl_multi_noise.json`

## Links

- Prior: [[2026-05-30-boolean-sl-network]] (deterministic version)
- Comparison data: [[2026-05-30-depmap-ddr-context-screen]] (DepMap Cohen's d)
- Thread: synthetic-lethal (items 5→7→8→9→11→12→10)
