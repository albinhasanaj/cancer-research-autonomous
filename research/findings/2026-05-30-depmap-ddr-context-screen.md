# Pan-DepMap DDR target screen in driver-mutation contexts

**Date:** 2026-05-30  
**Item:** 12 (open_questions)  
**Status:** KEEP (honest mixed result)  
**Triage:** EXTENDABLE — the SL principles are established; this adds systematic
quantitative validation of the bipartite network's specific predictions.

## Question

Does DepMap CRISPR data confirm the bipartite network's (item 7) top-ranked
synthetic lethal predictions? Specifically: are ATR/CHK1/WEE1 preferentially
essential in TP53-mut or ATM-loss contexts, and is PARP1 preferentially
essential in BRCA1/2-mut contexts?

## Method

- **Dataset:** DepMap Public 26Q1+Score, Chronos gene effect scores
- **Cell lines:** 1208 screened
- **Targets:** ATR, CHEK1, WEE1, PARP1
- **Driver contexts:** TP53-mut (n=799), ATM-mut (n=36), BRCA1-mut (n=24),
  BRCA2-mut (n=41)
- **Test:** Mann-Whitney U, one-sided (mut more dependent = lower Chronos score)
- **Effect size:** Cohen's d, rank-biserial correlation
- **Script:** `simulations/depmap_ddr_context_screen.py`
- **Output:** `simulations/output/depmap_ddr_context_screen.{json,csv}`

## Results

### Rankings by Cohen's d (positive = mut more dependent)

| Rank | Pair | d | p | Predicted? |
|------|------|---|---|-----------|
| 1 | BRCA1→PARP1 | +0.510 | 0.004** | ✓ |
| 2 | BRCA1→ATR | +0.467 | 0.013* | ✗ (novel) |
| 3 | BRCA2→PARP1 | +0.313 | 0.082 | ✓ |
| 4 | BRCA1→CHEK1 | +0.245 | 0.117 | ✗ |
| 5 | TP53→CHEK1 | +0.179 | 0.008** | ✓ |
| 6 | ATM→PARP1 | +0.143 | 0.188 | ✗ |
| 7 | TP53→WEE1 | +0.070 | 0.133 | ✓ |
| 8 | TP53→ATR | +0.011 | 0.356 | ✓ |
| 9–16 | ATM→ATR/CHK1/WEE1 | ≤ 0 | ns | ✓ (all fail) |

### Summary

- **Predicted SL pairs tested:** 8/8
- **Significant at p<0.05:** 2/8 (BRCA1→PARP1, TP53→CHEK1)
- **Mean Cohen's d (predicted):** +0.109
- **Non-predicted pairs significant:** 1/8 (BRCA1→ATR)

## Interpretation

### Confirmed predictions
- **BRCA1→PARP1** (d=0.51, p=0.004): Strongest signal — the most validated
  clinical SL pair (PMID 42207998). Network correctly ranks this highly.
- **TP53→CHEK1** (d=0.18, p=0.008): Modest but significant. Supports the
  G1-checkpoint-loss → S/G2-checkpoint-dependency rationale.

### Failed predictions
- **ATM→ATR/CHK1/WEE1:** All non-significant, some even negative direction.
  Likely reasons: (a) severe underpowering (n=36), (b) binary mutation
  annotation may miss functional ATM loss (biallelic vs monoallelic, epigenetic
  silencing), (c) real-world redundancy not captured in the simplified network.
  The literature's strong ATM→ATR SL (PMID: PMC10234020) is from isogenic
  screens, not heterogeneous pan-cancer DepMap data.
- **TP53→ATR** and **TP53→WEE1:** Non-significant despite large n (799). The
  effect exists but is diluted across pan-cancer heterogeneity; may require
  lineage stratification.

### Surprise finding
- **BRCA1→ATR** (d=0.47, p=0.013): Not predicted by bipartite network (which
  has BRCA→PARP1 only), but biologically plausible — BRCA1-loss increases
  replication stress → ATR becomes essential for replication fork protection.
  Suggests the bipartite network's edge set is incomplete.

## Critic assessment

- The bipartite network's **BRCA→PARP1 edge is robustly validated**; its
  claim that ATR/CHK1/WEE1 are top targets "via TP53+ATM context" is **only
  partially supported** — TP53→CHEK1 works, but ATM context is invisible in
  pan-cancer DepMap.
- The network's 57% population-coverage claim (TP53+ATM → ATR/CHK1/WEE1) is
  **overestimated** — the ATM component (~7% frequency) contributes no
  detectable DepMap signal at pan-cancer level.
- The surprise BRCA1→ATR pair indicates the network should include
  replication-stress dependencies, not only the canonical repair-pathway SL.

## Links

- [[2026-05-30-sl-bipartite-network]] — the bipartite network whose
  predictions are tested here
- [[2026-05-30_synthetic_lethality_survey]] — SL literature grounding
- [[2026-05-30-depmap-wrn-brca-validation]] — prior DepMap analysis (item 11)
