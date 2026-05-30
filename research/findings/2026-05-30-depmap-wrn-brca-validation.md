# DepMap functional validation: BRCA+WRN synthetic lethality

**Date:** 2026-05-30  
**Status:** KEEP (honest mixed/negative)  
**Thread:** Synthetic-lethal → item 11

## Question

The [[2026-05-30-boolean-sl-network|Boolean DDR model]] predicted BRCA+WRN as a
novel SL pair. The [[2026-05-30-tcga-codeletion-brca-wrn|TCGA co-deletion test]]
was confounded by MSI-driven hypermutation. Can DepMap CRISPR dependency data
confirm or refute BRCA+WRN SL in a functional (cell-viability) assay?

## Triage

**Frontier check:** Web search confirms WRN SL is established for MSI (mismatch
repair deficiency), not specifically for BRCA1/2 loss. No published evidence of
direct BRCA+WRN SL in MSS context. Classification: **OPEN** — warrants a
computational test with publicly available DepMap data.

## Method

- **Data:** DepMap 26Q1 via portal API (CRISPR Gene Dependency probability +
  Chronos gene effect scores)
- **Design:** Compare WRN dependency in BRCA1/2-damaging-mutant vs wild-type
  cell lines. Stratify by MSI status (proxy: WRN dependency probability > 0.5).
- **Test:** Mann-Whitney U, one-sided (H₁: BRCA-mut more WRN-dependent)
- **Script:** `simulations/depmap_wrn_brca_validation.py`

## Results

### All cell lines (n=1208)

| Group | n | Mean WRN dep | Median |
|-------|---|-------------|--------|
| BRCA-mut (damaging) | 62 | 0.365 | 0.126 |
| BRCA-WT | 1146 | 0.134 | 0.060 |

- Mann-Whitney U one-sided p = **1.96 × 10⁻⁶** (significant)
- Chronos confirmation: BRCA-mut mean = −0.604, WT mean = −0.157, p = 2.35 × 10⁻⁶

### MSS-only (excluding 92 MSI-proxy lines)

| Group | n | Mean WRN dep | Median |
|-------|---|-------------|--------|
| BRCA-mut MSS | 43 | 0.119 | 0.077 |
| BRCA-WT MSS | 1073 | 0.091 | 0.056 |

- Mann-Whitney U one-sided p = **0.053** (borderline, not significant at α=0.05)
- Rank-biserial r = 0.146 (small effect)

## Interpretation

**CONFOUNDED.** The strong pan-line signal (p=2e-6) is largely driven by
BRCA-mutant lines that are also MSI-high (and thus WRN-dependent via the known
MSI→WRN pathway). After excluding MSI-proxy lines:

- The signal drops to borderline (p=0.053)
- A weak trend persists in the predicted direction (BRCA-mut slightly more
  WRN-dependent), but insufficient to confirm direct BRCA+WRN SL
- The effect size is small (r=0.15)

**Conclusion:** DepMap data does **not** robustly support a direct BRCA+WRN
synthetic lethal interaction independent of MSI context. The Boolean model's
BRCA+WRN prediction was likely an artifact of simplified pathway topology — the
model collapses HR repair into a single pathway where BRCA and WRN are
co-essential for repair, but real cells have more redundant repair routes.

## Caveats

1. MSI proxy is based on WRN dependency threshold, not direct MSI annotation
   (conservative: removes all high-WRN-dep lines regardless of cause)
2. BRCA mutations include all "damaging" (likely_lof + tumor_suppressor_high_impact
   + HIGH vep_impact + frameshift/stop_gained/splice), not just biallelic loss
3. Borderline p=0.053 could become significant with a stricter BRCA-loss
   definition (homozygous only) or with copy-number data

## Links

- [[2026-05-30-boolean-sl-network]] — source of the BRCA+WRN prediction
- [[2026-05-30-tcga-codeletion-brca-wrn]] — TCGA test (also confounded)
- [[2026-05-30_synthetic_lethality_survey]] — SL literature survey
