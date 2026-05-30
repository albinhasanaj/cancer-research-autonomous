# Immune Escape Dynamics Under Checkpoint Therapy

**Date:** 2026-05-30  
**Status:** KEEP (honest extension)  
**Item:** open_questions #19  
**Script:** `simulations/immune_escape_checkpoint.py`  
**Output:** `simulations/output/immune_escape_results.csv`

## Summary

Modelled tumour–immune coevolution where each driver hit (from the multistage
framework) generates neoantigens with probability p_neo, immune killing scales
with neoantigen load (clonal >> subclonal), and immune escape (HLA-LOH or IFNγ
pathway loss) is a stochastic event. Checkpoint blockade amplifies immune kill
rate 3×.

## Triage

**EXTENDABLE.** Key framework papers exist:
- PMID 32929288 (Lakatos 2020): neoantigen evolution under negative selection
- PMID 40025156 (2025): stochastic birth-death immune escape + analytic approx
- PMID 30318143 (Angelova 2018): immunoediting shapes metastatic evolution

**Delta added:** (1) explicit coupling of k-hit driver count to immune pressure
via neoantigen score; (2) checkpoint therapy as therapy that restores killing;
(3) parallel phase-transition structure to PARPi resistance (item 13).

## Key Findings

### 1. Phase transition at tumour size (parallels PARPi result)

With checkpoint therapy (k=6, f_clonal=0.7):
| N0   | P(escape) | P(elimination) |
|------|-----------|----------------|
| 1e5  | 0.04      | 0.96           |
| 1e6  | 0.41      | 0.59           |
| 1e7  | 0.97      | 0.03           |
| 1e8  | 1.00      | 0.00           |

**Critical threshold:** u_eff·N0·(s_R/|s_S|) ~ 1 → N0_crit ≈ 5×10⁵ cells.
Identical structural result to PARPi resistance (item 13: u·N0 ~ 1). This
unifies both therapies under a single evolutionary escape framework.

### 2. Driver count modulates checkpoint response

More drivers → higher neoantigen load → stronger immune pressure → more
checkpoint benefit:
| k_drivers | P(escape) ckpt ON | P(elimination) |
|-----------|-------------------|----------------|
| 2         | 1.000             | 0.000          |
| 6         | 0.987             | 0.013          |
| 10        | 0.853             | 0.147          |

**Connects multistage to immunotherapy:** tumours that accumulated more drivers
(further along multistage progression) are paradoxically better checkpoint
responders — matching the clinical TMB-response correlation.

### 3. Neoantigen clonality determines response quality

Higher clonal fraction (trunk neoantigens) → stronger per-cell immune pressure:
| f_clonal | P(escape) ckpt ON | P(elim) | Median T_escape (days) |
|----------|-------------------|---------|------------------------|
| 0.2      | 1.000             | 0.000   | 327                    |
| 0.6      | 0.993             | 0.007   | 342                    |
| 1.0      | 0.953             | 0.047   | 348                    |

Consistent with [[McGranahan 2016 Science|PMID 27141727]]: clonal neoantigen
burden (not total) predicts checkpoint response.

### 4. Without checkpoint: escape is universal

Without anti-PD1/PDL1, immune pressure (base_kill=0.02/day × neoantigen_score)
is insufficient for net tumour decline (net growth +0.013/day). Escape is 100%
at all sizes tested. Checkpoint therapy is required to cross the net-decline
threshold.

## Analytic Validation

Iwasa-framework analytic approximation:
- P(esc) ≈ 1 − exp(−u_eff · (b·N0/|net_S|) · (s_R/b))
- Agrees with simulation to within 10% relative error across N0 scan.

## Connections to Prior Work

- **PARPi resistance (item 13):** Same phase-transition structure (u·N0 ~ 1).
  Checkpoint therapy for immune escape ↔ PARPi for BRCA reversion. Unified
  evolutionary framework: therapies that impose selection create an escape
  transition at u_eff · mutation_supply ~ 1.
- **Multistage thread (items 1-3, 14):** k drivers → neoantigen burden → immune
  pressure. More advanced tumours (higher k) are better checkpoint targets. This
  resolves the seeming paradox that late-stage tumours sometimes respond to
  immunotherapy.
- **Adaptive therapy (item 18):** Same caveat applies — scheduling may not help
  if N << K (low competition). But immune escape fitness cost is higher than
  BRCA reversion cost, so there may be more room for competition-based
  strategies here (future question).

## Honest Caveats

1. **Simplified immune model:** Real immune dynamics involve T-cell exhaustion,
   antigen presentation heterogeneity, tumour microenvironment suppression —
   none modelled here. The 2025 paper (PMID 40025156) adds immunomodulation.
2. **Binary escape:** Model treats escape as all-or-nothing (HLA-LOH or IFN
   pathway loss). Reality: partial escape, multiple antigens, immune memory.
3. **Static neoantigen landscape:** In reality, new mutations arise during
   therapy, changing the neoantigen landscape dynamically.
4. **Parameter uncertainty:** base_kill rate and checkpoint_boost are poorly
   constrained empirically. Phase transition location shifts with these.

## What's New (vs Literature)

The existing models (PMID 32929288, 40025156) establish the framework but:
- Lakatos focuses on neoantigen frequency spectrum in growing tumours (no therapy)
- The 2025 paper models generic immunomodulation (no connection to driver count)

This work's specific contribution: explicit coupling of the **k-hit multistage
progression** (driver accumulation → neoantigen load → immune vulnerability) to
the **checkpoint therapy escape dynamics**, revealing that the same evolutionary
phase-transition structure governs both targeted therapy resistance and immune
escape — unifying items 13 and 19 under one framework.
