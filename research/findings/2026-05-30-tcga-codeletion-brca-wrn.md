# TCGA co-deletion counter-selection test for BRCA+WRN

**Date:** 2026-05-30  
**Status:** KEEP (honest partial-negative)  
**Tags:** #finding #synthetic-lethality #TCGA #co-deletion #BRCA #WRN  
**Script:** `simulations/tcga_codeletion_counterselection.py`  
**Output:** `simulations/output/codeletion_results.csv`,
`simulations/output/codeletion_power_analysis.csv`

## Question

The Boolean DDR network ([[2026-05-30-boolean-sl-network]]) predicts BRCA1+WRN
and BRCA2+WRN as synthetic-lethal pairs. If true, TCGA tumours should show
**counter-selection** (mutual exclusivity): fewer co-alterations of both genes
than expected under independence, because cells with both losses die.

## Method

1. Queried cBioPortal public API for mutation + homozygous deletion data across
   3 TCGA PanCancer Atlas studies (whole-exome):
   - UCEC (uterine, N=529; high MSI prevalence)
   - OV (ovarian serous, N=585; low MSI, BRCA-relevant)
   - COADREAD (colorectal, N=594; mixed MSI)
2. Built 2×2 contingency tables per gene pair.
3. One-tailed Fisher's exact test for mutual exclusivity (OR < 1).
4. Controls: KRAS+BRAF (known ME in CRC), TP53+KRAS (context-dependent).
5. Analytical power analysis at published pan-cancer frequencies.

## Results

| Study | Pair | Obs | Exp | OR | p(ME) | Verdict |
|-------|------|-----|-----|-----|-------|---------|
| UCEC | BRCA1+WRN | 27 | 5.7 | 16.2 | 1.0 | **co-occurrence** |
| UCEC | BRCA2+WRN | 37 | 9.7 | 13.4 | 1.0 | **co-occurrence** |
| OV | BRCA1+WRN | 1 | 1.4 | 0.69 | 0.58 | not significant |
| OV | BRCA2+WRN | 1 | 1.1 | 0.88 | 0.69 | not significant |
| COADREAD | BRCA1+WRN | 5 | 1.1 | 7.1 | 1.0 | **co-occurrence** |
| COADREAD | BRCA2+WRN | 6 | 2.6 | 2.8 | 0.99 | **co-occurrence** |
| COADREAD | KRAS+BRAF | 6 | 22.9 | 0.16 | 4e-7 | **mutual exclusivity** ✓ |
| UCEC | TP53+KRAS | 16 | 36.3 | 0.27 | 8e-7 | **mutual exclusivity** ✓ |

## Interpretation

### The hypermutation confound

In MSI-high contexts (UCEC, CRC), BRCA+WRN shows **strong co-occurrence**. This
is NOT evidence against SL — it reflects the well-known phenomenon that MSI-H
tumours accumulate passenger mutations across the genome including DNA repair
genes. The co-occurrence is driven by shared hypermutator background, not
functional synergy.

### Ovarian (the cleanest test)

In ovarian serous carcinoma (low MSI, BRCA germline/somatic alterations are
pathogenic drivers), BRCA1+WRN shows OR=0.69 — **trending toward ME** but with
only 25 BRCA1-altered and 33 WRN-altered samples (expected co-alt = 1.4),
statistical power is extremely low. The result is consistent with either
weak/partial SL or independence.

### Power analysis

At published pan-cancer frequencies (BRCA ~3%, WRN ~2%), N=10,000 samples:
- Complete SL (obs=0 co-alt): **detectable** (p=0.002)
- Partial SL (obs=⅓ expected): **borderline** (p=0.058)
- Individual studies (N=500–600): severely underpowered for these rare events

### Controls validate methodology

- KRAS+BRAF ME in colorectal: confirmed (OR=0.16, p=4×10⁻⁷) — known biological
  ME due to parallel MAPK pathway activation.
- TP53+KRAS ME in UCEC: confirmed (OR=0.27, p=8×10⁻⁷) — known subtype
  separation (serous vs endometrioid).

## Conclusion

The naive co-deletion test **cannot confirm or refute** the BRCA+WRN SL
prediction because:
1. High-MSI contexts dominate and confound with co-occurrence.
2. Low-MSI contexts (ovarian) have insufficient events for power.

This is an **honest partial-negative**: the test framework works (controls pass)
but the specific BRCA+WRN question requires either:
- (a) MSI-status stratification (test only MSS tumours),
- (b) Pan-cancer mega-analysis with TMB correction, or
- (c) Direct functional data (cell-line viability screens, e.g. DepMap).

## Links

- Predicted from: [[2026-05-30-boolean-sl-network]]
- SL survey: [[2026-05-30_synthetic_lethality_survey]]
- Next step: Item 10 (stochastic extension) or new item: MSI-stratified
  co-deletion test / DepMap functional validation.
