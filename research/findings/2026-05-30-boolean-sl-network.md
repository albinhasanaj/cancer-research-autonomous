# Boolean Network SL Simulation — DDR / Cell-Cycle Pathway

**Date:** 2026-05-30  
**Type:** finding  
**Thread:** synthetic-lethal  
**Status:** KEEP  
**Script:** `simulations/boolean_sl_network.py`  
**Output:** `simulations/output/boolean_sl_pairs.csv`  

## Summary

Constructed a 14-node Boolean network of the DDR + cell-cycle checkpoint
pathway and simulated all 66 single/double knockout combinations under DNA
damage. Identified synthetic-lethal pairs from **network topology alone**.

## Network design

- 12 knockoutable nodes: ATM, ATR, TP53, CHK1, CHK2, WEE1, BRCA1, BRCA2,
  PARP1, WRN, RB1, PLK1
- Boolean update rules reflect canonical pathway wiring (not fitted to data)
- Survival requires THREE redundant systems to remain partially intact:
  1. **Repair:** HR (BRCA1+BRCA2) OR alt-repair (PARP1+WRN)
  2. **Checkpoint:** G1 (ATM→TP53) OR G2 (ATR→CHK1→WEE1)
  3. **Mitotic fidelity:** If RB1 lost → PLK1 required

## Results

- **Single knockouts:** All 12 single KOs viable (no essential genes under this
  topology — redundancy provides buffering).
- **SL pairs found:** 11 pairs (of 66 tested)
- **Known pairs recovered: 9/9 (100%)**
  - BRCA1+PARP1, BRCA2+PARP1 (DDR-DDR, PMID 42092061)
  - TP53+ATR, TP53+CHK1, TP53+WEE1 (DDR-checkpoint, PMID 40759474)
  - ATM+ATR, ATM+CHK1, ATM+WEE1 (DDR-checkpoint, PMID 40759474)
  - RB1+PLK1 (cell-cycle, PMID 34359636)
- **Novel predictions:** 2 pairs
  - BRCA1+WRN, BRCA2+WRN (HR loss + WRN loss → no repair arm functional)

## Interpretation

The model demonstrates that **minimal pathway-topology logic** (redundant
repair arms, redundant checkpoints, conditional mitotic fidelity) is
*sufficient* to explain the known SL relationships. Three independent
redundancy modules each generate SL when both arms are lost.

## Honest caveats

1. **Confirmation, not blind prediction.** The Boolean rules encode the pathway
   wiring that *produces* the known SL — this confirms logical consistency, not
   independent discovery. A true prediction test would require a network wired
   from protein–protein interaction topology alone (without prior SL knowledge).
2. **Deterministic / simplified.** Real SL has dose-dependence, incomplete
   penetrance, and context-specificity not captured here.
3. **Novel predictions need validation.** BRCA+WRN SL is mechanistically
   plausible (no repair) but not yet clinically established.

## Novel prediction: BRCA+WRN

Mechanism: BRCA loss abolishes HR. WRN loss abolishes structure-resolution
needed for alt-repair pathway function. Together → complete repair failure →
death. This is consistent with WRN's role in resolving stalled forks that arise
when HR is absent. Could be tested computationally by checking TCGA co-deletion
frequencies (cells with both lost would be counter-selected).

## Links

- Builds on: [[2026-05-30_synthetic_lethality_survey]], [[2026-05-30-sl-bipartite-network]]
- Related: [[open_questions]] item 8
