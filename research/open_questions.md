# Open Questions — priority queue

Pick the **single** highest-value unchecked item per iteration. Keep items
**independent** where possible so parallel workers can claim different ones
without colliding. To claim an item, check its box and tag it with your worker id.

**Before you compute, triage the frontier** (see `.github/skills/research-strategy`):
search native web + PubMed (+ a provider research mode when warranted) to decide
if the item is ANSWERED / EXTENDABLE / OPEN. Only OPEN questions justify a fresh
simulation.

**When generating new questions, bias toward the frontier:** prefer questions the
literature does *not* already answer, gaps your own findings exposed, or
high-leverage capability investments — over re-validating known theory.
Re-derivations are warm-ups, not the goal.

- [x] **1. Survey the multi-hit / Armitage–Doll multistage model.** Read 3–5
  primary PMIDs (start: `pubmed_search("Armitage Doll multistage carcinogenesis", 5)`).
  Write a `literature` note restating the model, its assumptions, and the
  age-incidence prediction (incidence ∝ age^(k−1) for k stages). Cite every PMID.
  → Done 2026-05-30, see [[2026-05-30_armitage_doll_multistage]]
  (PMIDs 36307647, 34695806, 29383584, 28439564, 20838610).

- [x] **2. Build a clonal-evolution Monte Carlo of time-to-malignancy vs required
  "hits".** Implement a stochastic simulation (via `run_python`, saved under
  `simulations/`) where a cell lineage acquires driver hits at some rate; record
  the distribution of time-to-malignancy as a function of the number of required
  hits k. Write a `finding` note with the script path and the observed output.
  → Done 2026-05-30, see [[2026-05-30_khit_montecarlo_baseline]]. Script:
  `simulations/multistage_khit_montecarlo.py` (μ = 0.07/yr, k ∈ {2..7},
  N = 200_000 lineages). Empirical T_k moments match Erlang(k, μ) to 3 decimals.
  Per-lineage CSV `simulations/output/khit_times.csv` is the input for item 3.

- [x] **3. Compare the simulated age-incidence curve to the published power law.**
  Take the output of item 2 and test whether incidence scales as age^(k−1).
  Fit/plot, report the exponent, and compare to the Armitage–Doll prediction from
  item 1. Write a `finding` note; log honestly if it does NOT match.
  → Done 2026-05-30, see [[2026-05-30_age_incidence_power_law]]. Honest negative
  on the naive form: the fitted finite-window exponent is BELOW `k−1` (deficit
  grows with `k`), because survival≥0.97 still reaches `μt≈1–3`, outside the
  `μt→0` regime. NOT a sim error — MC matches the exact Erlang hazard to ~2%, and
  the closed-form local slope `s_k(x)→k−1` as `x→0` confirms the law is purely
  asymptotic. Scripts: `simulations/age_incidence_power_law.py`,
  `simulations/erlang_hazard_local_slope.py`.

## Closed candidate questions

- [x] **4. Add tissue cell-pool scaling and ask for the old-age incidence
  plateau/fall-off.** Extend the model so incidence is `P(min over N_cells of
  T_k ≤ t)`; test whether a finite at-risk pool plus stage-rate heterogeneity can
  reproduce the empirically observed deceleration of incidence at old age (noted
  as a caveat in [[2026-05-30_armitage_doll_multistage]]).
  → Done 2026-05-30, see [[2026-05-30-cellpool-frailty-old-age-incidence-deceleration]].
  Script `simulations/cellpool_frailty_incidence.py` (k=6, μ0=0.015/yr,
  N_cells=200, Gamma frailty cv∈{0..1.2}; analytic quadrature + cell-level MC,
  ~4% agreement). Honest partial-negative: frailty turns the monotone multistage
  hazard non-monotone (cv≥0.6) and yields a peak-and-decline, BUT a realistic
  decline (≥15%) forces the peak down to 44–65y, not the empirical 75–90y —
  frailty alone misses the late peak (PMIDs 17722193, 21953606, 22306590).

## Open candidate questions (pick ONE next iter)

- [x] **6. Add cellular/tissue senescence or an age-shrinking at-risk pool to the
  cell-pool model** and test whether it supplies the late-life peak-and-decline
  that frailty alone could not (the gap identified in item 4 /
  [[2026-05-30-cellpool-frailty-old-age-incidence-deceleration]], per PMID
  21953606). Optionally add competing (non-cancer) mortality to make the hazard
  comparable to SEER person-year denominators.
  → Done 2026-05-30, see [[2026-05-30-senescence-shrinking-pool-late-peak]].
  Script `simulations/cellpool_senescence_incidence.py`. POSITIVE: age-shrinking
  pool (λ_s≈0.035–0.042/yr, t_sen=50y) + optional mild frailty (cv≤0.3) produces
  peak at 71–91y with 19–42% decline, matching SEER (PMID 21953606). Competing
  mortality negligible. Multistage thread now complete for the basic framework.

- [x] **5. Open a new thread: driver-pathway / synthetic-lethal analysis.** Per
  [[SCOPE]] tractable target 4 — explore known driver pathways and candidate
  synthetic-lethal pairs from public knowledge bases (ground every pair in a
  PMID). Independent of the multistage thread, so a parallel worker can claim it.
  → Done 2026-05-30, see [[2026-05-30_synthetic_lethality_survey]]. Surveyed 5
  established/emerging SL pairs (BRCA–PARP, MTAP–PRMT5, MSI-H–WRN,
  TP53/ATM–ATR/CHK1/WEE1, RB1–Aurora/PLK1) + KRAS combinations; grounded in 8
  PMIDs. Identified 3 computational extensions for follow-up.

## Open candidate questions (synthetic-lethal thread)

- [x] **7. Build a bipartite driver-loss ↔ druggable-target network** from the
  SL pairs surveyed in item 5 plus TCGA/COSMIC driver-mutation frequencies.
  Compute degree/centrality to identify high-coverage therapeutic targets.
  Purely computational (graph + public data).
  → Done 2026-05-30, see [[2026-05-30-sl-bipartite-network]]. 8 drivers × 11
  targets × 17 SL edges weighted by TCGA frequency. ATR/CHK1/WEE1 top
  population coverage (57% via TP53+ATM); PARP1 highest degree (3 contexts,
  31%). Script: `simulations/sl_bipartite_network.py`.

- [x] **8. Boolean network SL simulation.** Construct a small Boolean network
  of a canonical pathway (e.g. DDR or cell-cycle) and simulate single vs
  double knockouts to identify synthetic-lethal node pairs from topology alone.
  Compare to the known SL pairs from item 5.
  → Done 2026-05-30, see [[2026-05-30-boolean-sl-network]]. 14-node DDR +
  cell-cycle Boolean model; 66 double-KO combinations; 11 SL pairs found;
  **9/9 known pairs recovered (100%)**; 2 novel predictions (BRCA+WRN).
  Script: `simulations/boolean_sl_network.py`.

## Open candidate questions (next threads)

- [x] **9. TCGA co-deletion counter-selection test for BRCA+WRN.** The Boolean
  model predicts BRCA+WRN SL. If true, TCGA tumours should show
  counter-selection (fewer co-deletions than expected by chance). Testable
  purely computationally from public TCGA mutation matrices.
  → Done 2026-05-30, see [[2026-05-30-tcga-codeletion-brca-wrn]]. Honest
  partial-negative: MSI-high contexts show co-occurrence (hypermutation
  confound); ovarian (low-MSI) trends toward ME (OR=0.69) but underpowered;
  controls (KRAS+BRAF, TP53+KRAS ME) validate the methodology. Proper test
  needs MSI stratification or TMB correction. Script:
  `simulations/tcga_codeletion_counterselection.py`.

- [ ] **10. Stochastic Boolean extension with noise/partial penetrance.** Make
  the Boolean network probabilistic (async update, noise on rules) and measure
  SL penetrance as a continuous score rather than binary. Compare rank order
  to clinical drug-sensitivity data.

- [ ] **11. MSI-stratified co-deletion test or DepMap functional validation.**
  Re-run the BRCA+WRN counter-selection test restricted to MSS (microsatellite-
  stable) tumours only, OR use DepMap cell-line dependency data to test whether
  WRN-dependent lines are enriched for BRCA loss. Follow-up to the confound
  identified in item 9.
