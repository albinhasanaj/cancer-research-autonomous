# Bipartite Driver-Loss ↔ Druggable-Target Network

**Date:** 2026-05-30  
**Type:** finding  
**Thread:** synthetic-lethal  
**Status:** KEEP  

## Summary

Built a bipartite graph connecting 8 driver-loss events to 11 druggable
targets via 17 synthetic-lethal edges, weighted by approximate TCGA/COSMIC
pan-cancer driver frequencies. Computed degree, population coverage
(Σ freq of drivers reachable), and betweenness (driver-pairs bridged).

## Key results

| Target | Degree | Pop. Coverage | Drivers |
|--------|--------|---------------|---------|
| ATR    | 2      | 57.0%         | TP53_mut, ATM_loss |
| CHK1   | 2      | 57.0%         | TP53_mut, ATM_loss |
| WEE1   | 2      | 57.0%         | TP53_mut, ATM_loss |
| PARP1  | 3      | 31.0%         | BRCA1_loss, BRCA2_loss, KRAS_mut |
| PRMT5  | 1      | 15.0%         | MTAP_del |
| WRN    | 1      | 12.0%         | dMMR_MSIH |

**Highest-coverage targets:** ATR, CHK1, WEE1 — each covers ~57% of solid
tumours (via the TP53-mut + ATM-loss SL contexts). This reflects the known
clinical interest in the DDR-checkpoint axis for TP53-mutant tumours (PMID
40759474).

**Highest-degree target:** PARP1 (3 driver contexts) — but lower population
coverage than ATR/CHK1/WEE1 because BRCA/KRAS individually are rarer.

**Driver with most therapeutic options:** RB1_loss (4 targets: AURKA, AURKB,
PLK1, TTK) — but only ~8% pan-cancer frequency.

## Caveats (honest)

1. **Frequencies are approximate.** Pan-cancer averages smooth over strong
   tissue-type variation (e.g. KRAS is 90% in pancreatic but ~5% in breast).
2. **Context-dependence.** Not every TP53-mut tumour is equally ATR-dependent;
   this is an upper bound on coverage.
3. **No druggability weighting.** All targets treated equally; in reality some
   (WRN, PRMT5) have less clinical-stage drug availability than others (PARP1).
4. **This is a structured confirmation** of known DDR-targeting priorities, not
   a novel discovery.

## Script

`simulations/sl_bipartite_network.py`

## Output

- `simulations/output/sl_network_targets.csv`
- `simulations/output/sl_network_drivers.csv`

## Next steps

- Item 8: [[open_questions]] — Boolean network SL simulation to test whether
  topology alone can predict SL pairs.
- Extend this graph with tissue-specific frequencies and druggability scores
  (DGIdb) for a frequency × druggability ranking.

## References

- PMID 42207998 — Novel SL strategies in precision oncology
- PMID 42092061 — Two decades of PARP inhibitor SL
- PMID 42198893 — MTAP deficiency / PRMT5
- PMID 41962327 — WRN helicase in MSI-H
- PMID 40759474 — DDR targeting in TP53/ATM-mutated tumours
- PMID 34359636 — RB1 loss targeting
- PMID 41735281 — PARP + KRAS(G12D) combination
- PMID 29625053 — TCGA pan-cancer driver frequencies (Bailey et al. 2018)
