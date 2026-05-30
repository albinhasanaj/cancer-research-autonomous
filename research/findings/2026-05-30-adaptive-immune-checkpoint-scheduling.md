# Adaptive Checkpoint Scheduling: Competition Helps Delay Immune Escape

**Date:** 2026-05-30  
**Item:** 20 (open_questions)  
**Status:** KEEP (honest positive — contrast with item 18 honest negative)  
**Script:** `simulations/adaptive_immune_checkpoint.py`  
**Output:** `simulations/output/adaptive_immune_checkpoint.csv`

## Context

Item 18 showed that adaptive therapy scheduling is **marginal** for PARPi
resistance in MRD (6–9% benefit) because N₀ ≪ K makes competition negligible.
Item 20 hypothesised that immune-escaped clones under checkpoint therapy face
different conditions: (1) bulk tumour burden (N₀/K ≈ 0.3–1.0), (2) potentially
higher fitness cost of escape (HLA-LOH → genomic instability).

## Triage

**EXTENDABLE.** The Gatenby adaptive therapy framework is well-established
(PMID 30278037 explicitly proposes "natural adaptive therapy" for immunotherapy).
The specific delta: does the immune escape model (item 19) benefit from adaptive
scheduling where PARPi MRD did not?

## Model

Lotka-Volterra competition ODE: S (immune-sensitive) + E (immune-escaped)
sharing carrying capacity K = 10⁹.

- Drug ON (checkpoint active): r_S = −0.06/day (strong immune kill), r_E = +0.03/day
- Drug OFF (holiday): r_S = +0.04/day (natural immune only), r_E = +0.03/day
- Competition: growth × (1 − total/K)
- Escape mutation: u = 7×10⁻⁷/division (HLA-LOH + IFNγ loss)
- Fitness cost of escape: 0.03/day (higher than PARPi's 0.01)
- Progression: E reaches 10⁸ cells

## Key Findings

### 1. Adaptive scheduling provides meaningful benefit (+17–38%)

| Schedule | TTP (days) | Benefit vs continuous |
|----------|-----------|----------------------|
| Continuous | 418 | baseline |
| 14on/14off | 438 | +4.8% |
| Adaptive (0.5/0.9) | 577 | +37.9% |
| Adaptive (0.3/0.7) | 516 | +23.3% |
| Adaptive (0.2/0.6) | 489 | +17.0% |

Adaptive therapy WORKS here — in stark contrast to PARPi MRD (item 18).

### 2. Competition IS the mechanism: N₀/K ratio determines benefit

| log₁₀(N₀) | N₀/K | Periodic benefit | Adaptive benefit |
|-----------|------|-----------------|-----------------|
| 6 | 0.001 | −2.6% | −1.7% |
| 7 | 0.010 | −2.9% | −1.9% |
| 8 | 0.100 | −2.5% | +1.1% |
| 8.5 | 0.316 | +0.5% | +11.5% |
| 9 | 1.000 | +24.0% | +24.0% |

**At N/K ≪ 1 (PARPi regime): no benefit or slight harm.**  
**At N/K ≥ 0.3: significant benefit emerges.**

This confirms the hypothesis: the Gatenby mechanism requires N ~ K to generate
meaningful competitive suppression of resistant clones.

### 3. Fitness cost modulates benefit magnitude

| Escape cost | TTP continuous | TTP adaptive | Adaptive benefit |
|-------------|---------------|-------------|-----------------|
| 0.005 | 237d | 295d | +24% |
| 0.01 | 259d | 323d | +25% |
| 0.03 | 418d | 516d | +23% |
| 0.05 | >1095d | >1095d | 0% (escape never occurs) |

At cost ≥ 0.05, escape is too slow to reach progression — the problem becomes
moot. The "sweet spot" for adaptive therapy is cost ∈ [0.005, 0.04] where escape
is fast enough to matter but slow enough to be modulated by competition.

## Mechanistic Explanation

1. **Drug ON:** checkpoint amplifies immune kill → S declines → escape mutations
   arise → E grows into vacated niche.
2. **Drug OFF (holiday):** S recovers rapidly (r_S = +0.04 > r_E = +0.03) → S
   fills niche → competitive suppression of E via (1 − total/K) term.
3. **Net effect:** intermittent therapy trades some short-term tumour control for
   long-term escape delay by maintaining competitive pressure on E.

This is EXACTLY the Gatenby mechanism — and it works here because:
- N ~ K (competition actually bites)
- Sensitive cells grow FASTER off-drug than escaped cells (s_S_off > r_E)
- Fitness cost of escape (0.03) gives sensitive cells a competitive edge

## Critical Assessment (why it failed for PARPi but works here)

| Factor | PARPi MRD (item 18) | Checkpoint (this) |
|--------|--------------------|--------------------|
| N₀/K | 0.01 | 0.5 |
| Competition term | 0.99 (negligible) | 0.50 (strong) |
| Fitness cost | 0.01 (reversion) | 0.03 (HLA-LOH) |
| r_S off-drug | 0.05 | 0.04 |
| r_E | 0.045 (reversion, nearly WT) | 0.03 (compromised) |
| **r_S_off − r_E** | **0.005** (tiny) | **0.01** (meaningful) |

The competitive advantage of sensitive cells off-drug (r_S_off − r_E = 0.01/day)
is 2× larger in the immune context, AND competition actually bites because N ~ K.

## Honest Caveats

1. **"No treatment" is best for escape delay** — but clinically unacceptable
   because tumour grows unchecked (r_S = +0.04/day). Adaptive scheduling is the
   realistic compromise.
2. **Model assumes homogeneous mixing** (well-mixed ODE). Real tumours have
   spatial structure that may reduce competition efficiency.
3. **Single escape route.** Real immune escape is multi-route (HLA-LOH, B2M loss,
   PDL1 upregulation, antigen loss). Multi-route would reduce benefit (as in
   item 16 for PARPi).
4. **Deterministic ODE** — stochastic effects at low E may matter; threshold
   crossing events not captured perfectly.

## Unifying Framework

Items 18 + 20 together establish a **predictive criterion** for when adaptive
therapy helps:

> Adaptive therapy benefit ∝ (N₀/K) × (r_S_off − r_E) / r_E

- If N₀/K ≪ 1 OR r_S_off ≈ r_E → negligible benefit (item 18)
- If N₀/K ~ 1 AND r_S_off > r_E → meaningful benefit (this item)

This criterion can guide clinical trial design: checkpoint adaptive scheduling
should be tested in patients with **high tumour burden** (advanced/metastatic),
not in adjuvant/MRD settings.

## Links

- Extends: [[2026-05-30-immune-escape-checkpoint-dynamics]] (item 19)
- Contrasts: [[2026-05-30-adaptive-therapy-parp-scheduling]] (item 18, negative)
- Literature: PMID 30278037 (Gatenby 2018, natural adaptive therapy)
- Literature: PMID 40998270 (2025, evolutionary double-bind + LV model)
