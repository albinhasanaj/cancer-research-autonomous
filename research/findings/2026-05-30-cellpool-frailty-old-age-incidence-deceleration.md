---
title: cellpool frailty old-age incidence deceleration
kind: finding
status: kept
created: 2026-05-30T16:41:04.940303+00:00
tags: [multistage, frailty, old-age-incidence, in-silico]
---

# Cell-pool frailty multistage model: old-age incidence deceleration vs. decline

**Date:** 2026-05-30
**Type:** finding (KEEP — honest, partly negative)
**Thread:** [[00_index]] -> multistage carcinogenesis (cell-pool / old-age extension)
**Related:** [[2026-05-30_khit_montecarlo_baseline]] (the k-hit Erlang baseline),
[[2026-05-30_age_incidence_power_law]] (Erlang hazard saturates to mu),
[[2026-05-30_armitage_doll_multistage]] (old-age plateau caveat); closes
[[open_questions]] item 4.

## Question

Item 4: extend the Armitage-Doll k-hit model with a finite tissue cell pool and
ask whether a finite at-risk pool **plus inter-individual stage-rate (mu)
heterogeneity (frailty)** can reproduce the empirically observed deceleration /
peak-and-decline of cancer incidence at old age (SEER: incidence peaks ~75-90y
then falls, PMID 21953606).

## Model (script: simulations/cellpool_frailty_incidence.py)

- **Cell:** time-to-malignancy ~ Erlang(k, mu) (k ordered hits, per-stage rate mu).
- **Individual = tissue of N_cells i.i.d. cells**, onset = the minimum cell time.
  Because cells are i.i.d., tissue survival is S_tissue=S_cell^N and tissue
  hazard is EXACTLY h_tissue = N * h_cell. The per-cell Erlang hazard is
  increasing and saturates to mu (Erlang is IFR), so a **homogeneous** population
  gives a monotone-increasing hazard plateauing at N*mu -- deceleration, never
  a decline. This is the null.
- **Frailty:** between individuals mu ~ Gamma(mean mu0, cv), shared across one
  individuals cells (per-cell i.i.d. frailty averages out within a large tissue
  by the LLN, so heterogeneity is placed at the individual level, per the
  epidemiological frailty literature PMID 17722193 / 22306590). Observed
  population incidence is the survival-weighted mixture hazard
  h_pop(t)=E_mu[h_ind S_ind]/E_mu[S_ind]; high-mu individuals deplete early so
  h_pop can peak then decline.
- Computed two independent ways: **exact quadrature** over the Gamma(mu) density
  (log-space S_cell^N), and a **genuine cell-level Monte Carlo** (draw mu_i,
  draw N_cells Erlang times, take the min; N=60_000 individuals/cv) as a check.
- Params: k=6, mu0=0.015/yr, N_cells=200 (an EFFECTIVE at-risk compartment,
  not a literal cell count), cv in {0, 0.3, 0.6, 0.9, 1.2}.

## Observed output (simulations/output/cellpool_frailty_summary.csv)

| cv | median onset age | monotone hazard? | peak age | post-peak decline | MC median rel-err |
|----|------------------|------------------|----------|-------------------|-------------------|
| 0.0 | 95 | yes | (120, window end) | 0.000 | 5.3% |
| 0.3 | 96 | yes | (120) | 0.000 | 3.6% |
| 0.6 | 105 | no | 101 | 1.7% | 3.7% |
| 0.9 | 120 | no | 65 | 15.2% | 3.9% |
| 1.2 | 120 | no | 44 | 30.5% | 5.7% |

The cell-level Monte Carlo reproduces the analytic population hazard to ~4-6%
median relative error across every cv (max 16-30% only in sparse tail bins),
confirming h_tissue = N*h_cell and the survival-weighted mixing are correct.

## Interpretation (the recorded claim)

1. **Frailty IS sufficient to turn the monotone multistage hazard into a
   decelerating / non-monotone one.** With no heterogeneity (cv<=0.3) the
   population hazard rises monotonically (plateau toward N*mu), matching the
   pure-IFR expectation. Adding Gamma frailty (cv>=0.6) makes it non-monotone and
   produces a genuine peak-and-decline via selective depletion of high-mu
   individuals -- the classic frailty mechanism (PMID 22306590).
2. **But frailty ALONE cannot reproduce the EMPIRICAL late-life peak.** There is
   a stiff trade-off: a substantial decline (>=15%) requires cv>=0.9, which pushes
   the incidence peak down to 44-65y -- far younger than the observed ~75-90y
   (PMID 21953606). Conversely, a peak in the realistic 75-90y window coincides
   with little or no decline. You get either a late peak with no fall, or a fall
   with too-early a peak -- not both.
3. **Therefore the finite-pool + frailty extension reproduces old-age
   *deceleration* but not the *late-life peak-and-decline* on its own.** This is
   consistent with PMID 21953606s argument that standard carcinogenesis models
   require additional mechanisms (cellular / tissue senescence, shrinking at-risk
   pool with age) to fit the oldest-age data. This iteration does NOT claim
   senescence is unnecessary; it shows frailty alone is insufficient.

## What this does NOT show / caveats

- **No competing mortality.** h_pop is incidence among cancer-free survivors of
  a pool that only exits via cancer; it overstates old-age incidence vs real
  cohorts where non-cancer death removes people first. A full SEER comparison
  needs a competing-risks extension.
- **N_cells is an effective compartment**, tuned to land onset in a human age
  range, not a literal stem-cell count; absolute ages are illustrative.
- **Not a novel mechanism.** Gamma-frailty multistage models are established
  (PMID 17722193, 22306590); the contribution here is the explicit cell-pool
  (min-over-N) framing and the quantified peak-age/decline trade-off showing
  frailty alone misses the empirical late peak.
- Binned hazard (1-yr bins, integer-age analytic points) carries a minor <1yr
  discretisation offset; the ~4% MC agreement shows it is immaterial.

## Critic pass (KEEP / DEMOTE / REJECT)

- **Claim:** Frailty makes the multistage population hazard non-monotone /
  decelerating. -> **KEEP** (cv>=0.6 non-monotone; MC-validated to ~4%).
- **Claim:** Frailty alone reproduces the empirical old-age peak-and-decline. ->
  **REJECT** as stated -- only achievable with an unrealistically early peak;
  recorded honestly as the central negative.
- **Claim:** The cell-level MC matches the analytic mixture hazard. -> **KEEP**
  (~4-6% median rel-err, all cv).
- No solved / cure / breakthrough language; in-silico textbook-model analysis,
  every empirical anchor cites a PMID.

## Pointers

- Script: simulations/cellpool_frailty_incidence.py
- Outputs: simulations/output/cellpool_frailty_hazard.csv,
  simulations/output/cellpool_frailty_summary.csv
- Literature anchors: PMID 17722193 (Gamma-frailty multistage fits cancer data),
  PMID 21953606 (SEER old-age peak-and-decline; models need modification),
  PMID 22306590 (ordered subpopulations / fixed frailty -> hazard deceleration).

