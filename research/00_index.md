# 00 — Index (home base)

This is the map of the research vault. Every iteration updates it.

## Navigation

- [[SCOPE]] — what is in and out of bounds
- [[open_questions]] — the priority queue (pick ONE item per iteration)
- `experiments/_log.md` — chronological log of every attempt, including dead ends

## Findings

- [[2026-05-30_khit_montecarlo_baseline]] — Armitage–Doll `k`-ordered-hit
  Monte Carlo of time-to-malignancy (`k = 2..7`, `μ = 0.07/yr`,
  `N = 200_000`). Empirical moments match `Erlang(k, μ)` to 3 decimals.
  Script: `simulations/multistage_khit_montecarlo.py`; output:
  `simulations/output/khit_{times,summary}.csv`.
- [[2026-05-30_age_incidence_power_law]] — age-incidence check (item 3). The
  `t^(k−1)` law is the `μt→0` asymptotic, **not** exact on the simulated window:
  the fitted effective exponent is below `k−1` (deficit grows with `k`), yet the
  MC reproduces the exact Erlang hazard to ~2% (Q2) and the closed-form local
  slope `s_k(x)=(k−1)−x·A_{k−1}/A_k → k−1` as `x→0` confirms the asymptotic.
  Scripts: `simulations/age_incidence_power_law.py`,
  `simulations/erlang_hazard_local_slope.py`.
- [[2026-05-30-cellpool-frailty-old-age-incidence-deceleration]] — cell-pool +
  inter-individual frailty extension (item 4). Individual = tissue of `N_cells`
  i.i.d. cells (onset = min), so `h_tissue = N·h_cell`; mixing `μ ~ Gamma(cv)`
  across individuals. **Honest partial-negative:** frailty makes the population
  hazard non-monotone (`cv ≥ 0.6`) and yields a peak-and-decline, but a realistic
  decline (`≥15%`) forces the peak to 44–65y, not the empirical 75–90y — frailty
  alone misses the late peak (so senescence / pool-shrinkage likely needed, PMID
  21953606). Analytic quadrature + cell-level MC agree to ~4%. Script:
  `simulations/cellpool_frailty_incidence.py`.
- [[2026-05-30-senescence-shrinking-pool-late-peak]] — senescence / shrinking
  at-risk pool extension (item 6). N(t) = N₀·exp(−λ_s·max(0, t−50)); tissue
  hazard h_tissue = N(t)·h_cell declines as the pool empties. **Positive result:**
  λ_s ≈ 0.035–0.042/yr (+ optional mild frailty cv ≤ 0.3) places the peak at
  71–91y with 19–42% decline — matching the empirical SEER pattern (PMID 21953606).
  Competing mortality has negligible effect. The shrinking pool is the **minimum
  sufficient extension** for the late-life peak-and-decline. Script:
  `simulations/cellpool_senescence_incidence.py`.

- [[2026-05-30-sl-bipartite-network]] — bipartite driver-loss ↔ druggable-target
  network (item 7). 8 drivers × 11 targets × 17 SL edges, weighted by TCGA
  pan-cancer frequency. ATR/CHK1/WEE1 top population coverage (57% via
  TP53+ATM); PARP1 highest degree (3 contexts, 31%). Script:
  `simulations/sl_bipartite_network.py`; output:
  `simulations/output/sl_network_{targets,drivers}.csv`.
- [[2026-05-30-boolean-sl-network]] — Boolean DDR/cell-cycle network SL screen
  (item 8). 14 nodes, 12 knockoutable; synchronous Boolean update under DNA
  damage. 11 SL pairs from 66 double-KOs; **9/9 known pairs recovered (100%)**;
  2 novel predictions (BRCA+WRN). Script: `simulations/boolean_sl_network.py`;
  output: `simulations/output/boolean_sl_pairs.csv`.

- [[2026-05-30-tcga-codeletion-brca-wrn]] — TCGA co-deletion counter-selection
  test for BRCA+WRN (item 9). Queried cBioPortal (UCEC, OV, COADREAD);
  **honest partial-negative:** MSI-H contexts show co-occurrence (hypermutation
  confound); ovarian trends toward ME (OR=0.69) but underpowered; controls
  validate methodology. Needs MSI stratification. Script:
  `simulations/tcga_codeletion_counterselection.py`.

## Literature notes

- [[2026-05-30_armitage_doll_multistage]] — restatement of the Armitage–Doll
  multistage model and its age-incidence prediction `I(t) ∝ t^(k−1)`, with
  modern status from 5 fetched PMIDs. Sets up open-questions items 2 & 3.
- [[2026-05-30_synthetic_lethality_survey]] — survey of synthetic lethality
  principles and 5 key SL pairs (BRCA–PARP, MTAP–PRMT5, MSI-H–WRN,
  TP53/ATM–DDR, RB1–mitotic kinases) + KRAS combinations. Grounded in 8 PMIDs.
  Opens the synthetic-lethal computational thread (items 7, 8).

## Active hypotheses

_(none yet — open hypotheses under review will be linked here)_

## Thread map

- **Multistage carcinogenesis thread.** Question 1 (literature) → Question 2
  (Monte Carlo of `k`-hit time-to-malignancy) → Question 3 (compare simulated
  age-incidence to `t^(k−1)` power law) → Question 4 (cell-pool + frailty vs the
  old-age incidence deceleration) → Question 6 (senescence / shrinking pool).
  Q1–3 closed (power law is asymptotic). Q4 closed: frailty alone misses the
  late peak. **Q6 closed:** age-shrinking pool (λ_s ≈ 0.035–0.042/yr after age
  50) IS the minimum sufficient mechanism for the empirical late-life
  peak-and-decline (peak 71–91y, decline 19–42%); competing mortality negligible.
  Thread complete for the basic multistage framework. Next open: Q5
  (synthetic-lethal) opens an independent thread.
- **Synthetic-lethal thread.** Question 5 (literature survey of SL principles
  and key pairs) → Question 7 (bipartite driver↔target network + centrality) →
  Question 8 (Boolean network SL simulation) → Question 9 (TCGA co-deletion
  counter-selection). Q5 closed: 5 SL pairs surveyed, grounded in 8 PMIDs.
  **Q7 closed:** bipartite network built; ATR/CHK1/WEE1 top coverage (57%),
  PARP1 highest degree (3 contexts). **Q8 closed:** 14-node Boolean DDR model
  recovers 9/9 known SL pairs from topology; 2 novel predictions (BRCA+WRN).
  **Q9 closed (partial-negative):** naive co-deletion test confounded by
  MSI-driven co-occurrence; ovarian trends ME but underpowered; MSI
  stratification needed. Next open: Q10 (stochastic extension), Q11
  (MSI-stratified/DepMap validation).

## System changes

_(none yet — log any agent self-extension of tools/ or structure here)_
