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

- [x] **10. Stochastic Boolean extension with noise/partial penetrance.** Make
  the Boolean network probabilistic (async update, noise on rules) and measure
  SL penetrance as a continuous score rather than binary. Compare rank order
  to clinical drug-sensitivity data.
  → Done 2026-05-30, see [[2026-05-30-stochastic-boolean-sl-penetrance]].
  Async update + noise p∈{0.02,0.05,0.10}, 2000 reps per pair. Top-5 SL pairs
  (RB1+PLK1, BRCA1+PARP1, BRCA1+WRN, BRCA2+PARP1, BRCA2+WRN) are robust
  across all noise levels. Honest negative: Spearman ρ=0.27, p=0.31 vs DepMap
  Cohen's d — no significant rank correlation. Boolean topology captures
  qualitative SL but NOT quantitative drug sensitivity. SL thread at ceiling;
  further progress needs data-driven or quantitative (ODE) modelling.
  Script: `simulations/stochastic_boolean_sl.py`.

## Open candidate questions (new threads)

- [x] **13. Evolutionary dynamics of resistance to SL-based therapy.** Model a
  population of tumour cells under PARP-inhibitor selection where BRCA-reversion
  mutations restore HR. Stochastic birth-death with mutation; predict
  time-to-resistance as f(tumour size, mutation rate, drug kill rate). Connects
  the multistage (clonal evolution) and SL threads. Purely computational.
  → Done 2026-05-30, see [[2026-05-30-parp-resistance-dynamics]]. Sharp phase
  transition at u·N0~1: bulk tumour (N0=1e9) → resistance inevitable in ~9mo;
  MRD (N0=1e6) → <1% develop resistance (explains long clinical PFS).
  "Paradox of effective killing": stronger drug delays resistance in MRD.
  Script: `simulations/parp_resistance_dynamics.py`.

- [x] **14. Multi-hit model with driver-specific fitness effects.** Extend the
  Armitage-Doll framework so each hit confers a selective advantage (not just
  unlocks the next stage). Compare clonal expansion dynamics to neutral
  accumulation. Literature suggests this matters (Beerenwinkel, Bozic). Could
  explain why observed mutation rates in sequenced tumours exceed the k-hit
  prediction.
  → Done 2026-05-30, see [[2026-05-30-fitness-effect-multistage]]. Triage:
  EXTENDABLE (Beerenwinkel 2007 / Bozic 2010 framework; delta = exponent
  analysis). **Honest negative on hypothesis:** realistic s≈0.004 gives only
  10-14% speedup; effective exponent slightly increases (more events in window),
  NOT decreases. Only unrealistic s≥0.02 depresses the exponent. Clonal
  expansion alone does NOT explain the driver-count discrepancy. Script:
  `simulations/multistage_fitness_expansion.py`.

- [x] **15. Non-ordered hit accumulation model.** Relax the Armitage-Doll
  assumption that hits must occur in strict order. Allow any-order acquisition
  (combinatorial paths). Compare waiting times and age-incidence exponents to the
  ordered model. This is a candidate explanation for the driver-count discrepancy
  that item 14 ruled out for clonal expansion.
  → Done 2026-05-30, see [[2026-05-30-unordered-hit-accumulation]]. Triage:
  EXTENDABLE (Beerenwinkel 2007 settles the theory; delta = computational
  verification). **Honest negative:** unordered model is ~H_k faster but exponent
  is INVARIANT to ordering (both ≈ k-1 in early regime). Non-ordered accumulation
  does NOT explain the driver-count discrepancy. Two candidates now ruled out
  (clonal expansion + ordering); heterogeneous per-gene rates remains top
  candidate. Script: `simulations/multistage_unordered_hits.py`.

- [x] **17. Heterogeneous per-gene mutation rates and effective exponent.** Model
  k required hits where each gene has a DIFFERENT mutation rate (e.g. drawn from
  a lognormal). When rates vary, only the slowest steps are rate-limiting; the
  effective exponent should reflect the number of HARD steps, not total k. This
  is the leading remaining candidate for the driver-count discrepancy (items 14
  and 15 ruled out clonal expansion and ordering respectively).
  → Done 2026-05-30, see [[2026-05-30-heterogeneous-rates-exponent]]. Triage:
  EXTENDABLE (Frank 2007, Luebeck & Moolgavkar 2002 establish principle; delta
  = computational verification of per-gene rate variation). **Honest negative:**
  asymptotic exponent is INVARIANT to per-gene rates (always k-1 regardless of
  spread); finite-window contribution is only ~0.15–0.2 additional depression.
  Third candidate ruled out. Resolution: the "discrepancy" is largely a
  finite-window artifact — homogeneous k=6 already gives fitted exponent ≈1.7
  in the 45–80yr epidemiological window. Script:
  `simulations/multistage_heterogeneous_rates.py`.

- [x] **16. Multi-mechanism PARPi resistance (reversion + efflux + shielding).**
  Extend the single-mechanism resistance model (item 13) to include 3 parallel
  resistance routes (BRCA reversion, drug efflux, replication fork protection).
  How does the diversity of escape routes change the phase transition threshold
  and time-to-resistance? Connects to clinical combination strategies.
  → Done 2026-05-30, see [[2026-05-30-parp-multi-mechanism-resistance]]. Triage:
  EXTENDABLE (Iwasa multi-type framework known; delta = PARPi-specific 3-route
  parameterization + regime analysis). **Key findings:** (1) u_eff = 1.6e-7 (16×
  reversion alone) shrinks MRD safe zone N0_crit from 1e8 → 6e6; (2) regime
  switch — reversion dominates in bulk (fastest growth 0.05/d) vs efflux
  dominates in MRD (highest supply u=1e-7); (3) blocking efflux alone halves
  P(R) from 29% → 12% at N0=1e7. Script:
  `simulations/parp_multi_mechanism_resistance.py`.

- [x] **18. Adaptive therapy scheduling for PARPi resistance delay.** Model
  intermittent dosing (drug holidays) where sensitive cells partially recover,
  suppressing resistant clones via competition. Determine optimal on/off schedule
  that maximises time-to-progression. Extends items 13+16. Purely computational
  (game-theoretic / ODE + stochastic).
  → Done 2026-05-30, see [[2026-05-30-adaptive-therapy-parp-scheduling]]. Triage:
  EXTENDABLE (Gatenby framework known; delta = PARPi multi-mechanism application).
  **Honest negative:** marginal benefit (6–9%) because PARPi MRD (N₀=10⁷) is at
  N << K; competition negligible; reversion fitness cost too low. Continuous dosing
  near-optimal in this regime. Script: `simulations/adaptive_therapy_parp.py`.

- [x] **19. Immune escape dynamics in the clonal evolution framework.** Model
  tumour–immune coevolution where immune editing applies selection against
  immunogenic clones. How does neoantigen load (correlated with driver count)
  interact with immune checkpoint therapy? Connects multistage + resistance
  threads to immunotherapy. Purely computational.
  → Done 2026-05-30, see [[2026-05-30-immune-escape-checkpoint-dynamics]].
  Triage: EXTENDABLE (Lakatos 2020 PMID 32929288 + 2025 PMID 40025156 establish
  framework; delta = coupling k-hit driver count → neoantigen burden → checkpoint
  response + unified escape framework). **Key findings:** (1) phase transition at
  u_eff·N0·(s_R/|s_S|) ~ 1 — same structure as PARPi resistance; N0_crit ≈ 5e5
  under checkpoint therapy; (2) higher k_drivers → more elimination (k=10: 14.7%
  elim vs k=2: 0%) — explains TMB-response correlation; (3) clonal neoantigen
  fraction modulates response (f_clonal=1.0: 4.7% elim vs f_clonal=0.2: 0%);
  (4) without checkpoint, escape 100% regardless (immune pressure alone
  insufficient). Unifies PARPi resistance + immune escape under one evolutionary
  framework. Script: `simulations/immune_escape_checkpoint.py`.

- [ ] **20. Immune escape + adaptive scheduling: does competition help here?**
  Unlike PARPi MRD (item 18: N << K, competition negligible), immune-escaped
  clones may have higher fitness cost (genomic instability from HLA-LOH).
  Test whether intermittent checkpoint dosing (drug holidays to let immune-
  sensitive cells compete) provides benefit in the immune escape model. Connects
  items 18 + 19.

- [ ] **21. Neoantigen dynamics during clonal evolution: does immunoediting
  shape the driver accumulation rate?** Extend the multistage model so immune
  selection removes immunogenic drivers (negative selection on neoantigens per
  Lakatos 2020). How does this change the effective mutation rate and time-to-
  malignancy? Could explain why some cancers accumulate fewer drivers than
  expected.

- [x] **11. MSI-stratified co-deletion test or DepMap functional validation.**
  Re-run the BRCA+WRN counter-selection test restricted to MSS (microsatellite-
  stable) tumours only, OR use DepMap cell-line dependency data to test whether
  WRN-dependent lines are enriched for BRCA loss. Follow-up to the confound
  identified in item 9.
  → Done 2026-05-30, see [[2026-05-30-depmap-wrn-brca-validation]]. Used DepMap
  26Q1 CRISPR data (1208 lines, Gene Dependency + Chronos). All-lines: strong
  BRCA-mut→WRN-dep signal (p=2e-6) but CONFOUNDED by MSI co-occurrence.
  MSS-only (92 MSI-proxy excluded): borderline p=0.053, small effect r=0.15.
  Conclusion: DepMap does NOT robustly confirm direct BRCA+WRN SL independent
  of MSI. Boolean model's prediction likely a topology artifact.
  Script: `simulations/depmap_wrn_brca_validation.py`.

- [x] **12. Pan-DepMap SL discovery: which gene pairs show strongest
  context-dependent co-dependency beyond known MSI→WRN?** Use the DepMap API
  to systematically screen DDR gene dependencies (ATR, CHK1, WEE1, PARP1)
  stratified by driver mutation context (TP53-mut vs WT, ATM-loss vs WT).
  Extends the bipartite network (item 7) with functional DepMap evidence.
  Tests whether the network's top-ranked targets (ATR/CHK1/WEE1 in TP53/ATM
  context) are confirmed by CRISPR screens.
  → Done 2026-05-30, see [[2026-05-30-depmap-ddr-context-screen]]. Honest
  mixed: BRCA1→PARP1 confirmed (d=0.51, p=0.004), TP53→CHEK1 confirmed
  (d=0.18, p=0.008), but ATM→ATR/CHK1/WEE1 all ns (underpowered n=36).
  Surprise: BRCA1→ATR (d=0.47, p=0.013) not predicted by network. Network
  partially validated; ATM 57% coverage claim overestimated.
  Script: `simulations/depmap_ddr_context_screen.py`.
